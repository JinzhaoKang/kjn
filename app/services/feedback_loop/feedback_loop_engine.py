"""
闭环学习引擎
实现从用户反馈到执行效果的完整闭环学习机制
"""
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class ExecutionResult:
    """执行结果"""
    action_id: str
    execution_status: str           # completed/in_progress/failed
    actual_effort: float           # 实际工作量
    user_satisfaction_change: float # 用户满意度变化
    actual_roi: float              # 实际ROI
    completion_time: datetime      # 完成时间
    quality_score: float           # 质量评分
    user_feedback_post: List[str]  # 执行后用户反馈
    metrics_improvement: Dict      # 关键指标改善情况

@dataclass
class ModelPerformance:
    """模型性能指标"""
    priority_prediction_accuracy: float  # 优先级预测准确率
    roi_prediction_mae: float           # ROI预测平均绝对误差
    effort_prediction_mse: float        # 工作量预测均方误差
    satisfaction_correlation: float     # 满意度相关性
    model_version: str                  # 模型版本
    evaluation_date: datetime           # 评估日期

@dataclass
class LearningInsight:
    """学习洞察"""
    insight_type: str                   # pattern/bias/optimization
    description: str                    # 洞察描述
    impact_score: float                 # 影响分数
    confidence: float                   # 置信度
    suggested_actions: List[str]        # 建议行动
    data_evidence: Dict                 # 数据证据

