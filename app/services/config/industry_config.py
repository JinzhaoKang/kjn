"""
行业配置管理器
支持不同行业的关键词库、权重配置、业务规则定制化
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class IndustryType(str, Enum):
    """行业类型枚举"""
    # 科技行业
    SOFTWARE = "software"           # 软件应用
    GAMING = "gaming"              # 游戏行业
    ECOMMERCE = "ecommerce"        # 电商平台
    FINTECH = "fintech"            # 金融科技
    
    # 传统行业
    RETAIL = "retail"              # 零售业
    HEALTHCARE = "healthcare"      # 医疗健康
    EDUCATION = "education"        # 教育培训
    TRAVEL = "travel"              # 旅游出行
    
    # 服务行业
    FOOD = "food"                  # 餐饮外卖
    BEAUTY = "beauty"              # 美妆护肤
    FITNESS = "fitness"            # 健身运动
    ENTERTAINMENT = "entertainment" # 娱乐影音
    
    # 通用配置
    GENERAL = "general"            # 通用配置

@dataclass
class KeywordConfig:
    """关键词配置"""
    bug_keywords: List[str]
    feature_keywords: List[str]
    performance_keywords: List[str]
    ui_ux_keywords: List[str]
    security_keywords: List[str]
    integration_keywords: List[str]
    urgency_keywords: List[str]
    positive_keywords: List[str]
    negative_keywords: List[str]

@dataclass
class WeightConfig:
    """权重配置"""
    content_quality: float = 0.25
    sentiment_intensity: float = 0.20
    business_relevance: float = 0.20
    urgency_indicators: float = 0.15
    user_value: float = 0.10
    novelty: float = 0.10

@dataclass
class BusinessRules:
    """业务规则配置"""
    min_content_length: int = 10
    max_content_length: int = 1000
    llm_processing_threshold: float = 0.7
    high_priority_threshold: float = 0.8
    batch_size: int = 100
    retention_days: int = 365

@dataclass
class IndustryConfig:
    """行业配置模型"""
    industry: IndustryType
    name: str
    description: str
    keywords: KeywordConfig
    weights: WeightConfig
    rules: BusinessRules
    custom_fields: Dict[str, Any] = None

class IndustryConfigManager:
    """行业配置管理器"""
    
    def __init__(self, config_dir: str = "configs/industries"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.configs: Dict[IndustryType, IndustryConfig] = {}
        self.current_industry: Optional[IndustryType] = None
        
        # 初始化默认配置
        self._load_default_configs()
        self._load_custom_configs()
    
    def _load_custom_configs(self):
        """加载自定义配置文件"""
        try:
            for config_file in self.config_dir.glob("*.json"):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    industry = IndustryType(config_data['industry'])
                    
                    # 解析配置数据
                    config = IndustryConfig(
                        industry=industry,
                        name=config_data['name'],
                        description=config_data['description'],
                        keywords=KeywordConfig(**config_data['keywords']),
                        weights=WeightConfig(**config_data['weights']),
                        rules=BusinessRules(**config_data['rules']),
                        custom_fields=config_data.get('custom_fields')
                    )
                    
                    self.configs[industry] = config
                    logger.info(f"加载自定义配置: {industry.value}")
                    
        except Exception as e:
            logger.error(f"加载自定义配置失败: {e}")
    
    def _load_default_configs(self):
        """加载默认行业配置"""
        default_configs = {
            IndustryType.SOFTWARE: self._create_software_config(),
            IndustryType.GAMING: self._create_gaming_config(),
            IndustryType.ECOMMERCE: self._create_ecommerce_config(),
            IndustryType.FINTECH: self._create_fintech_config(),
            IndustryType.GENERAL: self._create_general_config()
        }
        
        self.configs.update(default_configs)
    
    def _create_software_config(self) -> IndustryConfig:
        """软件应用行业配置"""
        return IndustryConfig(
            industry=IndustryType.SOFTWARE,
            name="软件应用",
            description="移动应用、桌面软件、SaaS平台等",
            keywords=KeywordConfig(
                bug_keywords=["崩溃", "闪退", "卡死", "无响应", "白屏", "黑屏", "异常", "错误", "故障", "bug"],
                feature_keywords=["功能", "需求", "建议", "希望", "增加", "新增", "改进", "优化", "完善"],
                performance_keywords=["慢", "卡", "延迟", "响应", "加载", "速度", "流畅", "性能", "内存", "耗电"],
                ui_ux_keywords=["界面", "设计", "布局", "颜色", "字体", "操作", "体验", "交互", "美观", "易用"],
                security_keywords=["安全", "隐私", "权限", "泄露", "保护", "加密", "认证", "授权"],
                integration_keywords=["集成", "兼容", "同步", "导入", "导出", "API", "第三方", "插件"],
                urgency_keywords=["紧急", "严重", "重要", "关键", "阻塞", "无法使用", "影响工作", "损失", "立即", "马上"],
                positive_keywords=["好用", "方便", "简单", "快速", "稳定", "完美", "优秀", "满意", "推荐", "赞"],
                negative_keywords=["难用", "复杂", "麻烦", "失望", "糟糕", "垃圾", "差劲", "无用", "后悔"]
            ),
            weights=WeightConfig(
                content_quality=0.25,
                sentiment_intensity=0.20,
                business_relevance=0.20,
                urgency_indicators=0.15,
                user_value=0.10,
                novelty=0.10
            ),
            rules=BusinessRules(
                min_content_length=10,
                max_content_length=1000,
                llm_processing_threshold=0.7,
                high_priority_threshold=0.8,
                batch_size=100,
                retention_days=365
            )
        )
    
    def _create_gaming_config(self) -> IndustryConfig:
        """游戏行业配置"""
        return IndustryConfig(
            industry=IndustryType.GAMING,
            name="游戏行业",
            description="手机游戏、PC游戏、主机游戏等",
            keywords=KeywordConfig(
                bug_keywords=["掉线", "卡顿", "闪退", "黑屏", "无法登录", "进不去", "卡关", "异常"],
                feature_keywords=["玩法", "模式", "角色", "装备", "技能", "关卡", "活动", "更新"],
                performance_keywords=["帧率", "延迟", "网络", "加载", "流畅", "优化", "发热", "耗电"],
                ui_ux_keywords=["界面", "操作", "手感", "画质", "音效", "设置", "菜单", "按钮"],
                security_keywords=["外挂", "作弊", "封号", "安全", "防沉迷", "实名"],
                integration_keywords=["社交", "好友", "公会", "排行榜", "分享", "直播"],
                urgency_keywords=["无法游戏", "充值问题", "数据丢失", "账号异常", "紧急", "严重"],
                positive_keywords=["好玩", "有趣", "刺激", "精彩", "爽快", "完美", "优秀", "推荐"],
                negative_keywords=["无聊", "坑钱", "垃圾", "糟糕", "失望", "后悔", "删游戏"]
            ),
            weights=WeightConfig(
                content_quality=0.20,
                sentiment_intensity=0.25,
                business_relevance=0.25,
                urgency_indicators=0.15,
                user_value=0.10,
                novelty=0.05
            ),
            rules=BusinessRules(
                min_content_length=5,
                max_content_length=500,
                llm_processing_threshold=0.6,
                high_priority_threshold=0.7,
                batch_size=200,
                retention_days=180
            )
        )
    
    def _create_ecommerce_config(self) -> IndustryConfig:
        """电商平台配置"""
        return IndustryConfig(
            industry=IndustryType.ECOMMERCE,
            name="电商平台",
            description="淘宝、京东、拼多多等电商平台",
            keywords=KeywordConfig(
                bug_keywords=["付款失败", "下单异常", "无法支付", "订单问题", "系统错误"],
                feature_keywords=["搜索", "推荐", "购物车", "收藏", "比价", "优惠券", "活动"],
                performance_keywords=["加载慢", "卡顿", "响应慢", "网络问题", "打开慢"],
                ui_ux_keywords=["界面", "操作", "导航", "分类", "筛选", "排序", "展示"],
                security_keywords=["支付安全", "信息泄露", "假货", "欺诈", "退款", "维权"],
                integration_keywords=["物流", "支付", "客服", "评价", "分享", "比价"],
                urgency_keywords=["无法下单", "支付问题", "订单异常", "退款延迟", "紧急"],
                positive_keywords=["便宜", "方便", "快速", "优质", "满意", "推荐", "好评"],
                negative_keywords=["贵", "假货", "慢", "差", "骗人", "垃圾", "差评"]
            ),
            weights=WeightConfig(
                content_quality=0.20,
                sentiment_intensity=0.30,
                business_relevance=0.25,
                urgency_indicators=0.15,
                user_value=0.05,
                novelty=0.05
            ),
            rules=BusinessRules(
                min_content_length=5,
                max_content_length=200,
                llm_processing_threshold=0.5,
                high_priority_threshold=0.6,
                batch_size=500,
                retention_days=90
            )
        )
    
    def _create_fintech_config(self) -> IndustryConfig:
        """金融科技配置"""
        return IndustryConfig(
            industry=IndustryType.FINTECH,
            name="金融科技",
            description="支付、理财、银行、保险等金融应用",
            keywords=KeywordConfig(
                bug_keywords=["转账失败", "登录异常", "验证码", "系统维护", "网络异常"],
                feature_keywords=["转账", "理财", "信贷", "保险", "查询", "统计", "分析"],
                performance_keywords=["响应慢", "加载慢", "超时", "卡顿", "网络"],
                ui_ux_keywords=["界面", "操作", "流程", "引导", "提示", "确认"],
                security_keywords=["安全", "密码", "验证", "风控", "防欺诈", "加密", "隐私"],
                integration_keywords=["银行卡", "第三方支付", "征信", "接口", "同步"],
                urgency_keywords=["资金安全", "交易异常", "账户冻结", "紧急", "重要"],
                positive_keywords=["安全", "方便", "快速", "稳定", "专业", "可靠"],
                negative_keywords=["不安全", "复杂", "麻烦", "风险", "担心", "怀疑"]
            ),
            weights=WeightConfig(
                content_quality=0.30,
                sentiment_intensity=0.15,
                business_relevance=0.25,
                urgency_indicators=0.20,
                user_value=0.05,
                novelty=0.05
            ),
            rules=BusinessRules(
                min_content_length=10,
                max_content_length=500,
                llm_processing_threshold=0.8,
                high_priority_threshold=0.9,
                batch_size=50,
                retention_days=730
            )
        )
    
    def _create_general_config(self) -> IndustryConfig:
        """通用配置"""
        return IndustryConfig(
            industry=IndustryType.GENERAL,
            name="通用配置",
            description="适用于所有行业的通用配置",
            keywords=KeywordConfig(
                bug_keywords=["问题", "错误", "异常", "故障", "失败"],
                feature_keywords=["功能", "需求", "建议", "希望", "改进"],
                performance_keywords=["慢", "卡", "延迟", "性能"],
                ui_ux_keywords=["界面", "操作", "体验", "设计"],
                security_keywords=["安全", "隐私", "保护"],
                integration_keywords=["集成", "兼容", "同步"],
                urgency_keywords=["紧急", "重要", "严重"],
                positive_keywords=["好", "满意", "推荐", "优秀"],
                negative_keywords=["差", "失望", "糟糕", "垃圾"]
            ),
            weights=WeightConfig(),
            rules=BusinessRules()
        )
    
    def get_config(self, industry: IndustryType) -> IndustryConfig:
        """获取指定行业配置"""
        return self.configs.get(industry, self.configs[IndustryType.GENERAL])
    
    def set_current_industry(self, industry: IndustryType):
        """设置当前行业"""
        self.current_industry = industry
        logger.info(f"切换到行业配置: {industry.value}")
    
    def get_current_config(self) -> IndustryConfig:
        """获取当前行业配置"""
        if self.current_industry:
            return self.get_config(self.current_industry)
        return self.configs[IndustryType.GENERAL]
    
    def save_config(self, config: IndustryConfig):
        """保存配置到文件"""
        try:
            config_file = self.config_dir / f"{config.industry.value}.json"
            config_dict = asdict(config)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            
            # 更新内存中的配置
            self.configs[config.industry] = config
            logger.info(f"保存配置成功: {config.industry.value}")
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise
    
    def get_available_industries(self) -> List[Dict[str, str]]:
        """获取可用的行业列表"""
        return [
            {
                "value": industry.value,
                "name": config.name,
                "description": config.description
            }
            for industry, config in self.configs.items()
        ]
    
    def create_custom_industry(self, 
                             industry_id: str,
                             name: str, 
                             description: str,
                             base_industry: IndustryType = IndustryType.GENERAL) -> IndustryConfig:
        """创建自定义行业配置"""
        # 基于现有配置创建
        base_config = self.get_config(base_industry)
        
        # 创建新配置
        custom_config = IndustryConfig(
            industry=IndustryType(industry_id),
            name=name,
            description=description,
            keywords=base_config.keywords,
            weights=base_config.weights,
            rules=base_config.rules
        )
        
        # 保存配置
        self.save_config(custom_config)
        
        return custom_config

# 全局配置管理器实例
industry_config_manager = IndustryConfigManager()

def get_industry_config_manager() -> IndustryConfigManager:
    """获取行业配置管理器实例"""
    return industry_config_manager 