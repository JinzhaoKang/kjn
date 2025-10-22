"""
LLM核心分析引擎
负责对用户反馈进行深度分析，包括情感分析、意图识别、主题提取等
"""
import json
import asyncio
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import logging
from abc import ABC, abstractmethod

from openai import AsyncOpenAI
import google.generativeai as genai
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_db
from app.models.settings import AppSettings

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """分析结果数据类"""
    sentiment: str  # "Positive", "Negative", "Neutral"
    sentiment_score: float  # -1.0 到 1.0
    intent: str  # "Bug Report", "Feature Request", "Question", "UX Complaint", "Praise"
    topics: List[str]  # 主题列表
    urgency_score: float  # 0.0 到 1.0
    summary: str  # 洞察摘要
    confidence: float  # 分析置信度 0.0 到 1.0


class SettingsService:
    """设置服务，用于动态获取数据库中的配置"""
    
    @staticmethod
    async def get_app_settings() -> AppSettings:
        """从数据库获取应用设置"""
        try:
            async for db in get_db():
                settings_doc = await db["settings"].find_one({"_id": "global"})
                if settings_doc and "settings" in settings_doc:
                    return AppSettings.model_validate(settings_doc["settings"])
                else:
                    # 返回默认设置
                    return AppSettings()
        except Exception as e:
            logger.error(f"获取设置失败: {e}")
            return AppSettings()


class LLMAnalyzer(ABC):
    """LLM分析器基类"""
    
    def __init__(self):
        self.analysis_prompt = self._build_analysis_prompt()
    
    def _build_analysis_prompt(self) -> str:
        """构建分析提示"""
        return """
你是一个专业的用户反馈分析专家。请仔细分析以下用户反馈内容，并以JSON格式返回分析结果。

用户反馈："{feedback_text}"

请从以下维度进行深度分析：

1. **情感分析 (sentiment)**: 
   - "Positive": 用户表达满意、赞扬、感谢等正面情感
   - "Negative": 用户表达不满、抱怨、批评等负面情感  
   - "Neutral": 用户表达中性的询问、建议或陈述

2. **情感强度 (sentiment_score)**: -1.0到1.0的数值，-1.0表示极度负面，1.0表示极度正面

3. **反馈类型 (intent)**:
   - "Bug Report": 报告系统错误、功能异常
   - "Feature Request": 建议新功能或改进
   - "UX Complaint": 用户体验问题投诉
   - "Question": 咨询类问题
   - "Praise": 表扬和赞美

4. **关键词提取 (topics)**: 
   - 提取3-5个最重要的关键概念词汇
   - 优先选择：功能模块名、技术术语、核心问题词
   - 避免：语气词、连接词、过于泛化的词
   - 示例：["登录模块", "页面加载", "数据同步", "用户界面"]

5. **紧急程度 (urgency_score)**: 0.0到1.0的数值
   - 0.0-0.3: 低优先级（建议、改进意见）
   - 0.4-0.6: 中等优先级（一般问题）
   - 0.7-0.9: 高优先级（影响使用的问题）
   - 0.9-1.0: 紧急（严重阻塞性问题）

6. **问题概要 (summary)**: 用1-2句话概括用户的核心反馈点

7. **分析置信度 (confidence)**: 
   - 基于反馈内容的清晰度和完整性评估
   - 0.0-0.5: 内容模糊或信息不足
   - 0.6-0.8: 内容较清晰
   - 0.9-1.0: 内容非常清晰明确

严格按照以下JSON格式返回，不要添加任何其他内容：
{{
    "sentiment": "Negative",
    "sentiment_score": -0.7,
    "intent": "Bug Report", 
    "topics": ["登录功能", "网络超时", "页面响应"],
    "urgency_score": 0.8,
    "summary": "用户反映登录功能存在网络超时问题，严重影响正常使用体验",
    "confidence": 0.9
}}
"""
    
    @abstractmethod
    async def analyze_feedback(self, feedback_text: str) -> AnalysisResult:
        """分析用户反馈"""
        pass
    
    def _parse_analysis_result(self, response_text: str) -> AnalysisResult:
        """解析分析结果"""
        try:
            # 尝试提取JSON部分
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                result_dict = json.loads(json_text)
                
                return AnalysisResult(
                    sentiment=result_dict.get("sentiment", "Neutral"),
                    sentiment_score=float(result_dict.get("sentiment_score", 0.0)),
                    intent=result_dict.get("intent", "Question"),
                    topics=result_dict.get("topics", []),
                    urgency_score=float(result_dict.get("urgency_score", 0.0)),
                    summary=result_dict.get("summary", ""),
                    confidence=float(result_dict.get("confidence", 0.5))
                )
            else:
                raise ValueError("无法找到有效的JSON格式")
                
        except Exception as e:
            logger.error(f"解析分析结果失败: {e}, 原始回复: {response_text}")
            # 返回默认结果
            return AnalysisResult(
                sentiment="Neutral",
                sentiment_score=0.0,
                intent="Question",
                topics=[],
                urgency_score=0.0,
                summary="分析失败",
                confidence=0.0
            )


