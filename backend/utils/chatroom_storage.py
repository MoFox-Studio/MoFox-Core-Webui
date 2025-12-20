"""
UI Chatroom 数据存储模块

使用JSON文件存储虚拟用户和聊天室设置
"""

import json
import time
from pathlib import Path
from typing import Any

from src.common.logger import get_logger

logger = get_logger("ui_chatroom_storage")


class ChatroomStorage:
    """聊天室数据存储"""

    def __init__(self, storage_dir: str | None = None):
        """初始化存储"""
        if storage_dir is None:
            # 默认使用 backend/storage/chatroom
            backend_dir = Path(__file__).parent.parent
            storage_dir = str(backend_dir / "storage" / "chatroom")

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 数据文件路径
        self.users_file = self.storage_dir / "virtual_users.json"
        self.settings_file = self.storage_dir / "settings.json"

        # 加载数据
        self._users: dict[str, dict[str, Any]] = self._load_json(self.users_file, {})
        self._settings: dict[str, Any] = self._load_json(
            self.settings_file,
            {
                "chat_id": "ui_chatroom_default",
                "bot_nickname": "麦麦",
                "welcome_message": "欢迎来到UI聊天室！",
            },
        )

        logger.info(f"聊天室存储初始化完成，存储目录: {self.storage_dir}")

    def _load_json(self, file_path: Path, default: Any) -> Any:
        """加载JSON文件"""
        try:
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return default
        except Exception as e:
            logger.error(f"加载JSON文件失败 {file_path}: {e}", exc_info=True)
            return default

    def _save_json(self, file_path: Path, data: Any):
        """保存JSON文件"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存JSON文件失败 {file_path}: {e}", exc_info=True)
            raise

    # ========== 虚拟用户管理 ==========

    def create_user(
        self, 
        user_id: str, 
        nickname: str, 
        impression: str = "", 
        short_impression: str = "",
        avatar: str = "",
        attitude: int | None = None
    ) -> dict[str, Any]:
        """创建虚拟用户"""
        if user_id in self._users:
            raise ValueError(f"用户 {user_id} 已存在")

        user = {
            "user_id": user_id,
            "nickname": nickname,
            "impression": impression,
            "short_impression": short_impression,
            "avatar": avatar,
            "attitude": attitude,
            "created_at": time.time(),
            "updated_at": time.time(),
        }

        self._users[user_id] = user
        self._save_json(self.users_file, self._users)

        logger.info(f"创建虚拟用户: {user_id} ({nickname})")
        return user.copy()

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        """获取虚拟用户"""
        user = self._users.get(user_id)
        return user.copy() if user else None

    def get_all_users(self) -> list[dict[str, Any]]:
        """获取所有虚拟用户"""
        return [user.copy() for user in self._users.values()]

    def update_user(self, user_id: str, **kwargs) -> dict[str, Any]:
        """更新虚拟用户"""
        if user_id not in self._users:
            raise ValueError(f"用户 {user_id} 不存在")

        user = self._users[user_id]

        # 更新允许的字段
        allowed_fields = {
            "nickname", 
            "impression", 
            "short_impression",
            "avatar", 
            "attitude"
        }
        for key, value in kwargs.items():
            if key in allowed_fields:
                user[key] = value

        user["updated_at"] = time.time()
        self._save_json(self.users_file, self._users)

        logger.info(f"更新虚拟用户: {user_id}")
        return user.copy()

    def delete_user(self, user_id: str) -> bool:
        """删除虚拟用户"""
        if user_id in self._users:
            del self._users[user_id]
            self._save_json(self.users_file, self._users)
            logger.info(f"删除虚拟用户: {user_id}")
            return True
        return False

    # ========== 设置管理 ==========

    def get_settings(self) -> dict[str, Any]:
        """获取设置"""
        return self._settings.copy()

    def get_chat_id(self) -> str:
        """获取聊天ID"""
        return self._settings.get("chat_id", "ui_chatroom_default")

    def update_settings(self, **kwargs):
        """更新设置"""
        self._settings.update(kwargs)
        self._save_json(self.settings_file, self._settings)
        logger.info("更新聊天室设置")


# 全局实例
_storage_instance: ChatroomStorage | None = None


def get_chatroom_storage() -> ChatroomStorage:
    """获取全局存储实例"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = ChatroomStorage()
    return _storage_instance
