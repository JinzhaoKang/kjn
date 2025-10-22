"""
地理位置和国家/地区模型
支持全球化数据标记和地区化配置
"""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel
from dataclasses import dataclass

class CountryCode(str, Enum):
    """ISO 3166-1 alpha-2 国家代码"""
    # 亚洲主要国家
    CHINA = "CN"              # 中国
    HONG_KONG = "HK"          # 香港
    TAIWAN = "TW"             # 台湾
    MACAO = "MO"              # 澳门
    JAPAN = "JP"              # 日本
    SOUTH_KOREA = "KR"        # 韩国
    SINGAPORE = "SG"          # 新加坡
    MALAYSIA = "MY"           # 马来西亚
    THAILAND = "TH"           # 泰国
    VIETNAM = "VN"            # 越南
    PHILIPPINES = "PH"        # 菲律宾
    INDONESIA = "ID"          # 印度尼西亚
    INDIA = "IN"              # 印度
    
    # 欧洲主要国家
    UNITED_KINGDOM = "GB"     # 英国
    GERMANY = "DE"            # 德国
    FRANCE = "FR"             # 法国
    ITALY = "IT"              # 意大利
    SPAIN = "ES"              # 西班牙
    NETHERLANDS = "NL"        # 荷兰
    SWEDEN = "SE"             # 瑞典
    NORWAY = "NO"             # 挪威
    FINLAND = "FI"            # 芬兰
    DENMARK = "DK"            # 丹麦
    SWITZERLAND = "CH"        # 瑞士
    AUSTRIA = "AT"            # 奥地利
    BELGIUM = "BE"            # 比利时
    POLAND = "PL"             # 波兰
    PORTUGAL = "PT"           # 葡萄牙
    RUSSIA = "RU"             # 俄罗斯
    
    # 北美洲
    UNITED_STATES = "US"      # 美国
    CANADA = "CA"             # 加拿大
    MEXICO = "MX"             # 墨西哥
    
    # 南美洲
    BRAZIL = "BR"             # 巴西
    ARGENTINA = "AR"          # 阿根廷
    CHILE = "CL"              # 智利
    COLOMBIA = "CO"           # 哥伦比亚
    
    # 大洋洲
    AUSTRALIA = "AU"          # 澳大利亚
    NEW_ZEALAND = "NZ"        # 新西兰
    
    # 非洲
    SOUTH_AFRICA = "ZA"       # 南非
    EGYPT = "EG"              # 埃及
    NIGERIA = "NG"            # 尼日利亚
    
    # 中东
    ISRAEL = "IL"             # 以色列
    SAUDI_ARABIA = "SA"       # 沙特阿拉伯
    UAE = "AE"                # 阿联酋
    TURKEY = "TR"             # 土耳其
    
    # 未知/其他
    UNKNOWN = "XX"            # 未知国家

class RegionCode(str, Enum):
    """地区分类代码"""
    # 亚太地区
    ASIA_PACIFIC = "APAC"     # 亚太地区
    EAST_ASIA = "EA"          # 东亚
    SOUTHEAST_ASIA = "SEA"    # 东南亚
    SOUTH_ASIA = "SA"         # 南亚
    
    # 欧洲
    EUROPE = "EU"             # 欧洲
    WESTERN_EUROPE = "WE"     # 西欧
    EASTERN_EUROPE = "EE"     # 东欧
    NORTHERN_EUROPE = "NE"    # 北欧
    SOUTHERN_EUROPE = "SE"    # 南欧
    
    # 美洲
    AMERICAS = "AM"           # 美洲
    NORTH_AMERICA = "NA"      # 北美
    SOUTH_AMERICA = "SA"      # 南美
    CENTRAL_AMERICA = "CA"    # 中美
    
    # 其他地区
    MIDDLE_EAST = "ME"        # 中东
    AFRICA = "AF"             # 非洲
    OCEANIA = "OC"            # 大洋洲
    
    # 全球
    GLOBAL = "GL"             # 全球