class OpenAIAnalyzer(LLMAnalyzer):
    """OpenAI分析器（兼容新版API）"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", base_url: str = None):
        super().__init__()
        if not api_key:
            raise ValueError("OpenAI API Key未配置")
        
        # 使用新版OpenAI客户端
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
    
    async def analyze_feedback(self, feedback_text: str) -> AnalysisResult:
        """使用OpenAI分析用户反馈"""
        try:
            prompt = self.analysis_prompt.format(feedback_text=feedback_text)
            
            # 使用新版API调用方式
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的用户反馈分析师。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content
            return self._parse_analysis_result(response_text)
            
        except Exception as e:
            logger.error(f"OpenAI分析失败: {e}")
            raise


class GeminiAnalyzer(LLMAnalyzer):
    """Google Gemini分析器"""
    
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        super().__init__()
        if not api_key:
            raise ValueError("Google API Key未配置")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    async def analyze_feedback(self, feedback_text: str) -> AnalysisResult:
        """使用Gemini分析用户反馈"""
        try:
            prompt = self.analysis_prompt.format(feedback_text=feedback_text)
            
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=500
                )
            )
            
            response_text = response.text
            return self._parse_analysis_result(response_text)
            
        except Exception as e:
            logger.error(f"Gemini分析失败: {e}")
            raise


class AnalysisEngine:
    """分析引擎主类"""
    
    def __init__(self):
        self.analyzers = {}
        self.primary_analyzer = None
        self._initialized = False
    
    async def initialize(self):
        """异步初始化分析器"""
        if self._initialized:
            return
        try:
            app_settings = await SettingsService.get_app_settings()
            self.analyzers = await self._init_analyzers(app_settings)
            self.primary_analyzer = self._get_primary_analyzer()
            self._initialized = True
            logger.info("分析引擎初始化完成")
        except Exception as e:
            logger.error(f"分析引擎初始化失败: {e}")
            raise
    
    async def _init_analyzers(self, app_settings: AppSettings) -> Dict[str, LLMAnalyzer]:
        """根据设置初始化可用的分析器"""
        analyzers = {}
        
        if not app_settings.analysis.llm.enabled:
            logger.warning("LLM分析功能已禁用")
            return analyzers
        
        llm_settings = app_settings.analysis.llm
        
        # 优先使用theturbo.ai配置
        theturbo_api_key = llm_settings.theturbo_api_key
        theturbo_base_url = llm_settings.theturbo_base_url
        model = llm_settings.model
        
        # 检查是否有theturbo.ai配置
        if theturbo_api_key and theturbo_base_url:
            api_key = theturbo_api_key
            base_url = theturbo_base_url
            logger.info("使用theturbo.ai配置进行LLM分析")
        else:
            # 回退到传统配置
            api_key = llm_settings.apiKey
            base_url = llm_settings.base_url
            logger.info("使用传统LLM配置")
        
        if not api_key:
            logger.warning("未配置LLM API Key")
            return analyzers
        
        # 根据模型类型初始化对应的分析器
        try:
            logger.info(f"🔧 准备初始化分析器，用户配置模型：{model}")
            
            if model.startswith("gemini") or "gemini" in model.lower():
                # 对于Gemini模型，优先使用theturbo.ai的OpenAI兼容接口
                if theturbo_api_key and theturbo_base_url:
                    analyzers["openai"] = OpenAIAnalyzer(api_key, model, base_url)
                    logger.info(f"✅ 使用theturbo.ai OpenAI兼容接口，模型：{model}，API端点：{base_url}")
                else:
                    # 回退到原生Gemini API
                    analyzers["gemini"] = GeminiAnalyzer(api_key, model)
                    logger.info(f"✅ 使用原生Gemini API，模型：{model}")
            elif model.startswith("gpt") or model.startswith("claude") or "turbo" in model.lower():
                # 对于OpenAI/Claude模型
                analyzers["openai"] = OpenAIAnalyzer(api_key, model, base_url)
                logger.info(f"✅ OpenAI兼容分析器初始化成功，模型：{model}，API端点：{base_url or '默认'}")
            else:
                # 默认使用OpenAI兼容分析器
                analyzers["openai"] = OpenAIAnalyzer(api_key, model, base_url)
                logger.info(f"✅ 使用OpenAI兼容分析器（默认），模型：{model}，API端点：{base_url or '默认'}")
        except Exception as e:
            logger.error(f"初始化{model}分析器失败: {e}")
        
        if not analyzers:
            logger.warning("没有可用的LLM分析器，请在前端设置页面配置API Key")
        
        return analyzers
    
    def _get_primary_analyzer(self) -> Optional[LLMAnalyzer]:
        """获取主要分析器"""
        if "openai" in self.analyzers:
            return self.analyzers["openai"]
        elif "gemini" in self.analyzers:
            return self.analyzers["gemini"]
        else:
            return None
    
    async def analyze_single_feedback(self, feedback_text: str) -> AnalysisResult:
        """分析单条反馈"""
        await self.initialize()
        
        if not self.primary_analyzer:
            raise RuntimeError("没有可用的分析器，请在前端设置页面配置LLM API Key")
        
        # 增强的内容检查
        if not feedback_text or not feedback_text.strip():
            raise ValueError("反馈内容不能为空")
        
        # 处理None值
        if feedback_text is None:
            raise ValueError("反馈内容为None")
        
        # 文本长度检查
        if len(feedback_text) > settings.max_feedback_length:
            feedback_text = feedback_text[:settings.max_feedback_length]
            logger.warning(f"反馈文本过长，已截断到{settings.max_feedback_length}字符")
        
        try:
            result = await self.primary_analyzer.analyze_feedback(feedback_text)
            logger.info(f"反馈分析完成: 情感={result.sentiment}, 意图={result.intent}")
            return result
        except Exception as e:
            logger.error(f"反馈分析失败: {e}")
            # 尝试使用备用分析器
            for name, analyzer in self.analyzers.items():
                if analyzer != self.primary_analyzer:
                    try:
                        logger.info(f"尝试使用备用分析器: {name}")
                        result = await analyzer.analyze_feedback(feedback_text)
                        return result
                    except Exception as backup_error:
                        logger.error(f"备用分析器{name}也失败: {backup_error}")
                        continue
            
            # 所有分析器都失败，抛出异常
            raise RuntimeError(f"所有分析器都失败，最后错误: {e}")
    
    async def analyze_batch_feedback(self, feedback_list: List[str]) -> List[AnalysisResult]:
        """批量分析反馈"""
        await self.initialize()
        
        tasks = [self.analyze_single_feedback(feedback) for feedback in feedback_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"批量分析中第{i+1}条反馈失败: {result}")
                # 添加默认结果
                processed_results.append(AnalysisResult(
                    sentiment="Neutral",
                    sentiment_score=0.0,
                    intent="Question",
                    topics=[],
                    urgency_score=0.0,
                    summary="批量分析失败",
                    confidence=0.0
                ))
            else:
                processed_results.append(result)
        
        return processed_results


# 创建全局分析引擎实例
analysis_engine = AnalysisEngine() 