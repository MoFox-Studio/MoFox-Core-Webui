"""实时日志路由组件

提供 WebSocket 端点，用于实时推送系统日志。
通过订阅日志输出事件，将日志实时发送给前端。
"""

import asyncio
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect, Query

from src.kernel.logger import get_logger
from src.core.components.base.router import BaseRouter
from src.core.config.core_config import get_core_config

logger = get_logger(name="RealtimeLog", color="#BB9AF7")


class RealtimeLogRouter(BaseRouter):
    """实时日志路由组件

    提供 WebSocket 端点 /ws/realtime，用于实时推送日志。
    
    API 密钥验证：
    - 通过查询参数 ?api_key=xxx 传递
    - 验证是否在 core.toml 的 http_router.api_keys 列表中

    前端连接示例：
    ws://host:port/plugins/webu/log_viewer/realtime?api_key=your_key
    """

    router_name = "RealtimeLog"
    router_description = "实时日志 WebSocket 接口"

    custom_route_path = "/webui/api/realtime_log"
    cors_origins = ["*"]

    # WebSocket 连接池（类级别变量，所有实例共享）
    active_connections: Set[WebSocket] = set()
    _broadcast_lock: asyncio.Lock = asyncio.Lock()

    def register_endpoints(self) -> None:
        """注册 WebSocket 端点"""

        @self.app.websocket("/realtime")
        async def websocket_endpoint(
            websocket: WebSocket,
            api_key: str = Query(..., description="API 密钥")
        ):
            """
            WebSocket 端点：实时日志推送

            查询参数:
                api_key: API 密钥，用于验证身份

            服务器推送格式:
                {
                    "timestamp": "2026-02-19T17:13:32.223",
                    "level": "DEBUG",
                    "logger_name": "event_manager",
                    "alias": "event_manager",
                    "event": "执行事件处理器: ..."
                }
            """
            # 验证 API 密钥
            try:
                config = get_core_config()
                valid_keys = config.http_router.api_keys
            except RuntimeError:
                logger.error("Core 配置未初始化，无法验证 API 密钥")
                await websocket.close(code=4001, reason="服务配置未初始化")
                return

            if not valid_keys:
                logger.warning("API 密钥列表为空，拒绝 WebSocket 连接")
                await websocket.close(code=4001, reason="服务未配置 API 密钥")
                return

            if api_key not in valid_keys:
                logger.warning(f"无效的 API 密钥（前4位）: {api_key[:4]}****")
                await websocket.close(code=4003, reason="无效的 API 密钥")
                return

            # 接受连接
            await websocket.accept()
            logger.info(f"WebSocket 客户端已连接，当前连接数: {len(self.active_connections) + 1}")

            # 添加到连接池
            async with self._broadcast_lock:
                self.active_connections.add(websocket)

            try:
                # 保持连接，处理客户端消息（如心跳）
                while True:
                    try:
                        data = await websocket.receive_text()
                        
                        # 心跳检测
                        if data == "ping":
                            await websocket.send_text("pong")
                            continue

                    except WebSocketDisconnect:
                        logger.info("WebSocket 客户端已断开")
                        break
                    except Exception as e:
                        logger.error(f"WebSocket 接收消息时出错: {e}")
                        break

            finally:
                # 从连接池移除
                async with self._broadcast_lock:
                    self.active_connections.discard(websocket)
                logger.info(f"WebSocket 客户端已清理，当前连接数: {len(self.active_connections)}")

    @classmethod
    async def broadcast_log(cls, log_data: dict) -> None:
        """
        广播日志到所有已连接的 WebSocket 客户端

        Args:
            log_data: 日志数据字典，包含 timestamp, level, logger_name, event 等字段
        """
        if not cls.active_connections:
            return

        # 格式化日志数据，转换为前端期望的格式
        formatted_log = {
            "timestamp": log_data.get("timestamp", ""),
            "level": log_data.get("level", "INFO"),
            "logger_name": log_data.get("display", log_data.get("logger_name", "")),
            "alias": log_data.get("display", ""),  # 兼容字段
            "logger_color": log_data.get("color"),  # Logger 颜色
            "event": log_data.get("message", "")
        }

        # 广播到所有连接
        async with cls._broadcast_lock:
            # 创建副本以避免在迭代时修改集合
            connections = cls.active_connections.copy()

        disconnected = set()
        for websocket in connections:
            try:
                await websocket.send_json(formatted_log)
            except Exception as e:
                logger.debug(f"发送日志到 WebSocket 失败: {e}")
                disconnected.add(websocket)

        # 清理失败的连接
        if disconnected:
            async with cls._broadcast_lock:
                cls.active_connections -= disconnected

    async def startup(self) -> None:
        logger.info(f"RealtimeLog 路由已启动，路径: {self.custom_route_path}/realtime")
        logger.info("WebSocket 端点可用，等待客户端连接")

    async def shutdown(self) -> None:
        logger.info("RealtimeLog 路由正在关闭，断开所有 WebSocket 连接")
        
        # 关闭所有活动连接
        async with self._broadcast_lock:
            connections = self.active_connections.copy()
            self.active_connections.clear()
        
        for websocket in connections:
            try:
                await websocket.close(code=1001, reason="服务器关闭")
            except Exception:
                pass
        
        logger.info("RealtimeLog 路由已关闭")
