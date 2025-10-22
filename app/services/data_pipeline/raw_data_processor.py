"""
原始数据处理器
负责第一层数据处理：清洗、标准化、入库
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import uuid

from ..data_ingestion.preprocessor import FeedbackPreprocessor
from ...core.database import get_db
from ...models.database import UserFeedback, FeedbackSource

logger = logging.getLogger(__name__)

@dataclass
class RawDataItem:
    """原始数据项"""
    data: Dict[str, Any]
    source: str = "spider"
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass 
class ProcessingResult:
    """处理结果"""
    success: bool
    processed_count: int
    failed_count: int
    feedback_ids: List[str] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.feedback_ids is None:
            self.feedback_ids = []
        if self.errors is None:
            self.errors = []

class RawDataProcessor:
    """原始数据处理器
    
    负责：
    1. 数据清洗和标准化
    2. 质量检查和过滤
    3. 数据格式统一
    4. 入库前预处理
    """
    
    def __init__(self):
        self.preprocessor = FeedbackPreprocessor()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    async def process_spider_batch(self, 
                                  spider_data: List[Dict[str, Any]], 
                                  task_metadata: Dict[str, Any] = None) -> ProcessingResult:
        """处理爬虫批量数据"""
        self.logger.info(f"开始处理 {len(spider_data)} 条爬虫数据")
        
        processed_items = []
        failed_count = 0
        errors = []
        
        # 第一步：数据清洗和标准化
        for i, raw_item in enumerate(spider_data):
            try:
                # 提取核心内容
                content = self._extract_content(raw_item)
                if not content or len(content.strip()) < 5:
                    failed_count += 1
                    filter_reason = f"内容过短 (长度: {len(content.strip()) if content else 0})"
                    self.logger.warning(f"🚫 过滤数据[索引{i}]: {filter_reason}")
                    self.logger.warning(f"   原始数据: {raw_item}")
                    errors.append(f"索引{i}: {filter_reason}")
                    continue
                
                # 数据预处理
                processed_item = self._preprocess_spider_item(raw_item, task_metadata)
                if processed_item:
                    processed_items.append(processed_item)
                    self.logger.debug(f"✅ 成功处理数据[索引{i}]: 质量分={processed_item['quality_score']:.3f}")
                else:
                    failed_count += 1
                    self.logger.warning(f"🚫 预处理失败[索引{i}]: 可能是质量评分过低")
                    errors.append(f"索引{i}: 预处理失败")
                    
            except Exception as e:
                failed_count += 1
                errors.append(f"索引{i}: {str(e)}")
                self.logger.error(f"处理爬虫数据项失败: {e}")
        
        # 第二步：批量入库
        if processed_items:
            feedback_ids = await self._batch_save_to_database(processed_items)
            self.logger.info(f"数据处理完成: 成功 {len(feedback_ids)} 条，失败 {failed_count} 条")
            
            # 详细错误报告
            if errors:
                self.logger.warning(f"🚫 过滤详情 ({failed_count}条):")
                for error in errors[:5]:  # 只显示前5个错误
                    self.logger.warning(f"   - {error}")
                if len(errors) > 5:
                    self.logger.warning(f"   ... 还有 {len(errors) - 5} 个错误")
            
            return ProcessingResult(
                success=True,
                processed_count=len(feedback_ids),
                failed_count=failed_count,
                feedback_ids=feedback_ids,
                errors=errors[:10]  # 只保留前10个错误
            )
        else:
            return ProcessingResult(
                success=False,
                processed_count=0,
                failed_count=failed_count,
                errors=errors[:10]
            )
    
    def _extract_content(self, raw_item: Dict[str, Any]) -> str:
        """提取核心内容"""
        # 尝试多种可能的内容字段
        content_fields = ['content', 'text', 'body', 'comment', 'review_text']
        
        for field in content_fields:
            content = raw_item.get(field, '')
            if content and isinstance(content, str) and len(content.strip()) > 0:
                return content.strip()
        
        return ""
    
    def _preprocess_spider_item(self, 
                               raw_item: Dict[str, Any], 
                               task_metadata: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """预处理单个爬虫数据项"""
        try:
            # 提取基础信息
            content = self._extract_content(raw_item)
            if not content:
                return None
            
            # 文本预处理
            processed_result = self.preprocessor.preprocess_feedback(
                original_text=content,
                source="spider",
                metadata=task_metadata
            )
            
            # 质量检查
            if processed_result['quality_score'] < 0.1:
                self.logger.warning(f"🚫 过滤低质量内容 (质量分: {processed_result['quality_score']:.3f})")
                self.logger.warning(f"   内容: {content[:100]}...")
                self.logger.warning(f"   处理步骤: {processed_result.get('processing_steps', [])}")
                self.logger.warning(f"   原因: 质量评分 {processed_result['quality_score']:.3f} < 0.1")
                return None
            
            # 构建标准格式
            processed_item = {
                # 基础信息 - 仅从爬虫数据提取，不做AI分析
                'content': processed_result['processed_text'],
                'original_content': content,
                'source': self._determine_source(raw_item),
                'source_platform': raw_item.get('source_platform', '未知平台'),
                'original_id': raw_item.get('original_id', str(uuid.uuid4())),
                'url': raw_item.get('url'),
                
                # 时间信息
                'created_at': self._parse_time(raw_item.get('created_at')),
                'published_at': self._parse_time(raw_item.get('published_at')),
                'crawled_at': datetime.now(),
                
                # 用户信息（原始）
                'user_info': raw_item.get('user_info', {}),
                
                # 产品信息（原始）
                'product_info': raw_item.get('product_info', {}),
                
                # 平台元数据（原始）
                'platform_metadata': raw_item.get('platform_metadata', {}),
                
                # 地理信息（原始）
                'geographical_info': raw_item.get('geographical_info', {}),
                
                # 预处理结果
                'language': processed_result['language'],
                'quality_score': processed_result['quality_score'],
                'processing_metadata': {
                    'preprocessed_at': datetime.now(),
                    'processing_steps': processed_result['processing_steps'],
                    'keywords': processed_result['keywords']
                },
                
                # 任务元数据
                'task_metadata': task_metadata or {},
                
                # 处理状态 - 标记需要后台处理
                'processing_status': {
                    'raw_processed': True,
                    'ai_analyzed': False,
                    'needs_ai_analysis': True,
                    'sentiment_analyzed': False,
                    'priority_calculated': False,
                    'categorized': False
                },
                
                # 数据血缘
                'data_lineage': {
                    'source': 'raw_data_processor',
                    'processing_stage': 'raw_preprocessing',
                    'processed_at': datetime.now().isoformat(),
                    'processor_version': '1.0'
                }
            }
            
            return processed_item
            
        except Exception as e:
            self.logger.error(f"预处理爬虫数据项失败: {e}")
            return None
    
    def _determine_source(self, raw_item: Dict[str, Any]) -> FeedbackSource:
        """确定反馈来源"""
        source_type = raw_item.get('source_type', '').lower()
        platform = raw_item.get('platform', '').lower()
        
        if 'ios' in source_type or 'app_store' in source_type:
            return FeedbackSource.APP_STORE
        elif 'android' in source_type or 'google_play' in source_type:
            return FeedbackSource.GOOGLE_PLAY
        elif 'qimai' in raw_item.get('source_platform', '').lower():
            # 七麦数据根据平台判断
            if 'ios' in platform:
                return FeedbackSource.APP_STORE
            elif 'android' in platform:
                return FeedbackSource.GOOGLE_PLAY
        
        return FeedbackSource.INTERNAL
    
    def _parse_time(self, time_value: Any) -> Optional[datetime]:
        """解析时间值"""
        if isinstance(time_value, datetime):
            return time_value
        
        if isinstance(time_value, str):
            try:
                # 常见时间格式
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%d"
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(time_value, fmt)
                    except ValueError:
                        continue
                        
            except Exception as e:
                self.logger.warning(f"时间解析失败: {time_value}, {e}")
        
        return None
    
    async def _batch_save_to_database(self, processed_items: List[Dict[str, Any]]) -> List[str]:
        """批量保存到数据库"""
        feedback_ids = []
        
        for item in processed_items:
            try:
                # 创建UserFeedback文档
                feedback = UserFeedback(
                    content=item['content'],
                    original_content=item['original_content'],
                    source=item['source'],
                    source_platform=item['source_platform'],
                    original_id=item['original_id'],
                    url=item.get('url'),
                    feedback_time=item.get('created_at', datetime.now()),
                    published_at=item.get('published_at'),
                    crawled_at=item.get('crawled_at', datetime.now()),
                    user_info=item.get('user_info', {}),
                    product_info=item.get('product_info', {}),
                    geographical_info=item.get('geographical_info', {}),
                    platform_metadata=item.get('platform_metadata', {}),
                    
                    # 预处理信息
                    language=item['language'],
                    quality_score=item['quality_score'],
                    processing_metadata=item['processing_metadata'],
                    
                    # 处理状态
                    processing_status=item['processing_status'],
                    
                    # AI分析结果（待填充）
                    sentiment=None,
                    category=None,
                    keywords=[],
                    priority=None,
                    ai_confidence=None,
                    
                    # 任务元数据
                    task_metadata=item.get('task_metadata', {}),
                    data_lineage=item['data_lineage'],
                    
                    # 兼容性字段
                    original_text=item['original_content'],  # 设置兼容字段
                    processed_text=item['content']          # 设置兼容字段
                )
                
                # 保存到数据库
                await feedback.save()
                feedback_ids.append(str(feedback.id))
                
            except Exception as e:
                self.logger.error(f"保存反馈数据失败: {e}")
                continue
        
        return feedback_ids
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        try:
            # 统计原始数据处理情况
            total_count = await UserFeedback.count()
            
            # 统计处理状态
            raw_processed = await UserFeedback.find(
                {"processing_status.raw_processed": True}
            ).count()
            
            needs_ai_analysis = await UserFeedback.find(
                {"processing_status.needs_ai_analysis": True}
            ).count()
            
            ai_analyzed = await UserFeedback.find(
                {"processing_status.ai_analyzed": True}
            ).count()
            
            return {
                "total_feedback_count": total_count,
                "raw_processed_count": raw_processed,
                "needs_ai_analysis_count": needs_ai_analysis,
                "ai_analyzed_count": ai_analyzed,
                "processing_completion_rate": round(ai_analyzed / total_count * 100, 2) if total_count > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"获取处理统计失败: {e}")
            return {"error": str(e)}

# 创建全局实例
raw_data_processor = RawDataProcessor() 