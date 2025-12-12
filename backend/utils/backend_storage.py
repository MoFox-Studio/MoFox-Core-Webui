"""
@File    :   backend_storage.py
@Time    :   2025/12/12 00:00:00
@Author  :   墨墨
@Version :   1.0
@Desc    :   WebUI 后端统一存储管理 API
"""

from typing import Any, Optional
from pathlib import Path
import sys

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.plugin_system.apis.storage_api import get_local_storage


class BackendStorage:
    """后端存储管理类，使用 storage_api 统一管理配置"""
    
    _storage_name = "webui_backend"
    
    @classmethod
    def _get_storage(cls):
        """获取存储实例"""
        return get_local_storage(cls._storage_name)
    
    # ==================== Git 配置相关 ====================
    
    @classmethod
    def get_git_path(cls) -> Optional[str]:
        """
        获取自定义的 Git 路径
        
        Returns:
            Optional[str]: Git 可执行文件路径，如果未设置则返回 None
        """
        storage = cls._get_storage()
        return storage.get("git_custom_path", None)
    
    @classmethod
    def set_git_path(cls, path: str) -> bool:
        """
        设置自定义的 Git 路径
        
        Args:
            path: Git 可执行文件的完整路径
            
        Returns:
            bool: 是否设置成功
        """
        storage = cls._get_storage()
        storage.set("git_custom_path", path)
        return True
    
    @classmethod
    def clear_git_path(cls) -> bool:
        """
        清除自定义的 Git 路径
        
        Returns:
            bool: 是否清除成功
        """
        storage = cls._get_storage()
        return storage.delete("git_custom_path")
    
    @classmethod
    def get_git_source(cls) -> str:
        """
        获取当前 Git 的来源类型
        
        Returns:
            str: 'custom' | 'portable' | 'system' | 'unknown'
        """
        storage = cls._get_storage()
        return storage.get("git_source", "unknown")
    
    @classmethod
    def set_git_source(cls, source: str) -> None:
        """
        设置 Git 的来源类型
        
        Args:
            source: 来源类型 ('custom' | 'portable' | 'system')
        """
        storage = cls._get_storage()
        storage.set("git_source", source)
    
    # ==================== 通用配置相关 ====================
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        storage = cls._get_storage()
        return storage.get(key, default)
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        storage = cls._get_storage()
        storage.set(key, value)
    
    @classmethod
    def delete(cls, key: str) -> bool:
        """
        删除配置
        
        Args:
            key: 配置键
            
        Returns:
            bool: 是否删除成功
        """
        storage = cls._get_storage()
        return storage.delete(key)
    
    @classmethod
    def get_all(cls) -> dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            dict: 所有配置数据
        """
        storage = cls._get_storage()
        return storage.get_all()
