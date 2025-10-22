# file: company_research_decision_standalone.py
# -*- coding: utf-8 -*-
"""
独立可运行：公司研究 -> DeepAnalysis -> 情感深度融合 -> 6维打分 -> 决策

用法示例：
  # 离线演示（不连外网、不用key）
  python company_research_decision_standalone.py "科沃斯机器人股份有限公司" --mock

  # 连 Gemini（可选）：
  pip install google-generativeai
  export GOOGLE_API_KEY="你的key"
  python company_research_decision_standalone.py "科沃斯机器人股份有限公司"

  # 带情感文件：
  pip install pandas openpyxl
  python company_research_decision_standalone.py "科沃斯机器人股份有限公司" \
      --sentiment "/mnt/data/Amazon_US_评论_情感结果_5cls.xlsx"
"""

import os
import re
import json
import math
import argparse
import asyncio
from dataclasses import dataclass, asdict, replace
from typing import Optional, Dict, Any, Tuple

# ============================== 1) DeepAnalysis 结构 ==============================

@dataclass
class DeepAnalysis:
    impact_scope: str                 # individual/team/department/company/ecosystem
    user_pain_level: str              # enhancement/minor_inconvenience/major_friction/blocker
    impact_frequency: str             # rarely/sometimes/often/always

    urgency_score: float              # 0~1
    estimated_timeline: str           # immediate/sprint/quarter/roadmap

    technical_complexity: str         # low/medium/high/very_high
    implementation_effort: str        # hours/days/weeks/months

    business_value: str               # efficiency/retention/acquisition/revenue/compliance
    competitive_advantage: str        # differentiator/parity/table_stakes/internal

    strategic_alignment: str          # off_strategy/nice_to_have/important/core
    requirement_priority: str         # wont_have/could_have/should_have/must_have

    confidence_score: float           # 0~1

    def validate(self) -> "DeepAnalysis":
        enums = {
            "impact_scope": {"individual","team","department","company","ecosystem"},
            "user_pain_level": {"enhancement","minor_inconvenience","major_friction","blocker"},
            "impact_frequency": {"rarely","sometimes","often","always"},
            "estimated_timeline": {"immediate","sprint","quarter","roadmap"},
            "technical_complexity": {"low","medium","high","very_high"},
            "implementation_effort": {"hours","days","weeks","months"},
            "business_value": {"efficiency","retention","acquisition","revenue","compliance"},
            "competitive_advantage": {"differentiator","parity","table_stakes","internal"},
            "strategic_alignment": {"off_strategy","nice_to_have","important","core"},
            "requirement_priority": {"wont_have","could_have","should_have","must_have"},
        }
        defaults = {
            "impact_scope": "team",
            "user_pain_level": "enhancement",
            "impact_frequency": "sometimes",
            "estimated_timeline": "quarter",
            "technical_complexity": "medium",
            "implementation_effort": "weeks",
            "business_value": "efficiency",
            "competitive_advantage": "parity",
            "strategic_alignment": "important",
            "requirement_priority": "should_have",
        }
        for k, allowed in enums.items():
            v = getattr(self, k)
            if v not in allowed:
                setattr(self, k, defaults[k])
        self.urgency_score = float(max(0.0, min(1.0, self.urgency_score)))
        self.confidence_score = float(max(0.0, min(1.0, self.confidence_score)))
        return self

# ============================== 2) LLM 客户端（Gemini；无key自动mock） ==============================

class GeminiJSONClient:
    """严格JSON补全；失败回 '{}'。"""
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-pro", force_mock: bool = False):
        self.force_mock = force_mock
        self.available = False
        self.client = None
        if not force_mock and api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel(model)
                self.available = True
            except Exception as e:
                print(f"[WARN] Gemini JSON 初始化失败，使用 mock: {e}")

    async def complete_json(self, prompt: str, temperature: float = 0.1, max_tokens: int = 1200) -> str:
        if not self.available:
            return "{}"
        try:
            import google.generativeai as genai
            resp = await self.client.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )
            text = (resp.text or "").strip()
            l = text.find("{"); r = text.rfind("}")
            return text[l:r+1] if (l != -1 and r > l) else "{}"
        except Exception as e:
            print(f"[WARN] Gemini JSON 调用失败：{e}")
            return "{}"

