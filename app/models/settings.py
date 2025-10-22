from pydantic import BaseModel, Field
from typing import Optional, List

class DatabaseSettings(BaseModel):
    host: str = "localhost"
    port: int = 27017

class SystemSettings(BaseModel):
    systemName: str = "用户反馈分析系统"
    description: str = "基于AI的用户反馈智能分析平台"
    timezone: str = "Asia/Shanghai"
    language: str = "zh-CN"
    dataRetentionDays: int = 365
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

class LLMSettings(BaseModel):
    enabled: bool = True
    model: str = "gpt-4"
    apiKey: Optional[str] = ""
    base_url: Optional[str] = ""
    temperature: float = 0.3
    maxTokens: int = 2000
    theturbo_api_key: str = "sk-iDcLuIYX3aRWWuIMBvjfH62w3Aqdz7NvrtIVdrAMpmAF0IiI"
    theturbo_base_url: str = "https://gateway.theturbo.ai/v1"

class PriorityWeights(BaseModel):
    userImpact: float = 0.4
    complexity: float = 0.3
    businessValue: float = 0.3

class PrioritySettings(BaseModel):
    enabled: bool = True
    weights: PriorityWeights = Field(default_factory=PriorityWeights)

class AnalysisSettings(BaseModel):
    enabled: bool = True
    threshold: float = 0.7
    llm: LLMSettings = Field(default_factory=LLMSettings)
    priority: PrioritySettings = Field(default_factory=PrioritySettings)

class EmailSettings(BaseModel):
    enabled: bool = True
    smtpHost: str = "smtp.gmail.com"
    smtpPort: int = 587
    username: Optional[str] = ""
    password: Optional[str] = ""
    fromEmail: Optional[str] = ""

class NotificationRules(BaseModel):
    newFeedback: bool = True
    highPriority: bool = True
    analysisComplete: bool = False
    reportGenerated: bool = True

class NotificationSettings(BaseModel):
    email: EmailSettings = Field(default_factory=EmailSettings)
    rules: NotificationRules = Field(default_factory=NotificationRules)

class PasswordPolicy(BaseModel):
    minLength: int = 8
    requireUppercase: bool = True
    requireLowercase: bool = True
    requireNumbers: bool = True
    requireSpecialChars: bool = False

class SessionSettings(BaseModel):
    timeout: int = 30
    rememberLogin: bool = True

class SecuritySettings(BaseModel):
    password: PasswordPolicy = Field(default_factory=PasswordPolicy)
    session: SessionSettings = Field(default_factory=SessionSettings)

class AppSettings(BaseModel):
    system: SystemSettings = Field(default_factory=SystemSettings)
    analysis: AnalysisSettings = Field(default_factory=AnalysisSettings)
    notification: NotificationSettings = Field(default_factory=NotificationSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

class SettingsInDB(BaseModel):
    id: str = "global"
    settings: AppSettings = Field(default_factory=AppSettings)
