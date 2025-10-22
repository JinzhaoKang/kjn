"""
智能预筛选模块
使用传统机器学习算法对反馈进行初步筛选和分类，减少需要LLM处理的数据量
支持行业配置化的关键词和权重设置
"""
import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import joblib
import numpy as np
import pandas as pd

# 传统ML模型
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# 深度学习模型
import torch
from transformers import (
    AutoTokenizer, AutoModel, 
    AutoModelForSequenceClassification,
    pipeline
)

# 中文处理
import jieba
from textstat import flesch_reading_ease

# 行业配置
from ..config.industry_config import get_industry_config_manager, IndustryConfig

logger = logging.getLogger(__name__)

@dataclass
class FilterResult:
    """预筛选结果"""
    should_process_with_llm: bool
    priority_score: float
    category: str
    sentiment: str
    confidence: float
    reason: str
    extracted_keywords: List[str]

class IntelligentFilter:
    """智能预筛选器"""
    
    def __init__(self):
        self.models = {}
        self.vectorizers = {}
        self.bert_model = None
        self.bert_tokenizer = None
        self.sentiment_pipeline = None
        
        # 获取行业配置管理器
        self.config_manager = get_industry_config_manager()
        
        # 默认权重（如果没有行业配置时使用）
        self.default_weights = {
            "content_quality": 0.25,      # 内容质量
            "sentiment_intensity": 0.20,   # 情感强度
            "business_relevance": 0.20,    # 业务相关性
            "urgency_indicators": 0.15,    # 紧急性指标
            "user_value": 0.10,            # 用户价值
            "novelty": 0.10               # 新颖性
        }
        
        # 默认关键词库（如果没有行业配置时使用）
        self.default_business_keywords = {
            "bug": ["崩溃", "错误", "异常", "故障", "问题", "卡顿", "闪退"],
            "feature": ["功能", "需求", "建议", "希望", "增加", "改进", "优化"],
            "performance": ["慢", "卡", "延迟", "响应", "加载", "速度"],
            "ui_ux": ["界面", "设计", "布局", "颜色", "字体", "操作", "体验"],
            "security": ["安全", "隐私", "权限", "泄露", "保护"],
            "integration": ["集成", "兼容", "同步", "导入", "导出"]
        }
        
        self.default_urgency_keywords = [
            "紧急", "严重", "重要", "关键", "阻塞", "无法使用", 
            "影响工作", "损失", "立即", "马上"
        ]
    
    def _get_current_config(self) -> IndustryConfig:
        """获取当前行业配置"""
        return self.config_manager.get_current_config()
    
    def _get_weights(self) -> Dict[str, float]:
        """获取当前权重配置"""
        config = self._get_current_config()
        return {
            "content_quality": config.weights.content_quality,
            "sentiment_intensity": config.weights.sentiment_intensity,
            "business_relevance": config.weights.business_relevance,
            "urgency_indicators": config.weights.urgency_indicators,
            "user_value": config.weights.user_value,
            "novelty": config.weights.novelty
        }
    
    def _get_business_keywords(self) -> Dict[str, List[str]]:
        """获取当前业务关键词"""
        config = self._get_current_config()
        return {
            "bug": config.keywords.bug_keywords,
            "feature": config.keywords.feature_keywords,
            "performance": config.keywords.performance_keywords,
            "ui_ux": config.keywords.ui_ux_keywords,
            "security": config.keywords.security_keywords,
            "integration": config.keywords.integration_keywords
        }
    
    def _get_urgency_keywords(self) -> List[str]:
        """获取当前紧急性关键词"""
        config = self._get_current_config()
        return config.keywords.urgency_keywords
    
    def _get_positive_keywords(self) -> List[str]:
        """获取正面关键词"""
        config = self._get_current_config()
        return config.keywords.positive_keywords
    
    def _get_negative_keywords(self) -> List[str]:
        """获取负面关键词"""
        config = self._get_current_config()
        return config.keywords.negative_keywords
    
    async def initialize_models(self):
        """初始化所有模型"""
        try:
            await self._load_traditional_models()
            await self._load_bert_models()
            await self._load_sentiment_model()
            logger.info("智能预筛选模型初始化完成")
        except Exception as e:
            logger.error(f"模型初始化失败: {e}")
            raise
    
    async def _load_traditional_models(self):
        """加载传统机器学习模型"""
        # 这里可以加载预训练的模型
        # 实际部署时应该从文件加载
        self.models['priority_classifier'] = RandomForestClassifier(n_estimators=100)
        self.models['category_classifier'] = MultinomialNB()
        self.vectorizers['tfidf'] = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    async def _load_bert_models(self):
        """加载BERT模型用于特征提取"""
        try:
            # 使用中文BERT模型
            model_name = "hfl/chinese-bert-wwm-ext"
            self.bert_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.bert_model = AutoModel.from_pretrained(model_name)
            logger.info("BERT模型加载成功")
        except Exception as e:
            logger.warning(f"BERT模型加载失败，使用传统方法: {e}")
    
    async def _load_sentiment_model(self):
        """加载情感分析模型"""
        try:
            # 使用预训练的中文情感分析模型
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="uer/roberta-base-finetuned-chinanews-chinese",
                tokenizer="uer/roberta-base-finetuned-chinanews-chinese"
            )
            logger.info("情感分析模型加载成功")
        except Exception as e:
            logger.warning(f"情感分析模型加载失败: {e}")
    
    async def filter_feedback(self, feedback_text: str, metadata: Dict = None) -> FilterResult:
        """对单条反馈进行智能筛选"""
        try:
            # 1. 内容质量评估
            quality_score = self._assess_content_quality(feedback_text)
            
            # 2. 情感强度分析
            sentiment_score = await self._analyze_sentiment_intensity(feedback_text)
            
            # 3. 业务相关性评估
            relevance_score = self._assess_business_relevance(feedback_text)
            
            # 4. 紧急性指标检测
            urgency_score = self._detect_urgency_indicators(feedback_text)
            
            # 5. 用户价值评估
            user_value_score = self._assess_user_value(metadata or {})
            
            # 6. 新颖性检测
            novelty_score = await self._detect_novelty(feedback_text)
            
            # 7. 综合优先级计算
            priority_score = self._calculate_priority_score({
                "content_quality": quality_score,
                "sentiment_intensity": sentiment_score,
                "business_relevance": relevance_score,
                "urgency_indicators": urgency_score,
                "user_value": user_value_score,
                "novelty": novelty_score
            })
            
            # 8. 分类预测
            category = self._predict_category(feedback_text)
            
            # 9. 决策是否需要LLM处理
            should_process, reason = self._decide_llm_processing(
                priority_score, quality_score, novelty_score
            )
            
            # 10. 提取关键词
            keywords = self._extract_keywords(feedback_text)
            
            return FilterResult(
                should_process_with_llm=should_process,
                priority_score=priority_score,
                category=category,
                sentiment=self._get_sentiment_label(sentiment_score),
                confidence=min(quality_score + relevance_score, 1.0),
                reason=reason,
                extracted_keywords=keywords
            )
            
        except Exception as e:
            logger.error(f"反馈筛选失败: {e}")
            # 默认处理策略：优先级低，但仍需LLM处理
            return FilterResult(
                should_process_with_llm=True,
                priority_score=0.3,
                category="unknown",
                sentiment="neutral",
                confidence=0.1,
                reason="筛选失败，默认处理",
                extracted_keywords=[]
            )
    
    def _assess_content_quality(self, text: str) -> float:
        """评估内容质量"""
        if not text or len(text.strip()) < 10:
            return 0.1
        
        score = 0.0
        
        # 长度适中性 (50-500字符较好)
        length = len(text)
        if 50 <= length <= 500:
            score += 0.3
        elif 20 <= length < 50 or 500 < length <= 1000:
            score += 0.2
        elif length > 1000:
            score += 0.1
        
        # 包含具体信息
        if any(keyword in text for keyword in ["什么时候", "如何", "为什么", "在哪里"]):
            score += 0.2
        
        # 避免纯情绪表达
        emotion_only_patterns = [
            r'^[很非常太极超]+[好坏差棒糟烂]*[！!]*$',
            r'^[哈呵嘿嘻]+$',
            r'^[。，,！!？?]*$'
        ]
        if not any(re.match(pattern, text.strip()) for pattern in emotion_only_patterns):
            score += 0.2
        
        # 包含具体产品相关词汇
        product_words = ["功能", "界面", "操作", "使用", "体验", "问题", "建议"]
        if any(word in text for word in product_words):
            score += 0.3
        
        return min(score, 1.0)
    
    async def _analyze_sentiment_intensity(self, text: str) -> float:
        """分析情感强度"""
        try:
            if self.sentiment_pipeline:
                result = self.sentiment_pipeline(text)[0]
                # 转换为-1到1的分数
                if result['label'] == 'POSITIVE':
                    return result['score']
                else:
                    return -result['score']
            else:
                # 使用关键词方法
                return self._keyword_based_sentiment(text)
        except Exception:
            return self._keyword_based_sentiment(text)
    
    def _keyword_based_sentiment(self, text: str) -> float:
        """基于关键词的情感分析"""
        # 使用当前行业配置的关键词
        positive_words = self._get_positive_keywords()
        negative_words = self._get_negative_keywords()
        
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        if pos_count + neg_count == 0:
            return 0.0
        
        return (pos_count - neg_count) / (pos_count + neg_count)
    
    def _assess_business_relevance(self, text: str) -> float:
        """评估业务相关性"""
        score = 0.0
        
        # 使用当前行业配置的关键词
        business_keywords = self._get_business_keywords()
        
        for category, keywords in business_keywords.items():
            if any(keyword in text for keyword in keywords):
                score += 0.2
        
        return min(score, 1.0)
    
    def _detect_urgency_indicators(self, text: str) -> float:
        """检测紧急性指标"""
        urgency_score = 0.0
        
        # 使用当前行业配置的紧急性关键词
        urgency_keywords = self._get_urgency_keywords()
        
        # 直接紧急关键词
        for keyword in urgency_keywords:
            if keyword in text:
                urgency_score += 0.3
        
        # 问题严重性描述
        severity_patterns = [
            r'完全无法.*',
            r'一直.*问题',
            r'每次都.*',
            r'根本.*不.*'
        ]
        
        for pattern in severity_patterns:
            if re.search(pattern, text):
                urgency_score += 0.2
        
        return min(urgency_score, 1.0)
    
    def _assess_user_value(self, metadata: Dict) -> float:
        """评估用户价值"""
        score = 0.5  # 默认分数
        
        # VIP用户
        if metadata.get('is_vip', False):
            score += 0.3
        
        # 付费用户
        if metadata.get('is_paid_user', False):
            score += 0.2
        
        # 活跃度
        if metadata.get('activity_level', 'low') == 'high':
            score += 0.2
        
        # 反馈历史
        feedback_count = metadata.get('feedback_count', 0)
        if feedback_count > 10:
            score += 0.1
        elif feedback_count > 5:
            score += 0.05
        
        return min(score, 1.0)
    
    async def _detect_novelty(self, text: str) -> float:
        """检测新颖性（是否是新问题）"""
        # 这里可以实现与历史数据的相似度计算
        # 暂时使用简单的关键词重复度检测
        
        # 使用BERT计算相似度（如果模型可用）
        if self.bert_model:
            try:
                return await self._bert_novelty_detection(text)
            except Exception:
                pass
        
        # 简单的关键词新颖性检测
        return self._keyword_novelty_detection(text)
    
    async def _bert_novelty_detection(self, text: str) -> float:
        """使用BERT检测新颖性"""
        # 这里应该与历史反馈库进行相似度计算
        # 暂时返回默认值
        return 0.7
    
    def _keyword_novelty_detection(self, text: str) -> float:
        """基于关键词的新颖性检测"""
        # 包含具体版本、功能名称等具体信息的视为新颖
        specific_patterns = [
            r'版本\d+',
            r'V\d+\.\d+',
            r'在.*页面',
            r'点击.*按钮'
        ]
        
        for pattern in specific_patterns:
            if re.search(pattern, text):
                return 0.8
        
        return 0.5
    
    def _calculate_priority_score(self, scores: Dict[str, float]) -> float:
        """计算综合优先级分数"""
        total_score = 0.0
        
        # 使用当前行业配置的权重
        weights = self._get_weights()
        
        for dimension, score in scores.items():
            weight = weights.get(dimension, 0.0)
            total_score += score * weight
        
        return min(total_score, 1.0)
    
    def _predict_category(self, text: str) -> str:
        """预测反馈类别"""
        # 使用当前行业配置的关键词进行分类
        business_keywords = self._get_business_keywords()
        
        # 基于关键词的简单分类
        for category, keywords in business_keywords.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return "general"
    
    def _decide_llm_processing(self, priority_score: float, quality_score: float, novelty_score: float) -> Tuple[bool, str]:
        """决策是否需要LLM处理"""
        
        # 高优先级必须处理
        if priority_score >= 0.7:
            return True, "高优先级反馈"
        
        # 高质量且新颖的反馈
        if quality_score >= 0.6 and novelty_score >= 0.6:
            return True, "高质量新颖反馈"
        
        # 质量太低的直接过滤
        if quality_score < 0.3:
            return False, "内容质量过低"
        
        # 中等优先级的随机采样处理
        if 0.4 <= priority_score < 0.7:
            import random
            if random.random() < 0.3:  # 30%概率处理
                return True, "中优先级随机采样"
            else:
                return False, "中优先级未采样"
        
        return False, "优先级过低"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 使用jieba分词
        words = jieba.lcut(text)
        
        # 过滤停用词和短词
        stop_words = {'的', '了', '是', '在', '有', '和', '就', '都', '而', '及'}
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        
        # 返回前10个关键词
        return keywords[:10]
    
    def _get_sentiment_label(self, sentiment_score: float) -> str:
        """获取情感标签"""
        if sentiment_score > 0.3:
            return "positive"
        elif sentiment_score < -0.3:
            return "negative"
        else:
            return "neutral"

    async def batch_filter(self, feedbacks: List[Dict]) -> List[FilterResult]:
        """批量筛选反馈"""
        results = []
        
        for feedback in feedbacks:
            text = feedback.get('text', '')
            metadata = feedback.get('metadata', {})
            
            result = await self.filter_feedback(text, metadata)
            results.append(result)
        
        return results

# 全局实例
intelligent_filter = IntelligentFilter() 