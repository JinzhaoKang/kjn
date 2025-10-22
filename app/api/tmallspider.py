# -*- coding: utf-8 -*-
"""
Ecommerce Spider Pack(单文件整合版)
- 统一的 EcommerceSpider(支持 tmall / jd,预留 pdd / douyin_mall)
- 平台 Driver(构造 headers/url/解析/规整)
- 适配器(映射为 FeedbackData)
- FastAPI 路由：/api/v1/spider/ecommerce/quick-run-with-import
- 兼容：若项目内已存在 BaseSpider/SpiderResult/FeedbackData/DataSourceType,会优先使用项目内实现
"""

from __future__ import annotations
import os
import re
import json
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Protocol

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# ==============================
# 兼容导入（若你项目已有这些类，会优先使用项目版本）
# ==============================
try:
    # 你的项目里若导出 BaseSpider/SpiderResult（通常在 services/spider 下）
    from app.services.spider.base import BaseSpider, SpiderResult   # 如果路径不同，请改为你的真实路径
except Exception:
    # 兜底：最小可用的 BaseSpider/SpiderResult
    @dataclass
    class SpiderResult:
        success: bool
        data: List[Dict[str, Any]]
        errors: List[str]
        pages_crawled: int = 0
        execution_time: Optional[float] = None

    class BaseSpider:
        """最小可用基类（支持暂停/停止、上下文管理）"""
        def __init__(self, config: Any):
            self.config = config
            self._stop = False
            self._pause = False

        def should_stop(self) -> bool:
            return self._stop

        def should_pause(self) -> bool:
            return self._pause

        def stop(self) -> None:
            self._stop = True

        def pause(self) -> None:
            self._pause = True

        def resume(self) -> None:
            self._pause = False

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

try:
    # 你的项目里的数据模型
    from app.models.data_source import FeedbackData, DataSourceType   # 若路径不同，请替换为真实路径
except Exception:
    # 兜底：最小可用的数据模型（仅保证运行不报错）
    class DataSourceType:
        TMALL = "tmall"
        JINGDONG = "jd"
        PINDUODUO = "pdd"
        DOUYIN_MALL = "douyin_mall"
    @dataclass
    class FeedbackData:
        content: str
        source_type: Any
        source_platform: str
        created_at: Any
        user_info: Dict[str, Any]
        product_info: Dict[str, Any]
        custom_fields: Dict[str, Any]
        async def insert(self):  # 占位：若你项目里是 ORM，这里会被真正实现替代
            return

# 尝试导入你现有的管道与管理器（存在就用，不存在就略过）
try:
    from app.services.data_pipeline.data_pipeline_manager import data_pipeline_manager
except Exception:
    data_pipeline_manager = None

try:
    from app.services.spider import get_spider_manager  # 若你打算走统一 SpiderManager
except Exception:
    get_spider_manager = None


# ==============================
# 公共配置 & 工具
# ==============================
SUPPORTED_PLATFORMS = {"tmall", "jd", "pdd", "douyin_mall"}

@dataclass
class EcommerceConfig:
    platform: str
    item_id: str
    days_back: int = 30
    max_pages: int = 10
    page_size: int = 20
    start_date: Optional[str] = None   # "YYYY-MM-DD"
    end_date: Optional[str] = None     # "YYYY-MM-DD"
    since: Optional[str] = None        # ISO8601 e.g. "2025-08-01T00:00:00Z"
    spider_name: str = "ecommerce"

def _strip_jsonp(text: str) -> str:
    m = re.match(r'^\s*[\w$]+\s*\((.*)\)\s*;?\s*$', text, flags=re.S)
    return m.group(1) if m else text

def _parse_dt(s: str) -> Optional[datetime]:
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None

def _in_range(ts: Optional[datetime],
              start: Optional[datetime],
              end: Optional[datetime],
              since: Optional[datetime]) -> bool:
    if ts is None:
        return True
    if since and ts <= since:
        return False
    if start and ts < start:
        return False
    if end and ts >= end:
        return False
    return True


