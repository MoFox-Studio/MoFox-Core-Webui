"""
UI Chatroom 路由组件

提供聊天室相关的HTTP接口:
- 获取历史消息
- 发送消息
- 虚拟用户管理
"""

import time
import uuid
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel

from src.common.logger import get_logger
from src.person_info.person_info import get_person_info_manager
from src.plugin_system.apis import message_api
from src.plugin_system.base import BaseRouterComponent

from ..adapters.ui_chatroom_adapter import get_ui_chatroom_adapter
from ..utils.chatroom_storage import get_chatroom_storage

logger = get_logger("ChatroomRouter")


# ========== Pydantic 模型 ==========


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    user_id: str
    content: str
    message_type: str = "text"
    reply_to: str | None = None


class CreateUserRequest(BaseModel):
    """创建用户请求"""
    user_id: str
    nickname: str
    impression: str = ""
    avatar: str = ""


class UpdateUserRequest(BaseModel):
    """更新用户请求"""
    nickname: str | None = None
    impression: str | None = None
    avatar: str | None = None


class MessageResponse(BaseModel):
    """消息响应"""
    message_id: str
    user_id: str
    nickname: str
    content: str
    timestamp: float
    message_type: str


class UserResponse(BaseModel):
    """用户响应"""
    user_id: str
    nickname: str
    impression: str
    avatar: str
    person_id: str | None = None
    created_at: float
    updated_at: float


# ========== 路由组件 ==========


