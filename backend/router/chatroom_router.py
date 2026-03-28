"""Chatroom 路由组件

提供 HTTP API 端点，统一前缀 /webui/api/chatroom，包括：
- 虚拟用户 CRUD（含 reset）
- 可复制用户列表
- 历史消息查询
- 消息发送
- Bot 回复轮询
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from fastapi import HTTPException, Query
from pydantic import BaseModel

from src.kernel.logger import get_logger
from src.core.components.base.router import BaseRouter
from src.core.utils.security import VerifiedDep

logger = get_logger(name="ChatroomRouter", color="#CBA6F7")

PLATFORM = "webui"


# ====================================================================== #
#  Pydantic 模型                                                         #
# ====================================================================== #

class MemoryPoint(BaseModel):
    content: str
    weight: float = 1.0


class CreateUserRequest(BaseModel):
    user_id: str
    nickname: str
    avatar: str = ""
    impression: str = ""
    short_impression: str = ""
    attitude: int = 50
    memory_points: list[MemoryPoint] = []


class UpdateUserRequest(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    impression: Optional[str] = None
    short_impression: Optional[str] = None
    attitude: Optional[int] = None
    memory_points: Optional[list[MemoryPoint]] = None


class SendRequest(BaseModel):
    user_id: str
    content: str
    message_type: str = "text"
    reply_to: Optional[str] = None


class UserResponse(BaseModel):
    user_id: str
    nickname: str
    avatar: str
    created_at: float
    updated_at: float
    person_id: str
    impression: str
    short_impression: str
    attitude: int
    memory_points: list[dict[str, Any]]


class MessageResponse(BaseModel):
    message_id: str
    user_id: str
    nickname: str
    content: str
    timestamp: float
    message_type: str
    reply_to: Optional[str] = None
    images: list[str] = []
    emojis: list[str] = []


class SendResponse(BaseModel):
    request_message: dict[str, Any]


# ====================================================================== #
#  Router 组件                                                           #
# ====================================================================== #

class ChatroomRouter(BaseRouter):
    """WebUI 聊天室路由组件"""

    router_name = "ChatroomRouter"
    custom_route_path = "/webui/api/chatroom"
    cors_origins = ["*"]

    def register_endpoints(self) -> None:  # type: ignore[override]
        """注册所有 /webui/api/chatroom/* 端点"""

        # -------------------------------------------------------------- #
        #  辅助方法：获取 VirtualUserStorage 实例                        #
        # -------------------------------------------------------------- #

        def _get_storage():
            from ..storage.virtual_user_storage import VirtualUserStorage
            return VirtualUserStorage()

        def _get_adapter():
            from ..adapter.chatroom_adapter import get_chatroom_adapter
            adapter = get_chatroom_adapter()
            if adapter is None:
                raise HTTPException(status_code=503, detail="ChatroomAdapter 尚未就绪")
            return adapter

        # -------------------------------------------------------------- #
        #  GET /users — 列出所有虚拟用户                                 #
        # -------------------------------------------------------------- #

        @self.app.get("/users")
        async def list_users(_ = VerifiedDep):
            """获取所有虚拟用户（合并 JSON 快照 + DB 当前状态）"""
            storage = _get_storage()
            try:
                users = await storage.get_all_merged_users()
                return {"users": users}
            except Exception as e:
                logger.error(f"获取用户列表失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # -------------------------------------------------------------- #
        #  POST /users — 创建虚拟用户                                    #
        # -------------------------------------------------------------- #

        @self.app.post("/users", response_model=UserResponse)
        async def create_user(req: CreateUserRequest, _ = VerifiedDep):
            """创建新虚拟用户"""
            storage = _get_storage()
            try:
                # 检查 user_id 是否已存在
                if await storage.user_exists(req.user_id):
                    raise HTTPException(status_code=409, detail=f"用户 {req.user_id} 已存在")

                now = time.time()
                memory_points_raw = [mp.model_dump() for mp in req.memory_points]

                # JSON 快照（含 init_* 初始快照字段）
                snapshot: dict[str, Any] = {
                    "user_id": req.user_id,
                    "nickname": req.nickname,
                    "avatar": req.avatar,
                    "created_at": now,
                    "init_impression": req.impression,
                    "init_short_impression": req.short_impression,
                    "init_attitude": req.attitude,
                    "init_memory_points": memory_points_raw,
                }
                await storage.create_user(req.user_id, snapshot)

                # 写入 PersonInfo DB
                ok = await storage.sync_create_to_db(
                    user_id=req.user_id,
                    nickname=req.nickname,
                    avatar=req.avatar,
                    impression=req.impression,
                    short_impression=req.short_impression,
                    attitude=req.attitude,
                    memory_points=memory_points_raw,
                    created_at=now,
                )
                if not ok:
                    logger.warning(f"PersonInfo 同步写入失败: user_id={req.user_id}")

                merged = await storage.get_merged_user(req.user_id)
                if merged is None:
                    raise HTTPException(status_code=500, detail="创建后无法读取用户")
                return merged

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"创建用户失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # -------------------------------------------------------------- #
        #  PUT /users/{user_id} — 更新虚拟用户                          #
        # -------------------------------------------------------------- #

        @self.app.put("/users/{user_id}")
        async def update_user(user_id: str, req: UpdateUserRequest, _ = VerifiedDep):
            """更新虚拟用户信息"""
            storage = _get_storage()
            try:
                if not await storage.user_exists(user_id):
                    raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")

                # 构建更新字典（只含非 None 字段）
                updates: dict[str, Any] = {}
                for field in ("nickname", "avatar", "impression", "short_impression", "attitude"):
                    val = getattr(req, field)
                    if val is not None:
                        updates[field] = val
                if req.memory_points is not None:
                    updates["memory_points"] = [mp.model_dump() for mp in req.memory_points]

                if updates:
                    # 更新 JSON 快照（nickname/avatar 部分）
                    snapshot_updates: dict[str, Any] = {}
                    for f in ("nickname", "avatar"):
                        if f in updates:
                            snapshot_updates[f] = updates[f]
                    if snapshot_updates:
                        await storage.update_user_snapshot(user_id, snapshot_updates)

                    # 同步 DB
                    await storage.sync_update_to_db(user_id, updates)

                merged = await storage.get_merged_user(user_id)
                if merged is None:
                    raise HTTPException(status_code=500, detail="更新后无法读取用户")
                return {"user": merged}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"更新用户失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # -------------------------------------------------------------- #
        #  DELETE /users/{user_id} — 删除虚拟用户                       #
        # -------------------------------------------------------------- #

        @self.app.delete("/users/{user_id}")
        async def delete_user(user_id: str, _ = VerifiedDep):
            """删除虚拟用户及其所有消息记录"""
            storage = _get_storage()
            try:
                if not await storage.user_exists(user_id):
                    raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")

                # 删除 Messages
                try:
                    from src.kernel.db import CRUDBase
                    from src.core.models.sql_alchemy import Messages, ChatStreams

                    # 查询该用户的所有 ChatStream 记录
                    stream_records = await CRUDBase(ChatStreams).get_multi(
                        platform=PLATFORM, user_id=user_id
                    )
                    for stream_record in stream_records:
                        # 删除该流下的所有消息
                        msg_records = await CRUDBase(Messages).get_multi(
                            stream_id=stream_record.stream_id
                        )
                        for msg in msg_records:
                            await CRUDBase(Messages).delete(msg.id)
                        await CRUDBase(ChatStreams).delete(stream_record.id)
                except Exception as db_err:
                    logger.warning(f"清理消息/流记录失败: {db_err}")

                # 删除 PersonInfo
                await storage.sync_delete_from_db(user_id)

                # 删除 JSON 快照
                await storage.delete_user(user_id)

                return {"message": f"用户 {user_id} 已删除"}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"删除用户失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # -------------------------------------------------------------- #
        #  POST /users/{user_id}/reset — 重置虚拟用户                   #
        # -------------------------------------------------------------- #

        @self.app.post("/users/{user_id}/reset")
        async def reset_user(user_id: str, _ = VerifiedDep):
            """重置用户人格（恢复 init_* 快照），并删除该用户所有消息记录"""
            storage = _get_storage()
            try:
                if not await storage.user_exists(user_id):
                    raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")

                # 恢复 PersonInfo 到 init_* 值
                ok = await storage.sync_reset_to_db(user_id)
                if not ok:
                    raise HTTPException(status_code=500, detail="重置 PersonInfo 失败")

                # 删除消息和 ChatStreams
                try:
                    from src.kernel.db import CRUDBase
                    from src.core.models.sql_alchemy import Messages, ChatStreams

                    stream_records = await CRUDBase(ChatStreams).get_multi(
                        platform=PLATFORM, user_id=user_id
                    )
                    for stream_record in stream_records:
                        msg_records = await CRUDBase(Messages).get_multi(
                            stream_id=stream_record.stream_id
                        )
                        for msg in msg_records:
                            await CRUDBase(Messages).delete(msg.id)
                        await CRUDBase(ChatStreams).delete(stream_record.id)
                except Exception as db_err:
                    logger.warning(f"重置时清理消息失败: {db_err}")

                return {"message": f"用户 {user_id} 已重置"}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"重置用户失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # -------------------------------------------------------------- #
        #  GET /copyable_users — 可复制用户列表                          #
        # -------------------------------------------------------------- #

        @self.app.get("/copyable_users")
        async def list_copyable_users(_ = VerifiedDep):
            """列出非 webui 平台的 PersonInfo 用户，供复制导入"""
            try:
                from src.kernel.db import QueryBuilder
                from src.core.models.sql_alchemy import PersonInfo

                query = QueryBuilder(PersonInfo)
                all_persons = await query.all(as_dict=True)

                result = []
                for person in all_persons:
                    if str(person.get("platform", "")) == PLATFORM:
                        continue
                    result.append({
                        "person_id": person.get("person_id", ""),
                        "platform": person.get("platform", ""),
                        "user_id": person.get("user_id", ""),
                        "nickname": person.get("nickname", ""),
                        "impression": person.get("impression", ""),
                        "short_impression": person.get("short_impression", ""),
                        "attitude": person.get("attitude", 50),
                    })
                return {"users": result}

            except Exception as e:
                logger.error(f"获取可复制用户失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # -------------------------------------------------------------- #
        #  GET /messages — 历史消息查询                                  #
        # -------------------------------------------------------------- #

        @self.app.get("/messages")
        async def get_messages(
            user_id: Optional[str] = Query(None, description="按用户 ID 过滤"),
            limit: int = Query(100, description="最大返回数量"),
            _ = VerifiedDep,
        ):
            """获取历史消息"""
            try:
                from src.kernel.db import get_session_factory
                from src.core.models.sql_alchemy import Messages, PersonInfo
                from sqlalchemy import select

                # 构建 JOIN 查询
                session_factory = await get_session_factory()
                async with session_factory() as session:
                    # 构建查询语句
                    stmt = (
                        select(Messages, PersonInfo.user_id, PersonInfo.nickname)
                        .outerjoin(PersonInfo, Messages.person_id == PersonInfo.person_id)
                        .where(Messages.platform == PLATFORM)
                        .order_by(Messages.time.desc())
                        .limit(limit)
                    )
                    
                    # 如果指定了 user_id，添加过滤条件
                    if user_id:
                        stmt = stmt.where(PersonInfo.user_id == user_id)
                    
                    result_proxy = await session.execute(stmt)
                    rows = result_proxy.all()
                
                # 反转顺序，让旧消息在前
                rows = list(reversed(rows))
                
                result = []
                for row in rows:
                    msg, db_user_id, db_nickname = row
                    
                    # 获取消息类型
                    message_type = msg.message_type or "text"
                    
                    # 获取用户信息（如果是 bot，特殊处理）
                    if msg.person_id == "bot":
                        display_user_id = "bot"
                        display_nickname = "Bot"
                    else:
                        display_user_id = db_user_id or msg.person_id or ""
                        display_nickname = db_nickname or "Unknown"
                    
                    # 获取内容和处理特殊类型
                    content = str(msg.processed_plain_text or msg.content or "")
                    emojis = []
                    images = []
                    
                    # 根据消息类型处理内容
                    if message_type == "emoji" and msg.content:
                        # 表情消息，content 可能是 base64 或列表
                        try:
                            import json
                            emoji_data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                            if isinstance(emoji_data, list):
                                emojis = emoji_data
                            else:
                                emojis = [str(emoji_data)]
                        except:
                            # 如果不是 JSON，直接作为单个表情
                            emojis = [str(msg.content)]
                    elif message_type == "image" and msg.content:
                        # 图片消息
                        try:
                            import json
                            image_data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                            if isinstance(image_data, list):
                                images = image_data
                            else:
                                images = [str(image_data)]
                        except:
                            images = [str(msg.content)]
                    
                    result.append(MessageResponse(
                        message_id=str(msg.message_id or ""),
                        user_id=str(display_user_id),
                        nickname=str(display_nickname),
                        content=content,
                        timestamp=float(msg.time or 0.0),
                        message_type=message_type,
                        reply_to=str(msg.reply_to) if msg.reply_to else None,
                        emojis=emojis,
                        images=images,
                    ))
                return {"messages": result}

            except Exception as e:
                logger.error(f"获取历史消息失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # -------------------------------------------------------------- #
        #  GET /messages/{message_id} — 单条消息                        #
        # -------------------------------------------------------------- #

        @self.app.get("/messages/{message_id}")
        async def get_message(message_id: str, _ = VerifiedDep):
            """根据 message_id 获取单条消息（查 DB）"""
            try:
                # 查 DB，JOIN PersonInfo 获取用户信息
                from src.kernel.db import get_session_factory
                from src.core.models.sql_alchemy import Messages, PersonInfo
                from sqlalchemy import select

                session_factory = await get_session_factory()
                async with session_factory() as session:
                    stmt = (
                        select(Messages, PersonInfo.user_id, PersonInfo.nickname)
                        .outerjoin(PersonInfo, Messages.person_id == PersonInfo.person_id)
                        .where(Messages.message_id == message_id)
                    )
                    result_proxy = await session.execute(stmt)
                    row = result_proxy.first()
                
                if not row:
                    raise HTTPException(status_code=404, detail=f"消息 {message_id} 不存在")
                
                msg, db_user_id, db_nickname = row

                # 获取消息类型
                message_type = msg.message_type or "text"
                
                # 获取用户信息（如果是 bot，特殊处理）
                if msg.person_id == "bot":
                    display_user_id = "bot"
                    display_nickname = "Bot"
                else:
                    display_user_id = db_user_id or msg.person_id or ""
                    display_nickname = db_nickname or "Unknown"
                
                # 获取内容和处理特殊类型
                content = str(msg.processed_plain_text or msg.content or "")
                emojis = []
                images = []
                
                # 根据消息类型处理内容
                if message_type == "emoji" and msg.content:
                    try:
                        import json
                        emoji_data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                        if isinstance(emoji_data, list):
                            emojis = emoji_data
                        else:
                            emojis = [str(emoji_data)]
                    except:
                        emojis = [str(msg.content)]
                elif message_type == "image" and msg.content:
                    try:
                        import json
                        image_data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                        if isinstance(image_data, list):
                            images = image_data
                        else:
                            images = [str(image_data)]
                    except:
                        images = [str(msg.content)]

                return {"message": MessageResponse(
                    message_id=str(msg.message_id or ""),
                    user_id=str(display_user_id),
                    nickname=str(display_nickname),
                    content=content,
                    timestamp=float(msg.time or 0.0),
                    message_type=message_type,
                    reply_to=str(msg.reply_to) if msg.reply_to else None,
                    emojis=emojis,
                    images=images,
                ).model_dump()}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取单条消息失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # -------------------------------------------------------------- #
        #  POST /send — 发送消息                                         #
        # -------------------------------------------------------------- #

        @self.app.post("/send", response_model=SendResponse)
        async def send_message(req: SendRequest, _ = VerifiedDep):
            """发送用户消息到 Bot 核心"""
            storage = _get_storage()
            adapter = _get_adapter()
            try:
                if not await storage.user_exists(req.user_id):
                    raise HTTPException(status_code=404, detail=f"用户 {req.user_id} 不存在")

                # 查 DB 获取 nickname
                db_user = await storage.get_db_user(req.user_id)
                nickname = db_user.get("nickname", req.user_id) if db_user else req.user_id

                message_id = str(uuid.uuid4())
                now = time.time()

                raw_message: dict[str, Any] = {
                    "message_id": message_id,
                    "user_id": req.user_id,
                    "nickname": nickname,
                    "content": req.content,
                    "timestamp": now,
                    "message_type": req.message_type,
                    "reply_to": req.reply_to,
                }

                await adapter.send_message(raw_message)

                return SendResponse(request_message=raw_message)

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"发送消息失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # -------------------------------------------------------------- #
        #  GET /poll — 轮询 Bot 回复                                     #
        # -------------------------------------------------------------- #

        @self.app.get("/poll")
        async def poll_responses(
            user_id: Optional[str] = Query(None, description="按用户 ID 过滤回复"),
            _ = VerifiedDep,
        ):
            """轮询待取消息（Bot 回复队列）"""
            adapter = _get_adapter()
            try:
                responses = await adapter.get_pending_responses(user_id=user_id)
                return {"messages": responses}
            except Exception as e:
                logger.error(f"轮询回复失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
