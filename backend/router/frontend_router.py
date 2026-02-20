
from src.kernel.logger import get_logger
from src.core.components.base.router import BaseRouter
from fastapi.staticfiles import StaticFiles
from pathlib import Path

logger = get_logger(name="Webui_Frontend",color="cyan")

class SPAStaticFiles(StaticFiles):
    """
    支持单页应用(SPA)的静态文件服务
    对于不存在的路径，返回index.html而不是404，让前端路由处理
    """
    async def get_response(self, path: str, scope):
        from starlette.exceptions import HTTPException as StarletteHTTPException

        # 标准化：去掉前导斜杠，保证判断一致
        normalized = (path or "").lstrip("/")

        try:
            return await super().get_response(normalized, scope)
        except Exception as exc:
            # 仅对“未找到”情形回退到 index.html；其它错误应原样抛出
            is_404 = isinstance(exc, FileNotFoundError) or (
                isinstance(exc, StarletteHTTPException) and getattr(exc, "status_code", None) == 404
            )

            # 保留 API / plugins 的原始行为（不做 SPA 回退）
            if normalized.startswith("api/") or normalized.startswith("plugins/"):
                raise

            if not is_404:
                # 非 404 的异常应当暴露出来以便定位问题
                raise

            return await super().get_response("index.html", scope)

class FrontendRouter(BaseRouter):
    """Frontend HTTP路由组件。

        挂载UI前端用于测试
    """

    router_name = "Frontend"
    router_description = "挂载UI前端"

    # 自定义路由路径
    custom_route_path = "/webui/frontend"

    # 允许所有来源访问
    cors_origins = ["*"]

    def register_endpoints(self) -> None:
        """注册HTTP端点。"""
        current_dir = Path(__file__).parent.parent
        static_dir = current_dir / "static"
        
        if static_dir.exists() and static_dir.is_dir():
            # 检查是否有index.html文件
            index_file = static_dir / "index.html"
            if index_file.exists():
                logger.debug(f"发现编译好的前端文件，将托管静态文件: {static_dir}")
                self.app.mount("/", SPAStaticFiles(directory=str(static_dir), html=True), name="static")
            else:
                logger.error("静态目录存在但未找到index.html，不托管静态文件")
        else:
            logger.warning(f"未找到编译好的前端文件(路径: {static_dir})，不托管静态文件")

    async def startup(self) -> None:
        """路由启动钩子。"""

    async def shutdown(self) -> None:
        """路由关闭钩子。"""
