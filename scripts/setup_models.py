#!/usr/bin/env python3
"""
模型环境设置脚本
快速下载和配置所有必需的模型
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent.parent))

from app.services.models.model_manager import model_manager
from app.services.models.pretrained_models import download_required_models
from app.services.models.custom_models import train_all_models_with_sample_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def setup_all_models():
    """设置所有模型"""
    print("🚀 开始设置反馈分析系统模型...")
    
    try:
        # 1. 检查系统要求
        print("\n📋 检查系统要求...")
        check_system_requirements()
        
        # 2. 创建模型目录
        print("\n📁 创建模型目录...")
        create_model_directories()
        
        # 3. 下载预训练模型
        print("\n⬇️ 下载预训练模型...")
        await download_pretrained_models()
        
        # 4. 训练自定义模型（使用示例数据）
        print("\n🔨 训练自定义模型...")
        await train_custom_models()
        
        # 5. 验证模型设置
        print("\n✅ 验证模型设置...")
        await verify_model_setup()
        
        print("\n🎉 模型设置完成！系统已准备就绪。")
        
    except Exception as e:
        logger.error(f"模型设置失败: {e}")
        print(f"\n❌ 模型设置失败: {e}")
        sys.exit(1)

def check_system_requirements():
    """检查系统要求"""
    import torch
    import transformers
    import sklearn
    
    print(f"✓ Python: {sys.version}")
    print(f"✓ PyTorch: {torch.__version__}")
    print(f"✓ Transformers: {transformers.__version__}")
    print(f"✓ Scikit-learn: {sklearn.__version__}")
    
    # 检查GPU
    if torch.cuda.is_available():
        print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("⚠️ GPU: 未检测到CUDA，将使用CPU模式")
    
    # 检查磁盘空间
    import shutil
    free_space = shutil.disk_usage('.').free // (1024 * 1024 * 1024)  # GB
    print(f"✓ 可用磁盘空间: {free_space}GB")
    
    if free_space < 2:
        print("⚠️ 警告：磁盘空间不足，建议至少有2GB可用空间")

def create_model_directories():
    """创建模型目录"""
    directories = [
        "models",
        "models/pretrained",
        "models/pretrained/transformers",
        "models/pretrained/sentence_transformers", 
        "models/custom",
        "models/logs"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ 创建目录: {dir_path}")

async def download_pretrained_models():
    """下载预训练模型"""
    try:
        # 使用预训练模型管理器
        manager = await download_required_models()
        
        info = manager.get_model_info()
        loaded_count = info['loaded_models']
        total_count = info['total_models']
        
        print(f"✓ 预训练模型下载完成: {loaded_count}/{total_count}")
        
        # 显示模型详情
        for name, model_info in info['models'].items():
            status = "✅" if model_info['loaded'] else "❌"
            print(f"  {status} {name}: {model_info['description']}")
        
    except Exception as e:
        logger.error(f"预训练模型下载失败: {e}")
        raise

async def train_custom_models():
    """训练自定义模型"""
    try:
        # 使用示例数据训练
        results = await train_all_models_with_sample_data()
        
        print("✓ 自定义模型训练完成:")
        
        for model_name, result in results.items():
            if result.success:
                print(f"  ✅ {model_name}: 准确率 {result.accuracy:.3f}")
            else:
                print(f"  ❌ {model_name}: {result.error_message}")
        
    except Exception as e:
        logger.error(f"自定义模型训练失败: {e}")
        raise

async def verify_model_setup():
    """验证模型设置"""
    try:
        # 初始化模型管理器
        results = await model_manager.initialize_all_models()
        
        success_count = sum(results.values())
        total_count = len(results)
        
        print(f"✓ 模型验证完成: {success_count}/{total_count}")
        
        # 获取详细信息
        info = model_manager.get_model_info()
        
        print("\n📊 模型状态详情:")
        print(f"  - 预训练模型: {info['pretrained_models']['loaded_models']}/{info['pretrained_models']['total_models']}")
        print(f"  - 自定义模型: {info['custom_models']['loaded_models']}/{info['custom_models']['total_models']}")
        print(f"  - 模型目录: {info['model_dir']}")
        
        if success_count == total_count:
            print("🎯 所有模型加载成功！")
        else:
            print("⚠️ 部分模型加载失败，但系统仍可运行")
        
    except Exception as e:
        logger.error(f"模型验证失败: {e}")
        raise

def print_usage():
    """打印使用说明"""
    print("""
🤖 反馈分析系统 - 模型设置工具

用法:
    python setup_models.py [选项]

选项:
    --help          显示此帮助信息
    --check-only    仅检查系统要求，不下载模型
    --download-only 仅下载预训练模型
    --train-only    仅训练自定义模型

示例:
    # 完整设置（推荐）
    python setup_models.py
    
    # 仅检查系统
    python setup_models.py --check-only
    
    # 仅下载预训练模型
    python setup_models.py --download-only

注意:
    - 首次运行需要下载约1GB的模型文件
    - 建议在良好的网络环境下运行
    - 如有GPU，会自动使用GPU加速
    """)

async def main():
    """主函数"""
    args = sys.argv[1:]
    
    if "--help" in args:
        print_usage()
        return
    
    if "--check-only" in args:
        print("🔍 检查系统要求...")
        check_system_requirements()
        return
    
    if "--download-only" in args:
        print("⬇️ 下载预训练模型...")
        create_model_directories()
        await download_pretrained_models()
        return
    
    if "--train-only" in args:
        print("🔨 训练自定义模型...")
        create_model_directories()
        await train_custom_models()
        return
    
    # 默认：完整设置
    await setup_all_models()

if __name__ == "__main__":
    asyncio.run(main()) 