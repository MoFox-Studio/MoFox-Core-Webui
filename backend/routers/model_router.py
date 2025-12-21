"""
模型配置管理路由组件
提供模型配置、测试、获取可用模型列表等API接口
"""
import time
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.config.config import CONFIG_DIR, model_config
from src.llm_models.model_client.base_client import client_registry
from src.llm_models.payload_content.message import MessageBuilder, RoleType
from src.plugin_system import BaseRouterComponent

logger = get_logger("WebUI.ModelRouter")

# 配置文件根目录
CONFIG_ROOT = Path(CONFIG_DIR)


# ==================== 响应模型 ====================

class ModelTestRequest(BaseModel):
    """模型测试请求"""
    model_name: str  # 模型配置名称（如 "default", "chat" 等）


class ModelTestResponse(BaseModel):
    """模型测试响应"""
    success: bool
    model_name: str
    connected: bool
    response_time: Optional[float] = None  # 响应时间（秒）
    response_text: Optional[str] = None  # 测试响应内容
    error: Optional[str] = None


class GetModelsRequest(BaseModel):
    """获取模型列表请求"""
    provider_name: str  # 提供商名称
    base_url: str  # API地址
    api_key: str  # API密钥
    client_type: str = "openai"  # 客户端类型


class ModelInfo(BaseModel):
    """模型信息"""
    id: str  # 模型ID
    name: str  # 模型显示名称
    created: Optional[int] = None  # 创建时间戳
    owned_by: Optional[str] = None  # 所有者


class GetModelsResponse(BaseModel):
    """获取模型列表响应"""
    success: bool
    models: list[ModelInfo] = []
    error: Optional[str] = None


# ==================== 工具函数 ====================

async def fetch_openai_models(base_url: str, api_key: str) -> list[ModelInfo]:
    """
    从OpenAI兼容的API获取模型列表
    """
    import httpx
    
    # 标准化URL
    if not base_url.startswith(("http://", "https://")):
        base_url = f"https://{base_url}"
    
    # 移除末尾的斜杠以便统一处理
    base_url = base_url.rstrip("/")
    
    # 构建models端点URL，避免重复的路径
    if base_url.endswith("/v1"):
        models_url = f"{base_url}/models"
    elif "/v1/" in base_url:
        # 如果URL中间有/v1/，确保不重复
        models_url = base_url.rstrip("/") + "/models"
    else:
        models_url = f"{base_url}/v1/models"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(models_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        models = []
        for model_data in data.get("data", []):
            models.append(ModelInfo(
                id=model_data.get("id", ""),
                name=model_data.get("id", ""),
                created=model_data.get("created"),
                owned_by=model_data.get("owned_by")
            ))
        
        return models


async def fetch_anthropic_models(api_key: str) -> list[ModelInfo]:
    """
    获取Anthropic可用模型列表（预定义）
    Anthropic API不提供模型列表端点，返回已知的模型
    """
    known_models = [
        ModelInfo(id="claude-3-5-sonnet-20241022", name="Claude 3.5 Sonnet (最新)", owned_by="anthropic"),
        ModelInfo(id="claude-3-5-sonnet-20240620", name="Claude 3.5 Sonnet (6月版)", owned_by="anthropic"),
        ModelInfo(id="claude-3-opus-20240229", name="Claude 3 Opus", owned_by="anthropic"),
        ModelInfo(id="claude-3-sonnet-20240229", name="Claude 3 Sonnet", owned_by="anthropic"),
        ModelInfo(id="claude-3-haiku-20240307", name="Claude 3 Haiku", owned_by="anthropic"),
    ]
    return known_models


async def fetch_gemini_models(base_url: str, api_key: str) -> list[ModelInfo]:
    """
    从Google Gemini API获取模型列表
    支持自定义base_url（例如通过代理访问）
    """
    import httpx
    
    # 标准化URL
    if not base_url.startswith(("http://", "https://")):
        base_url = f"https://{base_url}"
    
    # 移除末尾的斜杠以便统一处理
    base_url = base_url.rstrip("/")
    
    # 构建模型列表URL
    models_url = f"{base_url}/models?key={api_key}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(models_url)
        response.raise_for_status()
        data = response.json()
        
        models = []
        for model_data in data.get("models", []):
            model_name = model_data.get("name", "")
            # 移除 "models/" 前缀
            if model_name.startswith("models/"):
                model_name = model_name[7:]
            
            # 只返回生成模型（不包括嵌入模型）
            if "generateContent" in model_data.get("supportedGenerationMethods", []):
                models.append(ModelInfo(
                    id=model_name,
                    name=model_data.get("displayName", model_name),
                    owned_by="google"
                ))
        
        return models


async def fetch_ollama_models(base_url: str) -> list[ModelInfo]:
    """
    从Ollama API获取本地模型列表
    """
    import httpx
    
    # 标准化URL
    if not base_url.startswith(("http://", "https://")):
        base_url = f"http://{base_url}"
    
    # 移除末尾的斜杠以便统一处理
    base_url = base_url.rstrip("/")
    
    tags_url = f"{base_url}/api/tags"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(tags_url)
        response.raise_for_status()
        data = response.json()
        
        models = []
        for model_data in data.get("models", []):
            models.append(ModelInfo(
                id=model_data.get("name", ""),
                name=model_data.get("name", ""),
                owned_by="ollama"
            ))
        
        return models


# ==================== HTTP路由组件 ====================

class WebUIModelRouter(BaseRouterComponent):
    """
    WebUI模型配置管理路由组件
    
    提供以下API端点：
    - POST /test-model: 测试模型连通性
    - POST /get-models: 获取可用模型列表
    """
    
    component_name = "model"
    component_description = "WebUI模型配置管理接口"
    
    def register_endpoints(self) -> None:
        """注册所有HTTP端点"""
        
        @self.router.post("/test-model", summary="测试模型连通性")
        async def test_model_connection(request: ModelTestRequest, _=VerifiedDep):
            """
            测试指定模型的连通性
            
            Args:
                request: 包含模型名称的请求
            
            返回：
            - 连接状态
            - 响应时间
            - 测试响应内容
            """
            try:
                # 检查 model_config 是否已加载
                if model_config is None:
                    return ModelTestResponse(
                        success=False,
                        model_name=request.model_name,
                        connected=False,
                        error="模型配置未加载"
                    )
                
                # 获取模型信息
                try:
                    model_info = model_config.get_model_info(request.model_name)
                except Exception:
                    return ModelTestResponse(
                        success=True,
                        model_name=request.model_name,
                        connected=False,
                        error=f"未找到模型配置: {request.model_name}"
                    )
                
                # 获取 API 提供商配置
                try:
                    api_provider = model_config.get_provider(model_info.api_provider)
                except Exception:
                    return ModelTestResponse(
                        success=True,
                        model_name=request.model_name,
                        connected=False,
                        error=f"未找到 API 提供商配置: {model_info.api_provider}"
                    )
                
                # 获取客户端实例
                try:
                    client = client_registry.get_client_class_instance(api_provider)
                except Exception as e:
                    return ModelTestResponse(
                        success=True,
                        model_name=request.model_name,
                        connected=False,
                        error=f"无法创建客户端实例: {str(e)}"
                    )
                
                # 构建测试消息
                test_prompt = "你好，这是一条测试消息，请简单回复'好的'即可。"
                message = MessageBuilder().set_role(RoleType.User).add_text_content(test_prompt).build()
                
                # 记录开始时间
                start_time = time.time()
                
                # 发送测试请求
                try:
                    response = await client.get_response(
                        model_info=model_info,
                        message_list=[message],
                        temperature=0.7,
                        max_tokens=50
                    )
                    
                    # 计算响应时间
                    response_time = time.time() - start_time
                    
                    if response and response.content:
                        logger.info(f"模型 {request.model_name} 测试成功，响应时间: {response_time:.2f}秒")
                        return ModelTestResponse(
                            success=True,
                            model_name=request.model_name,
                            connected=True,
                            response_time=round(response_time, 2),
                            response_text=response.content[:200]  # 限制响应长度
                        )
                    else:
                        logger.warning(f"模型 {request.model_name} 返回空响应")
                        return ModelTestResponse(
                            success=True,
                            model_name=request.model_name,
                            connected=False,
                            response_time=round(response_time, 2),
                            error="模型返回空响应"
                        )
                        
                except Exception as e:
                    response_time = time.time() - start_time
                    logger.error(f"模型 {request.model_name} 请求失败: {e}")
                    return ModelTestResponse(
                        success=True,
                        model_name=request.model_name,
                        connected=False,
                        response_time=round(response_time, 2),
                        error=f"请求失败: {str(e)}"
                    )
                    
            except Exception as e:
                logger.error(f"测试模型 {request.model_name} 时出错: {e}")
                return ModelTestResponse(
                    success=False,
                    model_name=request.model_name,
                    connected=False,
                    error=str(e)
                )
        
        @self.router.post("/get-models", summary="获取可用模型列表")
        async def get_available_models(request: GetModelsRequest, _=VerifiedDep):
            """
            根据提供商类型获取可用的模型列表
            
            Args:
                request: 包含提供商信息的请求
            
            返回：
            - 模型列表
            """
            try:
                logger.info(f"获取模型列表: provider={request.provider_name}, client_type={request.client_type}")
                
                client_type = request.client_type.lower()
                
                # 根据客户端类型调用不同的获取方法
                if client_type == "anthropic":
                    models = await fetch_anthropic_models(request.api_key)
                elif client_type == "gemini" or client_type == "aiohttp_gemini":
                    models = await fetch_gemini_models(request.base_url, request.api_key)
                elif client_type == "ollama":
                    models = await fetch_ollama_models(request.base_url)
                else:  # openai 或其他兼容OpenAI的
                    models = await fetch_openai_models(request.base_url, request.api_key)
                
                logger.info(f"成功获取 {len(models)} 个模型")
                return GetModelsResponse(
                    success=True,
                    models=models
                )
                
            except Exception as e:
                logger.error(f"获取模型列表失败: {e}")
                return GetModelsResponse(
                    success=False,
                    error=str(e)
                )
