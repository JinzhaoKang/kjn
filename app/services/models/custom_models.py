"""
自定义模型管理器
负责训练、保存和加载业务特定的机器学习模型
"""
import os
import logging
import joblib
import asyncio
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime
from dataclasses import dataclass

# 机器学习库
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline

from .model_config import ModelConfig

logger = logging.getLogger(__name__)

@dataclass
class TrainingResult:
    """训练结果"""
    model_name: str
    success: bool
    accuracy: float
    training_samples: int
    training_time: float
    model_path: str
    error_message: str = ""

class CustomModelManager:
    """自定义模型管理器"""
    
    def __init__(self, model_dir: str):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = ModelConfig()
        self.loaded_models = {}
        self.training_history = {}
    
    async def load_all_models(self) -> Dict[str, bool]:
        """加载所有自定义模型"""
        results = {}
        
        for model_name in self.config.CUSTOM_MODELS.keys():
            try:
                model = await self.load_model(model_name)
                results[model_name] = model is not None
                
                if model:
                    logger.info(f"✅ 自定义模型 {model_name} 加载成功")
                else:
                    logger.warning(f"⚠️ 自定义模型 {model_name} 未找到，需要训练")
                    
            except Exception as e:
                logger.error(f"❌ {model_name} 加载失败: {e}")
                results[model_name] = False
        
        return results
    
    async def load_model(self, model_name: str) -> Optional[Any]:
        """加载指定的自定义模型"""
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        model_path = self.model_dir / f"{model_name}.joblib"
        
        if not model_path.exists():
            logger.info(f"模型文件不存在: {model_path}")
            return None
        
        try:
            # 在线程池中加载模型，避免阻塞
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(None, joblib.load, str(model_path))
            
            self.loaded_models[model_name] = model
            logger.info(f"成功加载自定义模型: {model_name}")
            
            return model
            
        except Exception as e:
            logger.error(f"加载模型失败 {model_name}: {e}")
            return None
    
    async def train_model(self, model_name: str, training_data: Dict) -> TrainingResult:
        """训练自定义模型"""
        start_time = datetime.now()
        
        try:
            # 验证训练数据
            if not self._validate_training_data(training_data):
                return TrainingResult(
                    model_name=model_name,
                    success=False,
                    accuracy=0.0,
                    training_samples=0,
                    training_time=0.0,
                    model_path="",
                    error_message="训练数据验证失败"
                )
            
            # 根据模型类型选择训练方法
            if model_name == "priority_classifier":
                result = await self._train_priority_classifier(training_data)
            elif model_name == "category_classifier":
                result = await self._train_category_classifier(training_data)
            elif model_name == "tfidf_vectorizer":
                result = await self._train_tfidf_vectorizer(training_data)
            elif model_name == "keyword_extractor":
                result = await self._train_keyword_extractor(training_data)
            else:
                raise ValueError(f"未知的模型类型: {model_name}")
            
            # 计算训练时间
            training_time = (datetime.now() - start_time).total_seconds()
            result.training_time = training_time
            
            # 保存模型
            if result.success:
                model_path = await self._save_model(model_name, result)
                result.model_path = str(model_path)
                
                # 更新训练历史
                self._update_training_history(model_name, result)
            
            return result
            
        except Exception as e:
            logger.error(f"训练模型 {model_name} 失败: {e}")
            return TrainingResult(
                model_name=model_name,
                success=False,
                accuracy=0.0,
                training_samples=0,
                training_time=(datetime.now() - start_time).total_seconds(),
                model_path="",
                error_message=str(e)
            )
    
    def _validate_training_data(self, training_data: Dict) -> bool:
        """验证训练数据"""
        required_fields = ['texts', 'labels']
        
        for field in required_fields:
            if field not in training_data:
                logger.error(f"训练数据缺少必需字段: {field}")
                return False
        
        texts = training_data['texts']
        labels = training_data['labels']
        
        if len(texts) != len(labels):
            logger.error("文本和标签数量不匹配")
            return False
        
        min_samples = self.config.TRAINING_CONFIG['min_training_samples']
        if len(texts) < min_samples:
            logger.error(f"训练样本不足，需要至少 {min_samples} 个样本，当前 {len(texts)} 个")
            return False
        
        return True
    
    async def _train_priority_classifier(self, training_data: Dict) -> TrainingResult:
        """训练优先级分类器"""
        texts = training_data['texts']
        priorities = training_data['labels']  # 优先级标签：high, medium, low
        
        # 文本预处理和特征提取
        vectorizer = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1, 2))
        X = vectorizer.fit_transform(texts)
        y = np.array(priorities)
        
        # 分割训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=self.config.TRAINING_CONFIG['test_split_ratio'],
            random_state=self.config.TRAINING_CONFIG['random_seed'],
            stratify=y
        )
        
        # 训练随机森林分类器
        classifier = RandomForestClassifier(
            n_estimators=100,
            random_state=self.config.TRAINING_CONFIG['random_seed']
        )
        
        # 在线程池中训练
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, classifier.fit, X_train, y_train)
        
        # 评估模型
        y_pred = classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # 保存模型和向量化器
        model_pipeline = Pipeline([
            ('vectorizer', vectorizer),
            ('classifier', classifier)
        ])
        
        self.loaded_models["priority_classifier"] = model_pipeline
        
        return TrainingResult(
            model_name="priority_classifier",
            success=True,
            accuracy=accuracy,
            training_samples=len(texts),
            training_time=0.0,  # 稍后设置
            model_path=""  # 稍后设置
        )
    
    async def _train_category_classifier(self, training_data: Dict) -> TrainingResult:
        """训练类别分类器"""
        texts = training_data['texts']
        categories = training_data['labels']  # 类别标签：bug, feature, performance等
        
        # 文本预处理和特征提取
        vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2))
        X = vectorizer.fit_transform(texts)
        y = np.array(categories)
        
        # 分割数据
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=self.config.TRAINING_CONFIG['test_split_ratio'],
            random_state=self.config.TRAINING_CONFIG['random_seed'],
            stratify=y
        )
        
        # 训练朴素贝叶斯分类器
        classifier = MultinomialNB(alpha=1.0)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, classifier.fit, X_train, y_train)
        
        # 评估
        y_pred = classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # 创建管道
        model_pipeline = Pipeline([
            ('vectorizer', vectorizer),
            ('classifier', classifier)
        ])
        
        self.loaded_models["category_classifier"] = model_pipeline
        
        return TrainingResult(
            model_name="category_classifier",
            success=True,
            accuracy=accuracy,
            training_samples=len(texts),
            training_time=0.0,
            model_path=""
        )
    
    async def _train_tfidf_vectorizer(self, training_data: Dict) -> TrainingResult:
        """训练TF-IDF向量化器"""
        texts = training_data['texts']
        
        # 训练TF-IDF向量化器
        vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=(1, 3),
            min_df=2,
            max_df=0.8
        )
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, vectorizer.fit, texts)
        
        self.loaded_models["tfidf_vectorizer"] = vectorizer
        
        return TrainingResult(
            model_name="tfidf_vectorizer",
            success=True,
            accuracy=1.0,  # 向量化器没有准确率概念
            training_samples=len(texts),
            training_time=0.0,
            model_path=""
        )
    
    async def _train_keyword_extractor(self, training_data: Dict) -> TrainingResult:
        """训练关键词提取器"""
        # 这里可以实现更复杂的关键词提取逻辑
        # 暂时使用简单的统计方法
        texts = training_data['texts']
        
        # 关键词提取器（基于TF-IDF的关键词提取）
        vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, vectorizer.fit, texts)
        
        self.loaded_models["keyword_extractor"] = vectorizer
        
        return TrainingResult(
            model_name="keyword_extractor",
            success=True,
            accuracy=1.0,
            training_samples=len(texts),
            training_time=0.0,
            model_path=""
        )
    
    async def _save_model(self, model_name: str, result: TrainingResult) -> Path:
        """保存训练好的模型"""
        model_path = self.model_dir / f"{model_name}.joblib"
        
        # 备份旧模型
        if model_path.exists() and self.config.TRAINING_CONFIG['backup_old_models']:
            backup_path = self.model_dir / f"{model_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
            model_path.rename(backup_path)
        
        # 保存新模型
        model = self.loaded_models[model_name]
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, joblib.dump, model, str(model_path))
        
        logger.info(f"模型已保存: {model_path}")
        return model_path
    
    def _update_training_history(self, model_name: str, result: TrainingResult):
        """更新训练历史"""
        if model_name not in self.training_history:
            self.training_history[model_name] = []
        
        self.training_history[model_name].append({
            "timestamp": datetime.now(),
            "accuracy": result.accuracy,
            "training_samples": result.training_samples,
            "training_time": result.training_time,
            "success": result.success
        })
        
        # 只保留最近10次训练记录
        self.training_history[model_name] = self.training_history[model_name][-10:]
    
    async def retrain_model(self, model_name: str) -> bool:
        """重新训练模型（使用历史数据）"""
        # 这里需要从数据库获取历史训练数据
        # 暂时返回False，表示需要提供新的训练数据
        logger.warning(f"重新训练 {model_name} 需要提供训练数据")
        return False
    
    def get_model_info(self) -> Dict:
        """获取自定义模型信息"""
        info = {
            "total_models": len(self.config.CUSTOM_MODELS),
            "loaded_models": len(self.loaded_models),
            "model_dir": str(self.model_dir),
            "models": {},
            "training_history": self.training_history
        }
        
        for name, model_info in self.config.CUSTOM_MODELS.items():
            model_path = self.model_dir / f"{name}.joblib"
            
            info["models"][name] = {
                "name": model_info.name,
                "type": model_info.model_type,
                "size_mb": model_info.size_mb,
                "description": model_info.description,
                "required": model_info.required,
                "loaded": name in self.loaded_models,
                "exists": model_path.exists(),
                "last_modified": model_path.stat().st_mtime if model_path.exists() else None
            }
        
        return info
    
    async def generate_sample_training_data(self) -> Dict:
        """生成示例训练数据（用于测试）"""
        sample_data = {
            "priority_classifier": {
                "texts": [
                    "应用经常崩溃，无法正常使用",
                    "建议增加夜间模式",
                    "界面很好看，体验不错",
                    "登录时偶尔会卡住",
                    "希望能支持多语言",
                    "严重bug，数据丢失",
                    "功能很实用，继续保持",
                    "加载速度有点慢",
                    "界面可以更简洁一些",
                    "crash频繁发生"
                ],
                "labels": [
                    "high", "medium", "low", "medium", "medium",
                    "high", "low", "medium", "low", "high"
                ]
            },
            "category_classifier": {
                "texts": [
                    "应用经常崩溃，无法正常使用",
                    "建议增加夜间模式",
                    "界面很好看，体验不错",
                    "登录时偶尔会卡住",
                    "希望能支持多语言",
                    "严重bug，数据丢失",
                    "功能很实用，继续保持",
                    "加载速度有点慢",
                    "界面可以更简洁一些"
                ],
                "labels": [
                    "bug", "feature", "ui_ux", "bug", "feature",
                    "bug", "general", "performance", "ui_ux"
                ]
            }
        }
        
        return sample_data

# 训练示例函数
async def train_all_models_with_sample_data():
    """使用示例数据训练所有模型"""
    manager = CustomModelManager("./model_cache/custom")
    
    # 生成示例数据
    sample_data = await manager.generate_sample_training_data()
    
    results = {}
    
    # 训练各个模型
    for model_name, training_data in sample_data.items():
        logger.info(f"开始训练 {model_name}...")
        result = await manager.train_model(model_name, training_data)
        results[model_name] = result
        
        if result.success:
            logger.info(f"✅ {model_name} 训练成功，准确率: {result.accuracy:.3f}")
        else:
            logger.error(f"❌ {model_name} 训练失败: {result.error_message}")
    
    return results 