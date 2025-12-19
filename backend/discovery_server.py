"""
发现服务器模块
提供一个固定端口的FastAPI服务器,用于前端发现主程序的IP和端口
同时支持托管编译好的前端静态文件
"""

import asyncio
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI
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
    
    # 检查是否存在编译好的前端静态文件
    # 使用相对于当前文件的路径定位static目录
    current_dir = Path(__file__).parent
    static_dir = current_dir / "static"
    
    if static_dir.exists() and static_dir.is_dir():
        # 检查是否有index.html文件
        index_file = static_dir / "index.html"
        if index_file.exists():
            logger.info(f"发现编译好的前端文件，将托管静态文件: {static_dir}")
            # 挂载静态文件目录
            app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
        else:
            logger.info("静态目录存在但未找到index.html，不托管静态文件")
    else:
        logger.info(f"未找到编译好的前端文件(路径: {static_dir})，不托管静态文件")
    
    @app.get("/api/health", summary="服务状态检查")
    def health_check():
        """检查服务是否运行"""
        return {"status": "ok", "service": "MoFox WebUI Discovery"}
    
    @app.get("/api/server-info", summary="获取主程序服务器信息", response_model=ServerInfo)
    def get_server_info():
        """
        获取主程序的IP和端口信息
        前端通过此接口获取主程序地址，然后自行拼接API地址
        """
        return ServerInfo(
            host=main_host,
            port=main_port
        )
    
    return app


async def start_discovery_server(
    main_host: str,
    main_port: int,
    discovery_host: str = "127.0.0.1"
) -> None:
    """
    启动发现服务器
    
    Args:
        main_host: 主程序的主机地址
        main_port: 主程序的端口
        discovery_host: 发现服务器绑定的主机地址，默认127.0.0.1
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
    logger.info(f"主程序地址配置为 http://{main_host}:{main_port}")
    
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
