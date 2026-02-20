"""Git 环境管理服务

封装与存储层的交互，提供对外统一的 Git 环境管理接口：
- get_git_env_status()   获取完整的 Git 环境状态
- set_git_path()         设置自定义 Git 路径（验证 + 持久化）
- auto_detect_git()      清除自定义配置并重新自动检测
"""

from __future__ import annotations

from typing import Any

from src.kernel.logger import get_logger
from ...storage import WebUISettingsStorage
from .detector import detect_git_path, get_git_version, get_system_os, resolve_git_source

logger = get_logger(name="GitEnvManager", color="#89DCEB")

# 模块级存储单例（与 initialization_router 共享同一实例）
_storage = WebUISettingsStorage()


async def get_git_env_status() -> dict[str, Any]:
    """获取完整的 Git 环境状态。

    优先使用存储中保存的自定义路径，其次自动检测。

    Returns:
        符合前端 GitEnvStatus 接口的字典：
        {
            "git_available": bool,
            "git_version": str | None,
            "git_path": str | None,
            "git_source": "custom" | "portable" | "system" | "unknown",
            "is_portable": bool,
            "system_os": str,
        }
    """
    system_os = get_system_os()
    custom_path = await _storage.get_git_path()

    if custom_path:
        # 使用存储的自定义路径
        version = get_git_version(custom_path)
        if version:
            return {
                "git_available": True,
                "git_version": version,
                "git_path": custom_path,
                "git_source": "custom",
                "is_portable": False,
                "system_os": system_os,
            }
        else:
            # 自定义路径已失效，回退到自动检测
            logger.warning(f"自定义 Git 路径无效，尝试自动检测: {custom_path!r}")

    # 自动检测
    detected_path = detect_git_path()
    if detected_path:
        version = get_git_version(detected_path)
        source, is_portable = resolve_git_source(detected_path)
        return {
            "git_available": True,
            "git_version": version,
            "git_path": detected_path,
            "git_source": source,
            "is_portable": is_portable,
            "system_os": system_os,
        }

    return {
        "git_available": False,
        "git_version": None,
        "git_path": None,
        "git_source": "unknown",
        "is_portable": False,
        "system_os": system_os,
    }


async def set_git_path(path: str) -> dict[str, Any]:
    """验证并持久化自定义 Git 路径。

    Args:
        path: Git 可执行文件的绝对或相对路径

    Returns:
        符合前端 GitSetPathResult 接口的字典：
        {"success": bool, "message": str, "git_path": str | None, "git_version": str | None, "error": str | None}
    """
    if not path:
        return {"success": False, "message": "路径不能为空", "error": "empty_path"}

    version = get_git_version(path)
    if not version:
        return {
            "success": False,
            "message": f"指定路径无法执行 Git: {path!r}",
            "error": "invalid_git_path",
        }

    await _storage.set_git_path(path)
    logger.info(f"自定义 Git 路径已保存: {path!r}  版本: {version}")
    return {
        "success": True,
        "message": "Git 路径已设置",
        "git_path": path,
        "git_version": version,
    }


async def auto_detect_git() -> dict[str, Any]:
    """清除自定义 Git 路径配置并重新自动检测。

    Returns:
        符合前端 GitSetPathResult 接口的字典
    """
    # 清除自定义路径
    await _storage.set_git_path("")

    detected_path = detect_git_path()
    if not detected_path:
        return {
            "success": False,
            "message": "未检测到系统中的 Git，请手动安装或指定路径",
            "git_path": None,
            "git_version": None,
        }

    version = get_git_version(detected_path)
    logger.info(f"自动检测到 Git: {detected_path!r}  版本: {version}")
    return {
        "success": True,
        "message": f"已检测到 Git: {detected_path}",
        "git_path": detected_path,
        "git_version": version,
    }


async def get_storage() -> WebUISettingsStorage:
    """返回共享存储实例（供其他模块复用）"""
    return _storage
