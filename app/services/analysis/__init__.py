"""
AI分析服务模块
提供多种AI分析能力：LLM分析、多模型支持、智能预筛选
"""

from .multi_model_analyzer import MultiModelAnalyzer, multi_model_analyzer
from .llm_analyzer import LLMAnalyzer

# 尝试导入增强LLM分析器（可选）
try:
    from .enhanced_llm_analyzer import EnhancedLLMAnalyzer
    ENHANCED_LLM_AVAILABLE = True
except ImportError:
    EnhancedLLMAnalyzer = None
    ENHANCED_LLM_AVAILABLE = False

__all__ = [
    'MultiModelAnalyzer',
    'multi_model_analyzer',
    'LLMAnalyzer',
    'EnhancedLLMAnalyzer',
    'ENHANCED_LLM_AVAILABLE'
]
