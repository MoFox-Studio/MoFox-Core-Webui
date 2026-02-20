"""WebUI 设置持久化存储

使用 BaseJSONStorage 管理 WebUI 全局设置数据，包括：
- is_initialized: 系统是否已完成初始化向导
- git_path: Git 可执行文件路径

JSON 文件结构:
{
    "is_initialized": false,
    "git_path": ""
}
"""

from __future__ import annotations

from src.kernel.logger import get_logger
from ..utils.storage_base import BaseJSONStorage

logger = get_logger(name="WebUISettingsStorage", color="#F9E2AF")

_DEFAULTS = {
    "is_initialized": False,
    "git_path": "",
}


class WebUISettingsStorage(BaseJSONStorage):
    """WebUI 设置存储类

    存储 WebUI 的全局配置，如初始化状态和 Git 路径。
    """

    storage_name = "webui_settings"

    async def get_all(self) -> dict:
        """获取所有设置（不存在时返回默认值）"""
        return await self.load_or_default(_DEFAULTS.copy())

    # ------------------------------------------------------------------ #
    #  初始化状态                                                          #
    # ------------------------------------------------------------------ #

    async def get_initialized(self) -> bool:
        """获取初始化完成状态"""
        return await self.get_value("is_initialized", False)

    async def set_initialized(self, value: bool = True) -> None:
        """设置初始化完成状态"""
        await self.set_value("is_initialized", value)
        logger.info(f"初始化状态已更新: {value}")

    # ------------------------------------------------------------------ #
    #  Git 路径                                                            #
    # ------------------------------------------------------------------ #

    async def get_git_path(self) -> str:
        """获取 Git 可执行文件路径"""
        return await self.get_value("git_path", "")

    async def set_git_path(self, git_path: str) -> None:
        """设置 Git 可执行文件路径"""
        await self.set_value("git_path", git_path)
        logger.info(f"Git 路径已更新: {git_path!r}")
