"""
核心配置模块
包含所有环境变量和应用配置
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = "用户反馈分析系统"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 数据库配置
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "feedback_analysis"
    
    # Redis配置（用于Celery和缓存）
    redis_url: str = "redis://localhost:6379/0"
    
    # LLM API配置
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    
    google_api_key: Optional[str] = None
    google_model: str = "gemini-pro"
    
    # 数据源API配置
    app_store_api_key: Optional[str] = None
    google_play_api_key: Optional[str] = None
    zendesk_api_key: Optional[str] = None
    zendesk_subdomain: Optional[str] = None
    
    # 分析引擎配置
    max_feedback_length: int = 2000  # 最大反馈文本长度
    batch_size: int = 50  # 批处理大小
    sentiment_threshold: float = 0.5  # 情感分析阈值
    urgency_threshold: float = 0.7  # 紧急度阈值
    
    # 决策框架配置
    priority_weights: dict = {
        "feedback_count": 0.4,
        "sentiment_score": 0.3,  
        "urgency_score": 0.3
    }
    
    # 聚类分析配置
    min_cluster_size: int = 5  # HDBSCAN最小聚类大小
    min_samples: int = 3  # HDBSCAN最小样本数
    
    # API配置
    api_v1_prefix: str = "/api/v1"
    cors_origins: list = [
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001", 
        "http://127.0.0.1:8080"
    ]
    
    # 安全配置
    secret_key: str = "your-secret-key-here"
    access_token_expire_minutes: int = 30
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings 