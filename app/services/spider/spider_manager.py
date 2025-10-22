"""
爬虫管理器
统一管理和调度所有爬虫实例
"""
import asyncio
import logging
import inspect
from typing import Dict, List, Optional, Any, Type
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import uuid

from .base_spider import BaseSpider, SpiderConfig, SpiderResult, SpiderStatus, DataSourcePlatform
from .qimai_spider import QimaiSpider, create_qimai_spider
from .ecommerce_spider import EcommerceSpider, create_jd_spider



class SpiderTask:
    """爬虫任务"""
    
    def __init__(self, 
                 task_id: str,
                 spider: BaseSpider,
                 task_params: Dict[str, Any] = None):
        self.task_id = task_id
        self.spider = spider
        self.task_params = task_params or {}
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[SpiderResult] = None
        self.error: Optional[str] = None
        
    @property
    def status(self) -> SpiderStatus:
        """获取任务状态"""
        if self.completed_at:
            return SpiderStatus.COMPLETED
        elif self.started_at:
            return self.spider.status
        else:
            return SpiderStatus.IDLE
    
    @property
    def duration(self) -> float:
        """任务执行时长（秒）"""
        if self.started_at is None:
            return 0.0
        
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()


class SpiderManager:
    """爬虫管理器"""
    
    def __init__(self, max_concurrent_tasks: int = 5):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.logger = logging.getLogger("spider.manager")
        
        # 任务管理
        self.tasks: Dict[str, SpiderTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # 爬虫注册表
        self.spider_registry: Dict[DataSourcePlatform, Type[BaseSpider]] = {
            DataSourcePlatform.QIMAI: QimaiSpider,
            DataSourcePlatform.APP_STORE_IOS: QimaiSpider,  # 使用qimai作为iOS App Store的数据源
            DataSourcePlatform.TMALL: EcommerceSpider,      # ← 新增
            DataSourcePlatform.JD: EcommerceSpider,     
        }
        # self.spider_registry[DataSourcePlatform.TMALL] = EcommerceSpider
        # self.spider_registry[DataSourcePlatform.JD] = EcommerceSpider

        
        # 统计信息
        self.total_tasks_created = 0
        self.total_tasks_completed = 0
        self.total_tasks_failed = 0
        
    def register_spider(self, platform: DataSourcePlatform, spider_class: Type[BaseSpider]):
        """注册爬虫"""
        self.spider_registry[platform] = spider_class
        self.logger.info(f"注册爬虫: {platform.value} -> {spider_class.__name__}")
    
    
    def create_qimai_task(self, 
                     appid: str,
                     country: str = "cn",
                     days_back: int = 365,
                     max_pages: int = 100,
                     task_name: Optional[str] = None) -> str:
        """创建七麦爬虫任务"""
        # 生成任务ID
        task_id = task_name or f"qimai_{appid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 创建爬虫实例
        spider = create_qimai_spider(
            appid=appid,
            country=country,
            days_back=days_back,
            max_pages=max_pages
        )
        
        # 创建任务
        task = SpiderTask(
            task_id=task_id,
            spider=spider,
            task_params={
                'appid': appid,
                'country': country,
                'days_back': days_back,
                'max_pages': max_pages
            }
        )
        
        self.tasks[task_id] = task
        self.total_tasks_created += 1
        
        self.logger.info(f"创建七麦爬虫任务: {task_id} (应用ID: {appid})")
        return task_id
    def create_jd_task(self, item_id: str, days_back: int = 30, max_pages: int = 30, page_size: int = 20, task_name: Optional[str] = None) -> str:
        spider = create_jd_spider(product_id=item_id, days_back=days_back, page_size=page_size, max_pages=max_pages)
        task_id = task_name or f"jd_{item_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task = SpiderTask(task_id=task_id, spider=spider, task_params={})
        self.tasks[task_id] = task
        self.total_tasks_created += 1
        self.logger.info(f"创建京东爬虫任务: {task_id} (SKU: {item_id})")
        return task_id
    
    def create_ecommerce_task(
        self,
        platform: DataSourcePlatform,
        item_id: str,
        days_back: int = 30,
        page_size: int = 20,
        max_pages: int = 50,
        task_name: Optional[str] = None,  # 这里改了
        ) -> str:
        if platform not in (DataSourcePlatform.TMALL, DataSourcePlatform.JD):
            raise ValueError(f"不支持的平台: {platform.value}")

        task_id = task_name or f"{platform.value}_{item_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 用工厂函数生成实例（与 create_qimai_spider 风格一致）
        spider = create_ecommerce_spider(
            platform=platform.value,  # "tmall" 或 "jd"
            item_id=item_id,
            days_back=days_back,
            page_size=page_size,
            max_pages=max_pages,
    )

    # 推荐：让 task_params 为空，避免 run(**params) 报 TypeError
        task = SpiderTask(
            task_id=task_id,
            spider=spider,
            task_params={},  # 如果你的 run_task 没做兼容，建议保持空字典
        )

        self.tasks[task_id] = task
        self.total_tasks_created += 1
        self.logger.info(f"创建电商爬虫任务: {task_id} (平台: {platform.value}, item_id: {item_id})")
        return task_id

    
    def create_qimai_android_task(self, 
                             market: str = "4",
                             max_pages: int = 100,
                             task_name: Optional[str] = None) -> str:
        """创建七麦Android爬虫任务"""
        # 市场名称映射
        market_names = {
            '4': '小米',
            '6': '华为', 
            '7': '魅族',
            '8': 'vivo',
            '9': 'oppo'
        }
        
        market_name = market_names.get(market, f'市场{market}')
        
        # 生成任务ID
        task_id = task_name or f"qimai_android_{market_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 创建Android爬虫实例
        spider = QimaiSpider.create_for_android_app(
            market=market,
            max_pages=max_pages
        )
        
        # 创建任务
        task = SpiderTask(
            task_id=task_id,
            spider=spider,
            task_params={
                'platform': 'android',
                'market': market,
                'market_name': market_name,
                'max_pages': max_pages
            }
        )
        
        self.tasks[task_id] = task
        self.total_tasks_created += 1
        
        self.logger.info(f"创建七麦Android爬虫任务: {task_id} ({market_name}应用市场)")
        return task_id
    
    
    def create_custom_task(self,
                      platform: DataSourcePlatform,
                      config: SpiderConfig,
                      task_params: Optional[Dict[str, Any]] = None,
                      task_name: Optional[str] = None) -> str:
        """创建自定义爬虫任务"""
        if platform not in self.spider_registry:
            raise ValueError(f"不支持的平台: {platform.value}")
        
        # 生成任务ID
        task_id = task_name or f"{platform.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # 创建爬虫实例
        spider_class = self.spider_registry[platform]
        spider = spider_class(config)
        
        # 创建任务
        task = SpiderTask(
            task_id=task_id,
            spider=spider,
            task_params=task_params or {}
        )
        
        self.tasks[task_id] = task
        self.total_tasks_created += 1
        
        self.logger.info(f"创建自定义爬虫任务: {task_id} (平台: {platform.value})")
        return task_id
    
    async def _run_spider_with_params(self, spider: BaseSpider, params: dict):
        """
        根据 spider.run 的签名只传递它能接受的参数；
        若不接受任何参数则无参调用，避免 TypeError。
        """
        params = params or {}
        sig = inspect.signature(spider.run)
        # 是否有 **kwargs
        has_var_kw = any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values())
        if has_var_kw:
            # run(**kwargs) 都能接，原样传
            return await spider.run(**params)

        # 仅保留 run 显式声明过的参数名
        accepted_keys = {name for name in sig.parameters.keys()}
        filtered = {k: v for k, v in params.items() if k in accepted_keys}

        try:
            return await spider.run(**filtered)
        except TypeError as e:
            # 若仍因“不接受参数”报错，退回无参调用
            msg = str(e)
            if "unexpected keyword argument" in msg or "positional arguments" in msg:
                return await spider.run()
            raise
    
    async def run_task(self, task_id: str) -> SpiderResult:
        """运行单个任务"""
        if task_id not in self.tasks:
            raise ValueError(f"任务不存在: {task_id}")
        
        task = self.tasks[task_id]
        
        if task.status != SpiderStatus.IDLE:
            raise ValueError(f"任务已在运行或已完成: {task_id}")
        
        # 检查并发限制
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            raise ValueError(f"达到最大并发任务数限制: {self.max_concurrent_tasks}")
        
        self.logger.info(f"开始运行任务: {task_id}")
        task.started_at = datetime.now()
        
        try:
            # 初始化爬虫
            # async with task.spider:
            #     # 运行爬虫
            #     result = await task.spider.run(**task.task_params)
            async with task.spider:
                result = await self._run_spider_with_params(task.spider, task.task_params)
   
                task.result = result
                task.completed_at = datetime.now()
                
                if result.status == SpiderStatus.COMPLETED:
                    self.total_tasks_completed += 1
                    self.logger.info(f"任务完成: {task_id}, 抓取 {len(result.data)} 条数据")
                else:
                    self.total_tasks_failed += 1
                    self.logger.error(f"任务失败: {task_id}, 状态: {result.status}")
                
                return result
        
        except Exception as e:
            task.error = str(e)
            task.completed_at = datetime.now()
            self.total_tasks_failed += 1
            
            self.logger.error(f"任务执行异常: {task_id}, 错误: {e}")
            
            # 创建错误结果
            error_result = SpiderResult(
                spider_name=task.spider.config.spider_name,
                platform=task.spider.config.platform,
                status=SpiderStatus.ERROR,
                metrics=task.spider.metrics,
                errors=[str(e)]
            )
            task.result = error_result
            
            return error_result
        
        finally:
            # 清理运行中任务记录
            self.running_tasks.pop(task_id, None)
    
    async def run_task_async(self, task_id: str) -> str:
        """异步运行任务（后台执行）"""
        if task_id not in self.tasks:
            raise ValueError(f"任务不存在: {task_id}")
        
        if task_id in self.running_tasks:
            raise ValueError(f"任务已在运行: {task_id}")
        
        # 创建异步任务
        async_task = asyncio.create_task(self.run_task(task_id))
        self.running_tasks[task_id] = async_task
        
        self.logger.info(f"任务开始后台执行: {task_id}")
        return task_id
    
    async def run_multiple_tasks(self, task_ids: List[str]) -> Dict[str, SpiderResult]:
        """并行运行多个任务"""
        if len(task_ids) > self.max_concurrent_tasks:
            raise ValueError(f"任务数量超过并发限制: {len(task_ids)} > {self.max_concurrent_tasks}")
        
        self.logger.info(f"开始并行运行 {len(task_ids)} 个任务")
        
        # 创建协程列表
        coroutines = [self.run_task(task_id) for task_id in task_ids]
        
        # 并行执行
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # 整理结果
        task_results = {}
        for task_id, result in zip(task_ids, results):
            if isinstance(result, Exception):
                self.logger.error(f"任务 {task_id} 执行异常: {result}")
                # 创建错误结果
                task_results[task_id] = SpiderResult(
                    spider_name="unknown",
                    platform=DataSourcePlatform.QIMAI,  # 默认平台
                    status=SpiderStatus.ERROR,
                    metrics=None,
                    errors=[str(result)]
                )
            else:
                task_results[task_id] = result
        
        return task_results
    
    def stop_task(self, task_id: str):
        """停止任务"""
        if task_id not in self.tasks:
            raise ValueError(f"任务不存在: {task_id}")
        
        task = self.tasks[task_id]
        
        # 停止爬虫
        task.spider.stop()
        
        # 取消异步任务
        if task_id in self.running_tasks:
            async_task = self.running_tasks[task_id]
            async_task.cancel()
            self.running_tasks.pop(task_id)
        
        self.logger.info(f"停止任务: {task_id}")
    
    def pause_task(self, task_id: str):
        """暂停任务"""
        if task_id not in self.tasks:
            raise ValueError(f"任务不存在: {task_id}")
        
        task = self.tasks[task_id]
        task.spider.pause()
        
        self.logger.info(f"暂停任务: {task_id}")
    
    def resume_task(self, task_id: str):
        """恢复任务"""
        if task_id not in self.tasks:
            raise ValueError(f"任务不存在: {task_id}")
        
        task = self.tasks[task_id]
        task.spider.resume()
        
        self.logger.info(f"恢复任务: {task_id}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        if task_id not in self.tasks:
            raise ValueError(f"任务不存在: {task_id}")
        
        task = self.tasks[task_id]
        
        return {
            "task_id": task_id,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "duration": task.duration,
            "spider_status": task.spider.get_status(),
            "task_params": task.task_params,
            "error": task.error,
            "result_summary": {
                "data_count": len(task.result.data) if task.result else 0,
                "errors_count": len(task.result.errors) if task.result else 0
            } if task.result else None
        }
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务状态"""
        return [self.get_task_status(task_id) for task_id in self.tasks.keys()]
    
    def get_running_tasks(self) -> List[Dict[str, Any]]:
        """获取运行中的任务"""
        running_task_ids = [
            task_id for task_id, task in self.tasks.items() 
            if task.status == SpiderStatus.RUNNING
        ]
        return [self.get_task_status(task_id) for task_id in running_task_ids]
    
    def cleanup_completed_tasks(self, keep_days: int = 7):
        """清理已完成的任务"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if (task.status in [SpiderStatus.COMPLETED, SpiderStatus.ERROR] and 
                task.completed_at and task.completed_at < cutoff_date):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            self.tasks.pop(task_id)
        
        self.logger.info(f"清理了 {len(tasks_to_remove)} 个过期任务")
        return len(tasks_to_remove)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取管理器统计信息"""
        return {
            "total_tasks": len(self.tasks),
            "running_tasks": len(self.running_tasks),
            "idle_tasks": len([t for t in self.tasks.values() if t.status == SpiderStatus.IDLE]),
            "completed_tasks": len([t for t in self.tasks.values() if t.status == SpiderStatus.COMPLETED]),
            "failed_tasks": len([t for t in self.tasks.values() if t.status == SpiderStatus.ERROR]),
            "total_created": self.total_tasks_created,
            "total_completed": self.total_tasks_completed,
            "total_failed": self.total_tasks_failed,
            "max_concurrent": self.max_concurrent_tasks,
            "registered_platforms": list(self.spider_registry.keys())
        }


# 全局爬虫管理器实例
_spider_manager: Optional[SpiderManager] = None


def get_spider_manager() -> SpiderManager:
    """获取全局爬虫管理器实例"""
    global _spider_manager
    if _spider_manager is None:
        _spider_manager = SpiderManager()
    return _spider_manager


def initialize_spider_manager(max_concurrent_tasks: int = 5) -> SpiderManager:
    """初始化全局爬虫管理器"""
    global _spider_manager
    _spider_manager = SpiderManager(max_concurrent_tasks)
    return _spider_manager 