# ==============================
# 平台驱动协议 & 实现
# ==============================
class PlatformDriver(Protocol):
    name: str
    def build_headers(self, item_id: str) -> Dict[str, str]: ...
    def build_url_and_params(self, item_id: str, page: int, page_size: int) -> Tuple[str, Dict[str, Any]]: ...
    def parse_records(self, raw_text: str) -> List[Dict[str, Any]]: ...
    def normalize_record(self, r: Dict[str, Any], item_id: str) -> Dict[str, Any]: ...
    def is_end_by_page(self, records: List[Dict[str, Any]]) -> bool: ...


class TmallDriver:
    name = "tmall"
    RATES_URL = "https://rate.tmall.com/list_detail_rate.htm"
    def __init__(self) -> None:
        self.cookie = os.getenv("TMALL_COOKIE", "")
        self.ua = os.getenv("SPIDER_UA", (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ))
    def build_headers(self, item_id: str) -> Dict[str, str]:
        return {
            "User-Agent": self.ua,
            "Referer": f"https://detail.tmall.com/item.htm?id={item_id}",
            "Cookie": self.cookie,
            "Accept": "*/*",
        }
    def build_url_and_params(self, item_id: str, page: int, page_size: int) -> Tuple[str, Dict[str, Any]]:
        callback = f"jsonp_{int(datetime.now().timestamp())}_{page}"
        params = {
            "itemId": item_id,
            "order": "3",
            "currentPage": page,
            "pageSize": page_size,
            "folded": "0",
            "callback": callback,
        }
        return self.RATES_URL, params
    def parse_records(self, raw_text: str) -> List[Dict[str, Any]]:
        j = json.loads(_strip_jsonp(raw_text))
        rate_list = (j.get("rateDetail", {}) or {}).get("rateList") or j.get("rateList") or []
        return rate_list
    def normalize_record(self, r: Dict[str, Any], item_id: str) -> Dict[str, Any]:
        return {
            "content": r.get("rateContent", "") or r.get("content", ""),
            "rating": r.get("auctionSkuRate", {}).get("star") or r.get("star"),
            "user_nick": r.get("displayUserNick") or r.get("nick"),
            "sku": r.get("auctionSku"),
            "rate_id": r.get("id") or r.get("rateId"),
            "item_id": item_id,
            "created_at": r.get("rateDate") or r.get("date"),
            "append": r.get("appendComment"),
            "pics": r.get("pics") or [],
        }
    def is_end_by_page(self, records: List[Dict[str, Any]]) -> bool:
        return False  # 没有明确 hasMore 时，靠 max_pages 控制


class JDDriver:
    name = "jd"
    COMMENTS_URL = "https://club.jd.com/comment/productPageComments.action"
    def __init__(self) -> None:
        self.cookie = os.getenv("JD_COOKIE", "")
        self.ua = os.getenv("SPIDER_UA", (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ))
    def build_headers(self, item_id: str) -> Dict[str, str]:
        return {
            "User-Agent": self.ua,
            "Referer": f"https://item.jd.com/{item_id}.html",
            "Cookie": self.cookie,
            "Accept": "*/*",
        }
    def build_url_and_params(self, item_id: str, page: int, page_size: int) -> Tuple[str, Dict[str, Any]]:
        callback = f"fetchJSON_comment98_{int(datetime.now().timestamp())}"
        params = {
            "callback": callback,
            "productId": item_id,
            "score": 0,
            "sortType": 5,
            "page": page - 1,   # JD 从 0 开始
            "pageSize": page_size,
            "isShadowSku": 0,
            "fold": 1,
        }
        return self.COMMENTS_URL, params
    def parse_records(self, raw_text: str) -> List[Dict[str, Any]]:
        j = json.loads(_strip_jsonp(raw_text))
        return j.get("comments") or []
    def normalize_record(self, r: Dict[str, Any], item_id: str) -> Dict[str, Any]:
        return {
            "content": r.get("content", ""),
            "rating": r.get("score"),
            "user_nick": r.get("nickname"),
            "sku": r.get("productColor") or r.get("productSize"),
            "rate_id": r.get("id"),
            "item_id": item_id,
            "created_at": r.get("creationTime"),
            "append": r.get("afterUserComment", {}).get("content") if r.get("afterUserComment") else None,
            "pics": [img.get("imgUrl") for img in (r.get("images") or []) if img.get("imgUrl")],
        }
    def is_end_by_page(self, records: List[Dict[str, Any]]) -> bool:
        return not records


