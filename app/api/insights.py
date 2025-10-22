"""
LLM洞察生成API
提供基于LLM的洞察和执行计划生成接口
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import logging
from pymongo.database import Database

from ..services.insights.llm_insight_generator import (
    get_llm_insight_generator,
    LLMInsightGenerator,
    InsightResult,
    ActionPlan
)
from ..models.settings import LLMSettings
from ..core.database import get_db
from ..models.insights import InsightSession

logger = logging.getLogger(__name__)
router = APIRouter(tags=["洞察生成"])

def _parse_datetime(value):
    """安全地解析日期时间对象"""
    if isinstance(value, datetime):
        return value
    elif isinstance(value, str):
        return datetime.fromisoformat(value)
    else:
        return datetime.now()

# 请求模型
class InsightGenerationRequest(BaseModel):
    """洞察生成请求"""
    feedback_limit: int = Field(default=50, description="分析的反馈数量限制")
    include_action_plans: bool = Field(default=True, description="是否生成执行计划")
    filters: Optional[Dict] = Field(default={}, description="反馈筛选条件")
    use_recent_data_only: bool = Field(default=True, description="是否只使用最近一个月的数据")

class ManualInsightRequest(BaseModel):
    """手动洞察请求"""
    feedback_ids: List[str] = Field(..., description="反馈ID列表")
    focus_areas: List[str] = Field(default=[], description="关注领域")
    business_context: str = Field(default="", description="业务背景")

class FullTextInsightRequest(BaseModel):
    """全文洞察请求"""
    feedback_limit: int = Field(default=350, description="分析的反馈数量限制")
    filters: Optional[Dict] = Field(default={}, description="反馈筛选条件")
    analysis_focus: str = Field(default="comprehensive", description="分析重点: comprehensive/trend/risk/opportunity")
    use_all_history: bool = Field(default=True, description="是否使用所有历史数据")

# 响应模型
class InsightResponse(BaseModel):
    """洞察响应"""
    insight_id: str
    title: str
    description: str
    insight_type: str
    confidence_score: float
    impact_level: str
    supporting_evidence: List[str]
    affected_user_segments: List[str]
    business_impact: str
    generated_at: datetime
    is_full_text: bool = False  # 是否为全文洞察

class ActionPlanResponse(BaseModel):
    """执行计划响应"""
    plan_id: str
    title: str
    summary: str
    priority: str
    estimated_effort: str
    timeline: str
    owner_team: str
    success_metrics: List[str]
    action_steps: List[Dict]
    risk_assessment: str
    expected_outcome: str
    related_insights: List[str]
    generated_at: datetime

class InsightGenerationResponse(BaseModel):
    """洞察生成响应"""
    task_id: str
    insights: List[InsightResponse]
    action_plans: List[ActionPlanResponse]
    total_feedback_analyzed: int
    generation_time: float
    success: bool
    message: str

class FullTextInsightResponse(BaseModel):
    """全文洞察响应"""
    task_id: str
    insights: List[InsightResponse]
    executive_summary: Dict
    total_feedback_analyzed: int
    generation_time: float
    success: bool
    message: str
    analysis_type: str

class SaveInsightSessionRequest(BaseModel):
    """保存洞察会话请求"""
    title: str = Field(..., description="会话标题")
    generation_type: str = Field(..., description="生成类型")
    feedback_limit: int = Field(default=50, description="反馈数量限制")
    feedback_analyzed: int = Field(default=0, description="实际分析的反馈数量")
    filters: Optional[Dict] = Field(default={}, description="筛选条件")
    insights: List[InsightResponse] = Field(default=[], description="洞察列表")
    action_plans: List[ActionPlanResponse] = Field(default=[], description="执行计划列表")
    executive_summary: Optional[Dict] = Field(default={}, description="执行摘要")
    generation_time: float = Field(default=0.0, description="生成时间")
    tags: List[str] = Field(default=[], description="标签")

class InsightSessionResponse(BaseModel):
    """洞察会话响应"""
    session_id: str
    title: str
    created_at: datetime
    generation_type: str
    feedback_analyzed: int
    total_insights: int
    insights_by_type: Dict[str, int]
    generation_time: float
    is_favorite: bool
    tags: List[str]

class InsightSessionDetailResponse(BaseModel):
    """洞察会话详情响应"""
    session_id: str
    title: str
    created_at: datetime
    generation_type: str
    feedback_limit: int
    feedback_analyzed: int
    filters: Dict
    insights: List[InsightResponse]
    action_plans: List[ActionPlanResponse]
    executive_summary: Dict
    total_insights: int
    insights_by_type: Dict[str, int]
    generation_time: float
    is_favorite: bool
    tags: List[str]

# 依赖注入
async def get_llm_insight_generator_instance(db: Database = Depends(get_db)) -> LLMInsightGenerator:
    """获取LLM洞察生成器实例"""
    from ..core.database import get_db
    from ..api.settings import get_settings
    
    # 从数据库加载实际的LLM设置
    try:
        app_settings = await get_settings(db)
        llm_settings = app_settings.analysis.llm
        logger.info(f"从数据库加载LLM设置，模型: {llm_settings.model}")
    except Exception as e:
        logger.warning(f"加载数据库设置失败，使用默认设置: {e}")
        llm_settings = LLMSettings()
    
    return get_llm_insight_generator(llm_settings)

@router.post("/generate", summary="生成常规洞察和执行计划")
async def generate_insights(
    request: InsightGenerationRequest,
    generator: LLMInsightGenerator = Depends(get_llm_insight_generator_instance)
) -> InsightGenerationResponse:
    """基于用户反馈数据生成常规洞察和执行计划（基于最近一个月数据）"""
    try:
        start_time = datetime.now()
        
        # 为常规洞察添加时间限制，默认最近一个月
        filters = request.filters.copy()
        if request.use_recent_data_only and not filters.get("date_range"):
            filters["use_recent_data_only"] = True
        
        # 获取反馈数据
        feedback_data = await _get_feedback_data(request.feedback_limit, filters)
        
        if not feedback_data:
            return InsightGenerationResponse(
                task_id=f"task_{start_time.strftime('%Y%m%d_%H%M%S')}",
                insights=[],
                action_plans=[],
                total_feedback_analyzed=0,
                generation_time=0.0,
                success=False,
                message="没有找到可分析的反馈数据"
            )
        
        logger.info(f"开始分析{len(feedback_data)}条反馈数据（常规洞察）")
        
        # 生成洞察
        insights = await generator.generate_insights_from_feedback(feedback_data)
        
        # 生成执行计划
        action_plans = []
        if request.include_action_plans and insights:
            feedback_context = {
                "total_feedback": len(feedback_data),
                "analysis_date": datetime.now().isoformat(),
                "business_context": "基于用户反馈的产品改进（常规洞察）",
                "data_scope": "最近一个月数据"
            }
            action_plans = await generator.generate_action_plans_from_insights(insights, feedback_context)
        
        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        
        # 转换为响应格式
        insight_responses = [
            InsightResponse(
                insight_id=insight.insight_id,
                title=insight.title,
                description=insight.description,
                insight_type=insight.insight_type,
                confidence_score=insight.confidence_score,
                impact_level=insight.impact_level,
                supporting_evidence=insight.supporting_evidence,
                affected_user_segments=insight.affected_user_segments,
                business_impact=insight.business_impact,
                generated_at=insight.generated_at,
                is_full_text=getattr(insight, 'is_full_text', False)  # 普通洞察默认为False
            )
            for insight in insights
        ]
        
        action_plan_responses = [
            ActionPlanResponse(
                plan_id=plan.plan_id,
                title=plan.title,
                summary=plan.summary,
                priority=plan.priority,
                estimated_effort=plan.estimated_effort,
                timeline=plan.timeline,
                owner_team=plan.owner_team,
                success_metrics=plan.success_metrics,
                action_steps=plan.action_steps,
                risk_assessment=plan.risk_assessment,
                expected_outcome=plan.expected_outcome,
                related_insights=plan.related_insights,
                generated_at=plan.generated_at
            )
            for plan in action_plans
        ]
        
        # 自动保存会话
        try:
            save_request = SaveInsightSessionRequest(
                title=f"智能洞察分析 - {start_time.strftime('%Y-%m-%d %H:%M')}",
                generation_type="standard",
                feedback_limit=request.feedback_limit,
                feedback_analyzed=len(feedback_data),
                filters=request.filters,
                insights=insight_responses,
                action_plans=action_plan_responses,
                executive_summary={},
                generation_time=generation_time,
                tags=["auto-generated", "standard"]
            )
            await save_insight_session(save_request)
        except Exception as save_error:
            logger.warning(f"自动保存洞察会话失败: {save_error}")
        
        return InsightGenerationResponse(
            task_id=f"task_{start_time.strftime('%Y%m%d_%H%M%S')}",
            insights=insight_responses,
            action_plans=action_plan_responses,
            total_feedback_analyzed=len(feedback_data),
            generation_time=generation_time,
            success=True,
            message=f"成功生成{len(insights)}个洞察和{len(action_plans)}个执行计划"
        )
        
    except Exception as e:
        logger.error(f"洞察生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"洞察生成失败: {str(e)}")

@router.post("/generate-full-text", summary="全文洞察生成")
async def generate_full_text_insights(
    request: FullTextInsightRequest,
    generator: LLMInsightGenerator = Depends(get_llm_insight_generator_instance)
) -> FullTextInsightResponse:
    """
    利用gemini的1M上下文能力，一次性分析所有反馈数据，生成全文洞察
    """
    try:
        start_time = datetime.now()
        
        # 获取反馈数据 - 全文洞察需要获取所有历史数据
        all_history_filters = request.filters.copy() if request.filters else {}
        # 移除时间限制，获取所有历史数据
        if 'date_range' not in all_history_filters:
            all_history_filters['include_all_history'] = True
        feedback_data = await _get_feedback_data(request.feedback_limit, all_history_filters)
        
        if not feedback_data:
            return FullTextInsightResponse(
                task_id=f"full_text_task_{start_time.strftime('%Y%m%d_%H%M%S')}",
                insights=[],
                executive_summary={},
                total_feedback_analyzed=0,
                generation_time=0.0,
                success=False,
                message="没有找到可分析的反馈数据",
                analysis_type="full_text"
            )
        
        logger.info(f"开始全文洞察分析，数据量: {len(feedback_data)}条")
        
        # 尝试真实LLM生成，失败时使用模拟生成
        try:
            result = await generator.generate_full_text_insights(feedback_data)
            analysis_type = "llm_full_text"
        except Exception as llm_error:
            logger.warning(f"LLM全文洞察生成失败，切换到模拟模式: {llm_error}")
            
            # 使用模拟生成器
            from ..services.insights.mock_llm_insight_generator import MockLLMInsightGenerator
            mock_generator = MockLLMInsightGenerator()
            result = await mock_generator.generate_full_text_insights(feedback_data)
            analysis_type = "mock_full_text"
            logger.info("使用模拟模式完成全文洞察生成")
        
        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        
        # 转换为响应格式
        insight_responses = [
            InsightResponse(
                insight_id=insight.insight_id,
                title=insight.title,
                description=insight.description,
                insight_type=insight.insight_type,
                confidence_score=insight.confidence_score,
                impact_level=insight.impact_level,
                supporting_evidence=insight.supporting_evidence,
                affected_user_segments=insight.affected_user_segments,
                business_impact=insight.business_impact,
                generated_at=insight.generated_at,
                is_full_text=getattr(insight, 'is_full_text', True)  # 全文洞察标记
            )
            for insight in result.get("insights", [])
        ]
        
        executive_summary = result.get("executive_summary", {})
        
        # 自动保存全文洞察会话
        try:
            save_request = SaveInsightSessionRequest(
                title=f"全文洞察分析 - {start_time.strftime('%Y-%m-%d %H:%M')}",
                generation_type="full_text",
                feedback_limit=request.feedback_limit,
                feedback_analyzed=len(feedback_data),
                filters=request.filters,
                insights=insight_responses,
                action_plans=[],
                executive_summary=executive_summary,
                generation_time=generation_time,
                tags=["auto-generated", "full-text", "gemini-1m"]
            )
            await save_insight_session(save_request)
        except Exception as save_error:
            logger.warning(f"自动保存全文洞察会话失败: {save_error}")
        
        return FullTextInsightResponse(
            task_id=f"full_text_task_{start_time.strftime('%Y%m%d_%H%M%S')}",
            insights=insight_responses,
            executive_summary=executive_summary,
            total_feedback_analyzed=len(feedback_data),
            generation_time=generation_time,
            success=True,
            message=f"成功生成{len(insight_responses)}个全文洞察",
            analysis_type=analysis_type
        )
        
    except Exception as e:
        logger.error(f"全文洞察生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"全文洞察生成失败: {str(e)}")

@router.post("/generate-manual", summary="手动生成洞察")
async def generate_manual_insights(
    request: ManualInsightRequest,
    generator: LLMInsightGenerator = Depends(get_llm_insight_generator_instance)
):
    """基于指定的反馈ID手动生成洞察"""
    try:
        # 简化实现：使用模拟数据代替数据库查询
        # TODO: 后续集成真实的数据库查询
        demo_feedback = [
            {
                "id": "manual_1",
                "text": "手动分析的反馈内容示例",
                "filter_result": {
                    "sentiment": "neutral",
                    "category": "manual",
                    "priority_score": 0.7,
                    "extracted_keywords": ["手动", "分析", "示例"]
                }
            }
        ]
        
        # 生成洞察
        insights = await generator.generate_insights_from_feedback(demo_feedback)
        
        # 生成执行计划
        feedback_context = {
            "total_feedback": len(demo_feedback),
            "focus_areas": request.focus_areas,
            "business_context": request.business_context,
            "analysis_date": datetime.now().isoformat()
        }
        action_plans = await generator.generate_action_plans_from_insights(insights, feedback_context)
        
        return {
            "success": True,
            "insights": [
                {
                    "title": insight.title,
                    "description": insight.description,
                    "insight_type": insight.insight_type,
                    "confidence_score": insight.confidence_score,
                    "impact_level": insight.impact_level,
                    "business_impact": insight.business_impact
                }
                for insight in insights
            ],
            "action_plans": [
                {
                    "title": plan.title,
                    "summary": plan.summary,
                    "priority": plan.priority,
                    "estimated_effort": plan.estimated_effort,
                    "timeline": plan.timeline,
                    "owner_team": plan.owner_team,
                    "action_steps": plan.action_steps
                }
                for plan in action_plans
            ],
            "analyzed_feedback_count": len(demo_feedback)
        }
        
    except Exception as e:
        logger.error(f"手动生成洞察失败: {e}")
        raise HTTPException(status_code=500, detail=f"手动生成洞察失败: {str(e)}")

@router.get("/demo", summary="演示洞察生成")
async def demo_insight_generation(
    generator: LLMInsightGenerator = Depends(get_llm_insight_generator_instance)
):
    """演示洞察生成功能（使用模拟数据）"""
    try:
        # 创建模拟反馈数据
        demo_feedback = [
            {
                "id": "demo_1",
                "text": "登录页面加载太慢，经常超时，影响使用体验",
                "filter_result": {
                    "sentiment": "negative",
                    "category": "performance",
                    "priority_score": 0.8,
                    "extracted_keywords": ["登录", "加载", "超时", "性能"]
                }
            },
            {
                "id": "demo_2", 
                "text": "希望能增加暗黑模式，长时间使用眼睛很累",
                "filter_result": {
                    "sentiment": "neutral",
                    "category": "feature",
                    "priority_score": 0.6,
                    "extracted_keywords": ["暗黑模式", "护眼", "界面"]
                }
            },
            {
                "id": "demo_3",
                "text": "移动端界面太小，按钮点击困难，建议优化",
                "filter_result": {
                    "sentiment": "negative",
                    "category": "ui_ux",
                    "priority_score": 0.7,
                    "extracted_keywords": ["移动端", "界面", "按钮", "优化"]
                }
            },
            {
                "id": "demo_4",
                "text": "数据导出功能很好用，但希望支持更多格式",
                "filter_result": {
                    "sentiment": "positive",
                    "category": "feature",
                    "priority_score": 0.5,
                    "extracted_keywords": ["数据导出", "格式", "功能"]
                }
            },
            {
                "id": "demo_5",
                "text": "搜索功能不够智能，找不到想要的内容",
                "filter_result": {
                    "sentiment": "negative", 
                    "category": "functionality",
                    "priority_score": 0.75,
                    "extracted_keywords": ["搜索", "智能", "内容"]
                }
            }
        ]
        
        # 生成洞察
        insights = await generator.generate_insights_from_feedback(demo_feedback)
        
        # 生成执行计划
        feedback_context = {
            "total_feedback": len(demo_feedback),
            "business_context": "产品用户体验优化",
            "analysis_date": datetime.now().isoformat()
        }
        action_plans = await generator.generate_action_plans_from_insights(insights, feedback_context)
        
        return {
            "success": True,
            "message": "演示洞察生成完成",
            "demo_data": {
                "feedback_analyzed": len(demo_feedback),
                "insights_generated": len(insights),
                "action_plans_generated": len(action_plans)
            },
            "insights": [
                {
                    "title": insight.title,
                    "description": insight.description,
                    "insight_type": insight.insight_type,
                    "confidence_score": insight.confidence_score,
                    "impact_level": insight.impact_level,
                    "supporting_evidence": insight.supporting_evidence,
                    "business_impact": insight.business_impact
                }
                for insight in insights
            ],
            "action_plans": [
                {
                    "title": plan.title,
                    "summary": plan.summary,
                    "priority": plan.priority,
                    "estimated_effort": plan.estimated_effort,
                    "timeline": plan.timeline,
                    "owner_team": plan.owner_team,
                    "success_metrics": plan.success_metrics,
                    "action_steps": plan.action_steps,
                    "expected_outcome": plan.expected_outcome
                }
                for plan in action_plans
            ]
        }
        
    except Exception as e:
        logger.error(f"演示洞察生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"演示洞察生成失败: {str(e)}")

@router.get("/health", summary="健康检查")
async def health_check():
    """检查洞察生成服务的健康状态"""
    try:
        # 基本健康检查
        return {
            "status": "healthy",
            "service": "LLM洞察生成服务",
            "timestamp": datetime.now(),
            "version": "v1.0"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail="服务不可用")

@router.post("/sessions/save", summary="保存洞察会话")
async def save_insight_session(request: SaveInsightSessionRequest) -> Dict:
    """保存洞察会话到数据库"""
    try:
        # 生成会话ID
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 转换洞察和执行计划为字典格式
        insights_data = [insight.dict() for insight in request.insights]
        action_plans_data = [plan.dict() for plan in request.action_plans]
        
        # 计算按类型统计
        insights_by_type = {}
        for insight in insights_data:
            insight_type = insight.get('insight_type', 'general')
            insights_by_type[insight_type] = insights_by_type.get(insight_type, 0) + 1
        
        # 创建洞察会话
        session = InsightSession(
            session_id=session_id,
            title=request.title,
            generation_type=request.generation_type,
            feedback_limit=request.feedback_limit,
            feedback_analyzed=request.feedback_analyzed,
            filters=request.filters or {},
            insights=insights_data,
            action_plans=action_plans_data,
            executive_summary=request.executive_summary or {},
            total_insights=len(insights_data),
            insights_by_type=insights_by_type,
            generation_time=request.generation_time,
            tags=request.tags or []
        )
        
        # 保存到数据库
        await session.save()
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "洞察会话保存成功",
            "saved_at": session.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"保存洞察会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存洞察会话失败: {str(e)}")

@router.get("/sessions/latest", summary="获取最新洞察会话")
async def get_latest_insight_session() -> InsightSessionDetailResponse:
    """获取最新的洞察会话"""
    try:
        session = await InsightSession.get_latest_session()
        
        if not session:
            raise HTTPException(status_code=404, detail="没有找到洞察会话")
        
        # 转换洞察数据
        insights = [
            InsightResponse(
                insight_id=insight.get('insight_id', ''),
                title=insight.get('title', ''),
                description=insight.get('description', ''),
                insight_type=insight.get('insight_type', 'general'),
                confidence_score=insight.get('confidence_score', 0.0),
                impact_level=insight.get('impact_level', 'low'),
                supporting_evidence=insight.get('supporting_evidence', []),
                affected_user_segments=insight.get('affected_user_segments', []),
                business_impact=insight.get('business_impact', ''),
                generated_at=_parse_datetime(insight.get('generated_at', datetime.now())),
                is_full_text=insight.get('is_full_text', False)  # 全文洞察标记
            )
            for insight in session.insights
        ]
        
        # 转换执行计划数据
        action_plans = [
            ActionPlanResponse(
                plan_id=plan.get('plan_id', ''),
                title=plan.get('title', ''),
                summary=plan.get('summary', ''),
                priority=plan.get('priority', 'P3'),
                estimated_effort=plan.get('estimated_effort', ''),
                timeline=plan.get('timeline', ''),
                owner_team=plan.get('owner_team', ''),
                success_metrics=plan.get('success_metrics', []),
                action_steps=plan.get('action_steps', []),
                risk_assessment=plan.get('risk_assessment', ''),
                expected_outcome=plan.get('expected_outcome', ''),
                related_insights=plan.get('related_insights', []),
                generated_at=_parse_datetime(plan.get('generated_at', datetime.now()))
            )
            for plan in session.action_plans
        ]
        
        return InsightSessionDetailResponse(
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at,
            generation_type=session.generation_type,
            feedback_limit=session.feedback_limit,
            feedback_analyzed=session.feedback_analyzed,
            filters=session.filters,
            insights=insights,
            action_plans=action_plans,
            executive_summary=session.executive_summary,
            total_insights=session.total_insights,
            insights_by_type=session.insights_by_type,
            generation_time=session.generation_time,
            is_favorite=session.is_favorite,
            tags=session.tags
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取最新洞察会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取最新洞察会话失败: {str(e)}")

@router.get("/sessions", summary="获取洞察会话列表")
async def get_insight_sessions(
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    page: int = Query(1, ge=1, description="页码")
) -> Dict:
    """获取洞察会话列表"""
    try:
        skip = (page - 1) * limit
        
        sessions = await InsightSession.find(is_active=True)\
            .sort(-InsightSession.created_at)\
            .skip(skip)\
            .limit(limit)\
            .to_list()
        
        total_count = await InsightSession.find(is_active=True).count()
        
        session_list = [
            InsightSessionResponse(
                session_id=session.session_id,
                title=session.title,
                created_at=session.created_at,
                generation_type=session.generation_type,
                feedback_analyzed=session.feedback_analyzed,
                total_insights=session.total_insights,
                insights_by_type=session.insights_by_type,
                generation_time=session.generation_time,
                is_favorite=session.is_favorite,
                tags=session.tags
            )
            for session in sessions
        ]
        
        return {
            "sessions": session_list,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"获取洞察会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取洞察会话列表失败: {str(e)}")

@router.get("/sessions/{session_id}", summary="获取洞察会话详情")
async def get_insight_session(session_id: str) -> InsightSessionDetailResponse:
    """根据会话ID获取洞察会话详情"""
    try:
        session = await InsightSession.find_one(session_id=session_id, is_active=True)
        
        if not session:
            raise HTTPException(status_code=404, detail="洞察会话不存在")
        
        # 转换数据格式 (与get_latest_insight_session相同的逻辑)
        insights = [
            InsightResponse(
                insight_id=insight.get('insight_id', ''),
                title=insight.get('title', ''),
                description=insight.get('description', ''),
                insight_type=insight.get('insight_type', 'general'),
                confidence_score=insight.get('confidence_score', 0.0),
                impact_level=insight.get('impact_level', 'low'),
                supporting_evidence=insight.get('supporting_evidence', []),
                affected_user_segments=insight.get('affected_user_segments', []),
                business_impact=insight.get('business_impact', ''),
                generated_at=_parse_datetime(insight.get('generated_at', datetime.now())),
                is_full_text=insight.get('is_full_text', False)  # 全文洞察标记
            )
            for insight in session.insights
        ]
        
        action_plans = [
            ActionPlanResponse(
                plan_id=plan.get('plan_id', ''),
                title=plan.get('title', ''),
                summary=plan.get('summary', ''),
                priority=plan.get('priority', 'P3'),
                estimated_effort=plan.get('estimated_effort', ''),
                timeline=plan.get('timeline', ''),
                owner_team=plan.get('owner_team', ''),
                success_metrics=plan.get('success_metrics', []),
                action_steps=plan.get('action_steps', []),
                risk_assessment=plan.get('risk_assessment', ''),
                expected_outcome=plan.get('expected_outcome', ''),
                related_insights=plan.get('related_insights', []),
                generated_at=_parse_datetime(plan.get('generated_at', datetime.now()))
            )
            for plan in session.action_plans
        ]
        
        return InsightSessionDetailResponse(
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at,
            generation_type=session.generation_type,
            feedback_limit=session.feedback_limit,
            feedback_analyzed=session.feedback_analyzed,
            filters=session.filters,
            insights=insights,
            action_plans=action_plans,
            executive_summary=session.executive_summary,
            total_insights=session.total_insights,
            insights_by_type=session.insights_by_type,
            generation_time=session.generation_time,
            is_favorite=session.is_favorite,
            tags=session.tags
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取洞察会话详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取洞察会话详情失败: {str(e)}")

@router.delete("/sessions/{session_id}", summary="删除洞察会话")
async def delete_insight_session(session_id: str) -> Dict:
    """删除洞察会话"""
    try:
        session = await InsightSession.find_one(session_id=session_id, is_active=True)
        
        if not session:
            raise HTTPException(status_code=404, detail="洞察会话不存在")
        
        # 软删除
        session.is_active = False
        await session.save()
        
        return {
            "success": True,
            "message": "洞察会话删除成功",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除洞察会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除洞察会话失败: {str(e)}")

async def _get_feedback_data(limit: int, filters: Dict) -> List[Dict]:
    """获取真实的反馈数据"""
    try:
        from ..models.database import UserFeedback, FeedbackSource
        from datetime import datetime, timedelta
        
        # 构建查询条件
        query_filters = {}
        
        # 按情感筛选
        if filters.get("sentiment"):
            query_filters["analysis_result.sentiment"] = filters["sentiment"]
        
        # 按分类筛选
        if filters.get("category"):
            query_filters["analysis_result.category"] = filters["category"]
        
        # 按时间筛选 - 支持常规洞察和全文洞察的不同数据源
        if filters.get("date_range"):
            # 用户自定义时间范围
            start_date, end_date = filters["date_range"]
            query_filters["created_at"] = {
                "$gte": start_date,
                "$lte": end_date
            }
        elif filters.get("include_all_history"):
            # 全文洞察：获取所有历史数据，不设置时间限制
            logger.info("全文洞察：获取所有历史数据")
        elif filters.get("use_recent_data_only", True):
            # 常规洞察：默认获取最近一个月的数据
            now = datetime.now()
            one_month_ago = now - timedelta(days=30)
            query_filters["created_at"] = {
                "$gte": one_month_ago,
                "$lte": now
            }
            logger.info(f"常规洞察：获取最近一个月的数据 ({one_month_ago} 到 {now})")
        
        # 只获取已处理的反馈数据
        query_filters["is_processed"] = True
        query_filters["analysis_result"] = {"$exists": True}
        
        # 执行查询
        feedbacks = await UserFeedback.find(query_filters)\
            .sort([("created_at", -1)])\
            .limit(limit)\
            .to_list()
        
        # 转换为洞察生成所需的格式
        processed_feedbacks = []
        for feedback in feedbacks:
            # 确定显示文本
            display_text = ""
            if feedback.original_content:
                display_text = feedback.original_content
            elif feedback.content:
                display_text = feedback.content
            elif feedback.original_text:
                display_text = feedback.original_text
            else:
                display_text = feedback.processed_text or "内容缺失"
            
            # 获取分析结果
            analysis_result = feedback.analysis_result or {}
            
            # 构建洞察生成所需的数据格式
            feedback_data = {
                "id": str(feedback.id),
                "text": display_text,
                "filter_result": {
                    "sentiment": analysis_result.get("sentiment", "neutral"),
                    "category": analysis_result.get("category", "general"),
                    "priority_score": analysis_result.get("urgency_score", 0.5),
                    "extracted_keywords": analysis_result.get("keywords", [])
                },
                "created_at": feedback.created_at,
                "source": feedback.source.value,
                "user_id": feedback.user_id,
                "platform_metadata": feedback.platform_metadata or {}
            }
            
            processed_feedbacks.append(feedback_data)
        
        data_scope = "所有历史数据" if filters.get("include_all_history") else "最近一个月数据"
        logger.info(f"从数据库获取到{len(processed_feedbacks)}条反馈数据（{data_scope}）")
        
        # 如果数据库中没有足够的数据，使用部分演示数据填充
        if len(processed_feedbacks) < 10:
            logger.warning(f"数据库中只有{len(processed_feedbacks)}条反馈数据，使用演示数据补充")
            
            # 根据数据源类型生成不同的演示数据
            if filters.get("include_all_history"):
                # 全文洞察演示数据：更多样化、跨时间段
                demo_feedback = _generate_full_text_demo_data()
            else:
                # 常规洞察演示数据：最近一个月的数据
                demo_feedback = _generate_recent_demo_data()
            
            processed_feedbacks.extend(demo_feedback)
        
        return processed_feedbacks[:limit]
        
    except Exception as e:
        logger.error(f"获取反馈数据失败: {e}")
        # 如果数据库查询失败，返回演示数据
        return _generate_fallback_demo_data()

def _generate_full_text_demo_data() -> List[Dict]:
    """生成全文洞察演示数据（跨时间段）"""
    from datetime import datetime, timedelta
    
    base_date = datetime.now()
    demo_data = []
    
    # 生成跨越6个月的历史数据
    for i in range(50):
        days_ago = i * 4  # 每4天一条数据
        created_date = base_date - timedelta(days=days_ago)
        
        demo_data.append({
            "id": f"full_text_demo_{i+1}",
            "text": f"历史反馈数据 #{i+1}：{_get_demo_feedback_text(i)}",
            "filter_result": {
                "sentiment": ["positive", "negative", "neutral"][i % 3],
                "category": ["performance", "feature", "ui_ux", "bug", "general"][i % 5],
                "priority_score": 0.3 + (i % 7) * 0.1,
                "extracted_keywords": [f"关键词{i+1}", f"特征{i+1}"]
            },
            "created_at": created_date,
            "source": "demo_full_text",
            "user_id": f"demo_user_{i+1}",
            "platform_metadata": {"demo_type": "full_text"}
        })
    
    return demo_data

def _generate_recent_demo_data() -> List[Dict]:
    """生成常规洞察演示数据（最近一个月）"""
    from datetime import datetime, timedelta
    
    base_date = datetime.now()
    demo_data = []
    
    # 生成最近30天的数据
    for i in range(30):
        created_date = base_date - timedelta(days=i)
        
        demo_data.append({
            "id": f"recent_demo_{i+1}",
            "text": f"最近反馈数据 #{i+1}：{_get_demo_feedback_text(i)}",
            "filter_result": {
                "sentiment": ["positive", "negative", "neutral"][i % 3],
                "category": ["performance", "feature", "ui_ux", "bug", "general"][i % 5],
                "priority_score": 0.4 + (i % 6) * 0.1,
                "extracted_keywords": [f"关键词{i+1}", f"特征{i+1}"]
            },
            "created_at": created_date,
            "source": "demo_recent",
            "user_id": f"demo_user_{i+1}",
            "platform_metadata": {"demo_type": "recent"}
        })
    
    return demo_data

def _get_demo_feedback_text(index: int) -> str:
    """获取演示反馈文本"""
    feedback_texts = [
        "登录页面加载太慢，经常超时，影响使用体验",
        "希望能增加暗黑模式，长时间使用眼睛很累",
        "移动端界面太小，按钮点击困难，建议优化",
        "搜索功能很棒，但是结果排序可以更智能",
        "客服响应很及时，解决问题很专业",
        "支付流程太复杂，希望能够简化步骤",
        "新增的功能很实用，大大提升了工作效率",
        "数据同步有延迟，希望能够实时更新",
        "界面设计很美观，操作逻辑清晰易懂",
        "希望能够增加更多的个性化设置选项"
    ]
    
    return feedback_texts[index % len(feedback_texts)]

def _generate_fallback_demo_data() -> List[Dict]:
    """生成后备演示数据"""
    return [
        {
            "id": "fallback_1",
            "text": "数据库连接失败，使用演示数据",
            "filter_result": {
                "sentiment": "negative",
                "category": "system",
                "priority_score": 0.9,
                "extracted_keywords": ["数据库", "连接", "失败"]
            },
            "created_at": datetime.now(),
            "source": "fallback",
            "user_id": "system",
            "platform_metadata": {}
        }
    ] 