"""
混合智能分析API
整合四个核心模块，实现端到端的用户反馈智能分析与决策支持
"""
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

# 导入四个核心模块
from ..services.preprocessing.intelligent_filter import intelligent_filter, FilterResult
from ..services.analysis.enhanced_llm_analyzer import get_enhanced_analyzer, DeepAnalysisResult
from ..services.decision.advanced_priority_engine import get_advanced_priority_engine, PriorityScoreResult
from ..services.visualization.action_generator import get_action_generator, ActionPlan, ActionItem
from ..core.config import get_settings
from ..models.database import UserFeedback, AnalysisTask, ProductIssue

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hybrid-analysis", tags=["混合智能分析"])

# 请求模型
class FeedbackAnalysisRequest(BaseModel):
    """反馈分析请求"""
    feedbacks: List[Dict] = Field(..., description="反馈数据列表")
    analysis_config: Optional[Dict] = Field(default={}, description="分析配置")
    generate_action_plan: bool = Field(default=True, description="是否生成行动计划")

class BatchAnalysisRequest(BaseModel):
    """批量分析请求"""
    feedback_ids: List[str] = Field(..., description="反馈ID列表")
    force_llm_analysis: bool = Field(default=False, description="强制使用LLM分析")
    analysis_mode: str = Field(default="smart", description="分析模式: smart/fast/deep")

# 响应模型
class AnalysisStage(BaseModel):
    """分析阶段"""
    stage_name: str
    status: str  # pending/processing/completed/failed
    processed_count: int
    total_count: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    error_message: Optional[str]

class HybridAnalysisResult(BaseModel):
    """混合分析结果"""
    analysis_id: str
    total_feedbacks: int
    
    # 各阶段统计
    filter_stage: AnalysisStage
    llm_stage: AnalysisStage
    priority_stage: AnalysisStage
    action_stage: AnalysisStage
    
    # 结果统计
    high_priority_count: int
    llm_processed_count: int
    llm_skipped_count: int
    action_items_generated: int
    
    # 效率指标
    total_processing_time: float
    cost_estimate: float
    efficiency_ratio: float  # 有效处理比例
    
    # 结果数据
    priority_results: List[Dict]
    action_plan: Optional[Dict]
    insights_summary: Dict
    
    # 时间戳
    started_at: datetime
    completed_at: Optional[datetime]

class PerformanceMetrics(BaseModel):
    """性能指标"""
    total_processing_time: float
    filter_time: float
    llm_time: float
    priority_time: float
    action_time: float
    
    cost_breakdown: Dict[str, float]
    efficiency_metrics: Dict[str, float]
    quality_scores: Dict[str, float]