class ChatroomRouterComponent(BaseRouterComponent):
    """聊天室路由组件"""

    component_name = "chatroom"
    component_description = "UI聊天室管理接口"
    component_version = "1.0.0"

    def __init__(self, plugin_config: dict | None = None):
        # 在调用super之前初始化需要的属性
        self.storage = get_chatroom_storage()
        self.person_manager = get_person_info_manager()
        super().__init__(plugin_config)

    def register_endpoints(self) -> None:
        """注册所有HTTP端点"""
        # 设置路由前缀和标签
        
        @self.router.get("/messages")
        async def get_messages(
            limit: int = 100,
            before_timestamp: float | None = None
        ):
            """
            获取历史消息
            
            Args:
                limit: 限制返回的消息数量
                before_timestamp: 获取此时间之前的消息
            """
            try:
                chat_id = self.storage.get_chat_id()
                
                # 使用 message_api 获取消息
                if before_timestamp:
                    messages = await message_api.get_messages_before_time_in_chat(
                        chat_id=chat_id,
                        timestamp=before_timestamp,
                        limit=limit
                    )
                else:
                    # 获取最近的消息
                    end_time = time.time()
                    start_time = end_time - 86400 * 7  # 最近7天
                    messages = await message_api.get_messages_by_time_in_chat(
                        chat_id=chat_id,
                        start_time=start_time,
                        end_time=end_time,
                        limit=limit,
                        limit_mode="latest"
                    )

                # 过滤出UI平台的消息
                ui_messages = [
                    msg for msg in messages
                    if msg.get("user_platform") == "web_ui_chatroom"
                ]
                logger.info(ui_messages)

                # 转换为前端格式
                result = []
                for msg in ui_messages:
                    user_id = msg.get("user_id", "unknown")
                    nickname = msg.get("nickname", "Unknown")
                    
                    # 尝试获取虚拟用户信息
                    virtual_user = self.storage.get_user(user_id)
                    if virtual_user:
                        nickname = virtual_user["nickname"]

                    result.append({
                        "message_id": msg.get("message_id"),
                        "user_id": user_id,
                        "nickname": nickname,
                        "content": msg.get("content", ""),
                        "timestamp": msg.get("timestamp", time.time()),
                        "message_type": "text",  # TODO: 支持更多类型
                    })

                return {
                    "success": True,
                    "messages": result,
                    "count": len(result)
                }

            except Exception as e:
                logger.error(f"获取消息失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/send")
        async def send_message(request: SendMessageRequest):
            """
            发送消息
            
            Args:
                request: 发送消息请求
            """
            try:
                adapter = get_ui_chatroom_adapter()
                if not adapter:
                    raise HTTPException(status_code=503, detail="UI Chatroom适配器未启动")

                # 获取虚拟用户信息
                virtual_user = self.storage.get_user(request.user_id)
                if not virtual_user:
                    raise HTTPException(status_code=404, detail=f"虚拟用户 {request.user_id} 不存在")

                # 确保该虚拟用户在person_info中存在
                person_id = await self._ensure_person_exists(
                    user_id=request.user_id,
                    nickname=virtual_user["nickname"],
                    impression=virtual_user.get("impression", "")
                )

                # 构建消息
                message_id = str(uuid.uuid4())
                raw_message = {
                    "message_id": message_id,
                    "user_id": request.user_id,
                    "nickname": virtual_user["nickname"],
                    "content": request.content,
                    "timestamp": time.time(),
                    "message_type": request.message_type,
                    "reply_to": request.reply_to,
                }

                # 发送到适配器（异步，不等待响应）
                await adapter.send_message(raw_message)

                # 立即返回用户消息
                return {
                    "success": True,
                    "request_message": {
                        "message_id": message_id,
                        "user_id": request.user_id,
                        "nickname": virtual_user["nickname"],
                        "content": request.content,
                        "timestamp": raw_message["timestamp"],
                        "message_type": request.message_type,
                        "reply_to": request.reply_to,
                    },
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"发送消息失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/users")
        async def get_users():
            """获取所有虚拟用户"""
            try:
                users = self.storage.get_all_users()
                
                # 添加person_id信息
                result = []
                for user in users:
                    person_id = self.person_manager.get_person_id("web_ui_chatroom", user["user_id"])
                    result.append({
                        **user,
                        "person_id": person_id
                    })

                return {
                    "success": True,
                    "users": result,
                    "count": len(result)
                }

            except Exception as e:
                logger.error(f"获取用户列表失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/users/{user_id}")
        async def get_user(user_id: str):
            """获取单个虚拟用户"""
            try:
                user = self.storage.get_user(user_id)
                if not user:
                    raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")

                # 获取person_info信息
                person_id = self.person_manager.get_person_id("web_ui_chatroom", user_id)
                person_info = await self.person_manager.get_person_info_by_person_id(person_id)

                return {
                    "success": True,
                    "user": {
                        **user,
                        "person_id": person_id,
                        "person_info": person_info
                    }
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取用户失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/users")
        async def create_user(request: CreateUserRequest):
            """创建虚拟用户"""
            try:
                # 验证用户ID只能是数字
                if not request.user_id.isdigit():
                    raise HTTPException(status_code=400, detail="用户ID只能包含数字")
                
                # 检查用户ID是否已存在
                existing_user = self.storage.get_user(request.user_id)
                if existing_user:
                    raise HTTPException(status_code=409, detail=f"用户ID {request.user_id} 已存在，请使用其他ID")
                
                # 检查昵称是否已存在
                all_users = self.storage.get_all_users()
                for user in all_users:
                    if user["nickname"] == request.nickname:
                        raise HTTPException(status_code=409, detail=f"昵称 '{request.nickname}' 已被使用，请使用其他昵称")
                
                # 创建虚拟用户
                user = self.storage.create_user(
                    user_id=request.user_id,
                    nickname=request.nickname,
                    impression=request.impression,
                    avatar=request.avatar
                )

                # 在person_info中创建对应记录
                person_id = await self._ensure_person_exists(
                    user_id=request.user_id,
                    nickname=request.nickname,
                    impression=request.impression
                )

                return {
                    "success": True,
                    "user": {
                        **user,
                        "person_id": person_id
                    }
                }

            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"创建用户失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.put("/users/{user_id}")
        async def update_user(user_id: str, request: UpdateUserRequest):
            """更新虚拟用户"""
            try:
                # 过滤None值
                update_data = {
                    k: v for k, v in request.dict().items()
                    if v is not None
                }

                # 如果更新了昵称，检查是否与其他用户冲突
                if "nickname" in update_data:
                    all_users = self.storage.get_all_users()
                    for user in all_users:
                        if user["user_id"] != user_id and user["nickname"] == update_data["nickname"]:
                            raise HTTPException(status_code=409, detail=f"昵称 '{update_data['nickname']}' 已被其他用户使用，请使用其他昵称")

                # 更新虚拟用户
                user = self.storage.update_user(user_id, **update_data)

                # 同步更新person_info
                person_id = self.person_manager.get_person_id("web_ui_chatroom", user_id)
                if "nickname" in update_data:
                    await self.person_manager.update_one_field(person_id, "nickname", update_data["nickname"])
                if "impression" in update_data:
                    await self.person_manager.update_one_field(person_id, "impression", update_data["impression"])

                return {
                    "success": True,
                    "user": {
                        **user,
                        "person_id": person_id
                    }
                }

            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                logger.error(f"更新用户失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.delete("/users/{user_id}")
        async def delete_user(user_id: str):
            """删除虚拟用户"""
            try:
                success = self.storage.delete_user(user_id)
                if not success:
                    raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")

                # 注意：这里不删除person_info中的记录，保留历史数据

                return {
                    "success": True,
                    "message": f"用户 {user_id} 已删除"
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"删除用户失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/settings")
        async def get_settings():
            """获取聊天室设置"""
            try:
                settings = self.storage.get_settings()
                return {
                    "success": True,
                    "settings": settings
                }

            except Exception as e:
                logger.error(f"获取设置失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/poll")
        async def poll_messages():
            """轮询获取新的AI回复消息"""
            try:
                adapter = get_ui_chatroom_adapter()
                if not adapter:
                    return {
                        "success": True,
                        "messages": []
                    }

                # 获取待处理的响应消息
                responses = await adapter.get_pending_responses(timeout=0.5)

                return {
                    "success": True,
                    "messages": responses,
                    "count": len(responses)
                }

            except Exception as e:
                logger.error(f"轮询消息失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/messages/{message_id}")
        async def get_message(message_id: str):
            """获取单条消息（用于查询引用的消息）"""
            try:
                adapter = get_ui_chatroom_adapter()
                if not adapter:
                    raise HTTPException(status_code=503, detail="UI Chatroom适配器未启动")

                # 从缓存获取消息
                message = adapter.get_cached_message(message_id)
                if not message:
                    raise HTTPException(status_code=404, detail=f"消息 {message_id} 不存在或已过期")

                return {
                    "success": True,
                    "message": message
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取消息失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

    async def _ensure_person_exists(self, user_id: str, nickname: str, impression: str = "") -> str:
        """确保person_info中存在该用户"""
        # 直接使用 get_or_create_person，它会自动生成正确的 person_id
        person_info = await self.person_manager.get_or_create_person(
            platform="web_ui_chatroom",
            user_id=int(user_id),  # 保持字符串类型
            nickname=nickname,
            user_cardname=nickname,
            user_avatar=""
        )
        
        # 获取 person_id
        person_id = self.person_manager.get_person_id("web_ui_chatroom", user_id)
        
        # 如果有印象信息，更新它
        if impression and person_info:
            await self.person_manager.update_one_field(person_id, "impression", impression)

        return person_id
