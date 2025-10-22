"""
分析引擎API路由
提供反馈分析和聚类功能
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging
from bson import ObjectId

from ..models.database import AnalysisTask, AnalysisResult
from ..core.database import db_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Mock数据
MOCK_TASKS = [
    {
        "id": "task_001",
        "feedback_id": "feedback_001",
        "status": "completed",
        "analysis_mode": "full",
        "priority": "high",
        "current_module": "action_generator",
        "progress": 100,
        "created_at": "2024-01-15T10:30:00",
        "started_at": "2024-01-15T10:30:05",
        "completed_at": "2024-01-15T10:35:00",
        "results": {
            "preprocessing": {
                "text_cleaned": True,
                "sentiment": "negative",
                "keywords": ["bug", "crash", "login"]
            },
            "llm_analysis": {
                "summary": "用户报告登录时应用崩溃的问题",
                "severity": "high",
                "category": "technical_issue"
            },
            "priority_assessment": {
                "score": 8.5,
                "factors": ["frequency", "severity", "business_impact"]
            },
            "action_recommendations": {
                "immediate": ["检查登录模块", "紧急修复"],
                "short_term": ["添加错误处理"],
                "long_term": ["重构登录系统"]
            }
        }
    },
    {
        "id": "task_002",
        "feedback_id": "feedback_002",
        "status": "running",
        "analysis_mode": "full",
        "priority": "normal",
        "current_module": "llm_analysis",
        "progress": 65,
        "created_at": "2024-01-15T11:00:00",
        "started_at": "2024-01-15T11:00:03",
        "results": {
            "preprocessing": {
                "text_cleaned": True,
                "sentiment": "neutral",
                "keywords": ["feature", "request", "ui"]
            },
            "llm_analysis": {
                "summary": "用户建议改进UI界面设计",
                "severity": "medium",
                "category": "feature_request"
            }
        }
    },
    {
        "id": "task_003",
        "feedback_id": "feedback_003",
        "status": "pending",
        "analysis_mode": "quick",
        "priority": "low",
        "current_module": "preprocessing",
        "progress": 0,
        "created_at": "2024-01-15T11:15:00"
    },
    {
        "id": "task_004",
        "feedback_id": "feedback_004",
        "status": "failed",
        "analysis_mode": "deep",
        "priority": "urgent",
        "current_module": "preprocessing",
        "progress": 10,
        "created_at": "2024-01-15T09:45:00",
        "started_at": "2024-01-15T09:45:02",
        "error_message": "文本预处理失败：编码错误"
    },
    {
        "id": "task_005",
        "feedback_id": "feedback_005",
        "status": "paused",
        "analysis_mode": "full",
        "priority": "normal",
        "current_module": "priority_assessment",
        "progress": 80,
        "created_at": "2024-01-15T10:00:00",
        "started_at": "2024-01-15T10:00:05"
    }
]


@router.get("/health", summary="分析引擎健康检查")
async def analysis_health():
    """分析引擎健康检查"""
    return {
        "status": "ok", 
        "module": "analysis",
        "preprocessing": True,
        "llm_analysis": True,
        "priority_engine": True,
        "action_generator": True
    }


@router.get("/tasks", summary="获取分析任务列表")
async def get_analysis_tasks(
    status: Optional[str] = Query(None, description="按状态筛选：pending, running, completed, failed, paused"),
    limit: int = Query(50, description="返回结果数量限制"),
    offset: int = Query(0, description="结果偏移量")
):
    """获取分析任务列表"""
    try:
        tasks = MOCK_TASKS.copy()
        
        # 按状态筛选
        if status:
            tasks = [task for task in tasks if task["status"] == status]
        
        # 分页
        total = len(tasks)
        tasks = tasks[offset:offset + limit]
        
        return {
            "data": tasks,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"获取分析任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分析任务失败: {str(e)}")


@router.post("/tasks", summary="创建分析任务")
async def create_analysis_task(task_data: dict):
    """创建新的分析任务"""
    try:
        # 生成新任务ID
        new_task_id = f"task_{len(MOCK_TASKS) + 1:03d}"
        
        new_task = {
            "id": new_task_id,
            "feedback_id": task_data.get("feedback_id"),
            "status": "pending",
            "analysis_mode": task_data.get("analysis_mode", "full"),
            "priority": task_data.get("priority", "normal"),
            "current_module": "preprocessing",
            "progress": 0,
            "created_at": datetime.now().isoformat()
        }
        
        MOCK_TASKS.append(new_task)
        
        return {
            "message": "分析任务创建成功",
            "task_id": new_task_id,
            "task": new_task
        }
    except Exception as e:
        logger.error(f"创建分析任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建分析任务失败: {str(e)}")


@router.get("/tasks/{task_id}", summary="获取分析任务详情")
async def get_analysis_task(task_id: str):
    """获取特定分析任务的详细信息"""
    try:
        task = next((task for task in MOCK_TASKS if task["id"] == task_id), None)
        
        if not task:
            raise HTTPException(status_code=404, detail="未找到指定的分析任务")
        
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分析任务详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")


@router.post("/tasks/{task_id}/pause", summary="暂停分析任务")
async def pause_analysis_task(task_id: str):
    """暂停正在运行的分析任务"""
    try:
        task = next((task for task in MOCK_TASKS if task["id"] == task_id), None)
        
        if not task:
            raise HTTPException(status_code=404, detail="未找到指定的分析任务")
        
        if task["status"] != "running":
            raise HTTPException(status_code=400, detail="只能暂停正在运行的任务")
        
        task["status"] = "paused"
        
        return {
            "message": "任务暂停成功",
            "task_id": task_id,
            "status": "paused"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停分析任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"暂停任务失败: {str(e)}")


@router.post("/tasks/{task_id}/resume", summary="恢复分析任务")
async def resume_analysis_task(task_id: str):
    """恢复暂停的分析任务"""
    try:
        task = next((task for task in MOCK_TASKS if task["id"] == task_id), None)
        
        if not task:
            raise HTTPException(status_code=404, detail="未找到指定的分析任务")
        
        if task["status"] != "paused":
            raise HTTPException(status_code=400, detail="只能恢复暂停的任务")
        
        task["status"] = "running"
        
        return {
            "message": "任务恢复成功",
            "task_id": task_id,
            "status": "running"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复分析任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"恢复任务失败: {str(e)}")


@router.post("/cluster", summary="触发聚类分析")
async def trigger_clustering():
    """触发反馈聚类分析"""
    try:
        # 这里将来可以实现聚类逻辑
        return {"message": "聚类分析已启动", "status": "initiated"}
    except Exception as e:
        logger.error(f"聚类分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"聚类分析失败: {str(e)}")


@router.get("/stats", summary="获取分析统计")
async def get_analysis_stats():
    """获取分析统计信息"""
    try:
        completed_tasks = len([task for task in MOCK_TASKS if task["status"] == "completed"])
        running_tasks = len([task for task in MOCK_TASKS if task["status"] == "running"])
        failed_tasks = len([task for task in MOCK_TASKS if task["status"] == "failed"])
        
        return {
            "total_tasks": len(MOCK_TASKS),
            "completed_tasks": completed_tasks,
            "running_tasks": running_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": completed_tasks / len(MOCK_TASKS) * 100 if MOCK_TASKS else 0,
            "last_analysis": MOCK_TASKS[0]["created_at"] if MOCK_TASKS else None
        }
    except Exception as e:
        logger.error(f"获取分析统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}") 