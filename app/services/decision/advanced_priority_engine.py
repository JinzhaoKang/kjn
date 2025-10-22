"""
高级优先级引擎
融合LLM分析结果和传统算法，实现多维度的需求洞察量化与优先级排序
"""
import math
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class PriorityScoreResult:
    """优先级得分结果"""
    feedback_id: str
    overall_priority_score: float  # 总体优先级得分 (0-100)
    
    # 分类得分
    impact_score: float           # 影响力得分 (0-100)
    urgency_score: float          # 紧急性得分 (0-100)
    effort_score: float           # 实现成本得分 (0-100, 越低越好)
    business_value_score: float   # 商业价值得分 (0-100)
    strategic_score: float        # 战略匹配得分 (0-100)
    user_voice_score: float       # 用户声音得分 (0-100)
    
    # 量化指标
    expected_roi: float           # 预期投资回报率
    risk_factor: float            # 风险因子 (0-1)
    confidence_level: float       # 置信度 (0-1)
    
    # 决策建议
    recommendation: str           # 推荐行动
    priority_tier: str            # 优先级层级 (P0/P1/P2/P3)
    estimated_impact_users: int   # 预估影响用户数
    
    # 时间相关
    suggested_timeline: str       # 建议时间线
    deadline_pressure: float     # 截止日期压力 (0-1)
    
    # 元数据
    calculation_timestamp: datetime
    model_version: str

@dataclass  
class PriorityInsight:
    """优先级洞察"""
    insight_type: str             # feature_gap/user_pain/competitive_threat/opportunity
    description: str              # 洞察描述
    supporting_evidence: List[str] # 支撑证据
    quantified_impact: float     # 量化影响 (0-1)
    confidence: float            # 置信度 (0-1)
    action_recommendations: List[str] # 行动建议

