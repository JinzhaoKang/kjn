"""
反馈管理API路由
提供用户反馈的CRUD操作接口
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime
import logging

from ..models.database import UserFeedback, FeedbackSource
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Mock反馈数据
MOCK_FEEDBACKS = [
    {
        "id": "feedback_001",
        "title": "登录问题反馈",
        "source": "mobile_app",
        "original_text": "每次登录时应用都会崩溃，这个问题已经持续了一周了。希望能尽快修复。",
        "processed_text": "每次登录时应用都会崩溃，这个问题已经持续了一周了。希望能尽快修复。",
        "feedback_time": "2024-01-15T09:30:00",
        "created_at": "2024-01-15T09:30:00",
        "is_processed": False,
        "status": "pending",
        "user_id": "user_001",
        "priority": "high",
        "category": "bug_report"
    },
    {
        "id": "feedback_002",
        "title": "UI界面改进建议",
        "source": "web_portal",
        "original_text": "建议改进用户界面设计，当前的界面不够直观，用户体验有待提升。",
        "processed_text": "建议改进用户界面设计，当前的界面不够直观，用户体验有待提升。",
        "feedback_time": "2024-01-15T10:15:00",
        "created_at": "2024-01-15T10:15:00",
        "is_processed": False,
        "status": "pending",
        "user_id": "user_002",
        "priority": "medium",
        "category": "feature_request"
    },
    {
        "id": "feedback_003",
        "title": "功能请求",
        "source": "customer_service",
        "original_text": "希望能添加数据导出功能，方便我们进行数据分析和报告生成。",
        "processed_text": "希望能添加数据导出功能，方便我们进行数据分析和报告生成。",
        "feedback_time": "2024-01-15T11:00:00",
        "created_at": "2024-01-15T11:00:00",
        "is_processed": False,
        "status": "pending",
        "user_id": "user_003",
        "priority": "low",
        "category": "feature_request"
    },
    {
        "id": "feedback_004",
        "title": "性能问题",
        "source": "mobile_app",
        "original_text": "应用运行速度太慢，加载页面需要很长时间，影响工作效率。",
        "processed_text": "应用运行速度太慢，加载页面需要很长时间，影响工作效率。",
        "feedback_time": "2024-01-15T08:45:00",
        "created_at": "2024-01-15T08:45:00",
        "is_processed": True,
        "status": "completed",
        "user_id": "user_004",
        "priority": "urgent",
        "category": "performance_issue",
        "analysis_result": {
            "sentiment": "negative",
            "category": "performance",
            "priority_score": 8.5
        }
    },
    {
        "id": "feedback_005",
        "title": "安全性关注",
        "source": "web_portal",
        "original_text": "担心数据安全问题，希望能加强用户隐私保护和数据加密。",
        "processed_text": "担心数据安全问题，希望能加强用户隐私保护和数据加密。",
        "feedback_time": "2024-01-15T12:20:00",
        "created_at": "2024-01-15T12:20:00",
        "is_processed": False,
        "status": "pending",
        "user_id": "user_005",
        "priority": "high",
        "category": "security_concern"
    },
    {
        "id": "feedback_006",
        "title": "用户体验反馈",
        "source": "customer_service",
        "original_text": "整体使用体验不错，但是某些功能的操作流程比较复杂，希望能简化。",
        "processed_text": "整体使用体验不错，但是某些功能的操作流程比较复杂，希望能简化。",
        "feedback_time": "2024-01-15T13:10:00",
        "created_at": "2024-01-15T13:10:00",
        "is_processed": False,
        "status": "pending",
        "user_id": "user_006",
        "priority": "medium",
        "category": "user_experience"
    }
]


# Pydantic模型
class FeedbackCreate(BaseModel):
    """创建反馈的请求模型"""
    original_text: str
    source: FeedbackSource = FeedbackSource.INTERNAL
    user_id: Optional[str] = None
    feedback_time: Optional[datetime] = None
    metadata: Optional[dict] = None


class FeedbackResponse(BaseModel):
    """反馈响应模型"""
    id: str
    source: FeedbackSource
    original_text: str
    processed_text: Optional[str]
    feedback_time: Optional[datetime]
    analysis_result: Optional[dict]
    created_at: datetime
    is_processed: bool


class FeedbackBatchCreate(BaseModel):
    """批量创建反馈的请求模型"""
    feedbacks: List[FeedbackCreate]


@router.post("/", response_model=FeedbackResponse, summary="创建单条反馈")
async def create_feedback(
    feedback: FeedbackCreate,
    background_tasks: BackgroundTasks
):
    """创建单条用户反馈并启动分析任务"""
    
    try:
        # 创建文档记录
        db_feedback = UserFeedback(
            content=feedback.original_text,
            original_content=feedback.original_text,
            source=feedback.source,
            source_platform="api",
            feedback_time=feedback.feedback_time or datetime.utcnow(),
            crawled_at=datetime.utcnow(),
            user_id=feedback.user_id,
            platform_metadata=feedback.metadata or {},
            # 兼容性字段
            original_text=feedback.original_text,
            processed_text=feedback.original_text
        )
        
        # 保存到MongoDB
        await db_feedback.save()
        
        logger.info(f"创建反馈成功，ID: {db_feedback.id}")
        
        # 返回响应
        return FeedbackResponse(
            id=str(db_feedback.id),
            source=db_feedback.source,
            original_text=db_feedback.original_text,
            processed_text=db_feedback.processed_text,
            feedback_time=db_feedback.feedback_time,
            analysis_result=db_feedback.analysis_result,
            created_at=db_feedback.created_at,
            is_processed=db_feedback.is_processed
        )
        
    except Exception as e:
        logger.error(f"创建反馈失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建反馈失败: {str(e)}")


@router.post("/batch", summary="批量创建反馈")
async def create_batch_feedback(batch_data: FeedbackBatchCreate):
    """批量创建用户反馈"""
    try:
        created_feedbacks = []
        
        for feedback_data in batch_data.feedbacks:
            # 生成新反馈ID
            new_feedback_id = f"feedback_{len(MOCK_FEEDBACKS) + len(created_feedbacks) + 1:03d}"
            
            new_feedback = {
                "id": new_feedback_id,
                "title": f"批量导入反馈 {new_feedback_id}",
                "source": feedback_data.source.value,
                "original_text": feedback_data.original_text,
                "processed_text": feedback_data.original_text,
                "feedback_time": (feedback_data.feedback_time or datetime.now()).isoformat(),
                "created_at": datetime.now().isoformat(),
                "is_processed": False,
                "status": "pending",
                "user_id": feedback_data.user_id or "anonymous",
                "priority": "normal",
                "category": "general"
            }
            
            MOCK_FEEDBACKS.append(new_feedback)
            created_feedbacks.append(new_feedback)
        
        return {
            "message": f"成功创建 {len(created_feedbacks)} 条反馈",
            "created_count": len(created_feedbacks),
            "feedbacks": created_feedbacks
        }
        
    except Exception as e:
        logger.error(f"批量创建反馈失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量创建反馈失败: {str(e)}")


@router.get("/", summary="查询反馈列表")
async def get_feedbacks(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="限制记录数"),
    status: Optional[str] = Query(None, description="按状态筛选：pending, completed, processing"),
    source: Optional[str] = Query(None, description="按来源筛选"),
    priority: Optional[str] = Query(None, description="按优先级筛选")
):
    """分页查询反馈列表，支持状态、来源等筛选"""
    try:
        # 构建查询条件
        query_filters = {}
        
        # 按状态筛选
        if status:
            if status == "pending":
                query_filters["is_processed"] = False
            elif status == "completed":
                query_filters["is_processed"] = True
            elif status == "processing":
                query_filters["is_processed"] = False
                query_filters["analysis_result"] = {"$exists": True}
        
        # 按来源筛选
        if source:
            try:
                query_filters["source"] = FeedbackSource(source)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的来源类型: {source}")
        
        # 执行查询
        feedbacks = await UserFeedback.find(query_filters)\
            .sort([("created_at", -1)])\
            .skip(skip)\
            .limit(limit)\
            .to_list()
        
        # 获取总数
        total_count = await UserFeedback.find(query_filters).count()
        
        # 转换为响应格式
        feedback_list = []
        for feedback in feedbacks:
            # 兼容旧数据：确定显示文本
            display_text = ""
            if feedback.original_content:  # 新字段
                display_text = feedback.original_content
            elif feedback.content:  # 新字段备选
                display_text = feedback.content
            elif feedback.original_text:  # 旧字段兼容
                display_text = feedback.original_text
            elif feedback.processed_text:  # 旧字段兼容
                display_text = feedback.processed_text
            else:
                display_text = "内容缺失"
            
            # 获取AI分析结果 - 优先从processing_metadata.ai_analysis_result读取
            ai_analysis = None
            if feedback.processing_metadata and feedback.processing_metadata.get("ai_analysis_result"):
                ai_analysis = feedback.processing_metadata["ai_analysis_result"]
            elif feedback.analysis_result:
                ai_analysis = feedback.analysis_result
            
            # 提取优先级信息
            priority_level = "normal"
            if ai_analysis:
                # 优先使用ai_analysis_result中的priority字段
                if "priority" in ai_analysis:
                    priority_level = ai_analysis["priority"]
                else:
                    urgency_score = ai_analysis.get("urgency_score", 0)
                    if urgency_score >= 0.8:
                        priority_level = "urgent"
                    elif urgency_score >= 0.6:
                        priority_level = "high"
                    elif urgency_score <= 0.3:
                        priority_level = "low"
            
            # 提取分类信息
            category = "general"
            if ai_analysis:
                # 优先使用ai_analysis_result中的category字段
                if "category" in ai_analysis:
                    category = ai_analysis["category"]
                else:
                    intent = ai_analysis.get("intent", "")
                    if "bug" in intent.lower():
                        category = "bug_report"
                    elif "feature" in intent.lower():
                        category = "feature_request"
                    elif "performance" in intent.lower():
                        category = "performance_issue"
            
            # 判断处理状态 - 基于processing_status.ai_analyzed
            is_ai_processed = False
            if feedback.processing_status and feedback.processing_status.get("ai_analyzed"):
                is_ai_processed = True
            elif feedback.is_processed:
                is_ai_processed = True
            
            feedback_item = {
                "id": str(feedback.id),
                "title": display_text[:50] + "..." if len(display_text) > 50 else display_text,
                "source": feedback.source.value,
                "original_text": display_text,  # 兼容性显示
                "processed_text": feedback.processed_text or display_text,
                "feedback_time": feedback.feedback_time.isoformat() if feedback.feedback_time else None,
                "created_at": feedback.created_at.isoformat(),
                "is_processed": is_ai_processed,  # 使用AI分析状态
                "status": "completed" if is_ai_processed else "pending",
                "user_id": feedback.user_id or "anonymous",
                "priority": priority_level,
                "category": category,
                "analysis_result": ai_analysis,  # 使用正确的AI分析结果
                "platform_metadata": feedback.platform_metadata or {},
                # 添加更多字段供前端显示
                "sentiment": ai_analysis.get("sentiment") if ai_analysis else None,
                "ai_confidence": ai_analysis.get("ai_confidence") if ai_analysis else None,
                "processing_status": feedback.processing_status,
                "keywords": ai_analysis.get("keywords", []) if ai_analysis else []
            }
            feedback_list.append(feedback_item)
        
        return {
            "data": feedback_list,
            "total": total_count,
            "skip": skip,
            "limit": limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询反馈列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/stats/overview", summary="获取反馈统计概览")
async def get_feedback_stats():
    """获取反馈的统计概览信息"""
    
    try:
        # 从数据库获取真实统计数据
        total_count = await UserFeedback.find().count()
        processed_count = await UserFeedback.find({"is_processed": True}).count()
        pending_count = await UserFeedback.find({"is_processed": False}).count()
        
        # 优先级统计
        priority_stats = {}
        for priority in ["low", "normal", "medium", "high", "urgent"]:
            # 根据urgency_score计算优先级
            if priority == "urgent":
                count = await UserFeedback.find({"analysis_result.urgency_score": {"$gte": 0.8}}).count()
            elif priority == "high":
                count = await UserFeedback.find({"analysis_result.urgency_score": {"$gte": 0.6, "$lt": 0.8}}).count()
            elif priority == "medium":
                count = await UserFeedback.find({"analysis_result.urgency_score": {"$gte": 0.4, "$lt": 0.6}}).count()
            elif priority == "low":
                count = await UserFeedback.find({"analysis_result.urgency_score": {"$lt": 0.3}}).count()
            else:  # normal
                count = await UserFeedback.find({"analysis_result.urgency_score": {"$gte": 0.3, "$lt": 0.4}}).count()
            priority_stats[priority] = count
        
        # 分类统计
        category_pipeline = [
            {"$group": {"_id": "$analysis_result.intent", "count": {"$sum": 1}}},
            {"$project": {"category": "$_id", "count": 1, "_id": 0}}
        ]
        category_results = await UserFeedback.aggregate(category_pipeline).to_list()
        category_stats = {item["category"] or "unknown": item["count"] for item in category_results}
        
        stats = {
            "total_feedback": total_count,
            "processed_feedback": processed_count,
            "pending_feedback": pending_count,
            "processing_rate": round((processed_count / total_count * 100), 2) if total_count > 0 else 0,
            "priority_distribution": priority_stats,
            "category_distribution": category_stats
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/{feedback_id}", summary="获取单条反馈")
async def get_feedback(feedback_id: str):
    """根据ID获取单条反馈详情"""
    
    try:
        from bson import ObjectId
        
        # 验证ObjectId格式
        if not ObjectId.is_valid(feedback_id):
            raise HTTPException(status_code=400, detail="无效的反馈ID格式")
        
        feedback = await UserFeedback.find_one({"_id": ObjectId(feedback_id)})
        
        if not feedback:
            raise HTTPException(status_code=404, detail="反馈不存在")
        
        # 兼容旧数据：确定显示文本
        display_text = ""
        if feedback.original_content:  # 新字段
            display_text = feedback.original_content
        elif feedback.content:  # 新字段备选
            display_text = feedback.content
        elif feedback.original_text:  # 旧字段兼容
            display_text = feedback.original_text
        elif feedback.processed_text:  # 旧字段兼容
            display_text = feedback.processed_text
        else:
            display_text = "内容缺失"
        
        # 提取优先级信息
        priority_level = "normal"
        if feedback.analysis_result:
            urgency_score = feedback.analysis_result.get("urgency_score", 0)
            if urgency_score >= 0.8:
                priority_level = "urgent"
            elif urgency_score >= 0.6:
                priority_level = "high"
            elif urgency_score <= 0.3:
                priority_level = "low"
        
        # 提取分类信息
        category = "general"
        if feedback.analysis_result:
            intent = feedback.analysis_result.get("intent", "")
            if "bug" in intent.lower():
                category = "bug_report"
            elif "feature" in intent.lower():
                category = "feature_request"
            elif "performance" in intent.lower():
                category = "performance_issue"
        
        feedback_detail = {
            "id": str(feedback.id),
            "title": display_text[:50] + "..." if len(display_text) > 50 else display_text,
            "source": feedback.source.value,
            "original_text": display_text,  # 兼容性显示
            "processed_text": feedback.processed_text or display_text,
            "feedback_time": feedback.feedback_time.isoformat() if feedback.feedback_time else None,
            "created_at": feedback.created_at.isoformat(),
            "is_processed": feedback.is_processed,
            "status": "completed" if feedback.is_processed else "pending",
            "user_id": feedback.user_id or "anonymous",
            "priority": priority_level,
            "category": category,
            "analysis_result": feedback.analysis_result,
            "platform_metadata": feedback.platform_metadata or {}
        }
        
        return feedback_detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取反馈失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取反馈失败: {str(e)}")


@router.delete("/{feedback_id}", summary="删除反馈")
async def delete_feedback(feedback_id: str):
    """删除指定的反馈"""
    try:
        from bson import ObjectId
        
        # 验证ObjectId格式
        if not ObjectId.is_valid(feedback_id):
            raise HTTPException(status_code=400, detail="无效的反馈ID格式")
        
        feedback = await UserFeedback.find_one({"_id": ObjectId(feedback_id)})
        
        if not feedback:
            raise HTTPException(status_code=404, detail="反馈不存在")
        
        # 删除反馈
        await feedback.delete()
        
        return {
            "message": "反馈删除成功",
            "deleted_feedback_id": feedback_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除反馈失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除反馈失败: {str(e)}")

 