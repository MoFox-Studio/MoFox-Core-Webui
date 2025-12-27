"""
UI Chatroom 路由组件

提供聊天室相关的HTTP接口:
- 获取历史消息
- 发送消息
- 虚拟用户管理
"""

import base64
import hashlib
import json
import os
import time
import uuid
import orjson

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update

from src.common.logger import get_logger
from src.common.database.core.models import PersonInfo, UserRelationships
from src.common.database.core.session import get_db_session
from src.person_info.person_info import get_person_info_manager
from src.plugin_system.apis import message_api
from src.plugin_system.base import BaseRouterComponent
from src.config.config import global_config
from src.chat.emoji_system.emoji_manager import get_emoji_manager

from ..adapters.ui_chatroom_adapter import get_ui_chatroom_adapter
from ..utils.chatroom_storage import (
    get_chatroom_storage,
    get_chatroom_message_storage,
)

logger = get_logger("ChatroomRouter")


# ========== Pydantic 模型 ==========


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    user_id: str
    content: str
    message_type: str = "text"
    reply_to: str | None = None


class MemoryPoint(BaseModel):
    """记忆点模型"""
    content: str
    weight: float = 1.0


class CreateUserRequest(BaseModel):
    """创建用户请求"""
    user_id: str
    nickname: str
    impression: str = ""
    short_impression: str = ""
    avatar: str = ""
    attitude: int | None = None
    memory_points: list[MemoryPoint] = []


