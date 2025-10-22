"""
后台任务处理引擎
负责第二层数据处理：AI分析、情感分析、优先级计算、分类等
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..preprocessing.intelligent_filter import intelligent_filter
from ..analysis.multi_model_analyzer import multi_model_analyzer
from ...core.database import get_db
from ...models.database import UserFeedback

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """任务类型"""
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    CATEGORY_CLASSIFICATION = "category_classification" 
    PRIORITY_CALCULATION = "priority_calculation"
    KEYWORD_EXTRACTION = "keyword_extraction"
    FULL_AI_ANALYSIS = "full_ai_analysis"

@dataclass
class BackgroundTask:
    """后台任务"""
    task_id: str
    task_type: TaskType
    feedback_id: str
    priority: int = 5
    model_id: Optional[str] = None  # 新增：指定使用的AI模型
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class ProcessingStats:
    """处理统计"""
    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    pending: int = 0
    
class BackgroundTaskEngine:
    """后台任务处理引擎
    
    负责：
    1. AI情感分析
    2. 内容分类
    3. 优先级计算
    4. 关键词提取
    5. 综合AI分析
    """
    
    def __init__(self, max_concurrent_tasks: int = 3):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 任务队列
        self.task_queue: List[BackgroundTask] = []
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # 多模型分析器
        self.multi_analyzer = multi_model_analyzer
        self.analyzer_available = False
        
        # 统计信息
        self.stats = ProcessingStats()
        
        # 运行状态
        self.is_running = False
        self._stop_flag = False
        
    async def initialize(self):
        """初始化引擎"""
        try:
            # 初始化多模型分析器
            try:
                await self.multi_analyzer.initialize()
                self.analyzer_available = True
                self.logger.info("多模型AI分析器初始化成功")
            except Exception as e:
                self.logger.warning(f"多模型分析器初始化失败，将使用智能预筛选: {e}")
                self.analyzer_available = False
            
            self.logger.info("后台任务引擎初始化完成")
            
        except Exception as e:
            self.logger.error(f"后台任务引擎初始化失败: {e}")
            raise
    
    async def start(self):
        """启动引擎"""
        if self.is_running:
            self.logger.warning("后台任务引擎已在运行")
            return
            
        self.is_running = True
        self._stop_flag = False
        
        # 启动任务处理协程
        asyncio.create_task(self._task_processor())
        
        self.logger.info("后台任务引擎已启动")
    
    async def stop(self):
        """停止引擎"""
        self._stop_flag = True
        
        # 等待运行中的任务完成
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        self.is_running = False
        self.logger.info("后台任务引擎已停止")
    
    async def add_feedback_for_processing(self, feedback_ids: List[str], 
                                        task_type: TaskType = TaskType.FULL_AI_ANALYSIS,
                                        priority: int = 5,
                                        model_id: Optional[str] = None) -> List[str]:
        """添加反馈数据到处理队列"""
        task_ids = []
        
        for feedback_id in feedback_ids:
            task_id = f"{task_type.value}_{feedback_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            task = BackgroundTask(
                task_id=task_id,
                task_type=task_type,
                feedback_id=feedback_id,
                priority=priority,
                model_id=model_id
            )
            
            self.task_queue.append(task)
            task_ids.append(task_id)
            self.stats.pending += 1
        
        # 按优先级排序
        self.task_queue.sort(key=lambda x: x.priority, reverse=True)
        
        self.logger.info(f"添加 {len(task_ids)} 个处理任务到队列")
        return task_ids
    
    async def process_new_feedback_batch(self, feedback_ids: List[str], 
                                       model_id: Optional[str] = None) -> Dict[str, Any]:
        """处理新入库的反馈批次"""
        self.logger.info(f"开始处理新入库的 {len(feedback_ids)} 条反馈")
        
        # 添加到处理队列
        task_ids = await self.add_feedback_for_processing(
            feedback_ids, 
            TaskType.FULL_AI_ANALYSIS,
            priority=8,  # 新数据优先级较高
            model_id=model_id
        )
        
        return {
            "added_task_count": len(task_ids),
            "task_ids": task_ids,
            "queue_size": len(self.task_queue),
            "model_id": model_id
        }
    
    async def get_available_ai_models(self) -> List[Dict[str, Any]]:
        """获取可用的AI模型列表"""
        if self.analyzer_available:
            return await self.multi_analyzer.get_available_models()
        return []
    
    async def _task_processor(self):
        """任务处理器（后台协程）"""
        while not self._stop_flag:
            try:
                # 检查是否有待处理任务
                if not self.task_queue:
                    await asyncio.sleep(5)  # 等待5秒
                    continue
                
                # 检查并发限制
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(2)
                    continue
                
                # 获取下一个任务
                task = self.task_queue.pop(0)
                self.stats.pending -= 1
                
                # 创建处理协程
                coro = self._process_single_task(task)
                asyncio_task = asyncio.create_task(coro)
                self.running_tasks[task.task_id] = asyncio_task
                
                # 清理完成的任务
                self._cleanup_completed_tasks()
                
            except Exception as e:
                self.logger.error(f"任务处理器异常: {e}")
                await asyncio.sleep(10)
    
    async def _process_single_task(self, task: BackgroundTask):
        """处理单个任务"""
        try:
            task.started_at = datetime.now()
            task.status = "running"
            
            self.logger.debug(f"开始处理任务: {task.task_id}")
            
            # 获取反馈数据
            feedback = await UserFeedback.get(task.feedback_id)
            if not feedback:
                raise ValueError(f"反馈数据不存在: {task.feedback_id}")
            
            # 根据任务类型执行处理
            if task.task_type == TaskType.FULL_AI_ANALYSIS:
                result = await self._full_ai_analysis(feedback, task.model_id)
            elif task.task_type == TaskType.SENTIMENT_ANALYSIS:
                result = await self._sentiment_analysis(feedback, task.model_id)
            elif task.task_type == TaskType.CATEGORY_CLASSIFICATION:
                result = await self._category_classification(feedback, task.model_id)
            elif task.task_type == TaskType.PRIORITY_CALCULATION:
                result = await self._priority_calculation(feedback, task.model_id)
            elif task.task_type == TaskType.KEYWORD_EXTRACTION:
                result = await self._keyword_extraction(feedback, task.model_id)
            else:
                raise ValueError(f"不支持的任务类型: {task.task_type}")
            
            # 更新反馈数据
            await self._update_feedback_with_result(feedback, result)
            
            # 更新任务状态
            task.completed_at = datetime.now()
            task.status = "completed"
            task.result = result
            
            self.stats.successful += 1
            self.stats.total_processed += 1
            
            self.logger.debug(f"任务完成: {task.task_id}")
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            
            self.stats.failed += 1
            self.stats.total_processed += 1
            
            self.logger.error(f"任务处理失败 {task.task_id}: {e}")
        
        finally:
            # 从运行中任务移除
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
    
    async def _full_ai_analysis(self, feedback: UserFeedback, model_id: Optional[str] = None) -> Dict[str, Any]:
        """完整AI分析"""
        result = {}
        
        # 0. 检查反馈内容是否有效
        content = feedback.content or feedback.original_content or feedback.original_text
        if not content or not content.strip():
            self.logger.error(f"反馈内容为空，无法进行分析: feedback_id={feedback.id}")
            return {
                "sentiment": "neutral",
                "category": "unknown", 
                "keywords": [],
                "priority": "low",
                "ai_confidence": 0.0,
                "analysis_summary": "反馈内容为空，无法分析",
                "suggestions": [],
                "analysis_method": "content_empty",
                "model_used": "none"
            }
        
        # 更新content字段（如果为空）
        if not feedback.content and content:
            feedback.content = content
            await feedback.save()
        
        # 1. 智能预筛选
        try:
            filter_result = await intelligent_filter.filter_feedback(
                content,
                {
                    "source_type": feedback.source.value,
                    "user_info": feedback.user_info or {}
                }
            )
        except Exception as e:
            self.logger.error(f"智能预筛选失败: {e}")
            # 如果预筛选失败，创建默认结果
            class DefaultFilterResult:
                sentiment = "neutral"
                category = "general"
                extracted_keywords = []
                priority_score = 0.5
                confidence = 0.3
                reason = f"预筛选失败: {e}"
            
            filter_result = DefaultFilterResult()
        
        # 2. 强制使用多模型AI分析（如果可用）- 不依赖预筛选判断
        if self.analyzer_available:
            try:
                self.logger.info(f"开始LLM分析，analyzer_available={self.analyzer_available}")
                ai_result = await self.multi_analyzer.analyze_feedback(content, model_id=model_id)
                
                if ai_result.get("success"):
                    result.update({
                        "sentiment": ai_result["sentiment"],
                        "category": ai_result["category"],
                        "keywords": ai_result["keywords"],
                        "priority": ai_result["priority"],
                        "ai_confidence": ai_result["confidence"],
                        "analysis_summary": ai_result["summary"],
                        "suggestions": ai_result["suggestions"],
                        "analysis_method": "multi_model_ai",
                        "model_used": ai_result["model_used"],
                        "processing_time": ai_result["processing_time"]
                    })
                    self.logger.info(f"LLM分析成功: {ai_result['sentiment']}/{ai_result['category']}")
                else:
                    # AI分析失败，降级到预筛选
                    self.logger.warning(f"AI分析失败，降级到预筛选: {ai_result.get('error')}")
                    result.update(self._get_fallback_result(filter_result))
                    
            except Exception as e:
                self.logger.warning(f"AI分析异常，使用预筛选结果: {e}")
                result.update(self._get_fallback_result(filter_result))
        else:
            # 分析器不可用，使用预筛选结果
            self.logger.warning("分析器不可用，使用预筛选结果")
            result.update(self._get_fallback_result(filter_result))
        
        return result
    
    def _get_fallback_result(self, filter_result) -> Dict[str, Any]:
        """获取降级分析结果"""
        return {
            "sentiment": filter_result.sentiment,
            "category": filter_result.category,
            "keywords": filter_result.extracted_keywords,
            "priority": self._convert_priority_score(filter_result.priority_score),
            "ai_confidence": filter_result.confidence,
            "analysis_summary": f"智能预筛选分析：{filter_result.reason}",
            "suggestions": [],
            "analysis_method": "intelligent_filter",
            "model_used": "intelligent_filter"
        }
    
    async def _sentiment_analysis(self, feedback: UserFeedback, model_id: Optional[str] = None) -> Dict[str, Any]:
        """情感分析"""
        if self.analyzer_available:
            try:
                ai_result = await self.multi_analyzer.analyze_feedback(
                    feedback.content, model_id=model_id
                )
                return {"sentiment": ai_result.sentiment, "model_used": ai_result.model_used}
            except Exception:
                pass
        
        # 降级处理
        filter_result = await intelligent_filter.filter_feedback(
            feedback.content,
            {"source_type": feedback.source.value}
        )
        return {"sentiment": filter_result.sentiment, "model_used": "intelligent_filter"}
    
    async def _category_classification(self, feedback: UserFeedback, model_id: Optional[str] = None) -> Dict[str, Any]:
        """分类分析"""
        if self.analyzer_available:
            try:
                ai_result = await self.multi_analyzer.analyze_feedback(
                    feedback.content, model_id=model_id
                )
                return {"category": ai_result.category, "model_used": ai_result.model_used}
            except Exception:
                pass
        
        # 降级处理
        filter_result = await intelligent_filter.filter_feedback(
            feedback.content,
            {"source_type": feedback.source.value}
        )
        return {"category": filter_result.category, "model_used": "intelligent_filter"}
    
    async def _priority_calculation(self, feedback: UserFeedback, model_id: Optional[str] = None) -> Dict[str, Any]:
        """优先级计算"""
        if self.analyzer_available:
            try:
                ai_result = await self.multi_analyzer.analyze_feedback(
                    feedback.content, model_id=model_id
                )
                return {"priority": ai_result.priority, "model_used": ai_result.model_used}
            except Exception:
                pass
        
        # 降级处理
        filter_result = await intelligent_filter.filter_feedback(
            feedback.content,
            {"source_type": feedback.source.value}
        )
        return {"priority": self._convert_priority_score(filter_result.priority_score), "model_used": "intelligent_filter"}
    
    async def _keyword_extraction(self, feedback: UserFeedback, model_id: Optional[str] = None) -> Dict[str, Any]:
        """关键词提取"""
        if self.analyzer_available:
            try:
                ai_result = await self.multi_analyzer.analyze_feedback(
                    feedback.content, model_id=model_id
                )
                return {"keywords": ai_result.keywords, "model_used": ai_result.model_used}
            except Exception:
                pass
        
        # 降级处理
        filter_result = await intelligent_filter.filter_feedback(
            feedback.content,
            {"source_type": feedback.source.value}
        )
        return {"keywords": filter_result.extracted_keywords, "model_used": "intelligent_filter"}
    
    def _convert_priority_score(self, score: float) -> str:
        """转换优先级分数为级别"""
        if score >= 0.8:
            return "high"
        elif score >= 0.5:
            return "medium"
        else:
            return "low"
    
    async def _update_feedback_with_result(self, feedback: UserFeedback, result: Dict[str, Any]):
        """用处理结果更新反馈数据"""
        try:
            # 确保processing_status不为None
            if feedback.processing_status is None:
                feedback.processing_status = {}
            
            # 更新分析结果
            if "sentiment" in result:
                feedback.sentiment = result["sentiment"]
            if "category" in result:
                feedback.category = result["category"]
            if "keywords" in result:
                feedback.keywords = result["keywords"]
            if "priority" in result:
                feedback.priority = result["priority"]
            if "ai_confidence" in result:
                feedback.ai_confidence = result["ai_confidence"]
            
            # 更新处理状态
            feedback.processing_status.update({
                "ai_analyzed": True,
                "sentiment_analyzed": "sentiment" in result,
                "priority_calculated": "priority" in result,
                "categorized": "category" in result,
                "last_ai_analysis": datetime.now(),
                "analysis_method": result.get("analysis_method", "unknown"),
                "model_used": result.get("model_used", "unknown")
            })
            
            # 添加分析元数据
            if not feedback.processing_metadata:
                feedback.processing_metadata = {}
            
            feedback.processing_metadata.update({
                "ai_analysis_result": result,
                "ai_processed_at": datetime.now(),
                "processing_engine": "background_task_engine_v2.0",
                "analyzer_available": self.analyzer_available
            })
            
            # 保存到数据库
            await feedback.save()
            
        except Exception as e:
            self.logger.error(f"更新反馈数据失败: {e}")
            raise
    
    def _cleanup_completed_tasks(self):
        """清理已完成的任务"""
        completed_tasks = []
        for task_id, asyncio_task in self.running_tasks.items():
            if asyncio_task.done():
                completed_tasks.append(task_id)
        
        for task_id in completed_tasks:
            del self.running_tasks[task_id]
    
    def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            "is_running": self.is_running,
            "queue_size": len(self.task_queue),
            "running_tasks": len(self.running_tasks),
            "max_concurrent": self.max_concurrent_tasks,
            "analyzer_available": self.analyzer_available,
            "statistics": {
                "total_processed": self.stats.total_processed,
                "successful": self.stats.successful,
                "failed": self.stats.failed,
                "pending": self.stats.pending,
                "success_rate": round(self.stats.successful / self.stats.total_processed * 100, 2) if self.stats.total_processed > 0 else 0
            }
        }

# 创建全局实例
background_task_engine = BackgroundTaskEngine() 