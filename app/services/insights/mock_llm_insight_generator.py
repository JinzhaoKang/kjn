"""
模拟LLM洞察生成器
不依赖OpenAI API，用于演示和测试
"""
import json
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)

@dataclass
class InsightResult:
    """洞察结果"""
    insight_id: str
    title: str
    description: str
    insight_type: str              # trend/pattern/opportunity/risk
    confidence_score: float        # 0-1
    impact_level: str              # high/medium/low
    supporting_evidence: List[str] # 支撑证据
    affected_user_segments: List[str] # 影响的用户群体
    business_impact: str           # 业务影响描述
    generated_at: datetime

@dataclass
class ActionPlan:
    """执行计划"""
    plan_id: str
    title: str
    summary: str
    priority: str                  # P0/P1/P2/P3
    estimated_effort: str          # 预估工作量
    timeline: str                  # 建议时间线
    owner_team: str               # 负责团队
    success_metrics: List[str]     # 成功指标
    action_steps: List[Dict]       # 具体执行步骤
    risk_assessment: str           # 风险评估
    expected_outcome: str          # 预期结果
    related_insights: List[str]    # 相关洞察ID
    generated_at: datetime

class MockLLMInsightGenerator:
    """模拟LLM洞察生成器"""
    
    def __init__(self, config: Dict):
        self.config = config
        logger.info("模拟LLM洞察生成器初始化完成")
    
    async def generate_insights_from_feedback(self, feedback_data: List[Dict]) -> List[InsightResult]:
        """从反馈数据生成洞察"""
        try:
            logger.info(f"开始分析{len(feedback_data)}条反馈数据")
            
            # 分析反馈数据
            analysis = self._analyze_feedback_data(feedback_data)
            
            # 生成洞察
            insights = self._generate_mock_insights(analysis)
            
            logger.info(f"成功生成{len(insights)}个洞察")
            return insights
            
        except Exception as e:
            logger.error(f"生成洞察失败: {e}")
            return []
    
    async def generate_action_plans_from_insights(self, insights: List[InsightResult], feedback_context: Dict) -> List[ActionPlan]:
        """从洞察生成模拟执行计划"""
        try:
            logger.info(f"基于{len(insights)}个洞察生成模拟执行计划")
            
            action_plans = []
            now = datetime.now()
            
            for i, insight in enumerate(insights):
                # 根据洞察类型和影响级别确定优先级
                if insight.impact_level == "high":
                    priority = "P0" if insight.insight_type == "risk" else "P1"
                elif insight.impact_level == "medium":
                    priority = "P1" if insight.insight_type == "risk" else "P2"
                else:
                    priority = "P2" if insight.insight_type == "risk" else "P3"
                
                plan = ActionPlan(
                    plan_id=f"action_plan_{now.strftime('%Y%m%d_%H%M%S')}_{i}",
                    title=f"解决方案：{insight.title[:30]}...",
                    summary=f"针对{insight.insight_type}类型洞察的解决方案，预期能够{['降低风险', '把握机会', '优化趋势', '识别模式'][i % 4]}。",
                    priority=priority,
                    estimated_effort=["1-2周", "2-3周", "1个月", "2个月"][i % 4],
                    timeline=["立即开始", "本月内", "下个月", "季度内"][i % 4],
                    owner_team=["engineering", "product", "design", "marketing"][i % 4],
                    success_metrics=[
                        f"提升用户满意度{10 + i * 5}%",
                        f"减少相关反馈{20 + i * 10}%",
                        f"提高功能使用率{15 + i * 5}%"
                    ],
                    action_steps=[
                        {
                            "step": 1,
                            "description": f"分析{insight.insight_type}问题的根本原因",
                            "owner": "分析师",
                            "duration": "3天"
                        },
                        {
                            "step": 2,
                            "description": "制定详细的解决方案",
                            "owner": "产品经理",
                            "duration": "5天"
                        },
                        {
                            "step": 3,
                            "description": "实施解决方案",
                            "owner": "开发团队",
                            "duration": "10天"
                        }
                    ],
                    risk_assessment=f"实施风险：{['低', '中', '高'][i % 3]}，主要风险来自于{['技术复杂度', '用户接受度', '资源投入'][i % 3]}",
                    expected_outcome=f"预期解决{insight.title}相关问题，提升用户体验和满意度",
                    related_insights=[insight.insight_id],
                    generated_at=now
                )
                action_plans.append(plan)
            
            logger.info(f"成功生成{len(action_plans)}个模拟执行计划")
            return action_plans
            
        except Exception as e:
            logger.error(f"生成模拟执行计划失败: {e}")
            return []

    async def generate_full_text_insights(self, feedback_data: List[Dict]) -> Dict:
        """
        生成模拟全文洞察 - 模拟利用1M上下文能力的深度分析
        """
        try:
            logger.info(f"开始模拟全文洞察分析，数据量: {len(feedback_data)}条")
            
            # 模拟全文深度分析
            insights = []
            now = datetime.now()
            total_feedback = len(feedback_data)
            
            # 1. 全局趋势洞察
            insights.append(InsightResult(
                insight_id=f"full_text_trend_{now.strftime('%Y%m%d_%H%M%S')}_001",
                title=f"基于{total_feedback}条反馈的全局用户体验趋势分析",
                description=f"""## 📈 全局趋势分析

通过对全部**{total_feedback}条反馈**的深度全文分析，发现用户对产品的整体满意度呈现出复杂的多层次特征：

### ✅ 正面反馈特征
- **功能实用性**: 用户普遍认可产品的核心价值
- **界面设计**: 美观性获得用户好评
- **核心优势**: 产品在关键功能上表现突出

### ⚠️ 改进空间
- **性能优化**: 需要持续提升系统响应速度
- **稳定性保障**: 减少异常和崩溃情况
- **体验细节**: 优化用户交互流程

### 📊 关键发现
通过跨时间、跨类别的综合分析，用户期望正在不断提升，产品需要在保持现有优势的同时，**重点解决影响用户留存的关键痛点**。""",
                insight_type="trend",
                confidence_score=0.95,
                impact_level="high",
                supporting_evidence=[
                    f"覆盖{total_feedback}条完整反馈的全文语义分析",
                    "跨时间维度的用户情感变化追踪",
                    "多类别问题的关联性深度挖掘",
                    "用户行为模式的隐含需求识别"
                ],
                affected_user_segments=["全体用户", "新用户", "活跃用户", "付费用户"],
                business_impact="全文分析揭示的趋势将直接影响产品战略方向，有助于制定更精准的用户体验优化策略和功能优先级规划。",
                generated_at=now,
                is_full_text=True  # 标记为全文洞察
            ))
            
            # 2. 深层模式识别洞察
            insights.append(InsightResult(
                insight_id=f"full_text_pattern_{now.strftime('%Y%m%d_%H%M%S')}_002",
                title="深层用户行为模式与隐藏需求识别",
                description=f"""## 🔍 深层模式识别

利用**1M上下文**的全文分析能力，识别出传统分析方法难以发现的深层用户行为模式。

### 🔗 问题聚集效应
- **负面连锁反应**: 用户遇到性能问题时，往往同时对界面交互和功能稳定性产生质疑
- **体验放大效应**: 核心问题会引发用户对其他功能的负面预期
- **正向连锁机制**: 核心功能表现良好时，用户对小缺陷的容忍度更高

### 🎯 个性化需求趋势
- **主题定制**: 用户期望更多视觉个性化选项
- **功能配置**: 希望能够根据使用习惯调整功能布局
- **交互方式**: 对多样化操作方式的需求增强

### 📊 关键发现
解决**核心性能问题**将产生正向连锁反应，显著提升整体用户满意度。个性化需求正在成为新的用户期望维度。""",
                insight_type="pattern",
                confidence_score=0.92,
                impact_level="high",
                supporting_evidence=[
                    "问题关联性的深度语义分析",
                    "用户情感传递的心理学模式识别",
                    "跨功能模块的用户体验关联分析",
                    "个性化需求的潜在信号检测"
                ],
                affected_user_segments=["性能敏感用户", "个性化需求用户", "深度体验用户"],
                business_impact="深层模式识别有助于优化产品架构设计，通过解决核心问题实现用户体验的系统性提升，同时为个性化功能开发提供精准指导。",
                generated_at=now,
                is_full_text=True  # 标记为全文洞察
            ))
            
            # 3. 战略机会洞察
            insights.append(InsightResult(
                insight_id=f"full_text_opportunity_{now.strftime('%Y%m%d_%H%M%S')}_003",
                title="基于全文分析的产品创新与差异化机会识别",
                description=f"""## 🚀 战略机会识别

全文深度分析揭示了**三个重要的战略机会**，为产品未来发展提供了明确的方向。

### 🤖 智能化体验需求
- **隐性需求**: 用户未直接表达，但从反馈中可推断出智能化趋势
- **关键指标**: 搜索精准度、个性化推荐、自动化功能的用户期望
- **技术机会**: AI驱动的智能化产品体验

### 🔗 生态整合期望
- **连接需求**: 用户希望产品能与其他工具和平台无缝连接
- **集成价值**: 提升工作效率和数据流转的便利性
- **竞争优势**: 打造产品生态系统护城河

### 💝 情感化设计机会
- **体验升级**: 用户不仅关注功能实现，更重视情感体验
- **品牌认同**: 情感化设计成为新的差异化竞争点
- **用户忠诚**: 通过情感连接提升用户粘性

### 🎯 战略价值
这些机会有助于在竞争激烈的市场中建立**独特的竞争优势**，推动产品向更高价值层次发展。""",
                insight_type="opportunity",
                confidence_score=0.88,
                impact_level="medium",
                supporting_evidence=[
                    "用户需求的前瞻性语义挖掘",
                    "竞争对手产品对比的用户期望分析",
                    "新兴技术趋势的用户接受度评估",
                    "情感化表达的深度内容分析"
                ],
                affected_user_segments=["创新早期采用者", "技术敏感用户", "品牌忠诚用户"],
                business_impact="战略机会的识别将为产品路线图规划提供重要输入，有助于提前布局未来趋势，在市场竞争中获得先发优势。",
                generated_at=now,
                is_full_text=True  # 标记为全文洞察
            ))
            
            # 4. 风险预警洞察
            insights.append(InsightResult(
                insight_id=f"full_text_risk_{now.strftime('%Y%m%d_%H%M%S')}_004",
                title="全文分析揭示的潜在风险与用户流失预警",
                description=f"""## ⚠️ 风险预警分析

通过对**{total_feedback}条反馈**的深度全文分析，识别出几个重要的风险信号。

### 🔻 用户容忍度下降
- **性能问题**: 用户对性能问题的容忍度正在快速下降
- **替代方案**: 部分用户已开始主动寻找替代产品
- **临界点**: 正在接近用户流失的临界阈值

### 📢 口碑传播风险
- **稳定性问题**: 正在影响产品的口碑传播
- **负面扩散**: 可能导致负面评价的病毒式扩散
- **品牌损害**: 口碑危机可能长期影响品牌形象

### 👥 新用户流失风险
- **学习成本**: 新用户的学习成本过高
- **首次体验**: 不佳的初次使用体验导致早期流失
- **转化率**: 新用户转化率可能持续下降

### 📊 深层风险分析
- **期望差距**: 用户期望与产品现状之间的差距正在扩大
- **流失模式**: 不同用户群体的流失模式存在差异
- **挽留策略**: 需要采取差异化的用户挽留策略

> **风险等级**: 🔴 **高风险** - 如不及时响应，可能面临用户大规模流失的风险""",
                insight_type="risk",
                confidence_score=0.94,
                impact_level="high",
                supporting_evidence=[
                    "用户流失意向的早期信号检测",
                    "负面情绪传播路径的深度分析",
                    "竞品转换意愿的语义识别",
                    "用户期望变化趋势的预测分析"
                ],
                affected_user_segments=["潜在流失用户", "新用户", "价格敏感用户", "竞品关注用户"],
                business_impact="风险预警为用户挽留和体验优化提供了重要参考，有助于制定精准的风险缓解策略，减少用户流失，保护用户生命周期价值。",
                generated_at=now,
                is_full_text=True  # 标记为全文洞察
            ))
            
            # 5. 用户生命周期洞察
            insights.append(InsightResult(
                insight_id=f"full_text_lifecycle_{now.strftime('%Y%m%d_%H%M%S')}_005",
                title="用户生命周期各阶段的深度行为分析",
                description=f"""## 👥 用户生命周期洞察

基于**{total_feedback}条历史反馈**的纵向分析，揭示用户在不同生命周期阶段的行为特征和需求变化。

### 🌱 新用户阶段（0-30天）
- **关注重点**: 主要关注功能易用性和学习曲线
- **反馈特征**: 操作指导、界面理解、功能发现等问题占比较高
- **流失风险**: 首次使用体验不佳是主要流失原因

### 🚀 活跃用户阶段（30-180天）
- **关注重点**: 功能深度和个性化需求
- **反馈特征**: 高级功能使用、效率优化、个性化设置等需求
- **价值驱动**: 开始产生真正的产品价值认知

### 🏆 忠诚用户阶段（180天+）
- **关注重点**: 产品战略和创新功能
- **反馈特征**: 建设性建议、功能扩展、集成需求等
- **品牌价值**: 成为产品的推荐者和布道者

### 📊 关键洞察
不同生命周期阶段的用户需求差异显著，需要**分层运营策略**来提升各阶段的用户体验和转化率。""",
                insight_type="pattern",
                confidence_score=0.89,
                impact_level="high",
                supporting_evidence=[
                    "用户反馈的时间序列分析",
                    "不同使用时长用户的反馈模式差异",
                    "用户生命周期价值变化趋势",
                    "各阶段用户的留存率分析"
                ],
                affected_user_segments=["新用户", "活跃用户", "忠诚用户"],
                business_impact="分层运营策略将显著提升用户留存率，优化用户生命周期价值，降低获客成本。",
                generated_at=now,
                is_full_text=True  # 标记为全文洞察
            ))
            
            # 6. 竞争优势洞察
            insights.append(InsightResult(
                insight_id=f"full_text_competitive_{now.strftime('%Y%m%d_%H%M%S')}_006",
                title="基于用户反馈的竞争优势与市场定位分析",
                description=f"""## 🏁 竞争优势分析

通过对用户反馈中的**竞品对比**和**功能期望**进行深度分析，识别产品的竞争优势和市场定位。

### ✅ 核心竞争优势
- **技术稳定性**: 用户认可产品的技术架构和稳定性
- **界面设计**: 在同类产品中具有明显的设计优势
- **用户体验**: 整体用户体验获得较高评价

### 📈 潜在优势领域
- **个性化功能**: 用户对个性化需求的反馈较多，存在差异化机会
- **性能优化**: 在性能方面有超越竞品的潜力
- **生态整合**: 可以通过生态整合建立竞争壁垒

### 🎯 市场定位建议
- **目标用户**: 专注于**效率驱动型用户**和**品质敏感用户**
- **价值主张**: 强调"稳定、美观、高效"的产品特性
- **差异化策略**: 在个性化和智能化方面建立竞争优势

### 🔍 竞争情报
基于用户反馈分析，竞品在**功能丰富度**方面有一定优势，但在**用户体验**和**稳定性**方面存在明显短板。""",
                insight_type="opportunity",
                confidence_score=0.87,
                impact_level="medium",
                supporting_evidence=[
                    "用户反馈中的竞品对比内容",
                    "功能期望与竞品功能的差异分析",
                    "用户转换意愿的语义分析",
                    "品牌认知度的间接指标分析"
                ],
                affected_user_segments=["潜在用户", "竞品用户", "品牌忠诚用户"],
                business_impact="明确的竞争优势认知将指导产品战略和营销策略，提升市场竞争力。",
                generated_at=now,
                is_full_text=True  # 标记为全文洞察
            ))
            
            # 7. 技术债务洞察
            insights.append(InsightResult(
                insight_id=f"full_text_technical_debt_{now.strftime('%Y%m%d_%H%M%S')}_007",
                title="用户反馈揭示的技术债务与系统优化机会",
                description=f"""## 🔧 技术债务分析

从用户反馈中识别出的**技术债务**和**系统优化**机会，为技术团队提供数据驱动的决策支持。

### 🚨 高优先级技术债务
- **性能瓶颈**: 用户反馈中频繁提及的响应速度问题
- **兼容性问题**: 不同设备和浏览器的兼容性反馈
- **稳定性隐患**: 偶发性崩溃和错误的用户报告

### 📊 系统优化机会
- **缓存策略**: 通过优化缓存提升用户体验
- **数据库性能**: 查询优化可以显著改善响应时间
- **前端优化**: 资源加载和渲染优化机会

### 🎯 技术投资建议
- **立即处理**: 影响用户核心体验的稳定性问题
- **中期规划**: 性能优化和架构升级
- **长期投资**: 技术栈现代化和可扩展性提升

### 💡 用户价值影响
技术债务的及时处理将直接提升用户满意度，减少用户流失，为业务增长提供技术保障。""",
                insight_type="risk",
                confidence_score=0.91,
                impact_level="high",
                supporting_evidence=[
                    "性能相关用户反馈的技术分析",
                    "错误和崩溃报告的模式识别",
                    "用户设备和环境的兼容性分析",
                    "技术问题对用户满意度的影响评估"
                ],
                affected_user_segments=["所有用户", "技术敏感用户", "企业用户"],
                business_impact="技术债务的解决将显著提升产品稳定性和用户体验，降低技术风险。",
                generated_at=now,
                is_full_text=True  # 标记为全文洞察
            ))
            
            # 构建执行摘要
            executive_summary = {
                "key_findings": [
                    f"全文分析覆盖{total_feedback}条反馈，识别出7个高价值洞察维度",
                    "用户体验问题具有明显的关联性和放大效应",
                    "个性化和智能化需求正在成为新的用户期望",
                    "产品稳定性是当前最关键的风险因素",
                    "用户生命周期各阶段的需求差异显著",
                    "技术债务对用户体验的影响日益显著",
                    "产品在稳定性和设计方面具有竞争优势"
                ],
                "top_priorities": [
                    "立即解决影响用户留存的性能和稳定性问题",
                    "建立用户体验的系统性优化机制",
                    "布局智能化和个性化功能开发",
                    "强化新用户引导和教育体系",
                    "建立分层运营策略，提升各阶段用户体验",
                    "制定技术债务清理计划，提升系统稳定性"
                ],
                "strategic_recommendations": [
                    "采用全链路性能监控，建立用户体验实时反馈机制",
                    "实施差异化的用户体验策略，满足不同群体的个性化需求",
                    "投资前瞻性技术研发，提前布局智能化产品功能",
                    "建立用户社区和反馈闭环，提升用户参与度和忠诚度",
                    "强化竞争优势领域，在稳定性和用户体验方面建立护城河",
                    "实施分层运营策略，优化用户生命周期价值管理",
                    "建立技术债务管理机制，持续优化系统性能"
                ],
                "risk_alerts": [
                    "用户流失风险正在加剧，需要立即采取挽留措施",
                    "性能问题可能引发口碑危机，影响品牌形象",
                    "竞品压力增大，用户选择权增加，忠诚度面临挑战",
                    "新用户转化率下降，获客成本可能上升",
                    "技术债务积累可能导致系统性风险",
                    "用户期望与产品现状的差距正在扩大"
                ]
            }
            
            logger.info(f"模拟全文洞察分析完成，生成{len(insights)}个深度洞察")
            return {"insights": insights, "executive_summary": executive_summary}
            
        except Exception as e:
            logger.error(f"模拟全文洞察生成失败: {e}")
            return {"insights": [], "executive_summary": {}}
    
    def _analyze_feedback_data(self, feedback_data: List[Dict]) -> Dict:
        """分析反馈数据"""
        analysis = {
            "total_feedback": len(feedback_data),
            "sentiment_distribution": {},
            "category_distribution": {},
            "priority_distribution": {"high": 0, "medium": 0, "low": 0},
            "key_issues": [],
            "keywords": []
        }
        
        for feedback in feedback_data:
            filter_result = feedback.get("filter_result", {})
            
            # 情感分析
            sentiment = filter_result.get("sentiment", "neutral")
            analysis["sentiment_distribution"][sentiment] = analysis["sentiment_distribution"].get(sentiment, 0) + 1
            
            # 类别分析
            category = filter_result.get("category", "general")
            analysis["category_distribution"][category] = analysis["category_distribution"].get(category, 0) + 1
            
            # 优先级分析
            priority_score = filter_result.get("priority_score", 0.5)
            if priority_score >= 0.7:
                analysis["priority_distribution"]["high"] += 1
            elif priority_score >= 0.5:
                analysis["priority_distribution"]["medium"] += 1
            else:
                analysis["priority_distribution"]["low"] += 1
            
            # 关键词收集
            keywords = filter_result.get("extracted_keywords", [])
            analysis["keywords"].extend(keywords)
        
        # 识别关键问题
        if analysis["keywords"]:
            keyword_counts = Counter(analysis["keywords"])
            analysis["key_issues"] = [f"{word}({count}次)" for word, count in keyword_counts.most_common(5)]
        
        return analysis
    
    def _generate_mock_insights(self, analysis: Dict) -> List[InsightResult]:
        """生成模拟洞察"""
        insights = []
        now = datetime.now()
        total_feedback = analysis["total_feedback"]
        
        # 根据数据量动态生成洞察，不再设置硬编码的限制条件
        logger.info(f"基于{total_feedback}条反馈数据生成洞察")
        
        # 1. 情感分析洞察 - 降低阈值，只要有负面反馈就生成
        negative_ratio = analysis["sentiment_distribution"].get("negative", 0) / total_feedback
        if negative_ratio > 0.1:  # 降低阈值从30%到10%
            insights.append(InsightResult(
                insight_id=f"insight_{now.strftime('%Y%m%d_%H%M%S')}_sentiment",
                title="用户负面反馈需要关注",
                description=f"当前负面反馈占比{negative_ratio:.1%}，主要问题集中在{', '.join(analysis['key_issues'][:3])}。虽然比例不算太高，但仍需要持续关注用户体验，防止问题积累扩大。",
                insight_type="risk",
                confidence_score=0.75 if negative_ratio > 0.3 else 0.65,
                impact_level="high" if negative_ratio > 0.3 else "medium",
                supporting_evidence=[
                    f"负面反馈占比{negative_ratio:.1%}",
                    f"高优先级问题{analysis['priority_distribution']['high']}个",
                    f"关键问题：{', '.join(analysis['key_issues'][:3])}"
                ],
                affected_user_segments=["活跃用户", "新用户"],
                business_impact="需要关注用户体验，防止负面情绪扩散影响产品口碑",
                generated_at=now
            ))
        
        # 2. 积极反馈洞察 - 降低阈值
        positive_ratio = analysis["sentiment_distribution"].get("positive", 0) / total_feedback
        if positive_ratio > 0.1:  # 降低阈值从20%到10%
            insights.append(InsightResult(
                insight_id=f"insight_{now.strftime('%Y%m%d_%H%M%S')}_opportunity",
                title="用户积极反馈显示产品优势",
                description=f"正面反馈占比{positive_ratio:.1%}，说明产品在某些方面获得了用户认可。可以深入分析这些积极反馈，找出产品的优势功能和特色，进一步强化和推广。",
                insight_type="opportunity",
                confidence_score=0.7 if positive_ratio > 0.3 else 0.6,
                impact_level="medium" if positive_ratio > 0.3 else "low",
                supporting_evidence=[
                    f"正面反馈占比{positive_ratio:.1%}",
                    "用户对产品某些功能表示满意",
                    "存在可以放大的产品优势"
                ],
                affected_user_segments=["满意用户", "忠实用户"],
                business_impact="可以通过强化优势功能提升用户满意度，形成口碑传播",
                generated_at=now
            ))
        
        # 3. 类别分析洞察 - 为每个主要类别生成洞察
        sorted_categories = sorted(analysis["category_distribution"].items(), key=lambda x: x[1], reverse=True)
        for i, (category_name, count) in enumerate(sorted_categories[:3]):  # 取前3个主要类别
            if count >= 1:  # 降低阈值从2到1
                category_map = {
                    "performance": "性能",
                    "ui_ux": "界面设计",
                    "feature": "功能需求",
                    "stability": "稳定性",
                    "functionality": "功能性",
                    "general": "通用"
                }
                
                category_display = category_map.get(category_name, category_name)
                insights.append(InsightResult(
                    insight_id=f"insight_{now.strftime('%Y%m%d_%H%M%S')}_category_{i}",
                    title=f"{category_display}问题反馈分析",
                    description=f"用户反馈中{category_display}相关问题有{count}条，占比{count/total_feedback:.1%}。这是用户关注的{'重点' if count >= 5 else '主要'}领域，需要{'优先' if count >= 5 else '持续'}关注和改进。",
                    insight_type="pattern",
                    confidence_score=0.8 if count >= 5 else 0.65,
                    impact_level="high" if count >= 8 else "medium" if count >= 3 else "low",
                    supporting_evidence=[
                        f"{category_display}相关反馈{count}条",
                        f"占总反馈比例{count/total_feedback:.1%}",
                        f"在所有类别中排名第{i+1}位"
                    ],
                    affected_user_segments=["活跃用户", "核心用户"],
                    business_impact=f"影响{category_display}相关的用户体验，需要持续改进",
                    generated_at=now
                ))
        
        # 4. 优先级分析洞察 - 为每个优先级生成洞察
        high_priority_count = analysis["priority_distribution"]["high"]
        medium_priority_count = analysis["priority_distribution"]["medium"]
        low_priority_count = analysis["priority_distribution"]["low"]
        
        if high_priority_count > 0:
            insights.append(InsightResult(
                insight_id=f"insight_{now.strftime('%Y%m%d_%H%M%S')}_priority_high",
                title="高优先级问题需要紧急处理",
                description=f"发现{high_priority_count}个高优先级问题，这些问题通常涉及核心功能故障或严重的用户体验问题。建议立即组织专项小组进行处理，避免问题扩大影响。",
                insight_type="risk",
                confidence_score=0.9,
                impact_level="high",
                supporting_evidence=[
                    f"高优先级问题{high_priority_count}个",
                    f"中优先级问题{medium_priority_count}个",
                    "问题紧急程度评分较高"
                ],
                affected_user_segments=["所有用户"],
                business_impact="高优先级问题可能导致用户无法正常使用核心功能，影响业务运营",
                generated_at=now
            ))
        
        if medium_priority_count > 0:
            insights.append(InsightResult(
                insight_id=f"insight_{now.strftime('%Y%m%d_%H%M%S')}_priority_medium",
                title="中优先级问题需要规划处理",
                description=f"发现{medium_priority_count}个中优先级问题，这些问题虽然不是紧急的，但会影响用户体验。建议制定改进计划，在接下来的版本中逐步解决。",
                insight_type="pattern",
                confidence_score=0.75,
                impact_level="medium",
                supporting_evidence=[
                    f"中优先级问题{medium_priority_count}个",
                    f"占总反馈比例{medium_priority_count/total_feedback:.1%}",
                    "问题影响用户体验但不紧急"
                ],
                affected_user_segments=["活跃用户"],
                business_impact="中优先级问题会逐步影响用户满意度，需要计划性解决",
                generated_at=now
            ))
        
        # 5. 数据量趋势洞察 - 基于反馈数据量生成洞察
        if total_feedback >= 100:
            insights.append(InsightResult(
                insight_id=f"insight_{now.strftime('%Y%m%d_%H%M%S')}_volume_trend",
                title="用户反馈数据量丰富，洞察价值高",
                description=f"本次分析包含{total_feedback}条用户反馈，数据量充足，能够提供可靠的洞察分析。这表明用户对产品的参与度较高，反馈积极性强，是产品改进的宝贵资源。",
                insight_type="trend",
                confidence_score=0.8,
                impact_level="medium",
                supporting_evidence=[
                    f"总反馈数量{total_feedback}条",
                    "数据覆盖面广，代表性强",
                    "用户参与度高"
                ],
                affected_user_segments=["所有用户"],
                business_impact="丰富的用户反馈为产品优化提供了强有力的数据支撑",
                generated_at=now
            ))
        
        # 6. 关键词频次洞察 - 基于高频关键词生成洞察
        if analysis["key_issues"]:
            top_keywords = analysis["key_issues"][:5]
            insights.append(InsightResult(
                insight_id=f"insight_{now.strftime('%Y%m%d_%H%M%S')}_keywords",
                title="关键问题词频分析显示用户关注焦点",
                description=f"通过词频分析发现用户最关注的问题是：{', '.join(top_keywords)}。这些高频关键词反映了用户的核心痛点和关注重点，应该优先解决。",
                insight_type="pattern",
                confidence_score=0.85,
                impact_level="high" if len(top_keywords) >= 3 else "medium",
                supporting_evidence=[
                    f"高频关键词：{', '.join(top_keywords)}",
                    "词频分析显示用户关注集中度",
                    "反映用户核心痛点"
                ],
                affected_user_segments=["活跃用户", "反馈用户"],
                business_impact="关键词分析帮助识别用户最关心的问题，指导产品改进方向",
                generated_at=now
            ))
        
        # 7. 中性反馈洞察 - 分析中性反馈的价值
        neutral_ratio = analysis["sentiment_distribution"].get("neutral", 0) / total_feedback
        if neutral_ratio > 0.3:
            insights.append(InsightResult(
                insight_id=f"insight_{now.strftime('%Y%m%d_%H%M%S')}_neutral",
                title="中性反馈比例较高，需要深入挖掘用户需求",
                description=f"中性反馈占比{neutral_ratio:.1%}，这类反馈往往包含用户的建议和改进意见。虽然不是强烈的正面或负面情绪，但可能蕴含重要的产品优化机会。",
                insight_type="opportunity",
                confidence_score=0.6,
                impact_level="medium",
                supporting_evidence=[
                    f"中性反馈占比{neutral_ratio:.1%}",
                    "包含用户建议和改进意见",
                    "潜在的产品优化机会"
                ],
                affected_user_segments=["理性用户", "专业用户"],
                business_impact="中性反馈可能包含有价值的改进建议，需要深入分析",
                generated_at=now
            ))
        
        logger.info(f"成功生成{len(insights)}个洞察")
        return insights
    
    def _generate_mock_action_plans(self, insights: List[InsightResult], context: Dict) -> List[ActionPlan]:
        """生成模拟执行计划"""
        action_plans = []
        now = datetime.now()
        
        for i, insight in enumerate(insights):
            # 根据洞察类型生成不同的执行计划
            if insight.insight_type == "risk":
                if "负面反馈" in insight.title or "优先级问题" in insight.title:
                    action_plans.append(ActionPlan(
                        plan_id=f"plan_{now.strftime('%Y%m%d_%H%M%S')}_{i}",
                        title="用户体验问题紧急修复计划",
                        summary="针对用户反馈的负面问题，制定紧急修复和改进计划，快速提升用户满意度",
                        priority="P0" if insight.impact_level == "high" else "P1",
                        estimated_effort="2-3周",
                        timeline="立即启动，2周内完成主要修复",
                        owner_team="engineering",
                        success_metrics=[
                            "负面反馈减少30%",
                            "用户满意度提升15%",
                            "关键问题解决率达到90%"
                        ],
                        action_steps=[
                            {"step": 1, "description": "问题分析和优先级排序", "owner": "产品经理", "duration": "2天"},
                            {"step": 2, "description": "技术方案设计", "owner": "技术负责人", "duration": "3天"},
                            {"step": 3, "description": "开发实现", "owner": "开发团队", "duration": "1-2周"},
                            {"step": 4, "description": "测试验证", "owner": "测试团队", "duration": "3天"},
                            {"step": 5, "description": "上线发布", "owner": "运维团队", "duration": "1天"}
                        ],
                        risk_assessment="技术实现复杂度可能影响进度，需要预留缓冲时间",
                        expected_outcome="显著改善用户体验，减少用户投诉，提升产品口碑",
                        related_insights=[insight.insight_id],
                        generated_at=now
                    ))
                    
            elif insight.insight_type == "pattern":
                if "性能" in insight.title:
                    action_plans.append(ActionPlan(
                        plan_id=f"plan_{now.strftime('%Y%m%d_%H%M%S')}_{i}",
                        title="系统性能优化专项计划",
                        summary="针对性能问题集中反馈，制定系统性的性能优化方案，提升系统响应速度和稳定性",
                        priority="P1",
                        estimated_effort="3-4周",
                        timeline="1周内启动，1个月内完成",
                        owner_team="engineering",
                        success_metrics=[
                            "页面加载时间减少50%",
                            "系统响应时间<2秒",
                            "性能相关投诉减少80%"
                        ],
                        action_steps=[
                            {"step": 1, "description": "性能基准测试", "owner": "性能工程师", "duration": "3天"},
                            {"step": 2, "description": "瓶颈分析", "owner": "架构师", "duration": "5天"},
                            {"step": 3, "description": "优化方案制定", "owner": "技术团队", "duration": "2天"},
                            {"step": 4, "description": "代码优化实施", "owner": "开发团队", "duration": "2-3周"},
                            {"step": 5, "description": "性能监控部署", "owner": "运维团队", "duration": "3天"}
                        ],
                        risk_assessment="优化可能影响系统稳定性，需要充分测试",
                        expected_outcome="系统性能显著提升，用户体验改善，技术债务减少",
                        related_insights=[insight.insight_id],
                        generated_at=now
                    ))
                elif "界面" in insight.title:
                    action_plans.append(ActionPlan(
                        plan_id=f"plan_{now.strftime('%Y%m%d_%H%M%S')}_{i}",
                        title="用户界面优化改进计划",
                        summary="基于用户反馈优化界面设计，提升用户交互体验和界面易用性",
                        priority="P2",
                        estimated_effort="2-3周",
                        timeline="2周内启动，3周内完成",
                        owner_team="design",
                        success_metrics=[
                            "界面满意度提升25%",
                            "用户操作成功率提升20%",
                            "界面相关投诉减少60%"
                        ],
                        action_steps=[
                            {"step": 1, "description": "用户体验调研", "owner": "UX设计师", "duration": "1周"},
                            {"step": 2, "description": "界面重设计", "owner": "UI设计师", "duration": "1周"},
                            {"step": 3, "description": "原型测试", "owner": "产品经理", "duration": "3天"},
                            {"step": 4, "description": "前端开发", "owner": "前端工程师", "duration": "1周"},
                            {"step": 5, "description": "用户测试", "owner": "测试团队", "duration": "2天"}
                        ],
                        risk_assessment="设计变更可能需要用户适应期，需要逐步推出",
                        expected_outcome="界面更加友好易用，用户操作效率提升，整体体验改善",
                        related_insights=[insight.insight_id],
                        generated_at=now
                    ))
                        
            elif insight.insight_type == "opportunity":
                action_plans.append(ActionPlan(
                    plan_id=f"plan_{now.strftime('%Y%m%d_%H%M%S')}_{i}",
                    title="优势功能强化推广计划",
                    summary="基于用户积极反馈，识别并强化产品优势功能，制定推广策略",
                    priority="P2",
                    estimated_effort="3-4周",
                    timeline="2周内启动，1个月内完成",
                    owner_team="product",
                    success_metrics=[
                        "优势功能使用率提升30%",
                        "用户推荐率增加20%",
                        "正面反馈增加40%"
                    ],
                    action_steps=[
                        {"step": 1, "description": "优势功能深度分析", "owner": "数据分析师", "duration": "1周"},
                        {"step": 2, "description": "功能增强设计", "owner": "产品经理", "duration": "1周"},
                        {"step": 3, "description": "推广策略制定", "owner": "市场经理", "duration": "3天"},
                        {"step": 4, "description": "功能优化实施", "owner": "开发团队", "duration": "2周"},
                        {"step": 5, "description": "推广活动执行", "owner": "运营团队", "duration": "持续进行"}
                    ],
                    risk_assessment="过度推广可能导致其他功能被忽视，需要平衡发展",
                    expected_outcome="优势功能得到更好利用，用户满意度和忠诚度提升",
                    related_insights=[insight.insight_id],
                    generated_at=now
                ))
        
        return action_plans

# 全局实例
mock_llm_insight_generator = None

def get_mock_llm_insight_generator(config: Dict) -> MockLLMInsightGenerator:
    """获取模拟LLM洞察生成器实例"""
    global mock_llm_insight_generator
    
    if mock_llm_insight_generator is None:
        mock_llm_insight_generator = MockLLMInsightGenerator(config)
    
    return mock_llm_insight_generator 