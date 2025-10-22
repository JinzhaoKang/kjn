"""
数据管道管理器
协调整个分层数据处理流程：原始数据处理 → 后台AI分析 → 反馈系统
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from .raw_data_processor import RawDataProcessor, ProcessingResult
from .background_task_engine import BackgroundTaskEngine, TaskType

logger = logging.getLogger(__name__)

@dataclass
class PipelineResult:
    """管道处理结果"""
    success: bool
    total_input: int
    raw_processed: int
    raw_failed: int
    ai_tasks_created: int
    feedback_ids: List[str]
    errors: List[str]
    processing_time: float
    
class DataPipelineManager:
    """数据管道管理器
    
    协调分层数据处理：
    第一层：爬虫数据 → 清洗预处理 → 入库
    第二层：后台任务 → AI分析 → 更新数据库
    第三层：反馈管理界面 → 展示完整数据
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 处理器组件
        self.raw_processor = RawDataProcessor()
        self.task_engine = BackgroundTaskEngine()
        
        # 初始化状态
        self._initialized = False
    
    async def initialize(self):
        """初始化管道"""
        if self._initialized:
            return
            
        try:
            # 初始化后台任务引擎
            await self.task_engine.initialize()
            await self.task_engine.start()
            
            self._initialized = True
            self.logger.info("数据管道管理器初始化完成")
            
        except Exception as e:
            self.logger.error(f"数据管道管理器初始化失败: {e}")
            raise
    
    async def shutdown(self):
        """关闭管道"""
        if self.task_engine.is_running:
            await self.task_engine.stop()
        
        self._initialized = False
        self.logger.info("数据管道管理器已关闭")
    
    async def process_spider_data(self, 
                                spider_data: List[Dict[str, Any]], 
                                task_metadata: Dict[str, Any] = None,
                                enable_ai_analysis: bool = True) -> PipelineResult:
        """处理爬虫数据（完整管道）"""
        start_time = datetime.now()
        
        self.logger.info(f"开始处理 {len(spider_data)} 条爬虫数据")
        
        if not self._initialized:
            await self.initialize()
        
        try:
            # 第一层：原始数据处理和入库
            self.logger.info("第一层：原始数据处理和入库")
            raw_result = await self.raw_processor.process_spider_batch(
                spider_data, task_metadata
            )
            
            if not raw_result.success:
                return PipelineResult(
                    success=False,
                    total_input=len(spider_data),
                    raw_processed=0,
                    raw_failed=raw_result.failed_count,
                    ai_tasks_created=0,
                    feedback_ids=[],
                    errors=raw_result.errors,
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
            
            # 第二层：添加到后台AI分析队列
            ai_tasks_created = 0
            if enable_ai_analysis and raw_result.feedback_ids:
                self.logger.info(f"第二层：添加 {len(raw_result.feedback_ids)} 条数据到AI分析队列")
                
                ai_result = await self.task_engine.process_new_feedback_batch(
                    raw_result.feedback_ids
                )
                ai_tasks_created = ai_result.get("added_task_count", 0)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = PipelineResult(
                success=True,
                total_input=len(spider_data),
                raw_processed=raw_result.processed_count,
                raw_failed=raw_result.failed_count,
                ai_tasks_created=ai_tasks_created,
                feedback_ids=raw_result.feedback_ids,
                errors=raw_result.errors,
                processing_time=processing_time
            )
            
            self.logger.info(
                f"数据管道处理完成：输入{result.total_input}条，"
                f"成功处理{result.raw_processed}条，"
                f"失败{result.raw_failed}条，"
                f"AI任务{result.ai_tasks_created}个，"
                f"耗时{result.processing_time:.2f}秒"
            )
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(f"数据管道处理失败: {e}")
            
            return PipelineResult(
                success=False,
                total_input=len(spider_data),
                raw_processed=0,
                raw_failed=len(spider_data),
                ai_tasks_created=0,
                feedback_ids=[],
                errors=[str(e)],
                processing_time=processing_time
            )
    
    async def process_raw_data_only(self, 
                                  spider_data: List[Dict[str, Any]], 
                                  task_metadata: Dict[str, Any] = None) -> PipelineResult:
        """仅处理原始数据（第一层），不进行AI分析"""
        return await self.process_spider_data(
            spider_data, task_metadata, enable_ai_analysis=False
        )
    
    async def trigger_ai_analysis(self, feedback_ids: List[str]) -> Dict[str, Any]:
        """手动触发AI分析"""
        if not self._initialized:
            await self.initialize()
        
        return await self.task_engine.process_new_feedback_batch(feedback_ids)
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """获取管道状态"""
        try:
            # 原始数据处理统计
            raw_stats = await self.raw_processor.get_processing_stats()
            
            # 后台任务引擎状态
            engine_status = self.task_engine.get_engine_status()
            
            return {
                "initialized": self._initialized,
                "timestamp": datetime.now().isoformat(),
                "raw_processing": raw_stats,
                "background_engine": engine_status,
                "pipeline_health": {
                    "raw_processor": "healthy",
                    "task_engine": "healthy" if engine_status["is_running"] else "stopped"
                }
            }
            
        except Exception as e:
            return {
                "initialized": self._initialized,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "pipeline_health": "unhealthy"
            }
    
    async def get_processing_queue_info(self) -> Dict[str, Any]:
        """获取处理队列信息"""
        if not self._initialized:
            return {"error": "管道未初始化"}
        
        engine_status = self.task_engine.get_engine_status()
        
        return {
            "queue_size": engine_status["queue_size"],
            "running_tasks": engine_status["running_tasks"],
            "max_concurrent": engine_status["max_concurrent"],
            "engine_running": engine_status["is_running"],
            "statistics": engine_status["statistics"]
        }
    
    async def retry_failed_ai_analysis(self, limit: int = 100) -> Dict[str, Any]:
        """重试失败的AI分析"""
        try:
            # 查找需要AI分析但未处理的反馈
            from ...models.database import UserFeedback
            
            failed_feedback = await UserFeedback.find({
                "processing_status.needs_ai_analysis": True,
                "processing_status.ai_analyzed": False
            }).limit(limit).to_list()
            
            if not failed_feedback:
                return {
                    "message": "没有需要重试的AI分析任务",
                    "retried_count": 0
                }
            
            feedback_ids = [str(feedback.id) for feedback in failed_feedback]
            
            # 添加到处理队列
            ai_result = await self.task_engine.process_new_feedback_batch(feedback_ids)
            
            return {
                "message": f"成功重试 {len(feedback_ids)} 个AI分析任务",
                "retried_count": len(feedback_ids),
                "added_tasks": ai_result.get("added_task_count", 0)
            }
            
        except Exception as e:
            self.logger.error(f"重试AI分析失败: {e}")
            return {"error": str(e)}

# 创建全局实例
data_pipeline_manager = DataPipelineManager() 