class GeminiTextClient:
    """文本生成；无key/失败则使用 mock 文本。"""
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-pro", force_mock: bool = False):
        self.force_mock = force_mock
        self.available = False
        self.client = None
        if not force_mock and api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel(model)
                self.available = True
            except Exception as e:
                print(f"[WARN] Gemini 文本初始化失败，使用 mock: {e}")

    async def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 2500) -> str:
        if not self.available:
            return self._mock_text(prompt)
        try:
            import google.generativeai as genai
            resp = await self.client.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )
            return (resp.text or "").strip()
        except Exception as e:
            print(f"[WARN] Gemini 文本调用失败，使用 mock：{e}")
            return self._mock_text(prompt)

    def _mock_text(self, prompt: str) -> str:
        return (
            "【执行摘要】公司近两期财务表现改善，现金流回正，海外增长显著。"
            "【业务与产品】双品牌协同，AI能力嵌入产品矩阵。"
            "【财务与现金流】营收回升、净利改善、经营现金流增长。"
            "【市场竞争】国内价格战压力，海外份额提升。"
            "【技术与专利】持续研发投入，发布AI智能体与快充技术。"
            "【风险与合规】库存与专利诉讼需关注。"
            "【展望与关键动作】聚焦高端差异化、深化海外本地化、巩固双品牌。"
        )

# ============================== 3) 研究抽取器：长文 -> DeepAnalysis ==============================

class ResearchExtractor:
    STRICT_JSON_PROMPT = """
只输出 JSON，不要任何解释。
把下面的公司研究内容转成一个 deep_analysis 对象，字段严格为：
impact_scope( individual/team/department/company/ecosystem ),
user_pain_level( enhancement/minor_inconvenience/major_friction/blocker ),
impact_frequency( rarely/sometimes/often/always ),
urgency_score( 0~1 ),
estimated_timeline( immediate/sprint/quarter/roadmap ),
technical_complexity( low/medium/high/very_high ),
implementation_effort( hours/days/weeks/months ),
business_value( efficiency/retention/acquisition/revenue/compliance ),
competitive_advantage( differentiator/parity/table_stakes/internal ),
strategic_alignment( off_strategy/nice_to_have/important/core ),
requirement_priority( wont_have/could_have/should_have/must_have ),
confidence_score( 0~1 ).

公司研究：
{research_text}
""".strip()

    def __init__(self, llm_json_client: GeminiJSONClient):
        self.llm = llm_json_client

    async def to_deep_analysis(self, research_text: str) -> DeepAnalysis:
        raw = await self.llm.complete_json(
            self.STRICT_JSON_PROMPT.format(research_text=research_text[:12000])
        )
        try:
            data = json.loads(raw or "{}")
            da = DeepAnalysis(
                impact_scope=data.get("impact_scope","team"),
                user_pain_level=data.get("user_pain_level","enhancement"),
                impact_frequency=data.get("impact_frequency","sometimes"),
                urgency_score=float(data.get("urgency_score",0.5)),
                estimated_timeline=data.get("estimated_timeline","quarter"),
                technical_complexity=data.get("technical_complexity","medium"),
                implementation_effort=data.get("implementation_effort","weeks"),
                business_value=data.get("business_value","efficiency"),
                competitive_advantage=data.get("competitive_advantage","parity"),
                strategic_alignment=data.get("strategic_alignment","important"),
                requirement_priority=data.get("requirement_priority","should_have"),
                confidence_score=float(data.get("confidence_score",0.6)),
            ).validate()
            if raw.strip() == "{}":
                return self._fallback_rules(research_text)
            return da
        except Exception:
            return self._fallback_rules(research_text)

    def _fallback_rules(self, text: str) -> DeepAnalysis:
        revenue = bool(re.search(r"营收|收入|revenue|增长|回升", text))
        ai = bool(re.search(r"大语言模型|ai|智能体|llm", text, re.I))
        overseas = bool(re.search(r"海外|欧洲|美国|全球|国际", text))
        risk = bool(re.search(r"价格战|竞争|诉讼|风险|库存|减值", text))
        impact_scope = "company" if (overseas or revenue) else "department"
        user_pain_level = "major_friction" if risk else "enhancement"
        impact_frequency = "often"
        urgency_score = 0.65 if risk else 0.55
        estimated_timeline = "quarter"
        technical_complexity = "high" if ai else "medium"
        implementation_effort = "months" if ai else "weeks"
        business_value = "revenue" if revenue else "efficiency"
        competitive_advantage = "differentiator" if ai else "parity"
        strategic_alignment = "core" if (ai or overseas) else "important"
        requirement_priority = "must_have" if (ai or revenue) else "should_have"
        confidence_score = 0.7 if (revenue or ai or overseas) else 0.55
        return DeepAnalysis(
            impact_scope=impact_scope,
            user_pain_level=user_pain_level,
            impact_frequency=impact_frequency,
            urgency_score=urgency_score,
            estimated_timeline=estimated_timeline,
            technical_complexity=technical_complexity,
            implementation_effort=implementation_effort,
            business_value=business_value,
            competitive_advantage=competitive_advantage,
            strategic_alignment=strategic_alignment,
            requirement_priority=requirement_priority,
            confidence_score=confidence_score
        ).validate()

