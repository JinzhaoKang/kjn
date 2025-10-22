"""
洞察生成服务模块
"""
from .llm_insight_generator import LLMInsightGenerator, get_llm_insight_generator, InsightResult, ActionPlan
from .mock_llm_insight_generator import MockLLMInsightGenerator, get_mock_llm_insight_generator

__all__ = [
    'LLMInsightGenerator',
    'get_llm_insight_generator', 
    'InsightResult',
    'ActionPlan',
    'MockLLMInsightGenerator',
    'get_mock_llm_insight_generator'
] 