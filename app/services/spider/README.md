# Spider 爬虫模块

## 概述

Spider爬虫模块是FeedbackAnalyzeCursor系统的数据采集子系统，提供专业的多平台用户反馈数据自动化抓取能力。

## 架构设计

### 核心组件

1. **BaseSpider** - 爬虫基类
   - 提供统一的爬虫接口规范
   - 异步HTTP请求管理
   - 智能重试和错误处理
   - 完整的生命周期管理

2. **QimaiSpider** - 七麦数据爬虫
   - 专业的App Store评论数据抓取
   - 支持分页抓取和智能解析
   - 自动数据格式转换

3. **SpiderManager** - 爬虫管理器
   - 多任务并发控制
   - 任务状态监控
   - 资源管理和清理

## 快速开始

### 1. 基础使用

```python
from app.services.spider import create_qimai_spider

# 创建爬虫实例
spider = create_qimai_spider(
    appid="1329458504",  # App ID
    country="cn",        # 国家代码
    days_back=30,        # 抓取天数
    max_pages=10         # 最大页数
)

# 运行爬虫
async with spider:
    result = await spider.run()
    print(f"抓取了 {len(result.data)} 条数据")
```

### 2. 使用管理器

```python
from app.services.spider import get_spider_manager

# 获取管理器
manager = get_spider_manager()

# 创建任务
task_id = manager.create_qimai_task(
    appid="1329458504",
    country="cn",
    days_back=7,
    max_pages=5
)

# 运行任务
result = await manager.run_task(task_id)
```

## API 端点

### 任务管理
- `POST /api/v1/spider/qimai/create` - 创建七麦任务
- `POST /api/v1/spider/task/run` - 异步运行任务
- `POST /api/v1/spider/task/run-sync` - 同步运行任务
- `POST /api/v1/spider/task/batch-run` - 批量运行任务

### 任务控制
- `POST /api/v1/spider/task/stop` - 停止任务
- `POST /api/v1/spider/task/pause` - 暂停任务
- `POST /api/v1/spider/task/resume` - 恢复任务

### 状态查询
- `GET /api/v1/spider/task/{task_id}/status` - 获取任务状态
- `GET /api/v1/spider/task/list` - 获取所有任务
- `GET /api/v1/spider/task/running` - 获取运行中任务

## 配置参数

### QimaiSpider 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| appid | str | 必填 | 应用ID |
| country | str | "cn" | 国家代码 |
| days_back | int | 365 | 回溯天数 |
| max_pages | int | 100 | 最大抓取页数 |

### SpiderConfig 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| max_concurrent | int | 3 | 最大并发数 |
| request_delay | float | 2.0 | 请求间隔(秒) |
| retry_times | int | 3 | 重试次数 |
| timeout | int | 30 | 超时时间(秒) |

## 许可证

本模块遵循项目整体的许可证协议。
