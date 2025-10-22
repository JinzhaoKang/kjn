"""
爬虫管理API
提供爬虫任务的创建、运行、监控等功能
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, Body
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from ..services.spider import get_spider_manager, SpiderManager, DataSourcePlatform
from ..services.data_pipeline.data_pipeline_manager import data_pipeline_manager


router = APIRouter(prefix="/api/v1/spider", tags=["爬虫管理"])


# 请求模型
class QimaiTaskRequest(BaseModel):
    """七麦爬虫任务请求 - iOS"""
    appid: str = Field(..., description="应用ID")
    country: str = Field("cn", description="国家代码")
    days_back: int = Field(365, description="回溯天数", ge=1, le=3650)
    max_pages: int = Field(100, description="最大抓取页数", ge=1, le=1000)
    task_name: Optional[str] = Field(None, description="任务名称")


class QimaiAndroidTaskRequest(BaseModel):
    """七麦Android爬虫任务请求"""
    market: str = Field("4", description="应用市场代码", pattern="^[4679]$")
    max_pages: int = Field(100, description="最大抓取页数", ge=1, le=1000)
    task_name: Optional[str] = Field(None, description="任务名称")
    
    class Config:
        schema_extra = {
            "example": {
                "market": "4",
                "max_pages": 100,
                "task_name": "小米应用市场评论抓取"
            }
        }


class TaskControlRequest(BaseModel):
    """任务控制请求"""
    task_id: str = Field(..., description="任务ID")


class BatchTaskRequest(BaseModel):
    """批量任务请求"""
    task_ids: List[str] = Field(..., description="任务ID列表")


class QuickRunRequest(BaseModel):
    """快速运行请求"""
    platform: str = Field(..., description="平台名称")
    app_id: str = Field(..., description="应用ID")
    max_pages: int = Field(3, description="最大页数", ge=1, le=10)
    enable_ai_analysis: bool = Field(True, description="是否启用AI分析")
    ai_model_id: Optional[str] = Field(None, description="指定AI模型ID")
    priority: int = Field(7, description="AI分析优先级", ge=1, le=10)


class SpiderConfig(BaseModel):
    """爬虫配置"""
    platform: str = Field(..., description="平台名称")
    settings: Dict[str, Any] = Field(..., description="爬虫设置")


class BatchAnalysisRequest(BaseModel):
    """批量分析请求"""
    feedback_ids: List[str] = Field(..., description="反馈ID列表")
    ai_model_id: Optional[str] = Field(None, description="指定AI模型ID")
    priority: int = Field(5, description="优先级", ge=1, le=10)


# 响应模型
class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    message: str
    status: str


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    duration: float
    spider_status: Dict[str, Any]
    task_params: Dict[str, Any]
    error: Optional[str]
    result_summary: Optional[Dict[str, Any]]


class SpiderStatisticsResponse(BaseModel):
    """爬虫统计响应"""
    total_tasks: int
    running_tasks: int
    idle_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_created: int
    total_completed: int
    total_failed: int
    max_concurrent: int
    registered_platforms: List[str]


# 依赖注入
def get_spider_manager_dep() -> SpiderManager:
    """获取爬虫管理器依赖"""
    return get_spider_manager()


@router.post("/qimai/create", response_model=TaskResponse)
async def create_qimai_task(
    request: QimaiTaskRequest,
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """创建七麦iOS爬虫任务"""
    try:
        task_id = spider_manager.create_qimai_task(
            appid=request.appid,
            country=request.country,
            days_back=request.days_back,
            max_pages=request.max_pages,
            task_name=request.task_name
        )
        
        return TaskResponse(
            task_id=task_id,
            message="七麦iOS爬虫任务创建成功",
            status="created"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建任务失败: {str(e)}")


@router.post("/qimai-android/create", response_model=TaskResponse)
async def create_qimai_android_task(
    request: QimaiAndroidTaskRequest,
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """创建七麦Android爬虫任务"""
    try:
        # 市场名称映射
        market_names = {
            '4': '小米应用市场',
            '6': '华为应用市场', 
            '7': '魅族应用市场',
            '8': 'vivo应用市场',
            '9': 'oppo应用市场'
        }
        
        market_name = market_names.get(request.market, f'应用市场({request.market})')
        
        task_id = spider_manager.create_qimai_android_task(
            market=request.market,
            max_pages=request.max_pages,
            task_name=request.task_name or f"{market_name}评论抓取"
        )
        
        return TaskResponse(
            task_id=task_id,
            message=f"七麦Android爬虫任务创建成功 - {market_name}",
            status="created"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建Android任务失败: {str(e)}")


@router.post("/task/run", response_model=TaskResponse)
async def run_task(
    request: TaskControlRequest,
    background_tasks: BackgroundTasks,
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """运行爬虫任务（异步执行）"""
    try:
        # 异步运行任务
        task_id = await spider_manager.run_task_async(request.task_id)
        
        return TaskResponse(
            task_id=task_id,
            message="任务开始后台执行",
            status="running"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"运行任务失败: {str(e)}")


@router.post("/task/run-sync")
async def run_task_sync(
    request: TaskControlRequest,
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """同步运行爬虫任务（等待完成）"""
    try:
        result = await spider_manager.run_task(request.task_id)
        
        return {
            "task_id": request.task_id,
            "message": "任务执行完成",
            "status": result.status.value,
            "data_count": len(result.data),
            "errors_count": len(result.errors),
            "duration": result.metrics.duration if result.metrics else 0,
            "success_rate": result.metrics.success_rate if result.metrics else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"运行任务失败: {str(e)}")


@router.post("/task/batch-run")
async def run_multiple_tasks(
    request: BatchTaskRequest,
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """批量运行爬虫任务"""
    try:
        results = await spider_manager.run_multiple_tasks(request.task_ids)
        
        response = []
        for task_id, result in results.items():
            response.append({
                "task_id": task_id,
                "status": result.status.value,
                "data_count": len(result.data),
                "errors_count": len(result.errors),
                "duration": result.metrics.duration if result.metrics else 0
            })
        
        return {
            "message": f"批量运行 {len(request.task_ids)} 个任务完成",
            "results": response
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"批量运行失败: {str(e)}")


@router.post("/task/stop", response_model=TaskResponse)
async def stop_task(
    request: TaskControlRequest,
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """停止爬虫任务"""
    try:
        spider_manager.stop_task(request.task_id)
        
        return TaskResponse(
            task_id=request.task_id,
            message="任务已停止",
            status="stopped"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"停止任务失败: {str(e)}")


@router.post("/task/pause", response_model=TaskResponse)
async def pause_task(
    request: TaskControlRequest,
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """暂停爬虫任务"""
    try:
        spider_manager.pause_task(request.task_id)
        
        return TaskResponse(
            task_id=request.task_id,
            message="任务已暂停",
            status="paused"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"暂停任务失败: {str(e)}")


@router.post("/task/resume", response_model=TaskResponse)
async def resume_task(
    request: TaskControlRequest,
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """恢复爬虫任务"""
    try:
        spider_manager.resume_task(request.task_id)
        
        return TaskResponse(
            task_id=request.task_id,
            message="任务已恢复",
            status="running"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"恢复任务失败: {str(e)}")


@router.post("/task/{task_id}/run", response_model=TaskResponse)
async def run_task_by_id(
    task_id: str,
    background_tasks: BackgroundTasks,
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """通过任务ID运行爬虫任务（RESTful风格）"""
    try:
        # 异步运行任务
        result_task_id = await spider_manager.run_task_async(task_id)
        
        return TaskResponse(
            task_id=result_task_id,
            message="任务开始后台执行",
            status="running"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"运行任务失败: {str(e)}")


@router.post("/task/{task_id}/stop", response_model=TaskResponse)
async def stop_task_by_id(
    task_id: str,
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """通过任务ID停止爬虫任务（RESTful风格）"""
    try:
        spider_manager.stop_task(task_id)
        
        return TaskResponse(
            task_id=task_id,
            message="任务已停止",
            status="stopped"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"停止任务失败: {str(e)}")


@router.post("/task/{task_id}/pause", response_model=TaskResponse)
async def pause_task_by_id(
    task_id: str,
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """通过任务ID暂停爬虫任务（RESTful风格）"""
    try:
        spider_manager.pause_task(task_id)
        
        return TaskResponse(
            task_id=task_id,
            message="任务已暂停",
            status="paused"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"暂停任务失败: {str(e)}")


@router.post("/task/{task_id}/resume", response_model=TaskResponse)
async def resume_task_by_id(
    task_id: str,
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """通过任务ID恢复爬虫任务（RESTful风格）"""
    try:
        spider_manager.resume_task(task_id)
        
        return TaskResponse(
            task_id=task_id,
            message="任务已恢复",
            status="running"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"恢复任务失败: {str(e)}")


@router.get("/task/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """获取任务状态"""
    try:
        status = spider_manager.get_task_status(task_id)
        
        return TaskStatusResponse(**status)
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"获取任务状态失败: {str(e)}")


@router.get("/task/list")
async def list_all_tasks(
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """获取所有任务列表"""
    try:
        tasks = spider_manager.get_all_tasks()
        
        return {
            "total": len(tasks),
            "tasks": tasks
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.get("/task/running")
async def list_running_tasks(
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """获取运行中的任务列表"""
    try:
        tasks = spider_manager.get_running_tasks()
        
        return {
            "total": len(tasks),
            "tasks": tasks
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取运行任务失败: {str(e)}")


@router.delete("/task/cleanup")
async def cleanup_completed_tasks(
    keep_days: int = Query(7, description="保留天数", ge=1, le=365),
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """清理已完成的任务"""
    try:
        cleaned_count = spider_manager.cleanup_completed_tasks(keep_days)
        
        return {
            "message": f"清理了 {cleaned_count} 个过期任务",
            "cleaned_count": cleaned_count,
            "keep_days": keep_days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理任务失败: {str(e)}")


@router.get("/statistics", response_model=SpiderStatisticsResponse)
async def get_spider_statistics(
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """获取爬虫统计信息"""
    try:
        stats = spider_manager.get_statistics()
        
        return SpiderStatisticsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/platforms")
async def get_supported_platforms():
    """获取支持的爬虫平台"""
    try:
        platforms = get_spider_manager().get_supported_platforms()
        return {
            "total": len(platforms),
            "platforms": platforms
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取平台列表失败: {str(e)}")


@router.get("/ai-models")
async def get_available_ai_models():
    """获取可用的AI模型列表"""
    try:
        models = data_pipeline_manager.task_engine.get_available_ai_models()
        return {
            "available": len(models) > 0,
            "total": len(models),
            "models": models,
            "default_model": data_pipeline_manager.task_engine.multi_analyzer.default_model if models else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取AI模型失败: {str(e)}")


@router.post("/qimai/quick-run")
async def qimai_quick_run(request: QuickRunRequest):
    """七麦数据快速爬取（原版，不使用数据管道）"""
    try:
        logger.info(f"启动七麦爬虫: {request.platform}/{request.app_id}")
        
        # 执行爬虫
        result = await get_spider_manager().run_spider(
            spider_name="qimai",
            settings={
                "platform": request.platform,
                "app_id": request.app_id,
                "max_pages": request.max_pages
            }
        )
        
        return {
            "message": "爬取完成",
            "spider": "qimai", 
            "platform": request.platform,
            "app_id": request.app_id,
            "result": result,
            "ai_analysis_enabled": False,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"七麦爬虫执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"爬虫执行失败: {str(e)}")


@router.post("/qimai/quick-run-with-import")
async def qimai_quick_run_with_import(request: QuickRunRequest):
    """七麦数据快速爬取并导入分层处理管道"""
    try:
        logger.info(f"启动七麦爬虫（带管道处理）: {request.platform}/{request.app_id}")
        
        # 执行爬虫
        spider_result = await get_spider_manager().run_spider(
            spider_name="qimai",
            settings={
                "platform": request.platform,
                "app_id": request.app_id,
                "max_pages": request.max_pages
            }
        )
        
        # 处理爬虫结果
        if not spider_result.get("success", False):
            raise HTTPException(status_code=500, detail=f"爬虫执行失败: {spider_result.get('error')}")
        
        # 使用数据管道处理爬虫数据
        raw_data = spider_result.get("data", [])
        if not raw_data:
            return {
                "message": "爬取完成，但没有获取到数据",
                "spider": "qimai",
                "platform": request.platform,
                "app_id": request.app_id,
                "data_count": 0,
                "ai_analysis_enabled": False,
                "timestamp": datetime.now().isoformat()
            }
        
        # 使用数据管道处理
        processing_result = await data_pipeline_manager.process_spider_data(
            spider_data=raw_data,
            task_metadata={
                "spider": "qimai",
                "platform": request.platform,
                "app_id": request.app_id,
                "crawl_time": datetime.now().isoformat()
            },
            enable_ai_analysis=request.enable_ai_analysis
        )
        
        return {
            "message": "爬取和数据处理完成",
            "spider": "qimai",
            "platform": request.platform,
            "app_id": request.app_id,
            "spider_result": {
                "data_count": len(raw_data),
                "execution_time": spider_result.get("execution_time"),
                "pages_crawled": spider_result.get("pages_crawled", 0)
            },
            "pipeline_result": processing_result,
            "ai_analysis": {
                "enabled": request.enable_ai_analysis,
                "model_id": request.ai_model_id,
                "priority": request.priority,
                "queued_tasks": processing_result.get("ai_analysis", {}).get("added_task_count", 0)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"七麦爬虫+管道处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.post("/batch-ai-analysis")
async def trigger_batch_ai_analysis(request: BatchAnalysisRequest):
    """批量触发AI分析"""
    try:
        # 验证AI模型
        if request.ai_model_id:
            available_models = data_pipeline_manager.task_engine.get_available_ai_models()
            model_ids = [m["id"] for m in available_models]
            if request.ai_model_id not in model_ids:
                raise HTTPException(
                    status_code=400, 
                    detail=f"AI模型不存在或不可用: {request.ai_model_id}. 可用模型: {model_ids}"
                )
        
        # 添加AI分析任务
        from ..services.data_pipeline.background_task_engine import TaskType
        task_ids = await data_pipeline_manager.task_engine.add_feedback_for_processing(
            feedback_ids=request.feedback_ids,
            task_type=TaskType.FULL_AI_ANALYSIS,
            priority=request.priority,
            model_id=request.ai_model_id
        )
        
        return {
            "message": f"成功添加 {len(task_ids)} 个AI分析任务",
            "feedback_count": len(request.feedback_ids),
            "task_ids": task_ids,
            "ai_model_id": request.ai_model_id,
            "priority": request.priority,
            "queue_info": await data_pipeline_manager.get_processing_queue_info()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量AI分析失败: {str(e)}")


@router.post("/analyze-all-unprocessed")
async def analyze_all_unprocessed():
    """一键分析所有未处理的反馈数据"""
    try:
        from ..models.database import UserFeedback
        from ..services.data_pipeline.background_task_engine import TaskType
        
        # 查找所有未分析的数据
        unanalyzed_feedback = await UserFeedback.find({
            '$or': [
                {'processing_status.ai_analyzed': {'$ne': True}},
                {'processing_status.ai_analyzed': {'$exists': False}},
                {'sentiment': {'$exists': False}},
                {'category': {'$exists': False}},
                {'priority': {'$exists': False}}
            ]
        }).to_list()
        
        if not unanalyzed_feedback:
            return {
                "message": "所有反馈数据都已完成AI分析",
                "unanalyzed_count": 0,
                "added_tasks": 0,
                "queue_info": await data_pipeline_manager.get_processing_queue_info()
            }
        
        feedback_ids = [str(feedback.id) for feedback in unanalyzed_feedback]
        
        # 添加到处理队列
        task_ids = await data_pipeline_manager.task_engine.add_feedback_for_processing(
            feedback_ids=feedback_ids,
            task_type=TaskType.FULL_AI_ANALYSIS,
            priority=8,  # 高优先级
            model_id=None  # 使用默认模型
        )
        
        return {
            "message": f"成功添加 {len(task_ids)} 个AI分析任务，处理 {len(feedback_ids)} 条未分析反馈",
            "unanalyzed_count": len(feedback_ids),
            "added_tasks": len(task_ids),
            "task_ids": task_ids,
            "queue_info": await data_pipeline_manager.get_processing_queue_info(),
            "analysis_details": {
                "priority": 8,
                "estimated_time": f"{len(feedback_ids) * 5}秒",
                "batch_size": len(feedback_ids)
            }
        }
        
    except Exception as e:
        logger.error(f"一键分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"一键分析失败: {str(e)}")


@router.post("/force-reanalyze-all")
async def force_reanalyze_all():
    """强制重新分析所有反馈数据（使用改进后的AI prompt）"""
    try:
        from ..models.database import UserFeedback
        from ..services.data_pipeline.background_task_engine import TaskType
        
        # 查找所有反馈数据，包括已分析的
        all_feedback = await UserFeedback.find({}).to_list()
        
        if not all_feedback:
            return {
                "message": "没有找到任何反馈数据",
                "total_count": 0,
                "added_tasks": 0,
                "queue_info": await data_pipeline_manager.get_processing_queue_info()
            }
        
        feedback_ids = [str(feedback.id) for feedback in all_feedback]
        
        # 先重置所有数据的AI分析状态，强制重新分析
        await UserFeedback.find({}).update_many({
            '$set': {
                'processing_status.ai_analyzed': False,
                'processing_status.force_reanalyze': True,
                'processing_status.reanalyze_reason': 'improved_prompt_quality'
            }
        })
        
        # 添加到处理队列，使用最高优先级
        task_ids = await data_pipeline_manager.task_engine.add_feedback_for_processing(
            feedback_ids=feedback_ids,
            task_type=TaskType.FULL_AI_ANALYSIS,
            priority=9,  # 最高优先级
            model_id=None  # 使用默认模型
        )
        
        return {
            "message": f"🔄 强制重新分析启动！将使用改进的AI prompt重新分析 {len(feedback_ids)} 条反馈数据",
            "total_count": len(feedback_ids),
            "added_tasks": len(task_ids),
            "task_ids": task_ids,
            "queue_info": await data_pipeline_manager.get_processing_queue_info(),
            "analysis_details": {
                "priority": 9,
                "estimated_time": f"{len(feedback_ids) * 3}秒",
                "batch_size": len(feedback_ids),
                "improvement": "使用优化的关键词提取算法和更精确的情感分析"
            }
        }
        
    except Exception as e:
        logger.error(f"强制重新分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"强制重新分析失败: {str(e)}")


@router.get("/status")
async def get_spider_status():
    """获取爬虫状态"""
    try:
        # 获取爬虫管理器状态
        spider_status = {
            "supported_platforms": get_spider_manager().get_supported_platforms(),
            "manager_initialized": True
        }
        
        # 获取数据管道状态
        pipeline_status = data_pipeline_manager.get_pipeline_status()
        
        # 获取AI模型状态
        ai_models = data_pipeline_manager.task_engine.get_available_ai_models()
        
        return {
            "spider_manager": spider_status,
            "data_pipeline": pipeline_status,
            "ai_capabilities": {
                "models_available": len(ai_models),
                "models": ai_models,
                "analyzer_enabled": pipeline_status["background_engine"]["analyzer_available"]
            },
            "integration_status": "fully_integrated",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.get("/processing-stats")
async def get_spider_processing_stats():
    """获取爬虫数据处理统计信息"""
    try:
        # 获取后台任务引擎状态
        engine_status = data_pipeline_manager.task_engine.get_engine_status()
        
        return {
            "success": True,
            "data": {
                "queue_size": engine_status["queue_size"],
                "running_tasks": engine_status["running_tasks"],
                "max_concurrent": engine_status["max_concurrent"],
                "engine_running": engine_status["is_running"],
                "analyzer_available": engine_status["analyzer_available"],
                "statistics": engine_status["statistics"]
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"获取统计信息失败: {str(e)}",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }


@router.post("/config")
async def configure_spider(request: SpiderConfig):
    """配置爬虫"""
    try:
        # 验证平台
        supported = get_spider_manager().get_supported_platforms()
        if request.platform not in [p["name"] for p in supported]:
            raise HTTPException(status_code=400, detail=f"不支持的平台: {request.platform}")
        
        # TODO: 实现爬虫配置逻辑
        return {
            "message": f"爬虫配置更新成功: {request.platform}",
            "platform": request.platform,
            "settings": request.settings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置爬虫失败: {str(e)}")


@router.get("/test-pipeline")
async def test_pipeline_integration():
    """测试管道集成"""
    try:
        # 检查数据管道状态
        pipeline_status = data_pipeline_manager.get_pipeline_status()
        
        # 检查AI分析器
        ai_models = data_pipeline_manager.task_engine.get_available_ai_models()
        
        # 模拟测试数据
        test_data = [{
            "content": "这个应用很好用，界面设计不错，但是加载速度有点慢",
            "user_info": {"rating": 4},
            "timestamp": datetime.now().isoformat()
        }]
        
        # 测试处理管道
        test_result = await data_pipeline_manager.process_spider_data(
            spider_data=test_data,
            task_metadata={
                "spider": "test",
                "platform": "test_platform",
                "app_id": "test_app"
            },
            enable_ai_analysis=True
        )
        
        return {
            "pipeline_integration": "success",
            "pipeline_status": pipeline_status["initialized"],
            "ai_analyzer_available": len(ai_models) > 0,
            "test_processing": test_result,
            "capabilities": {
                "raw_processing": True,
                "ai_analysis": len(ai_models) > 0,
                "queue_management": True
            }
        }
        
    except Exception as e:
        return {
            "pipeline_integration": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.post("/task/{task_id}/import-data")
async def import_spider_data(
    task_id: str,
    enable_ai_analysis: bool = Query(True, description="是否启用AI分析"),
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """将爬虫数据导入到系统（使用分层数据管道）"""
    try:
        # 获取任务状态
        task_status = spider_manager.get_task_status(task_id)
        
        if task_status["status"] != "completed":
            raise HTTPException(status_code=400, detail="任务尚未完成，无法导入数据")
        
        # 获取任务结果
        task = spider_manager.tasks[task_id]
        if not task.result or not task.result.data:
            raise HTTPException(status_code=400, detail="任务没有可导入的数据")
        
        # 使用数据管道处理
        pipeline_result = await data_pipeline_manager.process_spider_data(
            spider_data=task.result.data,
            task_metadata={
                "spider_task_id": task_id,
                "spider_platform": task.spider.config.platform.value,
                "import_time": datetime.now().isoformat(),
                "task_params": task.task_params
            },
            enable_ai_analysis=enable_ai_analysis
        )
        
        return {
            "message": "爬虫数据导入成功（分层处理）",
            "task_id": task_id,
            "pipeline_result": {
                "success": pipeline_result.success,
                "total_input": pipeline_result.total_input,
                "raw_processed": pipeline_result.raw_processed,
                "raw_failed": pipeline_result.raw_failed,
                "ai_tasks_created": pipeline_result.ai_tasks_created,
                "processing_time": pipeline_result.processing_time
            },
            "feedback_ids": pipeline_result.feedback_ids,
            "processing_layers": {
                "layer_1_raw_processing": "completed",
                "layer_2_ai_analysis": "queued" if enable_ai_analysis else "skipped"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入数据失败: {str(e)}")


@router.get("/task/{task_id}/preview")
async def preview_spider_data(
    task_id: str,
    limit: int = Query(10, description="预览数量", ge=1, le=100),
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """预览爬虫数据"""
    try:
        # 获取任务
        if task_id not in spider_manager.tasks:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task = spider_manager.tasks[task_id]
        
        if not task.result:
            raise HTTPException(status_code=400, detail="任务尚未完成或没有结果")
        
        # 预览数据
        preview_data = task.result.data[:limit]
        
        return {
            "task_id": task_id,
            "total_count": len(task.result.data),
            "preview_count": len(preview_data),
            "preview_data": preview_data,
            "task_info": {
                "status": task.status.value,
                "platform": task.spider.config.platform.value,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览数据失败: {str(e)}")


# 快捷创建和运行
@router.post("/qimai/quick-run")
async def quick_run_qimai_spider(
    request: QimaiTaskRequest,
    background_tasks: BackgroundTasks,
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """快速创建并运行七麦爬虫"""
    try:
        # 创建任务
        task_id = spider_manager.create_qimai_task(
            appid=request.appid,
            country=request.country,
            days_back=request.days_back,
            max_pages=request.max_pages,
            task_name=request.task_name
        )
        
        # 异步运行任务
        await spider_manager.run_task_async(task_id)
        
        return {
            "task_id": task_id,
            "message": "七麦爬虫任务创建并开始执行",
            "status": "running",
            "app_info": {
                "appid": request.appid,
                "country": request.country,
                "days_back": request.days_back,
                "max_pages": request.max_pages
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"快速运行失败: {str(e)}")


@router.post("/qimai/quick-run-with-import")
async def quick_run_qimai_spider_with_import(
    request: QimaiTaskRequest,
    background_tasks: BackgroundTasks,
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """快速创建并运行七麦爬虫，自动导入数据到数据库"""
    try:
        # 创建任务
        task_id = spider_manager.create_qimai_task(
            appid=request.appid,
            country=request.country,
            days_back=request.days_back,
            max_pages=request.max_pages,
            task_name=request.task_name
        )
        
        # 同步运行任务并等待完成
        result = await spider_manager.run_task(task_id)
        
        # 自动导入数据（使用数据管道）
        if result.data:
            pipeline_result = await data_pipeline_manager.process_spider_data(
                spider_data=result.data,
                task_metadata={
                    "spider_task_id": task_id,
                    "spider_platform": spider_manager.tasks[task_id].spider.config.platform.value,
                    "import_time": datetime.now().isoformat(),
                    "app_info": {
                        "appid": request.appid,
                        "country": request.country
                    }
                },
                enable_ai_analysis=True
            )
            
            return {
                "task_id": task_id,
                "message": "七麦爬虫任务完成并成功导入数据",
                "status": "completed_with_import",
                "app_info": {
                    "appid": request.appid,
                    "country": request.country,
                    "days_back": request.days_back,
                    "max_pages": request.max_pages
                },
                "spider_result": {
                    "data_count": len(result.data),
                    "errors_count": len(result.errors),
                    "duration": result.metrics.duration if result.metrics else 0,
                    "success_rate": result.metrics.success_rate if result.metrics else 0
                },
                "pipeline_result": {
                    "raw_processed": pipeline_result.raw_processed,
                    "raw_failed": pipeline_result.raw_failed,
                    "ai_tasks_created": pipeline_result.ai_tasks_created,
                    "processing_time": pipeline_result.processing_time,
                    "success_rate": round(pipeline_result.raw_processed / pipeline_result.total_input * 100, 2) if pipeline_result.total_input > 0 else 0
                }
            }
        else:
            return {
                "task_id": task_id,
                "message": "七麦爬虫任务完成，但没有数据可导入",
                "status": "completed_no_data",
                "app_info": {
                    "appid": request.appid,
                    "country": request.country,
                    "days_back": request.days_back,
                    "max_pages": request.max_pages
                },
                "spider_result": {
                    "data_count": 0,
                    "errors_count": len(result.errors),
                    "duration": result.metrics.duration if result.metrics else 0
                }
            }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"快速运行和导入失败: {str(e)}")


@router.post("/qimai-android/quick-run-with-import")
async def quick_run_qimai_android_spider_with_import(
    request: QimaiAndroidTaskRequest,
    background_tasks: BackgroundTasks,
    spider_manager: SpiderManager = Depends(get_spider_manager_dep)
):
    """快速创建并运行七麦Android爬虫，自动导入数据到数据库"""
    try:
        # 市场名称映射
        market_names = {
            '4': '小米应用市场',
            '6': '华为应用市场', 
            '7': '魅族应用市场',
            '8': 'vivo应用市场',
            '9': 'oppo应用市场'
        }
        
        market_name = market_names.get(request.market, f'应用市场({request.market})')
        
        # 创建任务
        task_id = spider_manager.create_qimai_android_task(
            market=request.market,
            max_pages=request.max_pages,
            task_name=request.task_name or f"{market_name}评论抓取"
        )
        
        # 同步运行任务并等待完成
        result = await spider_manager.run_task(task_id)
        
        # 自动导入数据（使用数据管道）
        if result.data:
            pipeline_result = await data_pipeline_manager.process_spider_data(
                spider_data=result.data,
                task_metadata={
                    "spider_task_id": task_id,
                    "spider_platform": spider_manager.tasks[task_id].spider.config.platform.value,
                    "import_time": datetime.now().isoformat(),
                    "market_info": {
                        "market": request.market,
                        "market_name": market_name
                    }
                },
                enable_ai_analysis=True
            )
            
            return {
                "task_id": task_id,
                "message": f"七麦Android爬虫任务完成并成功导入数据 - {market_name}",
                "status": "completed_with_import",
                "market_info": {
                    "market": request.market,
                    "market_name": market_name,
                    "max_pages": request.max_pages
                },
                "spider_result": {
                    "data_count": len(result.data),
                    "errors_count": len(result.errors),
                    "duration": result.metrics.duration if result.metrics else 0,
                    "success_rate": result.metrics.success_rate if result.metrics else 0
                },
                "pipeline_result": {
                    "raw_processed": pipeline_result.raw_processed,
                    "raw_failed": pipeline_result.raw_failed,
                    "ai_tasks_created": pipeline_result.ai_tasks_created,
                    "processing_time": pipeline_result.processing_time,
                    "success_rate": round(pipeline_result.raw_processed / pipeline_result.total_input * 100, 2) if pipeline_result.total_input > 0 else 0
                }
            }
        else:
            return {
                "task_id": task_id,
                "message": f"七麦Android爬虫任务完成，但没有数据可导入 - {market_name}",
                "status": "completed_no_data",
                "market_info": {
                    "market": request.market,
                    "market_name": market_name,
                    "max_pages": request.max_pages
                },
                "spider_result": {
                    "data_count": 0,
                    "errors_count": len(result.errors),
                    "duration": result.metrics.duration if result.metrics else 0
                }
            }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"快速运行和导入失败: {str(e)}")


@router.get("/health")
async def spider_health_check():
    """爬虫系统健康检查"""
    try:
        spider_manager = get_spider_manager()
        stats = spider_manager.get_statistics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "spider_manager": {
                "total_tasks": stats["total_tasks"],
                "running_tasks": stats["running_tasks"],
                "max_concurrent": stats["max_concurrent"]
            },
            "supported_platforms": list(spider_manager.spider_registry.keys())
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        } 