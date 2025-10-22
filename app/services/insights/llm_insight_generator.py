"""
LLM洞察生成器
使用LLM直接从用户反馈数据中生成洞察和执行计划
"""
import json
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import openai
from ...models.settings import LLMSettings
import re

logger = logging.getLogger(__name__)

@dataclass
class InsightResult:
    """洞察结果"""
    insight_id: str
    title: str
    description: str
    insight_type: str              # trend/pattern/opportunity/risk
    confidence_score: float        # 0-1
    impact_level: str              # high/medium/low
    supporting_evidence: List[str] # 支撑证据
    affected_user_segments: List[str] # 影响的用户群体
    business_impact: str           # 业务影响描述
    generated_at: datetime
    is_full_text: bool = False     # 是否为全文洞察

@dataclass
class ActionPlan:
    """执行计划"""
    plan_id: str
    title: str
    summary: str
    priority: str                  # P0/P1/P2/P3
    estimated_effort: str          # 工作量估算
    timeline: str                  # 时间线
    owner_team: str                # 负责团队
    success_metrics: List[str]     # 成功指标
    action_steps: List[Dict]       # 执行步骤
    risk_assessment: str           # 风险评估
    expected_outcome: str          # 预期结果
    related_insights: List[str]    # 相关洞察
    generated_at: datetime

