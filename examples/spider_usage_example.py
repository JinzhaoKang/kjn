#!/usr/bin/env python3
"""
爬虫模块使用示例
展示如何使用七麦数据爬虫抓取App Store评论
"""
import asyncio
import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.spider import (
    create_qimai_spider, 
    get_spider_manager, 
    initialize_spider_manager,
    QimaiSpider
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def example_1_basic_usage():
    """示例1: 基础使用 - 创建和运行单个爬虫"""
    logger.info("=== 示例1: 基础使用 ===")
    
    # 创建七麦爬虫实例
    spider = create_qimai_spider(
        appid="1329458504",  # 科沃斯机器人App ID
        country="cn",
        days_back=30,  # 抓取最近30天的数据
        max_pages=5    # 最多抓取5页
    )
    
    logger.info(f"创建爬虫: {spider.config.spider_name}")
    
    # 运行爬虫
    async with spider:
        result = await spider.run()
        
        logger.info(f"爬虫执行结果:")
        logger.info(f"  状态: {result.status}")
        logger.info(f"  抓取数据量: {len(result.data)}")
        logger.info(f"  错误数量: {len(result.errors)}")
        logger.info(f"  执行时长: {result.metrics.duration:.2f}秒")
        logger.info(f"  成功率: {result.metrics.success_rate:.2%}")
        
        # 显示前3条数据样例
        if result.data:
            logger.info("前3条数据样例:")
            for i, item in enumerate(result.data[:3], 1):
                logger.info(f"  {i}. 评分: {item.get('product_info', {}).get('rating', 'N/A')}")
                logger.info(f"     内容: {item.get('content', 'N/A')[:50]}...")
                logger.info(f"     用户: {item.get('user_info', {}).get('nickname', 'N/A')}")
                logger.info(f"     时间: {item.get('created_at', 'N/A')}")
                logger.info("")


async def example_2_spider_manager():
    """示例2: 使用爬虫管理器 - 管理多个爬虫任务"""
    logger.info("=== 示例2: 爬虫管理器 ===")
    
    # 初始化爬虫管理器
    spider_manager = initialize_spider_manager(max_concurrent_tasks=3)
    logger.info("初始化爬虫管理器")
    
    # 创建多个任务
    apps = [
        {"appid": "1329458504", "name": "科沃斯机器人"},
        {"appid": "1452635449", "name": "小米有品"},  # 假设的App ID
        {"appid": "414478124", "name": "淘宝"}       # 假设的App ID
    ]
    
    task_ids = []
    for app in apps:
        try:
            task_id = spider_manager.create_qimai_task(
                appid=app["appid"],
                country="cn",
                days_back=7,  # 最近7天
                max_pages=3,  # 每个任务最多3页
                task_name=f"spider_{app['name']}"
            )
            task_ids.append(task_id)
            logger.info(f"创建任务: {task_id} - {app['name']}")
        except Exception as e:
            logger.error(f"创建任务失败 {app['name']}: {e}")
    
    # 显示管理器统计信息
    stats = spider_manager.get_statistics()
    logger.info(f"管理器统计: {stats}")
    
    # 批量运行任务
    if task_ids:
        logger.info(f"开始并行运行 {len(task_ids)} 个任务...")
        try:
            results = await spider_manager.run_multiple_tasks(task_ids)
            
            logger.info("所有任务执行完成:")
            for task_id, result in results.items():
                logger.info(f"  {task_id}: {result.status} - {len(result.data)}条数据")
                
        except Exception as e:
            logger.error(f"批量运行失败: {e}")


async def example_3_task_control():
    """示例3: 任务控制 - 启动、暂停、恢复、停止"""
    logger.info("=== 示例3: 任务控制 ===")
    
    spider_manager = get_spider_manager()
    
    # 创建一个长时间运行的任务
    task_id = spider_manager.create_qimai_task(
        appid="1329458504",
        country="cn", 
        days_back=365,  # 一年的数据
        max_pages=50,   # 较多页数
        task_name="long_running_task"
    )
    
    logger.info(f"创建长时间任务: {task_id}")
    
    # 异步启动任务
    await spider_manager.run_task_async(task_id)
    logger.info("任务开始后台执行")
    
    # 等待一段时间
    await asyncio.sleep(5)
    
    # 获取任务状态
    status = spider_manager.get_task_status(task_id)
    logger.info(f"任务状态: {status['status']}")
    logger.info(f"已运行时长: {status['duration']:.2f}秒")
    
    # 暂停任务
    spider_manager.pause_task(task_id)
    logger.info("任务已暂停")
    
    await asyncio.sleep(2)
    
    # 恢复任务
    spider_manager.resume_task(task_id)
    logger.info("任务已恢复")
    
    await asyncio.sleep(3)
    
    # 停止任务
    spider_manager.stop_task(task_id)
    logger.info("任务已停止")
    
    # 最终状态
    final_status = spider_manager.get_task_status(task_id)
    logger.info(f"最终状态: {final_status['status']}")


async def example_4_data_preview():
    """示例4: 数据预览和分析"""
    logger.info("=== 示例4: 数据预览和分析 ===")
    
    spider_manager = get_spider_manager()
    
    # 创建并运行一个小任务
    task_id = spider_manager.create_qimai_task(
        appid="1329458504",
        country="cn",
        days_back=7,
        max_pages=2,
        task_name="preview_task"
    )
    
    logger.info("运行预览任务...")
    result = await spider_manager.run_task(task_id)
    
    if result.data:
        logger.info(f"抓取到 {len(result.data)} 条数据")
        
        # 统计分析
        ratings = []
        sentiments = {"positive": 0, "negative": 0, "neutral": 0}
        content_lengths = []
        
        for item in result.data:
            # 评分统计
            rating = item.get('product_info', {}).get('rating', 0)
            if rating:
                ratings.append(rating)
            
            # 情感统计
            sentiment = item.get('sentiment', 'neutral')
            if sentiment in sentiments:
                sentiments[sentiment] += 1
            
            # 内容长度统计
            content = item.get('content', '')
            content_lengths.append(len(content))
        
        # 显示统计结果
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            logger.info(f"平均评分: {avg_rating:.2f}")
        
        logger.info("情感分布:")
        for sentiment, count in sentiments.items():
            logger.info(f"  {sentiment}: {count}条")
        
        if content_lengths:
            avg_length = sum(content_lengths) / len(content_lengths)
            logger.info(f"平均内容长度: {avg_length:.1f}字符")
        
        # 显示一些样例数据
        logger.info("\n样例数据:")
        for i, item in enumerate(result.data[:3], 1):
            logger.info(f"样例 {i}:")
            logger.info(f"  评分: {item.get('product_info', {}).get('rating', 'N/A')}")
            logger.info(f"  情感: {item.get('sentiment', 'N/A')}")
            logger.info(f"  优先级: {item.get('priority', 'N/A')}")
            logger.info(f"  地理位置: {item.get('geographical_info', {}).get('country_name', 'N/A')}")
            logger.info(f"  质量评分: {item.get('quality_score', 'N/A')}")
            logger.info(f"  内容: {item.get('content', 'N/A')[:100]}...")
            logger.info("")


async def example_5_error_handling():
    """示例5: 错误处理和恢复"""
    logger.info("=== 示例5: 错误处理 ===")
    
    spider_manager = get_spider_manager()
    
    # 创建一个可能出错的任务（使用无效的App ID）
    try:
        task_id = spider_manager.create_qimai_task(
            appid="invalid_app_id",
            country="cn",
            days_back=7,
            max_pages=1,
            task_name="error_test_task"
        )
        
        logger.info("运行可能出错的任务...")
        result = await spider_manager.run_task(task_id)
        
        logger.info(f"任务状态: {result.status}")
        if result.errors:
            logger.info("错误信息:")
            for error in result.errors:
                logger.info(f"  - {error}")
        
    except Exception as e:
        logger.error(f"任务执行异常: {e}")
    
    # 显示管理器统计（包括失败任务）
    stats = spider_manager.get_statistics()
    logger.info(f"最终统计: 成功 {stats['total_completed']} / 失败 {stats['total_failed']}")


async def main():
    """主函数 - 运行所有示例"""
    logger.info("开始运行爬虫模块使用示例")
    logger.info("=" * 50)
    
    try:
        await example_1_basic_usage()
        await asyncio.sleep(2)
        
        await example_2_spider_manager()
        await asyncio.sleep(2)
        
        await example_3_task_control()
        await asyncio.sleep(2)
        
        await example_4_data_preview()
        await asyncio.sleep(2)
        
        await example_5_error_handling()
        
    except Exception as e:
        logger.error(f"示例运行出错: {e}", exc_info=True)
    
    logger.info("=" * 50)
    logger.info("所有示例运行完成")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main()) 