"""
爬虫基类
定义所有爬虫的通用接口和数据模型
"""
import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
import logging
try:
    import aiohttp
except ImportError:
    aiohttp = None
import json
from urllib.parse import urljoin, urlparse

from pydantic import BaseModel, Field



class SpiderStatus(str, Enum):
    """爬虫状态"""
    IDLE = "idle"                    # 空闲
    RUNNING = "running"              # 运行中
    PAUSED = "paused"                # 暂停
    STOPPED = "stopped"              # 已停止
    ERROR = "error"                  # 错误状态
    COMPLETED = "completed"          # 已完成


class DataSourcePlatform(str, Enum):
    """数据源平台"""
    APP_STORE_IOS = "app_store_ios"           # iOS App Store
    APP_STORE_ANDROID = "app_store_android"   # Android各大应用市场
    QIMAI = "qimai"                          # 七麦数据
    XIAOHONGSHU = "xiaohongshu"              # 小红书
    DOUYIN = "douyin"                        # 抖音
    WEIBO = "weibo"                          # 微博
    TAOBAO = "taobao"                        # 淘宝
    TMALL = "tmall"                          # 天猫
    JD = "jd"                                # 淘宝


@dataclass
class SpiderConfig:
    """爬虫配置"""
    # 基础配置
    spider_name: str                          # 爬虫名称
    platform: DataSourcePlatform             # 平台类型
    is_enabled: bool = True                   # 是否启用
    
    # 请求配置
    base_url: str = ""                        # 基础URL
    headers: Dict[str, str] = field(default_factory=dict)  # 请求头
    cookies: Dict[str, str] = field(default_factory=dict)  # Cookie
    timeout: int = 30                         # 超时时间(秒)
    
    # 并发控制
    max_concurrent: int = 5                   # 最大并发数
    request_delay: float = 1.0                # 请求间隔(秒)
    retry_times: int = 3                      # 重试次数
    retry_delay: float = 5.0                  # 重试间隔(秒)
    
    # 数据配置
    max_pages: int = 100                      # 最大抓取页数
    items_per_page: int = 20                  # 每页条目数
    date_range: Optional[tuple] = None        # 时间范围 (start_date, end_date)
    
    # 代理配置
    proxy_url: Optional[str] = None           # 代理URL
    use_proxy_pool: bool = False              # 是否使用代理池
    
    # 扩展配置
    custom_params: Dict[str, Any] = field(default_factory=dict)  # 自定义参数


@dataclass 
class SpiderMetrics:
    """爬虫统计指标"""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_requests: int = 0                   # 总请求数
    successful_requests: int = 0              # 成功请求数
    failed_requests: int = 0                  # 失败请求数
    total_items: int = 0                      # 总抓取条目数
    valid_items: int = 0                      # 有效条目数
    duplicate_items: int = 0                  # 重复条目数
    error_messages: List[str] = field(default_factory=list)  # 错误信息
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def duration(self) -> float:
        """执行时长(秒)"""
        if self.end_time is None:
            return (datetime.now() - self.start_time).total_seconds()
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def items_per_second(self) -> float:
        """每秒抓取条目数"""
        duration = self.duration
        if duration == 0:
            return 0.0
        return self.total_items / duration


class SpiderResult(BaseModel):
    """爬虫结果"""
    spider_name: str                          # 爬虫名称
    platform: DataSourcePlatform             # 平台类型
    status: SpiderStatus                      # 状态
    metrics: SpiderMetrics                    # 统计指标
    data: List[Dict[str, Any]] = Field(default_factory=list)  # 抓取的数据
    errors: List[str] = Field(default_factory=list)          # 错误信息
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True


