"""
行业配置管理API
提供行业配置的增删改查功能
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..services.config.industry_config import (
    get_industry_config_manager, IndustryConfig, IndustryType,
    KeywordConfig, WeightConfig, BusinessRules
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/industry-config", tags=["行业配置"])

class IndustryConfigResponse(BaseModel):
    """行业配置响应"""
    industry: str
    name: str
    description: str
    keywords: Dict[str, List[str]]
    weights: Dict[str, float]
    rules: Dict[str, Any]
    custom_fields: Optional[Dict[str, Any]] = None

class IndustryConfigRequest(BaseModel):
    """行业配置请求"""
    name: str
    description: str
    keywords: Dict[str, List[str]]
    weights: Dict[str, float]
    rules: Dict[str, Any]
    custom_fields: Optional[Dict[str, Any]] = None

class IndustrySummary(BaseModel):
    """行业概要"""
    industry: str
    name: str
    description: str
    is_current: bool = False

@router.get("/industries", response_model=List[IndustrySummary])
async def get_available_industries():
    """获取可用的行业列表"""
    try:
        config_manager = get_industry_config_manager()
        current_config = config_manager.get_current_config()
        
        industries = []
        for industry_data in config_manager.get_available_industries():
            industries.append(IndustrySummary(
                industry=industry_data["value"],
                name=industry_data["name"],
                description=industry_data["description"],
                is_current=(industry_data["value"] == current_config.industry.value)
            ))
        
        return industries
        
    except Exception as e:
        logger.error(f"获取行业列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/industries/{industry_type}", response_model=IndustryConfigResponse)
async def get_industry_config(industry_type: IndustryType):
    """获取指定行业配置"""
    try:
        config_manager = get_industry_config_manager()
        config = config_manager.get_config(industry_type)
        
        return IndustryConfigResponse(
            industry=config.industry.value,
            name=config.name,
            description=config.description,
            keywords={
                "bug_keywords": config.keywords.bug_keywords,
                "feature_keywords": config.keywords.feature_keywords,
                "performance_keywords": config.keywords.performance_keywords,
                "ui_ux_keywords": config.keywords.ui_ux_keywords,
                "security_keywords": config.keywords.security_keywords,
                "integration_keywords": config.keywords.integration_keywords,
                "urgency_keywords": config.keywords.urgency_keywords,
                "positive_keywords": config.keywords.positive_keywords,
                "negative_keywords": config.keywords.negative_keywords
            },
            weights={
                "content_quality": config.weights.content_quality,
                "sentiment_intensity": config.weights.sentiment_intensity,
                "business_relevance": config.weights.business_relevance,
                "urgency_indicators": config.weights.urgency_indicators,
                "user_value": config.weights.user_value,
                "novelty": config.weights.novelty
            },
            rules={
                "min_content_length": config.rules.min_content_length,
                "max_content_length": config.rules.max_content_length,
                "llm_processing_threshold": config.rules.llm_processing_threshold,
                "high_priority_threshold": config.rules.high_priority_threshold,
                "batch_size": config.rules.batch_size,
                "retention_days": config.rules.retention_days
            },
            custom_fields=config.custom_fields
        )
        
    except Exception as e:
        logger.error(f"获取行业配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/current", response_model=IndustryConfigResponse)
async def get_current_industry_config():
    """获取当前行业配置"""
    try:
        config_manager = get_industry_config_manager()
        config = config_manager.get_current_config()
        
        return IndustryConfigResponse(
            industry=config.industry.value,
            name=config.name,
            description=config.description,
            keywords={
                "bug_keywords": config.keywords.bug_keywords,
                "feature_keywords": config.keywords.feature_keywords,
                "performance_keywords": config.keywords.performance_keywords,
                "ui_ux_keywords": config.keywords.ui_ux_keywords,
                "security_keywords": config.keywords.security_keywords,
                "integration_keywords": config.keywords.integration_keywords,
                "urgency_keywords": config.keywords.urgency_keywords,
                "positive_keywords": config.keywords.positive_keywords,
                "negative_keywords": config.keywords.negative_keywords
            },
            weights={
                "content_quality": config.weights.content_quality,
                "sentiment_intensity": config.weights.sentiment_intensity,
                "business_relevance": config.weights.business_relevance,
                "urgency_indicators": config.weights.urgency_indicators,
                "user_value": config.weights.user_value,
                "novelty": config.weights.novelty
            },
            rules={
                "min_content_length": config.rules.min_content_length,
                "max_content_length": config.rules.max_content_length,
                "llm_processing_threshold": config.rules.llm_processing_threshold,
                "high_priority_threshold": config.rules.high_priority_threshold,
                "batch_size": config.rules.batch_size,
                "retention_days": config.rules.retention_days
            },
            custom_fields=config.custom_fields
        )
        
    except Exception as e:
        logger.error(f"获取当前行业配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/current/{industry_type}")
async def set_current_industry(industry_type: IndustryType):
    """设置当前行业"""
    try:
        config_manager = get_industry_config_manager()
        config_manager.set_current_industry(industry_type)
        
        return {
            "success": True,
            "message": f"已切换到行业配置: {industry_type.value}",
            "current_industry": industry_type.value
        }
        
    except Exception as e:
        logger.error(f"设置当前行业失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/industries/{industry_type}", response_model=IndustryConfigResponse)
async def update_industry_config(industry_type: IndustryType, request: IndustryConfigRequest):
    """更新行业配置"""
    try:
        config_manager = get_industry_config_manager()
        
        # 构建新的配置
        keywords_config = KeywordConfig(
            bug_keywords=request.keywords.get("bug_keywords", []),
            feature_keywords=request.keywords.get("feature_keywords", []),
            performance_keywords=request.keywords.get("performance_keywords", []),
            ui_ux_keywords=request.keywords.get("ui_ux_keywords", []),
            security_keywords=request.keywords.get("security_keywords", []),
            integration_keywords=request.keywords.get("integration_keywords", []),
            urgency_keywords=request.keywords.get("urgency_keywords", []),
            positive_keywords=request.keywords.get("positive_keywords", []),
            negative_keywords=request.keywords.get("negative_keywords", [])
        )
        
        weights_config = WeightConfig(
            content_quality=request.weights.get("content_quality", 0.25),
            sentiment_intensity=request.weights.get("sentiment_intensity", 0.20),
            business_relevance=request.weights.get("business_relevance", 0.20),
            urgency_indicators=request.weights.get("urgency_indicators", 0.15),
            user_value=request.weights.get("user_value", 0.10),
            novelty=request.weights.get("novelty", 0.10)
        )
        
        rules_config = BusinessRules(
            min_content_length=request.rules.get("min_content_length", 10),
            max_content_length=request.rules.get("max_content_length", 1000),
            llm_processing_threshold=request.rules.get("llm_processing_threshold", 0.7),
            high_priority_threshold=request.rules.get("high_priority_threshold", 0.8),
            batch_size=request.rules.get("batch_size", 100),
            retention_days=request.rules.get("retention_days", 365)
        )
        
        # 创建新配置
        new_config = IndustryConfig(
            industry=industry_type,
            name=request.name,
            description=request.description,
            keywords=keywords_config,
            weights=weights_config,
            rules=rules_config,
            custom_fields=request.custom_fields
        )
        
        # 保存配置
        config_manager.save_config(new_config)
        
        # 返回更新后的配置
        return await get_industry_config(industry_type)
        
    except Exception as e:
        logger.error(f"更新行业配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/industries/custom")
async def create_custom_industry(
    industry_id: str,
    request: IndustryConfigRequest,
    base_industry: IndustryType = IndustryType.GENERAL
):
    """创建自定义行业配置"""
    try:
        config_manager = get_industry_config_manager()
        
        # 创建自定义配置
        custom_config = config_manager.create_custom_industry(
            industry_id=industry_id,
            name=request.name,
            description=request.description,
            base_industry=base_industry
        )
        
        # 更新配置内容
        custom_config.keywords = KeywordConfig(
            bug_keywords=request.keywords.get("bug_keywords", []),
            feature_keywords=request.keywords.get("feature_keywords", []),
            performance_keywords=request.keywords.get("performance_keywords", []),
            ui_ux_keywords=request.keywords.get("ui_ux_keywords", []),
            security_keywords=request.keywords.get("security_keywords", []),
            integration_keywords=request.keywords.get("integration_keywords", []),
            urgency_keywords=request.keywords.get("urgency_keywords", []),
            positive_keywords=request.keywords.get("positive_keywords", []),
            negative_keywords=request.keywords.get("negative_keywords", [])
        )
        
        custom_config.weights = WeightConfig(
            content_quality=request.weights.get("content_quality", 0.25),
            sentiment_intensity=request.weights.get("sentiment_intensity", 0.20),
            business_relevance=request.weights.get("business_relevance", 0.20),
            urgency_indicators=request.weights.get("urgency_indicators", 0.15),
            user_value=request.weights.get("user_value", 0.10),
            novelty=request.weights.get("novelty", 0.10)
        )
        
        custom_config.rules = BusinessRules(
            min_content_length=request.rules.get("min_content_length", 10),
            max_content_length=request.rules.get("max_content_length", 1000),
            llm_processing_threshold=request.rules.get("llm_processing_threshold", 0.7),
            high_priority_threshold=request.rules.get("high_priority_threshold", 0.8),
            batch_size=request.rules.get("batch_size", 100),
            retention_days=request.rules.get("retention_days", 365)
        )
        
        custom_config.custom_fields = request.custom_fields
        
        # 保存配置
        config_manager.save_config(custom_config)
        
        return {
            "success": True,
            "message": f"自定义行业配置创建成功: {industry_id}",
            "industry_id": industry_id
        }
        
    except Exception as e:
        logger.error(f"创建自定义行业配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def get_industry_templates():
    """获取行业配置模板"""
    try:
        templates = []
        
        # 软件应用模板
        templates.append({
            "industry": "software",
            "name": "软件应用",
            "description": "移动应用、桌面软件、SaaS平台等",
            "template": {
                "keywords": {
                    "bug_keywords": ["崩溃", "闪退", "卡死", "无响应", "白屏", "黑屏", "异常", "错误", "故障", "bug"],
                    "feature_keywords": ["功能", "需求", "建议", "希望", "增加", "新增", "改进", "优化", "完善"],
                    "performance_keywords": ["慢", "卡", "延迟", "响应", "加载", "速度", "流畅", "性能", "内存", "耗电"],
                    "ui_ux_keywords": ["界面", "设计", "布局", "颜色", "字体", "操作", "体验", "交互", "美观", "易用"],
                    "security_keywords": ["安全", "隐私", "权限", "泄露", "保护", "加密", "认证", "授权"],
                    "integration_keywords": ["集成", "兼容", "同步", "导入", "导出", "API", "第三方", "插件"],
                    "urgency_keywords": ["紧急", "严重", "重要", "关键", "阻塞", "无法使用", "影响工作", "损失", "立即", "马上"],
                    "positive_keywords": ["好用", "方便", "简单", "快速", "稳定", "完美", "优秀", "满意", "推荐", "赞"],
                    "negative_keywords": ["难用", "复杂", "麻烦", "失望", "糟糕", "垃圾", "差劲", "无用", "后悔"]
                },
                "weights": {
                    "content_quality": 0.25,
                    "sentiment_intensity": 0.20,
                    "business_relevance": 0.20,
                    "urgency_indicators": 0.15,
                    "user_value": 0.10,
                    "novelty": 0.10
                },
                "rules": {
                    "min_content_length": 10,
                    "max_content_length": 1000,
                    "llm_processing_threshold": 0.7,
                    "high_priority_threshold": 0.8,
                    "batch_size": 100,
                    "retention_days": 365
                }
            }
        })
        
        # 电商平台模板
        templates.append({
            "industry": "ecommerce",
            "name": "电商平台",
            "description": "淘宝、京东、拼多多等电商平台",
            "template": {
                "keywords": {
                    "bug_keywords": ["付款失败", "下单异常", "无法支付", "订单问题", "系统错误"],
                    "feature_keywords": ["搜索", "推荐", "购物车", "收藏", "比价", "优惠券", "活动"],
                    "performance_keywords": ["加载慢", "卡顿", "响应慢", "网络问题", "打开慢"],
                    "ui_ux_keywords": ["界面", "操作", "导航", "分类", "筛选", "排序", "展示"],
                    "security_keywords": ["支付安全", "信息泄露", "假货", "欺诈", "退款", "维权"],
                    "integration_keywords": ["物流", "支付", "客服", "评价", "分享", "比价"],
                    "urgency_keywords": ["无法下单", "支付问题", "订单异常", "退款延迟", "紧急"],
                    "positive_keywords": ["便宜", "方便", "快速", "优质", "满意", "推荐", "好评"],
                    "negative_keywords": ["贵", "假货", "慢", "差", "骗人", "垃圾", "差评"]
                },
                "weights": {
                    "content_quality": 0.20,
                    "sentiment_intensity": 0.30,
                    "business_relevance": 0.25,
                    "urgency_indicators": 0.15,
                    "user_value": 0.05,
                    "novelty": 0.05
                },
                "rules": {
                    "min_content_length": 5,
                    "max_content_length": 200,
                    "llm_processing_threshold": 0.5,
                    "high_priority_threshold": 0.6,
                    "batch_size": 500,
                    "retention_days": 90
                }
            }
        })
        
        return {"templates": templates}
        
    except Exception as e:
        logger.error(f"获取行业模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 