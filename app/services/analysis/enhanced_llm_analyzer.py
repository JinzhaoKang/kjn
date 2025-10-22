"""
增强的LLM分析器
对预筛选后的高价值反馈进行深度维度挖掘和分析
"""
import json
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio

# LLM客户端
import openai
import google.generativeai as genai

logger = logging.getLogger(__name__)

@dataclass
class DeepAnalysisResult:
    """深度分析结果"""
    # 基础维度
    primary_sentiment: str  # positive/negative/neutral
    sentiment_intensity: float  # 0-1
    urgency_level: str  # critical/high/medium/low
    urgency_score: float  # 0-1
    
    # 需求维度
    requirement_type: str  # functional/non_functional/technical/business
    requirement_category: str  # bug_fix/feature_request/improvement/integration
    requirement_priority: str  # must_have/should_have/could_have/wont_have
    
    # 影响维度
    impact_scope: str  # individual/team/department/company/ecosystem
    impact_frequency: str  # always/often/sometimes/rarely
    user_journey_stage: str  # onboarding/daily_use/advanced_use/migration
    
    # 技术维度  
    technical_complexity: str  # low/medium/high/very_high
    implementation_effort: str  # hours/days/weeks/months
    dependency_level: str  # independent/low_dependency/high_dependency/blocking
    
    # 业务维度
    business_value: str  # revenue/retention/acquisition/efficiency/compliance
    strategic_alignment: str  # core/important/nice_to_have/off_strategy
    competitive_advantage: str  # differentiator/parity/table_stakes/internal
    
    # 用户维度
    user_segment: str  # new_users/power_users/enterprise/mobile/web
    user_pain_level: str  # blocker/major_friction/minor_inconvenience/enhancement
    user_workaround: Optional[str]  # 用户当前的解决方案
    
    # 洞察维度
    root_cause: Optional[str]  # 问题根本原因
    solution_suggestion: Optional[str]  # 建议解决方案
    related_areas: List[str]  # 相关功能区域
    
    # 可执行维度
    action_owner: str  # product/engineering/design/support/marketing
    estimated_timeline: str  # immediate/sprint/quarter/roadmap
    success_metrics: List[str]  # 成功指标
    
    # 元数据
    confidence_score: float  # 分析置信度
    analysis_timestamp: datetime
    llm_model_used: str

class EnhancedLLMAnalyzer:
    """增强的LLM分析器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.openai_client = None
        self.gemini_model = None
        
        # 分析提示词模板
        self.analysis_prompt_template = """
你是一位资深的产品经理和用户体验专家，需要对用户反馈进行深度的多维度分析。

用户反馈：
{feedback_text}

用户元数据：
{user_metadata}

请从以下维度深度分析这条反馈，返回JSON格式结果：

1. 基础维度分析：
   - primary_sentiment: 主要情感倾向 (positive/negative/neutral)
   - sentiment_intensity: 情感强度 (0-1数值)
   - urgency_level: 紧急程度 (critical/high/medium/low)
   - urgency_score: 紧急程度分数 (0-1数值)

2. 需求维度分析：
   - requirement_type: 需求类型 (functional/non_functional/technical/business)
   - requirement_category: 需求类别 (bug_fix/feature_request/improvement/integration)
   - requirement_priority: 需求优先级 (must_have/should_have/could_have/wont_have)

3. 影响维度分析：
   - impact_scope: 影响范围 (individual/team/department/company/ecosystem)
   - impact_frequency: 影响频率 (always/often/sometimes/rarely)
   - user_journey_stage: 用户旅程阶段 (onboarding/daily_use/advanced_use/migration)

4. 技术维度分析：
   - technical_complexity: 技术复杂度 (low/medium/high/very_high)
   - implementation_effort: 实现工作量 (hours/days/weeks/months)
   - dependency_level: 依赖程度 (independent/low_dependency/high_dependency/blocking)

5. 业务维度分析：
   - business_value: 业务价值 (revenue/retention/acquisition/efficiency/compliance)
   - strategic_alignment: 战略匹配度 (core/important/nice_to_have/off_strategy)
   - competitive_advantage: 竞争优势 (differentiator/parity/table_stakes/internal)

6. 用户维度分析：
   - user_segment: 用户群体 (new_users/power_users/enterprise/mobile/web)
   - user_pain_level: 用户痛点程度 (blocker/major_friction/minor_inconvenience/enhancement)
   - user_workaround: 用户当前解决方案（如果有的话）

7. 洞察维度分析：
   - root_cause: 问题根本原因分析
   - solution_suggestion: 建议的解决方案
   - related_areas: 相关的功能区域列表

