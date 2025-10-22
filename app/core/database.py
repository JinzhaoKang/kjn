"""
数据库连接和会话管理
提供MongoDB连接、初始化等核心功能
"""
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import logging
from typing import Optional

from .config import settings

logger = logging.getLogger(__name__)

# MongoDB客户端实例
mongodb_client: Optional[AsyncIOMotorClient] = None


async def connect_to_mongo():
    """连接到MongoDB"""
    global mongodb_client
    try:
        mongodb_client = AsyncIOMotorClient(
            settings.mongodb_url,
            maxPoolSize=10,
            minPoolSize=1
        )
        # 测试连接
        await mongodb_client.admin.command('ping')
        logger.info(f"成功连接到MongoDB: {settings.mongodb_url}")
    except Exception as e:
        logger.error(f"MongoDB连接失败: {e}")
        raise


async def close_mongo_connection():
    """关闭MongoDB连接"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        logger.info("MongoDB连接已关闭")


async def init_database():
    """初始化数据库和文档模型"""
    try:
        # 导入所有文档模型
        from ..models.database import UserFeedback, ProductIssue
        from ..models.insights import InsightSession
        
        # 获取数据库实例
        database = mongodb_client[settings.mongodb_database]
        
        # 初始化Beanie
        await init_beanie(
            database=database,
            document_models=[UserFeedback, ProductIssue, InsightSession]
        )
        
        logger.info("MongoDB数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def get_database():
    """获取数据库实例"""
    if mongodb_client is None:
        raise RuntimeError("数据库未连接")
    return mongodb_client[settings.mongodb_database]


def get_db():
    """获取数据库实例 (FastAPI依赖项)"""
    return get_database()


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.client = mongodb_client
    
    async def health_check(self) -> bool:
        """数据库健康检查"""
        try:
            if self.client:
                await self.client.admin.command('ping')
                return True
            return False
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return False
    
    async def get_collection_stats(self):
        """获取集合统计信息"""
        try:
            db = get_database()
            collections = await db.list_collection_names()
            stats = {}
            
            for collection_name in collections:
                collection = db[collection_name]
                count = await collection.count_documents({})
                stats[collection_name] = count
            
            return stats
        except Exception as e:
            logger.error(f"获取集合统计失败: {e}")
            return {}


# 创建全局数据库管理器实例
db_manager = DatabaseManager() 