class LanguageCode(str, Enum):
    """ISO 639-1 语言代码"""
    # 中文系
    CHINESE_SIMPLIFIED = "zh-CN"    # 简体中文
    CHINESE_TRADITIONAL = "zh-TW"   # 繁体中文
    CHINESE_HONG_KONG = "zh-HK"     # 香港中文
    
    # 其他亚洲语言
    JAPANESE = "ja"                 # 日语
    KOREAN = "ko"                   # 韩语
    THAI = "th"                     # 泰语
    VIETNAMESE = "vi"               # 越南语
    MALAY = "ms"                    # 马来语
    INDONESIAN = "id"               # 印尼语
    HINDI = "hi"                    # 印地语
    
    # 欧洲语言
    ENGLISH = "en"                  # 英语
    GERMAN = "de"                   # 德语
    FRENCH = "fr"                   # 法语
    SPANISH = "es"                  # 西班牙语
    ITALIAN = "it"                  # 意大利语
    PORTUGUESE = "pt"               # 葡萄牙语
    DUTCH = "nl"                    # 荷兰语
    SWEDISH = "sv"                  # 瑞典语
    NORWEGIAN = "no"                # 挪威语
    FINNISH = "fi"                  # 芬兰语
    DANISH = "da"                   # 丹麦语
    POLISH = "pl"                   # 波兰语
    RUSSIAN = "ru"                  # 俄语
    
    # 中东语言
    ARABIC = "ar"                   # 阿拉伯语
    HEBREW = "he"                   # 希伯来语
    TURKISH = "tr"                  # 土耳其语
    
    # 其他
    UNKNOWN = "xx"                  # 未知语言

@dataclass
class CountryInfo:
    """国家信息"""
    code: CountryCode
    name_en: str
    name_local: str
    region: RegionCode
    primary_language: LanguageCode
    supported_languages: List[LanguageCode]
    timezone_offset: float  # UTC偏移小时数
    currency: str
    phone_code: str

class GeographicalInfo(BaseModel):
    """地理位置信息"""
    country_code: CountryCode = CountryCode.UNKNOWN
    country_name: str = "未知"
    region_code: RegionCode = RegionCode.GLOBAL
    region_name: str = "全球"
    detected_language: LanguageCode = LanguageCode.UNKNOWN
    timezone_offset: Optional[float] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    ip_address: Optional[str] = None
    
    # 检测置信度
    detection_confidence: float = 0.0
    detection_method: str = "unknown"  # ip, language, platform, manual