class PDDDriver:
    name = "pdd"
    # TODO: 按你们合规可用的接口/页面补齐
    def __init__(self) -> None:
        self.cookie = os.getenv("PDD_COOKIE", "")
        self.ua = os.getenv("SPIDER_UA", "Mozilla/5.0")
    def build_headers(self, item_id: str) -> Dict[str, str]:
        return {"User-Agent": self.ua, "Cookie": self.cookie}
    def build_url_and_params(self, item_id: str, page: int, page_size: int) -> Tuple[str, Dict[str, Any]]:
        url = "https://example.pinduoduo.com/comments"
        params = {"goods_id": item_id, "page": page, "page_size": page_size}
        return url, params
    def parse_records(self, raw_text: str) -> List[Dict[str, Any]]:
        try:
            return json.loads(raw_text).get("comments") or []
        except Exception:
            return []
    def normalize_record(self, r: Dict[str, Any], item_id: str) -> Dict[str, Any]:
        return {
            "content": r.get("content", ""),
            "rating": r.get("rating"),
            "user_nick": r.get("nickname"),
            "sku": r.get("sku"),
            "rate_id": r.get("comment_id"),
            "item_id": item_id,
            "created_at": r.get("created_at"),
            "append": r.get("append"),
            "pics": r.get("images") or [],
        }
    def is_end_by_page(self, records: List[Dict[str, Any]]) -> bool:
        return not records


class DouyinMallDriver:
    name = "douyin_mall"
    # TODO: 按你们合规可用的接口/页面补齐
    def __init__(self) -> None:
        self.cookie = os.getenv("DOUYIN_COOKIE", "")
        self.ua = os.getenv("SPIDER_UA", "Mozilla/5.0")
    def build_headers(self, item_id: str) -> Dict[str, str]:
        return {"User-Agent": self.ua, "Cookie": self.cookie}
    def build_url_and_params(self, item_id: str, page: int, page_size: int) -> Tuple[str, Dict[str, Any]]:
        url = "https://example.douyin.com/mall/comments"
        params = {"product_id": item_id, "page": page, "page_size": page_size}
        return url, params
    def parse_records(self, raw_text: str) -> List[Dict[str, Any]]:
        try:
            return json.loads(raw_text).get("comments") or []
        except Exception:
            return []
    def normalize_record(self, r: Dict[str, Any], item_id: str) -> Dict[str, Any]:
        return {
            "content": r.get("content", ""),
            "rating": r.get("rating"),
            "user_nick": r.get("user_nick") or r.get("nickname"),
            "sku": r.get("sku"),
            "rate_id": r.get("cid") or r.get("comment_id"),
            "item_id": item_id,
            "created_at": r.get("created_at"),
            "append": r.get("append"),
            "pics": r.get("images") or [],
        }
    def is_end_by_page(self, records: List[Dict[str, Any]]) -> bool:
        return not records


DRIVERS: Dict[str, PlatformDriver] = {
    "tmall": TmallDriver(),
    "jd": JDDriver(),
    "pdd": PDDDriver(),
    "douyin_mall": DouyinMallDriver(),
}


