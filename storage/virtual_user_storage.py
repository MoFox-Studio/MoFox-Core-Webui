"""虚拟用户 JSON 持久化存储

使用 BaseJSONStorage 管理 chatroom 虚拟用户数据，并同步写入 PersonInfo 数据库表。

JSON 文件结构:
{
    "<user_id>": {
        "user_id": "string",
        "nickname": "string",
        "avatar": "string",
        "created_at": 1234567890.0,
        "init_impression": "string",
        "init_short_impression": "string",
        "init_attitude": 50,
        "init_memory_points": [{"content": "...", "weight": 1.0}]
    }
}
"""

from __future__ import annotations

import json
import time
from typing import Any

from src.kernel.logger import get_logger
from ..utils.storage_base import BaseJSONStorage

logger = get_logger(name="VirtualUserStorage", color="#89DCEB")

PLATFORM = "webui"


class VirtualUserStorage(BaseJSONStorage):
    """虚拟用户存储类

    负责管理 chatroom 虚拟用户的 JSON 快照数据，
    并通过 CRUDBase 同步写入 PersonInfo 数据库表。
    """

    storage_name = "chatroom_users"

    # ------------------------------------------------------------------ #
    #  JSON 快照 CRUD                                                     #
    # ------------------------------------------------------------------ #

    async def get_all_users(self) -> dict[str, dict[str, Any]]:
        """获取所有虚拟用户的 JSON 快照"""
        return await self.load_or_default({})

    async def get_user(self, user_id: str) -> dict[str, Any] | None:
        """获取单个虚拟用户的 JSON 快照"""
        data = await self.load_or_default({})
        return data.get(user_id)

    async def create_user(self, user_id: str, user_data: dict[str, Any]) -> None:
        """新增虚拟用户快照到 JSON 文件"""
        data = await self.load_or_default({})
        data[user_id] = user_data
        await self.save(data)

    async def update_user_snapshot(self, user_id: str, updates: dict[str, Any]) -> bool:
        """更新虚拟用户快照（只更新传入的字段）"""
        data = await self.load_or_default({})
        if user_id not in data:
            return False
        data[user_id].update(updates)
        await self.save(data)
        return True

    async def delete_user(self, user_id: str) -> bool:
        """从 JSON 文件中删除虚拟用户快照"""
        data = await self.load_or_default({})
        if user_id not in data:
            return False
        del data[user_id]
        await self.save(data)
        return True

    async def user_exists(self, user_id: str) -> bool:
        """判断虚拟用户是否存在"""
        data = await self.load_or_default({})
        return user_id in data

    # ------------------------------------------------------------------ #
    #  DB 同步：PersonInfo                                                #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_person_id(user_id: str) -> str:
        return f"{PLATFORM}:{user_id}"

    @staticmethod
    def _serialize_points(memory_points: list[dict[str, Any]] | None) -> str | None:
        """将 memory_points 列表序列化为 JSON 字符串存入 points 字段"""
        if memory_points is None:
            return None
        return json.dumps(memory_points, ensure_ascii=False)

    @staticmethod
    def _deserialize_points(points_str: str | None) -> list[dict[str, Any]]:
        """从 points 字段反序列化 memory_points 列表"""
        if not points_str:
            return []
        try:
            return json.loads(points_str)
        except (json.JSONDecodeError, TypeError):
            return []

    async def sync_create_to_db(
        self,
        user_id: str,
        nickname: str,
        avatar: str = "",
        impression: str = "",
        short_impression: str = "",
        attitude: int = 50,
        memory_points: list[dict[str, Any]] | None = None,
        created_at: float | None = None,
    ) -> bool:
        """将新虚拟用户同步写入 PersonInfo 数据库表"""
        try:
            from src.kernel.db import CRUDBase
            from src.core.models.sql_alchemy import PersonInfo

            now = created_at or time.time()
            record = {
                "person_id": self._build_person_id(user_id),
                "platform": PLATFORM,
                "user_id": user_id,
                "nickname": nickname,
                "impression": impression,
                "short_impression": short_impression,
                "attitude": attitude,
                "points": self._serialize_points(memory_points or []),
                "created_at": now,
                "updated_at": now,
            }
            crud = CRUDBase(PersonInfo)
            await crud.create(record)
            return True
        except Exception as e:
            logger.error(f"同步创建 PersonInfo 失败 (user_id={user_id}): {e}", exc_info=True)
            return False

    async def sync_update_to_db(
        self,
        user_id: str,
        updates: dict[str, Any],
    ) -> bool:
        """将字段更新同步写入 PersonInfo 数据库表"""
        try:
            from src.kernel.db import CRUDBase
            from src.core.models.sql_alchemy import PersonInfo

            person_id = self._build_person_id(user_id)
            db_updates: dict[str, Any] = {}

            for field in ("nickname", "impression", "short_impression", "attitude"):
                if field in updates:
                    db_updates[field] = updates[field]

            if "memory_points" in updates:
                db_updates["points"] = self._serialize_points(updates["memory_points"])

            if not db_updates:
                return True  # 没有需要更新的字段

            db_updates["updated_at"] = time.time()
            crud = CRUDBase(PersonInfo)
            record = await crud.get_by(person_id=person_id)
            if record is None:
                # DB 记录不存在（可能建用户时写库失败），拉快照重建后再更新
                logger.warning(f"update: PersonInfo 不存在，尝试重新创建 (user_id={user_id})")
                snapshot = await self.get_user(user_id)
                if not snapshot:
                    return False
                created = await self.sync_create_to_db(
                    user_id=user_id,
                    nickname=snapshot.get("nickname", ""),
                    impression=snapshot.get("init_impression", ""),
                    short_impression=snapshot.get("init_short_impression", ""),
                    attitude=snapshot.get("init_attitude", 50),
                    memory_points=snapshot.get("init_memory_points", []),
                    created_at=snapshot.get("created_at"),
                )
                if not created:
                    return False
                record = await crud.get_by(person_id=person_id)
                if record is None:
                    return False
            await crud.update(record.id, db_updates)
            return True
        except Exception as e:
            logger.error(f"同步更新 PersonInfo 失败 (user_id={user_id}): {e}", exc_info=True)
            return False

    async def sync_delete_from_db(self, user_id: str) -> bool:
        """从 PersonInfo 数据库表中删除虚拟用户"""
        try:
            from src.kernel.db import CRUDBase
            from src.core.models.sql_alchemy import PersonInfo

            person_id = self._build_person_id(user_id)
            crud = CRUDBase(PersonInfo)
            record = await crud.get_by(person_id=person_id)
            if record is None:
                return True  # 已不存在，视为成功
            await crud.delete(record.id)
            return True
        except Exception as e:
            logger.error(f"同步删除 PersonInfo 失败 (user_id={user_id}): {e}", exc_info=True)
            return False

    async def sync_reset_to_db(self, user_id: str) -> bool:
        """将 PersonInfo 恢复为 JSON 快照中的 init_* 初始值，并清空 points"""
        try:
            from src.kernel.db import CRUDBase
            from src.core.models.sql_alchemy import PersonInfo

            snapshot = await self.get_user(user_id)
            if not snapshot:
                return False

            person_id = self._build_person_id(user_id)
            reset_data = {
                "impression": snapshot.get("init_impression", ""),
                "short_impression": snapshot.get("init_short_impression", ""),
                "attitude": snapshot.get("init_attitude", 50),
                "points": self._serialize_points(snapshot.get("init_memory_points", [])),
                "updated_at": time.time(),
            }
            crud = CRUDBase(PersonInfo)
            record = await crud.get_by(person_id=person_id)
            if record is None:
                # DB 记录不存在（可能建用户时写库失败），重新创建
                logger.warning(f"reset: PersonInfo 不存在，尝试重新创建 (user_id={user_id})")
                return await self.sync_create_to_db(
                    user_id=user_id,
                    nickname=snapshot.get("nickname", ""),
                    impression=reset_data["impression"],
                    short_impression=reset_data["short_impression"],
                    attitude=reset_data["attitude"],
                    memory_points=snapshot.get("init_memory_points", []),
                    created_at=snapshot.get("created_at"),
                )
            await crud.update(record.id, reset_data)
            return True
        except Exception as e:
            logger.error(f"重置 PersonInfo 失败 (user_id={user_id}): {e}", exc_info=True)
            return False

    async def get_db_user(self, user_id: str) -> dict[str, Any] | None:
        """从 PersonInfo 数据库查询单个虚拟用户的当前状态"""
        try:
            from src.kernel.db import QueryBuilder
            from src.core.models.sql_alchemy import PersonInfo

            person_id = self._build_person_id(user_id)
            query = QueryBuilder(PersonInfo).filter(person_id=person_id)
            result = await query.first(as_dict=True)
            return result
        except Exception as e:
            logger.error(f"查询 PersonInfo 失败 (user_id={user_id}): {e}", exc_info=True)
            return None

    async def get_merged_user(self, user_id: str) -> dict[str, Any] | None:
        """合并 JSON 快照 + DB 当前状态，返回完整用户信息"""
        snapshot = await self.get_user(user_id)
        if not snapshot:
            return None

        db_record = await self.get_db_user(user_id)

        merged: dict[str, Any] = {
            "user_id": user_id,
            "nickname": snapshot.get("nickname", ""),
            "avatar": snapshot.get("avatar", ""),
            "created_at": snapshot.get("created_at", 0.0),
            "person_id": self._build_person_id(user_id),
            # DB 当前值（若无则降回快照初始值）
            "impression": db_record.get("impression", snapshot.get("init_impression", "")) if db_record else snapshot.get("init_impression", ""),
            "short_impression": db_record.get("short_impression", snapshot.get("init_short_impression", "")) if db_record else snapshot.get("init_short_impression", ""),
            "attitude": db_record.get("attitude", snapshot.get("init_attitude", 50)) if db_record else snapshot.get("init_attitude", 50),
            "memory_points": self._deserialize_points(db_record.get("points") if db_record else None),
            "updated_at": db_record.get("updated_at", snapshot.get("created_at", 0.0)) if db_record else snapshot.get("created_at", 0.0),
        }
        return merged

    async def get_all_merged_users(self) -> list[dict[str, Any]]:
        """批量获取所有虚拟用户的合并信息"""
        snapshots = await self.get_all_users()
        result = []
        for user_id in snapshots:
            merged = await self.get_merged_user(user_id)
            if merged:
                result.append(merged)
        return result
