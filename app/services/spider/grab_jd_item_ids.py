#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
grab_jd_item_ids.py
---------------------------------
从京东店铺/搜索结果/活动页里提取商品 item_id（SKU）。
优先用快速 HTTP 抓取 + 正则；若数据是懒加载或强 JS 渲染，
可加 --use-playwright 用无头浏览器滚动并提取（无需手抄 Cookie）。

依赖：
  pip install httpx  # 或 requests
  # 可选：需要兜底时
  pip install playwright && playwright install
"""
import os, re, sys, json, time, argparse
from typing import List, Set
from urllib.parse import urlparse, parse_qs

try:
    import httpx
except Exception:
    httpx = None
try:
    import requests
except Exception:
    requests = None

ITEM_HREF_RE = re.compile(r'(?:https?:)?//(?:item\.jd\.com|item\.m\.jd\.com)/(\d+)\.html', re.I)
SKU_PARAM_RE = re.compile(r'[?&]sku=(\d+)\b', re.I)
DATA_SKU_RE = re.compile(r'data-sku=["\'](\d+)["\']', re.I)
DATA_SKUID_RE = re.compile(r'data-skuid=["\'](\d+)["\']', re.I)
JSON_SKUID_RE = re.compile(r'"skuId"\s*:\s*"(\d+)"', re.I)
JSON_SKU_RE = re.compile(r'"sku"\s*:\s*"(\d+)"', re.I)

def _log(msg: str): print(msg, file=sys.stderr)

def _headers(base_url: str, ua: str) -> dict:
    ua = ua or os.getenv("SPIDER_UA", "Mozilla/5.0")
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": base_url,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Connection": "keep-alive",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
    }

def fetch_text(url: str, headers: dict, timeout: float = 15.0) -> str:
    if httpx is not None:
        with httpx.Client(timeout=timeout, follow_redirects=True, http2=True) as client:
            r = client.get(url, headers=headers)
            r.raise_for_status()
            return r.text
    elif requests is not None:
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        return r.text
    else:
        raise RuntimeError("需要安装 httpx 或 requests 其中之一：pip install httpx 或 pip install requests")

def extract_ids_from_html(html: str) -> List[str]:
    ids: List[str] = []
    seen: Set[str] = set()
    for m in ITEM_HREF_RE.finditer(html):
        sku = m.group(1)
        if sku not in seen: seen.add(sku); ids.append(sku)
    for m in SKU_PARAM_RE.finditer(html):
        sku = m.group(1)
        if sku not in seen: seen.add(sku); ids.append(sku)
    for m in DATA_SKU_RE.finditer(html):
        sku = m.group(1)
        if sku not in seen: seen.add(sku); ids.append(sku)
    for m in DATA_SKUID_RE.finditer(html):
        sku = m.group(1)
        if sku not in seen: seen.add(sku); ids.append(sku)
    for m in JSON_SKUID_RE.finditer(html):
        sku = m.group(1)
        if sku not in seen: seen.add(sku); ids.append(sku)
    for m in JSON_SKU_RE.finditer(html):
        sku = m.group(1)
        if sku not in seen: seen.add(sku); ids.append(sku)
    return ids

def scan_simple(base_url: str, pages: int, limit: int, ua: str) -> List[str]:
    headers = _headers(base_url, ua)
    found: List[str] = []; seen: Set[str] = set()
    for i in range(1, max(1, pages) + 1):
        if i == 1:
            url = base_url
        else:
            if "page=" in base_url:
                url = re.sub(r"(?:[?&])page=\d+", lambda _: _.group(0)[:_.group(0).find('=')+1] + str(i), base_url, count=1)
                if url == base_url:
                    sep = "&" if "?" in base_url else "?"
                    url = f"{base_url}{sep}page={i}"
            else:
                sep = "&" if "?" in base_url else "?"
                url = f"{base_url}{sep}page={i}"
        try:
            html = fetch_text(url, headers)
        except Exception as e:
            _log(f"[warn] page {i} request error: {e}")
            continue
        ids = extract_ids_from_html(html)
        _log(f"[info] page {i}: got {len(ids)} ids (before dedupe)")
        for sku in ids:
            if sku not in seen:
                seen.add(sku); found.append(sku)
                if len(found) >= limit: return found
        time.sleep(0.35)
    return found

async def scan_with_playwright(base_url: str, scroll_steps: int, pause_ms: int, limit: int, ua: str) -> List[str]:
    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        raise RuntimeError("未安装 Playwright。请先：pip install playwright && playwright install") from e
    ids: List[str] = []; seen: Set[str] = set()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(user_agent=ua or None)
        page = await ctx.new_page()
        await page.goto(base_url, wait_until="networkidle")
        for _ in range(max(1, scroll_steps)):
            await page.mouse.wheel(0, 2500)
            await page.wait_for_timeout(max(0, pause_ms))
        hrefs: List[str] = await page.eval_on_selector_all("a", "els => els.map(e => e.href).filter(Boolean)")
        for h in hrefs:
            m = ITEM_HREF_RE.search(h)
            if m:
                sku = m.group(1)
                if sku not in seen:
                    seen.add(sku); ids.append(sku)
                    if len(ids) >= limit: break
        if len(ids) < limit:
            ds1 = await page.eval_on_selector_all("[data-sku]", "els => els.map(e => e.getAttribute('data-sku'))")
            ds2 = await page.eval_on_selector_all("[data-skuid]", "els => els.map(e => e.getAttribute('data-skuid'))")
            for val in (ds1 or []) + (ds2 or []):
                if val and val.isdigit() and val not in seen:
                    seen.add(val); ids.append(val)
                    if len(ids) >= limit: break
        if len(ids) < limit:
            html = await page.content()
            more = extract_ids_from_html(html)
            for sku in more:
                if sku not in seen:
                    seen.add(sku); ids.append(sku)
                    if len(ids) >= limit: break
        await browser.close()
    return ids

def main():
    ap = argparse.ArgumentParser(description="从京东页面提取商品 item_id（SKU）")
    ap.add_argument("--url", required=True, help="店铺 / 搜索 / 列表 / 活动页 URL")
    ap.add_argument("--pages", type=int, default=3, help="简单模式：尝试翻多少页（?page=2..N）")
    ap.add_argument("--limit", type=int, default=200, help="最多提取多少个 item_id")
    ap.add_argument("--ua", type=str, default=os.getenv("SPIDER_UA", ""), help="User-Agent（默认读环境变量 SPIDER_UA）")
    ap.add_argument("--use-playwright", action="store_true", help="启用 Playwright 渲染+滚动（需安装）")
    ap.add_argument("--scroll-steps", type=int, default=12, help="Playwright 模式：滚动次数")
    ap.add_argument("--pause-ms", type=int, default=800, help="Playwright 模式：每次滚动后的停顿毫秒数")
    ap.add_argument("--json-out", type=str, default="jd_item_ids.json", help="输出 JSON 文件名")
    ap.add_argument("--txt-out", type=str, default="jd_item_ids.txt", help="输出 TXT 文件名")
    args = ap.parse_args()

    ids = scan_simple(args.url, pages=args.pages, limit=args.limit, ua=args.ua)
    _log(f"[info] simple mode found: {len(ids)}")
    need_pw = args.use_playwright or len(ids) == 0
    if need_pw:
        try:
            import asyncio
            ids2 = asyncio.run(scan_with_playwright(args.url, args.scroll_steps, args.pause_ms, args.limit, args.ua))
            seen = set(ids)
            for sku in ids2:
                if sku not in seen:
                    ids.append(sku); seen.add(sku)
            _log(f"[info] playwright mode added, total: {len(ids)}")
        except Exception as e:
            _log(f"[warn] playwright fallback skipped: {e}")

    dedup, seen = [], set()
    for sku in ids:
        if sku not in seen:
            seen.add(sku); dedup.append(sku)

    print(json.dumps({"count": len(dedup), "item_ids": dedup}, ensure_ascii=False, indent=2))
    try:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(dedup, f, ensure_ascii=False, indent=2)
        with open(args.txt_out, "w", encoding="utf-8") as f:
            f.write("\n".join(dedup))
        _log(f"[ok] saved: %s, %s" % (args.json_out, args.txt_out))
    except Exception as e:
        _log(f"[warn] save files error: {e}")

if __name__ == "__main__":
    main()
