"""
Spider爬虫模块
用于从各种第三方平台抓取用户反馈数据
"""
from .base_spider import BaseSpider, SpiderConfig, SpiderResult, DataSourcePlatform
from .qimai_spider import QimaiSpider, create_qimai_spider
from .spider_manager import SpiderManager, get_spider_manager, initialize_spider_manager

__all__ = [
    'BaseSpider',
    'SpiderConfig', 
    'SpiderResult',
    'DataSourcePlatform',
    'QimaiSpider',
    'create_qimai_spider',
    'SpiderManager',
    'get_spider_manager',
    'initialize_spider_manager'
] 