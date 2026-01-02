"""
发现服务器模块
提供一个固定端口的FastAPI服务器,用于前端发现主程序的IP和端口
同时支持托管编译好的前端静态文件
并代理主程序的API请求
"""

import asyncio
from pathlib import Path
from typing import Optional

import httpx
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.common.logger import get_logger

logger = get_logger("WebUIAuth.DiscoveryServer")

# 发现服务器的固定端口
DISCOVERY_PORT = 12138

# 全局变量存储服务器实例
_server_instance: Optional[uvicorn.Server] = None
_server_task: Optional[asyncio.Task] = None


class ServerInfo(BaseModel):
    """主程序服务器信息"""
    host: str
    port: int


class SPAStaticFiles(StaticFiles):
    """
    支持单页应用(SPA)的静态文件服务
    对于不存在的路径，返回index.html而不是404，让前端路由处理
    """
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except Exception:
            # 如果文件不存在，返回index.html
            # 但排除API路径和插件路径
            if path.startswith("api/") or path.startswith("plugins/"):
                logger.info("raise!")
                raise
            return await super().get_response("index.html", scope)


def create_discovery_app(main_host: str, main_port: int) -> FastAPI:
    """
    创建发现服务的FastAPI应用
    
    Args:
        main_host: 主程序的主机地址
        main_port: 主程序的端口
        
    Returns:
        FastAPI应用实例
    """
    app = FastAPI(
        title="MoFox WebUI Discovery Service",
        description="用于前端发现主程序地址的服务",
        version="1.0.0"
    )
    
    # 添加CORS中间件，允许前端跨域访问
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 创建 HTTP 客户端用于转发请求
    http_client = httpx.AsyncClient(timeout=30.0)
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """关闭时清理HTTP客户端"""
        await http_client.aclose()
    
    # 先定义API路由，确保它们不会被静态文件拦截
    @app.get("/api/health", summary="服务状态检查")
    def health_check():
        """检查服务是否运行"""
        return {"status": "ok", "service": "MoFox WebUI Discovery"}
    
    @app.get("/api/server-info", summary="获取主程序服务器信息", response_model=ServerInfo)
    def get_server_info():
        """
        获取主程序的IP和端口信息
        前端通过此接口获取主程序地址，然后自行拼接API地址
        （保留用于调试和兼容性）
        """
        return ServerInfo(
            host=main_host,
            port=main_port
        )
    
    # 🌟 核心功能：代理所有对主程序的 API 请求
    # 注意：这个路由必须在静态文件挂载之前定义
    @app.api_route(
        "/plugins/{path:path}",
        methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
        summary="代理主程序 API 请求",
        include_in_schema=True
    )
    async def proxy_to_main_server(request: Request, path: str):
        """
        将所有 /plugins/* 请求转发到主程序
        前端直接请求 http://hostname:12138/plugins/webui_backend/xxx
        """
        # 构建目标 URL
        target_url = f"http://{main_host}:{main_port}/plugins/{path}"
        
        # 获取查询参数
        query_params = dict(request.query_params)
        
        # 获取请求头（排除 host）
        headers = dict(request.headers)
        headers.pop("host", None)
        
        # 获取请求体
        body = await request.body()
        
        try:
            # 转发请求到主程序
            response = await http_client.request(
                method=request.method,
                url=target_url,
                params=query_params,
                headers=headers,
                content=body,
                follow_redirects=True
            )
            
            # 返回响应
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
            
        except httpx.RequestError as e:
            logger.error(f"代理请求失败 [{request.method} {target_url}]: {e}")
            return Response(
                content=f'{{"error": "无法连接到主程序服务器: {str(e)}"}}',
                status_code=502,
                media_type="application/json"
            )
        except Exception as e:
            logger.error(f"代理请求出错 [{request.method} {target_url}]: {e}")
            return Response(
                content=f'{{"error": "代理请求失败: {str(e)}"}}',
                status_code=500,
                media_type="application/json"
            )
    
    # 最后挂载静态文件，避免拦截API路由
    # 检查是否存在编译好的前端静态文件
    # 使用相对于当前文件的路径定位static目录
    current_dir = Path(__file__).parent
    static_dir = current_dir / "static"
    
    if static_dir.exists() and static_dir.is_dir():
        # 检查是否有index.html文件
        index_file = static_dir / "index.html"
        if index_file.exists():
            logger.debug(f"发现编译好的前端文件，将托管静态文件: {static_dir}")
            app.mount("/", SPAStaticFiles(directory=str(static_dir), html=True), name="static")
        else:
            logger.error("静态目录存在但未找到index.html，不托管静态文件")
    else:
        logger.warning(f"未找到编译好的前端文件(路径: {static_dir})，不托管静态文件")
    
    return app


async def start_discovery_server(
    main_host: str,
    main_port: int,
    discovery_host: str = "0.0.0.0"
) -> None:
    """
    启动发现服务器
    
    Args:
        main_host: 主程序的主机地址
        main_port: 主程序的端口
        discovery_host: 发现服务器绑定的主机地址，默认0.0.0.0（允许外部访问）
    """
    global _server_instance, _server_task
    
    app = create_discovery_app(main_host, main_port)
    
    config = uvicorn.Config(
        app=app,
        host=discovery_host,
        port=DISCOVERY_PORT,
        log_level="warning",  # 减少日志输出
        access_log=False
    )
    
    _server_instance = uvicorn.Server(config)
    
    logger.info(f"发现服务器启动在 http://{discovery_host}:{DISCOVERY_PORT}")
    
    try:
        await _server_instance.serve()
    except Exception as e:
        logger.error(f"发现服务器运行出错: {e}")


async def stop_discovery_server() -> None:
    """停止发现服务器"""
    global _server_instance, _server_task
    
    if _server_instance:
        logger.info("正在停止发现服务器...")
        _server_instance.should_exit = True
        _server_instance = None
    
    if _server_task and not _server_task.done():
        _server_task.cancel()
        try:
            await _server_task
        except asyncio.CancelledError:
            pass
        _server_task = None
    
    logger.info("发现服务器已停止")