# ==============================
# 统一的 EcommerceSpider
# ==============================
class EcommerceSpider(BaseSpider):
    def __init__(self, config: EcommerceConfig):
        super().__init__(config)
        self.config = config
        if self.config.platform not in DRIVERS:
            raise ValueError(f"Unsupported platform: {self.config.platform}")
        self.driver = DRIVERS[self.config.platform]
        self.proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")

    async def run(self) -> SpiderResult:
        start_time = datetime.now(tz=timezone.utc)
        data: List[Dict[str, Any]] = []
        errors: List[str] = []
        pages_crawled = 0

        # 时间窗口
        now = datetime.now(timezone.utc)
        start_dt: Optional[datetime] = None
        end_dt: Optional[datetime] = None
        since_dt: Optional[datetime] = None
        if self.config.start_date:
            start_dt = datetime.fromisoformat(self.config.start_date + "T00:00:00+00:00")
        if self.config.end_date:
            end_dt = datetime.fromisoformat(self.config.end_date + "T00:00:00+00:00")
        if self.config.since:
            since_dt = datetime.fromisoformat(self.config.since)
        if not start_dt and not self.config.since:
            start_dt = now - timedelta(days=self.config.days_back)

        timeout = httpx.Timeout(20.0)
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
        headers = self.driver.build_headers(self.config.item_id)

        async with httpx.AsyncClient(timeout=timeout, limits=limits, proxies=self.proxy) as client:
            for page in range(1, self.config.max_pages + 1):
                if self.should_stop():
                    break
                while self.should_pause():
                    await asyncio.sleep(0.3)
                try:
                    url, params = self.driver.build_url_and_params(
                        self.config.item_id, page, self.config.page_size
                    )
                    text = await self._get_with_retry(client, url, params, headers)
                    raw_records = self.driver.parse_records(text)

                    page_rows: List[Dict[str, Any]] = []
                    for r in raw_records:
                        row = self.driver.normalize_record(r, self.config.item_id)
                        ts = _parse_dt(row.get("created_at"))
                        if _in_range(ts, start_dt, end_dt, since_dt):
                            page_rows.append(row)

                    data.extend(page_rows)
                    pages_crawled += 1

                    if self.driver.is_end_by_page(raw_records):
                        break

                    await asyncio.sleep(0.4)  # 轻限流
                except Exception as e:
                    errors.append(f"page={page}: {e}")
                    await asyncio.sleep(1.0)

        duration = (datetime.now(tz=timezone.utc) - start_time).total_seconds()
        return SpiderResult(
            success=len(errors) == 0,
            data=data,
            errors=errors,
            pages_crawled=pages_crawled,
            execution_time=duration,
        )

    async def _get_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: Dict[str, Any],
        headers: Dict[str, str],
        max_retry: int = 3,
        backoff: float = 0.8,
    ) -> str:
        last_err: Optional[Exception] = None
        for i in range(max_retry):
            try:
                resp = await client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                return resp.text
            except Exception as e:
                last_err = e
                await asyncio.sleep(backoff * (2 ** i))
        raise last_err if last_err else RuntimeError("unknown http error")


# ==============================
# 适配器（把 Spider 的规范化记录 -> FeedbackData）
# ==============================
class _BaseAdapter:
    source_type: Any = None
    def transform(self, raw: dict) -> FeedbackData:
        raise NotImplementedError
    def validate_data(self, fb: FeedbackData) -> bool:
        return bool(fb.content and fb.created_at)

class TmallAdapter(_BaseAdapter):
    source_type = getattr(DataSourceType, "TMALL", "tmall")
    def transform(self, raw: dict) -> FeedbackData:
        return FeedbackData(
            content = raw.get("content", ""),
            source_type = self.source_type,
            source_platform = "tmall",
            created_at = raw.get("created_at"),
            user_info = {"nickname": raw.get("user_nick")},
            product_info = {
                "item_id": raw.get("item_id"),
                "sku": raw.get("sku"),
                "rating": raw.get("rating"),
            },
            custom_fields = {
                "rate_id": raw.get("rate_id"),
                "pics": raw.get("pics", []),
                "append": raw.get("append"),
            }
        )