class GeographicalManager:
    """地理位置管理器"""
    
    def __init__(self):
        self.country_mappings = self._init_country_mappings()
        self.platform_country_mappings = self._init_platform_mappings()
        self.language_country_mappings = self._init_language_mappings()
    
    def _init_country_mappings(self) -> Dict[CountryCode, CountryInfo]:
        """初始化国家信息映射"""
        return {
            CountryCode.CHINA: CountryInfo(
                code=CountryCode.CHINA,
                name_en="China",
                name_local="中国",
                region=RegionCode.EAST_ASIA,
                primary_language=LanguageCode.CHINESE_SIMPLIFIED,
                supported_languages=[LanguageCode.CHINESE_SIMPLIFIED],
                timezone_offset=8.0,
                currency="CNY",
                phone_code="+86"
            ),
            CountryCode.HONG_KONG: CountryInfo(
                code=CountryCode.HONG_KONG,
                name_en="Hong Kong",
                name_local="香港",
                region=RegionCode.EAST_ASIA,
                primary_language=LanguageCode.CHINESE_TRADITIONAL,
                supported_languages=[LanguageCode.CHINESE_TRADITIONAL, LanguageCode.ENGLISH],
                timezone_offset=8.0,
                currency="HKD",
                phone_code="+852"
            ),
            CountryCode.TAIWAN: CountryInfo(
                code=CountryCode.TAIWAN,
                name_en="Taiwan",
                name_local="台湾",
                region=RegionCode.EAST_ASIA,
                primary_language=LanguageCode.CHINESE_TRADITIONAL,
                supported_languages=[LanguageCode.CHINESE_TRADITIONAL],
                timezone_offset=8.0,
                currency="TWD",
                phone_code="+886"
            ),
            CountryCode.JAPAN: CountryInfo(
                code=CountryCode.JAPAN,
                name_en="Japan",
                name_local="日本",
                region=RegionCode.EAST_ASIA,
                primary_language=LanguageCode.JAPANESE,
                supported_languages=[LanguageCode.JAPANESE],
                timezone_offset=9.0,
                currency="JPY",
                phone_code="+81"
            ),
            CountryCode.SOUTH_KOREA: CountryInfo(
                code=CountryCode.SOUTH_KOREA,
                name_en="South Korea",
                name_local="대한민국",
                region=RegionCode.EAST_ASIA,
                primary_language=LanguageCode.KOREAN,
                supported_languages=[LanguageCode.KOREAN],
                timezone_offset=9.0,
                currency="KRW",
                phone_code="+82"
            ),
            CountryCode.UNITED_STATES: CountryInfo(
                code=CountryCode.UNITED_STATES,
                name_en="United States",
                name_local="United States",
                region=RegionCode.NORTH_AMERICA,
                primary_language=LanguageCode.ENGLISH,
                supported_languages=[LanguageCode.ENGLISH, LanguageCode.SPANISH],
                timezone_offset=-5.0,  # EST
                currency="USD",
                phone_code="+1"
            ),
            CountryCode.UNITED_KINGDOM: CountryInfo(
                code=CountryCode.UNITED_KINGDOM,
                name_en="United Kingdom",
                name_local="United Kingdom",
                region=RegionCode.WESTERN_EUROPE,
                primary_language=LanguageCode.ENGLISH,
                supported_languages=[LanguageCode.ENGLISH],
                timezone_offset=0.0,  # GMT
                currency="GBP",
                phone_code="+44"
            ),
            # 可以继续添加更多国家...
        }
    
    def _init_platform_mappings(self) -> Dict[str, List[CountryCode]]:
        """初始化平台与国家的映射关系"""
        return {
            # 中国平台
            "xiaohongshu": [CountryCode.CHINA, CountryCode.HONG_KONG, CountryCode.TAIWAN],
            "douyin": [CountryCode.CHINA],
            "weibo": [CountryCode.CHINA, CountryCode.HONG_KONG, CountryCode.TAIWAN],
            "bilibili": [CountryCode.CHINA, CountryCode.HONG_KONG, CountryCode.TAIWAN],
            "taobao": [CountryCode.CHINA, CountryCode.HONG_KONG, CountryCode.TAIWAN],
            "jingdong": [CountryCode.CHINA],
            "pinduoduo": [CountryCode.CHINA],
            "tmall": [CountryCode.CHINA, CountryCode.HONG_KONG],
            
            # 国际平台
            "app_store": [CountryCode.UNITED_STATES, CountryCode.UNITED_KINGDOM, CountryCode.JAPAN, 
                         CountryCode.SOUTH_KOREA, CountryCode.CHINA, CountryCode.GERMANY, 
                         CountryCode.FRANCE, CountryCode.AUSTRALIA],
            "google_play": [CountryCode.UNITED_STATES, CountryCode.UNITED_KINGDOM, CountryCode.GERMANY,
                           CountryCode.FRANCE, CountryCode.JAPAN, CountryCode.SOUTH_KOREA,
                           CountryCode.INDIA, CountryCode.BRAZIL],
            
            # 华为生态
            "huawei_store": [CountryCode.CHINA, CountryCode.GERMANY, CountryCode.UNITED_KINGDOM,
                            CountryCode.FRANCE, CountryCode.SPAIN, CountryCode.ITALY],
            
            # 其他亚洲平台
            "xiaomi_store": [CountryCode.CHINA, CountryCode.INDIA, CountryCode.INDONESIA],
            "oppo_store": [CountryCode.CHINA, CountryCode.INDONESIA, CountryCode.THAILAND],
            "vivo_store": [CountryCode.CHINA, CountryCode.INDIA, CountryCode.INDONESIA],
            "samsung_store": [CountryCode.SOUTH_KOREA, CountryCode.UNITED_STATES, CountryCode.GERMANY]
        }
    
    def _init_language_mappings(self) -> Dict[LanguageCode, List[CountryCode]]:
        """初始化语言与国家的映射关系"""
        return {
            LanguageCode.CHINESE_SIMPLIFIED: [CountryCode.CHINA, CountryCode.SINGAPORE],
            LanguageCode.CHINESE_TRADITIONAL: [CountryCode.TAIWAN, CountryCode.HONG_KONG, CountryCode.MACAO],
            LanguageCode.ENGLISH: [CountryCode.UNITED_STATES, CountryCode.UNITED_KINGDOM, 
                                 CountryCode.CANADA, CountryCode.AUSTRALIA, CountryCode.NEW_ZEALAND,
                                 CountryCode.SINGAPORE, CountryCode.SOUTH_AFRICA],
            LanguageCode.JAPANESE: [CountryCode.JAPAN],
            LanguageCode.KOREAN: [CountryCode.SOUTH_KOREA],
            LanguageCode.GERMAN: [CountryCode.GERMANY, CountryCode.AUSTRIA, CountryCode.SWITZERLAND],
            LanguageCode.FRENCH: [CountryCode.FRANCE, CountryCode.CANADA, CountryCode.BELGIUM],
            LanguageCode.SPANISH: [CountryCode.SPAIN, CountryCode.MEXICO, CountryCode.ARGENTINA, 
                                 CountryCode.COLOMBIA, CountryCode.CHILE],
            LanguageCode.PORTUGUESE: [CountryCode.BRAZIL, CountryCode.PORTUGAL],
            LanguageCode.RUSSIAN: [CountryCode.RUSSIA],
            LanguageCode.ARABIC: [CountryCode.SAUDI_ARABIA, CountryCode.UAE, CountryCode.EGYPT]
        }
    
    def detect_country_from_platform(self, platform_name: str) -> List[CountryCode]:
        """根据平台名称检测可能的国家"""
        platform_key = platform_name.lower().replace(" ", "_").replace("-", "_")
        return self.platform_country_mappings.get(platform_key, [CountryCode.UNKNOWN])
    
    def detect_country_from_language(self, language: LanguageCode) -> List[CountryCode]:
        """根据语言检测可能的国家"""
        return self.language_country_mappings.get(language, [CountryCode.UNKNOWN])
    
    def detect_language_from_text(self, text: str) -> LanguageCode:
        """从文本内容检测语言（简单实现）"""
        if not text:
            return LanguageCode.UNKNOWN
        
        # 检测中文
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        if chinese_chars > len(text) * 0.3:
            # 进一步区分简繁体
            simplified_indicators = ['的', '了', '是', '在', '有', '和']
            traditional_indicators = ['的', '了', '是', '在', '有', '和', '這', '個', '們']
            
            simplified_count = sum(1 for indicator in simplified_indicators if indicator in text)
            traditional_count = sum(1 for indicator in traditional_indicators if indicator in text)
            
            if traditional_count > simplified_count:
                return LanguageCode.CHINESE_TRADITIONAL
            else:
                return LanguageCode.CHINESE_SIMPLIFIED
        
        # 检测日文
        hiragana_katakana = sum(1 for char in text if 
                               ('\u3040' <= char <= '\u309f') or  # 平假名
                               ('\u30a0' <= char <= '\u30ff'))    # 片假名
        if hiragana_katakana > 0:
            return LanguageCode.JAPANESE
        
        # 检测韩文
        hangul = sum(1 for char in text if '\uac00' <= char <= '\ud7af')
        if hangul > 0:
            return LanguageCode.KOREAN
        
        # 检测阿拉伯文
        arabic = sum(1 for char in text if '\u0600' <= char <= '\u06ff')
        if arabic > 0:
            return LanguageCode.ARABIC
        
        # 默认为英文
        return LanguageCode.ENGLISH
    
    def get_geographical_info(self, 
                            platform_name: str = None,
                            text_content: str = None,
                            ip_address: str = None,
                            explicit_country: CountryCode = None) -> GeographicalInfo:
        """综合检测地理位置信息"""
        
        geo_info = GeographicalInfo()
        confidence_scores = {}
        
        # 1. 显式指定的国家（最高优先级）
        if explicit_country and explicit_country != CountryCode.UNKNOWN:
            geo_info.country_code = explicit_country
            geo_info.detection_method = "manual"
            geo_info.detection_confidence = 1.0
        
        # 2. 基于平台检测
        elif platform_name:
            possible_countries = self.detect_country_from_platform(platform_name)
            if possible_countries and possible_countries[0] != CountryCode.UNKNOWN:
                geo_info.country_code = possible_countries[0]
                geo_info.detection_method = "platform"
                geo_info.detection_confidence = 0.8
        
        # 3. 基于语言检测
        elif text_content:
            detected_language = self.detect_language_from_text(text_content)
            geo_info.detected_language = detected_language
            
            possible_countries = self.detect_country_from_language(detected_language)
            if possible_countries and possible_countries[0] != CountryCode.UNKNOWN:
                geo_info.country_code = possible_countries[0]
                geo_info.detection_method = "language"
                geo_info.detection_confidence = 0.6
        
        # 4. 基于IP地址检测（需要第三方服务）
        elif ip_address:
            # 这里可以集成IP地理位置服务
            geo_info.ip_address = ip_address
            geo_info.detection_method = "ip"
            geo_info.detection_confidence = 0.4
        
        # 填充国家信息
        if geo_info.country_code in self.country_mappings:
            country_info = self.country_mappings[geo_info.country_code]
            geo_info.country_name = country_info.name_local
            geo_info.region_code = country_info.region
            geo_info.region_name = self._get_region_name(country_info.region)
            geo_info.timezone_offset = country_info.timezone_offset
            
            if geo_info.detected_language == LanguageCode.UNKNOWN:
                geo_info.detected_language = country_info.primary_language
        
        return geo_info
    
    def _get_region_name(self, region_code: RegionCode) -> str:
        """获取地区中文名称"""
        region_names = {
            RegionCode.EAST_ASIA: "东亚",
            RegionCode.SOUTHEAST_ASIA: "东南亚",
            RegionCode.SOUTH_ASIA: "南亚",
            RegionCode.WESTERN_EUROPE: "西欧",
            RegionCode.EASTERN_EUROPE: "东欧",
            RegionCode.NORTHERN_EUROPE: "北欧",
            RegionCode.SOUTHERN_EUROPE: "南欧",
            RegionCode.NORTH_AMERICA: "北美",
            RegionCode.SOUTH_AMERICA: "南美",
            RegionCode.MIDDLE_EAST: "中东",
            RegionCode.AFRICA: "非洲",
            RegionCode.OCEANIA: "大洋洲",
            RegionCode.GLOBAL: "全球"
        }
        return region_names.get(region_code, "未知地区")
    
    def get_supported_countries(self) -> List[Dict[str, str]]:
        """获取支持的国家列表"""
        return [
            {
                "code": country_info.code.value,
                "name_en": country_info.name_en,
                "name_local": country_info.name_local,
                "region": country_info.region.value,
                "language": country_info.primary_language.value
            }
            for country_info in self.country_mappings.values()
        ]

# 全局地理位置管理器
geographical_manager = GeographicalManager()

def get_geographical_manager() -> GeographicalManager:
    """获取地理位置管理器实例"""
    return geographical_manager 