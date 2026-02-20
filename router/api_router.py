"""WebUI API 路由器

提供认证、配置管理等 API 端点。
"""

from src.kernel.logger import get_logger
from src.core.components.base.router import BaseRouter
from src.core.utils.security import VerifiedDep, get_api_key
from fastapi import Depends
from pydantic import BaseModel

logger = get_logger(name="WebUI_API", color="cyan")


class LoginResponse(BaseModel):
    """登录响应模型"""
    success: bool
    message: str = "认证成功"


class ApiRouter(BaseRouter):
    """WebUI API 路由组件
    
    提供认证、配置管理等 API 端点。
    所有端点路径都会加上 /webui 前缀（由 custom_route_path 定义）。
    """

    router_name = "WebUI_API"
    router_description = "WebUI API 接口"

    # 使用与前端 SPA 相同的路由路径
    custom_route_path = "/webui/api/auth"

    # 允许所有来源访问
    cors_origins = ["*"]

    def register_endpoints(self) -> None:
        """注册 API 端点"""
        
        @self.app.get("/login")
        async def login(api_key: str = Depends(get_api_key)) -> LoginResponse:
            """登录认证端点
            
            前端调用流程：
            1. 用户输入密钥
            2. 前端将密钥设置为 token，并通过 X-API-Key 请求头发送
            3. 后端验证密钥是否在 config/core.toml 的 http_router.api_keys 列表中
            4. 验证通过返回成功响应
            
            Returns:
                LoginResponse: 包含 success 和 message 字段
            """
            logger.info(f"用户认证成功（密钥前4位）: {api_key[:4]}****")
            return LoginResponse(success=True, message="认证成功")
        
        @self.app.get("/health")
        async def health_check():
            """健康检查端点（无需认证）"""
            return {"status": "ok"}

    async def startup(self) -> None:
        """路由启动钩子"""
        logger.info(f"API 路由已启动，路径: {self.custom_route_path}")

    async def shutdown(self) -> None:
        """路由关闭钩子"""
        logger.info("API 路由已关闭")
