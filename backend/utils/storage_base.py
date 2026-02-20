"""统一的 JSON 本地持久化存储基类

提供抽象基类供其他模块继承使用。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from src.kernel.storage import json_store


class BaseJSONStorage(ABC):
    """JSON 持久化存储抽象基类
    
    子类需要设置 storage_name 类属性来指定存储文件名。
    
    示例:
        >>> class UserStorage(BaseJSONStorage):
        ...     storage_name = "users"
        ...     
        ...     async def get_user(self, user_id: str):
        ...         data = await self.load()
        ...         return data.get(user_id) if data else None
        ...
        >>> user_storage = UserStorage()
        >>> await user_storage.save({"user1": {"name": "Alice"}})
        >>> user = await user_storage.get_user("user1")
    """
    
    storage_name: ClassVar[str] = ""
    """存储文件名（不含 .json 后缀），子类必须设置此属性"""
    
    def __init__(self):
        """初始化存储基类"""
        if not self.storage_name:
            raise ValueError(
                f"{self.__class__.__name__} 必须设置 storage_name 类属性"
            )
    
    async def save(self, data: dict[str, Any]) -> None:
        """保存数据到 JSON 文件
        
        Args:
            data: 要保存的数据字典
            
        Raises:
            IOError: 如果文件写入失败
        """
        await json_store.save(self.storage_name, data)
    
    async def load(self) -> dict[str, Any] | None:
        """从 JSON 文件加载数据
        
        Returns:
            dict[str, Any] | None: 加载的数据字典，如果文件不存在则返回 None
            
        Raises:
            json.JSONDecodeError: 如果 JSON 格式错误
        """
        return await json_store.load(self.storage_name)
    
    async def delete(self) -> bool:
        """删除存储文件
        
        Returns:
            bool: 是否成功删除（文件不存在时返回 False）
        """
        return await json_store.delete(self.storage_name)
    
    async def exists(self) -> bool:
        """检查存储文件是否存在
        
        Returns:
            bool: 文件是否存在
        """
        return await json_store.exists(self.storage_name)
    
    async def load_or_default(self, default: dict[str, Any] | None = None) -> dict[str, Any]:
        """加载数据，如果不存在则返回默认值
        
        Args:
            default: 默认值，如果为 None 则返回空字典
            
        Returns:
            dict[str, Any]: 加载的数据或默认值
        """
        data = await self.load()
        if data is None:
            return default if default is not None else {}
        return data
    
    async def update(self, updates: dict[str, Any], merge: bool = True) -> None:
        """更新数据
        
        Args:
            updates: 要更新的数据
            merge: 是否合并现有数据，True 则合并，False 则覆盖
        """
        if merge:
            existing = await self.load_or_default()
            existing.update(updates)
            await self.save(existing)
        else:
            await self.save(updates)
    
    async def get_value(self, key: str, default: Any = None) -> Any:
        """获取指定键的值
        
        Args:
            key: 键名
            default: 默认值
            
        Returns:
            Any: 键对应的值，如果不存在则返回默认值
        """
        data = await self.load_or_default()
        return data.get(key, default)
    
    async def set_value(self, key: str, value: Any) -> None:
        """设置指定键的值
        
        Args:
            key: 键名
            value: 要设置的值
        """
        data = await self.load_or_default()
        data[key] = value
        await self.save(data)
    
    async def delete_value(self, key: str) -> bool:
        """删除指定键
        
        Args:
            key: 键名
            
        Returns:
            bool: 是否成功删除（键不存在时返回 False）
        """
        data = await self.load_or_default()
        if key in data:
            del data[key]
            await self.save(data)
            return True
        return False


__all__ = ["BaseJSONStorage"]
