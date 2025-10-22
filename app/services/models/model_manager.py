"""
统一模型管理器
负责协调预训练模型和自训练模型的加载、更新和管理
"""
import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, Optional, Any
import joblib
import torch
from datetime import datetime

from .pretrained_models import PretrainedModelManager
from .custom_models import CustomModelManager
from .model_config import ModelConfig
from ...core.config import settings

logger = logging.getLogger(__name__)

class ModelManager:
    """统一模型管理器"""
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        # 子管理器
        self.pretrained_manager = PretrainedModelManager(self.model_dir / "pretrained")
        self.custom_manager = CustomModelManager(self.model_dir / "custom")
        
        # 模型配置
        self.config = ModelConfig()
        
        # 已加载的模型缓存
        self.loaded_models = {}
        
        # 模型状态
        self.model_status = {}
    
    async def initialize_all_models(self) -> Dict[str, bool]:
        """初始化所有模型"""
        logger.info("开始初始化所有模型...")
        
        results = {}
        
        try:
            # 1. 初始化预训练模型
            logger.info("加载预训练模型...")
            pretrained_results = await self.pretrained_manager.load_all_models()
            results.update(pretrained_results)
            
            # 2. 初始化自训练模型
            logger.info("加载自训练模型...")
            custom_results = await self.custom_manager.load_all_models()
            results.update(custom_results)
            
            # 3. 更新模型状态
            self._update_model_status(results)
            
            logger.info(f"模型初始化完成，成功加载: {sum(results.values())}/{len(results)}")
            
        except Exception as e:
            logger.error(f"模型初始化失败: {e}")
            raise
        
        return results
    
    async def get_model(self, model_name: str) -> Optional[Any]:
        """获取指定模型"""
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        # 尝试加载模型
        model = await self._load_single_model(model_name)
        if model:
            self.loaded_models[model_name] = model
        
        return model
    
    async def _load_single_model(self, model_name: str) -> Optional[Any]:
        """加载单个模型"""
        # 检查是否为预训练模型
        if model_name in self.config.PRETRAINED_MODELS:
            return await self.pretrained_manager.load_model(model_name)
        
        # 检查是否为自训练模型
        if model_name in self.config.CUSTOM_MODELS:
            return await self.custom_manager.load_model(model_name)
        
        logger.warning(f"未知模型: {model_name}")
        return None
    
    def _update_model_status(self, results: Dict[str, bool]):
        """更新模型状态"""
        for model_name, success in results.items():
            self.model_status[model_name] = {
                "loaded": success,
                "last_update": datetime.now(),
                "type": self._get_model_type(model_name)
            }
    
    def _get_model_type(self, model_name: str) -> str:
        """获取模型类型"""
        if model_name in self.config.PRETRAINED_MODELS:
            return "pretrained"
        elif model_name in self.config.CUSTOM_MODELS:
            return "custom"
        else:
            return "unknown"
    
    async def train_custom_model(self, model_name: str, training_data: Any) -> bool:
        """训练自定义模型"""
        return await self.custom_manager.train_model(model_name, training_data)
    
    async def update_model(self, model_name: str) -> bool:
        """更新模型"""
        if model_name in self.config.PRETRAINED_MODELS:
            return await self.pretrained_manager.update_model(model_name)
        elif model_name in self.config.CUSTOM_MODELS:
            return await self.custom_manager.retrain_model(model_name)
        else:
            logger.warning(f"无法更新未知模型: {model_name}")
            return False
    
    def get_model_info(self) -> Dict:
        """获取所有模型信息"""
        return {
            "pretrained_models": self.pretrained_manager.get_model_info(),
            "custom_models": self.custom_manager.get_model_info(),
            "model_status": self.model_status,
            "total_models": len(self.loaded_models),
            "model_dir": str(self.model_dir)
        }
    
    async def cleanup_models(self):
        """清理模型资源"""
        logger.info("清理模型资源...")
        
        # 清理GPU内存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # 清理加载的模型
        self.loaded_models.clear()
        
        logger.info("模型资源清理完成")

# 全局模型管理器实例
model_manager = ModelManager()

async def get_model_manager() -> ModelManager:
    """获取模型管理器实例"""
    return model_manager 