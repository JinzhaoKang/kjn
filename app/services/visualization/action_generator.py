"""
行动指令自动生成器
将用户反馈分析结果转化为具体的可执行行动建议和任务规划
"""
import json
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """行动类型枚举"""
    BUG_FIX = "bug_fix"
    FEATURE_DEVELOPMENT = "feature_development"
    UX_IMPROVEMENT = "ux_improvement"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    INTEGRATION = "integration"
    RESEARCH = "research"
    DESIGN = "design"
    TESTING = "testing"
    COMMUNICATION = "communication"

class Priority(Enum):
    """优先级枚举"""
    P0 = "P0"  # 紧急 - 立即处理
    P1 = "P1"  # 高 - 当前迭代
    P2 = "P2"  # 中 - 下个版本
    P3 = "P3"  # 低 - 长期规划

@dataclass
class ActionItem:
    """行动项"""
    id: str
    title: str
    description: str
    action_type: ActionType
    priority: Priority
    owner_team: str              # 负责团队
    assignee: Optional[str]      # 具体负责人
    estimated_effort: str        # 预估工作量
    timeline: str                # 时间线
    dependencies: List[str]      # 依赖项
    acceptance_criteria: List[str] # 验收标准
    success_metrics: List[str]   # 成功指标
    business_justification: str  # 业务理由
    technical_details: str       # 技术细节
    risk_assessment: str         # 风险评估
    mitigation_plan: str         # 风险缓解计划
    related_feedback_ids: List[str] # 相关反馈ID
    created_at: datetime
    updated_at: datetime

@dataclass
class ActionPlan:
    """行动计划"""
    plan_id: str
    title: str
    summary: str
    total_actions: int
    p0_actions: int
    p1_actions: int
    p2_actions: int
    p3_actions: int
    estimated_timeline: str
    total_effort_estimate: str
    key_milestones: List[Dict]
    resource_requirements: Dict
    risk_factors: List[str]
    expected_outcomes: List[str]
    action_items: List[ActionItem]
    created_at: datetime

@dataclass
class DashboardData:
    """仪表盘数据"""
    # 概览数据
    total_feedback_processed: int
    high_priority_issues: int
    in_progress_actions: int
    completed_actions: int
    
    # 趋势数据
    feedback_trend: List[Dict]       # 反馈趋势
    sentiment_trend: List[Dict]      # 情感趋势
    priority_distribution: Dict     # 优先级分布
    category_distribution: Dict     # 类别分布
    
    # 优先级矩阵
    priority_matrix: List[Dict]     # 影响力vs努力矩阵
    
    # Top问题
    top_bugs: List[Dict]            # Top 5 Bug
    top_features: List[Dict]        # Top 5 功能需求
    
    # 团队工作负载
    team_workload: Dict             # 各团队工作负载
    
    # 预测数据
    predicted_user_satisfaction: float  # 预测用户满意度
    estimated_roi: float               # 预期ROI
    
    # 更新时间
    last_updated: datetime

