"""实时聊天路由组件

提供 WebSocket 端点用于实时消息推送，以及 HTTP API 端点用于：
- 获取聊天流列表
- 获取历史消息
- 发送消息
"""

import asyncio
import json
from typing import Set, Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect, Query, HTTPException
from pydantic import BaseModel

from src.kernel.logger import get_logger
from src.core.components.base.router import BaseRouter
from src.core.utils.security import VerifiedDep

logger = get_logger(name="LiveChat", color="#F5C2E7")


# ==================== Pydantic 模型 ====================

class StreamInfo(BaseModel):
    """聊天流信息模型"""
    stream_id: str
    platform: str
    user_id: str = ""
    group_id: str = ""
    chat_type: str
    last_message_time: Optional[float] = None
    last_message_content: str = ""
    unread_count: int = 0


class MessageInfo(BaseModel):
    """消息信息模型"""
    message_id: str
    stream_id: str
    platform: str
    chat_type: str
    time: float
    content: str
    sender_id: str
    sender_name: str
    is_sent: bool = False
    is_bot: bool = False
    is_webui: bool = False
    images: list[dict[str, str]] = []
    reply_message_id: Optional[str] = None
    metadata: dict[str, Any] = {}


class SendMessageRequest(BaseModel):
    """发送消息请求模型"""
    stream_id: str
    content: str
    message_type: str = "text"  # text, image, emoji


class SendMessageResponse(BaseModel):
    """发送消息响应模型"""
    success: bool
    message: str = ""
    message_id: Optional[str] = None


# ==================== LiveChatRouter ====================

