"""
初始化系统路由组件
提供首次配置向导的后端接口
"""

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import tomlkit
from fastapi import HTTPException
from pydantic import BaseModel

from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.config.config import CONFIG_DIR
from src.plugin_system import BaseRouterComponent

# 导入后端存储管理
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.backend_storage import BackendStorage

logger = get_logger("WebUI.InitializationRouter")

# 配置文件路径
CONFIG_ROOT = Path(CONFIG_DIR)
BOT_CONFIG_PATH = CONFIG_ROOT / "bot_config.toml"
MODEL_CONFIG_PATH = CONFIG_ROOT / "model_config.toml"

# 初始化状态的存储键名
INIT_STATUS_KEY = "is_initialized"


# ==================== 请求/响应模型 ====================

class InitStatusResponse(BaseModel):
    """初始化状态响应"""
    is_initialized: bool


class BotConfigRequest(BaseModel):
    """机器人配置请求"""
    qq_account: int
    nickname: str
    alias_names: list[str]
    personality_core: str
    identity: str
    reply_style: str
    master_users: list[list[str]] = []  # 主人用户列表，格式为 [[platform, user_id], ...]


class ModelConfigRequest(BaseModel):
    """模型配置请求"""
    api_key: str
    provider_name: str = "SiliconFlow"
    base_url: str = "https://api.siliconflow.cn/v1"


class GitConfigRequest(BaseModel):
    """Git配置请求"""
    git_path: str


class ValidationResponse(BaseModel):
    """验证响应"""
    valid: bool
    message: Optional[str] = None


class ApiKeyValidationRequest(BaseModel):
    """API密钥验证请求"""
    api_key: str


# ==================== 工具函数 ====================