class ActionGenerator:
    """行动指令生成器"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # 团队能力配置
        self.team_capabilities = {
            "product": ["需求分析", "产品设计", "用户研究", "产品规划"],
            "engineering": ["前端开发", "后端开发", "数据库设计", "API开发", "性能优化"],
            "design": ["UI设计", "UX设计", "交互设计", "视觉设计"],
            "qa": ["功能测试", "性能测试", "自动化测试", "用户验收测试"],
            "devops": ["部署", "监控", "安全", "基础设施"],
            "support": ["用户支持", "文档编写", "培训", "客户沟通"],
            "marketing": ["用户调研", "竞品分析", "推广策略", "用户教育"]
        }
        
        # 工作量估算规则
        self.effort_estimation_rules = {
            "simple_ui_change": "2-4小时",
            "complex_ui_redesign": "1-2周",
            "simple_backend_api": "1-3天",
            "complex_backend_feature": "1-3周",
            "database_schema_change": "3-7天",
            "third_party_integration": "1-2周",
            "performance_optimization": "3-10天",
            "security_fix": "1-5天",
            "mobile_app_update": "1-2周",
            "user_research": "1-2周"
        }

    async def generate_action_plan(self, priority_results: List[Dict]) -> ActionPlan:
        """生成行动计划"""
        try:
            # 生成行动项
            action_items = []
            for result in priority_results:
                action_item = await self._create_action_item(result)
                if action_item:
                    action_items.append(action_item)
            
            # 优化行动项顺序
            optimized_actions = self._optimize_action_sequence(action_items)
            
            # 生成计划概要
            plan_summary = self._generate_plan_summary(optimized_actions)
            
            # 计算关键指标
            metrics = self._calculate_plan_metrics(optimized_actions)
            
            plan = ActionPlan(
                plan_id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=f"用户反馈驱动的产品改进计划 - {datetime.now().strftime('%Y年%m月')}",
                summary=plan_summary,
                total_actions=len(optimized_actions),
                p0_actions=len([a for a in optimized_actions if a.priority == Priority.P0]),
                p1_actions=len([a for a in optimized_actions if a.priority == Priority.P1]),
                p2_actions=len([a for a in optimized_actions if a.priority == Priority.P2]),
                p3_actions=len([a for a in optimized_actions if a.priority == Priority.P3]),
                estimated_timeline=metrics["timeline"],
                total_effort_estimate=metrics["effort"],
                key_milestones=[],
                resource_requirements={},
                risk_factors=[],
                expected_outcomes=[],
                action_items=optimized_actions,
                created_at=datetime.now()
            )
            
            return plan
            
        except Exception as e:
            logger.error(f"生成行动计划失败: {e}")
            return self._create_default_action_plan()
    
    async def _create_action_item(self, priority_result: Dict) -> Optional[ActionItem]:
        """创建单个行动项"""
        try:
            feedback_data = priority_result.get('feedback_data', {})
            llm_analysis = feedback_data.get('deep_analysis', {})
            priority_score = priority_result.get('priority_score', {})
            
            # 确定行动类型
            action_type = self._determine_action_type(llm_analysis)
            
            # 生成标题和描述
            title = self._generate_action_title(llm_analysis, action_type)
            description = self._generate_action_description(feedback_data, llm_analysis)
            
            action_item = ActionItem(
                id=f"action_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(title) % 10000}",
                title=title,
                description=description,
                action_type=action_type,
                priority=Priority(priority_score.get('priority_tier', 'P3')),
                owner_team=self._assign_owner_team(action_type, llm_analysis),
                assignee=None,
                estimated_effort=llm_analysis.get('implementation_effort', '1-2周'),
                timeline=priority_score.get('suggested_timeline', '待定'),
                dependencies=[],
                acceptance_criteria=self._generate_acceptance_criteria(action_type),
                success_metrics=llm_analysis.get('success_metrics', []),
                business_justification=self._generate_business_justification(llm_analysis),
                technical_details=f"技术复杂度：{llm_analysis.get('technical_complexity', 'medium')}",
                risk_assessment=f"风险等级：{'高' if priority_score.get('risk_factor', 0.5) > 0.7 else '中等'}",
                mitigation_plan="定期review进度，及时沟通问题",
                related_feedback_ids=[feedback_data.get('id', '')],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            return action_item
            
        except Exception as e:
            logger.error(f"创建行动项失败: {e}")
            return None
    
    def _determine_action_type(self, llm_analysis: Dict) -> ActionType:
        """确定行动类型"""
        category = llm_analysis.get('requirement_category', 'improvement')
        
        mapping = {
            'bug_fix': ActionType.BUG_FIX,
            'feature_request': ActionType.FEATURE_DEVELOPMENT,
            'improvement': ActionType.UX_IMPROVEMENT,
            'integration': ActionType.INTEGRATION
        }
        
        return mapping.get(category, ActionType.UX_IMPROVEMENT)
    
    def _generate_action_title(self, llm_analysis: Dict, action_type: ActionType) -> str:
        """生成行动项标题"""
        if action_type == ActionType.BUG_FIX:
            return f"修复{llm_analysis.get('root_cause', '系统')}相关问题"
        elif action_type == ActionType.FEATURE_DEVELOPMENT:
            return f"开发{llm_analysis.get('solution_suggestion', '新功能')}"
        elif action_type == ActionType.UX_IMPROVEMENT:
            return f"改进{llm_analysis.get('user_journey_stage', '用户')}体验"
        else:
            return f"处理用户反馈"
    
    def _generate_action_description(self, feedback_data: Dict, llm_analysis: Dict) -> str:
        """生成行动项描述"""
        original_feedback = feedback_data.get('text', '')
        description = f"基于用户反馈：「{original_feedback[:100]}...」\n\n"
        description += f"影响范围：{llm_analysis.get('impact_scope', '个人用户')}\n"
        description += f"紧急程度：{llm_analysis.get('urgency_level', '中等')}"
        return description
    
    def _assign_owner_team(self, action_type: ActionType, llm_analysis: Dict) -> str:
        """分配负责团队"""
        if action_type == ActionType.BUG_FIX:
            return "engineering"
        elif action_type == ActionType.FEATURE_DEVELOPMENT:
            return "engineering"
        elif action_type == ActionType.UX_IMPROVEMENT:
            return "design"
        else:
            return "product"
    
    def _generate_acceptance_criteria(self, action_type: ActionType) -> List[str]:
        """生成验收标准"""
        if action_type == ActionType.BUG_FIX:
            return ["问题不再重现", "相关功能正常工作", "通过回归测试"]
        elif action_type == ActionType.FEATURE_DEVELOPMENT:
            return ["功能按需求实现", "用户界面友好", "通过用户验收测试"]
        else:
            return ["改进效果可量化", "用户反馈积极", "指标有提升"]
    
    def _generate_business_justification(self, llm_analysis: Dict) -> str:
        """生成业务理由"""
        business_value = llm_analysis.get('business_value', 'efficiency')
        return f"业务价值：{business_value}\n战略匹配度：{llm_analysis.get('strategic_alignment', '重要')}"
    
    def _optimize_action_sequence(self, action_items: List[ActionItem]) -> List[ActionItem]:
        """优化行动项顺序"""
        def sort_key(item):
            priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
            return priority_order.get(item.priority.value, 3)
        
        return sorted(action_items, key=sort_key)
    
    def _generate_plan_summary(self, action_items: List[ActionItem]) -> str:
        """生成计划摘要"""
        total = len(action_items)
        p0_count = len([a for a in action_items if a.priority == Priority.P0])
        return f"本计划包含{total}个行动项，其中P0级{p0_count}个。主要聚焦于用户反馈中的关键问题。"
    
    def _calculate_plan_metrics(self, action_items: List[ActionItem]) -> Dict:
        """计算计划指标"""
        p0_items = [a for a in action_items if a.priority == Priority.P0]
        
        if p0_items:
            timeline = "立即开始，1-2周内完成P0项目"
        else:
            timeline = "按季度规划执行"
        
        total_effort = f"{len(action_items) * 2}-{len(action_items) * 5}人周"
        
        return {"timeline": timeline, "effort": total_effort}
    
    def _create_default_action_plan(self) -> ActionPlan:
        """创建默认行动计划"""
        return ActionPlan(
            plan_id="default_plan",
            title="默认行动计划",
            summary="由于数据不足，生成默认计划",
            total_actions=0,
            p0_actions=0,
            p1_actions=0,
            p2_actions=0,
            p3_actions=0,
            estimated_timeline="待定",
            total_effort_estimate="待评估",
            key_milestones=[],
            resource_requirements={},
            risk_factors=["数据不足"],
            expected_outcomes=["建立完善的反馈收集机制"],
            action_items=[],
            created_at=datetime.now()
        )

    async def generate_dashboard_data(self, feedback_data: List[Dict], priority_results: List[Dict], action_plan: ActionPlan) -> DashboardData:
        """生成仪表盘数据"""
        try:
            # 计算概览指标
            total_feedback = len(feedback_data)
            high_priority_issues = len([r for r in priority_results if r.get('priority_score', {}).get('priority_tier') in ['P0', 'P1']])
            in_progress = len([a for a in action_plan.action_items if a.priority in [Priority.P0, Priority.P1]])
            completed = 0  # TODO: 需要从数据库获取已完成的行动项
            
            # 生成趋势数据
            feedback_trend = self._generate_feedback_trend(feedback_data)
            sentiment_trend = self._generate_sentiment_trend(feedback_data)
            
            # 分布数据
            priority_distribution = self._calculate_priority_distribution(priority_results)
            category_distribution = self._calculate_category_distribution(feedback_data)
            
            # 优先级矩阵
            priority_matrix = self._generate_priority_matrix(priority_results)
            
            # Top问题
            top_bugs, top_features = self._identify_top_issues(priority_results)
            
            # 团队工作负载
            team_workload = action_plan.resource_requirements.get('team_workload', {})
            
            # 预测指标
            predicted_satisfaction = self._predict_user_satisfaction(priority_results)
            estimated_roi = self._calculate_total_roi(priority_results)
            
            dashboard_data = DashboardData(
                total_feedback_processed=total_feedback,
                high_priority_issues=high_priority_issues,
                in_progress_actions=in_progress,
                completed_actions=completed,
                feedback_trend=feedback_trend,
                sentiment_trend=sentiment_trend,
                priority_distribution=priority_distribution,
                category_distribution=category_distribution,
                priority_matrix=priority_matrix,
                top_bugs=top_bugs,
                top_features=top_features,
                team_workload=team_workload,
                predicted_user_satisfaction=predicted_satisfaction,
                estimated_roi=estimated_roi,
                last_updated=datetime.now()
            )
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"生成仪表盘数据失败: {e}")
            return self._create_default_dashboard_data()
    
    def _generate_feedback_trend(self, feedback_data: List[Dict]) -> List[Dict]:
        """生成反馈趋势数据"""
        # 按日期分组统计
        from collections import defaultdict
        daily_counts = defaultdict(int)
        
        for feedback in feedback_data:
            created_at = feedback.get('created_at', datetime.now().isoformat())
            try:
                date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                daily_counts[date.isoformat()] += 1
            except:
                daily_counts[datetime.now().date().isoformat()] += 1
        
        # 转换为图表数据格式
        trend_data = []
        for date, count in sorted(daily_counts.items()):
            trend_data.append({"date": date, "count": count})
        
        return trend_data[-30:]  # 返回最近30天的数据
    
    def _generate_sentiment_trend(self, feedback_data: List[Dict]) -> List[Dict]:
        """生成情感趋势数据"""
        from collections import defaultdict
        daily_sentiment = defaultdict(list)
        
        for feedback in feedback_data:
            created_at = feedback.get('created_at', datetime.now().isoformat())
            sentiment = feedback.get('filter_result', {}).get('sentiment', 'neutral')
            
            try:
                date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                daily_sentiment[date.isoformat()].append(sentiment)
            except:
                daily_sentiment[datetime.now().date().isoformat()].append(sentiment)
        
        trend_data = []
        for date, sentiments in sorted(daily_sentiment.items()):
            positive = sentiments.count('positive')
            negative = sentiments.count('negative')
            neutral = sentiments.count('neutral')
            total = len(sentiments)
            
            if total > 0:
                trend_data.append({
                    "date": date,
                    "positive_ratio": positive / total,
                    "negative_ratio": negative / total,
                    "neutral_ratio": neutral / total
                })
        
        return trend_data[-30:]
    
    def _calculate_priority_distribution(self, priority_results: List[Dict]) -> Dict:
        """计算优先级分布"""
        distribution = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        
        for result in priority_results:
            priority = result.get('priority_score', {}).get('priority_tier', 'P3')
            distribution[priority] += 1
        
        return distribution
    
    def _calculate_category_distribution(self, feedback_data: List[Dict]) -> Dict:
        """计算类别分布"""
        distribution = {}
        
        for feedback in feedback_data:
            category = feedback.get('filter_result', {}).get('category', 'general')
            distribution[category] = distribution.get(category, 0) + 1
        
        return distribution
    
    def _generate_priority_matrix(self, priority_results: List[Dict]) -> List[Dict]:
        """生成优先级矩阵数据（影响力vs工作量）"""
        matrix_data = []
        
        for result in priority_results:
            priority_score = result.get('priority_score', {})
            feedback_data = result.get('feedback_data', {})
            
            matrix_data.append({
                "id": feedback_data.get('id', ''),
                "title": feedback_data.get('text', '')[:50] + "...",
                "impact": priority_score.get('impact_score', 30),
                "effort": priority_score.get('effort_score', 50),
                "priority": priority_score.get('priority_tier', 'P3'),
                "roi": priority_score.get('expected_roi', 0)
            })
        
        return matrix_data
    
    def _identify_top_issues(self, priority_results: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """识别Top问题"""
        bugs = []
        features = []
        
        for result in priority_results:
            feedback_data = result.get('feedback_data', {})
            llm_analysis = feedback_data.get('deep_analysis', {})
            priority_score = result.get('priority_score', {})
            
            item = {
                "id": feedback_data.get('id', ''),
                "title": feedback_data.get('text', '')[:100],
                "priority_score": priority_score.get('overall_priority_score', 0),
                "impact_users": priority_score.get('estimated_impact_users', 0),
                "priority_tier": priority_score.get('priority_tier', 'P3')
            }
            
            category = llm_analysis.get('requirement_category', 'improvement')
            if category == 'bug_fix':
                bugs.append(item)
            elif category == 'feature_request':
                features.append(item)
        
        # 按优先级得分排序，返回Top 5
        bugs.sort(key=lambda x: x['priority_score'], reverse=True)
        features.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return bugs[:5], features[:5]
    
    def _predict_user_satisfaction(self, priority_results: List[Dict]) -> float:
        """预测用户满意度"""
        if not priority_results:
            return 0.7  # 默认值
        
        # 基于高优先级问题的解决情况预测满意度
        high_priority_count = len([r for r in priority_results if r.get('priority_score', {}).get('priority_tier') in ['P0', 'P1']])
        total_count = len(priority_results)
        
        if total_count == 0:
            return 0.7
        
        high_priority_ratio = high_priority_count / total_count
        
        # 简单的预测模型：高优先级问题越多，满意度提升潜力越大
        baseline_satisfaction = 0.6
        improvement_potential = high_priority_ratio * 0.3
        
        return min(baseline_satisfaction + improvement_potential, 0.95)
    
    def _calculate_total_roi(self, priority_results: List[Dict]) -> float:
        """计算总体ROI"""
        if not priority_results:
            return 0.0
        
        total_roi = sum(r.get('priority_score', {}).get('expected_roi', 0) for r in priority_results)
        return total_roi / len(priority_results)
    
    def _create_default_dashboard_data(self) -> DashboardData:
        """创建默认仪表盘数据"""
        return DashboardData(
            total_feedback_processed=0,
            high_priority_issues=0,
            in_progress_actions=0,
            completed_actions=0,
            feedback_trend=[],
            sentiment_trend=[],
            priority_distribution={"P0": 0, "P1": 0, "P2": 0, "P3": 0},
            category_distribution={},
            priority_matrix=[],
            top_bugs=[],
            top_features=[],
            team_workload={},
            predicted_user_satisfaction=0.7,
            estimated_roi=0.0,
            last_updated=datetime.now()
        )

# 全局实例
action_generator = None

def get_action_generator(config: Dict) -> ActionGenerator:
    """获取行动生成器实例"""
    global action_generator
    
    if action_generator is None:
        action_generator = ActionGenerator(config)
    
    return action_generator 