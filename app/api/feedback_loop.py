"""
闭环学习API
提供反馈循环、模型性能监控和学习洞察的API接口
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import logging

from ..services.feedback_loop.feedback_loop_engine import (
    get_feedback_loop_engine,
    FeedbackLoopEngine,
    ExecutionResult,
    ModelPerformance,
    LearningInsight
)
from ..core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feedback-loop", tags=["闭环学习"])

# 请求模型
class ExecutionResultRequest(BaseModel):
    """执行结果请求"""
    action_id: str = Field(..., description="行动项ID")
    execution_status: str = Field(..., description="执行状态")
    actual_effort: float = Field(..., description="实际工作量")
    user_satisfaction_change: float = Field(..., description="用户满意度变化")
    actual_roi: float = Field(..., description="实际ROI")
    completion_time: datetime = Field(..., description="完成时间")
    quality_score: float = Field(..., description="质量评分")
    user_feedback_post: List[str] = Field(default=[], description="执行后用户反馈")
    metrics_improvement: Dict = Field(default={}, description="关键指标改善情况")

class LearningConfigRequest(BaseModel):
    """学习配置请求"""
    learning_rate: float = Field(default=0.1, description="学习率")
    performance_threshold: float = Field(default=0.8, description="性能阈值")
    insight_confidence_threshold: float = Field(default=0.7, description="洞察置信度阈值")

# 响应模型
class PerformanceSummaryResponse(BaseModel):
    """性能摘要响应"""
    latest_performance: Dict
    total_executions: int
    total_insights: int
    recent_insights: List[Dict]

class LearningRecommendationResponse(BaseModel):
    """学习建议响应"""
    recommendations: List[Dict]
    total_count: int
    high_priority_count: int

# 依赖注入
def get_feedback_loop_engine_instance() -> FeedbackLoopEngine:
    """获取反馈循环引擎实例"""
    settings = get_settings()
    config = {
        "learning_rate": 0.1,
        "performance_threshold": 0.8,
        "insight_confidence_threshold": 0.7
    }
    return get_feedback_loop_engine(config)

@router.post("/execution-result", summary="记录执行结果")
async def record_execution_result(
    request: ExecutionResultRequest,
    engine: FeedbackLoopEngine = Depends(get_feedback_loop_engine_instance)
):
    """记录行动项的执行结果，触发闭环学习"""
    try:
        # 转换为ExecutionResult对象
        execution_result = ExecutionResult(
            action_id=request.action_id,
            execution_status=request.execution_status,
            actual_effort=request.actual_effort,
            user_satisfaction_change=request.user_satisfaction_change,
            actual_roi=request.actual_roi,
            completion_time=request.completion_time,
            quality_score=request.quality_score,
            user_feedback_post=request.user_feedback_post,
            metrics_improvement=request.metrics_improvement
        )
        
        # 记录执行结果并触发学习
        await engine.record_execution_result(execution_result)
        
        return {
            "success": True,
            "message": "执行结果记录成功，已触发闭环学习",
            "action_id": request.action_id,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"记录执行结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"记录执行结果失败: {str(e)}")

@router.get("/performance-summary", summary="获取性能摘要")
async def get_performance_summary(
    engine: FeedbackLoopEngine = Depends(get_feedback_loop_engine_instance)
) -> PerformanceSummaryResponse:
    """获取模型性能摘要和学习洞察"""
    try:
        summary = await engine.get_performance_summary()
        
        return PerformanceSummaryResponse(
            latest_performance=summary.get("latest_performance", {}),
            total_executions=summary.get("total_executions", 0),
            total_insights=summary.get("total_insights", 0),
            recent_insights=summary.get("recent_insights", [])
        )
        
    except Exception as e:
        logger.error(f"获取性能摘要失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取性能摘要失败: {str(e)}")

@router.get("/learning-recommendations", summary="获取学习建议")
async def get_learning_recommendations(
    engine: FeedbackLoopEngine = Depends(get_feedback_loop_engine_instance)
) -> LearningRecommendationResponse:
    """获取基于学习洞察的优化建议"""
    try:
        recommendations = await engine.get_learning_recommendations()
        
        high_priority_count = sum(1 for rec in recommendations if rec.get("priority") == "high")
        
        return LearningRecommendationResponse(
            recommendations=recommendations,
            total_count=len(recommendations),
            high_priority_count=high_priority_count
        )
        
    except Exception as e:
        logger.error(f"获取学习建议失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取学习建议失败: {str(e)}")

@router.get("/model-performance-history", summary="获取模型性能历史")
async def get_model_performance_history(
    limit: int = 10,
    engine: FeedbackLoopEngine = Depends(get_feedback_loop_engine_instance)
):
    """获取模型性能历史记录"""
    try:
        history = engine.model_performance_history[-limit:]
        
        return {
            "performance_history": [
                {
                    "priority_prediction_accuracy": p.priority_prediction_accuracy,
                    "roi_prediction_mae": p.roi_prediction_mae,
                    "effort_prediction_mse": p.effort_prediction_mse,
                    "satisfaction_correlation": p.satisfaction_correlation,
                    "model_version": p.model_version,
                    "evaluation_date": p.evaluation_date
                }
                for p in history
            ],
            "total_records": len(engine.model_performance_history)
        }
        
    except Exception as e:
        logger.error(f"获取模型性能历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型性能历史失败: {str(e)}")

@router.get("/learning-insights", summary="获取学习洞察")
async def get_learning_insights(
    insight_type: Optional[str] = None,
    min_confidence: float = 0.0,
    limit: int = 20,
    engine: FeedbackLoopEngine = Depends(get_feedback_loop_engine_instance)
):
    """获取学习洞察列表"""
    try:
        insights = engine.learning_insights
        
        # 过滤条件
        if insight_type:
            insights = [i for i in insights if i.insight_type == insight_type]
        
        if min_confidence > 0:
            insights = [i for i in insights if i.confidence >= min_confidence]
        
        # 按置信度排序
        insights.sort(key=lambda x: x.confidence, reverse=True)
        
        # 限制数量
        insights = insights[:limit]
        
        return {
            "insights": [
                {
                    "insight_type": insight.insight_type,
                    "description": insight.description,
                    "impact_score": insight.impact_score,
                    "confidence": insight.confidence,
                    "suggested_actions": insight.suggested_actions,
                    "data_evidence": insight.data_evidence
                }
                for insight in insights
            ],
            "total_count": len(engine.learning_insights),
            "filtered_count": len(insights)
        }
        
    except Exception as e:
        logger.error(f"获取学习洞察失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取学习洞察失败: {str(e)}")

@router.get("/execution-analytics", summary="获取执行分析")
async def get_execution_analytics(
    engine: FeedbackLoopEngine = Depends(get_feedback_loop_engine_instance)
):
    """获取执行结果的分析统计"""
    try:
        history = engine.execution_history
        
        if not history:
            return {"message": "暂无执行数据"}
        
        # 计算统计指标
        total_executions = len(history)
        successful_executions = sum(1 for r in history if r.execution_status == 'completed')
        success_rate = successful_executions / total_executions if total_executions > 0 else 0
        
        # ROI统计
        roi_values = [r.actual_roi for r in history]
        avg_roi = sum(roi_values) / len(roi_values) if roi_values else 0
        
        # 工作量统计
        effort_values = [r.actual_effort for r in history]
        avg_effort = sum(effort_values) / len(effort_values) if effort_values else 0
        
        # 满意度统计
        satisfaction_values = [r.user_satisfaction_change for r in history]
        avg_satisfaction_change = sum(satisfaction_values) / len(satisfaction_values) if satisfaction_values else 0
        
        return {
            "total_executions": total_executions,
            "success_rate": round(success_rate, 3),
            "avg_roi": round(avg_roi, 3),
            "avg_effort": round(avg_effort, 3),
            "avg_satisfaction_change": round(avg_satisfaction_change, 3),
            "high_roi_count": sum(1 for roi in roi_values if roi > 1.5),
            "low_effort_count": sum(1 for effort in effort_values if effort < 0.5),
            "positive_satisfaction_count": sum(1 for sat in satisfaction_values if sat > 0)
        }
        
    except Exception as e:
        logger.error(f"获取执行分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取执行分析失败: {str(e)}")

@router.post("/simulate-execution", summary="模拟执行结果")
async def simulate_execution_result(
    action_count: int = 5,
    engine: FeedbackLoopEngine = Depends(get_feedback_loop_engine_instance)
):
    """模拟执行结果用于测试闭环学习功能"""
    try:
        import random
        
        simulated_results = []
        
        for i in range(action_count):
            # 模拟执行结果
            execution_result = ExecutionResult(
                action_id=f"action_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                execution_status=random.choice(['completed', 'completed', 'completed', 'in_progress', 'failed']),
                actual_effort=random.uniform(0.2, 1.5),
                user_satisfaction_change=random.uniform(-0.5, 0.8),
                actual_roi=random.uniform(0.1, 2.5),
                completion_time=datetime.now(),
                quality_score=random.uniform(0.6, 1.0),
                user_feedback_post=[f"模拟用户反馈{i}"],
                metrics_improvement={
                    "conversion_rate": random.uniform(-0.1, 0.3),
                    "user_engagement": random.uniform(-0.2, 0.4)
                }
            )
            
            # 记录执行结果
            await engine.record_execution_result(execution_result)
            simulated_results.append(execution_result.action_id)
        
        return {
            "success": True,
            "message": f"成功模拟{action_count}个执行结果",
            "simulated_actions": simulated_results,
            "total_history_count": len(engine.execution_history)
        }
        
    except Exception as e:
        logger.error(f"模拟执行结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"模拟执行结果失败: {str(e)}")

@router.get("/system-health", summary="系统健康检查")
async def get_system_health(
    engine: FeedbackLoopEngine = Depends(get_feedback_loop_engine_instance)
):
    """获取闭环学习系统的健康状态"""
    try:
        # 系统健康指标
        health_status = {
            "engine_status": "healthy",
            "execution_history_count": len(engine.execution_history),
            "performance_history_count": len(engine.model_performance_history),
            "learning_insights_count": len(engine.learning_insights),
            "recent_activity": {
                "last_execution": engine.execution_history[-1].completion_time if engine.execution_history else None,
                "last_performance_eval": engine.model_performance_history[-1].evaluation_date if engine.model_performance_history else None
            },
            "configuration": {
                "learning_rate": engine.learning_rate,
                "performance_threshold": engine.performance_threshold,
                "insight_confidence_threshold": engine.insight_confidence_threshold
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"获取系统健康状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统健康状态失败: {str(e)}") 