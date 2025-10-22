from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database
from app.core.database import get_db
from app.models.settings import AppSettings, SettingsInDB
import httpx
import logging
from typing import List, Dict

router = APIRouter()
logger = logging.getLogger(__name__)

SETTINGS_COLLECTION = "settings"
GLOBAL_SETTINGS_ID = "global"

@router.get("/settings", response_model=AppSettings)
async def get_settings(db: Database = Depends(get_db)):
    """
    Retrieve the global application settings.
    If no settings are found, create and return the default settings.
    """
    settings_doc = await db[SETTINGS_COLLECTION].find_one({"_id": GLOBAL_SETTINGS_ID})
    if settings_doc:
        # Pydantic V2 doesn't use .dict(), it serializes directly
        return AppSettings.model_validate(settings_doc["settings"])
    
    # If no settings exist, create default ones
    default_settings = SettingsInDB(id=GLOBAL_SETTINGS_ID)
    # Pydantic V2 uses .model_dump() instead of .dict()
    await db[SETTINGS_COLLECTION].insert_one({"_id": GLOBAL_SETTINGS_ID, "settings": default_settings.settings.model_dump()})
    return default_settings.settings

@router.post("/settings", response_model=AppSettings)
async def update_settings(settings: AppSettings, db: Database = Depends(get_db)):
    """
    Update the global application settings.
    """
    # Pydantic V2 uses .model_dump() instead of .dict()
    update_data = {"settings": settings.model_dump()}
    result = await db[SETTINGS_COLLECTION].update_one(
        {"_id": GLOBAL_SETTINGS_ID},
        {"$set": update_data},
        upsert=True
    )
    
    if result.modified_count == 0 and not result.upserted_id:
        # This case might happen if the settings submitted are identical to what's in the DB
        # We can just return the submitted settings as they are now the current state.
        pass

    return settings

@router.get("/llm/models")
async def get_available_llm_models(db: Database = Depends(get_db)) -> Dict:
    """
    获取可用的LLM模型列表，实时从theturbo.ai获取
    """
    try:
        # 获取当前设置
        settings_doc = await db[SETTINGS_COLLECTION].find_one({"_id": GLOBAL_SETTINGS_ID})
        if not settings_doc:
            # 使用默认配置
            default_settings = SettingsInDB(id=GLOBAL_SETTINGS_ID)
            theturbo_api_key = default_settings.settings.analysis.llm.theturbo_api_key
            theturbo_base_url = default_settings.settings.analysis.llm.theturbo_base_url
        else:
            app_settings = AppSettings.model_validate(settings_doc["settings"])
            theturbo_api_key = app_settings.analysis.llm.theturbo_api_key
            theturbo_base_url = app_settings.analysis.llm.theturbo_base_url
        
        # 调用theturbo.ai API获取模型列表
        models_url = f"{theturbo_base_url.rstrip('/')}/models"
        headers = {
            "Authorization": f"Bearer {theturbo_api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                models_url,
                headers=headers,
                params={"apikey": theturbo_api_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"成功获取theturbo.ai模型列表，共{len(data.get('data', []))}个模型")
                return {
                    "success": True,
                    "models": data.get('data', []),
                    "source": "theturbo.ai"
                }
            else:
                logger.error(f"获取theturbo.ai模型列表失败: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"API调用失败: {response.text}")
                
    except httpx.TimeoutException:
        logger.error("获取theturbo.ai模型列表超时")
        raise HTTPException(status_code=408, detail="请求超时")
    except httpx.RequestError as e:
        logger.error(f"获取theturbo.ai模型列表网络错误: {e}")
        raise HTTPException(status_code=500, detail=f"网络错误: {str(e)}")
    except Exception as e:
        logger.error(f"获取theturbo.ai模型列表失败: {e}")
        # 返回备用模型列表
        fallback_models = [
            {"id": "gpt-4", "object": "model", "owned_by": "openai"},
            {"id": "gpt-3.5-turbo", "object": "model", "owned_by": "openai"},
            {"id": "claude-3-haiku", "object": "model", "owned_by": "anthropic"},
            {"id": "claude-3-sonnet", "object": "model", "owned_by": "anthropic"}
        ]
        return {
            "success": False,
            "models": fallback_models,
            "source": "fallback",
            "error": str(e)
        }
