"""
FastAPI主应用
用户反馈分析系统的后端API服务
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from .core.config import settings
from .core.database import db_manager, connect_to_mongo, close_mongo_connection, init_database
from .api import feedback, analysis, dashboard, data_import, industry_config, geographical, spider, settings as app_settings, data_pipeline, hybrid_analysis, decision_engine, feedback_loop, insights

# 配置日志
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于大语言模型的用户反馈分析系统",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化操作"""
    try:
        # 连接到MongoDB
        await connect_to_mongo()
        logger.info("MongoDB连接成功")
        
        # 初始化数据库和文档模型
        await init_database()
        logger.info("数据库初始化完成")
        
        # 初始化数据管道
        try:
            from .services.data_pipeline.data_pipeline_manager import data_pipeline_manager
            await data_pipeline_manager.initialize()
            logger.info("数据管道初始化成功")
        except Exception as e:
            logger.error(f"数据管道初始化失败: {e}")
        
        logger.info(f"{settings.app_name} v{settings.app_version} 启动成功")
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理操作"""
    logger.info("应用正在关闭...")
    try:
        await close_mongo_connection()
        logger.info("MongoDB连接已关闭")
        
        # 关闭数据管道
        try:
            from .services.data_pipeline.data_pipeline_manager import data_pipeline_manager
            await data_pipeline_manager.shutdown()
            logger.info("数据管道已关闭")
        except Exception as e:
            logger.error(f"数据管道关闭失败: {e}")
        
        logger.info("应用已关闭")
    except Exception as e:
        logger.error(f"关闭MongoDB连接时出错: {e}")

# 根路径
@app.get("/", summary="API根路径")
async def root():
    """API根路径，返回系统基本信息"""
    return {
        "message": f"欢迎使用{settings.app_name}",
        "version": settings.app_version,
        "timestamp": datetime.now().isoformat(),
        "status": "运行中"
    }

# 健康检查端点
@app.get("/health", summary="健康检查")
async def health_check():
    """系统健康检查"""
    try:
        # 检查数据库连接
        db_healthy = await db_manager.health_check()
        
        health_status = {
            "status": "healthy" if db_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "database": "ok" if db_healthy else "error",
                "api": "ok"
            }
        }
        
        if not db_healthy:
            logger.warning("数据库健康检查失败")
            return JSONResponse(
                status_code=503,
                content=health_status
            )
        
        return health_status
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

# 包含API路由
app.include_router(
    feedback.router,
    prefix=f"{settings.api_v1_prefix}/feedback",
    tags=["反馈管理"]
)

app.include_router(
    analysis.router,
    prefix=f"{settings.api_v1_prefix}/analysis",
    tags=["分析引擎"]
)

app.include_router(
    dashboard.router,
    prefix=f"{settings.api_v1_prefix}/dashboard",
    tags=["数据看板"]
)

app.include_router(
    data_import.router,
    prefix=f"{settings.api_v1_prefix}/data-import",
    tags=["数据导入"]
)

app.include_router(
    industry_config.router,
    prefix=f"{settings.api_v1_prefix}/industry-config",
    tags=["行业配置"]
)

app.include_router(
    geographical.router,
    prefix=f"{settings.api_v1_prefix}/geographical",
    tags=["地理位置管理"]
)

app.include_router(
    spider.router,
    tags=["爬虫管理"]
)

app.include_router(
    app_settings.router,
    prefix=f"{settings.api_v1_prefix}/system",
    tags=["系统设置"]
)

app.include_router(
    data_pipeline.router,
    tags=["数据管道"]
)

app.include_router(
    hybrid_analysis.router,
    prefix=f"{settings.api_v1_prefix}/analysis",
    tags=["混合智能分析"]
)

app.include_router(
    decision_engine.router,
    prefix=f"{settings.api_v1_prefix}",
    tags=["决策引擎"]
)

app.include_router(
    feedback_loop.router,
    prefix=f"{settings.api_v1_prefix}/feedback-loop",
    tags=["反馈循环"]
)

app.include_router(
    insights.router,
    prefix=f"{settings.api_v1_prefix}/insights",
    tags=["洞察生成"]
)

# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "内部服务器错误",
            "message": "请稍后重试或联系管理员",
            "timestamp": datetime.now().isoformat()
        }
    )

# HTTP异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    ) 