# ============================== 4) 公司研究服务 ==============================

class CompanyResearchService:
    RESEARCH_PROMPT = """
你是一名产业与公司研究员。请围绕公司：{company}，
生成一份“深度研究稿”，要求：
- 结构：执行摘要 / 业务与产品 / 财务与现金流 / 市场竞争 / 技术与专利 / 风险与合规 / 展望与关键动作
- 语气：客观、可验证；突出关键数据（如同比/环比、份额、现金流、研发支出）
- 字数：1200-1800字
- 输出语言：中文
注意：如果你不确定事实，请使用“可能/推测/需验证”等表述，避免凭空捏造。
"""

    def __init__(self, text_client: GeminiTextClient):
        self.llm = text_client

    async def draft(self, company: str) -> str:
        prompt = self.RESEARCH_PROMPT.format(company=company)
        return await self.llm.generate(prompt)

# ============================== 5) 情感汇总器（Excel/CSV 5类或1-5星） ==============================

class SentimentAggregator:
    label_map = {
        # 中文
        "极负": -1.0, "非常消极": -1.0, "强烈负面": -1.0,
        "负面": -0.5, "消极": -0.5,
        "中性": 0.0,
        "正面": 0.5, "积极": 0.5,
        "极正": 1.0, "非常积极": 1.0, "强烈正面": 1.0,
        # 英文
        "very negative": -1.0, "vnegative": -1.0, "very_neg": -1.0,
        "negative": -0.5, "neg": -0.5,
        "neutral": 0.0,
        "positive": 0.5, "pos": 0.5,
        "very positive": 1.0, "vpositive": 1.0, "very_pos": 1.0
    }

    def __init__(self, path: str):
        self.path = path
        self.summary = None

    def _detect_label_col(self, df) -> str:
        candidates = ["label","sentiment","情感","情感标签","分类","预测","pred","prediction","预测标签","类别","情绪"]
        lower_cols = {c.lower(): c for c in df.columns}
        for c in candidates:
            if c in lower_cols:
                return lower_cols[c]
        for c in ["rating","stars","评分","星级","score","打分"]:
            if c in lower_cols:
                return lower_cols[c]
        return df.columns[0]

    def _label_to_score(self, v) -> Optional[float]:
        if v is None:
            return None
        s = str(v).strip().lower()
        if s in self.label_map:
            return self.label_map[s]
        try:
            f = float(s)
            if f <= 1.5: return -1.0
            if f <= 2.5: return -0.5
            if f <= 3.5: return  0.0
            if f <= 4.5: return  0.5
            return 1.0
        except Exception:
            return None

    def aggregate(self) -> Dict[str, Any]:
        try:
            import pandas as pd
        except Exception as e:
            raise RuntimeError("需要 pandas 才能解析情感文件，请先 pip install pandas openpyxl") from e
        if not os.path.exists(self.path):
            raise FileNotFoundError(self.path)
        try:
            if self.path.lower().endswith(".xlsx"):
                df = pd.read_excel(self.path, engine="openpyxl")
            else:
                df = pd.read_csv(self.path)
        except Exception:
            df = pd.read_excel(self.path)  # 再试一次默认engine
        col = self._detect_label_col(df)
        scores = []
        for v in df[col].tolist():
            sc = self._label_to_score(v)
            if sc is not None:
                scores.append(sc)
        n = len(scores)
        if n == 0:
            raise ValueError("无法从情感文件解析出有效标签")
        avg = sum(scores)/n
        mag = sum(abs(x) for x in scores)/n
        neg_share = sum(1 for x in scores if x < 0)/n
        pos_share = sum(1 for x in scores if x > 0)/n
        neu_share = 1 - neg_share - pos_share
        self.summary = {
            "count": n,
            "avg": avg,                # [-1,1]
            "magnitude": mag,          # [0,1]
            "neg_share": neg_share,
            "pos_share": pos_share,
            "neu_share": neu_share
        }
        return self.summary

