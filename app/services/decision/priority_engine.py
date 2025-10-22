"""
优先级排序引擎
负责对产品问题进行优先级计算、排序和决策支持
"""
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

from ...core.config import settings

logger = logging.getLogger(__name__)


class PriorityEngine:
    """优先级计算引擎"""
    
    def __init__(self):
        self.priority_weights = settings.priority_weights
        
        # 预定义的影响等级映射
        self.impact_mapping = {
            "Low": 1.0,
            "Medium": 2.0, 
            "High": 3.0
        }
        
        # 预定义的复杂度惩罚
        self.complexity_penalty = {
            "Low": 1.0,
            "Medium": 0.8,
            "High": 0.6
        }
    
    def calculate_base_priority_score(self, issue: Dict) -> float:
        """计算基础优先级得分"""
        
        feedback_count = issue.get("feedback_count", 0)
        avg_sentiment_score = issue.get("avg_sentiment_score", 0.0)
        avg_urgency_score = issue.get("avg_urgency_score", 0.0)
        
        # 基础公式：Priority = log(feedback_count) * w1 + |sentiment_score| * w2 + urgency_score * w3
        feedback_score = math.log(max(feedback_count, 1)) * self.priority_weights.get("feedback_count", 0.4)
        sentiment_score = abs(avg_sentiment_score) * self.priority_weights.get("sentiment_score", 0.3)
        urgency_score = avg_urgency_score * self.priority_weights.get("urgency_score", 0.3)
        
        base_score = feedback_score + sentiment_score + urgency_score
        
        logger.debug(f"基础得分计算: feedback={feedback_score:.2f}, sentiment={sentiment_score:.2f}, urgency={urgency_score:.2f}")
        
        return base_score
    
    def apply_time_decay(self, issue: Dict, base_score: float) -> float:
        """应用时间衰减"""
        
        last_seen = issue.get("last_seen")
        if not last_seen:
            return base_score
        
        if isinstance(last_seen, str):
            try:
                last_seen = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
            except:
                return base_score
        
        # 计算天数差
        days_since_last = (datetime.now() - last_seen).days
        
        # 时间衰减函数：score * exp(-days/30)
        # 30天后衰减到原来的1/e ≈ 37%
        time_factor = math.exp(-days_since_last / 30.0)
        
        adjusted_score = base_score * time_factor
        
        logger.debug(f"时间衰减: {days_since_last}天前, 衰减因子={time_factor:.3f}")
        
        return adjusted_score
    
    def apply_business_impact(self, issue: Dict, score: float) -> float:
        """应用业务影响调整"""
        
        business_impact = issue.get("business_impact", "Medium")
        impact_multiplier = self.impact_mapping.get(business_impact, 2.0)
        
        adjusted_score = score * impact_multiplier
        
        logger.debug(f"业务影响调整: {business_impact}, 乘数={impact_multiplier}")
        
        return adjusted_score
    
    def apply_complexity_penalty(self, issue: Dict, score: float) -> float:
        """应用技术复杂度惩罚"""
        
        technical_complexity = issue.get("technical_complexity", "Medium")
        complexity_factor = self.complexity_penalty.get(technical_complexity, 0.8)
        
        adjusted_score = score * complexity_factor
        
        logger.debug(f"复杂度惩罚: {technical_complexity}, 因子={complexity_factor}")
        
        return adjusted_score
    
    def calculate_comprehensive_priority(self, issue: Dict) -> float:
        """计算综合优先级得分"""
        
        # 1. 计算基础得分
        base_score = self.calculate_base_priority_score(issue)
        
        # 2. 应用时间衰减
        time_adjusted_score = self.apply_time_decay(issue, base_score)
        
        # 3. 应用业务影响
        business_adjusted_score = self.apply_business_impact(issue, time_adjusted_score)
        
        # 4. 应用复杂度惩罚
        final_score = self.apply_complexity_penalty(issue, business_adjusted_score)
        
        # 5. 确保得分在合理范围内
        final_score = max(0.0, min(100.0, final_score))
        
        logger.info(f"问题 '{issue.get('issue_theme', 'Unknown')}' 优先级得分: {final_score:.2f}")
        
        return final_score
    
    def categorize_priority(self, score: float) -> str:
        """根据得分分类优先级"""
        
        if score >= 8.0:
            return "Critical"
        elif score >= 6.0:
            return "High"
        elif score >= 4.0:
            return "Medium"
        elif score >= 2.0:
            return "Low"
        else:
            return "Minimal"
    
    def estimate_effort(self, issue: Dict) -> str:
        """估算工作量"""
        
        feedback_count = issue.get("feedback_count", 0)
        technical_complexity = issue.get("technical_complexity", "Medium")
        
        # 简单的工作量估算逻辑
        if technical_complexity == "High":
            return "High"
        elif technical_complexity == "Low" and feedback_count < 10:
            return "Low"
        else:
            return "Medium"
    
    def generate_action_recommendation(self, issue: Dict, priority_score: float) -> Dict:
        """生成行动建议"""
        
        priority_category = self.categorize_priority(priority_score)
        estimated_effort = self.estimate_effort(issue)
        
        # 根据优先级和工作量生成建议
        if priority_category in ["Critical", "High"]:
            if estimated_effort == "Low":
                action = "立即处理"
                timeline = "本周内"
            else:
                action = "优先排期"
                timeline = "2周内"
        elif priority_category == "Medium":
            action = "计划处理"
            timeline = "本月内"
        else:
            action = "后续考虑"
            timeline = "下季度"
        
        recommendation = {
            "action": action,
            "timeline": timeline,
            "rationale": self._generate_rationale(issue, priority_score, priority_category),
            "suggested_assignee": self._suggest_assignee(issue),
            "dependencies": self._identify_dependencies(issue)
        }
        
        return recommendation
    
    def _generate_rationale(self, issue: Dict, score: float, category: str) -> str:
        """生成决策理由"""
        
        feedback_count = issue.get("feedback_count", 0)
        avg_sentiment_score = issue.get("avg_sentiment_score", 0.0)
        theme = issue.get("issue_theme", "问题")
        
        rationale_parts = []
        
        if feedback_count > 20:
            rationale_parts.append(f"影响用户数量较多({feedback_count}条反馈)")
        
        if avg_sentiment_score < -0.5:
            rationale_parts.append("用户情感倾向强烈负面")
        
        if category == "Critical":
            rationale_parts.append("属于关键问题，需要紧急处理")
        elif category == "High":
            rationale_parts.append("属于高优先级问题，应优先处理")
        
        if not rationale_parts:
            rationale_parts.append("基于综合评估得出的优先级")
        
        return f"关于{theme}的问题：" + "，".join(rationale_parts) + f"（综合得分: {score:.1f}）"
    
    def _suggest_assignee(self, issue: Dict) -> str:
        """建议责任人"""
        
        theme = issue.get("issue_theme", "").lower()
        
        # 简单的责任人分配逻辑
        if any(keyword in theme for keyword in ["登录", "注册", "账户", "login", "auth"]):
            return "后端团队"
        elif any(keyword in theme for keyword in ["界面", "ui", "ux", "设计", "交互"]):
            return "前端团队"
        elif any(keyword in theme for keyword in ["性能", "速度", "卡顿", "crash"]):
            return "性能优化团队"
        elif any(keyword in theme for keyword in ["支付", "订单", "购买"]):
            return "业务团队"
        else:
            return "产品团队"
    
    def _identify_dependencies(self, issue: Dict) -> List[str]:
        """识别依赖关系"""
        
        theme = issue.get("issue_theme", "").lower()
        dependencies = []
        
        # 简单的依赖识别逻辑
        if any(keyword in theme for keyword in ["支付", "订单"]):
            dependencies.append("第三方支付接口")
        
        if any(keyword in theme for keyword in ["登录", "账户"]):
            dependencies.append("用户认证系统")
        
        if any(keyword in theme for keyword in ["数据", "同步"]):
            dependencies.append("数据库团队")
        
        return dependencies
    
    def sort_issues_by_priority(self, issues: List[Dict]) -> List[Dict]:
        """按优先级排序问题列表"""
        
        if not issues:
            return []
        
        # 为每个问题计算优先级得分
        for issue in issues:
            try:
                priority_score = self.calculate_comprehensive_priority(issue)
                priority_category = self.categorize_priority(priority_score)
                recommendation = self.generate_action_recommendation(issue, priority_score)
                
                # 更新问题数据
                issue["priority_score"] = priority_score
                issue["priority_category"] = priority_category
                issue["estimated_effort"] = self.estimate_effort(issue)
                issue["action_recommendation"] = recommendation
                
            except Exception as e:
                logger.error(f"计算问题优先级失败: {e}")
                # 设置默认值
                issue["priority_score"] = 0.0
                issue["priority_category"] = "Minimal"
                issue["estimated_effort"] = "Medium"
                issue["action_recommendation"] = {
                    "action": "需要进一步分析",
                    "timeline": "待定",
                    "rationale": f"优先级计算失败: {str(e)}",
                    "suggested_assignee": "产品团队",
                    "dependencies": []
                }
        
        # 按优先级得分排序（降序）
        sorted_issues = sorted(issues, key=lambda x: x.get("priority_score", 0.0), reverse=True)
        
        # 添加排名
        for rank, issue in enumerate(sorted_issues, 1):
            issue["priority_rank"] = rank
        
        logger.info(f"完成 {len(sorted_issues)} 个问题的优先级排序")
        
        return sorted_issues
    
    def get_priority_distribution(self, issues: List[Dict]) -> Dict:
        """获取优先级分布统计"""
        
        if not issues:
            return {}
        
        priority_counts = {}
        total_feedback = 0
        
        for issue in issues:
            category = issue.get("priority_category", "Minimal")
            feedback_count = issue.get("feedback_count", 0)
            
            if category not in priority_counts:
                priority_counts[category] = {
                    "count": 0,
                    "total_feedback": 0
                }
            
            priority_counts[category]["count"] += 1
            priority_counts[category]["total_feedback"] += feedback_count
            total_feedback += feedback_count
        
        # 计算百分比
        for category in priority_counts:
            priority_counts[category]["percentage"] = round(
                (priority_counts[category]["count"] / len(issues)) * 100, 1
            )
        
        return {
            "distribution": priority_counts,
            "total_issues": len(issues),
            "total_feedback": total_feedback
        }


# 创建全局优先级引擎实例
priority_engine = PriorityEngine() 