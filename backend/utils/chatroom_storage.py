"""
UI Chatroom 数据存储模块

使用JSON文件存储虚拟用户和聊天室设置
使用SQLite数据库存储聊天室消息
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from src.common.logger import get_logger
from src.config.config import PROJECT_ROOT


logger = get_logger("ui_chatroom_storage")


class ChatroomStorage:
    """聊天室数据存储（用户和设置）"""

    def __init__(self, storage_dir: str | None = None):
        """初始化存储"""
        if storage_dir is None:
            # 统一使用 data/webui/ 目录
            storage_dir = "data/webui"

        self.storage_dir = Path(PROJECT_ROOT) / storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 数据文件路径
        self.users_file = self.storage_dir / "virtual_users.json"
        self.settings_file = self.storage_dir / "chatroom_settings.json"

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
        attitude: int | None = None,
        memory_points: list[str] | None = None
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
            "memory_points": memory_points or [],
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
            "attitude",
            "memory_points"
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


class ChatroomMessageStorage:
    """聊天室消息存储（SQLite数据库）"""

    def __init__(self, db_path: str | None = None):
        """初始化存储"""
        if db_path is None:
            # 统一使用 data/webui/chatroom_messages.db
            db_path = "data/webui/chatroom_messages.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_database()

        logger.info(f"聊天室消息存储初始化完成，数据库路径: {self.db_path}")

    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建消息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    nickname TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    message_type TEXT DEFAULT 'text',
                    reply_to TEXT,
                    user_platform TEXT DEFAULT 'web_ui_chatroom',
                    chat_id TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    emoji_hashes TEXT
                )
            """)
            
            # 检查并添加emoji_hashes列（如果不存在）
            try:
                cursor.execute("SELECT emoji_hashes FROM messages LIMIT 1")
            except sqlite3.OperationalError:
                # 列不存在，添加它
                cursor.execute("ALTER TABLE messages ADD COLUMN emoji_hashes TEXT")
                logger.info("已添加emoji_hashes列到messages表")
            
            # 创建索引以提高查询性能
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON messages(timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_id 
                ON messages(chat_id, timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id 
                ON messages(user_id, timestamp DESC)
            """)
            
            conn.commit()
            logger.debug("消息数据库表初始化完成")

    def save_message(
        self,
        message_id: str,
        user_id: str,
        nickname: str,
        content: str,
        timestamp: float,
        chat_id: str,
        message_type: str = "text",
        reply_to: str | None = None,
        user_platform: str = "web_ui_chatroom",
        emoji_hashes: str | None = None
    ) -> bool:
        """保存消息到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO messages 
                    (message_id, user_id, nickname, content, timestamp, 
                     message_type, reply_to, user_platform, chat_id, created_at, emoji_hashes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    message_id, user_id, nickname, content, timestamp,
                    message_type, reply_to, user_platform, chat_id, time.time(), emoji_hashes
                ))
                conn.commit()
                logger.debug(f"保存消息: {message_id} from {nickname}")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"消息已存在: {message_id}")
            return False
        except Exception as e:
            logger.error(f"保存消息失败: {e}", exc_info=True)
            return False

    def get_message(self, message_id: str) -> dict[str, Any] | None:
        """获取单条消息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM messages WHERE message_id = ?
                """, (message_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"获取消息失败: {e}", exc_info=True)
            return None

    def get_messages_by_time_range(
        self,
        chat_id: str,
        start_time: float | None = None,
        end_time: float | None = None,
        limit: int = 100,
        limit_mode: str = "latest"
    ) -> list[dict[str, Any]]:
        """
        按时间范围获取消息
        
        Args:
            chat_id: 聊天ID
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            limit: 限制返回数量
            limit_mode: "latest" 返回最新的消息, "earliest" 返回最早的消息
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 构建查询
                query = "SELECT * FROM messages WHERE chat_id = ?"
                params = [chat_id]
                
                if start_time is not None:
                    query += " AND timestamp >= ?"
                    params.append(start_time)
                
                if end_time is not None:
                    query += " AND timestamp <= ?"
                    params.append(end_time)
                
                # 排序和限制
                if limit_mode == "latest":
                    query += " ORDER BY timestamp DESC LIMIT ?"
                else:
                    query += " ORDER BY timestamp ASC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                messages = [dict(row) for row in rows]
                
                # 如果是获取最新消息，需要反转顺序以保持时间顺序
                if limit_mode == "latest":
                    messages.reverse()
                
                logger.debug(f"获取到 {len(messages)} 条消息")
                return messages
        except Exception as e:
            logger.error(f"获取消息失败: {e}", exc_info=True)
            return []

    def get_messages_before_time(
        self,
        chat_id: str,
        timestamp: float,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """获取指定时间之前的消息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM messages 
                    WHERE chat_id = ? AND timestamp < ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (chat_id, timestamp, limit))
                
                rows = cursor.fetchall()
                messages = [dict(row) for row in rows]
                
                # 反转以保持时间顺序
                messages.reverse()
                
                logger.debug(f"获取到 {len(messages)} 条消息（before {timestamp}）")
                return messages
        except Exception as e:
            logger.error(f"获取消息失败: {e}", exc_info=True)
            return []

    def get_messages_after_time(
        self,
        chat_id: str,
        timestamp: float,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """获取指定时间之后的消息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM messages 
                    WHERE chat_id = ? AND timestamp > ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                """, (chat_id, timestamp, limit))
                
                rows = cursor.fetchall()
                messages = [dict(row) for row in rows]
                
                logger.debug(f"获取到 {len(messages)} 条消息（after {timestamp}）")
                return messages
        except Exception as e:
            logger.error(f"获取消息失败: {e}", exc_info=True)
            return []

    def get_user_messages(
        self,
        user_id: str,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """获取指定用户的消息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM messages 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
                
                rows = cursor.fetchall()
                messages = [dict(row) for row in rows]
                messages.reverse()
                
                logger.debug(f"获取到用户 {user_id} 的 {len(messages)} 条消息")
                return messages
        except Exception as e:
            logger.error(f"获取用户消息失败: {e}", exc_info=True)
            return []

    def delete_message(self, message_id: str) -> bool:
        """删除消息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM messages WHERE message_id = ?", (message_id,))
                conn.commit()
                
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"删除消息: {message_id}")
                return deleted
        except Exception as e:
            logger.error(f"删除消息失败: {e}", exc_info=True)
            return False

    def delete_chat_messages(self, chat_id: str) -> int:
        """删除指定聊天的所有消息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
                conn.commit()
                
                deleted_count = cursor.rowcount
                logger.info(f"删除聊天 {chat_id} 的 {deleted_count} 条消息")
                return deleted_count
        except Exception as e:
            logger.error(f"删除聊天消息失败: {e}", exc_info=True)
            return 0

    def get_message_count(self, chat_id: str | None = None) -> int:
        """获取消息数量"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if chat_id:
                    cursor.execute("SELECT COUNT(*) FROM messages WHERE chat_id = ?", (chat_id,))
                else:
                    cursor.execute("SELECT COUNT(*) FROM messages")
                
                count = cursor.fetchone()[0]
                return count
        except Exception as e:
            logger.error(f"获取消息数量失败: {e}", exc_info=True)
            return 0


# 全局实例
_storage_instance: ChatroomStorage | None = None
_message_storage_instance: ChatroomMessageStorage | None = None


def get_chatroom_storage() -> ChatroomStorage:
    """获取全局存储实例（用户和设置）"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = ChatroomStorage()
    return _storage_instance


def get_chatroom_message_storage() -> ChatroomMessageStorage:
    """获取全局消息存储实例"""
    global _message_storage_instance
    if _message_storage_instance is None:
        _message_storage_instance = ChatroomMessageStorage()
    return _message_storage_instance
