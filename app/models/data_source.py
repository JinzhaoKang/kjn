"""
多数据源数据模型
支持社交媒体、电商评论、应用市场等不同平台的反馈数据
包含地理位置信息支持
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from beanie import Document
from pydantic import BaseModel, Field

# 导入地理位置模型 🌍
from .geographical import GeographicalInfo, CountryCode, RegionCode, LanguageCode

class DataSourceType(str, Enum):
    """数据源类型"""
    # 社交媒体
    XIAOHONGSHU = "xiaohongshu"        # 小红书
    DOUYIN = "douyin"                  # 抖音
    WECHAT_MP = "wechat_mp"           # 微信公众号
    WEIBO = "weibo"                   # 微博
    BILIBILI = "bilibili"             # B站
    
    # 电商平台
    TAOBAO = "taobao"                 # 淘宝
    JINGDONG = "jingdong"             # 京东
    PINDUODUO = "pinduoduo"           # 拼多多
    DOUYIN_MALL = "douyin_mall"       # 抖音电商
    TMALL = "tmall"                   # 天猫
    
    # 应用市场
    APP_STORE = "app_store"           # iOS App Store
    GOOGLE_PLAY = "google_play"       # Google Play
    HUAWEI_STORE = "huawei_store"     # 华为应用市场
    XIAOMI_STORE = "xiaomi_store"     # 小米应用商店
    OPPO_STORE = "oppo_store"         # OPPO软件商店
    VIVO_STORE = "vivo_store"         # vivo应用商店
    SAMSUNG_STORE = "samsung_store"   # 三星应用商店
    
    # 其他平台
    CUSTOMER_SERVICE = "customer_service"  # 客服系统
    EMAIL = "email"                       # 邮件反馈
    SURVEY = "survey"                     # 问卷调查
    OFFLINE = "offline"                   # 线下反馈

class ContentType(str, Enum):
    """内容类型"""
    TEXT = "text"               # 纯文本
    IMAGE = "image"             # 图片
    VIDEO = "video"             # 视频
    AUDIO = "audio"             # 音频
    MIXED = "mixed"             # 混合内容

class SentimentType(str, Enum):
    """情感类型"""
    POSITIVE = "positive"       # 正面
    NEGATIVE = "negative"       # 负面
    NEUTRAL = "neutral"         # 中性
    MIXED = "mixed"             # 混合情感

class PriorityLevel(str, Enum):
    """优先级级别"""
    CRITICAL = "critical"       # 紧急
    HIGH = "high"              # 高
    MEDIUM = "medium"          # 中
    LOW = "low"                # 低

class UserInfo(BaseModel):
    """用户信息"""
    user_id: Optional[str] = None           # 用户ID
    username: Optional[str] = None          # 用户名
    nickname: Optional[str] = None          # 昵称
    avatar_url: Optional[str] = None        # 头像URL
    follower_count: Optional[int] = 0       # 粉丝数
    level: Optional[str] = None             # 用户等级
    is_verified: bool = False               # 是否认证用户
    registration_date: Optional[datetime] = None  # 注册时间
    
class ProductInfo(BaseModel):
    """产品信息"""
    product_id: Optional[str] = None        # 产品ID
    product_name: Optional[str] = None      # 产品名称
    category: Optional[str] = None          # 产品类别
    brand: Optional[str] = None             # 品牌
    version: Optional[str] = None           # 版本号
    price: Optional[float] = None           # 价格
    rating: Optional[float] = None          # 评分
    
class PlatformMetadata(BaseModel):
    """平台特定元数据"""
    post_id: Optional[str] = None           # 帖子/评论ID
    parent_id: Optional[str] = None         # 父级ID（回复）
    thread_id: Optional[str] = None         # 话题/主题ID
    likes_count: int = 0                    # 点赞数
    comments_count: int = 0                 # 评论数
    shares_count: int = 0                   # 分享数
    views_count: int = 0                    # 浏览数
    is_pinned: bool = False                 # 是否置顶
    is_featured: bool = False               # 是否精选
    tags: List[str] = Field(default_factory=list)  # 标签
    hashtags: List[str] = Field(default_factory=list)  # 话题标签
    mentions: List[str] = Field(default_factory=list)  # 提及用户
    location: Optional[str] = None          # 地理位置
    
class MediaAttachment(BaseModel):
    """媒体附件"""
    type: ContentType
    url: str
    thumbnail_url: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[int] = None          # 音视频时长（秒）
    width: Optional[int] = None
    height: Optional[int] = None
    description: Optional[str] = None

class ProcessingStatus(BaseModel):
    """处理状态"""
    is_processed: bool = False              # 是否已处理
    processed_at: Optional[datetime] = None # 处理时间
    processing_version: Optional[str] = None # 处理版本
    ai_confidence: Optional[float] = None   # AI置信度
    human_reviewed: bool = False            # 是否人工审核
    reviewed_by: Optional[str] = None       # 审核人
    reviewed_at: Optional[datetime] = None  # 审核时间

class FeedbackData(Document):
    """统一反馈数据模型"""
    
    # 基础信息
    source_type: DataSourceType             # 数据源类型
    source_platform: str                    # 平台名称
    original_id: str                        # 原始平台ID
    url: Optional[str] = None               # 原始链接
    
    # 内容信息
    title: Optional[str] = None             # 标题
    content: str                            # 主要内容
    content_type: ContentType = ContentType.TEXT  # 内容类型
    language: str = "zh-CN"                 # 语言
    
    # 地理位置信息 🌍
    geographical_info: GeographicalInfo = Field(default_factory=GeographicalInfo, description="地理位置信息")
    
    # 时间信息
    created_at: datetime                    # 创建时间
    published_at: Optional[datetime] = None # 发布时间
    updated_at: Optional[datetime] = None   # 更新时间
    crawled_at: datetime = Field(default_factory=datetime.now)  # 爬取时间
    
    # 用户信息
    user_info: Optional[UserInfo] = None
    
    # 产品信息
    product_info: Optional[ProductInfo] = None
    
    # 平台元数据
    platform_metadata: Optional[PlatformMetadata] = None
    
    # 媒体附件
    attachments: List[MediaAttachment] = Field(default_factory=list)
    
    # AI分析结果
    sentiment: Optional[SentimentType] = None        # 情感分析
    priority: Optional[PriorityLevel] = None         # 优先级
    category: Optional[str] = None                   # 分类
    keywords: List[str] = Field(default_factory=list)  # 关键词
    topics: List[str] = Field(default_factory=list)    # 主题
    entities: Dict[str, Any] = Field(default_factory=dict)  # 实体识别
    
    # 处理状态
    processing_status: ProcessingStatus = Field(default_factory=ProcessingStatus)
    
    # 质量评估
    quality_score: Optional[float] = None           # 内容质量分数
    credibility_score: Optional[float] = None      # 可信度分数
    influence_score: Optional[float] = None        # 影响力分数
    
    # 扩展字段
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    # 数据血缘
    data_lineage: Dict[str, Any] = Field(default_factory=dict)  # 数据血缘追踪
    
    class Settings:
        name = "feedback_data"
        indexes = [
            "source_type",
            "source_platform", 
            "created_at",
            "sentiment",
            "priority",
            "processing_status.is_processed",
            # 🌍 地理位置相关索引
            "geographical_info.country_code",
            "geographical_info.region_code", 
            "geographical_info.detected_language",
            [("source_type", 1), ("created_at", -1)],
            [("sentiment", 1), ("priority", 1)],
            [("geographical_info.country_code", 1), ("created_at", -1)],
            [("geographical_info.region_code", 1), ("sentiment", 1)],
            "user_info.user_id",
            "product_info.product_id"
        ]

class DataSourceConfig(Document):
    """数据源配置"""
    
    source_type: DataSourceType
    platform_name: str
    is_active: bool = True
    
    # 爬取配置
    crawl_config: Dict[str, Any] = Field(default_factory=dict)
    
    # API配置
    api_config: Dict[str, Any] = Field(default_factory=dict)
    
    # 处理配置
    processing_config: Dict[str, Any] = Field(default_factory=dict)
    
    # 字段映射配置
    field_mapping: Dict[str, str] = Field(default_factory=dict)
    
    # 过滤规则
    filter_rules: Dict[str, Any] = Field(default_factory=dict)
    
    # 更新配置
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None
    
    class Settings:
        name = "data_source_configs"

class DataSourceStats(Document):
    """数据源统计"""
    
    source_type: DataSourceType
    date: datetime
    
    # 数据量统计
    total_count: int = 0
    processed_count: int = 0
    pending_count: int = 0
    error_count: int = 0
    
    # 质量统计
    avg_quality_score: Optional[float] = None
    high_quality_count: int = 0
    low_quality_count: int = 0
    
    # 情感统计
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    
    # 优先级统计
    critical_count: int = 0
    high_priority_count: int = 0
    medium_priority_count: int = 0
    low_priority_count: int = 0
    
    # 性能统计
    avg_processing_time: Optional[float] = None  # 平均处理时间（秒）
    success_rate: Optional[float] = None         # 成功率
    
    class Settings:
        name = "data_source_stats"
        indexes = [
            [("source_type", 1), ("date", -1)],
            "date"
        ] 