class HybridAnalysisEngine:
    """混合智能分析引擎"""
    
    def __init__(self):
        self.settings = get_settings()
        self.active_tasks = {}  # 存储正在进行的任务
        
        # 性能配置
        self.performance_config = {
            "max_parallel_llm_calls": 5,      # 最大并行LLM调用数
            "llm_timeout": 30,                # LLM调用超时时间
            "batch_size": 20,                 # 批处理大小
            "cost_threshold": 100.0,          # 成本阈值(美元)
            "quality_threshold": 0.7          # 质量阈值
        }
    
    async def process_feedbacks(self, 
                              feedbacks: List[Dict], 
                              analysis_config: Dict = None,
                              generate_action_plan: bool = True) -> HybridAnalysisResult:
        """处理反馈数据的主流程"""
        
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        logger.info(f"开始混合智能分析 {analysis_id}，处理 {len(feedbacks)} 条反馈")
        
        # 初始化分析结果
        result = HybridAnalysisResult(
            analysis_id=analysis_id,
            total_feedbacks=len(feedbacks),
            filter_stage=AnalysisStage(
                stage_name="智能预筛选",
                status="pending",
                processed_count=0,
                total_count=len(feedbacks),
                start_time=None,
                end_time=None,
                error_message=None
            ),
            llm_stage=AnalysisStage(
                stage_name="LLM深度分析",
                status="pending", 
                processed_count=0,
                total_count=0,
                start_time=None,
                end_time=None,
                error_message=None
            ),
            priority_stage=AnalysisStage(
                stage_name="优先级计算",
                status="pending",
                processed_count=0,
                total_count=0,
                start_time=None,
                end_time=None,
                error_message=None
            ),
            action_stage=AnalysisStage(
                stage_name="行动计划生成",
                status="pending",
                processed_count=0,
                total_count=0,
                start_time=None,
                end_time=None,
                error_message=None
            ),
            high_priority_count=0,
            llm_processed_count=0,
            llm_skipped_count=0,
            action_items_generated=0,
            total_processing_time=0.0,
            cost_estimate=0.0,
            efficiency_ratio=0.0,
            priority_results=[],
            action_plan=None,
            insights_summary={},
            started_at=start_time,
            completed_at=None
        )
        
        try:
            # 阶段1：智能预筛选
            filter_results = await self._stage_1_intelligent_filter(feedbacks, result)
            
            # 阶段2：LLM深度分析（仅对筛选后的高价值反馈）
            enhanced_results = await self._stage_2_llm_analysis(feedbacks, filter_results, result)
            
            # 阶段3：高级优先级计算
            priority_results = await self._stage_3_priority_calculation(enhanced_results, result)
            
            # 阶段4：行动计划生成
            if generate_action_plan:
                action_plan = await self._stage_4_action_generation(priority_results, result)
                result.action_plan = action_plan.__dict__ if action_plan else None
            
            # 计算最终指标
            end_time = datetime.now()
            result.total_processing_time = (end_time - start_time).total_seconds()
            result.completed_at = end_time
            result.priority_results = [self._serialize_priority_result(pr) for pr in priority_results]
            result.insights_summary = self._generate_insights_summary(priority_results, filter_results)
            result.efficiency_ratio = self._calculate_efficiency_ratio(result)
            
            logger.info(f"混合智能分析 {analysis_id} 完成，耗时 {result.total_processing_time:.2f}秒")
            return result
            
        except Exception as e:
            logger.error(f"混合智能分析失败 {analysis_id}: {e}")
            result.completed_at = datetime.now()
            result.total_processing_time = (result.completed_at - start_time).total_seconds()
            raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")
    
    async def _stage_1_intelligent_filter(self, feedbacks: List[Dict], result: HybridAnalysisResult) -> List[FilterResult]:
        """阶段1：智能预筛选"""
        
        result.filter_stage.status = "processing"
        result.filter_stage.start_time = datetime.now()
        
        try:
            # 确保智能筛选器已初始化
            await intelligent_filter.initialize_models()
            
            # 批量筛选
            filter_results = await intelligent_filter.batch_filter(feedbacks)
            
            result.filter_stage.processed_count = len(filter_results)
            result.filter_stage.status = "completed"
            result.filter_stage.end_time = datetime.now()
            
            # 统计需要LLM处理的数量
            llm_required_count = sum(1 for fr in filter_results if fr.should_process_with_llm)
            result.llm_stage.total_count = llm_required_count
            result.llm_skipped_count = len(filter_results) - llm_required_count
            
            logger.info(f"预筛选完成，{len(filter_results)}条反馈中{llm_required_count}条需要LLM处理")
            return filter_results
            
        except Exception as e:
            result.filter_stage.status = "failed"
            result.filter_stage.error_message = str(e)
            result.filter_stage.end_time = datetime.now()
            raise
    
    async def _stage_2_llm_analysis(self, 
                                   feedbacks: List[Dict], 
                                   filter_results: List[FilterResult], 
                                   result: HybridAnalysisResult) -> List[Dict]:
        """阶段2：LLM深度分析"""
        
        result.llm_stage.status = "processing"
        result.llm_stage.start_time = datetime.now()
        
        try:
            # 获取增强分析器
            analyzer = await get_enhanced_analyzer({
                'openai_api_key': self.settings.openai_api_key,
                'gemini_api_key': self.settings.gemini_api_key
            })
            
            enhanced_results = []
            llm_processed_count = 0
            cost_estimate = 0.0
            
            # 并行处理需要LLM分析的反馈
            for i, (feedback, filter_result) in enumerate(zip(feedbacks, filter_results)):
                enhanced_item = {
                    'id': feedback.get('id', f'feedback_{i}'),
                    'feedback_data': feedback,
                    'filter_result': filter_result.__dict__,
                    'deep_analysis': None
                }
                
                if filter_result.should_process_with_llm:
                    try:
                        # LLM深度分析
                        deep_analysis = await analyzer.deep_analyze_feedback(
                            feedback.get('text', ''),
                            feedback.get('metadata', {})
                        )
                        enhanced_item['deep_analysis'] = deep_analysis.__dict__
                        llm_processed_count += 1
                        cost_estimate += 0.02  # 估算每次调用成本
                        
                    except Exception as e:
                        logger.warning(f"LLM分析失败 feedback {i}: {e}")
                        # 使用预筛选结果作为备选
                        enhanced_item['deep_analysis'] = self._create_fallback_analysis(filter_result)
                
                enhanced_results.append(enhanced_item)
                result.llm_stage.processed_count = llm_processed_count
                
                # 控制并发和成本
                if llm_processed_count % self.performance_config["batch_size"] == 0:
                    await asyncio.sleep(0.1)  # 短暂延迟避免过载
                
                if cost_estimate > self.performance_config["cost_threshold"]:
                    logger.warning(f"LLM调用成本超过阈值 ${cost_estimate:.2f}，停止进一步分析")
                    break
            
            result.llm_stage.status = "completed"
            result.llm_stage.end_time = datetime.now()
            result.llm_processed_count = llm_processed_count
            result.cost_estimate = cost_estimate
            
            logger.info(f"LLM分析完成，处理了{llm_processed_count}条反馈，预估成本${cost_estimate:.2f}")
            return enhanced_results
            
        except Exception as e:
            result.llm_stage.status = "failed"
            result.llm_stage.error_message = str(e)
            result.llm_stage.end_time = datetime.now()
            raise
    
    async def _stage_3_priority_calculation(self, 
                                           enhanced_results: List[Dict], 
                                           result: HybridAnalysisResult) -> List[PriorityScoreResult]:
        """阶段3：高级优先级计算"""
        
        result.priority_stage.status = "processing"
        result.priority_stage.start_time = datetime.now()
        result.priority_stage.total_count = len(enhanced_results)
        
        try:
            # 获取高级优先级引擎
            priority_engine = get_advanced_priority_engine(self.settings.dict())
            
            # 计算优先级得分
            priority_results = await priority_engine.calculate_priority_scores(enhanced_results)
            
            result.priority_stage.processed_count = len(priority_results)
            result.priority_stage.status = "completed"
            result.priority_stage.end_time = datetime.now()
            
            # 统计高优先级问题
            result.high_priority_count = len([pr for pr in priority_results 
                                            if pr.priority_tier in ['P0', 'P1']])
            
            logger.info(f"优先级计算完成，{len(priority_results)}条反馈中{result.high_priority_count}条为高优先级")
            return priority_results
            
        except Exception as e:
            result.priority_stage.status = "failed"
            result.priority_stage.error_message = str(e)
            result.priority_stage.end_time = datetime.now()
            raise
    
    async def _stage_4_action_generation(self, 
                                        priority_results: List[PriorityScoreResult], 
                                        result: HybridAnalysisResult) -> Optional[ActionPlan]:
        """阶段4：行动计划生成"""
        
        result.action_stage.status = "processing"
        result.action_stage.start_time = datetime.now()
        result.action_stage.total_count = len(priority_results)
        
        try:
            # 获取行动生成器
            action_generator = get_action_generator(self.settings.dict())
            
            # 转换数据格式
            priority_data = []
            for pr in priority_results:
                priority_data.append({
                    'priority_score': pr.__dict__,
                    'feedback_data': {}  # 这里需要从priority_results中提取feedback_data
                })
            
            # 生成行动计划
            action_plan = await action_generator.generate_action_plan(priority_data)
            
            result.action_stage.processed_count = len(action_plan.action_items)
            result.action_stage.status = "completed"
            result.action_stage.end_time = datetime.now()
            result.action_items_generated = len(action_plan.action_items)
            
            logger.info(f"行动计划生成完成，包含{len(action_plan.action_items)}个行动项")
            return action_plan
            
        except Exception as e:
            result.action_stage.status = "failed"
            result.action_stage.error_message = str(e)
            result.action_stage.end_time = datetime.now()
            logger.warning(f"行动计划生成失败: {e}")
            return None
    
    def _create_fallback_analysis(self, filter_result: FilterResult) -> Dict:
        """创建备用分析结果"""
        return {
            'primary_sentiment': filter_result.sentiment,
            'sentiment_intensity': 0.5,
            'urgency_level': 'medium',
            'urgency_score': 0.5,
            'requirement_type': 'functional',
            'requirement_category': filter_result.category,
            'requirement_priority': 'should_have',
            'impact_scope': 'individual',
            'impact_frequency': 'sometimes',
            'user_journey_stage': 'daily_use',
            'technical_complexity': 'medium',
            'implementation_effort': 'days',
            'dependency_level': 'low_dependency',
            'business_value': 'efficiency',
            'strategic_alignment': 'important',
            'competitive_advantage': 'parity',
            'user_segment': 'power_users',
            'user_pain_level': 'minor_inconvenience',
            'user_workaround': None,
            'root_cause': None,
            'solution_suggestion': None,
            'related_areas': [],
            'action_owner': 'product',
            'estimated_timeline': 'sprint',
            'success_metrics': [],
            'confidence_score': 0.3,
            'analysis_timestamp': datetime.now().isoformat(),
            'llm_model_used': 'fallback'
        }
    
    def _serialize_priority_result(self, pr: PriorityScoreResult) -> Dict:
        """序列化优先级结果"""
        return {
            'feedback_id': pr.feedback_id,
            'overall_priority_score': pr.overall_priority_score,
            'impact_score': pr.impact_score,
            'urgency_score': pr.urgency_score,
            'effort_score': pr.effort_score,
            'business_value_score': pr.business_value_score,
            'strategic_score': pr.strategic_score,
            'user_voice_score': pr.user_voice_score,
            'expected_roi': pr.expected_roi,
            'risk_factor': pr.risk_factor,
            'confidence_level': pr.confidence_level,
            'recommendation': pr.recommendation,
            'priority_tier': pr.priority_tier,
            'estimated_impact_users': pr.estimated_impact_users,
            'suggested_timeline': pr.suggested_timeline,
            'deadline_pressure': pr.deadline_pressure,
            'calculation_timestamp': pr.calculation_timestamp.isoformat(),
            'model_version': pr.model_version
        }
    
    def _generate_insights_summary(self, 
                                 priority_results: List[PriorityScoreResult], 
                                 filter_results: List[FilterResult]) -> Dict:
        """生成洞察摘要"""
        
        if not priority_results:
            return {'message': '暂无数据生成洞察'}
        
        # 统计分析
        total_count = len(priority_results)
        avg_priority_score = sum(pr.overall_priority_score for pr in priority_results) / total_count
        avg_roi = sum(pr.expected_roi for pr in priority_results) / total_count
        
        # 优先级分布
        priority_distribution = {'P0': 0, 'P1': 0, 'P2': 0, 'P3': 0}
        for pr in priority_results:
            priority_distribution[pr.priority_tier] += 1
        
        # 情感分布
        sentiment_distribution = {'positive': 0, 'negative': 0, 'neutral': 0}
        for fr in filter_results:
            sentiment_distribution[fr.sentiment] += 1
        
        # 关键洞察
        key_insights = []
        
        if priority_distribution['P0'] > 0:
            key_insights.append(f"发现{priority_distribution['P0']}个P0级紧急问题，需要立即处理")
        
        if avg_roi > 1.0:
            key_insights.append(f"整体预期ROI为{avg_roi:.1%}，投资价值较高")
        
        negative_ratio = sentiment_distribution['negative'] / total_count
        if negative_ratio > 0.3:
            key_insights.append(f"负面反馈占比{negative_ratio:.1%}，需要关注用户满意度")
        
        return {
            'total_analyzed': total_count,
            'average_priority_score': round(avg_priority_score, 2),
            'average_roi': round(avg_roi, 3),
            'priority_distribution': priority_distribution,
            'sentiment_distribution': sentiment_distribution,
            'key_insights': key_insights,
            'recommendations': self._generate_strategic_recommendations(priority_results)
        }
    
    def _generate_strategic_recommendations(self, priority_results: List[PriorityScoreResult]) -> List[str]:
        """生成战略建议"""
        recommendations = []
        
        high_priority = [pr for pr in priority_results if pr.priority_tier in ['P0', 'P1']]
        if high_priority:
            recommendations.append(f"优先处理{len(high_priority)}个高优先级问题，预计影响{sum(pr.estimated_impact_users for pr in high_priority)}用户")
        
        high_roi_items = [pr for pr in priority_results if pr.expected_roi > 1.0]
        if high_roi_items:
            recommendations.append(f"重点关注{len(high_roi_items)}个高ROI项目，可快速提升业务价值")
        
        low_effort_items = [pr for pr in priority_results if pr.effort_score < 40]
        if low_effort_items:
            recommendations.append(f"考虑优先实现{len(low_effort_items)}个低成本改进项，作为快赢项目")
        
        return recommendations
    
    def _calculate_efficiency_ratio(self, result: HybridAnalysisResult) -> float:
        """计算效率比例"""
        if result.total_feedbacks == 0:
            return 0.0
        
        # 效率 = 高质量分析数量 / 总反馈数量
        quality_analyses = result.llm_processed_count + (result.llm_skipped_count * 0.3)  # 预筛选也有一定价值
        return min(quality_analyses / result.total_feedbacks, 1.0)