def detect_git_path() -> Optional[str]:
    """自动检测Git路径"""
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Windows: 尝试获取git.exe的路径
            result = subprocess.run(
                ["where", "git"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip().split("\n")[0]
    except Exception:
        pass
    return None


def create_backup(config_path: Path) -> Optional[str]:
    """创建配置文件备份"""
    if not config_path.exists():
        return None
    
    backup_dir = config_path.parent / "backups_from_webui"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{config_path.stem}_webinit_backup_{timestamp}{config_path.suffix}"
    backup_path = backup_dir / backup_name
    
    shutil.copy2(config_path, backup_path)
    logger.info(f"已创建配置备份: {backup_path}")
    return str(backup_path)


def save_bot_config(config: BotConfigRequest) -> None:
    """保存机器人配置"""
    template_path = CONFIG_ROOT.parent / "template" / "bot_config_template.toml"
    
    if BOT_CONFIG_PATH.exists():
        # 已存在配置文件，更新现有配置
        create_backup(BOT_CONFIG_PATH)
        with open(BOT_CONFIG_PATH, "r", encoding="utf-8") as f:
            raw_content = f.read()
        doc = tomlkit.parse(raw_content)
    else:
        # 配置文件不存在，从模板创建
        logger.info("配置文件不存在，从模板创建")
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                doc = tomlkit.load(f)
        else:
            logger.warning("模板文件不存在，创建空配置")
            doc = tomlkit.document()
    
    # 更新配置
    logger.debug(f"开始更新配置，bot section 存在: {'bot' in doc}")
    if "bot" not in doc:
        logger.info("创建新的 bot section")
        doc["bot"] = tomlkit.table()
    
    # 直接通过 doc 更新，避免类型问题
    doc["bot"]["qq_account"] = config.qq_account
    doc["bot"]["nickname"] = config.nickname
    doc["bot"]["alias_names"] = config.alias_names
    
    logger.debug(f"personality section 存在: {'personality' in doc}")
    if "personality" not in doc:
        logger.info("创建新的 personality section")
        doc["personality"] = tomlkit.table()
    
    # 直接通过 doc 更新
    doc["personality"]["personality_core"] = config.personality_core
    doc["personality"]["identity"] = config.identity
    doc["personality"]["reply_style"] = config.reply_style
    logger.debug("已更新 personality section")
    
    # 更新主人用户配置
    if config.master_users:
        logger.debug(f"开始更新主人用户配置，共 {len(config.master_users)} 个用户")
        if "security" not in doc:
            logger.info("创建新的 security section")
            doc["security"] = tomlkit.table()
        doc["security"]["master_users"] = config.master_users
    
    output_content = tomlkit.dumps(doc)
    with open(BOT_CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(output_content)
    
    logger.info("✓ 机器人配置已成功保存")


def save_model_config(config: ModelConfigRequest) -> None:
    """保存模型配置"""
    
    
    if MODEL_CONFIG_PATH.exists():
        logger.info("模型配置文件已存在，更新现有配置")
        create_backup(MODEL_CONFIG_PATH)
        with open(MODEL_CONFIG_PATH, "r", encoding="utf-8") as f:
            raw_content = f.read()
        doc = tomlkit.parse(raw_content)
        logger.debug("已读取现有模型配置")
    
    # 查找或创建 SiliconFlow provider
    providers = doc.get("api_providers", [])
    siliconflow_provider = None
    
    for i, provider in enumerate(providers):
        provider_name = provider.get("name")
        logger.debug(f"检查 provider[{i}]: {provider_name}")
        if provider_name == config.provider_name:
            siliconflow_provider = provider
            break
    
    if siliconflow_provider is None:
        # 创建新的provider
        logger.info(f"创建新的 provider: {config.provider_name}")
        siliconflow_provider = {
            "name": config.provider_name,
            "base_url": config.base_url,
            "api_key": config.api_key,
            "client_type": "openai",
            "max_retry": 2,
            "timeout": 30,
            "retry_interval": 10
        }
        providers.append(siliconflow_provider)
    else:
        # 更新已有provider
        logger.debug(f"更新已存在的 provider: {config.provider_name}")
        logger.debug(f"旧 API key 前缀: {str(siliconflow_provider.get('api_key', ''))[:10]}...")
        siliconflow_provider["api_key"] = config.api_key
        siliconflow_provider["base_url"] = config.base_url
        logger.debug(f"新 API key 前缀: {config.api_key[:10]}...")
    
    doc["api_providers"] = providers
    
    # 保存
    logger.debug(f"保存模型配置到文件: {MODEL_CONFIG_PATH}")
    output_content = tomlkit.dumps(doc)
    with open(MODEL_CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(output_content)
    
    logger.info("✓ 模型配置已成功保存")


def save_git_config(config: GitConfigRequest) -> None:
    """保存Git配置到 BackendStorage"""
    logger.info(f"开始保存 Git 配置: {config.git_path}")
    
    try:
        # 使用 BackendStorage 保存 Git 路径
        BackendStorage.set_git_path(config.git_path)
        # 设置来源为自定义
        BackendStorage.set_git_source("custom")
        logger.debug(f"已通过 BackendStorage 设置 git_path: {config.git_path}")
        logger.info("✓ Git 配置已成功保存到 BackendStorage")
    except Exception as e:
        logger.error(f"保存 Git 配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


def mark_as_initialized() -> None:
    """标记初始化完成"""
    BackendStorage.set(INIT_STATUS_KEY, True)
    logger.info("已通过 BackendStorage 标记初始化完成")


# ==================== HTTP路由组件 ====================

class InitializationRouter(BaseRouterComponent):
    """
    初始化系统路由组件
    
    提供首次配置向导的后端接口：
    - GET /status: 获取初始化状态
    - POST /bot-config: 保存机器人配置
    - POST /model-config: 保存模型配置
    - POST /git-config: 保存Git配置
    - POST /complete: 完成初始化
    - POST /validate-api-key: 验证API密钥
    - GET /detect-git: 自动检测Git路径
    """
    
    component_name = "initialization"
    component_description = "初始化系统接口"
    
    def register_endpoints(self) -> None:
        """注册所有HTTP端点"""
        
        @self.router.get("/status", summary="获取初始化状态", response_model=InitStatusResponse)
        def get_init_status(_=VerifiedDep):
            """
            检查系统初始化状态
            
            返回：
            - is_initialized: 是否已完成初始化
            - bot_config_exists: bot_config.toml是否存在
            - model_config_exists: model_config.toml是否存在
            - has_api_key: 是否配置了API密钥
            - has_git_path: 是否配置了Git路径
            """
            try:
                # 从 BackendStorage 检查初始化标记
                is_initialized = BackendStorage.get(INIT_STATUS_KEY, False)
                logger.debug(f"从 BackendStorage 读取初始化状态: {is_initialized}")
                
                return InitStatusResponse(
                    is_initialized=is_initialized,
                )
            
            except Exception as e:
                logger.error(f"获取初始化状态失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/bot-config", summary="获取机器人配置")
        def get_bot_config_endpoint(_=VerifiedDep):
            """
            获取现有的机器人配置
            
            返回：当前的机器人配置信息（如果配置文件存在）
            """
            try:
                if not BOT_CONFIG_PATH.exists():
                    return {"success": True, "data": None}
                
                with open(BOT_CONFIG_PATH, "r", encoding="utf-8") as f:
                    doc = tomlkit.load(f)
                
                bot_section = doc.get("bot", {})
                personality_section = doc.get("personality", {})
                security_section = doc.get("security", {})
                
                config_data = {
                    "qq_account": bot_section.get("qq_account", 0),
                    "nickname": bot_section.get("nickname", ""),
                    "alias_names": bot_section.get("alias_names", []),
                    "personality_core": personality_section.get("personality_core", ""),
                    "identity": personality_section.get("identity", ""),
                    "reply_style": personality_section.get("reply_style", ""),
                    "master_users": security_section.get("master_users", [])
                }
                
                return {"success": True, "data": config_data}
            except Exception as e:
                logger.error(f"获取机器人配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/bot-config", summary="保存机器人配置")
        def save_bot_config_endpoint(config: BotConfigRequest, _=VerifiedDep):
            """
            保存机器人配置
            
            包括：QQ账号、昵称、别名、人格、身份、回复风格
            """
            try:
                save_bot_config(config)
                return {"success": True, "message": "机器人配置已保存"}
            except Exception as e:
                logger.error(f"保存机器人配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/model-config", summary="获取模型配置")
        def get_model_config_endpoint(_=VerifiedDep):
            """
            获取现有的模型配置
            
            返回：当前的SiliconFlow配置信息（如果配置文件存在）
            """
            try:
                if not MODEL_CONFIG_PATH.exists():
                    return {"success": True, "data": None}
                
                with open(MODEL_CONFIG_PATH, "r", encoding="utf-8") as f:
                    doc = tomlkit.load(f)
                
                # 将 AoT 对象转换为普通列表
                providers = list(doc.get("api_providers", []))
                siliconflow_provider = None
                
                for provider in providers:
                    # 将 provider 转换为字典以便访问
                    provider_dict = dict(provider)
                    if provider_dict.get("name") == "SiliconFlow":
                        siliconflow_provider = provider_dict
                        break
                
                if siliconflow_provider:
                    api_key = siliconflow_provider.get("api_key", "")
                    if isinstance(api_key, list):
                        api_key = api_key[0] if api_key else ""
                    
                    config_data = {
                        "api_key": api_key,
                        "provider_name": siliconflow_provider.get("name", "SiliconFlow"),
                        "base_url": siliconflow_provider.get("base_url", "https://api.siliconflow.cn/v1")
                    }
                    return {"success": True, "data": config_data}
                else:
                    return {"success": True, "data": None}
            except Exception as e:
                logger.error(f"获取模型配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/model-config", summary="保存模型配置")
        def save_model_config_endpoint(config: ModelConfigRequest, _=VerifiedDep):
            """
            保存模型配置
            
            配置SiliconFlow API密钥
            """
            try:
                save_model_config(config)
                return {"success": True, "message": "模型配置已保存"}
            except Exception as e:
                logger.error(f"保存模型配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/git-config", summary="获取Git配置")
        def get_git_config_endpoint(_=VerifiedDep):
            """
            获取现有的Git配置
            
            返回：当前的Git路径配置（如果存在）
            """
            try:
                git_path = BackendStorage.get_git_path()
                
                if git_path and git_path.strip():
                    config_data = {"git_path": git_path}
                    return {"success": True, "data": config_data}
                else:
                    return {"success": True, "data": None}
            except Exception as e:
                logger.error(f"获取Git配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/git-config", summary="保存Git配置")
        def save_git_config_endpoint(config: GitConfigRequest, _=VerifiedDep):
            """
            保存Git配置
            
            配置Git可执行文件路径，用于系统更新
            """
            try:
                save_git_config(config)
                return {"success": True, "message": "Git配置已保存"}
            except Exception as e:
                logger.error(f"保存Git配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/complete", summary="完成初始化")
        def complete_initialization(_=VerifiedDep):
            """
            标记初始化流程完成
            
            创建 .initialized 标记文件
            """
            try:
                mark_as_initialized()
                return {"success": True, "message": "初始化流程已完成"}
            except Exception as e:
                logger.error(f"完成初始化失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/validate-api-key", summary="验证API密钥")
        def validate_api_key(request: ApiKeyValidationRequest, _=VerifiedDep):
            """
            验证API密钥格式
            
            简单的格式验证，不进行实际调用
            """
            try:               
                api_key = request.api_key
                # 基本格式验证
                if not api_key or len(api_key) < 10:
                    return ValidationResponse(
                        valid=False,
                        message="API密钥长度不足"
                    )
                
                if api_key.startswith("your-"):
                    return ValidationResponse(
                        valid=False,
                        message="请替换为真实的API密钥"
                    )
                
                return ValidationResponse(valid=True)
            
            except Exception as e:
                logger.error(f"验证API密钥失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/detect-git", summary="自动检测Git路径")
        def detect_git(_=VerifiedDep):
            """
            自动检测系统中的Git可执行文件路径
            
            返回：
            - found: 是否找到Git
            - path: Git路径（如果找到）
            """
            try:
                git_path = detect_git_path()
                
                if git_path:
                    return {
                        "found": True,
                        "path": git_path
                    }
                else:
                    return {
                        "found": False,
                        "path": None
                    }
            
            except Exception as e:
                logger.error(f"检测Git路径失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