class BaseSpider(ABC):
    """爬虫基类"""
    
    def __init__(self, config: SpiderConfig):
        self.config = config
        self.status = SpiderStatus.IDLE
        self.metrics = SpiderMetrics()
        self.logger = logging.getLogger(f"spider.{config.spider_name}")
        self.session: Optional[aiohttp.ClientSession] = None
        self._stop_flag = False
        self._pause_flag = False
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup()
    
    async def initialize(self):
        """初始化爬虫"""
        self.logger.info(f"初始化爬虫 {self.config.spider_name}")
        
        # 创建HTTP会话
        if aiohttp is not None:
            connector = aiohttp.TCPConnector(
                limit=self.config.max_concurrent,
                limit_per_host=self.config.max_concurrent
            )
            
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            self.session = aiohttp.ClientSession(
                headers=self.config.headers,
                cookies=self.config.cookies,
                timeout=timeout,
                connector=connector
            )
        else:
            self.logger.warning("aiohttp not available, using requests as fallback")
            self.session = None
        
        # 执行自定义初始化
        await self.custom_initialize()
        
    async def cleanup(self):
        """清理资源"""
        self.logger.info(f"清理爬虫 {self.config.spider_name}")
        
        if self.session and aiohttp is not None:
            await self.session.close()
            self.session = None
            
        await self.custom_cleanup()
    
    @abstractmethod
    async def custom_initialize(self):
        """自定义初始化（子类实现）"""
        pass
    
    @abstractmethod
    async def custom_cleanup(self):
        """自定义清理（子类实现）"""
        pass
    
    @abstractmethod
    async def fetch_data(self, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """抓取数据（子类实现）"""
        pass
    
    @abstractmethod
    def parse_item(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析单个数据项（子类实现）"""
        pass
    
    async def run(self, **kwargs) -> SpiderResult:
        """运行爬虫"""
        self.logger.info(f"开始运行爬虫 {self.config.spider_name}")
        
        self.status = SpiderStatus.RUNNING
        self.metrics = SpiderMetrics()
        collected_data = []
        errors = []
        
        try:
            # 抓取数据
            async for raw_item in self.fetch_data(**kwargs):
                # 检查停止标志
                if self._stop_flag:
                    self.logger.info("收到停止信号，终止爬虫")
                    break
                
                # 检查暂停标志
                while self._pause_flag and not self._stop_flag:
                    await asyncio.sleep(1)
                
                try:
                    # 解析数据项
                    parsed_item = self.parse_item(raw_item)
                    if parsed_item:
                        collected_data.append(parsed_item)
                        self.metrics.valid_items += 1
                    
                    self.metrics.total_items += 1
                    
                    # 请求间隔
                    if self.config.request_delay > 0:
                        await asyncio.sleep(self.config.request_delay)
                        
                except Exception as e:
                    error_msg = f"解析数据项失败: {e}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
                    self.metrics.error_messages.append(error_msg)
            
            self.status = SpiderStatus.COMPLETED
            self.logger.info(f"爬虫完成，抓取 {len(collected_data)} 条有效数据")
            
        except Exception as e:
            self.status = SpiderStatus.ERROR
            error_msg = f"爬虫运行失败: {e}"
            self.logger.error(error_msg)
            errors.append(error_msg)
            self.metrics.error_messages.append(error_msg)
        
        finally:
            self.metrics.end_time = datetime.now()
        
        return SpiderResult(
            spider_name=self.config.spider_name,
            platform=self.config.platform,
            status=self.status,
            metrics=self.metrics,
            data=collected_data,
            errors=errors
        )
    
    async def make_request(self, 
                          url: str, 
                          method: str = "GET",
                          params: Optional[Dict[str, Any]] = None,
                          data: Optional[Dict[str, Any]] = None,
                          **kwargs) -> Optional[Dict[str, Any]]:
        """发起HTTP请求"""
        self.metrics.total_requests += 1
        
        for attempt in range(self.config.retry_times + 1):
            try:
                if self.session is not None:
                    # 使用aiohttp
                    async with self.session.request(
                        method=method,
                        url=url,
                        params=params,
                        data=data,
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
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    self.metrics.failed_requests += 1
                    return None
        
        return None
    
    def stop(self):
        """停止爬虫"""
        self.logger.info(f"停止爬虫 {self.config.spider_name}")
        self._stop_flag = True
        self.status = SpiderStatus.STOPPED
    
    def pause(self):
        """暂停爬虫"""
        self.logger.info(f"暂停爬虫 {self.config.spider_name}")
        self._pause_flag = True
        self.status = SpiderStatus.PAUSED
    
    def resume(self):
        """恢复爬虫"""
        self.logger.info(f"恢复爬虫 {self.config.spider_name}")
        self._pause_flag = False
        self.status = SpiderStatus.RUNNING
    
    def get_status(self) -> Dict[str, Any]:
        """获取爬虫状态"""
        return {
            "spider_name": self.config.spider_name,
            "platform": self.config.platform.value,
            "status": self.status.value,
            "metrics": {
                "duration": self.metrics.duration,
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "success_rate": self.metrics.success_rate,
                "total_items": self.metrics.total_items,
                "valid_items": self.metrics.valid_items,
                "items_per_second": self.metrics.items_per_second
            }
        } 