class JDAdapter(_BaseAdapter):
    source_type = getattr(DataSourceType, "JINGDONG", "jd")
    def transform(self, raw: dict) -> FeedbackData:
        return FeedbackData(
            content = raw.get("content", ""),
            source_type = self.source_type,
            source_platform = "jd",
            created_at = raw.get("created_at"),
            user_info = {"nickname": raw.get("user_nick")},
            product_info = {
                "item_id": raw.get("item_id"),
                "sku": raw.get("sku"),
                "rating": raw.get("rating"),
            },
            custom_fields = {
                "rate_id": raw.get("rate_id"),
                "pics": raw.get("pics", []),
                "append": raw.get("append"),
            }
        )

class PDDAdapter(_BaseAdapter):
    source_type = getattr(DataSourceType, "PINDUODUO", "pdd")
    def transform(self, raw: dict) -> FeedbackData:
        return FeedbackData(
            content = raw.get("content", ""),
            source_type = self.source_type,
            source_platform = "pdd",
            created_at = raw.get("created_at"),
            user_info = {"nickname": raw.get("user_nick")},
            product_info = {
                "item_id": raw.get("item_id"),
                "sku": raw.get("sku"),
                "rating": raw.get("rating"),
            },
            custom_fields = {
                "rate_id": raw.get("rate_id"),
                "pics": raw.get("pics", []),
                "append": raw.get("append"),
            }
        )

class DouyinAdapter(_BaseAdapter):
    source_type = getattr(DataSourceType, "DOUYIN_MALL", "douyin_mall")
    def transform(self, raw: dict) -> FeedbackData:
        return FeedbackData(
            content = raw.get("content", ""),
            source_type = self.source_type,
            source_platform = "douyin_mall",
            created_at = raw.get("created_at"),
            user_info = {"nickname": raw.get("user_nick")},
            product_info = {
                "item_id": raw.get("item_id"),
                "sku": raw.get("sku"),
                "rating": raw.get("rating"),
            },
            custom_fields = {
                "rate_id": raw.get("rate_id"),
                "pics": raw.get("pics", []),
                "append": raw.get("append"),
            }
        )

ADAPTERS_BY_PLATFORM = {
    "tmall": TmallAdapter(),
    "jd": JDAdapter(),
    "pdd": PDDAdapter(),
    "douyin_mall": DouyinAdapter(),
}


# ==============================
# 快速调用（直接创建并运行 Spider，不依赖 SpiderManager 也可用）
# ==============================
async def run_ecommerce_spider_once(settings: Dict[str, Any]) -> Dict[str, Any]:
    cfg = EcommerceConfig(
        platform=settings["platform"],
        item_id=settings["item_id"],
        days_back=settings.get("days_back", 30),
        max_pages=settings.get("max_pages", 10),
        page_size=settings.get("page_size", 20),
        start_date=settings.get("start_date"),
        end_date=settings.get("end_date"),
        since=settings.get("since"),
    )
    async with EcommerceSpider(cfg) as spider:
        result = await spider.run()
    return {
        "success": result.success,
        "data": result.data,
        "errors": result.errors,
        "pages_crawled": result.pages_crawled,
        "execution_time": result.execution_time,
    }


# ==============================
# FastAPI 路由（可直接 include）
# ==============================
class QuickRunPayload(BaseModel):
    platform: str = Field(..., description="tmall | jd | pdd | douyin_mall")
    item_id: str = Field(..., description="商品ID，不是名称")
    days_back: int = Field(30, ge=1, le=3650)
    max_pages: int = Field(10, ge=1, le=1000)
    page_size: int = Field(20, ge=1, le=100)
    start_date: Optional[str] = None   # YYYY-MM-DD
    end_date: Optional[str] = None     # YYYY-MM-DD
    since: Optional[str] = None        # ISO8601

