"""
决策引擎API
暴露洞察量化、优先级排序、行动规划生成等决策支持功能
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from ..services.decision.advanced_priority_engine import AdvancedPriorityEngine, PriorityScoreResult
from ..services.decision.priority_engine import PriorityEngine
from ..services.visualization.action_generator import ActionGenerator, ActionPlan
from ..models.database import UserFeedback
from ..core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/decision-engine", tags=["决策引擎"])

# 请求模型
class PriorityCalculationRequest(BaseModel):
    """优先级计算请求"""
    feedback_ids: List[str] = Field(..., description="反馈ID列表")
    use_advanced_engine: bool = Field(True, description="是否使用高级优先级引擎")
    weights: Optional[Dict[str, float]] = Field(None, description="自定义权重配置")

class ActionPlanGenerationRequest(BaseModel):
    """行动计划生成请求"""
    feedback_ids: List[str] = Field(..., description="反馈ID列表")
    priority_threshold: float = Field(0.6, description="优先级阈值", ge=0, le=1)
    include_low_priority: bool = Field(False, description="是否包含低优先级项目")

# 响应模型
class PriorityAnalysisResponse(BaseModel):
    """优先级分析响应"""
    total_analyzed: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    avg_priority_score: float
    avg_roi: float
    priority_distribution: Dict[str, int]
    top_priority_items: List[Dict]
    analysis_timestamp: datetime

class ActionPlanResponse(BaseModel):
    """行动计划响应"""
    plan_id: str
    total_actions: int
    p0_actions: int
    p1_actions: int
    p2_actions: int
    p3_actions: int
    estimated_timeline: str
    total_effort_estimate: str
    key_insights: List[str]
    action_items: List[Dict]
    created_at: datetime

@router.get("/health", summary="决策引擎健康检查")
async def decision_engine_health():
    """决策引擎健康检查"""
    return {
        "status": "ok",
        "module": "decision_engine",
        "advanced_priority_engine": True,
        "priority_engine": True,
        "action_generator": True,
        "timestamp": datetime.now()
    }

@router.get("/weights/config", summary="获取权重配置")
async def get_weights_config():
    """获取当前的6维度权重配置"""
    try:
        settings = get_settings()
        advanced_engine = AdvancedPriorityEngine(settings.dict())
        
        return {
            "dimension_weights": advanced_engine.dimension_weights,
            "business_rules": advanced_engine.business_rules,
            "time_decay_params": advanced_engine.time_decay_params,
            "description": {
                "impact": "影响力权重 - 评估问题影响的用户范围和程度",
                "urgency": "紧急性权重 - 评估问题的时间敏感性",
                "effort": "实现成本权重 - 评估解决问题的技术复杂度和工作量",
                "business_value": "商业价值权重 - 评估解决问题的商业收益",
                "strategic": "战略匹配权重 - 评估与公司战略的匹配度",
                "user_voice": "用户声音权重 - 评估用户反馈的质量和代表性"
            }
        }
    except Exception as e:
        logger.error(f"获取权重配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取权重配置失败: {str(e)}")

@router.post("/priority/calculate", summary="计算优先级得分")
async def calculate_priority_scores(request: PriorityCalculationRequest):
    """计算反馈的6维度优先级得分"""
    try:
        # 获取反馈数据 - 支持多种ID格式
        from bson import ObjectId
        
        # 尝试将字符串ID转换为ObjectId，如果失败则保持字符串格式
        object_ids = []
        string_ids = []
        
        for feedback_id in request.feedback_ids:
            try:
                object_ids.append(ObjectId(feedback_id))
            except:
                string_ids.append(feedback_id)
        
        # 使用多种方式查找反馈数据
        query_conditions = []
        if object_ids:
            query_conditions.append({"_id": {"$in": object_ids}})
        if string_ids:
            query_conditions.append({"id": {"$in": string_ids}})
        
        if query_conditions:
            if len(query_conditions) == 1:
                query = query_conditions[0]
            else:
                query = {"$or": query_conditions}
        else:
            query = {"_id": {"$in": []}}  # 空查询
        
        feedbacks = await UserFeedback.find(query).to_list()
        
        if not feedbacks:
            raise HTTPException(status_code=404, detail=f"未找到指定的反馈数据，查询条件: {query}, 传入ID: {request.feedback_ids}")
        
        # 准备分析数据
        feedbacks_with_analysis = []
        for feedback in feedbacks:
            feedback_data = {
                'id': str(feedback.id),
                'text': feedback.original_content or feedback.content or "",
                'filter_result': {
                    'filter_score': getattr(feedback, 'filter_score', None),
                    'filter_reason': getattr(feedback, 'filter_reason', None)
                },
                'deep_analysis': feedback.analysis_result or {},
                'metadata': {
                    'created_at': feedback.created_at,
                    'source': feedback.source
                }
            }
            feedbacks_with_analysis.append(feedback_data)
        
        # 执行优先级计算
        settings = get_settings()
        if request.use_advanced_engine:
            priority_engine = AdvancedPriorityEngine(settings.dict())
            # 应用自定义权重
            if request.weights:
                priority_engine.dimension_weights.update(request.weights)
            
            priority_results = await priority_engine.calculate_priority_scores(feedbacks_with_analysis)
        else:
            priority_engine = PriorityEngine()
            priority_results = []
            for feedback_data in feedbacks_with_analysis:
                # 转换为传统引擎格式
                issue_data = {
                    "feedback_count": 1,
                    "avg_sentiment_score": feedback_data.get('deep_analysis', {}).get('sentiment_score', 0),
                    "avg_urgency_score": feedback_data.get('deep_analysis', {}).get('urgency_score', 0.5),
                    "issue_theme": feedback_data.get('text', '')[:50]
                }
                priority_score = priority_engine.calculate_comprehensive_priority(issue_data)
                priority_category = priority_engine.categorize_priority(priority_score)
                
                # 构造兼容的结果格式
                result = {
                    'feedback_id': feedback_data['id'],
                    'overall_priority_score': priority_score,
                    'priority_tier': 'P0' if priority_category == 'Critical' else 
                                   'P1' if priority_category == 'High' else
                                   'P2' if priority_category == 'Medium' else 'P3',
                    'recommendation': f"优先级: {priority_category}"
                }
                priority_results.append(result)
        
        # 统计分析
        total_analyzed = len(priority_results)
        if isinstance(priority_results[0], PriorityScoreResult):
            # 高级引擎结果
            high_priority_count = len([r for r in priority_results if r.priority_tier in ['P0', 'P1']])
            medium_priority_count = len([r for r in priority_results if r.priority_tier == 'P2'])
            low_priority_count = len([r for r in priority_results if r.priority_tier == 'P3'])
            avg_priority_score = sum(r.overall_priority_score for r in priority_results) / total_analyzed
            avg_roi = sum(r.expected_roi for r in priority_results) / total_analyzed
            
            # 优先级分布
            priority_distribution = {}
            for tier in ['P0', 'P1', 'P2', 'P3']:
                priority_distribution[tier] = len([r for r in priority_results if r.priority_tier == tier])
            
            # Top 优先级项目
            top_priority_items = [
                {
                    "feedback_id": r.feedback_id,
                    "priority_score": r.overall_priority_score,
                    "priority_tier": r.priority_tier,
                    "impact_score": r.impact_score,
                    "urgency_score": r.urgency_score,
                    "business_value_score": r.business_value_score,
                    "expected_roi": r.expected_roi,
                    "estimated_impact_users": r.estimated_impact_users,
                    "recommendation": r.recommendation
                }
                for r in sorted(priority_results, key=lambda x: x.overall_priority_score, reverse=True)[:10]
            ]
        else:
            # 传统引擎结果
            high_priority_count = len([r for r in priority_results if r['priority_tier'] in ['P0', 'P1']])
            medium_priority_count = len([r for r in priority_results if r['priority_tier'] == 'P2'])
            low_priority_count = len([r for r in priority_results if r['priority_tier'] == 'P3'])
            avg_priority_score = sum(r['overall_priority_score'] for r in priority_results) / total_analyzed
            avg_roi = 0.0  # 传统引擎不支持ROI计算
            
            priority_distribution = {}
            for tier in ['P0', 'P1', 'P2', 'P3']:
                priority_distribution[tier] = len([r for r in priority_results if r['priority_tier'] == tier])
            
            top_priority_items = sorted(priority_results, key=lambda x: x['overall_priority_score'], reverse=True)[:10]
        
        return PriorityAnalysisResponse(
            total_analyzed=total_analyzed,
            high_priority_count=high_priority_count,
            medium_priority_count=medium_priority_count,
            low_priority_count=low_priority_count,
            avg_priority_score=round(avg_priority_score, 2),
            avg_roi=round(avg_roi, 3),
            priority_distribution=priority_distribution,
            top_priority_items=top_priority_items,
            analysis_timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算优先级得分失败: {e}")
        raise HTTPException(status_code=500, detail=f"优先级计算失败: {str(e)}")

@router.post("/action-plan/generate", summary="生成行动计划")
async def generate_action_plan(request: ActionPlanGenerationRequest, background_tasks: BackgroundTasks):
    """基于优先级分析结果生成可执行的行动计划"""
    try:
        # 先计算优先级
        priority_request = PriorityCalculationRequest(
            feedback_ids=request.feedback_ids,
            use_advanced_engine=True
        )
        priority_response = await calculate_priority_scores(priority_request)
        
        # 筛选符合阈值的项目
        eligible_items = [
            item for item in priority_response.top_priority_items
            if item["priority_score"] >= request.priority_threshold * 100 or request.include_low_priority
        ]
        
        if not eligible_items:
            return ActionPlanResponse(
                plan_id=f"plan_empty_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                total_actions=0,
                p0_actions=0,
                p1_actions=0,
                p2_actions=0,
                p3_actions=0,
                estimated_timeline="无需行动",
                total_effort_estimate="0人周",
                key_insights=["暂无符合条件的高优先级项目"],
                action_items=[],
                created_at=datetime.now()
            )
        
        # 生成行动计划
        settings = get_settings()
        action_generator = ActionGenerator(settings.dict())
        
        # 准备数据格式
        priority_data = []
        for item in eligible_items:
            priority_data.append({
                'priority_score': item,
                'feedback_data': {
                    'id': item['feedback_id'],
                    'text': f"优先级得分: {item['priority_score']}"
                }
            })
        
        action_plan = await action_generator.generate_action_plan(priority_data)
        
        # 生成关键洞察
        key_insights = []
        if priority_response.high_priority_count > 0:
            key_insights.append(f"发现 {priority_response.high_priority_count} 个高优先级问题需要立即关注")
        
        if priority_response.avg_roi > 0.5:
            key_insights.append(f"平均ROI为 {priority_response.avg_roi:.1%}，整体投资价值较高")
        
        if len(eligible_items) > 5:
            key_insights.append(f"建议分批执行，优先处理前 5 个最高优先级项目")
        
        return ActionPlanResponse(
            plan_id=action_plan.plan_id,
            total_actions=action_plan.total_actions,
            p0_actions=action_plan.p0_actions,
            p1_actions=action_plan.p1_actions,
            p2_actions=action_plan.p2_actions,
            p3_actions=action_plan.p3_actions,
            estimated_timeline=action_plan.estimated_timeline,
            total_effort_estimate=action_plan.total_effort_estimate,
            key_insights=key_insights,
            action_items=[
                {
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "action_type": item.action_type.value,
                    "priority": item.priority.value,
                    "owner_team": item.owner_team,
                    "estimated_effort": item.estimated_effort,
                    "timeline": item.timeline,
                    "business_justification": item.business_justification,
                    "risk_assessment": item.risk_assessment
                }
                for item in action_plan.action_items
            ],
            created_at=action_plan.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成行动计划失败: {e}")
        raise HTTPException(status_code=500, detail=f"行动计划生成失败: {str(e)}")

@router.get("/analytics/overview", summary="决策引擎分析概览")
async def get_decision_analytics():
    """获取决策引擎的分析概览数据"""
    try:
        # 获取最近的反馈数据进行分析
        recent_feedbacks = await UserFeedback.find().sort([("created_at", -1)]).limit(100).to_list()
        
        if not recent_feedbacks:
            return {
                "total_feedbacks": 0,
                "analyzed_count": 0,
                "priority_distribution": {"P0": 0, "P1": 0, "P2": 0, "P3": 0},
                "avg_scores": {
                    "priority": 0,
                    "roi": 0,
                    "confidence": 0
                },
                "engine_usage": {
                    "advanced_priority": 0,
                    "basic_priority": 0,
                    "action_plans_generated": 0
                },
                "recommendations_summary": []
            }
        
        # Mock 分析结果
        return {
            "total_feedbacks": len(recent_feedbacks),
            "analyzed_count": len([f for f in recent_feedbacks if f.analysis_result]),
            "priority_distribution": {
                "P0": 5,
                "P1": 15,
                "P2": 35,
                "P3": 45
            },
            "avg_scores": {
                "priority": 65.2,
                "roi": 0.15,
                "confidence": 0.78
            },
            "six_dimensions_avg": {
                "impact": 72.3,
                "urgency": 58.7,
                "effort": 45.2,
                "business_value": 69.8,
                "strategic": 55.4,
                "user_voice": 61.9
            },
            "engine_usage": {
                "advanced_priority": 87,
                "basic_priority": 13,
                "action_plans_generated": 23
            },
            "recommendations_summary": [
                "优先处理登录相关的高优先级问题",
                "关注用户体验改进项目的ROI",
                "建议增加前端团队资源投入"
            ],
            "last_updated": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"获取决策分析概览失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分析概览失败: {str(e)}")

@router.get("/insights/top-priorities", summary="获取Top优先级洞察")
async def get_top_priority_insights(limit: int = Query(10, ge=1, le=50)):
    """获取最高优先级的洞察和建议"""
    try:
        # Mock 数据（实际应该从优先级计算结果获取）
        insights = [
            {
                "id": "insight_001",
                "type": "user_pain",
                "title": "登录功能严重影响用户体验",
                "description": "多个用户反馈登录过程复杂，导致转化率下降",
                "priority_score": 85.6,
                "impact_users": 5000,
                "expected_roi": 0.45,
                "confidence": 0.9,
                "supporting_evidence": [
                    "15条用户反馈提及登录问题",
                    "登录成功率仅为78%",
                    "客服工单中30%与登录相关"
                ],
                "action_recommendations": [
                    "简化登录流程",
                    "添加社交登录选项",
                    "优化错误提示信息"
                ],
                "timeline": "当前迭代",
                "owner_team": "产品团队"
            },
            {
                "id": "insight_002", 
                "type": "feature_gap",
                "title": "缺少深色模式功能",
                "description": "用户强烈要求添加深色模式，提升夜间使用体验",
                "priority_score": 72.3,
                "impact_users": 2500,
                "expected_roi": 0.28,
                "confidence": 0.85,
                "supporting_evidence": [
                    "8条用户反馈要求深色模式",
                    "竞品都已支持深色模式",
                    "GitHub issue获得120个赞"
                ],
                "action_recommendations": [
                    "设计深色主题方案",
                    "实现主题切换功能",
                    "适配所有界面组件"
                ],
                "timeline": "下个季度",
                "owner_team": "设计团队"
            }
        ]
        
        return {
            "total_insights": len(insights),
            "insights": insights[:limit],
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"获取Top优先级洞察失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取洞察失败: {str(e)}") 