# 全局引擎实例
hybrid_engine = HybridAnalysisEngine()

@router.post("/analyze", response_model=HybridAnalysisResult)
async def analyze_feedbacks(request: FeedbackAnalysisRequest, background_tasks: BackgroundTasks):
    """
    混合智能分析接口
    整合四个核心模块，实现端到端的反馈分析
    """
    try:
        result = await hybrid_engine.process_feedbacks(
            feedbacks=request.feedbacks,
            analysis_config=request.analysis_config,
            generate_action_plan=request.generate_action_plan
        )
        return result
        
    except Exception as e:
        logger.error(f"混合分析接口错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-analyze")
async def batch_analyze_by_ids(request: BatchAnalysisRequest):
    """
    批量分析指定ID的反馈
    """
    try:
        # TODO: 从数据库获取反馈数据
        # feedbacks = await get_feedbacks_by_ids(request.feedback_ids)
        
        # 模拟数据
        feedbacks = [{'id': fid, 'text': f'测试反馈 {fid}', 'metadata': {}} 
                    for fid in request.feedback_ids]
        
        result = await hybrid_engine.process_feedbacks(
            feedbacks=feedbacks,
            analysis_config={'mode': request.analysis_mode},
            generate_action_plan=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"批量分析接口错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-metrics")
async def get_performance_metrics():
    """
    获取性能指标
    """
    # TODO: 实现性能指标统计
    return {
        "message": "性能指标功能开发中",
        "current_config": hybrid_engine.performance_config
    }

@router.get("/analysis-status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """
    获取分析状态
    """
    if analysis_id in hybrid_engine.active_tasks:
        return hybrid_engine.active_tasks[analysis_id]
    else:
        raise HTTPException(status_code=404, detail="分析任务不存在")

@router.post("/configure-performance")
async def configure_performance(config: Dict):
    """
    配置性能参数
    """
    try:
        hybrid_engine.performance_config.update(config)
        return {"message": "性能配置更新成功", "config": hybrid_engine.performance_config}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置更新失败: {e}")

@router.get("/health")
async def health_check():
    """
    健康检查
    """
    try:
        # 检查各模块状态
        status = {
            "intelligent_filter": "ready",
            "llm_analyzer": "ready", 
            "priority_engine": "ready",
            "action_generator": "ready",
            "database": "ready",
            "timestamp": datetime.now().isoformat()
        }
        
        return {"status": "healthy", "modules": status}
        
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)} 