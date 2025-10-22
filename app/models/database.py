"""
MongoDB文档模型定义
包含用户反馈和产品问题的文档结构
"""
from beanie import Document, Indexed
from pydantic import Field, BaseModel
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum
from bson import ObjectId


class FeedbackSource(str, Enum):
    """反馈来源枚举"""
    APP_STORE = "app_store"
    GOOGLE_PLAY = "google_play" 
    ZENDESK = "zendesk"
    SOCIAL_MEDIA = "social_media"
    USER_SURVEY = "user_survey"
    INTERNAL = "internal"


class IssueStatus(str, Enum):
    """问题状态枚举"""
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    REJECTED = "Rejected"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EffortLevel(str, Enum):
    """工作量级别枚举"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class UserFeedback(Document):
    """用户反馈文档 - 存储原始反馈和LLM分析结果"""
    
    # 基础内容字段（兼容旧数据）
    content: Optional[str] = Field(None, description="处理后的内容")
    original_content: Optional[str] = Field(None, description="原始反馈文本")
    original_text: Optional[str] = Field(None, description="原始反馈文本(兼容旧版)")
    processed_text: Optional[str] = Field(None, description="预处理后的文本(兼容旧版)")
    
    # 数据源信息
    source: FeedbackSource = Field(FeedbackSource.INTERNAL, description="数据源")
    source_platform: Optional[str] = Field("未知平台", description="来源平台")
    original_id: Optional[str] = Field(None, description="原始平台ID")
    url: Optional[str] = Field(None, description="原始链接")
    
    # 时间信息
    feedback_time: Optional[datetime] = Field(None, description="反馈时间")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    published_at: Optional[datetime] = Field(None, description="发布时间")
    crawled_at: Optional[datetime] = Field(None, description="爬取时间")
    
    # 用户和产品信息
    user_id: Optional[str] = Field(None, description="用户ID")
    user_info: Optional[Dict[str, Any]] = Field(None, description="用户信息")
    product_info: Optional[Dict[str, Any]] = Field(None, description="产品信息")
    
    # 地理和语言信息
    geographical_info: Optional[Dict[str, Any]] = Field(None, description="地理信息")
    language: Optional[str] = Field(None, description="语言")
    
    # 平台元数据
    platform_metadata: Optional[Dict[str, Any]] = Field(None, description="平台相关元数据")
    
    # 质量和处理信息
    quality_score: Optional[float] = Field(None, description="质量评分")
    processing_metadata: Optional[Dict[str, Any]] = Field(None, description="处理元数据")
    processing_status: Optional[Dict[str, Any]] = Field(None, description="处理状态")
    
    # AI分析结果
    sentiment: Optional[str] = Field(None, description="情感分析结果")
    category: Optional[str] = Field(None, description="分类结果")
    keywords: List[str] = Field(default_factory=list, description="关键词")
    priority: Optional[str] = Field(None, description="优先级")
    ai_confidence: Optional[float] = Field(None, description="AI置信度")
    
    # LLM分析结果 (兼容旧版)
    analysis_result: Optional[Dict[str, Any]] = Field(None, description="LLM分析结果")
    
    # 任务和数据血缘
    task_metadata: Optional[Dict[str, Any]] = Field(None, description="任务元数据")
    data_lineage: Optional[Dict[str, Any]] = Field(None, description="数据血缘")
    
    # 状态控制字段
    is_processed: bool = Field(default=False, description="是否已处理")
    needs_llm_analysis: bool = Field(default=True, description="是否需要LLM分析")
    
    # 智能筛选相关字段
    filter_score: Optional[float] = Field(None, description="智能筛选评分")
    filter_reason: Optional[str] = Field(None, description="筛选决策原因")
    
    class Settings:
        name = "user_feedback"
        indexes = [
            [("source", 1)],
            [("source_platform", 1)],
            [("created_at", -1)],
            [("feedback_time", -1)],
            [("is_processed", 1)],
            [("needs_llm_analysis", 1)],
            [("user_id", 1)],
            [("original_id", 1)],
            [("sentiment", 1)],
            [("category", 1)],
            [("priority", 1)],
            [("quality_score", -1)],
            [("language", 1)],
            [("processing_status.ai_analyzed", 1)],
            [("processing_status.needs_ai_analysis", 1)],
            [("crawled_at", -1)],
        ]
    
    def get_sentiment(self) -> Optional[str]:
        """获取情感分析结果"""
        if self.analysis_result:
            return self.analysis_result.get("sentiment")
        return None
    
    def get_topics(self) -> List[str]:
        """获取主题列表"""
        if self.analysis_result:
            return self.analysis_result.get("topics", [])
        return []
    
    def get_sentiment_score(self) -> Optional[float]:
        """获取情感分数"""
        if self.analysis_result:
            return self.analysis_result.get("sentiment_score")
        return None
    
    def get_urgency_score(self) -> Optional[float]:
        """获取紧急度分数"""
        if self.analysis_result:
            return self.analysis_result.get("urgency_score")
        return None


class ProductIssue(Document):
    """产品问题文档 - 存储聚合后的问题卡片"""
    
    # 基础字段
    issue_theme: str = Field(..., description="问题主题")
    issue_summary: Optional[str] = Field(None, description="LLM生成的问题总体描述")
    
    # 统计指标
    feedback_count: int = Field(default=0, description="反馈总次数")
    affected_users: Optional[int] = Field(None, description="影响的用户数")
    avg_sentiment_score: Optional[float] = Field(None, description="平均情感得分")
    avg_urgency_score: Optional[float] = Field(None, description="平均紧急度得分")
    
    # 时间字段
    first_seen: Optional[datetime] = Field(None, description="首次发现时间")
    last_seen: Optional[datetime] = Field(None, description="最后发现时间")
    
    # 优先级和状态
    priority_score: Optional[float] = Field(None, description="优先级得分")
    status: IssueStatus = Field(default=IssueStatus.OPEN, description="状态")
    
    # 决策支持字段
    estimated_effort: Optional[EffortLevel] = Field(None, description="预估工作量")
    business_impact: Optional[EffortLevel] = Field(None, description="业务影响")
    technical_complexity: Optional[EffortLevel] = Field(None, description="技术复杂度")
    
    # 关联字段
    related_feedback_ids: List[str] = Field(default_factory=list, description="关联的反馈ID列表")
    assignee: Optional[str] = Field(None, description="负责人")
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    
    # 高级分析字段
    pps_score: Optional[float] = Field(None, description="PPS优先级评分")
    expected_roi: Optional[float] = Field(None, description="预期投资回报率")
    action_items: Optional[List[Dict[str, Any]]] = Field(None, description="生成的行动项")
    
    class Settings:
        name = "product_issues"
        indexes = [
            [("priority_score", -1)],
            [("created_at", -1)],
            [("status", 1)],
            [("assignee", 1)],
            [("issue_theme", 1)],
        ]
    
    def calculate_priority_score(self, weights: Dict[str, float]) -> float:
        """根据权重计算优先级得分"""
        import math
        
        # 基础计算公式
        feedback_score = math.log(max(self.feedback_count, 1)) * weights.get("feedback_count", 0.4)
        sentiment_score = abs(self.avg_sentiment_score or 0) * weights.get("sentiment_score", 0.3)
        urgency_score = (self.avg_urgency_score or 0) * weights.get("urgency_score", 0.3)
        
        return feedback_score + sentiment_score + urgency_score
    
    def update_timestamps(self, feedback_time: datetime):
        """更新时间戳"""
        if not self.first_seen or feedback_time < self.first_seen:
            self.first_seen = feedback_time
        if not self.last_seen or feedback_time > self.last_seen:
            self.last_seen = feedback_time
        self.updated_at = datetime.utcnow()


# 分析任务模型
class AnalysisTask(BaseModel):
    """分析任务模型"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    feedback_id: str = Field(..., description="关联的反馈ID")
    status: str = Field(default="pending", description="任务状态：pending, running, completed, failed, paused")
    analysis_mode: str = Field(default="full", description="分析模式：full, quick, deep")
    priority: str = Field(default="normal", description="优先级：low, normal, high, urgent")
    current_module: str = Field(default="preprocessing", description="当前执行的模块")
    progress: int = Field(default=0, description="进度百分比")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "forbid"


class AnalysisResult(BaseModel):
    """分析结果模型"""
    task_id: str = Field(..., description="任务ID")
    preprocessing: Optional[Dict[str, Any]] = None
    llm_analysis: Optional[Dict[str, Any]] = None
    priority_assessment: Optional[Dict[str, Any]] = None
    action_recommendations: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "forbid"


# 统计和报告相关的辅助模型
class FeedbackStats(BaseModel):
    """反馈统计模型"""
    total_count: int
    processed_count: int
    by_source: Dict[str, int]
    by_sentiment: Dict[str, int]
    avg_sentiment_score: float
    avg_urgency_score: float


class IssueStats(BaseModel):
    """问题统计模型"""
    total_count: int
    by_status: Dict[str, int]
    by_priority: Dict[str, int]
    avg_priority_score: float
    top_issues: List[Dict[str, Any]] 