# ============================== 6) 情感 × 研究 深度融合策略 ==============================

class SentimentFusionPolicy:
    RANKS = {
        "impact_scope": ["individual","team","department","company","ecosystem"],
        "user_pain_level": ["enhancement","minor_inconvenience","major_friction","blocker"],
        "impact_frequency": ["rarely","sometimes","often","always"],
        "estimated_timeline": ["roadmap","quarter","sprint","immediate"],
        "requirement_priority": ["wont_have","could_have","should_have","must_have"],
        "competitive_advantage": ["internal","parity","table_stakes","differentiator"],
    }

    @staticmethod
    def _rank(name, value):
        arr = SentimentFusionPolicy.RANKS[name]
        return arr.index(value) if value in arr else 0

    @staticmethod
    def _raise(name, value, steps=1):
        arr = SentimentFusionPolicy.RANKS[name]
        i = SentimentFusionPolicy._rank(name, value)
        return arr[min(i+steps, len(arr)-1)]

    @staticmethod
    def _max_by_rank(name, a, b):
        arr = SentimentFusionPolicy.RANKS[name]
        ia = arr.index(a) if a in arr else 0
        ib = arr.index(b) if b in arr else 0
        return a if ia >= ib else b

    def fuse(self, deep: DeepAnalysis, senti: dict, volume_thresholds=(100, 500)) -> Tuple[DeepAnalysis, float, float]:
        """
        :param deep: 研究得到的 deep_analysis
        :param senti: SentimentAggregator.aggregate() 的结果
        :param volume_thresholds: 评论量阈值 (team->department, department->company)
        :return: (fused_deep, user_voice_base(0~1), business_uplift(±分))
        """
        N   = int(senti.get("count", 0))
        avg = float(senti.get("avg", 0.0))
        mag = float(senti.get("magnitude", 0.0))
        neg = float(senti.get("neg_share", 0.0))
        pos = float(senti.get("pos_share", 0.0))

        # 1) 情感建议
        if neg >= 0.60 or (avg < -0.40 and mag > 0.60):
            pain_sug = "blocker"
        elif neg >= 0.40 or avg < -0.20:
            pain_sug = "major_friction"
        elif neg >= 0.20:
            pain_sug = "minor_inconvenience"
        else:
            pain_sug = "enhancement"

        if neg >= 0.60:   freq_sug = "always"
        elif neg >= 0.40: freq_sug = "often"
        elif neg >= 0.20: freq_sug = "sometimes"
        else:             freq_sug = "rarely"

        t_team2dept, t_dept2co = volume_thresholds
        if N >= t_dept2co:     scope_sug = "company"
        elif N >= t_team2dept: scope_sug = "department"
        elif N >= 1:           scope_sug = "team"
        else:                  scope_sug = "individual"

        urg_bump = 0.30*neg + 0.10*mag + 0.10*max(0.0, -avg)  # 最大约0.5
        fused_urg = max(0.0, min(1.0, deep.urgency_score + urg_bump))
        if fused_urg >= 0.85:      tl_sug = "immediate"
        elif fused_urg >= 0.70:    tl_sug = "sprint"
        else:                      tl_sug = deep.estimated_timeline

        rp = deep.requirement_priority
        if neg >= 0.70 or avg <= -0.50:
            rp_sug = self._raise("requirement_priority", rp, steps=2)
        elif neg >= 0.50 or avg <= -0.30:
            rp_sug = self._raise("requirement_priority", rp, steps=1)
        else:
            rp_sug = rp

        ca = deep.competitive_advantage
        if pos >= 0.60 and avg >= 0.20:
            ca_sug = "differentiator"
        elif neg >= 0.60 and avg <= -0.20:
            ca_sug = "parity" if self._rank("competitive_advantage", ca) > self._rank("competitive_advantage","parity") else ca
        else:
            ca_sug = ca

        # 2) 与研究合并（取更严重/更紧急）
        fused = replace(
            deep,
            user_pain_level=self._max_by_rank("user_pain_level", deep.user_pain_level, pain_sug),
            impact_frequency=self._max_by_rank("impact_frequency", deep.impact_frequency, freq_sug),
            impact_scope=self._max_by_rank("impact_scope", deep.impact_scope, scope_sug),
            urgency_score=fused_urg,
            estimated_timeline=self._max_by_rank("estimated_timeline", deep.estimated_timeline, tl_sug),
            requirement_priority=rp_sug,
            competitive_advantage=ca_sug,
        )

        # 3) user_voice & business 数值加成
        user_voice_base = max(0.0, min(1.0, 0.35 + 0.55*neg + 0.10*mag))
        business_uplift = 10.0 if pos >= 0.70 else (5.0 if pos >= 0.50 else 0.0)
        if business_uplift == 0.0 and (neg >= 0.60 and avg <= -0.20):
            business_uplift = -5.0

        return fused.validate(), user_voice_base, business_uplift

