"""
模型配置
定义系统中使用的所有模型类型、来源和参数
"""
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class ModelInfo:
    """模型信息"""
    name: str
    source: str  # huggingface, local, custom
    model_type: str  # transformer, sklearn, pytorch
    size_mb: int
    description: str
    required: bool = True
    gpu_required: bool = False

class ModelConfig:
    """模型配置管理"""
    
    # 预训练模型配置
    PRETRAINED_MODELS = {
        # 句向量模型（用于聚类）
        "sentence_transformer": ModelInfo(
            name="all-MiniLM-L6-v2",
            source="sentence-transformers",
            model_type="transformer",
            size_mb=90,
            description="轻量级句向量模型，用于文本聚类",
            required=True,
            gpu_required=False
        ),
        
        # 中文BERT模型（用于特征提取）
        "chinese_bert": ModelInfo(
            name="hfl/chinese-bert-wwm-ext",
            source="huggingface",
            model_type="transformer",
            size_mb=400,
            description="哈工大中文BERT模型，用于文本理解",
            required=False,  # 可选，有fallback方案
            gpu_required=True
        ),
        
        # 中文情感分析模型
        "chinese_sentiment": ModelInfo(
            name="uer/roberta-base-finetuned-chinanews-chinese",
            source="huggingface",
            model_type="transformer",
            size_mb=400,
            description="中文情感分析模型",
            required=False,  # 可选，有关键词fallback
            gpu_required=True
        ),
        
        # 中文分词模型
        "jieba": ModelInfo(
            name="jieba",
            source="pip",
            model_type="traditional",
            size_mb=5,
            description="中文分词工具",
            required=True,
            gpu_required=False
        )
    }
    
    # 自定义模型配置（需要用业务数据训练）
    CUSTOM_MODELS = {
        # 优先级分类器
        "priority_classifier": ModelInfo(
            name="priority_classifier_v1",
            source="custom",
            model_type="sklearn",
            size_mb=10,
            description="反馈优先级分类器（RandomForest）",
            required=True,
            gpu_required=False
        ),
        
        # 类别分类器
        "category_classifier": ModelInfo(
            name="category_classifier_v1",
            source="custom",
            model_type="sklearn",
            size_mb=5,
            description="反馈类别分类器（MultinomialNB）",
            required=True,
            gpu_required=False
        ),
        
        # TF-IDF向量化器
        "tfidf_vectorizer": ModelInfo(
            name="tfidf_vectorizer_v1",
            source="custom",
            model_type="sklearn",
            size_mb=50,
            description="TF-IDF特征提取器",
            required=True,
            gpu_required=False
        ),
        
        # 业务关键词提取器
        "keyword_extractor": ModelInfo(
            name="keyword_extractor_v1",
            source="custom",
            model_type="sklearn",
            size_mb=20,
            description="业务关键词提取器",
            required=False,
            gpu_required=False
        )
    }
    
    # 模型下载配置
    DOWNLOAD_CONFIG = {
        "cache_dir": "./model_cache",
        "max_retries": 3,
        "timeout_seconds": 300,
        "use_proxy": False,
        "proxy_url": None
    }
    
    # 训练配置
    TRAINING_CONFIG = {
        "min_training_samples": 100,
        "test_split_ratio": 0.2,
        "validation_split_ratio": 0.1,
        "random_seed": 42,
        "save_intermediate": True,
        "backup_old_models": True
    }
    
    # 硬件配置
    HARDWARE_CONFIG = {
        "use_gpu": True,
        "gpu_memory_limit": "4GB",
        "cpu_cores": 4,
        "max_ram_usage": "8GB"
    }
    
    def get_required_models(self) -> Dict[str, ModelInfo]:
        """获取必需的模型列表"""
        required = {}
        
        for name, info in self.PRETRAINED_MODELS.items():
            if info.required:
                required[name] = info
        
        for name, info in self.CUSTOM_MODELS.items():
            if info.required:
                required[name] = info
        
        return required
    
    def get_optional_models(self) -> Dict[str, ModelInfo]:
        """获取可选的模型列表"""
        optional = {}
        
        for name, info in self.PRETRAINED_MODELS.items():
            if not info.required:
                optional[name] = info
        
        for name, info in self.CUSTOM_MODELS.items():
            if not info.required:
                optional[name] = info
        
        return optional
    
    def estimate_total_size(self) -> int:
        """估算所有模型的总大小（MB）"""
        total_size = 0
        
        for info in self.PRETRAINED_MODELS.values():
            total_size += info.size_mb
        
        for info in self.CUSTOM_MODELS.values():
            total_size += info.size_mb
        
        return total_size
    
    def get_gpu_models(self) -> Dict[str, ModelInfo]:
        """获取需要GPU的模型"""
        gpu_models = {}
        
        for name, info in self.PRETRAINED_MODELS.items():
            if info.gpu_required:
                gpu_models[name] = info
        
        for name, info in self.CUSTOM_MODELS.items():
            if info.gpu_required:
                gpu_models[name] = info
        
        return gpu_models 