"""
聚类分析引擎
负责对用户反馈进行主题聚类，生成问题卡片
"""
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import json

from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
import hdbscan
from collections import Counter, defaultdict

from ...core.config import settings

logger = logging.getLogger(__name__)


class TopicClusteringEngine:
    """主题聚类引擎"""
    
    def __init__(self):
        # 初始化句向量模型
        try:
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("句向量模型初始化成功")
        except Exception as e:
            logger.warning(f"句向量模型初始化失败: {e}")
            self.sentence_model = None
        
        # 初始化TF-IDF向量化器
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        
        # 聚类器
        self.clusterer = hdbscan.HDBSCAN(
            min_cluster_size=settings.min_cluster_size,
            min_samples=settings.min_samples,
            metric='euclidean'
        )
    
    def extract_features(self, feedback_list: List[Dict]) -> Tuple[np.ndarray, List[str]]:
        """提取特征向量"""
        
        texts = []
        summaries = []
        
        for feedback in feedback_list:
            analysis_result = feedback.get('analysis_result', {})
            summary = analysis_result.get('summary', '')
            processed_text = feedback.get('processed_text', '')
            
            text_for_clustering = summary if summary else processed_text
            if text_for_clustering:
                texts.append(text_for_clustering)
                summaries.append(summary)
        
        if not texts:
            return np.array([]), []
        
        # 使用句向量模型
        if self.sentence_model:
            try:
                embeddings = self.sentence_model.encode(texts)
                return embeddings, summaries
            except Exception as e:
                logger.warning(f"句向量生成失败: {e}")
        
        # 回退到TF-IDF
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            return tfidf_matrix.toarray(), summaries
        except Exception as e:
            logger.error(f"特征提取失败: {e}")
            return np.array([]), []
    
    def perform_clustering(self, features: np.ndarray) -> np.ndarray:
        """执行聚类"""
        if features.size == 0:
            return np.array([])
        
        try:
            cluster_labels = self.clusterer.fit_predict(features)
            return cluster_labels
        except Exception as e:
            logger.error(f"聚类失败: {e}")
            return np.array([-1] * len(features))
    
    def calculate_metrics(self, cluster_feedbacks: List[Dict]) -> Dict:
        """计算聚类指标"""
        
        if not cluster_feedbacks:
            return {
                "feedback_count": 0,
                "avg_sentiment_score": 0.0,
                "avg_urgency_score": 0.0,
                "first_seen": datetime.now(),
                "last_seen": datetime.now()
            }
        
        sentiment_scores = []
        urgency_scores = []
        feedback_times = []
        
        for feedback in cluster_feedbacks:
            analysis_result = feedback.get('analysis_result', {})
            sentiment_scores.append(analysis_result.get('sentiment_score', 0.0))
            urgency_scores.append(analysis_result.get('urgency_score', 0.0))
            
            feedback_time = feedback.get('feedback_time', datetime.now())
            if isinstance(feedback_time, str):
                try:
                    feedback_time = datetime.fromisoformat(feedback_time.replace('Z', '+00:00'))
                except:
                    feedback_time = datetime.now()
            feedback_times.append(feedback_time)
        
        return {
            "feedback_count": len(cluster_feedbacks),
            "avg_sentiment_score": np.mean(sentiment_scores) if sentiment_scores else 0.0,
            "avg_urgency_score": np.mean(urgency_scores) if urgency_scores else 0.0,
            "first_seen": min(feedback_times) if feedback_times else datetime.now(),
            "last_seen": max(feedback_times) if feedback_times else datetime.now()
        }
    
    def generate_cluster_theme(self, cluster_feedbacks: List[Dict]) -> str:
        """生成聚类主题"""
        
        all_topics = []
        for feedback in cluster_feedbacks:
            analysis_result = feedback.get('analysis_result', {})
            topics = analysis_result.get('topics', [])
            all_topics.extend(topics)
        
        if all_topics:
            topic_counts = Counter(all_topics)
            most_common_topic = topic_counts.most_common(1)[0][0]
            return most_common_topic
        
        return "用户反馈问题"
    
    def cluster_to_issues(self, feedback_list: List[Dict]) -> List[Dict]:
        """将反馈聚类转换为问题卡片"""
        
        if not feedback_list:
            return []
        
        # 提取特征
        features, summaries = self.extract_features(feedback_list)
        
        if features.size == 0:
            return []
        
        # 执行聚类
        cluster_labels = self.perform_clustering(features)
        
        if len(cluster_labels) == 0:
            return []
        
        # 按聚类分组
        clustered_feedback = defaultdict(list)
        for i, label in enumerate(cluster_labels):
            if i < len(feedback_list):
                clustered_feedback[label].append(feedback_list[i])
        
        # 生成问题卡片
        issue_cards = []
        
        for cluster_id, cluster_feedbacks in clustered_feedback.items():
            if cluster_id == -1 or len(cluster_feedbacks) < settings.min_cluster_size:
                continue
            
            try:
                theme = self.generate_cluster_theme(cluster_feedbacks)
                metrics = self.calculate_metrics(cluster_feedbacks)
                
                issue_card = {
                    "cluster_id": cluster_id,
                    "issue_theme": theme,
                    "issue_summary": f"用户关于{theme}的反馈问题",
                    **metrics,
                    "related_feedback_ids": [fb.get('id') for fb in cluster_feedbacks if fb.get('id')],
                    "created_at": datetime.now()
                }
                
                issue_cards.append(issue_card)
                
            except Exception as e:
                logger.error(f"处理聚类 {cluster_id} 失败: {e}")
                continue
        
        return issue_cards


# 创建全局实例
clustering_engine = TopicClusteringEngine() 