class LiveChatRouter(BaseRouter):
    """实时聊天路由组件

    提供 WebSocket 端点 /ws 用于实时消息推送。
    提供 HTTP API 端点用于获取聊天流、历史消息和发送消息。
    
    API 密钥验证：
    - WebSocket 通过查询参数 ?api_key=xxx 传递
    - HTTP API 通过 X-API-Key 请求头传递

    前端连接示例：
    - WebSocket: ws://host:port/webui/api/live_chat/ws?api_key=your_key
    - HTTP: GET http://host:port/webui/api/live_chat/streams
    """

    router_name = "LiveChat"
    router_description = "实时聊天 WebSocket 和 HTTP API 接口"

    custom_route_path = "/webui/api/live_chat"
    cors_origins = ["*"]

    # WebSocket 连接池（类级别变量，所有实例共享）
    # stream_id -> Set[WebSocket]
    active_connections: Dict[str, Set[WebSocket]] = {}
    _broadcast_lock: asyncio.Lock = asyncio.Lock()

    def register_endpoints(self) -> None:
        """注册 WebSocket 和 HTTP 端点"""

        # ==================== WebSocket 端点 ====================

        @self.app.websocket("/ws")
        async def websocket_endpoint(
            websocket: WebSocket,
            api_key: str = Query(..., description="API 密钥")
        ):
            """
            WebSocket 端点：实时消息推送

            查询参数:
                api_key: API 密钥，用于验证身份

            客户端消息格式:
                {
                    "type": "subscribe",
                    "stream_id": "qq_group_123456"
                }
                {
                    "type": "unsubscribe",
                    "stream_id": "qq_group_123456"
                }
                {
                    "type": "ping"
                }

            服务器推送格式:
                {
                    "type": "message",
                    "data": {
                        "message_id": "...",
                        "stream_id": "...",
                        "content": "...",
                        ...
                    }
                }
                {
                    "type": "subscribed",
                    "stream_id": "..."
                }
            """
            # 验证 API 密钥
            from src.core.config.core_config import get_core_config
            try:
                config = get_core_config()
                valid_keys = config.http_router.api_keys
                if not valid_keys or api_key not in valid_keys:
                    await websocket.close(code=4003, reason="无效的 API 密钥")
                    return
            except Exception as e:
                logger.error(f"验证 API 密钥失败: {e}")
                await websocket.close(code=4001, reason="服务配置错误")
                return

            # 接受连接
            await websocket.accept()
            logger.info("WebSocket 客户端已连接")

            # 当前订阅的流
            subscribed_streams: Set[str] = set()

            try:
                # 保持连接，处理客户端消息
                while True:
                    try:
                        # 接收文本消息
                        text = await websocket.receive_text()
                        
                        # 如果是空消息，跳过
                        if not text or not text.strip():
                            continue
                        
                        # 处理纯文本心跳（前端可能发送 "ping" 而不是 JSON）
                        if text.strip() == "ping":
                            await websocket.send_text("pong")
                            continue
                        
                        # 解析 JSON
                        try:
                            data = json.loads(text)
                        except json.JSONDecodeError as e:
                            logger.warning(f"收到无效的 JSON 消息: {text[:100]}, 错误: {e}")
                            continue
                        
                        msg_type = data.get("type")
                        
                        # 订阅流
                        if msg_type == "subscribe":
                            stream_id = data.get("stream_id")
                            if stream_id:
                                await self._subscribe_stream(websocket, stream_id)
                                subscribed_streams.add(stream_id)
                                await websocket.send_json({
                                    "type": "subscribed",
                                    "stream_id": stream_id
                                })
                                logger.debug(f"客户端订阅流: {stream_id}")

                        # 取消订阅流
                        elif msg_type == "unsubscribe":
                            stream_id = data.get("stream_id")
                            if stream_id:
                                await self._unsubscribe_stream(websocket, stream_id)
                                subscribed_streams.discard(stream_id)
                                logger.debug(f"客户端取消订阅流: {stream_id}")

                        # 心跳检测
                        elif msg_type == "ping":
                            await websocket.send_json({"type": "pong"})

                    except WebSocketDisconnect:
                        logger.info("WebSocket 客户端已断开")
                        break
                    except Exception as e:
                        logger.error(f"WebSocket 接收消息时出错: {e}")
                        break

            finally:
                # 清理订阅
                for stream_id in subscribed_streams:
                    await self._unsubscribe_stream(websocket, stream_id)
                logger.info("WebSocket 客户端已清理")

        # ==================== HTTP API 端点 ====================

        @self.app.get("/streams", response_model=list[StreamInfo])
        async def get_streams(
            limit: int = Query(100, description="最大返回数量"),
            _ = VerifiedDep
        ):
            """
            获取聊天流列表

            查询参数:
                limit: 最大返回数量

            返回:
                聊天流信息列表，按最后消息时间降序排序
            """

            try:
                from src.kernel.db import QueryBuilder
                from src.core.models.sql_alchemy import ChatStreams

                # 查询所有聊天流
                streams_query = QueryBuilder(ChatStreams).order_by("-last_message_time").limit(limit)
                streams = await streams_query.all(as_dict=True)

                result = []
                for stream in streams:
                    if str(stream.get("platform", "")) == "astrbot":
                        continue
                    stream_info = StreamInfo(
                        stream_id=str(stream.get("stream_id", "")),
                        platform=str(stream.get("platform", "")),
                        user_id=str(stream.get("user_id", "")),
                        group_id=str(stream.get("group_id", "")),
                        chat_type=str(stream.get("chat_type", "private")),
                        last_message_time=stream.get("last_message_time"),
                        last_message_content=str(stream.get("last_message_content", "")),
                        unread_count=0,
                    )
                    result.append(stream_info)

                logger.debug(f"返回 {len(result)} 个聊天流")
                return result

            except Exception as e:
                logger.error(f"获取聊天流列表失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/messages/{stream_id}", response_model=list[MessageInfo])
        async def get_messages(
            stream_id: str,
            limit: int = Query(100, description="最大返回数量"),
            before_time: Optional[float] = Query(None, description="获取此时间之前的消息"),
            _ = VerifiedDep
        ):
            """
            获取指定聊天流的历史消息

            路径参数:
                stream_id: 聊天流 ID

            查询参数:
                limit: 最大返回数量
                before_time: 获取此时间之前的消息（用于分页）

            返回:
                消息列表，按时间升序排序
            """

            try:
                from src.app.plugin_system.api import message_api

                # 使用 message_api 获取历史消息
                if before_time is not None:
                    messages = await message_api.get_messages_before_time_in_chat(
                        stream_id=stream_id,
                        timestamp=before_time,
                        limit=limit,
                        filter_bot=False,
                    )
                else:
                    # 获取最近的消息
                    messages = await message_api.get_recent_messages(
                        stream_id=stream_id,
                        hours=24 * 30,  # 最近30天
                        limit=limit,
                        limit_mode="latest",
                        filter_bot=False,
                    )

                # 转换为 MessageInfo 模型
                result = []
                for msg in messages:
                    message_info = MessageInfo(
                        message_id=str(msg.get("message_id", "")),
                        stream_id=str(msg.get("stream_id", "")),
                        platform=str(msg.get("platform", "")),
                        chat_type=str(msg.get("chat_type", "private")),
                        time=float(msg.get("time", 0)),
                        content=str(msg.get("content", "")),
                        sender_id=str(msg.get("sender_id", "")),
                        sender_name=str(msg.get("sender_name", "")),
                        is_sent=False,  # 历史消息都标记为接收
                        is_bot=await self._is_bot_message(msg),
                        is_webui=False,
                        metadata=msg.get("metadata", {}),
                    )
                    result.append(message_info)

                logger.debug(f"返回 {len(result)} 条消息，stream_id={stream_id}")
                return result

            except Exception as e:
                logger.error(f"获取历史消息失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/send", response_model=SendMessageResponse)
        async def send_message(
            request: SendMessageRequest,
            _ = VerifiedDep
        ):
            """
            发送消息

            请求体:
                {
                    "stream_id": "qq_group_123456",
                    "content": "Hello!",
                    "message_type": "text"
                }

            返回:
                {
                    "success": true,
                    "message": "发送成功",
                    "message_id": "..."
                }
            """

            try:
                from src.app.plugin_system.api import send_api
                from src.core.managers.stream_manager import get_stream_manager

                # 从数据库查询 stream 信息以获取正确的 platform
                stream_manager = get_stream_manager()
                stream_info = await stream_manager.get_stream_info(request.stream_id)
                
                if not stream_info:
                    logger.error(f"找不到聊天流: {request.stream_id}")
                    return SendMessageResponse(
                        success=False,
                        message="找不到指定的聊天流",
                    )
                
                platform = stream_info.get("platform", "")
                if not platform:
                    logger.error(f"聊天流缺少 platform 信息: {request.stream_id}")
                    return SendMessageResponse(
                        success=False,
                        message="聊天流缺少平台信息",
                    )

                # 使用 send_api 发送消息，明确指定 platform
                if request.message_type == "text":
                    success = await send_api.send_text(
                        content=request.content,
                        stream_id=request.stream_id,
                        platform=platform,
                    )
                elif request.message_type == "image":
                    success = await send_api.send_image(
                        image_data=request.content,
                        stream_id=request.stream_id,
                        platform=platform,
                    )
                elif request.message_type == "emoji":
                    success = await send_api.send_emoji(
                        emoji_data=request.content,
                        stream_id=request.stream_id,
                        platform=platform,
                    )
                else:
                    raise HTTPException(status_code=400, detail=f"不支持的消息类型: {request.message_type}")

                if success:
                    logger.info(f"消息发送成功: stream_id={request.stream_id}")
                    return SendMessageResponse(
                        success=True,
                        message="发送成功",
                    )
                else:
                    logger.error(f"消息发送失败: stream_id={request.stream_id}")
                    return SendMessageResponse(
                        success=False,
                        message="发送失败",
                    )

            except Exception as e:
                logger.error(f"发送消息失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

    # ==================== 辅助方法 ====================

    async def _subscribe_stream(self, websocket: WebSocket, stream_id: str) -> None:
        """订阅流"""
        async with self._broadcast_lock:
            if stream_id not in self.active_connections:
                self.active_connections[stream_id] = set()
            self.active_connections[stream_id].add(websocket)

    async def _unsubscribe_stream(self, websocket: WebSocket, stream_id: str) -> None:
        """取消订阅流"""
        async with self._broadcast_lock:
            if stream_id in self.active_connections:
                self.active_connections[stream_id].discard(websocket)
                if not self.active_connections[stream_id]:
                    del self.active_connections[stream_id]

    async def _is_bot_message(self, msg: dict[str, Any]) -> bool:
        """判断消息是否由 Bot 发送"""
        try:
            from src.core.managers.adapter_manager import get_adapter_manager
            from src.core.components.registry import get_global_registry
            from src.core.components.types import ComponentType

            platform = msg.get("platform", "")
            sender_id = str(msg.get("sender_id", ""))

            if not platform or not sender_id:
                return False

            # 查找匹配平台的适配器
            registry = get_global_registry()
            adapters = registry.get_by_type(ComponentType.ADAPTER)

            for sig, adapter_cls in adapters.items():
                if hasattr(adapter_cls, "platform") and adapter_cls.platform == platform:
                    adapter_manager = get_adapter_manager()
                    adapter = adapter_manager.get_adapter(sig)
                    if adapter:
                        bot_info = await adapter.get_bot_info()
                        bot_id = str(bot_info.get("bot_id", ""))
                        return bot_id == sender_id

            return False

        except Exception as e:
            logger.warning(f"判断 Bot 消息失败: {e}")
            return False

    @classmethod
    async def broadcast_message(cls, message_data: dict[str, Any]) -> None:
        """
        广播消息到订阅了相应流的所有 WebSocket 客户端

        Args:
            message_data: 消息数据字典，必须包含 stream_id 字段
        """
        stream_id = message_data.get("stream_id")
        if not stream_id:
            logger.warning("消息数据缺少 stream_id，无法广播")
            return

        if stream_id not in cls.active_connections:
            logger.debug(f"流 {stream_id} 没有订阅者")
            return

        # 构建 WebSocket 消息
        ws_message = {
            "type": "message",
            "data": message_data
        }

        # 广播到所有订阅者
        async with cls._broadcast_lock:
            connections = cls.active_connections[stream_id].copy()

        disconnected = set()
        for websocket in connections:
            try:
                await websocket.send_json(ws_message)
            except Exception as e:
                logger.debug(f"发送消息到 WebSocket 失败: {e}")
                disconnected.add(websocket)

        # 清理失败的连接
        if disconnected:
            async with cls._broadcast_lock:
                if stream_id in cls.active_connections:
                    cls.active_connections[stream_id] -= disconnected
                    if not cls.active_connections[stream_id]:
                        del cls.active_connections[stream_id]

    async def startup(self) -> None:
        """路由启动钩子"""
        logger.info(f"实时聊天路由已启动，路径: {self.custom_route_path}")

    async def shutdown(self) -> None:
        """路由关闭钩子"""
        logger.info("实时聊天路由已关闭")
