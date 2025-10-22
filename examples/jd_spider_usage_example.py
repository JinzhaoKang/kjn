# examples/jd_spider_usage_example.py
# -*- coding: utf-8 -*-
"""
JD 评论抓取示例（只改 example）
- 支持单个 SKU 或文件批量
- 可选 Playwright 预热（滚动加载，使用保存的登录状态）
- 新增限速/翻页参数：--cooldown-ms、--max-pages（默认更保守）
- 结果保存为 JSON/CSV，并处理 datetime 可序列化
"""

import os
import sys
import csv
import json
import time
import argparse
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# 允许从项目根运行：PYTHONPATH=$(pwd) python3 examples/jd_spider_usage_example.py ...
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 导入你的电商爬虫（保持与你项目一致）
from app.services.spider.ecommerce_spider import create_ecommerce_spider  # noqa: E402


# --------------------------- 工具函数 ---------------------------

def now_tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_dir(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def normalize_for_json(obj: Any) -> Any:
    """把 datetime / set / 非字符串列表 等转成可 JSON 序列化的形态"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (set, tuple)):
        return list(obj)
    if isinstance(obj, dict):
        return {k: normalize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize_for_json(v) for v in obj]
    return obj


def save_json(path: Path, data: Any):
    ensure_dir(path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(normalize_for_json(data), f, ensure_ascii=False, indent=2)
    print(f"[OK]  Saved: {path}")


def save_csv(path: Path, rows: List[Dict[str, Any]]):
    """把统一结构的若干条评论写成 CSV"""
    ensure_dir(path)
    # 预定义常用列；其余字段自动追加到尾部
    base_cols = [
        "item_id", "platform", "rating", "content",
        "created_at", "published_at", "user_nick",
        "sku", "pics", "sentiment", "priority", "quality_score"
    ]
    # 收集所有列
    all_keys = set()
    for r in rows:
        all_keys.update(r.keys())
    # 保序：先放 base，再放其它
    other_cols = [k for k in sorted(all_keys) if k not in base_cols]
    fieldnames = base_cols + other_cols

    def _stringify(v: Any) -> str:
        if isinstance(v, (dict, list, set, tuple)):
            return json.dumps(normalize_for_json(v), ensure_ascii=False)
        if isinstance(v, datetime):
            return v.isoformat()
        v = "" if v is None else str(v)
        # 清理换行，避免把 CSV 撑坏
        return v.replace("\r", " ").replace("\n", " ").strip()

    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            row = {k: _stringify(r.get(k)) for k in fieldnames}
            w.writerow(row)
    print(f"[OK]  Saved: {path}")


def load_sku_list(p: Path) -> List[str]:
    if not p.exists():
        raise FileNotFoundError(str(p))
    text = p.read_text(encoding="utf-8").strip()
    # 支持 json 数组或 txt 每行一个
    if text.startswith("["):
        arr = json.loads(text)
        return [str(x).strip() for x in arr if str(x).strip()]
    else:
        return [line.strip() for line in text.splitlines() if line.strip()]


def warmup_with_playwright(
    sku: str,
    ua: Optional[str] = None,
    scroll_steps: int = 24,
    pause_ms: int = 1000,
    state_file: Optional[Path] = None,
) -> bool:
    """
    用 Playwright 预热商品页（降低风控概率）。
    若未安装 playwright，则跳过并返回 False。
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print("[WARN] 未安装 Playwright，跳过预热。可：pip install playwright && playwright install")
        return False

    url = f"https://item.jd.com/{sku}.html"
    ok = False
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx_kwargs: Dict[str, Any] = {}
        if ua:
            ctx_kwargs["user_agent"] = ua
        if state_file and Path(state_file).exists():
            ctx_kwargs["storage_state"] = str(state_file)

        ctx = browser.new_context(**ctx_kwargs)
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded")

        # 慢慢滚动（更像真人）
        height = page.evaluate("() => document.body.scrollHeight") or 4000
        step_px = max(400, int(height / max(8, scroll_steps)))
        for _ in range(max(1, scroll_steps)):
            page.evaluate(f"window.scrollBy(0,{step_px});")
            page.wait_for_timeout(max(0, pause_ms))
        ok = True
        ctx.close()
        browser.close()
    return ok


def flatten_item(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    把 spider.parse_item 输出的统一结构，拍平成 CSV/JSON 友好格式
    """
    if not parsed:
        return {}

    user = parsed.get("user_info") or {}
    prod = parsed.get("product_info") or {}
    meta = parsed.get("platform_metadata") or {}

    row = {
        "item_id": prod.get("product_id"),
        "platform": parsed.get("source_platform") or parsed.get("source_type") or "jd",
        "rating": prod.get("rating"),
        "content": parsed.get("content"),
        "created_at": parsed.get("created_at"),
        "published_at": parsed.get("published_at"),
        "user_nick": user.get("nickname") or user.get("username"),
        "sku": meta.get("sku") or "",
        "pics": meta.get("pics") or [],
        "sentiment": parsed.get("sentiment"),
        "priority": parsed.get("priority"),
        "quality_score": parsed.get("quality_score"),
    }

    # 追加所有一级字段，避免丢信息
    for k, v in parsed.items():
        if k not in row:
            row[k] = v
    return row


# --------------------------- 主流程 ---------------------------

def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="JD 评论抓取示例（只改 example）")

    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--sku", type=str, help="单个 JD SKU（如 100269926206）")
    group.add_argument("--sku-file", type=str, help="SKU 列表文件（json 数组或 txt 每行一个）")

    ap.add_argument("--days-back", type=int, default=30, help="时间窗口：最近 N 天（默认 30）")
    ap.add_argument("--page-size", type=int, default=20, help="每页条数（默认 20）")

    # === 新增：更保守的默认限速与翻页 ===
    ap.add_argument("--max-pages", type=int, default=20,
                    help="最大翻页数（默认 20）")
    ap.add_argument("--cooldown-ms", type=int, default=3500,
                    help="每次请求后的冷却毫秒（默认 3500，建议 3000–5000）")

    # Playwright 预热参数
    ap.add_argument("--use-playwright", action="store_true", help="预热商品页（降低风控），需安装 playwright")
    ap.add_argument("--scroll-steps", type=int, default=24, help="Playwright 滚动次数（默认 24）")
    ap.add_argument("--pause-ms", type=int, default=1000, help="Playwright 每次滚动后的停顿毫秒（默认 1000）")
    ap.add_argument("--state", type=str, default="", help="Playwright storage_state 路径（如 examples/jd_state.json）")

    # UA 可覆盖
    ap.add_argument("--ua", type=str,
                    default=os.getenv("SPIDER_UA",
                                      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                                      "Chrome/139.0.0.0 Safari/537.36"),
                    help="User-Agent（默认读环境变量 SPIDER_UA 或内置 UA）")

    ap.add_argument("--out-dir", type=str, default="examples/output_jd_comments",
                    help="输出目录（默认 examples/output_jd_comments）")
    return ap


async def run_once_for_sku(
    sku: str,
    args: argparse.Namespace,
    out_dir: Path,
) -> Dict[str, Any]:
    # 可选：Playwright 预热，降低 403/风控
    if args.use_playwright:
        ok = warmup_with_playwright(
            sku=sku,
            ua=args.ua,
            scroll_steps=args.scroll_steps,
            pause_ms=args.pause_ms,
            state_file=Path(args.state) if args.state else None,
        )
        if not ok:
            print("[WARN] Playwright 预热未执行或失败，继续 HTTP 抓取。")

    # 创建 JD 爬虫
    spider = create_ecommerce_spider(
        platform="jd",
        item_id=sku,
        days_back=args.days_back,
        page_size=args.page_size,
        max_pages=args.max_pages,
    )
    # 应用 UA / 限速 / 翻页
    spider.config.headers["User-Agent"] = args.ua
    spider.config.request_delay = max(0.0, args.cooldown_ms / 1000.0)
    spider.config.max_pages = max(1, args.max_pages)

    # 运行
    async with spider:
        result = await spider.run()

    # 解析为平铺结构（CSV 友好）
    flat_rows: List[Dict[str, Any]] = []
    for it in result.data:
        flat_rows.append(flatten_item(it))

    # 输出
    ts = now_tag()
    base = f"jd_comments_{sku}_{ts}"
    out_json = out_dir / f"{base}.json"
    out_csv = out_dir / f"{base}.csv"

    save_json(out_json, flat_rows)
    save_csv(out_csv, flat_rows)

    status = {
        "sku": sku,
        "status": result.status.value if hasattr(result.status, "value") else str(result.status),
        "items": len(flat_rows),
        "req": result.metrics.total_requests if result.metrics else None,
        "ok": result.metrics.successful_requests if result.metrics else None,
    }
    print(f"[INFO] SKU {sku} => status={status.get('status')}, items={status.get('items')}, "
          f"req={status.get('req')}, ok={status.get('ok')}")
    return status


async def main():
    ap = build_argparser()
    args = ap.parse_args()

    # 准备 SKU 列表
    if args.sku:
        sku_list = [args.sku]
    else:
        sku_list = load_sku_list(Path(args.sku_file))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] 将抓取 {len(sku_list)} 个 SKU, UA = {args.ua[:80]}{'...' if len(args.ua)>80 else ''}")
    statuses = []
    for sku in sku_list:
        try:
            st = await run_once_for_sku(sku, args, out_dir)
            statuses.append(st)
        except Exception as e:
            print(f"[ERROR] SKU {sku} 失败：{e}")

        # 批量任务之间也稍作停顿，进一步稳一点
        time.sleep(max(0.5, args.cooldown_ms / 1000.0))

    # 汇总保存
    summary_path = out_dir / f"jd_batch_{now_tag()}.json"
    save_json(summary_path, statuses)


if __name__ == "__main__":
    asyncio.run(main())