# ============================== 7) 高级优先级打分器（6维 + 总分 + 决策） ==============================

@dataclass
class PriorityScores:
    impact: float
    urgency: float
    effort: float
    business_value: float
    strategic: float
    user_voice: float
    overall_priority_score: float
    tier: str
    recommendation: str
    estimated_timeline: str

class AdvancedPriorityEngine:
    weights = {
        "impact": 0.25, "urgency": 0.20, "effort": 0.15,
        "business_value": 0.20, "strategic": 0.10, "user_voice": 0.10
    }
    scope_score = {"individual":20,"team":40,"department":60,"company":80,"ecosystem":100}
    pain_score = {"enhancement":25,"minor_inconvenience":40,"major_friction":70,"blocker":100}
    freq_mul = {"rarely":0.7,"sometimes":1.0,"often":1.3,"always":1.5}
    timeline_mul = {"immediate":1.5,"sprint":1.2,"quarter":1.0,"roadmap":0.8}
    complexity_score = {"low":25,"medium":50,"high":75,"very_high":100}
    effort_bucket = {"hours":20,"days":40,"weeks":70,"months":90}
    biz_base = {"efficiency":40,"retention":60,"acquisition":80,"revenue":100,"compliance":70}
    comp_adv_mul = {"differentiator":1.4,"table_stakes":1.2,"parity":1.0,"internal":0.8}
    strategic_map = {"off_strategy":20,"nice_to_have":40,"important":70,"core":100}
    require_map = {"wont_have":20,"could_have":40,"should_have":70,"must_have":100}

    def _clip(self, x: float, lo=0.0, hi=100.0) -> float:
        return max(lo, min(hi, float(x)))

    def score_impact(self, da: DeepAnalysis) -> float:
        s = (self.scope_score[da.impact_scope] + self.pain_score[da.user_pain_level]) / 2.0
        s *= self.freq_mul[da.impact_frequency]
        return self._clip(s)

    def score_urgency(self, da: DeepAnalysis) -> float:
        base = da.urgency_score * 100.0
        base *= self.timeline_mul[da.estimated_timeline]
        return self._clip(base)

    def score_effort(self, da: DeepAnalysis) -> float:
        comp = self.complexity_score[da.technical_complexity]
        eff = self.effort_bucket[da.implementation_effort]
        return self._clip((comp + eff) / 2.0)

    def score_business(self, da: DeepAnalysis) -> float:
        base = self.biz_base[da.business_value] * self.comp_adv_mul[da.competitive_advantage]
        return self._clip(base)

    def score_strategic(self, da: DeepAnalysis) -> float:
        return self._clip((self.strategic_map[da.strategic_alignment] + self.require_map[da.requirement_priority]) / 2.0)

    def score_user_voice(self, base_priority_score: float, is_vip=False, is_paid=False) -> float:
        mult = 1.0 + (0.3 if is_vip else 0.0) + (0.2 if is_paid else 0.0)
        return self._clip(base_priority_score * 100.0 * mult)

    def overall(self, impact, urgency, effort, business, strategic, user_voice) -> float:
        score = (
            impact * self.weights["impact"] +
            urgency * self.weights["urgency"] +
            (100.0 - effort) * self.weights["effort"] +  # effort 反向
            business * self.weights["business_value"] +
            strategic * self.weights["strategic"] +
            user_voice * self.weights["user_voice"]
        )
        return self._clip(score)

    def tier_and_reco(self, overall: float) -> Tuple[str, str, str]:
        if overall >= 85:  return "P0","立即推进：拉高资源优先级，目标本迭代内落地","immediate"
        if overall >= 70:  return "P1","优先规划：纳入当季计划，明确负责人与里程碑","sprint"
        if overall >= 50:  return "P2","评估排期：下季度推进，先做方案与原型验证","quarter"
        return "P3","观察跟踪：列入路线图，持续监测指标与风险","roadmap"

    def decide(self, da: DeepAnalysis, base_priority_score: float = 0.55,
               is_vip=False, is_paid=False, business_uplift: float = 0.0) -> PriorityScores:
        impact   = self.score_impact(da)
        urgency  = self.score_urgency(da)
        effort   = self.score_effort(da)
        business = min(100.0, self.score_business(da) + business_uplift)
        strategic = self.score_strategic(da)
        user_voice = self.score_user_voice(base_priority_score, is_vip, is_paid)
        overall = self.overall(impact, urgency, effort, business, strategic, user_voice)
        tier, reco, timeline = self.tier_and_reco(overall)
        return PriorityScores(impact, urgency, effort, business, strategic, user_voice,
                              overall, tier, reco, timeline)

