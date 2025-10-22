"""
数据源适配器系统
负责将不同平台的原始数据转换为统一的数据格式
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass

from ...models.data_source import (
    FeedbackData, DataSourceType, ContentType, UserInfo, 
    ProductInfo, PlatformMetadata, MediaAttachment, ProcessingStatus
)
from ...models.geographical import (
    GeographicalInfo, CountryCode, RegionCode, LanguageCode,
    get_geographical_manager
)

logger = logging.getLogger(__name__)

@dataclass
class RawDataItem:
    """原始数据项"""
    source_type: DataSourceType
    raw_data: Dict[str, Any]
    metadata: Dict[str, Any] = None

class BaseDataAdapter(ABC):
    """数据适配器基类"""
    
    def __init__(self, source_type: DataSourceType):
        self.source_type = source_type
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def can_handle(self, raw_data: Dict[str, Any]) -> bool:
        """判断是否能处理此数据"""
        pass
    
    @abstractmethod
    def transform(self, raw_data: Dict[str, Any]) -> FeedbackData:
        """将原始数据转换为标准格式"""
        pass
    
    def validate_data(self, data: FeedbackData) -> bool:
        """验证转换后的数据"""
        try:
            # 基础字段验证
            if not data.content or len(data.content.strip()) < 1:
                return False
            
            if not data.original_id:
                return False
            
            if not data.created_at:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"数据验证失败: {e}")
            return False
    
    def extract_user_info(self, raw_data: Dict[str, Any]) -> Optional[UserInfo]:
        """提取用户信息（子类可重写）"""
        return None
    
    def extract_product_info(self, raw_data: Dict[str, Any]) -> Optional[ProductInfo]:
        """提取产品信息（子类可重写）"""
        return None
    
    def extract_platform_metadata(self, raw_data: Dict[str, Any]) -> Optional[PlatformMetadata]:
        """提取平台元数据（子类可重写）"""
        return None
    
    def detect_geographical_info(self, raw_data: Dict[str, Any], content: str = None) -> GeographicalInfo:
        """检测地理位置信息 🌍"""
        geo_manager = get_geographical_manager()
        
        # 1. 检查是否有显式的国家信息
        explicit_country = None
        if 'country' in raw_data:
            country_str = raw_data['country'].upper()
            try:
                explicit_country = CountryCode(country_str)
            except ValueError:
                pass
        
        # 2. 从平台信息检测
        platform_name = None
        if hasattr(self, 'source_type'):
            platform_name = self.source_type.value
        
        # 3. 从内容检测语言
        text_content = content or raw_data.get('content', raw_data.get('text', ''))
        
        # 4. 从IP地址检测（如果有）
        ip_address = raw_data.get('ip_address', raw_data.get('user_ip'))
        
        # 综合检测
        geo_info = geo_manager.get_geographical_info(
            platform_name=platform_name,
            text_content=text_content,
            ip_address=ip_address,
            explicit_country=explicit_country
        )
        
        self.logger.debug(f"检测到地理位置信息: {geo_info.country_name} ({geo_info.detection_method})")
        
        return geo_info

class SocialMediaAdapter(BaseDataAdapter):
    """社交媒体适配器基类"""
    
    def extract_user_info(self, raw_data: Dict[str, Any]) -> Optional[UserInfo]:
        """提取社交媒体用户信息"""
        user_data = raw_data.get('user', {})
        
        if not user_data:
            return None
        
        return UserInfo(
            user_id=user_data.get('id'),
            username=user_data.get('username'),
            nickname=user_data.get('nickname', user_data.get('display_name')),
            avatar_url=user_data.get('avatar_url'),
            follower_count=user_data.get('follower_count', 0),
            level=user_data.get('level'),
            is_verified=user_data.get('is_verified', False),
            registration_date=self._parse_datetime(user_data.get('registration_date'))
        )
    
    def extract_platform_metadata(self, raw_data: Dict[str, Any]) -> Optional[PlatformMetadata]:
        """提取社交媒体平台元数据"""
        return PlatformMetadata(
            post_id=raw_data.get('id'),
            parent_id=raw_data.get('parent_id'),
            thread_id=raw_data.get('thread_id'),
            likes_count=raw_data.get('likes_count', 0),
            comments_count=raw_data.get('comments_count', 0),
            shares_count=raw_data.get('shares_count', 0),
            views_count=raw_data.get('views_count', 0),
            is_pinned=raw_data.get('is_pinned', False),
            is_featured=raw_data.get('is_featured', False),
            tags=raw_data.get('tags', []),
            hashtags=raw_data.get('hashtags', []),
            mentions=raw_data.get('mentions', []),
            location=raw_data.get('location')
        )
    
    def _parse_datetime(self, date_str: Any) -> Optional[datetime]:
        """解析时间字符串"""
        if not date_str:
            return None
        
        if isinstance(date_str, datetime):
            return date_str
        
        try:
            # 常见的时间格式
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y/%m/%d %H:%M:%S"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(str(date_str), fmt)
                except ValueError:
                    continue
            
            # 如果都失败了，尝试pandas解析
            import pandas as pd
            return pd.to_datetime(date_str).to_pydatetime()
            
        except Exception as e:
            self.logger.warning(f"时间解析失败: {date_str}, {e}")
            return None

class XiaohongshuAdapter(SocialMediaAdapter):
    """小红书数据适配器"""
    
    def __init__(self):
        super().__init__(DataSourceType.XIAOHONGSHU)
    
    def can_handle(self, raw_data: Dict[str, Any]) -> bool:
        """判断是否为小红书数据"""
        return (
            'note_id' in raw_data or 
            'platform' in raw_data and raw_data['platform'] == 'xiaohongshu'
        )
    
    def transform(self, raw_data: Dict[str, Any]) -> FeedbackData:
        """转换小红书数据"""
        content = raw_data.get('content', raw_data.get('text', ''))
        
        return FeedbackData(
            source_type=self.source_type,
            source_platform="小红书",
            original_id=raw_data.get('note_id', raw_data.get('id')),
            url=raw_data.get('url'),
            title=raw_data.get('title'),
            content=content,
            content_type=self._determine_content_type(raw_data),
            created_at=self._parse_datetime(raw_data.get('created_time', raw_data.get('publish_time'))),
            published_at=self._parse_datetime(raw_data.get('publish_time')),
            user_info=self.extract_user_info(raw_data),
            platform_metadata=self.extract_platform_metadata(raw_data),
            attachments=self._extract_attachments(raw_data),
            geographical_info=self.detect_geographical_info(raw_data, content),  # 🌍 新增地理位置检测
            processing_status=ProcessingStatus()
        )
    
    def _determine_content_type(self, raw_data: Dict[str, Any]) -> ContentType:
        """判断内容类型"""
        if raw_data.get('images') or raw_data.get('pic_ids'):
            if raw_data.get('video_url'):
                return ContentType.MIXED
            return ContentType.IMAGE
        elif raw_data.get('video_url'):
            return ContentType.VIDEO
        else:
            return ContentType.TEXT
    
    def _extract_attachments(self, raw_data: Dict[str, Any]) -> List[MediaAttachment]:
        """提取媒体附件"""
        attachments = []
        
        # 处理图片
        images = raw_data.get('images', [])
        for img in images:
            attachments.append(MediaAttachment(
                type=ContentType.IMAGE,
                url=img.get('url', img) if isinstance(img, dict) else img,
                thumbnail_url=img.get('thumbnail_url') if isinstance(img, dict) else None
            ))
        
        # 处理视频
        video_url = raw_data.get('video_url')
        if video_url:
            attachments.append(MediaAttachment(
                type=ContentType.VIDEO,
                url=video_url,
                thumbnail_url=raw_data.get('video_cover'),
                duration=raw_data.get('video_duration')
            ))
        
        return attachments

class DouyinAdapter(SocialMediaAdapter):
    """抖音数据适配器"""
    
    def __init__(self):
        super().__init__(DataSourceType.DOUYIN)
    
    def can_handle(self, raw_data: Dict[str, Any]) -> bool:
        """判断是否为抖音数据"""
        return (
            'aweme_id' in raw_data or
            'platform' in raw_data and raw_data['platform'] == 'douyin'
        )
    
    def transform(self, raw_data: Dict[str, Any]) -> FeedbackData:
        """转换抖音数据"""
        return FeedbackData(
            source_type=self.source_type,
            source_platform="抖音",
            original_id=raw_data.get('aweme_id', raw_data.get('id')),
            url=raw_data.get('share_url'),
            title=raw_data.get('desc'),  # 抖音通常没有标题
            content=raw_data.get('desc', ''),
            content_type=ContentType.VIDEO,  # 抖音主要是视频内容
            created_at=self._parse_datetime(raw_data.get('create_time')),
            user_info=self.extract_user_info(raw_data),
            platform_metadata=self.extract_platform_metadata(raw_data),
            processing_status=ProcessingStatus()
        )

class EcommerceAdapter(BaseDataAdapter):
    """电商平台适配器基类"""
    
    def extract_product_info(self, raw_data: Dict[str, Any]) -> Optional[ProductInfo]:
        """提取商品信息"""
        product_data = raw_data.get('product', {})
        
        return ProductInfo(
            product_id=product_data.get('id', raw_data.get('product_id')),
            product_name=product_data.get('name', raw_data.get('product_name')),
            category=product_data.get('category'),
            brand=product_data.get('brand'),
            version=product_data.get('version'),
            price=product_data.get('price'),
            rating=product_data.get('rating', raw_data.get('product_rating'))
        )

class TaobaoAdapter(EcommerceAdapter):
    """淘宝数据适配器"""
    
    def __init__(self):
        super().__init__(DataSourceType.TAOBAO)
    
    def can_handle(self, raw_data: Dict[str, Any]) -> bool:
        """判断是否为淘宝数据"""
        return (
            'review_id' in raw_data or
            'platform' in raw_data and raw_data['platform'] == 'taobao'
        )
    
    def transform(self, raw_data: Dict[str, Any]) -> FeedbackData:
        """转换淘宝评论数据"""
        return FeedbackData(
            source_type=self.source_type,
            source_platform="淘宝",
            original_id=raw_data.get('review_id', raw_data.get('id')),
            url=raw_data.get('product_url'),
            content=raw_data.get('content', raw_data.get('review_text', '')),
            content_type=ContentType.TEXT,
            created_at=self._parse_datetime(raw_data.get('review_time')),
            user_info=self._extract_taobao_user(raw_data),
            product_info=self.extract_product_info(raw_data),
            platform_metadata=self._extract_taobao_metadata(raw_data),
            processing_status=ProcessingStatus()
        )
    
    def _extract_taobao_user(self, raw_data: Dict[str, Any]) -> Optional[UserInfo]:
        """提取淘宝用户信息"""
        return UserInfo(
            user_id=raw_data.get('user_id'),
            username=raw_data.get('username'),
            nickname=raw_data.get('user_nick'),
            level=raw_data.get('user_level'),
            is_verified=raw_data.get('is_vip', False)
        )
    
    def _extract_taobao_metadata(self, raw_data: Dict[str, Any]) -> PlatformMetadata:
        """提取淘宝平台元数据"""
        return PlatformMetadata(
            post_id=raw_data.get('review_id'),
            likes_count=raw_data.get('useful_count', 0),
            tags=raw_data.get('tags', [])
        )

class AppStoreAdapter(BaseDataAdapter):
    """应用商店适配器基类"""
    
    def extract_product_info(self, raw_data: Dict[str, Any]) -> Optional[ProductInfo]:
        """提取应用信息"""
        app_data = raw_data.get('app', {})
        
        return ProductInfo(
            product_id=app_data.get('id', raw_data.get('app_id')),
            product_name=app_data.get('name', raw_data.get('app_name')),
            category=app_data.get('category'),
            brand=app_data.get('developer', raw_data.get('developer')),
            version=app_data.get('version', raw_data.get('app_version')),
            rating=raw_data.get('rating')
        )

class IOSAppStoreAdapter(AppStoreAdapter):
    """iOS App Store适配器"""
    
    def __init__(self):
        super().__init__(DataSourceType.APP_STORE)
    
    def can_handle(self, raw_data: Dict[str, Any]) -> bool:
        """判断是否为App Store数据"""
        return (
            'review_id' in raw_data and 'platform' in raw_data and 
            raw_data['platform'] in ['app_store', 'ios']
        )
    
    def transform(self, raw_data: Dict[str, Any]) -> FeedbackData:
        """转换App Store评论数据"""
        return FeedbackData(
            source_type=self.source_type,
            source_platform="App Store",
            original_id=raw_data.get('review_id', raw_data.get('id')),
            url=raw_data.get('app_url'),
            title=raw_data.get('title'),
            content=raw_data.get('content', raw_data.get('review_text', '')),
            content_type=ContentType.TEXT,
            created_at=self._parse_datetime(raw_data.get('created_date')),
            user_info=self._extract_appstore_user(raw_data),
            product_info=self.extract_product_info(raw_data),
            platform_metadata=self._extract_appstore_metadata(raw_data),
            processing_status=ProcessingStatus()
        )
    
    def _extract_appstore_user(self, raw_data: Dict[str, Any]) -> Optional[UserInfo]:
        """提取App Store用户信息"""
        return UserInfo(
            username=raw_data.get('reviewer_name'),
            user_id=raw_data.get('reviewer_id')
        )
    
    def _extract_appstore_metadata(self, raw_data: Dict[str, Any]) -> PlatformMetadata:
        """提取App Store元数据"""
        return PlatformMetadata(
            post_id=raw_data.get('review_id'),
            likes_count=raw_data.get('helpfulness_count', 0)
        )

class DataAdapterRegistry:
    """数据适配器注册表"""
    
    def __init__(self):
        self.adapters: Dict[DataSourceType, BaseDataAdapter] = {}
        self.logger = logging.getLogger(__name__)
        self._register_default_adapters()
    
    def _register_default_adapters(self):
        """注册默认适配器"""
        adapters = [
            XiaohongshuAdapter(),
            DouyinAdapter(),
            TaobaoAdapter(),
            IOSAppStoreAdapter(),
        ]
        
        for adapter in adapters:
            self.register_adapter(adapter)
    
    def register_adapter(self, adapter: BaseDataAdapter):
        """注册适配器"""
        self.adapters[adapter.source_type] = adapter
        logger.info(f"注册数据适配器: {adapter.source_type.value}")
    
    def get_adapter(self, source_type: DataSourceType) -> Optional[BaseDataAdapter]:
        """获取适配器"""
        return self.adapters.get(source_type)
    
    def find_adapter(self, raw_data: Dict[str, Any]) -> Optional[BaseDataAdapter]:
        """根据原始数据查找合适的适配器"""
        for adapter in self.adapters.values():
            if adapter.can_handle(raw_data):
                return adapter
        return None
    
    def transform_data(self, raw_data: Dict[str, Any], source_type: DataSourceType = None) -> Optional[FeedbackData]:
        """转换单条原始数据为标准格式"""
        try:
            # 如果指定了源类型，优先使用对应的适配器
            if source_type:
                adapter = self.get_adapter(source_type)
                if adapter and adapter.can_handle(raw_data):
                    feedback_data = adapter.transform(raw_data)
                    if adapter.validate_data(feedback_data):
                        return feedback_data
            
            # 自动查找适配器
            adapter = self.find_adapter(raw_data)
            if adapter:
                feedback_data = adapter.transform(raw_data)
                if adapter.validate_data(feedback_data):
                    return feedback_data
                else:
                    self.logger.warning(f"数据验证失败，跳过此条数据")
                    return None
            else:
                self.logger.warning(f"未找到合适的适配器处理数据: {list(raw_data.keys())[:3]}")
                return None
        
        except Exception as e:
            self.logger.error(f"数据转换失败: {e}")
            return None

    async def batch_import_data(self, 
                               data: List[Dict[str, Any]], 
                               source_type: str = "spider",
                               metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """批量导入数据到数据库"""
        from ...models.database import UserFeedback, FeedbackSource
        
        imported_count = 0
        failed_count = 0
        failed_items = []
        
        self.logger.info(f"开始批量导入 {len(data)} 条数据")
        
        for i, raw_item in enumerate(data):
            try:
                # 判断数据源类型
                if source_type == "spider":
                    # 处理爬虫数据
                    feedback_doc = await self._convert_spider_data_to_feedback(raw_item, metadata)
                else:
                    # 处理其他类型数据
                    feedback_doc = await self._convert_raw_data_to_feedback(raw_item, source_type, metadata)
                
                if feedback_doc:
                    # 保存到MongoDB
                    await feedback_doc.save()
                    imported_count += 1
                    self.logger.debug(f"成功导入第 {i+1} 条数据")
                else:
                    failed_count += 1
                    failed_items.append({"index": i, "reason": "数据转换失败"})
                    
            except Exception as e:
                failed_count += 1
                failed_items.append({"index": i, "reason": str(e)})
                self.logger.error(f"导入第 {i+1} 条数据失败: {e}")
        
        self.logger.info(f"批量导入完成: 成功 {imported_count} 条，失败 {failed_count} 条")
        
        return {
            "imported_count": imported_count,
            "failed_count": failed_count,
            "total_count": len(data),
            "failed_items": failed_items[:10],  # 只返回前10个失败项
            "success_rate": imported_count / len(data) if data else 0
        }
    
    async def _convert_spider_data_to_feedback(self, 
                                             spider_data: Dict[str, Any], 
                                             metadata: Dict[str, Any] = None) -> Optional['UserFeedback']:
        """将爬虫数据转换为UserFeedback文档"""
        from ...models.database import UserFeedback, FeedbackSource
        
        try:
            # 提取基本信息
            content = spider_data.get('content', spider_data.get('text', ''))
            if not content or len(content.strip()) < 1:
                return None
                
            # 判断平台类型
            platform = spider_data.get('platform', 'unknown')
            if platform in ['ios', 'app_store']:
                source = FeedbackSource.APP_STORE
            elif platform == 'android':
                source = FeedbackSource.GOOGLE_PLAY
            else:
                source = FeedbackSource.INTERNAL
            
            # 解析时间
            feedback_time = self._parse_spider_time(spider_data.get('created_at', spider_data.get('date')))
            
            # 构建平台元数据
            platform_metadata = {
                "original_id": spider_data.get('id', spider_data.get('review_id')),
                "rating": spider_data.get('rating'),
                "title": spider_data.get('title'),
                "author": spider_data.get('author', spider_data.get('username')),
                "app_info": spider_data.get('app_info', {}),
                "country": spider_data.get('country'),
                "platform": platform
            }
            
            # 添加爬虫元数据
            if metadata:
                platform_metadata.update(metadata)
            
            # 创建UserFeedback文档
            feedback_doc = UserFeedback(
                content=content,
                original_content=content,
                source=source,
                source_platform=spider_data.get('source_platform', platform),
                original_id=spider_data.get('id', spider_data.get('review_id')),
                url=spider_data.get('url'),
                feedback_time=feedback_time,
                crawled_at=datetime.now(),
                user_id=spider_data.get('user_id', spider_data.get('author')),
                platform_metadata=platform_metadata,
                needs_llm_analysis=True,
                # 兼容性字段
                original_text=content,
                processed_text=content
            )
            
            return feedback_doc
            
        except Exception as e:
            self.logger.error(f"转换爬虫数据失败: {e}")
            return None
    
    async def _convert_raw_data_to_feedback(self, 
                                          raw_data: Dict[str, Any], 
                                          source_type: str,
                                          metadata: Dict[str, Any] = None) -> Optional['UserFeedback']:
        """将原始数据转换为UserFeedback文档"""
        from ...models.database import UserFeedback, FeedbackSource
        
        try:
            # 使用适配器转换数据
            feedback_data = self.transform_data(raw_data)
            if not feedback_data:
                return None
            
            # 转换为UserFeedback文档
            feedback_doc = UserFeedback(
                content=feedback_data.content,
                original_content=feedback_data.content,
                source=FeedbackSource.INTERNAL,  # 默认为内部数据
                source_platform="internal",
                feedback_time=feedback_data.created_at,
                crawled_at=datetime.now(),
                user_id=str(feedback_data.user_info.user_id) if feedback_data.user_info else None,
                platform_metadata=metadata or {},
                # 兼容性字段
                original_text=feedback_data.content,
                processed_text=feedback_data.content
            )
            
            return feedback_doc
            
        except Exception as e:
            self.logger.error(f"转换原始数据失败: {e}")
            return None
    
    def _parse_spider_time(self, time_str: Any) -> Optional['datetime']:
        """解析爬虫时间字符串"""
        if not time_str:
            return None
        
        if isinstance(time_str, datetime):
            return time_str
        
        try:
            # 常见的时间格式
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y/%m/%d %H:%M:%S",
                "%Y年%m月%d日 %H:%M:%S",
                "%Y-%m-%d"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(str(time_str), fmt)
                except ValueError:
                    continue
            
            # 尝试自动解析
            import dateutil.parser
            return dateutil.parser.parse(str(time_str))
            
        except Exception as e:
            self.logger.warning(f"时间解析失败: {time_str}, {e}")
            return datetime.now()

    def get_supported_sources(self) -> List[DataSourceType]:
        """获取支持的数据源列表"""
        return list(self.adapters.keys())

# 全局适配器注册表
adapter_registry = DataAdapterRegistry()

def get_adapter_registry() -> DataAdapterRegistry:
    """获取适配器注册表实例"""
    return adapter_registry

def get_adapter_manager() -> DataAdapterRegistry:
    """获取适配器管理器实例（别名）"""
    return adapter_registry 