class LLMInsightGenerator:
    """LLM洞察生成器"""
    
    def __init__(self, llm_settings: LLMSettings):
        self.llm_settings = llm_settings
        
        # 使用系统配置的LLM设置
        if llm_settings.enabled:
            # 优先使用theturbo配置
            api_key = llm_settings.theturbo_api_key if llm_settings.theturbo_api_key else llm_settings.apiKey
            base_url = llm_settings.theturbo_base_url if llm_settings.theturbo_base_url else llm_settings.base_url
            
            self.openai_client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            
            logger.info(f"LLM洞察生成器初始化完成，使用模型: {llm_settings.model}")
        else:
            logger.warning("LLM功能已禁用，将无法生成洞察")
            self.openai_client = None

        # 全文洞察生成提示词模板（基于所有历史数据）
        self.full_text_insight_prompt_template = """
你是一位顶级的产品战略分析师和数据洞察专家。请基于以下所有历史用户反馈数据，利用大语言模型的强大分析能力进行深度全文分析，生成具有战略价值的洞察报告。

📊 **完整历史反馈数据集**：
{full_feedback_data}

📈 **数据统计概览**：
- 总反馈数：{total_count}
- 时间跨度：{time_range}
- 数据来源：{data_sources}
- 情感分布：{sentiment_stats}
- 类别分布：{category_stats}
- 优先级分布：{priority_stats}

🎯 **全文洞察分析要求**：
请对所有历史反馈数据进行深度全文分析，生成具有战略价值的洞察。重点关注：

1. **全局趋势洞察**：跨时间、跨类别的整体趋势和变化模式
2. **深层模式识别**：用户行为模式、问题关联性、隐藏需求
3. **机会挖掘**：基于用户反馈发现的产品机会和创新方向
4. **风险预警**：潜在的产品风险、用户流失风险和竞争威胁
5. **用户洞察**：不同用户群体的深度需求分析和用户画像
6. **业务影响评估**：对业务目标、收入、用户满意度的具体影响
7. **长期战略洞察**：基于历史数据的长期发展趋势和战略方向

🔍 **洞察要求**：
- **不限制生成洞察的条数**，根据数据的丰富程度和价值，从各个角度进行深度分析
- 每个洞察需要有充分的数据支撑
- 优先生成高价值、可执行的洞察
- 洞察要具有前瞻性和战略意义
- 要包含具体的数据引用和证据
- **洞察描述必须使用markdown格式，包含标题、列表、重点标记、代码块等结构化内容**
- 利用全量数据的优势，挖掘单独月度分析无法发现的深层洞察

💡 **全文洞察特色**：
- 基于完整历史数据的长期趋势分析
- 跨时间维度的用户行为演变洞察
- 深度关联分析和模式识别
- 前瞻性战略建议和风险预警
- 全量数据支撑的量化洞察

请以JSON格式返回，严格按照以下格式：
{{
  "insights": [
    {{
      "title": "洞察标题",
      "description": "详细描述（使用markdown格式，包含## 标题、- 列表、**重点**等结构化内容）",
      "insight_type": "trend/pattern/opportunity/risk",
      "confidence_score": 0.95,
      "impact_level": "high/medium/low",
      "supporting_evidence": ["具体证据1", "具体证据2", "数据引用"],
      "affected_user_segments": ["用户群体1", "用户群体2"],
      "business_impact": "对业务的具体影响和建议",
      "data_references": ["引用的具体反馈ID或内容片段"],
      "strategic_value": "战略价值和意义"
    }}
  ],
  "executive_summary": {{
    "key_findings": ["关键发现1", "关键发现2"],
    "top_priorities": ["优先事项1", "优先事项2"],
    "strategic_recommendations": ["战略建议1", "战略建议2"],
    "risk_alerts": ["风险警报1", "风险警报2"]
  }}
}}
"""

        # 洞察生成提示词模板（基于最近一个月数据）
        self.insight_prompt_template = """
你是一位资深的产品经理和数据分析专家。请基于以下最近一个月的用户反馈数据，生成深度洞察和具体可执行的改进建议。

📊 **最近一个月反馈数据汇总**：
{feedback_summary}

📈 **反馈统计信息**：
- 总反馈数：{total_feedback}
- 高优先级反馈：{high_priority_count}
- 主要情感分布：{sentiment_distribution}
- 主要类别分布：{category_distribution}
- 关键问题TOP5：{top_issues}

🎯 **常规洞察分析要求**：
请从以下角度进行深度分析并生成洞察：

1. **趋势洞察**：识别用户反馈中的趋势变化和模式
2. **机会洞察**：发现产品改进和创新的机会点
3. **风险洞察**：识别潜在的产品风险和用户流失风险
4. **用户洞察**：分析不同用户群体的需求和痛点

💡 **洞察要求**：
对于每个洞察，请包含：
- 洞察标题（简洁明了）
- 详细描述（**严格限制在300字以内**，**必须使用markdown格式**，包含## 标题、- 列表、**重点**等结构化内容）
- 洞察类型（trend/pattern/opportunity/risk）
- 置信度（0-1，基于数据支撑程度）
- 影响级别（high/medium/low）
- 支撑证据（具体的数据点或反馈内容）
- 影响的用户群体
- 业务影响描述（**必须包含具体可执行的建议，而非方向性建议**）

**重要提示**：
- 每个洞察的业务影响描述必须包含具体的执行建议，例如"**立即优化**XX功能的YY问题，预计2周内完成"而非"需要改善XX功能"
- 洞察描述必须包含具体的数据支撑和量化指标
- 避免空泛的方向性建议，要求具体的行动方案
- 描述内容必须控制在300字以内，保持简洁精准

请以JSON格式返回，严格按照以下格式：
{{
  "insights": [
    {{
      "title": "洞察标题",
      "description": "详细描述（**markdown格式，严格限制300字以内**）",
      "insight_type": "trend/pattern/opportunity/risk",
      "confidence_score": 0.85,
      "impact_level": "high/medium/low",
      "supporting_evidence": ["证据1", "证据2"],
      "affected_user_segments": ["新用户", "企业用户"],
      "business_impact": "业务影响描述（**包含具体可执行的建议**）"
    }}
  ]
}}
"""

        # 执行计划生成提示词模板
        self.action_plan_prompt_template = """
你是一位经验丰富的产品经理。基于以下洞察结果，制定具体的执行计划。

洞察结果：
{insights}

用户反馈上下文：
{context}

请为每个洞察制定详细的执行计划，包含：

1. **计划标题**：简洁明了的执行计划名称
2. **计划概要**：50-100字的简要说明
3. **优先级**：P0(紧急)/P1(高)/P2(中)/P3(低)
4. **预估工作量**：如"2-3周"、"1个月"等
5. **建议时间线**：何时开始和完成
6. **负责团队**：engineering/product/design/marketing
7. **成功指标**：如何衡量成功
8. **具体步骤**：3-5个可执行的步骤
9. **风险评估**：潜在风险和缓解措施
10. **预期结果**：实施后的预期效果

请以JSON格式返回：
{{
  "action_plans": [
    {{
      "title": "计划标题",
      "summary": "计划概要",
      "priority": "P0/P1/P2/P3",
      "estimated_effort": "工作量估算",
      "timeline": "时间线",
      "owner_team": "负责团队",
      "success_metrics": ["指标1", "指标2"],
      "action_steps": [
        {{"step": 1, "description": "步骤描述", "owner": "负责人", "duration": "时长"}},
        {{"step": 2, "description": "步骤描述", "owner": "负责人", "duration": "时长"}}
      ],
      "risk_assessment": "风险评估",
      "expected_outcome": "预期结果",
      "related_insights": ["相关洞察标题"]
    }}
  ]
}}
"""
    
    async def generate_full_text_insights(self, feedback_data: List[Dict]) -> Dict:
        """
        全文洞察生成 - 利用gemini的1M上下文能力一次性分析所有反馈数据
        """
        try:
            logger.info(f"开始全文洞察分析，数据量: {len(feedback_data)}条")
            
            # 准备完整的反馈数据
            full_data = self._prepare_full_feedback_data(feedback_data)
            
            # 构建全文洞察提示词
            prompt = self.full_text_insight_prompt_template.format(**full_data)
            
            # 调用LLM生成全文洞察
            response = await self._call_llm(prompt)
            
            # 解析全文洞察结果
            result = self._parse_full_text_insights_response(response)
            
            logger.info(f"全文洞察分析完成，生成{len(result.get('insights', []))}个洞察")
            return result
            
        except Exception as e:
            logger.error(f"全文洞察生成失败: {e}")
            return {"insights": [], "executive_summary": {}}
    
    async def generate_insights_from_feedback(self, feedback_data: List[Dict]) -> List[InsightResult]:
        """从反馈数据生成洞察"""
        try:
            # 准备数据摘要
            summary = self._prepare_feedback_summary(feedback_data)
            
            # 构建提示词
            prompt = self.insight_prompt_template.format(**summary)
            
            # 调用LLM生成洞察
            response = await self._call_llm(prompt)
            
            # 解析结果
            insights = self._parse_insights_response(response)
            
            logger.info(f"成功生成{len(insights)}个洞察")
            return insights
            
        except Exception as e:
            logger.error(f"生成洞察失败: {e}")
            return []
    
    async def generate_action_plans_from_insights(self, insights: List[InsightResult], feedback_context: Dict) -> List[ActionPlan]:
        """从洞察生成执行计划"""
        try:
            # 准备洞察数据
            insights_data = [
                {
                    "title": insight.title,
                    "description": insight.description,
                    "insight_type": insight.insight_type,
                    "impact_level": insight.impact_level,
                    "confidence_score": insight.confidence_score
                }
                for insight in insights
            ]
            
            # 构建提示词
            prompt = self.action_plan_prompt_template.format(
                insights=json.dumps(insights_data, ensure_ascii=False, indent=2),
                context=json.dumps(feedback_context, ensure_ascii=False, indent=2)
            )
            
            # 调用LLM生成执行计划
            response = await self._call_llm(prompt)
            
            # 解析结果
            action_plans = self._parse_action_plans_response(response)
            
            logger.info(f"成功生成{len(action_plans)}个执行计划")
            return action_plans
            
        except Exception as e:
            logger.error(f"生成执行计划失败: {e}")
            return []
    
    def _prepare_feedback_summary(self, feedback_data: List[Dict]) -> Dict:
        """准备反馈数据摘要"""
        total_feedback = len(feedback_data)
        
        # 统计情感分布
        sentiment_counts = {}
        category_counts = {}
        high_priority_count = 0
        
        sample_feedback = []
        
        for feedback in feedback_data:
            # 情感统计
            sentiment = feedback.get('filter_result', {}).get('sentiment', 'neutral')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            
            # 类别统计
            category = feedback.get('filter_result', {}).get('category', 'general')
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # 高优先级统计
            priority_score = feedback.get('filter_result', {}).get('priority_score', 0)
            if priority_score > 0.7:
                high_priority_count += 1
            
            # 收集样本反馈
            if len(sample_feedback) < 10:
                sample_feedback.append({
                    "text": feedback.get('text', '')[:200],
                    "sentiment": sentiment,
                    "category": category,
                    "priority_score": priority_score
                })
        
        # 识别TOP问题
        top_issues = self._identify_top_issues(feedback_data)
        
        return {
            "feedback_summary": json.dumps(sample_feedback, ensure_ascii=False, indent=2),
            "total_feedback": total_feedback,
            "high_priority_count": high_priority_count,
            "sentiment_distribution": sentiment_counts,
            "category_distribution": category_counts,
            "top_issues": top_issues
        }
    
    def _prepare_full_feedback_data(self, feedback_data: List[Dict]) -> Dict:
        """准备完整的反馈数据用于全文洞察"""
        all_feedback_text = "".join([f"用户反馈: {f.get('text', '')}\n" for f in feedback_data])
        total_count = len(feedback_data)
        time_range = "N/A" # 需要从反馈数据中提取
        data_sources = "用户直接反馈" # 需要从反馈数据中提取
        
        sentiment_stats = {}
        category_stats = {}
        priority_stats = {}
        
        for f in feedback_data:
            sentiment = f.get('filter_result', {}).get('sentiment', 'neutral')
            sentiment_stats[sentiment] = sentiment_stats.get(sentiment, 0) + 1
            
            category = f.get('filter_result', {}).get('category', 'general')
            category_stats[category] = category_stats.get(category, 0) + 1
            
            priority_score = f.get('filter_result', {}).get('priority_score', 0)
            priority_level = "high" if priority_score > 0.7 else "medium" if priority_score > 0.3 else "low"
            priority_stats[priority_level] = priority_stats.get(priority_level, 0) + 1
        
        return {
            "full_feedback_data": all_feedback_text,
            "total_count": total_count,
            "time_range": time_range,
            "data_sources": data_sources,
            "sentiment_stats": sentiment_stats,
            "category_stats": category_stats,
            "priority_stats": priority_stats
        }
    
    def _parse_full_text_insights_response(self, response: str) -> Dict:
        """解析全文洞察响应"""
        try:
            logger.info(f"原始全文洞察响应: {response[:500]}...")
            
            # 尝试提取JSON部分
            response = response.strip()
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                if end != -1:
                    response = response[start:end].strip()
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                if end != -1:
                    response = response[start:end].strip()
            
            if '{' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                if end > start:
                    response = response[start:end]
            
            logger.info(f"清理后的全文洞察JSON: {response[:200]}...")
            
            # 尝试修复JSON格式问题
            response = self._fix_json_format(response)
            
            data = json.loads(response)
            
            # 解析洞察列表
            insights = []
            for i, insight_data in enumerate(data.get('insights', [])):
                insight = InsightResult(
                    insight_id=f"full_text_insight_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                    title=insight_data.get('title', ''),
                    description=insight_data.get('description', ''),
                    insight_type=insight_data.get('insight_type', 'pattern'),
                    confidence_score=insight_data.get('confidence_score', 0.5),
                    impact_level=insight_data.get('impact_level', 'medium'),
                    supporting_evidence=insight_data.get('supporting_evidence', []),
                    affected_user_segments=insight_data.get('affected_user_segments', []),
                    business_impact=insight_data.get('business_impact', ''),
                    generated_at=datetime.now(),
                    is_full_text=True  # 标记为全文洞察
                )
                insights.append(insight)
            
            # 解析执行摘要
            executive_summary = {
                "key_findings": data.get('executive_summary', {}).get('key_findings', []),
                "top_priorities": data.get('executive_summary', {}).get('top_priorities', []),
                "strategic_recommendations": data.get('executive_summary', {}).get('strategic_recommendations', []),
                "risk_alerts": data.get('executive_summary', {}).get('risk_alerts', [])
            }
            
            return {"insights": insights, "executive_summary": executive_summary}
            
        except json.JSONDecodeError as e:
            logger.error(f"解析全文洞察响应失败: {e}")
            logger.error(f"响应内容: {response}")
            return {"insights": [], "executive_summary": {}}
        except Exception as e:
            logger.error(f"处理全文洞察响应时出错: {e}")
            logger.error(f"响应内容: {response}")
            return {"insights": [], "executive_summary": {}}
    
    def _fix_json_format(self, json_str: str) -> str:
        """修复常见的JSON格式问题"""
        try:
            # 移除多余的换行符和制表符
            json_str = json_str.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            
            # 压缩多余的空格
            json_str = re.sub(r'\s+', ' ', json_str)
            
            # 修复截断的JSON - 查找最后一个完整的对象
            if not json_str.strip().endswith('}'):
                logger.info("检测到JSON截断，尝试修复...")
                
                # 计算大括号平衡
                brace_count = 0
                bracket_count = 0
                in_string = False
                escape_next = False
                last_complete_pos = -1
                
                for i, char in enumerate(json_str):
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    
                    if not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                last_complete_pos = i
                        elif char == '[':
                            bracket_count += 1
                        elif char == ']':
                            bracket_count -= 1
                
                # 如果找到完整的对象，截取到那个位置
                if last_complete_pos > 0:
                    json_str = json_str[:last_complete_pos + 1]
                    logger.info(f"成功修复JSON截断，截取到位置: {last_complete_pos}")
                else:
                    # 如果没有找到完整的对象，尝试手动补全
                    logger.info("尝试手动补全JSON...")
                    
                    # 计算需要补全的括号数量
                    missing_braces = brace_count
                    missing_brackets = bracket_count
                    
                    # 移除末尾的不完整部分
                    json_str = json_str.rstrip(', \t\n\r')
                    
                    # 补全缺失的括号
                    for _ in range(missing_brackets):
                        json_str += ']'
                    for _ in range(missing_braces):
                        json_str += '}'
                    
                    logger.info(f"补全了 {missing_brackets} 个方括号和 {missing_braces} 个大括号")
            
            # 修复常见的JSON语法错误
            # 移除尾部逗号
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            
            # 修复引号问题
            json_str = json_str.replace('""', '"')
            
            # 修复数字格式问题
            json_str = re.sub(r'(\d+)\.(\d+)', r'\1.\2', json_str)
            
            # 验证修复后的JSON
            try:
                json.loads(json_str)
                logger.info("JSON修复成功，格式验证通过")
                return json_str
            except json.JSONDecodeError as e:
                logger.warning(f"JSON修复后仍有格式问题: {e}")
                # 尝试更激进的修复
                return self._aggressive_json_fix(json_str)
            
        except Exception as e:
            logger.error(f"修复JSON格式时出错: {e}")
            return json_str
    
    def _aggressive_json_fix(self, json_str: str) -> str:
        """更激进的JSON修复方法"""
        try:
            logger.info("执行激进的JSON修复...")
            
            # 尝试提取insights部分
            insights_start = json_str.find('"insights":')
            if insights_start == -1:
                logger.error("未找到insights字段")
                return '{"insights": [], "executive_summary": {}}'
            
            # 查找insights数组的开始
            array_start = json_str.find('[', insights_start)
            if array_start == -1:
                logger.error("未找到insights数组")
                return '{"insights": [], "executive_summary": {}}'
            
            # 尝试提取完整的insights对象
            insights_objects = []
            brace_count = 0
            current_object = ""
            in_string = False
            escape_next = False
            
            i = array_start + 1
            while i < len(json_str):
                char = json_str[i]
                
                if escape_next:
                    current_object += char
                    escape_next = False
                    i += 1
                    continue
                
                if char == '\\':
                    escape_next = True
                    current_object += char
                    i += 1
                    continue
                
                if char == '"':
                    in_string = not in_string
                    current_object += char
                    i += 1
                    continue
                
                if not in_string:
                    if char == '{':
                        brace_count += 1
                        current_object += char
                    elif char == '}':
                        brace_count -= 1
                        current_object += char
                        if brace_count == 0:
                            # 找到一个完整的对象
                            try:
                                obj = json.loads(current_object)
                                insights_objects.append(obj)
                                current_object = ""
                                logger.info(f"成功提取第{len(insights_objects)}个洞察对象")
                            except json.JSONDecodeError:
                                logger.warning(f"对象{len(insights_objects)+1}格式错误，跳过")
                                current_object = ""
                    elif char == ']':
                        break
                    else:
                        current_object += char
                else:
                    current_object += char
                
                i += 1
            
            # 构建最终的JSON
            result = {
                "insights": insights_objects,
                "executive_summary": {
                    "key_findings": [],
                    "top_priorities": [],
                    "strategic_recommendations": [],
                    "risk_alerts": []
                }
            }
            
            logger.info(f"激进修复完成，提取了{len(insights_objects)}个洞察对象")
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"激进JSON修复失败: {e}")
            return '{"insights": [], "executive_summary": {}}'
    
    def _identify_top_issues(self, feedback_data: List[Dict]) -> List[str]:
        """识别TOP问题"""
        # 简化实现：基于关键词频率
        from collections import Counter
        
        all_keywords = []
        for feedback in feedback_data:
            keywords = feedback.get('filter_result', {}).get('extracted_keywords', [])
            all_keywords.extend(keywords)
        
        if all_keywords:
            top_keywords = Counter(all_keywords).most_common(5)
            return [f"{keyword}({count}次提及)" for keyword, count in top_keywords]
        
        return ["暂无明显问题模式"]
    
    async def _call_llm(self, prompt: str) -> str:
        """调用LLM"""
        try:
            if not self.openai_client:
                raise Exception("LLM功能已禁用")
                
            response = self.openai_client.chat.completions.create(
                model=self.llm_settings.model,
                messages=[
                    {"role": "system", "content": "你是一位资深的产品经理和数据分析专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.llm_settings.temperature,
                max_tokens=self.llm_settings.maxTokens
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"调用LLM失败: {e}")
            raise
    
    def _parse_insights_response(self, response: str) -> List[InsightResult]:
        """解析洞察响应"""
        try:
            logger.info(f"原始LLM响应: {response[:500]}...")  # 记录前500字符
            
            # 尝试提取JSON部分
            response = response.strip()
            if '```json' in response:
                # 提取JSON代码块
                start = response.find('```json') + 7
                end = response.find('```', start)
                if end != -1:
                    response = response[start:end].strip()
            elif '```' in response:
                # 提取任何代码块
                start = response.find('```') + 3
                end = response.find('```', start)
                if end != -1:
                    response = response[start:end].strip()
            
            # 如果响应以{开头，尝试提取JSON部分
            if '{' in response:
                start = response.find('{')
                # 找到最后一个}
                end = response.rfind('}') + 1
                if end > start:
                    response = response[start:end]
            
            logger.info(f"清理后的JSON: {response[:200]}...")
            
            data = json.loads(response)
            insights = []
            
            for i, insight_data in enumerate(data.get('insights', [])):
                insight = InsightResult(
                    insight_id=f"insight_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                    title=insight_data.get('title', ''),
                    description=insight_data.get('description', ''),
                    insight_type=insight_data.get('insight_type', 'pattern'),
                    confidence_score=insight_data.get('confidence_score', 0.5),
                    impact_level=insight_data.get('impact_level', 'medium'),
                    supporting_evidence=insight_data.get('supporting_evidence', []),
                    affected_user_segments=insight_data.get('affected_user_segments', []),
                    business_impact=insight_data.get('business_impact', ''),
                    generated_at=datetime.now()
                )
                insights.append(insight)
            
            return insights
            
        except json.JSONDecodeError as e:
            logger.error(f"解析洞察响应失败: {e}")
            logger.error(f"响应内容: {response}")
            return []
        except Exception as e:
            logger.error(f"处理洞察响应时出错: {e}")
            logger.error(f"响应内容: {response}")
            return []
    
    def _parse_action_plans_response(self, response: str) -> List[ActionPlan]:
        """解析执行计划响应"""
        try:
            logger.info(f"原始执行计划响应: {response[:500]}...")
            
            # 同样的JSON清理逻辑
            response = response.strip()
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                if end != -1:
                    response = response[start:end].strip()
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                if end != -1:
                    response = response[start:end].strip()
            
            if '{' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                if end > start:
                    response = response[start:end]
            
            logger.info(f"清理后的执行计划JSON: {response[:200]}...")
            
            data = json.loads(response)
            action_plans = []
            
            for i, plan_data in enumerate(data.get('action_plans', [])):
                plan = ActionPlan(
                    plan_id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                    title=plan_data.get('title', ''),
                    summary=plan_data.get('summary', ''),
                    priority=plan_data.get('priority', 'P2'),
                    estimated_effort=plan_data.get('estimated_effort', ''),
                    timeline=plan_data.get('timeline', ''),
                    owner_team=plan_data.get('owner_team', 'product'),
                    success_metrics=plan_data.get('success_metrics', []),
                    action_steps=plan_data.get('action_steps', []),
                    risk_assessment=plan_data.get('risk_assessment', ''),
                    expected_outcome=plan_data.get('expected_outcome', ''),
                    related_insights=plan_data.get('related_insights', []),
                    generated_at=datetime.now()
                )
                action_plans.append(plan)
            
            return action_plans
            
        except json.JSONDecodeError as e:
            logger.error(f"解析执行计划响应失败: {e}")
            logger.error(f"响应内容: {response}")
            return []
        except Exception as e:
            logger.error(f"处理执行计划响应时出错: {e}")
            logger.error(f"响应内容: {response}")
            return []

# 全局实例
llm_insight_generator = None

def get_llm_insight_generator(llm_settings: LLMSettings) -> LLMInsightGenerator:
    """获取LLM洞察生成器实例"""
    global llm_insight_generator
    
    if llm_insight_generator is None:
        llm_insight_generator = LLMInsightGenerator(llm_settings)
    
    return llm_insight_generator 