# ============================== 8) 一条龙：公司名 -> 研究 -> deep_analysis -> 情感融合 -> 决策 ==============================

async def run_pipeline(company: str,
                       sentiment_path: Optional[str] = None,
                       force_mock: bool = False,
                       is_vip: bool = False,
                       is_paid: bool = True) -> Dict[str, Any]:

    # LLM
    api_key = os.getenv("GOOGLE_API_KEY", "").strip() or None
    text_client = GeminiTextClient(api_key=api_key, force_mock=force_mock or not api_key)
    json_client = GeminiJSONClient(api_key=api_key, force_mock=force_mock or not api_key)

    # 1) 公司研究
    research_service = CompanyResearchService(text_client)
    research_text = await research_service.draft(company)

    # 2) 研究 -> deep_analysis
    extractor = ResearchExtractor(json_client)
    deep = await extractor.to_deep_analysis(research_text)

    # 3) 情感深度融合（可选）
    sentiment_summary = None
    base_priority_score = 0.55
    business_uplift = 0.0
    if sentiment_path:
        try:
            aggr = SentimentAggregator(sentiment_path)
            sentiment_summary = aggr.aggregate()
            fusion = SentimentFusionPolicy()
            deep, base_priority_score, business_uplift = fusion.fuse(deep, sentiment_summary)
        except Exception as e:
            sentiment_summary = {"error": f"读取/解析情感文件失败：{e}"}

    # 4) 决策打分
    engine = AdvancedPriorityEngine()
    scores = engine.decide(
        da=deep,
        base_priority_score=base_priority_score,
        is_vip=is_vip,
        is_paid=is_paid,
        business_uplift=business_uplift
    )

    # 5) 输出
    return {
        "company": company,
        "research_text_preview": research_text[:400] + ("..." if len(research_text) > 400 else ""),
        "deep_analysis": asdict(deep),
        "sentiment_summary": sentiment_summary,  # None 或包含 count/avg/magnitude/neg_share/pos_share/neu_share
        "scores": asdict(scores)
    }

# ============================== 9) CLI ==============================

def pretty(d: Dict[str, Any]) -> str:
    return json.dumps(d, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="公司研究 -> DeepAnalysis -> 情感深度融合 -> 决策（独立可运行）")
    parser.add_argument("company", type=str, help="公司名称，例如：科沃斯机器人股份有限公司")
    parser.add_argument("--sentiment", type=str, default=None, help="情感结果文件路径（xlsx/csv），5分类或1~5星")
    parser.add_argument("--mock", action="store_true", help="强制使用本地mock（不调用外部API）")
    parser.add_argument("--vip", action="store_true", help="是否VIP用户（影响user_voice乘数）")
    parser.add_argument("--paid", action="store_true", help="是否付费用户（影响user_voice乘数）")
    args = parser.parse_args()

    result = asyncio.run(run_pipeline(
        company=args.company,
        sentiment_path=args.sentiment,
        force_mock=args.mock,
        is_vip=args.vip,
        is_paid=(True if args.paid else False)
    ))
    print(pretty(result))