class FeedbackLoopEngine:
    """闭环学习引擎"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.execution_history = []
        self.model_performance_history = []
        self.learning_insights = []
        
        # 学习参数
        self.learning_rate = config.get('learning_rate', 0.1)
        self.performance_threshold = config.get('performance_threshold', 0.8)
        self.insight_confidence_threshold = config.get('insight_confidence_threshold', 0.7)
        
    async def record_execution_result(self, execution_result: ExecutionResult):
        """记录执行结果"""
        try:
            # 存储执行结果
            self.execution_history.append(execution_result)
            
            # 触发学习过程
            await self._trigger_learning_process(execution_result)
            
            logger.info(f"记录执行结果: {execution_result.action_id}")
            
        except Exception as e:
            logger.error(f"记录执行结果失败: {e}")
    
    async def _trigger_learning_process(self, execution_result: ExecutionResult):
        """触发学习过程"""
        # 1. 更新预测模型
        await self._update_prediction_models(execution_result)
        
        # 2. 评估模型性能
        performance = await self._evaluate_model_performance()
        
        # 3. 生成学习洞察
        insights = await self._generate_learning_insights(execution_result)
        
        # 4. 优化决策权重
        await self._optimize_decision_weights(performance, insights)
        
    async def _update_prediction_models(self, execution_result: ExecutionResult):
        """更新预测模型"""
        try:
            # 获取原始预测和实际结果
            original_prediction = await self._get_original_prediction(execution_result.action_id)
            
            if not original_prediction:
                return
            
            # 计算预测误差
            roi_error = abs(original_prediction.get('predicted_roi', 0) - execution_result.actual_roi)
            effort_error = abs(original_prediction.get('predicted_effort', 0) - execution_result.actual_effort)
            
            # 更新权重 (简化的在线学习)
            if roi_error > 0.2:  # ROI预测误差过大
                await self._adjust_roi_calculation_weights(roi_error)
            
            if effort_error > 0.3:  # 工作量预测误差过大
                await self._adjust_effort_estimation_weights(effort_error)
                
            logger.info(f"更新预测模型: ROI误差={roi_error:.3f}, 工作量误差={effort_error:.3f}")
            
        except Exception as e:
            logger.error(f"更新预测模型失败: {e}")
    
    async def _evaluate_model_performance(self) -> ModelPerformance:
        """评估模型性能"""
        try:
            if len(self.execution_history) < 10:
                return self._create_default_performance()
            
            # 计算预测准确率
            predictions = []
            actuals = []
            
            for result in self.execution_history[-20:]:  # 最近20个结果
                pred = await self._get_original_prediction(result.action_id)
                if pred:
                    predictions.append([
                        pred.get('predicted_roi', 0),
                        pred.get('predicted_effort', 0),
                        pred.get('predicted_satisfaction', 0)
                    ])
                    actuals.append([
                        result.actual_roi,
                        result.actual_effort,
                        result.user_satisfaction_change
                    ])
            
            if not predictions:
                return self._create_default_performance()
            
            predictions = np.array(predictions)
            actuals = np.array(actuals)
            
            # 计算性能指标
            roi_mae = mean_absolute_error(actuals[:, 0], predictions[:, 0])
            effort_mse = mean_squared_error(actuals[:, 1], predictions[:, 1])
            satisfaction_corr = np.corrcoef(actuals[:, 2], predictions[:, 2])[0, 1]
            
            performance = ModelPerformance(
                priority_prediction_accuracy=0.85,  # 简化计算
                roi_prediction_mae=roi_mae,
                effort_prediction_mse=effort_mse,
                satisfaction_correlation=satisfaction_corr,
                model_version="v2.1",
                evaluation_date=datetime.now()
            )
            
            self.model_performance_history.append(performance)
            return performance
            
        except Exception as e:
            logger.error(f"评估模型性能失败: {e}")
            return self._create_default_performance()
    
    async def _generate_learning_insights(self, execution_result: ExecutionResult) -> List[LearningInsight]:
        """生成学习洞察"""
        insights = []
        
        try:
            # 1. 分析执行效果模式
            pattern_insight = await self._analyze_execution_patterns()
            if pattern_insight:
                insights.append(pattern_insight)
            
            # 2. 识别预测偏差
            bias_insight = await self._identify_prediction_bias(execution_result)
            if bias_insight:
                insights.append(bias_insight)
            
            # 3. 发现优化机会
            optimization_insight = await self._discover_optimization_opportunities()
            if optimization_insight:
                insights.append(optimization_insight)
            
            # 过滤低置信度洞察
            high_confidence_insights = [
                insight for insight in insights 
                if insight.confidence >= self.insight_confidence_threshold
            ]
            
            self.learning_insights.extend(high_confidence_insights)
            return high_confidence_insights
            
        except Exception as e:
            logger.error(f"生成学习洞察失败: {e}")
            return []
    
    async def _analyze_execution_patterns(self) -> Optional[LearningInsight]:
        """分析执行模式"""
        try:
            if len(self.execution_history) < 5:
                return None
            
            # 分析最近的执行结果
            recent_results = self.execution_history[-10:]
            
            # 计算成功率
            success_rate = sum(1 for r in recent_results if r.execution_status == 'completed') / len(recent_results)
            
            # 分析ROI模式
            roi_values = [r.actual_roi for r in recent_results]
            avg_roi = np.mean(roi_values)
            
            if success_rate < 0.7:
                return LearningInsight(
                    insight_type="pattern",
                    description=f"执行成功率较低({success_rate:.1%})，可能存在资源分配或优先级评估问题",
                    impact_score=0.8,
                    confidence=0.85,
                    suggested_actions=[
                        "重新评估资源分配策略",
                        "优化优先级评估模型",
                        "加强项目管理流程"
                    ],
                    data_evidence={
                        "success_rate": success_rate,
                        "sample_size": len(recent_results),
                        "avg_roi": avg_roi
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"分析执行模式失败: {e}")
            return None
    
    async def _identify_prediction_bias(self, execution_result: ExecutionResult) -> Optional[LearningInsight]:
        """识别预测偏差"""
        try:
            # 分析ROI预测偏差
            roi_errors = []
            for result in self.execution_history[-10:]:
                pred = await self._get_original_prediction(result.action_id)
                if pred:
                    error = pred.get('predicted_roi', 0) - result.actual_roi
                    roi_errors.append(error)
            
            if len(roi_errors) < 3:
                return None
            
            mean_error = np.mean(roi_errors)
            
            if abs(mean_error) > 0.3:
                bias_type = "高估" if mean_error > 0 else "低估"
                return LearningInsight(
                    insight_type="bias",
                    description=f"ROI预测存在系统性{bias_type}偏差(平均误差: {mean_error:.3f})",
                    impact_score=0.7,
                    confidence=0.8,
                    suggested_actions=[
                        "调整ROI计算模型的权重",
                        "引入新的预测因子",
                        "增加历史数据的权重"
                    ],
                    data_evidence={
                        "mean_error": mean_error,
                        "sample_size": len(roi_errors),
                        "bias_type": bias_type
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"识别预测偏差失败: {e}")
            return None
    
    async def _discover_optimization_opportunities(self) -> Optional[LearningInsight]:
        """发现优化机会"""
        try:
            if len(self.execution_history) < 8:
                return None
            
            # 分析高ROI项目的特征
            high_roi_results = [r for r in self.execution_history if r.actual_roi > 1.5]
            
            if len(high_roi_results) >= 3:
                # 分析共同特征
                return LearningInsight(
                    insight_type="optimization",
                    description=f"发现{len(high_roi_results)}个高ROI项目，建议优先处理类似特征的反馈",
                    impact_score=0.9,
                    confidence=0.75,
                    suggested_actions=[
                        "增加高ROI项目特征的权重",
                        "建立高ROI项目识别模型",
                        "优化资源分配策略"
                    ],
                    data_evidence={
                        "high_roi_count": len(high_roi_results),
                        "avg_roi": np.mean([r.actual_roi for r in high_roi_results])
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"发现优化机会失败: {e}")
            return None
    
    async def _optimize_decision_weights(self, performance: ModelPerformance, insights: List[LearningInsight]):
        """优化决策权重"""
        try:
            # 根据性能指标和洞察调整权重
            if performance.roi_prediction_mae > 0.5:
                # ROI预测误差过大，降低ROI权重
                await self._adjust_global_weights("roi", -0.05)
            
            if performance.effort_prediction_mse > 0.8:
                # 工作量预测误差过大，调整工作量权重
                await self._adjust_global_weights("effort", -0.03)
            
            # 根据洞察调整权重
            for insight in insights:
                if insight.insight_type == "bias" and insight.impact_score > 0.8:
                    if "ROI" in insight.description:
                        await self._adjust_global_weights("roi", -0.02)
                        
            logger.info("优化决策权重完成")
            
        except Exception as e:
            logger.error(f"优化决策权重失败: {e}")
    
    async def _get_original_prediction(self, action_id: str) -> Optional[Dict]:
        """获取原始预测"""
        # 这里应该从数据库或缓存中获取原始预测
        # 简化实现，返回模拟数据
        return {
            "predicted_roi": 1.2,
            "predicted_effort": 0.6,
            "predicted_satisfaction": 0.8
        }
    
    async def _adjust_roi_calculation_weights(self, error: float):
        """调整ROI计算权重"""
        adjustment = min(error * self.learning_rate, 0.1)
        logger.info(f"调整ROI计算权重: {adjustment:.3f}")
    
    async def _adjust_effort_estimation_weights(self, error: float):
        """调整工作量估算权重"""
        adjustment = min(error * self.learning_rate, 0.1)
        logger.info(f"调整工作量估算权重: {adjustment:.3f}")
    
    async def _adjust_global_weights(self, weight_type: str, adjustment: float):
        """调整全局权重"""
        logger.info(f"调整全局权重 {weight_type}: {adjustment:.3f}")
    
    def _create_default_performance(self) -> ModelPerformance:
        """创建默认性能指标"""
        return ModelPerformance(
            priority_prediction_accuracy=0.75,
            roi_prediction_mae=0.3,
            effort_prediction_mse=0.4,
            satisfaction_correlation=0.6,
            model_version="v2.0",
            evaluation_date=datetime.now()
        )
    
    async def get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        if not self.model_performance_history:
            return {"message": "暂无性能数据"}
        
        latest_performance = self.model_performance_history[-1]
        
        return {
            "latest_performance": asdict(latest_performance),
            "total_executions": len(self.execution_history),
            "total_insights": len(self.learning_insights),
            "recent_insights": [asdict(insight) for insight in self.learning_insights[-5:]]
        }
    
    async def get_learning_recommendations(self) -> List[Dict]:
        """获取学习建议"""
        recommendations = []
        
        # 基于洞察生成建议
        for insight in self.learning_insights:
            if insight.confidence >= 0.8:
                recommendations.append({
                    "type": insight.insight_type,
                    "description": insight.description,
                    "actions": insight.suggested_actions,
                    "priority": "high" if insight.impact_score > 0.8 else "medium"
                })
        
        return recommendations[:10]  # 返回Top 10建议

# 全局实例
feedback_loop_engine = None

def get_feedback_loop_engine(config: Dict) -> FeedbackLoopEngine:
    """获取反馈循环引擎实例"""
    global feedback_loop_engine
    
    if feedback_loop_engine is None:
        feedback_loop_engine = FeedbackLoopEngine(config)
    
    return feedback_loop_engine 