class AdvancedPriorityEngine:
    """高级优先级引擎"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # 权重配置 - 可根据业务需求调整
        self.dimension_weights = {
            "impact": 0.25,        # 影响力权重
            "urgency": 0.20,       # 紧急性权重  
            "effort": 0.15,        # 实现成本权重 (负向)
            "business_value": 0.20, # 商业价值权重
            "strategic": 0.10,     # 战略匹配权重
            "user_voice": 0.10     # 用户声音权重
        }
        
        # 业务规则配置
        self.business_rules = {
            "security_multiplier": 1.5,      # 安全问题优先级倍数
            "compliance_multiplier": 1.3,    # 合规问题优先级倍数
            "vip_user_multiplier": 1.2,      # VIP用户反馈倍数
            "critical_bug_threshold": 0.8,   # 严重Bug阈值
            "feature_vs_bug_ratio": 0.7      # 功能vs Bug优先级比例
        }
        
        # 时间衰减参数
        self.time_decay_params = {
            "half_life_days": 30,            # 半衰期天数
            "max_age_penalty": 0.5           # 最大时间惩罚
        }
        
        # 聚类参数
        self.clustering_params = {
            "n_clusters": 5,                 # 聚类数量
            "feature_dimensions": [           # 聚类特征维度
                "sentiment_intensity",
                "urgency_score", 
                "impact_scope_numeric",
                "business_value_numeric"
            ]
        }
        
    async def calculate_priority_scores(self, feedbacks_with_analysis: List[Dict]) -> List[PriorityScoreResult]:
        """计算优先级得分"""
        results = []
        
        for i, feedback_data in enumerate(feedbacks_with_analysis):
            try:
                # 获取各维度得分
                impact = self._calculate_impact_score(feedback_data)
                urgency = self._calculate_urgency_score(feedback_data)
                effort = self._calculate_effort_score(feedback_data)
                business_value = self._calculate_business_value_score(feedback_data)
                strategic = self._calculate_strategic_score(feedback_data)
                user_voice = self._calculate_user_voice_score(feedback_data)
                
                # 计算总体优先级得分
                overall_score = self._calculate_overall_score(
                    impact, urgency, effort, business_value, strategic, user_voice
                )
                
                # 计算风险和置信度
                risk_factor = self._calculate_risk_factor(feedback_data)
                confidence = self._calculate_confidence_level(feedback_data)
                
                # 生成决策建议
                recommendation, priority_tier = self._generate_recommendation(
                    overall_score, urgency, impact, effort
                )
                
                # 预估影响用户数
                estimated_users = self._estimate_impact_users(feedback_data)
                
                # 计算ROI
                expected_roi = self._calculate_expected_roi(
                    business_value, effort, impact, feedback_data
                )
                
                # 时间线建议
                timeline = self._suggest_timeline(priority_tier, effort, urgency)
                deadline_pressure = self._calculate_deadline_pressure(feedback_data)
                
                result = PriorityScoreResult(
                    feedback_id=feedback_data.get('id', f'feedback_{i}'),
                    overall_priority_score=round(overall_score, 2),
                    impact_score=round(impact, 2),
                    urgency_score=round(urgency, 2),
                    effort_score=round(effort, 2),
                    business_value_score=round(business_value, 2),
                    strategic_score=round(strategic, 2),
                    user_voice_score=round(user_voice, 2),
                    expected_roi=round(expected_roi, 2),
                    risk_factor=round(risk_factor, 3),
                    confidence_level=round(confidence, 3),
                    recommendation=recommendation,
                    priority_tier=priority_tier,
                    estimated_impact_users=estimated_users,
                    suggested_timeline=timeline,
                    deadline_pressure=round(deadline_pressure, 3),
                    calculation_timestamp=datetime.now(),
                    model_version="v2.0"
                )
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"计算优先级得分失败 (feedback {i}): {e}")
                # 添加默认结果
                results.append(self._create_default_priority_result(
                    feedback_data.get('id', f'unknown_{i}')
                ))
        
        # 排序结果
        results.sort(key=lambda x: x.overall_priority_score, reverse=True)
        
        return results
    
    def _calculate_impact_score(self, feedback_data: Dict) -> float:
        """计算影响力得分"""
        llm_analysis = feedback_data.get('deep_analysis', {})
        
        # 基础影响力
        impact_scope = llm_analysis.get('impact_scope', 'individual')
        scope_score = {'individual': 20, 'team': 40, 'department': 60, 'company': 80, 'ecosystem': 100}.get(impact_scope, 40)
        
        # 用户痛点程度
        pain_level = llm_analysis.get('user_pain_level', 'minor_inconvenience')
        pain_score = {'enhancement': 25, 'minor_inconvenience': 40, 'major_friction': 70, 'blocker': 100}.get(pain_level, 40)
        
        # 频率影响
        frequency = llm_analysis.get('impact_frequency', 'sometimes')
        freq_multiplier = {'rarely': 0.7, 'sometimes': 1.0, 'often': 1.3, 'always': 1.5}.get(frequency, 1.0)
        
        impact_score = (scope_score + pain_score) / 2 * freq_multiplier
        return min(impact_score, 100)
    
    def _calculate_urgency_score(self, feedback_data: Dict) -> float:
        """计算紧急性得分"""
        llm_analysis = feedback_data.get('deep_analysis', {})
        
        # LLM紧急性得分
        urgency_base = llm_analysis.get('urgency_score', 0.5) * 100
        
        # 时间敏感性
        timeline = llm_analysis.get('estimated_timeline', 'sprint')
        timeline_multiplier = {
            'immediate': 1.5,
            'sprint': 1.2,
            'quarter': 1.0,
            'roadmap': 0.8
        }.get(timeline, 1.0)
        
        urgency_score = urgency_base * timeline_multiplier
        return min(urgency_score, 100)
    
    def _calculate_effort_score(self, feedback_data: Dict) -> float:
        """计算实现成本得分（越低越好）"""
        llm_analysis = feedback_data.get('deep_analysis', {})
        
        # 技术复杂度
        complexity = llm_analysis.get('technical_complexity', 'medium')
        complexity_score = {'low': 25, 'medium': 50, 'high': 75, 'very_high': 100}.get(complexity, 50)
        
        # 实现工作量
        effort = llm_analysis.get('implementation_effort', 'days')
        effort_score = {'hours': 20, 'days': 40, 'weeks': 70, 'months': 90}.get(effort, 50)
        
        return (complexity_score + effort_score) / 2
    
    def _calculate_business_value_score(self, feedback_data: Dict) -> float:
        """计算商业价值得分"""
        llm_analysis = feedback_data.get('deep_analysis', {})
        
        # 基础业务价值
        business_value = llm_analysis.get('business_value', 'efficiency')
        base_score = {'efficiency': 40, 'retention': 60, 'acquisition': 80, 'revenue': 100, 'compliance': 70}.get(business_value, 50)
        
        # 竞争优势加成
        competitive_advantage = llm_analysis.get('competitive_advantage', 'parity')
        competitive_multiplier = {
            'differentiator': 1.4,
            'parity': 1.0,
            'table_stakes': 1.2,
            'internal': 0.8
        }.get(competitive_advantage, 1.0)
        
        return min(base_score * competitive_multiplier, 100)
    
    def _calculate_strategic_score(self, feedback_data: Dict) -> float:
        """计算战略匹配得分"""
        llm_analysis = feedback_data.get('deep_analysis', {})
        
        # 战略匹配度
        alignment = llm_analysis.get('strategic_alignment', 'important')
        alignment_score = {'off_strategy': 20, 'nice_to_have': 40, 'important': 70, 'core': 100}.get(alignment, 50)
        
        # 需求优先级
        priority = llm_analysis.get('requirement_priority', 'should_have')
        priority_score = {'wont_have': 20, 'could_have': 40, 'should_have': 70, 'must_have': 100}.get(priority, 50)
        
        return (alignment_score + priority_score) / 2
    
    def _calculate_user_voice_score(self, feedback_data: Dict) -> float:
        """计算用户声音得分"""
        filter_result = feedback_data.get('filter_result', {})
        user_metadata = feedback_data.get('metadata', {})
        
        # 预筛选优先级得分
        base_score = filter_result.get('priority_score', 0.5) * 100
        
        # 用户价值加成
        user_value_multiplier = 1.0
        if user_metadata.get('is_vip', False):
            user_value_multiplier += 0.3
        if user_metadata.get('is_paid_user', False):
            user_value_multiplier += 0.2
        
        return min(base_score * user_value_multiplier, 100)
    
    def _calculate_overall_score(self, impact: float, urgency: float, effort: float, 
                               business_value: float, strategic: float, user_voice: float) -> float:
        """计算总体优先级得分"""
        
        # effort是负向指标，需要转换
        effort_normalized = 100 - effort
        
        weighted_score = (
            impact * self.dimension_weights['impact'] +
            urgency * self.dimension_weights['urgency'] +
            effort_normalized * self.dimension_weights['effort'] +
            business_value * self.dimension_weights['business_value'] +
            strategic * self.dimension_weights['strategic'] +
            user_voice * self.dimension_weights['user_voice']
        )
        
        return min(weighted_score, 100)
    
    def _calculate_risk_factor(self, feedback_data: Dict) -> float:
        """计算风险因子"""
        llm_analysis = feedback_data.get('deep_analysis', {})
        
        # 技术风险
        complexity = llm_analysis.get('technical_complexity', 'medium')
        tech_risk = {'low': 0.1, 'medium': 0.3, 'high': 0.6, 'very_high': 0.8}.get(complexity, 0.3)
        
        # 置信度风险
        confidence = llm_analysis.get('confidence_score', 0.7)
        conf_risk = 1.0 - confidence
        
        return (tech_risk + conf_risk) / 2
    
    def _calculate_confidence_level(self, feedback_data: Dict) -> float:
        """计算置信度"""
        filter_result = feedback_data.get('filter_result', {})
        llm_analysis = feedback_data.get('deep_analysis', {})
        
        confidences = []
        
        if 'confidence' in filter_result:
            confidences.append(filter_result['confidence'])
        
        if 'confidence_score' in llm_analysis:
            confidences.append(llm_analysis['confidence_score'])
        
        return np.mean(confidences) if confidences else 0.5
    
    def _generate_recommendation(self, overall_score: float, urgency: float, impact: float, effort: float) -> Tuple[str, str]:
        """生成决策建议"""
        
        # 确定优先级层级
        if overall_score >= 80:
            priority_tier = "P0"
            recommendation = "立即启动开发，分配最优资源"
        elif overall_score >= 65:
            priority_tier = "P1"
            recommendation = "纳入当前迭代，优先处理"
        elif overall_score >= 45:
            priority_tier = "P2"
            recommendation = "加入产品路线图，合适时机实现"
        else:
            priority_tier = "P3"
            recommendation = "暂时搁置，定期重新评估"
        
        return recommendation, priority_tier
    
    def _estimate_impact_users(self, feedback_data: Dict) -> int:
        """预估影响用户数"""
        llm_analysis = feedback_data.get('deep_analysis', {})
        
        scope = llm_analysis.get('impact_scope', 'individual')
        base_users = {
            'individual': 100,
            'team': 500, 
            'department': 2000,
            'company': 10000,
            'ecosystem': 50000
        }.get(scope, 500)
        
        frequency = llm_analysis.get('impact_frequency', 'sometimes')
        freq_multiplier = {
            'always': 1.0,
            'often': 0.8,
            'sometimes': 0.5,
            'rarely': 0.2
        }.get(frequency, 0.5)
        
        return int(base_users * freq_multiplier)
    
    def _calculate_expected_roi(self, business_value: float, effort: float, impact: float, feedback_data: Dict) -> float:
        """计算预期投资回报率"""
        benefits = (business_value * impact) / 10000
        costs = effort / 100
        
        if costs > 0:
            roi = (benefits - costs) / costs
        else:
            roi = benefits
        
        return max(roi, -1.0)
    
    def _suggest_timeline(self, priority_tier: str, effort: float, urgency: float) -> str:
        """建议实现时间线"""
        if priority_tier == "P0":
            return "立即(1-3天)" if urgency >= 80 else "当前迭代"
        elif priority_tier == "P1":
            return "下个迭代" if effort <= 40 else "本季度"
        elif priority_tier == "P2":
            return "未来2-3个季度"
        else:
            return "长期规划"
    
    def _calculate_deadline_pressure(self, feedback_data: Dict) -> float:
        """计算截止日期压力"""
        llm_analysis = feedback_data.get('deep_analysis', {})
        
        urgency = llm_analysis.get('urgency_score', 0.5)
        timeline = llm_analysis.get('estimated_timeline', 'sprint')
        
        timeline_pressure = {
            'immediate': 1.0,
            'sprint': 0.7,
            'quarter': 0.4,
            'roadmap': 0.2
        }.get(timeline, 0.5)
        
        return (urgency + timeline_pressure) / 2
    
    def _create_default_priority_result(self, feedback_id: str) -> PriorityScoreResult:
        """创建默认优先级结果"""
        return PriorityScoreResult(
            feedback_id=feedback_id,
            overall_priority_score=30.0,
            impact_score=30.0,
            urgency_score=30.0,
            effort_score=50.0,
            business_value_score=30.0,
            strategic_score=30.0,
            user_voice_score=30.0,
            expected_roi=0.0,
            risk_factor=0.5,
            confidence_level=0.3,
            recommendation="需要更多信息进行评估",
            priority_tier="P3",
            estimated_impact_users=100,
            suggested_timeline="待定",
            deadline_pressure=0.3,
            calculation_timestamp=datetime.now(),
            model_version="v2.0"
        )

# 全局实例
advanced_priority_engine = None

def get_advanced_priority_engine(config: Dict) -> AdvancedPriorityEngine:
    """获取高级优先级引擎实例"""
    global advanced_priority_engine
    
    if advanced_priority_engine is None:
        advanced_priority_engine = AdvancedPriorityEngine(config)
    
    return advanced_priority_engine 