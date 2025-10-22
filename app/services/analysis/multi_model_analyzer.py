"""
多模型分析器
整合多个分析引擎的结果，提供更准确的分析
"""
import asyncio
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from .llm_analyzer import AnalysisEngine, AnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class MultiModelResult:
    """多模型分析结果"""
    consensus_result: AnalysisResult
    individual_results: Dict[str, AnalysisResult]
    confidence_score: float
    agreement_score: float


class MultiModelAnalyzer:
    """多模型分析器"""
    
    def __init__(self):
        self.analysis_engine = AnalysisEngine()
        self._initialized = False
    
    async def initialize(self):
        """初始化分析器"""
        if not self._initialized:
            await self.analysis_engine.initialize()
            self._initialized = True
    
    async def analyze_with_consensus(self, feedback_text: str) -> MultiModelResult:
        """使用多个模型进行分析并生成共识结果"""
        await self.initialize()
        
        if not self.analysis_engine.analyzers:
            raise RuntimeError("没有可用的分析器，请在前端设置页面配置LLM API Key")
        
        # 如果只有一个分析器，直接使用它
        if len(self.analysis_engine.analyzers) == 1:
            analyzer_name = list(self.analysis_engine.analyzers.keys())[0]
            analyzer = self.analysis_engine.analyzers[analyzer_name]
            result = await analyzer.analyze_feedback(feedback_text)
            
            return MultiModelResult(
                consensus_result=result,
                individual_results={analyzer_name: result},
                confidence_score=result.confidence,
                agreement_score=1.0
            )
        
        # 多个分析器的情况
        tasks = []
        analyzer_names = []
        
        for name, analyzer in self.analysis_engine.analyzers.items():
            tasks.append(analyzer.analyze_feedback(feedback_text))
            analyzer_names.append(name)
        
        # 并行执行分析
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        valid_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"分析器{analyzer_names[i]}分析失败: {result}")
            else:
                valid_results[analyzer_names[i]] = result
        
        if not valid_results:
            raise RuntimeError("所有分析器都失败了")
        
        # 生成共识结果
        consensus_result = self._generate_consensus(valid_results)
        agreement_score = self._calculate_agreement(valid_results)
        confidence_score = self._calculate_overall_confidence(valid_results, agreement_score)
        
        return MultiModelResult(
            consensus_result=consensus_result,
            individual_results=valid_results,
            confidence_score=confidence_score,
            agreement_score=agreement_score
        )
    
    def _generate_consensus(self, results: Dict[str, AnalysisResult]) -> AnalysisResult:
        """生成共识结果"""
        if len(results) == 1:
            return list(results.values())[0]
        
        # 情感分析 - 投票决定
        sentiment_votes = {}
        sentiment_scores = []
        
        for result in results.values():
            sentiment_votes[result.sentiment] = sentiment_votes.get(result.sentiment, 0) + 1
            sentiment_scores.append(result.sentiment_score)
        
        consensus_sentiment = max(sentiment_votes, key=sentiment_votes.get)
        consensus_sentiment_score = sum(sentiment_scores) / len(sentiment_scores)
        
        # 意图分析 - 投票决定
        intent_votes = {}
        for result in results.values():
            intent_votes[result.intent] = intent_votes.get(result.intent, 0) + 1
        
        consensus_intent = max(intent_votes, key=intent_votes.get)
        
        # 主题 - 合并所有主题，取出现频率高的
        all_topics = []
        for result in results.values():
            all_topics.extend(result.topics)
        
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # 取出现次数大于等于一半的主题
        threshold = len(results) / 2
        consensus_topics = [topic for topic, count in topic_counts.items() if count >= threshold]
        
        # 紧急度 - 平均值
        urgency_scores = [result.urgency_score for result in results.values()]
        consensus_urgency = sum(urgency_scores) / len(urgency_scores)
        
        # 摘要 - 取置信度最高的结果的摘要
        best_result = max(results.values(), key=lambda x: x.confidence)
        consensus_summary = best_result.summary
        
        # 置信度 - 平均值
        confidences = [result.confidence for result in results.values()]
        consensus_confidence = sum(confidences) / len(confidences)
        
        return AnalysisResult(
            sentiment=consensus_sentiment,
            sentiment_score=consensus_sentiment_score,
            intent=consensus_intent,
            topics=consensus_topics,
            urgency_score=consensus_urgency,
            summary=consensus_summary,
            confidence=consensus_confidence
        )
    
    def _calculate_agreement(self, results: Dict[str, AnalysisResult]) -> float:
        """计算多个结果之间的一致性"""
        if len(results) <= 1:
            return 1.0
        
        result_list = list(results.values())
        agreement_scores = []
        
        # 情感一致性
        sentiments = [r.sentiment for r in result_list]
        sentiment_agreement = len(set(sentiments)) == 1
        agreement_scores.append(1.0 if sentiment_agreement else 0.5)
        
        # 意图一致性
        intents = [r.intent for r in result_list]
        intent_agreement = len(set(intents)) == 1
        agreement_scores.append(1.0 if intent_agreement else 0.5)
        
        # 情感分数差异
        sentiment_scores = [r.sentiment_score for r in result_list]
        if len(sentiment_scores) > 1:
            score_variance = sum((s - sum(sentiment_scores)/len(sentiment_scores))**2 for s in sentiment_scores) / len(sentiment_scores)
            score_agreement = max(0, 1.0 - score_variance)
            agreement_scores.append(score_agreement)
        
        return sum(agreement_scores) / len(agreement_scores)
    
    def _calculate_overall_confidence(self, results: Dict[str, AnalysisResult], agreement_score: float) -> float:
        """计算整体置信度"""
        individual_confidences = [r.confidence for r in results.values()]
        avg_confidence = sum(individual_confidences) / len(individual_confidences)
        
        # 置信度受一致性影响
        return avg_confidence * (0.5 + 0.5 * agreement_score)
    
    async def analyze_feedback(self, feedback_text: str, model_id: Optional[str] = None) -> Dict:
        """分析反馈文本，返回标准化结果字典格式"""
        try:
            # 使用指定模型或默认模型进行分析
            result = await self.analysis_engine.analyze_single_feedback(feedback_text)
            
            # 转换为期望的字典格式
            return {
                "success": True,
                "sentiment": self._map_sentiment(result.sentiment),
                "category": self._map_category(result.intent),
                "keywords": result.topics,
                "priority": self._map_priority(result.urgency_score),
                "confidence": result.confidence,
                "summary": result.summary,
                "suggestions": [],  # 可以后续扩展
                "model_used": model_id or "default",
                "processing_time": 0.0,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"多模型分析失败: {e}")
            # 返回降级结果
            return {
                "success": False,
                "sentiment": "neutral",
                "category": "unknown",
                "keywords": [],
                "priority": "medium",
                "confidence": 0.0,
                "summary": "分析失败",
                "suggestions": [],
                "model_used": "fallback",
                "processing_time": 0.0,
                "error": str(e)
            }
    
    def _map_sentiment(self, sentiment: str) -> str:
        """映射情感标签"""
        sentiment_map = {
            "Positive": "positive",
            "Negative": "negative", 
            "Neutral": "neutral"
        }
        return sentiment_map.get(sentiment, "neutral")
    
    def _map_category(self, intent: str) -> str:
        """映射分类标签"""
        category_map = {
            "Bug Report": "bug_report",
            "Feature Request": "feature_request",
            "Question": "question",
            "UX Complaint": "ux_complaint",
            "Praise": "praise"
        }
        return category_map.get(intent, "general")
    
    def _map_priority(self, urgency_score: float) -> str:
        """映射优先级"""
        if urgency_score >= 0.7:
            return "high"
        elif urgency_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    async def analyze_batch_with_consensus(self, feedback_list: List[str]) -> List[MultiModelResult]:
        """批量分析并生成共识结果"""
        await self.initialize()
        
        tasks = [self.analyze_with_consensus(feedback) for feedback in feedback_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"批量分析中第{i+1}条反馈失败: {result}")
                # 创建默认结果
                default_result = AnalysisResult(
                    sentiment="Neutral",
                    sentiment_score=0.0,
                    intent="Question",
                    topics=[],
                    urgency_score=0.0,
                    summary="批量分析失败",
                    confidence=0.0
                )
                processed_results.append(MultiModelResult(
                    consensus_result=default_result,
                    individual_results={},
                    confidence_score=0.0,
                    agreement_score=0.0
                ))
            else:
                processed_results.append(result)
        
        return processed_results


# 创建全局多模型分析器实例
multi_model_analyzer = MultiModelAnalyzer() 