ecommerce_router = APIRouter(prefix="/api/v1/spider", tags=["爬虫管理"])

@ecommerce_router.post("/ecommerce/quick-run-with-import")
async def ecommerce_quick_run_with_import(payload: QuickRunPayload):
    if payload.platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {payload.platform}")

    # 1) 运行蜘蛛
    spider_result = await run_ecommerce_spider_once(payload.dict())

    if not spider_result.get("success"):
        # 失败也返回错误详情，方便排查
        raise HTTPException(status_code=500, detail={
            "message": "抓取失败",
            "errors": spider_result.get("errors", [])
        })

    raw_data = spider_result.get("data", [])
    if not raw_data:
        return {
            "message": "爬取完成，但没有获取到数据",
            "spider": "ecommerce",
            "platform": payload.platform,
            "item_id": payload.item_id,
            "data_count": 0,
            "timestamp": datetime.now().isoformat()
        }

    # 2) 适配为 FeedbackData 并入库（如你的项目有 data_pipeline_manager，则直接用它）
    inserted = 0
    failed = 0
    errs: List[str] = []
    adapter = ADAPTERS_BY_PLATFORM[payload.platform]

    if data_pipeline_manager:
        # 直接用你现有的数据管道批处理（效率更高）
        processing_result = await data_pipeline_manager.process_spider_data(
            spider_data=raw_data,
            task_metadata={
                "spider": "ecommerce",
                "platform": payload.platform,
                "item_id": payload.item_id,
                "crawl_time": datetime.now().isoformat()
            },
            enable_ai_analysis=True
        )
        return {
            "message": "爬取和数据处理完成",
            "spider": "ecommerce",
            "platform": payload.platform,
            "item_id": payload.item_id,
            "spider_result": {
                "data_count": len(raw_data),
                "pages_crawled": spider_result.get("pages_crawled", 0),
                "execution_time": spider_result.get("execution_time"),
            },
            "pipeline_result": processing_result,
            "timestamp": datetime.now().isoformat()
        }
    else:
        # 没有数据管道也能工作：逐条 transform + insert（演示用途）
        for r in raw_data:
            try:
                fb = adapter.transform(r)
                if not adapter.validate_data(fb):
                    failed += 1
                    continue
                await fb.insert()  # 你的 ORM/ODM 会真正入库
                inserted += 1
            except Exception as e:
                failed += 1
                errs.append(str(e))

        return {
            "message": "爬取完成（未接入管道，已逐条入库）",
            "spider": "ecommerce",
            "platform": payload.platform,
            "item_id": payload.item_id,
            "spider_result": {
                "data_count": len(raw_data),
                "pages_crawled": spider_result.get("pages_crawled", 0),
                "execution_time": spider_result.get("execution_time"),
            },
            "insert_summary": {
                "inserted": inserted,
                "failed": failed,
                "errors": errs[:10],
            },
            "timestamp": datetime.now().isoformat()
        }


# ==============================
# （可选）注册到你现有的 SpiderManager
# ==============================
def register_ecommerce_spider(spider_registry: Dict[str, Any]) -> None:
    """
    若你在 SpiderManager 里用 dict registry（和 Qimai 一样），调用：
        from app.extensions.ecommerce_spider_pack import register_ecommerce_spider
        register_ecommerce_spider(spider_registry)
    """
    def factory(settings: Dict[str, Any]) -> EcommerceSpider:
        cfg = EcommerceConfig(
            platform=settings["platform"],
            item_id=settings["item_id"],
            days_back=settings.get("days_back", 30),
            max_pages=settings.get("max_pages", 10),
            page_size=settings.get("page_size", 20),
            start_date=settings.get("start_date"),
            end_date=settings.get("end_date"),
            since=settings.get("since"),
        )
        return EcommerceSpider(cfg)
    spider_registry["ecommerce"] = factory