# -*- coding: utf-8 -*-
"""
Ecommerce Spider (JD/Tmall)
- 这里主要实现了 JD 评论抓取（JSONP + Playwright 兜底）
- 兼容你的 BaseSpider：使用 _stop_flag/_pause_flag，不引用 should_stop()
- Python 3.8 兼容（无 '|' 类型注解）
"""

import os
import re
import json
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, AsyncGenerator, List

from .base_spider import BaseSpider, SpiderConfig, DataSourcePlatform


def _strip_jsonp(text):
    """去掉 JSONP 包裹"""
    m = re.match(r'^\s*[\w$]+\s*\((.*)\)\s*;?\s*$', text, flags=re.S)
    return m.group(1) if m else text


def _parse_dt(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None


class EcommerceSpider(BaseSpider):
    """电商评论爬虫（目前重点实现 JD）"""

    def __init__(self, config=None):
        if config is None:
            config = self._get_default_config()
        super(EcommerceSpider, self).__init__(config)

    # ---------- 构造 & 默认配置 ----------
    @classmethod
    def _get_default_config(cls):
        ua = os.getenv(
            "SPIDER_UA",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        )
        return SpiderConfig(
            spider_name="ecommerce_spider",
            platform=DataSourcePlatform.JD,  # 默认 JD
            base_url="",
            headers={
                "Accept": "*/*",
                "User-Agent": ua,
                "Connection": "keep-alive",
            },
            cookies={},           # 不使用 dict cookie，必要 cookie 放 headers["Cookie"]
            timeout=25,
            max_concurrent=3,
            request_delay=0.5,
            retry_times=2,
            retry_delay=1.0,
            max_pages=20
        )

    # -------- 工厂：JD --------
    @classmethod
    def create_for_jd(cls,
                      product_id,
                      days_back=30,
                      page_size=20,
                      max_pages=20,
                      use_playwright=False,
                      state_path=None,
                      ua_override=None):
        cfg = cls._get_default_config()
        cfg.platform = DataSourcePlatform.JD

        if ua_override:
            cfg.headers["User-Agent"] = ua_override

        # login cookie 若走 HTTP 可放入
        jd_cookie = os.getenv("JD_COOKIE", "")
        if jd_cookie:
            cfg.headers["Cookie"] = jd_cookie

        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days_back)
        cfg.custom_params = {
            "platform": "jd",
            "product_id": str(product_id),
            "page_size": int(page_size),
            "start_date": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "use_playwright": bool(use_playwright),
            "state_path": state_path,
            "ua_override": ua_override,
        }
        cfg.max_pages = int(max_pages)
        return cls(cfg)

    # -------- 工厂：Tmall（占位，后续再完善）--------
    @classmethod
    def create_for_tmall(cls,
                         item_id,
                         days_back=30,
                         page_size=20,
                         max_pages=20,
                         ua_override=None):
        cfg = cls._get_default_config()
        cfg.platform = DataSourcePlatform.TMALL
        if ua_override:
            cfg.headers["User-Agent"] = ua_override
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days_back)
        cfg.custom_params = {
            "platform": "tmall",
            "item_id": str(item_id),
            "page_size": int(page_size),
            "start_date": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
        }
        cfg.max_pages = int(max_pages)
        return cls(cfg)

    # ---------- 生命周期 ----------
    async def custom_initialize(self):
        plat = self.config.custom_params.get("platform")
        if plat not in ("jd", "tmall"):
            raise ValueError("不支持的平台: %s" % plat)
        if plat == "jd":
            for k in ("product_id", "start_date", "end_date", "page_size"):
                if k not in self.config.custom_params:
                    raise ValueError("缺少必要参数: %s" % k)

    async def custom_cleanup(self):
        return

    # ---------- 低层：取文本（为 JSONP 服务） ----------
    async def _get_text(self, url, method="GET", params=None):
        self.metrics.total_requests += 1
        params = params or {}
        for attempt in range(self.config.retry_times + 1):
            try:
                if self.session is not None:
                    async with self.session.request(
                        method=method,
                        url=url,
                        params=params,
                        headers=self.config.headers,
                        timeout=self.config.timeout
                    ) as resp:
                        text = await resp.text()
                        if resp.status == 200:
                            self.metrics.successful_requests += 1
                            return text
                        else:
                            self.logger.warning("HTTP %s: %s", resp.status, url)
                else:
                    import requests
                    r = requests.request(
                        method=method, url=url, params=params,
                        headers=self.config.headers, timeout=self.config.timeout
                    )
                    if r.status_code == 200:
                        self.metrics.successful_requests += 1
                        return r.text
                    else:
                        self.logger.warning("HTTP %s: %s", r.status_code, url)
            except Exception as e:
                self.logger.error("请求异常 (%s/%s): %s",
                                  attempt + 1, self.config.retry_times + 1, e)
            if attempt < self.config.retry_times:
                await asyncio.sleep(self.config.retry_delay)
        self.metrics.failed_requests += 1
        return None

    # ---------- 抓取 ----------
    async def fetch_data(self, **kwargs):
        plat = self.config.custom_params.get("platform")
        if plat == "jd":
            async for r in self._fetch_jd_data():
                yield r
        elif plat == "tmall":
            self.logger.warning("Tmall 抓取尚未实现")
        else:
            self.logger.error("不支持的平台: %s", plat)

    async def _fetch_jd_data(self):
        """JD 评论 JSONP 抓取 + Playwright 兜底"""
        product_id = self.config.custom_params["product_id"]
        page_size = int(self.config.custom_params["page_size"])
        start_dt = _parse_dt(self.config.custom_params["start_date"])
        end_dt = _parse_dt(self.config.custom_params["end_date"])
        max_pages = int(self.config.max_pages)
        use_pw = bool(self.config.custom_params.get("use_playwright"))
        state_path = self.config.custom_params.get("state_path")
        ua_override = self.config.custom_params.get("ua_override")

        base_url = "https://club.jd.com/comment/productPageComments.action"

        async def http_try(page_index):
            callback = "fetchJSON_comment98_%d" % int(datetime.now().timestamp())
            params = {
                "callback": callback,
                "productId": product_id,
                "score": 0,
                "sortType": 5,
                "page": page_index,  # 0-based
                "pageSize": page_size,
                "isShadowSku": 0,
                "fold": 1,
            }
            text = await self._get_text(base_url, "GET", params=params)
            if not text:
                return None
            try:
                j = json.loads(_strip_jsonp(text))
                return j
            except Exception:
                return None

        async def pw_try(page_index):
            try:
                from playwright.async_api import async_playwright
            except Exception as e:
                self.logger.warning("Playwright 不可用: %s", e)
                return None

            product_url = "https://item.jd.com/%s.html" % product_id

            # 启动参数：代理/Chrome渠道
            proxy_server = os.getenv("PLAYWRIGHT_PROXY")
            launch_kwargs = {"headless": True}
            if proxy_server:
                launch_kwargs["proxy"] = {"server": proxy_server}
            channel = os.getenv("PLAYWRIGHT_CHANNEL")
            if channel:
                launch_kwargs["channel"] = channel  # e.g., "chrome"

            # 延迟参数（毫秒）
            low = int(os.getenv("JD_DELAY_MIN_MS", "2000"))
            high = int(os.getenv("JD_DELAY_MAX_MS", "5000"))
            if low > high:
                low, high = 2000, 5000

            async with async_playwright() as pw:
                browser = await pw.chromium.launch(**launch_kwargs)

                context_kwargs = {}
                # 覆盖 UA
                if ua_override:
                    context_kwargs["user_agent"] = ua_override
                # 登录态
                if state_path and os.path.exists(state_path):
                    try:
                        context_kwargs["storage_state"] = state_path
                    except Exception:
                        pass

                ctx = await browser.new_context(**context_kwargs)
                page = await ctx.new_page()

                await page.goto(product_url, wait_until="domcontentloaded")

                # 在页面里注入 JSONP（script 标签方式，无 CORS 问题）
                callback = "jsonp_cb_%d" % int(datetime.now().timestamp())
                jsonp_url = (
                    "https://club.jd.com/comment/productPageComments.action?"
                    f"callback={callback}&productId={product_id}&score=0&sortType=5&"
                    f"page={page_index}&pageSize={page_size}&isShadowSku=0&fold=1"
                )
                js = """
                (url, cbName, timeoutMs) => {
                    return new Promise((resolve, reject) => {
                        let timer = setTimeout(() => {
                            reject(new Error("jsonp_timeout"));
                        }, timeoutMs || 8000);
                        window[cbName] = function(data) {
                            try { clearTimeout(timer); } catch(e) {}
                            resolve(data);
                            delete window[cbName];
                        };
                        const s = document.createElement('script');
                        s.src = url;
                        s.onerror = () => {
                            try { clearTimeout(timer); } catch(e) {}
                            reject(new Error("jsonp_error"));
                        };
                        document.head.appendChild(s);
                    });
                }
                """
                data = None
                try:
                    data = await page.evaluate(js, jsonp_url, callback, 8000)
                except Exception as e:
                    self.logger.warning("JD/Playwright 异常: %s", e)

                # 限速（带随机抖动）
                await page.wait_for_timeout(random.randint(low, high))

                await ctx.close()
                await browser.close()
                return data

        for page in range(0, max_pages):  # JD 从 0 开始
            if self._stop_flag:
                self.logger.info("收到停止信号，终止")
                break
            while self._pause_flag and not self._stop_flag:
                await asyncio.sleep(0.25)

            # 先 HTTP
            j = await http_try(page)
            source = "HTTP"

            # HTTP 失败再走 PW
            if (not j) and use_pw:
                j = await pw_try(page)
                source = "Playwright"

            if not j:
                self.logger.warning("JD/HTTP 解析 JSONP 失败，准备尝试 %s", "Playwright" if use_pw else "结束")
                if not use_pw:
                    break

            # 解析
            comments = []
            try:
                comments = j.get("comments") or []
            except Exception:
                comments = []

            if not comments:
                self.logger.info("JD/%s 页 %s 无评论或被风控，结束", source, page)
                break

            for r in comments:
                dt = _parse_dt(r.get("creationTime"))
                if start_dt and dt and dt < start_dt:
                    continue
                if end_dt and dt and dt > end_dt:
                    continue
                r["_platform"] = "jd"
                r["_product_id"] = product_id
                yield r

    # ---------- 解析统一结构 ----------
    def parse_item(self, raw):
        try:
            plat = raw.get("_platform") or self.config.custom_params.get("platform")
            if plat == "jd":
                content = raw.get("content", "")
                rating = raw.get("score", 0)
                user_nick = raw.get("nickname", "")
                sku = raw.get("productColor") or raw.get("productSize")
                rate_id = raw.get("id")
                created_at = _parse_dt(raw.get("creationTime"))

                parsed = {
                    'source_type': 'jd',
                    'source_platform': 'JD',
                    'original_id': rate_id,
                    'url': None,

                    'title': '',
                    'content': content,
                    'content_type': 'text',
                    'language': 'zh',

                    'created_at': created_at,
                    'published_at': created_at,
                    'crawled_at': datetime.now(),

                    'user_info': {
                        'user_id': None,
                        'nickname': user_nick,
                        'username': user_nick,
                        'is_verified': False
                    },

                    'product_info': {
                        'product_id': self.config.custom_params.get("product_id"),
                        'product_name': None,
                        'category': 'Ecommerce',
                        'rating': rating
                    },

                    'platform_metadata': {
                        'post_id': rate_id,
                        'likes_count': 0,
                        'is_pinned': False,
                        'tags': [],
                        'sku': sku,
                        'pics': [img.get("imgUrl") for img in (raw.get("images") or []) if img.get("imgUrl")]
                    },

                    'sentiment': self._determine_sentiment(int(rating) if rating is not None else 0),
                    'priority': self._calculate_priority(int(rating) if rating is not None else 0, content),
                    'category': None,
                    'keywords': [],

                    'geographical_info': {
                        'country_code': 'CN',
                        'country_name': '中国',
                        'region_code': 'EAST_ASIA',
                        'detected_language': 'zh',
                        'detection_confidence': 0.8,
                        'detection_method': 'platform_default'
                    },

                    'processing_status': {
                        'is_processed': False,
                        'ai_confidence': None,
                        'human_reviewed': False
                    },

                    'quality_score': self._assess_quality('', content),

                    'custom_fields': {
                        'ecommerce': {
                            'platform': 'jd'
                        }
                    },

                    'data_lineage': {
                        'source': 'jd',
                        'collection_method': 'web_spider',
                        'collection_time': datetime.now().isoformat(),
                        'spider_version': '1.1'
                    }
                }
                return parsed

            elif plat == "tmall":
                # 占位：后续完善
                return None

            else:
                self.logger.error("未知平台: %s", plat)
                return None

        except Exception as e:
            self.logger.error("解析失败: %s", e)
            return None

    # 小工具
    def _determine_sentiment(self, rating):
        try:
            rating = int(rating)
        except Exception:
            rating = 0
        if rating >= 4:
            return "positive"
        elif rating <= 2:
            return "negative"
        else:
            return "neutral"

    def _calculate_priority(self, rating, content):
        try:
            rating = int(rating)
        except Exception:
            rating = 0
        text = content or ""
        if rating <= 2 and len(text) > 50:
            return "high"
        elif rating <= 2 or len(text) > 100:
            return "medium"
        else:
            return "low"

    def _assess_quality(self, title, body):
        score = 0.5
        if title and len(title.strip()) > 2:
            score += 0.2
        content_length = len((body or "").strip())
        if content_length > 10:
            score += 0.1
        if content_length > 50:
            score += 0.1
        if content_length > 100:
            score += 0.1
        if body and not body.isupper():
            score += 0.1
        return min(score, 1.0)


# 便捷工厂
def create_jd_spider(product_id,
                     days_back=30,
                     page_size=20,
                     max_pages=20,
                     use_playwright=False,
                     state_path=None,
                     ua_override=None):
    return EcommerceSpider.create_for_jd(
        product_id=product_id,
        days_back=days_back,
        page_size=page_size,
        max_pages=max_pages,
        use_playwright=use_playwright,
        state_path=state_path,
        ua_override=ua_override
    )
