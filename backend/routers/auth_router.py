"""
认证路由组件
提供带有验证的API接口供前端登录和访问
"""

from typing import Optional

from pydantic import BaseModel

from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.plugin_system import BaseRouterComponent

logger = get_logger("WebUIAuth.AuthRouter")


# ==================== 请求/响应模型 ====================

class LoginResponse(BaseModel):
    """登录响应"""
    success: bool
    mmc: Optional[str] = None
    error: Optional[str] = None


class UserInfoResponse(BaseModel):
    """用户信息响应"""
    authenticated: bool
    username: Optional[str] = None
    permissions: list[str] = []


class VerifyTokenRequest(BaseModel):
    """验证Token请求"""
    token: str


class VerifyTokenResponse(BaseModel):
    """验证Token响应"""
    valid: bool
    message: str


# ==================== HTTP路由组件 ====================

class WebUIAuthRouter(BaseRouterComponent):
    """
    WebUI认证路由组件
    
    提供以下API端点：
    - GET /health: 健康检查
    - GET /login: 登录验证
    """
    
    component_name = "auth"
    component_description = "WebUI认证接口"
    
    def register_endpoints(self) -> None:
        """注册所有HTTP端点"""
        
        @self.router.get("/health", summary="健康检查")
        def health_check():
            """
            检查API服务是否正常运行
            此端点不需要认证
            """
            return {"status": "healthy", "service": "WebUI Auth API"}
        
        @self.router.get("/login", summary="登录验证", response_model=LoginResponse)
        def login(_=VerifiedDep):
            """
            登录验证接口
            
            前端在请求头中携带 X-API-Key，如果验证通过则返回成功
            VerifiedDep 会自动验证请求头中的 API Key
            如果 Key 无效，会自动返回 401/403 错误
            
            Returns:
                登录成功响应，包含验证通过的 API Key
            """
            # 如果能到达这里，说明 VerifiedDep 验证通过
            logger.info("用户登录验证成功")
            return LoginResponse(
                success=True,
                mmc="verified"  # 返回标记表示验证成功
            )
