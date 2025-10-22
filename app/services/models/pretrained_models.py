"""
预训练模型管理器
负责下载、缓存和加载来自HuggingFace等平台的预训练模型
"""
import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, Optional, Any
import torch
from transformers import AutoTokenizer, AutoModel, pipeline
from sentence_transformers import SentenceTransformer
import jieba

from .model_config import ModelConfig

logger = logging.getLogger(__name__)

class PretrainedModelManager:
    """预训练模型管理器"""
    
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = ModelConfig()
        self.loaded_models = {}
        
        # 设置环境变量，指定模型缓存目录
        os.environ['TRANSFORMERS_CACHE'] = str(self.cache_dir / "transformers")
        os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(self.cache_dir / "sentence_transformers")
    
    async def load_all_models(self) -> Dict[str, bool]:
        """加载所有预训练模型"""
        results = {}
        
        for model_name, model_info in self.config.PRETRAINED_MODELS.items():
            try:
                logger.info(f"加载预训练模型: {model_name}")
                success = await self._load_single_pretrained_model(model_name, model_info)
                results[model_name] = success
                
                if success:
                    logger.info(f"✅ {model_name} 加载成功")
                else:
                    logger.warning(f"⚠️ {model_name} 加载失败")
                    
            except Exception as e:
                logger.error(f"❌ {model_name} 加载失败: {e}")
                results[model_name] = False
        
        return results
    
    async def _load_single_pretrained_model(self, model_name: str, model_info) -> bool:
        """加载单个预训练模型"""
        try:
            if model_name == "sentence_transformer":
                return await self._load_sentence_transformer(model_info)
            
            elif model_name == "chinese_bert":
                return await self._load_chinese_bert(model_info)
            
            elif model_name == "chinese_sentiment":
                return await self._load_chinese_sentiment(model_info)
            
            elif model_name == "jieba":
                return await self._load_jieba(model_info)
            
            else:
                logger.warning(f"未知的预训练模型类型: {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"加载 {model_name} 失败: {e}")
            return False
    
    async def _load_sentence_transformer(self, model_info) -> bool:
        """加载句向量模型"""
        try:
            # 在线程池中执行，避免阻塞事件循环
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(
                None, 
                lambda: SentenceTransformer(model_info.name, cache_folder=str(self.cache_dir / "sentence_transformers"))
            )
            
            self.loaded_models["sentence_transformer"] = model
            return True
            
        except Exception as e:
            logger.error(f"SentenceTransformer加载失败: {e}")
            return False
    
    async def _load_chinese_bert(self, model_info) -> bool:
        """加载中文BERT模型"""
        try:
            loop = asyncio.get_event_loop()
            
            # 加载tokenizer
            tokenizer = await loop.run_in_executor(
                None,
                lambda: AutoTokenizer.from_pretrained(
                    model_info.name,
                    cache_dir=str(self.cache_dir / "transformers")
                )
            )
            
            # 加载模型
            model = await loop.run_in_executor(
                None,
                lambda: AutoModel.from_pretrained(
                    model_info.name,
                    cache_dir=str(self.cache_dir / "transformers")
                )
            )
            
            self.loaded_models["chinese_bert"] = {
                "tokenizer": tokenizer,
                "model": model
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Chinese BERT加载失败: {e}")
            return False
    
    async def _load_chinese_sentiment(self, model_info) -> bool:
        """加载中文情感分析模型"""
        try:
            loop = asyncio.get_event_loop()
            
            sentiment_pipeline = await loop.run_in_executor(
                None,
                lambda: pipeline(
                    "sentiment-analysis",
                    model=model_info.name,
                    tokenizer=model_info.name,
                    model_kwargs={"cache_dir": str(self.cache_dir / "transformers")}
                )
            )
            
            self.loaded_models["chinese_sentiment"] = sentiment_pipeline
            return True
            
        except Exception as e:
            logger.error(f"Chinese Sentiment模型加载失败: {e}")
            return False
    
    async def _load_jieba(self, model_info) -> bool:
        """初始化jieba分词器"""
        try:
            # jieba是轻量级的，可以直接初始化
            jieba.initialize()
            self.loaded_models["jieba"] = jieba
            return True
            
        except Exception as e:
            logger.error(f"Jieba初始化失败: {e}")
            return False
    
    async def load_model(self, model_name: str) -> Optional[Any]:
        """加载指定的预训练模型"""
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        if model_name not in self.config.PRETRAINED_MODELS:
            logger.warning(f"未找到预训练模型配置: {model_name}")
            return None
        
        model_info = self.config.PRETRAINED_MODELS[model_name]
        success = await self._load_single_pretrained_model(model_name, model_info)
        
        if success:
            return self.loaded_models.get(model_name)
        else:
            return None
    
    async def update_model(self, model_name: str) -> bool:
        """更新预训练模型（重新下载）"""
        try:
            # 清除缓存中的模型
            if model_name in self.loaded_models:
                del self.loaded_models[model_name]
            
            # 重新加载
            model_info = self.config.PRETRAINED_MODELS[model_name]
            return await self._load_single_pretrained_model(model_name, model_info)
            
        except Exception as e:
            logger.error(f"更新模型 {model_name} 失败: {e}")
            return False
    
    def get_model_info(self) -> Dict:
        """获取预训练模型信息"""
        info = {
            "total_models": len(self.config.PRETRAINED_MODELS),
            "loaded_models": len(self.loaded_models),
            "cache_dir": str(self.cache_dir),
            "models": {}
        }
        
        for name, model_info in self.config.PRETRAINED_MODELS.items():
            info["models"][name] = {
                "name": model_info.name,
                "source": model_info.source,
                "size_mb": model_info.size_mb,
                "description": model_info.description,
                "required": model_info.required,
                "loaded": name in self.loaded_models
            }
        
        return info
    
    def check_disk_space(self) -> Dict:
        """检查磁盘空间"""
        try:
            import shutil
            
            total_size = self.config.estimate_total_size()
            free_space = shutil.disk_usage(self.cache_dir).free // (1024 * 1024)  # MB
            
            return {
                "required_space_mb": total_size,
                "available_space_mb": free_space,
                "sufficient": free_space > total_size * 1.2  # 留20%余量
            }
            
        except Exception as e:
            logger.error(f"检查磁盘空间失败: {e}")
            return {"error": str(e)}
    
    async def cleanup_cache(self):
        """清理模型缓存"""
        try:
            import shutil
            
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info("模型缓存已清理")
            
            self.loaded_models.clear()
            
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")

# 使用示例
async def download_required_models():
    """下载必需的预训练模型"""
    manager = PretrainedModelManager("./model_cache/pretrained")
    
    # 检查磁盘空间
    space_info = manager.check_disk_space()
    if not space_info.get("sufficient", False):
        logger.warning(f"磁盘空间可能不足: {space_info}")
    
    # 加载所有模型
    results = await manager.load_all_models()
    
    # 输出结果
    success_count = sum(results.values())
    total_count = len(results)
    
    logger.info(f"模型下载完成: {success_count}/{total_count}")
    
    return manager 