class UpdateUserRequest(BaseModel):
    """更新用户请求"""
    nickname: str | None = None
    impression: str | None = None
    short_impression: str | None = None
    avatar: str | None = None
    attitude: int | None = None
    memory_points: list[MemoryPoint] | None = None


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
    short_impression: str
    avatar: str
    attitude: int | None = None
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
        self.message_storage = get_chatroom_message_storage()
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
                
                # 使用内置 SQLite 数据库获取消息
                if before_timestamp:
                    messages = self.message_storage.get_messages_before_time(
                        chat_id=chat_id,
                        timestamp=before_timestamp,
                        limit=limit
                    )
                else:
                    # 获取最近的消息
                    end_time = time.time()
                    start_time = end_time - 86400 * 7  # 最近7天
                    messages = self.message_storage.get_messages_by_time_range(
                        chat_id=chat_id,
                        start_time=start_time,
                        end_time=end_time,
                        limit=limit,
                        limit_mode="latest"
                    )

                # 过滤出UI平台的消息（已经是UI平台的消息了）
                ui_messages = [
                    msg for msg in messages
                    if msg.get("user_platform") == "web_ui_chatroom"
                ]
                logger.info(f"获取到 {len(ui_messages)} 条UI消息")

                # 转换为前端格式
                result = []
                for msg in ui_messages:
                    user_id = msg.get("user_id", "unknown")
                    nickname = msg.get("nickname", "Unknown")
                    
                    # 尝试获取虚拟用户信息
                    virtual_user = self.storage.get_user(user_id)
                    if virtual_user:
                        nickname = virtual_user["nickname"]
                    elif user_id == "mofox_bot":
                        nickname = global_config.bot.nickname
                    
                    # 处理表情包：从emoji_hashes获取base64图片
                    emoji_images = []
                    emoji_hashes_str = msg.get("emoji_hashes")
                    if emoji_hashes_str:
                        try:
                            emoji_hashes = json.loads(emoji_hashes_str)
                            emoji_images = await self._get_emoji_images_by_hashes(emoji_hashes)
                        except Exception as e:
                            logger.error(f"解析emoji哈希失败: {e}")

                    result.append({
                        "message_id": msg.get("message_id"),
                        "user_id": user_id,
                        "nickname": nickname,
                        "content": msg.get("content", ""),
                        "timestamp": msg.get("timestamp", time.time()),
                        "message_type": msg.get("message_type", "text"),
                        "emojis": emoji_images,  # 添加表情包图片列表
                        "reply_to": msg.get("reply_to"),
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
                await self._ensure_person_exists(
                    user_id=request.user_id,
                    nickname=virtual_user["nickname"],
                    impression=virtual_user.get("impression", "")
                )

                # 构建消息
                message_id = str(uuid.uuid4())
                timestamp = time.time()
                chat_id = self.storage.get_chat_id()
                
                raw_message = {
                    "message_id": message_id,
                    "user_id": request.user_id,
                    "nickname": virtual_user["nickname"],
                    "content": request.content,
                    "timestamp": timestamp,
                    "message_type": request.message_type,
                    "reply_to": request.reply_to,
                }

                # 保存到SQLite
                self.message_storage.save_message(
                    message_id=message_id,
                    user_id=request.user_id,
                    nickname=virtual_user["nickname"],
                    content=request.content,
                    timestamp=timestamp,
                    chat_id=chat_id,
                    message_type=request.message_type,
                    reply_to=request.reply_to,
                    user_platform="web_ui_chatroom"
                )

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
                    short_impression=request.short_impression,
                    avatar=request.avatar,
                    attitude=request.attitude,
                    memory_points=request.memory_points
                )

                # 在person_info中创建对应记录
                person_id = await self._ensure_person_exists(
                    user_id=request.user_id,
                    nickname=request.nickname,
                    impression=request.impression,
                    short_impression=request.short_impression,
                    attitude=request.attitude,
                    memory_points=request.memory_points
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
                if "short_impression" in update_data:
                    await self.person_manager.update_one_field(person_id, "short_impression", update_data["short_impression"])
                if "attitude" in update_data:
                    await self.person_manager.update_one_field(person_id, "attitude", update_data["attitude"])
                if "memory_points" in update_data and request.memory_points is not None:
                    # 转换记忆点格式: [content, weight, timestamp]
                    points_data = [
                        [point.content, point.weight, time.time()] 
                        for point in request.memory_points
                    ]
                    await self.person_manager.update_one_field(person_id, "points", orjson.dumps(points_data).decode('utf-8'))

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

                # 同时删除person_info中的记录
                person_id = self.person_manager.get_person_id("web_ui_chatroom", user_id)
                await self.person_manager.del_one_document(person_id)
                logger.info(f"已删除虚拟用户 {user_id} 及其person_info记录 {person_id}")

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
                
                # 将AI响应消息保存到SQLite
                chat_id = self.storage.get_chat_id()
                for response in responses:
                    # 提取表情包的base64数据并计算哈希值
                    emoji_hashes = []
                    emojis_base64 = response.get("emojis", [])
                    if emojis_base64:
                        for emoji_b64 in emojis_base64:
                            try:
                                emoji_bytes = base64.b64decode(emoji_b64)
                                emoji_hash = hashlib.md5(emoji_bytes).hexdigest()
                                emoji_hashes.append(emoji_hash)
                                logger.debug(f"提取表情包哈希: {emoji_hash}")
                            except Exception as e:
                                logger.error(f"计算表情包哈希失败: {e}")
                    
                    # 将emoji哈希列表转换为JSON字符串保存
                    emoji_hashes_json = json.dumps(emoji_hashes) if emoji_hashes else None
                    
                    # 保存消息到SQLite（包含emoji哈希）
                    self.message_storage.save_message(
                        message_id=response.get("message_id"),
                        user_id=response.get("user_id", "mofox_bot"),
                        nickname=response.get("nickname", "麦麦"),
                        content=response.get("content", ""),
                        timestamp=response.get("timestamp", time.time()),
                        chat_id=chat_id,
                        message_type=response.get("message_type", "text"),
                        reply_to=response.get("reply_to"),
                        user_platform="web_ui_chatroom",
                        emoji_hashes=emoji_hashes_json
                    )

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

        @self.router.get("/copyable_users")
        async def get_copyable_users(platform: str | None = None):
            """获取可复制的用户列表"""
            try:
                async with get_db_session() as session:
                    stmt = select(PersonInfo).where(PersonInfo.platform != "web_ui_chatroom")
                    if platform:
                        stmt = stmt.where(PersonInfo.platform == platform)
                    
                    # 按最后交互时间排序
                    stmt = stmt.order_by(PersonInfo.last_know.desc())
                    
                    result = await session.execute(stmt)
                    persons = result.scalars().all()
                    
                    users = []
                    for p in persons:
                        # 解析记忆点
                        memory_points = []
                        if p.points:
                            try:
                                if isinstance(p.points, str):
                                    points_data = orjson.loads(p.points)
                                else:
                                    points_data = p.points
                                
                                for point in points_data:
                                    if isinstance(point, (list, tuple)) and len(point) >= 1:
                                        memory_points.append({
                                            "content": str(point[0]),
                                            "weight": float(point[1]) if len(point) > 1 else 1.0
                                        })
                            except Exception:
                                pass

                        users.append({
                            "person_id": p.person_id,
                            "nickname": p.nickname or p.person_name or "Unknown",
                            "platform": p.platform,
                            "user_id": p.user_id,
                            "impression": p.impression,
                            "short_impression": p.short_impression,
                            "attitude": p.attitude,
                            "memory_points": memory_points
                        })
                        
                    return {
                        "success": True,
                        "users": users,
                        "count": len(users)
                    }
            except Exception as e:
                logger.error(f"获取可复制用户列表失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/users/{user_id}/reset")
        async def reset_user_relationship(user_id: str):
            """重置用户关系"""
            try:
                # 1. 获取虚拟用户配置
                virtual_user = self.storage.get_user(user_id)
                if not virtual_user:
                    raise HTTPException(status_code=404, detail=f"虚拟用户 {user_id} 不存在")
                
                # 2. 获取 person_id
                person_id = self.person_manager.get_person_id("web_ui_chatroom", user_id)
                
                # 3. 重置 PersonInfo
                async with get_db_session() as session:
                    # 更新 PersonInfo
                    stmt_person = update(PersonInfo).where(
                        PersonInfo.person_id == person_id
                    ).values(
                        impression=virtual_user.get("impression", ""),
                        short_impression=virtual_user.get("short_impression", ""),
                        attitude=virtual_user.get("attitude", 50),
                        points="[]",  # 清空记忆点
                        know_times=0,
                        know_since=time.time(),
                        last_know=time.time()
                    )
                    await session.execute(stmt_person)
                    
                    # 更新 UserRelationships
                    # 查找 UserRelationships
                    stmt_rel = update(UserRelationships).where(
                        UserRelationships.user_id == user_id
                    ).values(
                        relationship_score=0.3,  # 默认初始值
                        relationship_text="",
                        impression_text="",
                        relationship_stage="stranger",
                        last_updated=time.time()
                    )
                    await session.execute(stmt_rel)
                    
                    await session.commit()
                
                return {
                    "success": True,
                    "message": "用户关系已重置"
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"重置用户关系失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

    async def _ensure_person_exists(
        self, 
        user_id: str, 
        nickname: str, 
        impression: str = "",
        short_impression: str = "",
        attitude: int | None = None,
        memory_points: list[MemoryPoint] | None = None
    ) -> str:
        """确保person_info中存在该用户，并更新所有相关字段"""
        # 直接使用 get_or_create_person，它会自动生成正确的 person_id
        person_info = await self.person_manager.get_or_create_person(
            platform="web_ui_chatroom",
            user_id=int(user_id),
            nickname=nickname,
            user_cardname=nickname,
            user_avatar=""
        )
        
        # 获取 person_id
        person_id = self.person_manager.get_person_id("web_ui_chatroom", user_id)
        
        # 更新所有提供的字段
        if impression and person_info:
            await self.person_manager.update_one_field(person_id, "impression", impression)
        if short_impression and person_info:
            await self.person_manager.update_one_field(person_id, "short_impression", short_impression)
        if attitude is not None and person_info:
            await self.person_manager.update_one_field(person_id, "attitude", attitude)
        if memory_points is not None and person_info:
            # 转换记忆点格式: [content, weight, timestamp]
            points_data = [
                [point.content, point.weight, time.time()] 
                for point in memory_points
            ]
            await self.person_manager.update_one_field(person_id, "points", orjson.dumps(points_data).decode('utf-8'))

        return person_id

    async def _get_emoji_images_by_hashes(self, emoji_hashes: list[str]) -> list[str]:
        """
        根据表情包哈希值列表从数据库获取对应的base64图片
        
        Args:
            emoji_hashes: 表情包哈希值列表
            
        Returns:
            base64编码的图片列表
        """
        emoji_images = []
        
        for emoji_hash in emoji_hashes:
            try:
                # 从数据库获取表情包对象
                emoji_list = await self.emoji_manager.get_emoji_from_db(emoji_hash)
                
                if emoji_list and len(emoji_list) > 0:
                    emoji_obj = emoji_list[0]
                    # 读取文件并转换为base64
                    if os.path.exists(emoji_obj.full_path):
                        from src.chat.utils.utils_image import image_path_to_base64
                        emoji_base64 = image_path_to_base64(emoji_obj.full_path)
                        if emoji_base64:
                            emoji_images.append(emoji_base64)
                            logger.debug(f"获取表情包成功: {emoji_hash}")
                        else:
                            logger.warning(f"转换表情包为base64失败: {emoji_hash}")
                    else:
                        logger.warning(f"表情包文件不存在: {emoji_obj.full_path}")
                else:
                    logger.warning(f"数据库中未找到表情包: {emoji_hash}")
                    
            except Exception as e:
                logger.error(f"获取表情包失败 {emoji_hash}: {e}")
                continue
        
        return emoji_images
