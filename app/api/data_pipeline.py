"""
数据管道管理API
提供分层数据处理管道的监控、管理和状态查询功能
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from ..services.data_pipeline.data_pipeline_manager import data_pipeline_manager
from ..services.data_pipeline.background_task_engine import TaskType

router = APIRouter(prefix="/api/v1/data-pipeline", tags=["数据管道"])

# 请求模型
class TriggerAIAnalysisRequest(BaseModel):
    """触发AI分析请求"""
    feedback_ids: List[str] = Field(..., description="反馈ID列表")
    task_type: str = Field("full_ai_analysis", description="任务类型")
    priority: int = Field(5, description="优先级", ge=1, le=10)
    model_id: Optional[str] = Field(None, description="指定AI模型ID")

class PipelineControlRequest(BaseModel):
    """管道控制请求"""
    action: str = Field(..., description="操作类型", pattern="^(start|stop|restart|initialize)$")

class ModelConfigRequest(BaseModel):
    """模型配置请求"""
    model_id: str = Field(..., description="模型ID")
    enabled: Optional[bool] = Field(None, description="是否启用")
    as_default: Optional[bool] = Field(None, description="设为默认模型")

# 响应模型
class PipelineStatusResponse(BaseModel):
    """管道状态响应"""
    initialized: bool
    timestamp: str
    raw_processing: Dict[str, Any]
    background_engine: Dict[str, Any]
    pipeline_health: Dict[str, str]

class QueueInfoResponse(BaseModel):
    """队列信息响应"""
    queue_size: int
    running_tasks: int
    max_concurrent: int
    engine_running: bool
    statistics: Dict[str, Any]

@router.get("/status", response_model=PipelineStatusResponse)
async def get_pipeline_status():
    """获取数据管道状态"""
    try:
        status = await data_pipeline_manager.get_pipeline_status()
        return PipelineStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取管道状态失败: {str(e)}")

@router.get("/queue-info", response_model=QueueInfoResponse) 
async def get_queue_info():
    """获取处理队列信息"""
    try:
        queue_info = await data_pipeline_manager.get_processing_queue_info()
        return QueueInfoResponse(**queue_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取队列信息失败: {str(e)}")

@router.post("/control")
async def control_pipeline(request: PipelineControlRequest):
    """控制数据管道"""
    try:
        if request.action == "initialize":
            await data_pipeline_manager.initialize()
            return {"message": "数据管道初始化成功", "action": request.action}
        
        elif request.action == "start":
            await data_pipeline_manager.task_engine.start()
            return {"message": "后台任务引擎已启动", "action": request.action}
        
        elif request.action == "stop":
            await data_pipeline_manager.task_engine.stop()
            return {"message": "后台任务引擎已停止", "action": request.action}
        
        elif request.action == "restart":
            await data_pipeline_manager.task_engine.stop()
            await data_pipeline_manager.task_engine.start()
            return {"message": "后台任务引擎已重启", "action": request.action}
        
        else:
            raise HTTPException(status_code=400, detail=f"不支持的操作: {request.action}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"控制管道失败: {str(e)}")

@router.post("/trigger-ai-analysis")
async def trigger_ai_analysis(request: TriggerAIAnalysisRequest):
    """手动触发AI分析"""
    try:
        # 验证任务类型
        try:
            task_type = TaskType(request.task_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的任务类型: {request.task_type}")
        
        # 添加任务到队列
        task_ids = await data_pipeline_manager.task_engine.add_feedback_for_processing(
            feedback_ids=request.feedback_ids,
            task_type=task_type,
            priority=request.priority,
            model_id=request.model_id
        )
        
        return {
            "message": f"成功添加 {len(task_ids)} 个AI分析任务",
            "task_ids": task_ids,
            "feedback_count": len(request.feedback_ids),
            "task_type": request.task_type,
            "priority": request.priority,
            "model_id": request.model_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发AI分析失败: {str(e)}")

@router.get("/ai-models")
async def get_available_ai_models():
    """获取可用的AI模型列表"""
    try:
        models = await data_pipeline_manager.task_engine.get_available_ai_models()
        
        # 获取模型统计信息
        if data_pipeline_manager.task_engine.analyzer_available:
            stats = data_pipeline_manager.task_engine.multi_analyzer.get_model_stats()
        else:
            stats = {"total_models": 0, "enabled_models": 0}
        
        return {
            "available": True if models else False,
            "total_models": len(models),
            "models": models,
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取AI模型列表失败: {str(e)}")

@router.post("/ai-models/configure")
async def configure_ai_model(request: ModelConfigRequest):
    """配置AI模型"""
    try:
        if not data_pipeline_manager.task_engine.analyzer_available:
            raise HTTPException(status_code=400, detail="AI分析器不可用")
        
        analyzer = data_pipeline_manager.task_engine.multi_analyzer
        
        # 检查模型是否存在
        if request.model_id not in analyzer.models:
            raise HTTPException(status_code=404, detail=f"模型不存在: {request.model_id}")
        
        config = analyzer.models[request.model_id]
        
        # 更新配置
        if request.enabled is not None:
            config.enabled = request.enabled
        
        if request.as_default and config.enabled:
            analyzer.set_default_model(request.model_id)
        
        return {
            "message": f"模型配置更新成功: {request.model_id}",
            "model_id": request.model_id,
            "enabled": config.enabled,
            "is_default": analyzer.default_model == request.model_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置模型失败: {str(e)}")

@router.post("/retry-failed-analysis")
async def retry_failed_analysis(
    limit: int = Query(100, description="重试数量限制", ge=1, le=1000),
    model_id: Optional[str] = Query(None, description="指定使用的AI模型")
):
    """重试失败的AI分析"""
    try:
        result = await data_pipeline_manager.retry_failed_ai_analysis(limit)
        
        # 如果指定了模型，使用指定模型重新分析
        if model_id and result.get("retried_count", 0) > 0:
            result["using_model"] = model_id
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重试失败分析失败: {str(e)}")

@router.get("/processing-stats")
async def get_processing_stats():
    """获取处理统计信息"""
    try:
        # 获取原始数据处理统计
        raw_stats = await data_pipeline_manager.raw_processor.get_processing_stats()
        
        # 获取后台任务引擎状态
        engine_status = data_pipeline_manager.task_engine.get_engine_status()
        
        # 计算综合统计
        total_feedback = raw_stats.get("total_feedback_count", 0)
        ai_analyzed = raw_stats.get("ai_analyzed_count", 0)
        processing_rate = round(ai_analyzed / total_feedback * 100, 2) if total_feedback > 0 else 0
        
        return {
            "summary": {
                "total_feedback": total_feedback,
                "raw_processed": raw_stats.get("raw_processed_count", 0),
                "needs_ai_analysis": raw_stats.get("needs_ai_analysis_count", 0),
                "ai_analyzed": ai_analyzed,
                "processing_completion_rate": processing_rate
            },
            "raw_processing": raw_stats,
            "background_tasks": engine_status["statistics"],
            "queue_status": {
                "queue_size": engine_status["queue_size"],
                "running_tasks": engine_status["running_tasks"],
                "max_concurrent": engine_status["max_concurrent"]
            },
            "ai_capabilities": {
                "analyzer_available": engine_status["analyzer_available"],
                "models_count": len(await data_pipeline_manager.task_engine.get_available_ai_models())
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取处理统计失败: {str(e)}")

@router.get("/supported-task-types")
async def get_supported_task_types():
    """获取支持的任务类型"""
    task_types = [
        {
            "type": "sentiment_analysis",
            "name": "情感分析",
            "description": "分析反馈的情感倾向"
        },
        {
            "type": "category_classification",
            "name": "分类分析",
            "description": "对反馈进行业务分类"
        },
        {
            "type": "priority_calculation",
            "name": "优先级计算",
            "description": "计算反馈的处理优先级"
        },
        {
            "type": "keyword_extraction",
            "name": "关键词提取",
            "description": "提取反馈中的关键词"
        },
        {
            "type": "full_ai_analysis",
            "name": "完整AI分析",
            "description": "执行完整的AI分析流程"
        }
    ]
    
    return {
        "total": len(task_types),
        "task_types": task_types
    }

@router.get("/health")
async def pipeline_health_check():
    """数据管道健康检查"""
    try:
        status = await data_pipeline_manager.get_pipeline_status()
        
        # 检查各组件健康状态
        health_checks = {
            "pipeline_manager": "healthy" if status["initialized"] else "not_initialized",
            "raw_processor": status["pipeline_health"]["raw_processor"],
            "task_engine": status["pipeline_health"]["task_engine"],
            "background_tasks": "healthy" if status["background_engine"]["is_running"] else "stopped",
            "ai_analyzer": "healthy" if status["background_engine"]["analyzer_available"] else "unavailable"
        }
        
        overall_health = "healthy" if all(h in ["healthy"] for h in health_checks.values()) else "degraded"
        
        return {
            "status": overall_health,
            "timestamp": datetime.now().isoformat(),
            "components": health_checks,
            "details": {
                "initialized": status["initialized"],
                "queue_size": status["background_engine"]["queue_size"],
                "running_tasks": status["background_engine"]["running_tasks"],
                "total_processed": status["background_engine"]["statistics"]["total_processed"],
                "ai_models_available": len(await data_pipeline_manager.task_engine.get_available_ai_models())
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.post("/initialize")
async def initialize_pipeline():
    """手动初始化数据管道"""
    try:
        await data_pipeline_manager.initialize()
        return {
            "message": "数据管道初始化成功",
            "timestamp": datetime.now().isoformat(),
            "status": "initialized"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化管道失败: {str(e)}")

@router.post("/shutdown")
async def shutdown_pipeline():
    """关闭数据管道"""
    try:
        await data_pipeline_manager.shutdown()
        return {
            "message": "数据管道已关闭",
            "timestamp": datetime.now().isoformat(),
            "status": "shutdown"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"关闭管道失败: {str(e)}")

@router.get("/architecture")
async def get_pipeline_architecture():
    """获取数据管道架构信息"""
    return {
        "architecture": {
            "layer_1": {
                "name": "原始数据处理层",
                "description": "爬虫数据清洗、标准化、入库",
                "components": ["RawDataProcessor", "FeedbackPreprocessor"],
                "responsibilities": [
                    "数据清洗和标准化",
                    "质量检查和过滤", 
                    "数据格式统一",
                    "入库前预处理"
                ]
            },
            "layer_2": {
                "name": "后台AI处理层",
                "description": "AI分析、情感分析、优先级计算",
                "components": ["BackgroundTaskEngine", "MultiModelAnalyzer", "IntelligentFilter"],
                "responsibilities": [
                    "AI情感分析",
                    "内容分类",
                    "优先级计算",
                    "关键词提取",
                    "综合AI分析"
                ]
            },
            "layer_3": {
                "name": "反馈管理层",
                "description": "完整数据展示和管理",
                "components": ["FeedbackManagement", "Dashboard", "Reports"],
                "responsibilities": [
                    "反馈数据展示",
                    "分析结果可视化",
                    "管理界面交互",
                    "报表生成"
                ]
            }
        },
        "data_flow": [
            "爬虫原始数据 → 数据清洗预处理 → 入库",
            "入库数据 → 后台AI分析队列 → AI处理",
            "AI分析结果 → 更新数据库 → 反馈管理界面展示"
        ],
        "ai_models": {
            "supported_providers": ["OpenAI", "Google", "Local", "Custom"],
            "current_status": "多模型支持，动态选择",
            "fallback_strategy": "智能预筛选降级处理"
        }
    } 