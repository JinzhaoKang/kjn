"""
地理位置管理API
提供国家/地区相关的查询和管理功能
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from app.models.geographical import (
    CountryCode, RegionCode, LanguageCode, GeographicalInfo,
    get_geographical_manager
)
from app.models.data_source import FeedbackData
from beanie import PydanticObjectId
from beanie.operators import In, Eq

router = APIRouter(prefix="/geographical", tags=["地理位置管理"])

class CountryStatsResponse(BaseModel):
    """国家统计响应"""
    country_code: CountryCode
    country_name: str
    region_code: RegionCode
    region_name: str
    feedback_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    avg_priority: float
    primary_language: LanguageCode

class RegionStatsResponse(BaseModel):
    """地区统计响应"""
    region_code: RegionCode
    region_name: str
    countries: List[CountryStatsResponse]
    total_feedback_count: int
    avg_quality_score: float

class GeographicalFilterRequest(BaseModel):
    """地理位置筛选请求"""
    countries: Optional[List[CountryCode]] = None
    regions: Optional[List[RegionCode]] = None
    languages: Optional[List[LanguageCode]] = None
    exclude_unknown: bool = True

@router.get("/countries", response_model=List[Dict[str, str]])
async def get_supported_countries():
    """获取支持的国家列表"""
    geo_manager = get_geographical_manager()
    return geo_manager.get_supported_countries()

@router.get("/regions", response_model=List[Dict[str, str]])
async def get_supported_regions():
    """获取支持的地区列表"""
    return [
        {"code": "APAC", "name": "亚太地区"},
        {"code": "EA", "name": "东亚"},
        {"code": "SEA", "name": "东南亚"},
        {"code": "SA", "name": "南亚"},
        {"code": "EU", "name": "欧洲"},
        {"code": "WE", "name": "西欧"},
        {"code": "EE", "name": "东欧"},
        {"code": "NE", "name": "北欧"},
        {"code": "SE", "name": "南欧"},
        {"code": "AM", "name": "美洲"},
        {"code": "NA", "name": "北美"},
        {"code": "SA", "name": "南美"},
        {"code": "ME", "name": "中东"},
        {"code": "AF", "name": "非洲"},
        {"code": "OC", "name": "大洋洲"},
        {"code": "GL", "name": "全球"}
    ]

@router.get("/languages", response_model=List[Dict[str, str]])
async def get_supported_languages():
    """获取支持的语言列表"""
    return [
        {"code": "zh-CN", "name": "简体中文"},
        {"code": "zh-TW", "name": "繁体中文"},
        {"code": "zh-HK", "name": "香港中文"},
        {"code": "en", "name": "英语"},
        {"code": "ja", "name": "日语"},
        {"code": "ko", "name": "韩语"},
        {"code": "de", "name": "德语"},
        {"code": "fr", "name": "法语"},
        {"code": "es", "name": "西班牙语"},
        {"code": "it", "name": "意大利语"},
        {"code": "pt", "name": "葡萄牙语"},
        {"code": "ru", "name": "俄语"},
        {"code": "ar", "name": "阿拉伯语"},
        {"code": "th", "name": "泰语"},
        {"code": "vi", "name": "越南语"},
        {"code": "hi", "name": "印地语"}
    ]

@router.get("/stats/countries", response_model=List[CountryStatsResponse])
async def get_country_statistics(
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("feedback_count", regex="^(feedback_count|positive_count|negative_count|avg_priority)$")
):
    """获取国家统计数据"""
    try:
        # 聚合查询
        pipeline = [
            {
                "$group": {
                    "_id": "$geographical_info.country_code",
                    "country_name": {"$first": "$geographical_info.country_name"},
                    "region_code": {"$first": "$geographical_info.region_code"},
                    "region_name": {"$first": "$geographical_info.region_name"},
                    "feedback_count": {"$sum": 1},
                    "positive_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$sentiment", "positive"]}, 1, 0]
                        }
                    },
                    "negative_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$sentiment", "negative"]}, 1, 0]
                        }
                    },
                    "neutral_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$sentiment", "neutral"]}, 1, 0]
                        }
                    },
                    "avg_priority": {"$avg": "$priority_score"},
                    "primary_language": {"$first": "$geographical_info.detected_language"}
                }
            },
            {
                "$match": {
                    "_id": {"$ne": "XX"}  # 排除未知国家
                }
            },
            {
                "$sort": {sort_by: -1}
            },
            {
                "$limit": limit
            }
        ]
        
        results = await FeedbackData.aggregate(pipeline).to_list()
        
        country_stats = []
        for result in results:
            country_stats.append(CountryStatsResponse(
                country_code=result["_id"],
                country_name=result.get("country_name", "未知"),
                region_code=result.get("region_code", "GL"),
                region_name=result.get("region_name", "全球"),
                feedback_count=result["feedback_count"],
                positive_count=result["positive_count"],
                negative_count=result["negative_count"],
                neutral_count=result["neutral_count"],
                avg_priority=result.get("avg_priority", 0.0),
                primary_language=result.get("primary_language", "xx")
            ))
        
        return country_stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取国家统计失败: {str(e)}")

@router.get("/stats/regions", response_model=List[RegionStatsResponse])
async def get_region_statistics():
    """获取地区统计数据"""
    try:
        # 聚合查询 - 按地区分组
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "region_code": "$geographical_info.region_code",
                        "country_code": "$geographical_info.country_code"
                    },
                    "region_name": {"$first": "$geographical_info.region_name"},
                    "country_name": {"$first": "$geographical_info.country_name"},
                    "feedback_count": {"$sum": 1},
                    "positive_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$sentiment", "positive"]}, 1, 0]
                        }
                    },
                    "negative_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$sentiment", "negative"]}, 1, 0]
                        }
                    },
                    "neutral_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$sentiment", "neutral"]}, 1, 0]
                        }
                    },
                    "avg_quality": {"$avg": "$quality_score"},
                    "primary_language": {"$first": "$geographical_info.detected_language"}
                }
            },
            {
                "$match": {
                    "_id.region_code": {"$ne": "GL"},  # 排除全球
                    "_id.country_code": {"$ne": "XX"}  # 排除未知国家
                }
            },
            {
                "$group": {
                    "_id": "$_id.region_code",
                    "region_name": {"$first": "$region_name"},
                    "countries": {
                        "$push": {
                            "country_code": "$_id.country_code",
                            "country_name": "$country_name",
                            "feedback_count": "$feedback_count",
                            "positive_count": "$positive_count",
                            "negative_count": "$negative_count",
                            "neutral_count": "$neutral_count",
                            "primary_language": "$primary_language"
                        }
                    },
                    "total_feedback_count": {"$sum": "$feedback_count"},
                    "avg_quality_score": {"$avg": "$avg_quality"}
                }
            },
            {
                "$sort": {"total_feedback_count": -1}
            }
        ]
        
        results = await FeedbackData.aggregate(pipeline).to_list()
        
        region_stats = []
        for result in results:
            countries = []
            for country in result["countries"]:
                countries.append(CountryStatsResponse(
                    country_code=country["country_code"],
                    country_name=country["country_name"],
                    region_code=result["_id"],
                    region_name=result["region_name"],
                    feedback_count=country["feedback_count"],
                    positive_count=country["positive_count"],
                    negative_count=country["negative_count"],
                    neutral_count=country["neutral_count"],
                    avg_priority=0.0,  # 这里可以进一步计算
                    primary_language=country["primary_language"]
                ))
            
            region_stats.append(RegionStatsResponse(
                region_code=result["_id"],
                region_name=result["region_name"],
                countries=countries,
                total_feedback_count=result["total_feedback_count"],
                avg_quality_score=result.get("avg_quality_score", 0.0)
            ))
        
        return region_stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取地区统计失败: {str(e)}")

@router.post("/filter")
async def filter_feedback_by_geography(
    filter_request: GeographicalFilterRequest,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """根据地理位置筛选反馈数据"""
    try:
        # 构建查询条件
        query_conditions = []
        
        # 国家筛选
        if filter_request.countries:
            query_conditions.append(In(FeedbackData.geographical_info.country_code, filter_request.countries))
        
        # 地区筛选
        if filter_request.regions:
            query_conditions.append(In(FeedbackData.geographical_info.region_code, filter_request.regions))
        
        # 语言筛选
        if filter_request.languages:
            query_conditions.append(In(FeedbackData.geographical_info.detected_language, filter_request.languages))
        
        # 排除未知
        if filter_request.exclude_unknown:
            query_conditions.append(FeedbackData.geographical_info.country_code != CountryCode.UNKNOWN)
        
        # 执行查询
        if query_conditions:
            feedback_list = await FeedbackData.find(*query_conditions).skip(skip).limit(limit).to_list()
            total_count = await FeedbackData.find(*query_conditions).count()
        else:
            feedback_list = await FeedbackData.find_all().skip(skip).limit(limit).to_list()
            total_count = await FeedbackData.find_all().count()
        
        return {
            "data": feedback_list,
            "total_count": total_count,
            "page_size": limit,
            "page": skip // limit + 1,
            "total_pages": (total_count + limit - 1) // limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"地理位置筛选失败: {str(e)}")

@router.get("/detect/{text}")
async def detect_geographical_info_from_text(text: str):
    """从文本检测地理位置信息"""
    try:
        geo_manager = get_geographical_manager()
        geo_info = geo_manager.get_geographical_info(text_content=text)
        
        return {
            "geographical_info": geo_info,
            "detection_details": {
                "detected_language": geo_info.detected_language,
                "confidence": geo_info.detection_confidence,
                "method": geo_info.detection_method
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"地理位置检测失败: {str(e)}")

@router.get("/platform/{platform_name}")
async def get_platform_countries(platform_name: str):
    """获取平台支持的国家列表"""
    geo_manager = get_geographical_manager()
    countries = geo_manager.detect_country_from_platform(platform_name)
    
    if not countries or countries[0] == CountryCode.UNKNOWN:
        return {"message": f"平台 {platform_name} 不在支持列表中"}
    
    result = []
    for country_code in countries:
        if country_code in geo_manager.country_mappings:
            country_info = geo_manager.country_mappings[country_code]
            result.append({
                "code": country_info.code.value,
                "name": country_info.name_local,
                "region": country_info.region.value,
                "language": country_info.primary_language.value
            })
    
    return {"platform": platform_name, "supported_countries": result} 