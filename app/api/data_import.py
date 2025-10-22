"""
数据导入API
支持多种数据源的反馈数据批量导入
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel, Field

from ..models.data_source import (
    FeedbackData, DataSourceType, DataSourceConfig, DataSourceStats
)
from ..services.data_ingestion.data_source_adapters import get_adapter_registry
from ..services.config.industry_config import get_industry_config_manager, IndustryType
from ..services.preprocessing.intelligent_filter import intelligent_filter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/data-import", tags=["数据导入"])

class ImportRequest(BaseModel):
    """数据导入请求"""
    source_type: DataSourceType
    industry_type: Optional[IndustryType] = IndustryType.GENERAL
    data: List[Dict[str, Any]]
    batch_name: Optional[str] = None
    description: Optional[str] = None

class ImportResponse(BaseModel):
    """数据导入响应"""
    batch_id: str
    total_count: int
    success_count: int
    failed_count: int
    processing_time: float
    failed_items: List[Dict[str, Any]] = Field(default_factory=list)

class DataSourceStatus(BaseModel):
    """数据源状态"""
    source_type: DataSourceType
    platform_name: str
    is_active: bool
    total_records: int
    last_import_time: Optional[datetime] = None
    success_rate: Optional[float] = None

@router.post("/import-batch", response_model=ImportResponse)
async def import_data_batch(request: ImportRequest):
    """批量导入反馈数据"""
    start_time = datetime.now()
    
    try:
        # 设置行业配置
        config_manager = get_industry_config_manager()
        config_manager.set_current_industry(request.industry_type)
        
        # 获取数据适配器
        adapter_registry = get_adapter_registry()
        adapter = adapter_registry.get_adapter(request.source_type)
        
        if not adapter:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的数据源类型: {request.source_type.value}"
            )
        
        # 生成批次ID
        batch_id = f"import_{request.source_type.value}_{int(datetime.now().timestamp())}"
        
        success_count = 0
        failed_count = 0
        failed_items = []
        
        # 批量处理数据
        for idx, raw_data in enumerate(request.data):
            try:
                # 1. 数据转换
                feedback_data = adapter.transform(raw_data)
                if not feedback_data:
                    failed_count += 1
                    failed_items.append({
                        "index": idx,
                        "error": "数据转换失败",
                        "raw_data": raw_data
                    })
                    continue
                
                # 2. 智能预筛选
                filter_result = await intelligent_filter.filter_feedback(
                    feedback_data.content,
                    {
                        "source_type": request.source_type.value,
                        "user_info": feedback_data.user_info.dict() if feedback_data.user_info else {}
                    }
                )
                
                # 3. 更新分析结果
                feedback_data.sentiment = filter_result.sentiment
                feedback_data.category = filter_result.category
                feedback_data.keywords = filter_result.extracted_keywords
                feedback_data.priority = _convert_priority_score_to_level(filter_result.priority_score)
                feedback_data.quality_score = filter_result.confidence
                
                # 4. 添加批次信息
                feedback_data.custom_fields.update({
                    "batch_id": batch_id,
                    "batch_name": request.batch_name,
                    "import_time": datetime.now(),
                    "should_process_with_llm": filter_result.should_process_with_llm
                })
                
                # 5. 保存到数据库
                await feedback_data.insert()
                
                success_count += 1
                logger.debug(f"成功导入数据项 {idx}")
                
            except Exception as e:
                failed_count += 1
                failed_items.append({
                    "index": idx,
                    "error": str(e),
                    "raw_data": raw_data
                })
                logger.error(f"处理数据项 {idx} 失败: {e}")
        
        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 更新统计信息
        await _update_import_stats(request.source_type, success_count, failed_count, processing_time)
        
        logger.info(f"批量导入完成: {success_count}/{len(request.data)} 成功")
        
        return ImportResponse(
            batch_id=batch_id,
            total_count=len(request.data),
            success_count=success_count,
            failed_count=failed_count,
            processing_time=processing_time,
            failed_items=failed_items[:10]  # 只返回前10个失败项
        )
        
    except Exception as e:
        logger.error(f"批量导入失败: {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

@router.post("/import-file")
async def import_from_file(
    file: UploadFile = File(...),
    source_type: DataSourceType = Form(...),
    industry_type: IndustryType = Form(IndustryType.GENERAL)
):
    """从文件导入数据"""
    try:
        # 检查文件类型
        if not file.filename.endswith(('.json', '.csv', '.xlsx')):
            raise HTTPException(
                status_code=400,
                detail="只支持JSON、CSV、XLSX格式文件"
            )
        
        # 读取文件内容
        content = await file.read()
        
        # 解析文件数据
        if file.filename.endswith('.json'):
            import json
            data = json.loads(content.decode('utf-8'))
        elif file.filename.endswith('.csv'):
            import pandas as pd
            import io
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
            data = df.to_dict('records')
        elif file.filename.endswith('.xlsx'):
            import pandas as pd
            import io
            df = pd.read_excel(io.BytesIO(content))
            data = df.to_dict('records')
        
        # 构建导入请求
        import_request = ImportRequest(
            source_type=source_type,
            industry_type=industry_type,
            data=data,
            batch_name=file.filename,
            description=f"从文件 {file.filename} 导入"
        )
        
        # 执行导入
        return await import_data_batch(import_request)
        
    except Exception as e:
        logger.error(f"文件导入失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件导入失败: {str(e)}")

@router.get("/data-sources", response_model=List[DataSourceStatus])
async def get_data_sources_status():
    """获取所有数据源状态"""
    try:
        statuses = []
        
        # 获取支持的数据源
        adapter_registry = get_adapter_registry()
        supported_sources = adapter_registry.get_supported_sources()
        
        for source_type in supported_sources:
            # 查询统计信息
            total_records = await FeedbackData.find(
                FeedbackData.source_type == source_type
            ).count()
            
            # 查询最近导入时间
            last_record = await FeedbackData.find(
                FeedbackData.source_type == source_type
            ).sort(-FeedbackData.crawled_at).limit(1).to_list()
            
            last_import_time = last_record[0].crawled_at if last_record else None
            
            # 计算成功率（最近7天）
            from datetime import timedelta
            week_ago = datetime.now() - timedelta(days=7)
            
            total_recent = await FeedbackData.find(
                FeedbackData.source_type == source_type,
                FeedbackData.crawled_at >= week_ago
            ).count()
            
            success_recent = await FeedbackData.find(
                FeedbackData.source_type == source_type,
                FeedbackData.crawled_at >= week_ago,
                FeedbackData.processing_status.is_processed == True
            ).count()
            
            success_rate = (success_recent / total_recent * 100) if total_recent > 0 else None
            
            statuses.append(DataSourceStatus(
                source_type=source_type,
                platform_name=_get_platform_name(source_type),
                is_active=True,  # 这里可以从配置中读取
                total_records=total_records,
                last_import_time=last_import_time,
                success_rate=success_rate
            ))
        
        return statuses
        
    except Exception as e:
        logger.error(f"获取数据源状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")

@router.get("/supported-sources")
async def get_supported_sources():
    """获取支持的数据源列表"""
    try:
        adapter_registry = get_adapter_registry()
        sources = adapter_registry.get_supported_sources()
        
        return {
            "supported_sources": [
                {
                    "value": source.value,
                    "name": _get_platform_name(source),
                    "category": _get_source_category(source)
                }
                for source in sources
            ]
        }
        
    except Exception as e:
        logger.error(f"获取支持数据源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-data")
async def validate_import_data(
    source_type: DataSourceType,
    sample_data: List[Dict[str, Any]]
):
    """验证导入数据格式"""
    try:
        adapter_registry = get_adapter_registry()
        adapter = adapter_registry.get_adapter(source_type)
        
        if not adapter:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的数据源类型: {source_type.value}"
            )
        
        validation_results = []
        
        for idx, raw_data in enumerate(sample_data[:5]):  # 只验证前5条
            try:
                feedback_data = adapter.transform(raw_data)
                is_valid = adapter.validate_data(feedback_data)
                
                validation_results.append({
                    "index": idx,
                    "is_valid": is_valid,
                    "transformed_data": {
                        "content": feedback_data.content[:100] + "..." if len(feedback_data.content) > 100 else feedback_data.content,
                        "source_platform": feedback_data.source_platform,
                        "created_at": feedback_data.created_at,
                        "user_info": feedback_data.user_info.dict() if feedback_data.user_info else None
                    }
                })
                
            except Exception as e:
                validation_results.append({
                    "index": idx,
                    "is_valid": False,
                    "error": str(e)
                })
        
        return {
            "source_type": source_type.value,
            "validation_results": validation_results
        }
        
    except Exception as e:
        logger.error(f"数据验证失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 辅助函数
def _convert_priority_score_to_level(score: float) -> str:
    """将优先级分数转换为级别"""
    if score >= 0.8:
        return "critical"
    elif score >= 0.6:
        return "high"
    elif score >= 0.4:
        return "medium"
    else:
        return "low"

def _get_platform_name(source_type: DataSourceType) -> str:
    """获取平台中文名称"""
    name_mapping = {
        DataSourceType.XIAOHONGSHU: "小红书",
        DataSourceType.DOUYIN: "抖音",
        DataSourceType.WECHAT_MP: "微信公众号",
        DataSourceType.WEIBO: "微博",
        DataSourceType.BILIBILI: "哔哩哔哩",
        DataSourceType.TAOBAO: "淘宝",
        DataSourceType.JINGDONG: "京东",
        DataSourceType.PINDUODUO: "拼多多",
        DataSourceType.DOUYIN_MALL: "抖音电商",
        DataSourceType.TMALL: "天猫",
        DataSourceType.APP_STORE: "App Store",
        DataSourceType.GOOGLE_PLAY: "Google Play",
        DataSourceType.HUAWEI_STORE: "华为应用市场",
        DataSourceType.XIAOMI_STORE: "小米应用商店",
        DataSourceType.OPPO_STORE: "OPPO软件商店",
        DataSourceType.VIVO_STORE: "vivo应用商店",
        DataSourceType.SAMSUNG_STORE: "三星应用商店"
    }
    return name_mapping.get(source_type, source_type.value)

def _get_source_category(source_type: DataSourceType) -> str:
    """获取数据源分类"""
    if source_type in [DataSourceType.XIAOHONGSHU, DataSourceType.DOUYIN, DataSourceType.WECHAT_MP, DataSourceType.WEIBO, DataSourceType.BILIBILI]:
        return "社交媒体"
    elif source_type in [DataSourceType.TAOBAO, DataSourceType.JINGDONG, DataSourceType.PINDUODUO, DataSourceType.DOUYIN_MALL, DataSourceType.TMALL]:
        return "电商平台"
    elif source_type in [DataSourceType.APP_STORE, DataSourceType.GOOGLE_PLAY, DataSourceType.HUAWEI_STORE, DataSourceType.XIAOMI_STORE, DataSourceType.OPPO_STORE, DataSourceType.VIVO_STORE, DataSourceType.SAMSUNG_STORE]:
        return "应用市场"
    else:
        return "其他"

async def _update_import_stats(source_type: DataSourceType, success_count: int, failed_count: int, processing_time: float):
    """更新导入统计"""
    try:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 查找今日统计记录
        stats = await DataSourceStats.find_one(
            DataSourceStats.source_type == source_type,
            DataSourceStats.date == today
        )
        
        if not stats:
            # 创建新记录
            stats = DataSourceStats(
                source_type=source_type,
                date=today
            )
        
        # 更新统计数据
        stats.total_count += success_count + failed_count
        stats.processed_count += success_count
        stats.error_count += failed_count
        
        # 更新平均处理时间
        if stats.avg_processing_time:
            stats.avg_processing_time = (stats.avg_processing_time + processing_time) / 2
        else:
            stats.avg_processing_time = processing_time
        
        # 更新成功率
        if stats.total_count > 0:
            stats.success_rate = stats.processed_count / stats.total_count * 100
        
        await stats.save()
        
    except Exception as e:
        logger.error(f"更新统计信息失败: {e}") 