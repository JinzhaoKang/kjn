"""
七麦数据爬虫
专门用于抓取qimai.cn提供的App Store评论数据
"""
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, AsyncGenerator
from urllib.parse import urlencode
import logging

from .base_spider import BaseSpider, SpiderConfig, DataSourcePlatform
from ...models.data_source import DataSourceType, ContentType
from ...models.geographical import get_geographical_manager


class QimaiSpider(BaseSpider):
    """七麦数据爬虫"""
    
    def __init__(self, config: SpiderConfig = None):
        # 如果没有提供配置，使用默认配置
        if config is None:
            config = self._get_default_config()
        
        super().__init__(config)
        self.geo_manager = get_geographical_manager()
        
    @classmethod
    def _get_default_config(cls) -> SpiderConfig:
        """获取默认配置"""
        return SpiderConfig(
            spider_name="qimai_app_store_spider",
            platform=DataSourcePlatform.QIMAI,
            base_url="https://api.qimai.cn",
            headers={
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Origin': 'https://www.qimai.cn',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
                'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"'
            },
            cookies={
                'qm_check': 'A1sdRUIQChtxen8pI0dAOQkKWVIeEHh+c3QgRioNDBgWFWVXXl1VRl0XXEcpCAkWUBd/AhlgRldJRjIGCwkfVl5UWVxUFG4AFBQBFxdTFxsQU1FVV1NHXEVYVElWBRsCHAkSSQ%3D%3D',
                'PHPSESSID': 'u4v2ose3rmgttbqmvv0ibkm0ud',
                'gr_user_id': '28cd5729-85b4-4603-a2a2-481a6cb77c23',
                'USERINFO': 'v0anUWCM0VTu0ZIaG8ySMf4WZCQG5ckUbZPPcljf2RcGD593ojHTrLe2eXbxknMxZNC6PUayAiuj067pvboWZ7CA4ObM17iPIwpmUZlhuIhAS4WLlqN%2F64jJHAXAzDCnL4hhghneJBjAD0P1GW5%2FKQ%3D%3D',
                'AUTHKEY': 'v4Dqm6P9B84rN5MqawT4%2FK6e9w2kxGPJUfF8KspCIf4ejiAjCHKP5weRDxddc5Kx5rbXy24FtiJZdXJqF%2Bp1YuNae4cdyusc32crPDH0oQV6t4m1QxRhBg%3D%3D',
                'ada35577182650f1_gr_last_sent_cs1': 'zhangliugang',
                'ada35577182650f1_gr_session_id': '0e0279bd-8d1d-4e0b-a2cb-2aed36ad5202',
                'ada35577182650f1_gr_last_sent_sid_with_cs1': '0e0279bd-8d1d-4e0b-a2cb-2aed36ad5202',
                'ada35577182650f1_gr_session_id_sent_vst': '0e0279bd-8d1d-4e0b-a2cb-2aed36ad5202',
                'ada35577182650f1_gr_cs1': 'zhangliugang',
                'syncd': '-1038',
                'synct': '1751508747.207'
            },
            timeout=30,
            max_concurrent=3,
            request_delay=2.0,
            retry_times=3,
            max_pages=100
        )
    
    @classmethod
    def create_for_app(cls, 
                      appid: str,
                      country: str = "cn",
                      days_back: int = 365,
                      analysis_key: str = "ezErHicsKEt6dWIUKiVwQSgMNhw1PRlBfHMmAyx9d1MrIylOND50SHonLVB1YiRVKzw5ATNxeE0sDjQMeQ8zUiUSKxBXVgpeJEIWVxUWSAsXFBdQX0MjR1gJB1ZUUV5LT0gFcRRQ",
                      max_pages: int = 100):
        """为特定应用创建爬虫实例 - iOS App Store"""
        config = cls._get_default_config()
        
        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        config.custom_params = {
            'platform': 'ios',
            'appid': appid,
            'country': country,
            'start_date': start_date.strftime("%Y-%m-%d %H:%M:%S"),
            'end_date': end_date.strftime("%Y-%m-%d %H:%M:%S"),
            'analysis_key': analysis_key,
            'keyword': ''
        }
        config.max_pages = max_pages
        
        return cls(config)
    
    @classmethod
    def create_for_android_app(cls,
                              market: str = "6",  # 默认华为（与curl一致）
                              analysis_key: str = "dkZJBgYcGApFHlAGECJWWwgDCRw0EAlBcRRaVFMBA1FfUlpATDoWAg%3D%3D",
                              days_back: int = 90,  # 默认90天时间跨度
                              max_pages: int = 100):
        """为Android应用创建爬虫实例"""
        config = cls._get_default_config()
        
        # Android固定appid
        android_appid = "6007162"
        
        # 计算时间范围（从当前时间往前推指定天数）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # 设置请求头为POST请求
        config.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        
        config.custom_params = {
            'platform': 'android',
            'appid': android_appid,
            'market': market,
            'analysis_key': analysis_key,
            'start_date': start_date.strftime("%Y-%m-%d %H:%M:%S"),
            'end_date': end_date.strftime("%Y-%m-%d %H:%M:%S")
        }
        config.max_pages = max_pages
        
        return cls(config)
    
    async def custom_initialize(self):
        """自定义初始化"""
        self.logger.info("初始化七麦爬虫")
        
        # 验证必要的参数
        platform = self.config.custom_params.get('platform', 'ios')
        
        if platform == 'ios':
            required_params = ['appid', 'country', 'start_date', 'end_date', 'analysis_key']
        elif platform == 'android':
            required_params = ['appid', 'market', 'analysis_key', 'start_date', 'end_date']
        else:
            raise ValueError(f"不支持的平台: {platform}")
            
        for param in required_params:
            if param not in self.config.custom_params:
                raise ValueError(f"缺少必要参数: {param}")
    
    async def custom_cleanup(self):
        """自定义清理"""
        self.logger.info("清理七麦爬虫资源")
    
    async def make_request(self, 
                          url: str, 
                          method: str = "GET",
                          params: Optional[Dict[str, Any]] = None,
                          data: Optional[Dict[str, Any]] = None,
                          **kwargs) -> Optional[Dict[str, Any]]:
        """重写make_request方法，确保cookies正确传递"""
        self.metrics.total_requests += 1
        
        for attempt in range(self.config.retry_times + 1):
            try:
                if self.session is not None:
                    # 使用aiohttp，每次请求都传递cookies
                    async with self.session.request(
                        method=method,
                        url=url,
                        params=params,
                        data=data,
                        cookies=self.config.cookies,  # 显式传递cookies
                        **kwargs
                    ) as response:
                        
                        if response.status == 200:
                            self.metrics.successful_requests += 1
                            
                            # 根据内容类型解析响应
                            content_type = response.headers.get('content-type', '').lower()
                            if 'application/json' in content_type:
                                return await response.json()
                            else:
                                text = await response.text()
                                try:
                                    import json
                                    return json.loads(text)
                                except json.JSONDecodeError:
                                    return {"text": text}
                        
                        else:
                            self.logger.warning(f"HTTP请求失败: {response.status} - {url}")
                else:
                    # 使用requests作为后备
                    import requests
                    
                    response = requests.request(
                        method=method,
                        url=url,
                        params=params,
                        data=data,
                        headers=self.config.headers,
                        cookies=self.config.cookies,
                        timeout=self.config.timeout,
                        **kwargs
                    )
                    
                    if response.status_code == 200:
                        self.metrics.successful_requests += 1
                        
                        try:
                            return response.json()
                        except json.JSONDecodeError:
                            return {"text": response.text}
                    else:
                        self.logger.warning(f"HTTP请求失败: {response.status_code} - {url}")
                        
            except Exception as e:
                self.logger.error(f"请求异常 (尝试 {attempt + 1}/{self.config.retry_times + 1}): {e}")
                
                if attempt < self.config.retry_times:
                    import asyncio
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    self.metrics.failed_requests += 1
                    return None
        
        return None
    
    async def fetch_data(self, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """抓取数据"""
        platform = self.config.custom_params.get('platform', 'ios')
        
        if platform == 'ios':
            async for item in self._fetch_ios_data():
                yield item
        elif platform == 'android':
            async for item in self._fetch_android_data():
                yield item
        else:
            self.logger.error(f"不支持的平台: {platform}")
            return
    
    async def _fetch_ios_data(self) -> AsyncGenerator[Dict[str, Any], None]:
        """抓取iOS App Store数据"""
        self.logger.info("开始抓取七麦App Store评论数据")
        
        # 获取参数
        appid = self.config.custom_params['appid']
        country = self.config.custom_params['country']
        start_date = self.config.custom_params['start_date']
        end_date = self.config.custom_params['end_date']
        analysis_key = self.config.custom_params['analysis_key']
        keyword = self.config.custom_params.get('keyword', '')
        
        # 首先获取总页数
        total_pages = await self._get_ios_total_pages(appid, country, start_date, end_date, analysis_key, keyword)
        if total_pages is None:
            self.logger.error("无法获取总页数")
            return
        
        # 限制最大页数
        max_pages = min(total_pages, self.config.max_pages)
        self.logger.info(f"总共 {total_pages} 页，将抓取前 {max_pages} 页")
        
        # 逐页抓取
        for page in range(1, max_pages + 1):
            self.logger.info(f"抓取第 {page}/{max_pages} 页")
            
            # 构建请求参数
            params = {
                'analysis': analysis_key,
                'appid': appid,
                'country': country,
                'sword': keyword,
                'sdate': start_date,
                'edate': end_date,
                'page': page
            }
            
            # 发起请求
            url = f"{self.config.base_url}/app/comment"
            response_data = await self.make_request(url, method="GET", params=params)
            
            if response_data is None:
                self.logger.error(f"第 {page} 页请求失败")
                continue
            
            # 检查响应状态
            if response_data.get('code') != 10000:
                self.logger.error(f"第 {page} 页API返回错误: {response_data.get('msg', 'Unknown error')}")
                continue
            
            # 提取评论数据
            app_comments = response_data.get('appComments', [])
            self.logger.info(f"第 {page} 页获取到 {len(app_comments)} 条评论")
            
            # 逐个返回评论
            for comment in app_comments:
                yield comment
            
            # 如果当前页没有数据，说明已经到了最后
            if not app_comments:
                self.logger.info("当前页无数据，停止抓取")
                break
    
    async def _fetch_android_data(self) -> AsyncGenerator[Dict[str, Any], None]:
        """抓取Android应用数据"""
        self.logger.info("开始抓取七麦Android应用评论数据")
        
        # 获取参数
        appid = self.config.custom_params['appid']
        market = self.config.custom_params['market']
        analysis_key = self.config.custom_params['analysis_key']
        start_date = self.config.custom_params['start_date']
        end_date = self.config.custom_params['end_date']
        
        self.logger.info(f"时间范围: {start_date} 至 {end_date} (90天跨度)")
        
        # 首先获取总页数
        total_pages = await self._get_android_total_pages(appid, market, analysis_key, start_date, end_date)
        if total_pages is None:
            self.logger.error("无法获取总页数")
            return
        
        # 限制最大页数
        max_pages = min(total_pages, self.config.max_pages)
        self.logger.info(f"总共 {total_pages} 页，将抓取前 {max_pages} 页")
        
        # 逐页抓取
        for page in range(1, max_pages + 1):
            self.logger.info(f"抓取第 {page}/{max_pages} 页")
            
            # 构建POST数据（必须是字符串格式，包含时间范围）
            from urllib.parse import urlencode
            data = urlencode({
                'appid': appid,
                'market': market,
                'page': page,
                'start_date': start_date,
                'end_date': end_date
            })
            
            # 发起请求
            url = f"{self.config.base_url}/andapp/getCommentList"
            response_data = await self.make_request(
                url, 
                method="POST", 
                params={'analysis': analysis_key}, 
                data=data
            )
            
            if response_data is None:
                self.logger.error(f"第 {page} 页请求失败")
                continue
            
            # 检查响应状态
            if response_data.get('code') == 10000:
                # 正常返回数据（七麦Android API返回的是result数组，不是data.list）
                comments = response_data.get('result', [])
                self.logger.info(f"第 {page} 页获取到 {len(comments)} 条评论")
                
                # 逐个返回评论
                for comment in comments:
                    yield comment
                    
                # 如果当前页没有数据，说明已经到了最后
                if not comments:
                    self.logger.info("当前页无数据，停止抓取")
                    break
                    
            elif response_data.get('code') == 10001:
                # 认证失败，返回错误信息
                self.logger.error(f"第 {page} 页认证失败，需要重新登录七麦数据账号")
                raise Exception("七麦数据认证已过期，请重新登录获取新的认证信息")
            else:
                self.logger.error(f"第 {page} 页API返回错误: {response_data.get('msg', 'Unknown error')}")
                continue
    
    async def _get_ios_total_pages(self, 
                                  appid: str, 
                                  country: str, 
                                  start_date: str, 
                                  end_date: str, 
                                  analysis_key: str, 
                                  keyword: str = '') -> Optional[int]:
        """获取iOS总页数"""
        params = {
            'analysis': analysis_key,
            'appid': appid,
            'country': country,
            'sword': keyword,
            'sdate': start_date,
            'edate': end_date,
            'page': 1
        }
        
        url = f"{self.config.base_url}/app/comment"
        response_data = await self.make_request(url, method="GET", params=params)
        
        if response_data and response_data.get('code') == 10000:
            max_page = response_data.get('maxPage', 1)
            comment_count = response_data.get('appCommentCount', 0)
            self.logger.info(f"iOS应用 {appid} 共有 {comment_count} 条评论，{max_page} 页")
            return max_page
        
        return None
    
    async def _get_android_total_pages(self, 
                                      appid: str, 
                                      market: str, 
                                      analysis_key: str,
                                      start_date: str,
                                      end_date: str) -> Optional[int]:
        """获取Android总页数"""
        from urllib.parse import urlencode
        data = urlencode({
            'appid': appid,
            'market': market,
            'page': 1,
            'start_date': start_date,
            'end_date': end_date
        })
        
        url = f"{self.config.base_url}/andapp/getCommentList"
        response_data = await self.make_request(
            url, 
            method="POST", 
            params={'analysis': analysis_key}, 
            data=data
        )
        
        if response_data and response_data.get('code') == 10000:
            # 七麦Android API返回的结构：max_page和total直接在根级别
            max_page = response_data.get('max_page', 1)
            comment_count = response_data.get('total', 0)
            market_name = self._get_market_name(market)
            self.logger.info(f"Android应用 {appid} ({market_name}) 时间范围 {start_date} 至 {end_date} 共有 {comment_count} 条评论，{max_page} 页")
            return max_page
        elif response_data and response_data.get('code') == 10001:
            # 认证失败，抛出异常
            self.logger.error("七麦API认证失败，需要重新登录")
            raise Exception("七麦数据认证已过期，请重新登录获取新的认证信息")
        
        return None
    
    def _get_market_name(self, market: str) -> str:
        """获取应用市场名称"""
        market_names = {
            '4': '小米',
            '6': '华为',
            '7': '魅族', 
            '8': 'vivo',
            '9': 'oppo'
        }
        return market_names.get(market, f'未知市场({market})')
    
    def parse_item(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析评论数据项 - 支持iOS和Android"""
        try:
            platform = self.config.custom_params.get('platform', 'ios')
            
            if platform == 'ios':
                return self._parse_ios_item(raw_data)
            elif platform == 'android':
                return self._parse_android_item(raw_data)
            else:
                self.logger.error(f"不支持的平台: {platform}")
                return None
                
        except Exception as e:
            self.logger.error(f"解析数据项失败: {e}")
            return None
    
    def _parse_ios_item(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析iOS评论数据项"""
        # 提取基础信息
        comment_id = raw_data.get('id')
        rating = raw_data.get('rating', 0)
        date_str = raw_data.get('date', '')
        is_top = raw_data.get('is_top', 0)
        
        # 提取评论详情
        comment_detail = raw_data.get('comment', {})
        user_name = comment_detail.get('name', '')
        title = comment_detail.get('title', '')
        body = comment_detail.get('body', '')
        user_review_id = comment_detail.get('user_review_id', '')
        
        # 解析时间
        created_at = self._parse_date(date_str)
        
        # 判断情感
        sentiment = self._determine_sentiment(rating)
        
        # 构建统一数据格式
        parsed_data = {
            # 基础信息
            'source_type': 'ios_app_store',
            'source_platform': '七麦数据-App Store',
            'original_id': comment_id,
            'url': None,
            
            # 内容信息
            'title': title,
            'content': body,
            'content_type': 'text',
            'language': 'zh',
            
            # 时间信息
            'created_at': created_at,
            'published_at': created_at,
            'crawled_at': datetime.now(),
            
            # 用户信息
            'user_info': {
                'user_id': user_review_id,
                'nickname': user_name,
                'username': None,
                'is_verified': False
            },
            
            # 产品信息
            'product_info': {
                'product_id': self.config.custom_params.get('appid'),
                'product_name': None,
                'category': 'App',
                'rating': rating
            },
            
            # 平台元数据
            'platform_metadata': {
                'post_id': comment_id,
                'likes_count': 0,
                'is_pinned': bool(is_top),
                'tags': []
            },
            
            # AI分析结果
            'sentiment': sentiment,
            'priority': self._calculate_priority(rating, body),
            'category': None,
            'keywords': [],
            
            # 地理位置信息（默认中国）
            'geographical_info': {
                'country_code': 'CN',
                'country_name': '中国',
                'region_code': 'EAST_ASIA',
                'detected_language': 'zh',
                'detection_confidence': 0.8,
                'detection_method': 'platform_default'
            },
            
            # 处理状态
            'processing_status': {
                'is_processed': False,
                'ai_confidence': None,
                'human_reviewed': False
            },
            
            # 质量评估
            'quality_score': self._assess_quality(title, body),
            
            # 扩展字段
            'custom_fields': {
                'qimai_data': {
                    'platform': 'ios',
                    'rating': rating,
                    'is_top': is_top
                }
            },
            
            # 数据血缘
            'data_lineage': {
                'source': 'qimai.cn',
                'collection_method': 'api_spider',
                'collection_time': datetime.now().isoformat(),
                'spider_version': '1.0'
            }
        }
        
        return parsed_data
    
    def _parse_android_item(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析Android评论数据项"""
        # 根据实际Android API返回的字段结构进行映射
        comment_id = raw_data.get('account_id')  # 使用account_id作为唯一标识
        rating = int(raw_data.get('stars', 0))  # Android使用stars字段
        content = raw_data.get('comment_info', '')  # Android使用comment_info字段
        username = raw_data.get('nick_name', '')  # Android使用nick_name字段
        date_str = raw_data.get('comment_time', '')  # Android使用comment_time字段
        
        # 解析时间
        created_at = self._parse_date(date_str)
        
        # 判断情感
        sentiment = self._determine_sentiment(rating)
        
        # 获取应用市场信息
        market = self.config.custom_params.get('market', '4')
        market_name = self._get_market_name(market)
        
        # 根据市场设置具体的source_type
        market_source_types = {
            '4': 'xiaomi_app_store',
            '6': 'huawei_app_store',
            '7': 'meizu_app_store',
            '8': 'vivo_app_store',
            '9': 'oppo_app_store'
        }
        source_type = market_source_types.get(market, 'android_app_store')
        
        # 构建统一数据格式
        parsed_data = {
            # 基础信息
            'source_type': source_type,
            'source_platform': f'七麦数据-{market_name}应用市场',
            'original_id': comment_id,
            'url': None,
            
            # 内容信息
            'title': '',  # Android评论可能没有标题
            'content': content,
            'content_type': 'text',
            'language': 'zh',
            
            # 时间信息
            'created_at': created_at,
            'published_at': created_at,
            'crawled_at': datetime.now(),
            
            # 用户信息
            'user_info': {
                'user_id': None,
                'nickname': username,
                'username': username,
                'is_verified': False
            },
            
            # 产品信息
            'product_info': {
                'product_id': self.config.custom_params.get('appid'),
                'product_name': None,
                'category': 'App',
                'rating': rating
            },
            
            # 平台元数据
            'platform_metadata': {
                'post_id': comment_id,
                'likes_count': 0,
                'is_pinned': False,
                'tags': [],
                'market': market_name
            },
            
            # AI分析结果
            'sentiment': sentiment,
            'priority': self._calculate_priority(rating, content),
            'category': None,
            'keywords': [],
            
            # 地理位置信息（默认中国）
            'geographical_info': {
                'country_code': 'CN',
                'country_name': '中国',
                'region_code': 'EAST_ASIA',
                'detected_language': 'zh',
                'detection_confidence': 0.8,
                'detection_method': 'platform_default'
            },
            
            # 处理状态
            'processing_status': {
                'is_processed': False,
                'ai_confidence': None,
                'human_reviewed': False
            },
            
            # 质量评估
            'quality_score': self._assess_quality('', content),
            
            # 扩展字段
            'custom_fields': {
                'qimai_data': {
                    'platform': 'android',
                    'market': market,
                    'market_name': market_name,
                    'rating': rating
                }
            },
            
            # 数据血缘
            'data_lineage': {
                'source': 'qimai.cn',
                'collection_method': 'api_spider',
                'collection_time': datetime.now().isoformat(),
                'spider_version': '1.0'
            }
        }
        
        return parsed_data
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            self.logger.warning(f"无法解析日期: {date_str}")
            return None
    
    def _determine_sentiment(self, rating: int) -> str:
        """根据评分判断情感"""
        if rating >= 4:
            return "positive"
        elif rating <= 2:
            return "negative"
        else:
            return "neutral"
    
    def _calculate_priority(self, rating: int, content: str) -> str:
        """计算优先级"""
        if rating <= 2 and len(content) > 50:
            return "high"
        elif rating <= 2 or len(content) > 100:
            return "medium"
        else:
            return "low"
    
    def _assess_quality(self, title: str, body: str) -> float:
        """评估内容质量"""
        score = 0.5
        
        if title and len(title.strip()) > 2:
            score += 0.2
        
        content_length = len(body.strip())
        if content_length > 10:
            score += 0.1
        if content_length > 50:
            score += 0.1
        if content_length > 100:
            score += 0.1
        
        if body and not body.isupper():
            score += 0.1
        
        return min(score, 1.0)
    
    def get_app_info(self) -> Dict[str, Any]:
        """获取当前抓取的应用信息"""
        return {
            'appid': self.config.custom_params.get('appid'),
            'country': self.config.custom_params.get('country'),
            'date_range': {
                'start': self.config.custom_params.get('start_date'),
                'end': self.config.custom_params.get('end_date')
            }
        }




# 便捷工厂函数
def create_qimai_spider(appid: str, 
                       country: str = "cn", 
                       days_back: int = 365,
                       max_pages: int = 100) -> QimaiSpider:
    """创建七麦爬虫的便捷函数"""
    return QimaiSpider.create_for_app(
        appid=appid,
        country=country,
        days_back=days_back,
        max_pages=max_pages
    ) 