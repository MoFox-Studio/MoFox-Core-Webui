"""初始化向导路由组件

提供系统首次初始化配置向导所需的 API 接口：
- 初始化状态查询
- 机器人基础配置（写入 core.toml 的 personality / permissions 节）
- AI 模型配置（写入 model.toml 的 SiliconFlow API Key）
- Git 路径配置（存入 WebUISettingsStorage）
- 完成初始化（写入 WebUISettingsStorage）

注意：初始化接口不需要 API Key 认证（系统尚未配置时无法认证）
"""

import tomllib
import shutil
import datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException
from pydantic import BaseModel

from src.kernel.logger import get_logger
from src.core.components.base.router import BaseRouter
from src.kernel.config.core import _render_toml_with_signature
from src.core.config.core_config import CoreConfig
from src.core.config.model_config import ModelConfig
from ..storage import WebUISettingsStorage
from ..services.git_env import detect_git_path

logger = get_logger(name="InitRouter", color="yellow")

CORE_CONFIG_PATH  = Path("config/core.toml")
MODEL_CONFIG_PATH = Path("config/model.toml")
BACKUP_DIR        = Path("config/backups")

# 模块级单例
_settings_storage = WebUISettingsStorage()


# ==================== Pydantic API Models ====================


class InitStatusResponse(BaseModel):
    """初始化状态"""
    is_initialized: bool


class BotConfigRequest(BaseModel):
    """机器人配置请求（对应 core.toml personality + permissions 节）"""
    nickname: str = ""
    alias_names: list[str] = []
    personality_core: str = ""
    identity: str = ""
    reply_style: str = ""
    owner_list: list[str] = []          # ["qq:123456", "telegram:789"]


class ModelConfigRequest(BaseModel):
    """模型配置请求（仅 SiliconFlow API Key）"""
    api_key: str


class GitConfigRequest(BaseModel):
    """Git 配置请求"""
    git_path: str


class GitDetectResponse(BaseModel):
    """Git 自动检测响应"""
    found: bool
    path: str | None = None


class OperationResponse(BaseModel):
    """通用操作响应"""
    success: bool
    message: str | None = None
    error: str | None = None


class ValidationResponse(BaseModel):
    """API Key 验证响应"""
    valid: bool
    message: str | None = None


# ==================== 内部工具函数 ====================