8. 可执行维度分析：
   - action_owner: 负责团队 (product/engineering/design/support/marketing)
   - estimated_timeline: 预估时间线 (immediate/sprint/quarter/roadmap)
   - success_metrics: 成功指标列表

请确保分析深入、准确，基于反馈内容进行合理推断。
"""

        self.batch_analysis_prompt = """
你需要对一批用户反馈进行批量分析，找出共同模式和关联性。

反馈列表：
{feedback_batch}

请：
1. 对每条反馈进行个体分析（使用前面的分析框架）
2. 识别反馈之间的关联性和模式
3. 提供批量洞察和建议

返回JSON格式：
{
  "individual_analyses": [...],
  "batch_insights": {
    "common_themes": [...],
    "user_segments_affected": [...],
    "priority_recommendations": [...],
    "implementation_sequence": [...]
  }
}
"""
    
    async def initialize(self):
        """初始化LLM客户端"""
        try:
            # 初始化OpenAI客户端
            if self.config.get('openai_api_key'):
                openai.api_key = self.config['openai_api_key']
                if self.config.get('openai_base_url'):
                    openai.api_base = self.config['openai_base_url']
                self.openai_client = openai
                logger.info("OpenAI客户端初始化成功")
            
            # 初始化Gemini客户端
            if self.config.get('gemini_api_key'):
                genai.configure(api_key=self.config['gemini_api_key'])
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini客户端初始化成功")
                
        except Exception as e:
            logger.error(f"LLM客户端初始化失败: {e}")
            raise
    
    async def deep_analyze_feedback(self, feedback_text: str, user_metadata: Dict = None) -> DeepAnalysisResult:
        """对单条反馈进行深度分析"""
        try:
            # 准备提示词
            prompt = self.analysis_prompt_template.format(
                feedback_text=feedback_text,
                user_metadata=json.dumps(user_metadata or {}, ensure_ascii=False, indent=2)
            )
            
            # 尝试使用OpenAI
            result = await self._analyze_with_openai(prompt)
            if not result:
                # 如果OpenAI失败，尝试Gemini
                result = await self._analyze_with_gemini(prompt)
            
            if not result:
                raise Exception("所有LLM引擎都失败了")
            
            # 解析结果
            return self._parse_analysis_result(result, "openai" if self.openai_client else "gemini")
            
        except Exception as e:
            logger.error(f"深度分析失败: {e}")
            # 返回默认结果
            return self._create_default_result()
    
    async def batch_analyze_feedback(self, feedbacks: List[Dict]) -> Dict:
        """批量分析反馈"""
        try:
            # 准备批量提示词
            feedback_batch = []
            for i, feedback in enumerate(feedbacks):
                feedback_batch.append({
                    "id": i + 1,
                    "text": feedback.get('text', ''),
                    "metadata": feedback.get('metadata', {})
                })
            
            prompt = self.batch_analysis_prompt.format(
                feedback_batch=json.dumps(feedback_batch, ensure_ascii=False, indent=2)
            )
            
            # 执行批量分析
            result = await self._analyze_with_openai(prompt, model="gpt-4-turbo")
            if not result:
                result = await self._analyze_with_gemini(prompt)
            
            if result:
                return json.loads(result)
            else:
                # 如果批量分析失败，逐个分析
                return await self._fallback_individual_analysis(feedbacks)
                
        except Exception as e:
            logger.error(f"批量分析失败: {e}")
            return await self._fallback_individual_analysis(feedbacks)
    
    async def _analyze_with_openai(self, prompt: str, model: str = "gpt-4") -> Optional[str]:
        """使用OpenAI进行分析"""
        if not self.openai_client:
            return None
        
        try:
            response = await self.openai_client.ChatCompletion.acreate(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一位资深的产品经理和用户体验专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI分析失败: {e}")
            return None
    
    async def _analyze_with_gemini(self, prompt: str) -> Optional[str]:
        """使用Gemini进行分析"""
        if not self.gemini_model:
            return None
        
        try:
            response = await self.gemini_model.generate_content_async(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini分析失败: {e}")
            return None
    
    def _parse_analysis_result(self, result_text: str, model_used: str) -> DeepAnalysisResult:
        """解析分析结果"""
        try:
            # 尝试提取JSON部分
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_text = result_text[json_start:json_end]
                result_data = json.loads(json_text)
            else:
                # 如果没有JSON格式，尝试解析结构化文本
                result_data = self._parse_structured_text(result_text)
            
            # 创建DeepAnalysisResult对象
            return DeepAnalysisResult(
                # 基础维度
                primary_sentiment=result_data.get('primary_sentiment', 'neutral'),
                sentiment_intensity=float(result_data.get('sentiment_intensity', 0.5)),
                urgency_level=result_data.get('urgency_level', 'medium'),
                urgency_score=float(result_data.get('urgency_score', 0.5)),
                
                # 需求维度
                requirement_type=result_data.get('requirement_type', 'functional'),
                requirement_category=result_data.get('requirement_category', 'improvement'),
                requirement_priority=result_data.get('requirement_priority', 'should_have'),
                
                # 影响维度
                impact_scope=result_data.get('impact_scope', 'individual'),
                impact_frequency=result_data.get('impact_frequency', 'sometimes'),
                user_journey_stage=result_data.get('user_journey_stage', 'daily_use'),
                
                # 技术维度
                technical_complexity=result_data.get('technical_complexity', 'medium'),
                implementation_effort=result_data.get('implementation_effort', 'days'),
                dependency_level=result_data.get('dependency_level', 'low_dependency'),
                
                # 业务维度
                business_value=result_data.get('business_value', 'efficiency'),
                strategic_alignment=result_data.get('strategic_alignment', 'important'),
                competitive_advantage=result_data.get('competitive_advantage', 'parity'),
                
                # 用户维度
                user_segment=result_data.get('user_segment', 'power_users'),
                user_pain_level=result_data.get('user_pain_level', 'minor_inconvenience'),
                user_workaround=result_data.get('user_workaround'),
                
                # 洞察维度
                root_cause=result_data.get('root_cause'),
                solution_suggestion=result_data.get('solution_suggestion'),
                related_areas=result_data.get('related_areas', []),
                
                # 可执行维度
                action_owner=result_data.get('action_owner', 'product'),
                estimated_timeline=result_data.get('estimated_timeline', 'sprint'),
                success_metrics=result_data.get('success_metrics', []),
                
                # 元数据
                confidence_score=float(result_data.get('confidence_score', 0.7)),
                analysis_timestamp=datetime.now(),
                llm_model_used=model_used
            )
            
        except Exception as e:
            logger.error(f"解析分析结果失败: {e}")
            return self._create_default_result()
    
    def _parse_structured_text(self, text: str) -> Dict:
        """解析结构化文本为字典"""
        # 简单的文本解析逻辑
        result = {}
        lines = text.split('\n')
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_').replace('-', '_')
                value = value.strip()
                result[key] = value
        
        return result
    
    def _create_default_result(self) -> DeepAnalysisResult:
        """创建默认分析结果"""
        return DeepAnalysisResult(
            primary_sentiment="neutral",
            sentiment_intensity=0.5,
            urgency_level="medium",
            urgency_score=0.5,
            requirement_type="functional",
            requirement_category="improvement",
            requirement_priority="should_have",
            impact_scope="individual",
            impact_frequency="sometimes",
            user_journey_stage="daily_use",
            technical_complexity="medium",
            implementation_effort="days",
            dependency_level="low_dependency",
            business_value="efficiency",
            strategic_alignment="important",
            competitive_advantage="parity",
            user_segment="power_users",
            user_pain_level="minor_inconvenience",
            user_workaround=None,
            root_cause=None,
            solution_suggestion=None,
            related_areas=[],
            action_owner="product",
            estimated_timeline="sprint",
            success_metrics=[],
            confidence_score=0.3,
            analysis_timestamp=datetime.now(),
            llm_model_used="default"
        )
    
    async def _fallback_individual_analysis(self, feedbacks: List[Dict]) -> Dict:
        """备用的逐个分析方法"""
        individual_analyses = []
        
        for feedback in feedbacks:
            result = await self.deep_analyze_feedback(
                feedback.get('text', ''),
                feedback.get('metadata', {})
            )
            individual_analyses.append(asdict(result))
        
        return {
            "individual_analyses": individual_analyses,
            "batch_insights": {
                "common_themes": [],
                "user_segments_affected": [],
                "priority_recommendations": [],
                "implementation_sequence": []
            }
        }

# 全局实例
enhanced_llm_analyzer = None

async def get_enhanced_analyzer(config: Dict) -> EnhancedLLMAnalyzer:
    """获取增强分析器实例"""
    global enhanced_llm_analyzer
    
    if enhanced_llm_analyzer is None:
        enhanced_llm_analyzer = EnhancedLLMAnalyzer(config)
        await enhanced_llm_analyzer.initialize()
    
    return enhanced_llm_analyzer 