def _read_toml(path: Path) -> dict[str, Any]:
    """读取 TOML 文件，不存在则返回空字典"""
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def _create_backup(src: Path, prefix: str) -> None:
    """备份文件，最多保留 10 份"""
    if not src.exists():
        return
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = BACKUP_DIR / f"{prefix}_{ts}.toml"
    shutil.copy2(src, dst)

    all_backups = sorted(
        BACKUP_DIR.glob(f"{prefix}_*.toml"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old in all_backups[10:]:
        try:
            old.unlink()
        except Exception:
            pass


def _reload_core_config() -> None:
    """热重载 core 配置（写文件后调用）"""
    try:
        from src.core.config.core_config import init_core_config
        init_core_config(str(CORE_CONFIG_PATH))
    except Exception as e:
        logger.warning(f"热重载 core 配置失败（不影响已保存文件）: {e}")


def _get_bot_config_from_toml() -> BotConfigRequest:
    """从 core.toml 读取机器人配置"""
    raw = _read_toml(CORE_CONFIG_PATH)
    personality = raw.get("personality", {})
    permissions  = raw.get("permissions", {})
    return BotConfigRequest(
        nickname=personality.get("nickname", ""),
        alias_names=personality.get("alias_names", []),
        personality_core=personality.get("personality_core", ""),
        identity=personality.get("identity", ""),
        reply_style=personality.get("reply_style", ""),
        owner_list=permissions.get("owner_list", []),
    )


def _save_bot_config_to_toml(config: BotConfigRequest) -> None:
    """将机器人配置写回 core.toml，保留其他节"""
    raw = _read_toml(CORE_CONFIG_PATH)

    raw.setdefault("personality", {})
    raw.setdefault("permissions", {})

    raw["personality"]["nickname"] = config.nickname
    raw["personality"]["alias_names"] = config.alias_names
    raw["personality"]["personality_core"] = config.personality_core
    raw["personality"]["identity"] = config.identity
    raw["personality"]["reply_style"] = config.reply_style
    raw["permissions"]["owner_list"] = config.owner_list

    _create_backup(CORE_CONFIG_PATH, "core")
    CORE_CONFIG_PATH.write_text(_render_toml_with_signature(CoreConfig, raw), encoding="utf-8")
    _reload_core_config()


def _get_siliconflow_api_key() -> str:
    """从 model.toml 读取 SiliconFlow API Key"""
    raw = _read_toml(MODEL_CONFIG_PATH)
    for provider in raw.get("api_providers", []):
        if "siliconflow" in provider.get("name", "").lower():
            key = provider.get("api_key", "")
            if isinstance(key, list) and key:
                return key[0]
            return str(key) if key else ""
    return ""


def _save_siliconflow_api_key(api_key: str) -> None:
    """将 SiliconFlow API Key 写回 model.toml"""
    raw = _read_toml(MODEL_CONFIG_PATH)

    providers: list[dict[str, Any]] = raw.get("api_providers", [])
    found = False
    for provider in providers:
        if "siliconflow" in provider.get("name", "").lower():
            provider["api_key"] = api_key
            found = True
            break

    if not found:
        # 如果不存在就新建一条默认的 SiliconFlow 提供商配置
        providers.append({
            "name": "SiliconFlow",
            "base_url": "https://api.siliconflow.cn/v1",
            "api_key": api_key,
            "client_type": "openai",
            "max_retry": 3,
            "timeout": 30,
            "retry_interval": 10,
        })
        raw["api_providers"] = providers

    _create_backup(MODEL_CONFIG_PATH, "model")
    MODEL_CONFIG_PATH.write_text(_render_toml_with_signature(ModelConfig, raw), encoding="utf-8")

    # 热重载模型配置
    try:
        from src.core.config.model_config import init_model_config
        init_model_config(str(MODEL_CONFIG_PATH))
    except Exception as e:
        logger.warning(f"热重载模型配置失败: {e}")


async def _validate_siliconflow_key(api_key: str) -> tuple[bool, str]:
    """发送一次极轻量的请求验证 SiliconFlow API Key"""
    url = "https://api.siliconflow.cn/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            return True, "API Key 有效"
        if resp.status_code in (401, 403):
            return False, "API Key 无效或已过期"
        return False, f"服务器返回 HTTP {resp.status_code}"
    except httpx.TimeoutException:
        return False, "请求超时，请检查网络"
    except Exception as e:
        return False, f"验证失败: {e}"


# ==================== Router ====================


class InitializationRouter(BaseRouter):
    """初始化向导路由组件

    提供以下 API 端点（均无需 API Key 认证）：
    - GET  /status             获取初始化状态
    - GET  /bot-config         获取当前机器人配置
    - POST /bot-config         保存机器人配置
    - GET  /model-config       获取当前模型配置（API Key）
    - POST /model-config       保存模型配置
    - POST /validate-api-key   验证 SiliconFlow API Key
    - GET  /git-config         获取 Git 路径
    - POST /git-config         保存 Git 路径
    - GET  /detect-git         自动检测 Git 路径
    - POST /complete           标记初始化完成
    """

    router_name = "InitializationRouter"
    router_description = "系统初始化向导接口"

    custom_route_path = "/webui/api/initialization"
    cors_origins = ["*"]

    def register_endpoints(self) -> None:
        """注册所有端点"""

        # -------- GET /status --------
        @self.app.get("/status", summary="获取初始化状态", response_model=InitStatusResponse)
        async def get_status():
            """检查系统是否已完成初始化"""
            is_init = await _settings_storage.get_initialized()
            return InitStatusResponse(is_initialized=is_init)

        # -------- GET /bot-config --------
        @self.app.get("/bot-config", summary="获取机器人配置")
        async def get_bot_config():
            """读取 core.toml 中的机器人相关配置"""
            try:
                cfg = _get_bot_config_from_toml()
                return {"success": True, "data": cfg.model_dump()}
            except Exception as e:
                logger.error(f"读取机器人配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # -------- POST /bot-config --------
        @self.app.post("/bot-config", summary="保存机器人配置", response_model=OperationResponse)
        async def save_bot_config(config: BotConfigRequest):
            """将机器人配置写入 core.toml（personality + permissions 节）"""
            try:
                _save_bot_config_to_toml(config)
                logger.info(f"机器人配置已保存: nickname={config.nickname}")
                return OperationResponse(success=True, message="机器人配置已保存")
            except Exception as e:
                logger.error(f"保存机器人配置失败: {e}")
                return OperationResponse(success=False, error=str(e))

        # -------- GET /model-config --------
        @self.app.get("/model-config", summary="获取模型配置")
        async def get_model_config():
            """读取 model.toml 中 SiliconFlow 的 API Key"""
            try:
                api_key = _get_siliconflow_api_key()
                return {"success": True, "data": {"api_key": api_key}}
            except Exception as e:
                logger.error(f"读取模型配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # -------- POST /model-config --------
        @self.app.post("/model-config", summary="保存模型配置", response_model=OperationResponse)
        async def save_model_config(config: ModelConfigRequest):
            """将 SiliconFlow API Key 写入 model.toml"""
            try:
                _save_siliconflow_api_key(config.api_key)
                logger.info("SiliconFlow API Key 已保存")
                return OperationResponse(success=True, message="模型配置已保存")
            except Exception as e:
                logger.error(f"保存模型配置失败: {e}")
                return OperationResponse(success=False, error=str(e))

        # -------- POST /validate-api-key --------
        @self.app.post("/validate-api-key", summary="验证 SiliconFlow API Key", response_model=ValidationResponse)
        async def validate_api_key(body: dict):
            """向 SiliconFlow 发送测试请求验证 API Key 有效性"""
            api_key = body.get("api_key", "")
            if not api_key:
                return ValidationResponse(valid=False, message="API Key 不能为空")
            valid, msg = await _validate_siliconflow_key(api_key)
            return ValidationResponse(valid=valid, message=msg)

        # -------- GET /git-config --------
        @self.app.get("/git-config", summary="获取 Git 配置")
        async def get_git_config():
            """从 WebUISettingsStorage 获取 Git 可执行文件路径"""
            try:
                git_path = await _settings_storage.get_git_path()
                return {"success": True, "data": {"git_path": git_path}}
            except Exception as e:
                logger.error(f"读取 Git 配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # -------- POST /git-config --------
        @self.app.post("/git-config", summary="保存 Git 配置", response_model=OperationResponse)
        async def save_git_config(config: GitConfigRequest):
            """将 Git 路径保存到 WebUISettingsStorage"""
            try:
                await _settings_storage.set_git_path(config.git_path)
                return OperationResponse(success=True, message="Git 配置已保存")
            except Exception as e:
                logger.error(f"保存 Git 配置失败: {e}")
                return OperationResponse(success=False, error=str(e))

        # -------- GET /detect-git --------
        @self.app.get("/detect-git", summary="自动检测 Git 路径", response_model=GitDetectResponse)
        async def detect_git():
            """扫描常见路径自动检测 Git 可执行文件"""
            path = detect_git_path()
            if path:
                return GitDetectResponse(found=True, path=path)
            return GitDetectResponse(found=False)

        # -------- POST /complete --------
        @self.app.post("/complete", summary="完成初始化", response_model=OperationResponse)
        async def complete_initialization():
            """将初始化完成标志写入 WebUISettingsStorage"""
            try:
                await _settings_storage.set_initialized(True)
                logger.info("系统初始化已标记完成")
                return OperationResponse(success=True, message="初始化完成")
            except Exception as e:
                logger.error(f"标记初始化完成失败: {e}")
                return OperationResponse(success=False, error=str(e))

    async def startup(self) -> None:
        logger.info(f"InitializationRouter 已启动，路径: {self.custom_route_path}")

    async def shutdown(self) -> None:
        logger.info("InitializationRouter 已关闭")
