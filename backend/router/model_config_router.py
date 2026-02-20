"""模型配置管理路由组件

提供 model.toml 配置文件的 CRUD 管理接口，包括：
- API 提供商管理
- 模型信息管理
- 任务配置管理
- 原始 TOML 读写
- 配置备份与恢复
"""

import shutil
import datetime
from typing import Any, Literal
from pathlib import Path

import tomllib
from fastapi import HTTPException
from pydantic import BaseModel

from src.kernel.logger import get_logger
from src.core.components.base.router import BaseRouter
from src.core.utils.security import VerifiedDep
from src.kernel.config.core import _render_toml_with_signature
from src.core.config import get_model_config

logger = get_logger(name="ModelConfigRouter", color="magenta")

MODEL_CONFIG_PATH = Path("config/model.toml")
BACKUP_DIR = Path("config/backups")


# ==================== Pydantic API Models ====================


class APIProviderData(BaseModel):
    """API 提供商数据"""
    name: str
    base_url: str
    api_key: str | list[str]
    client_type: Literal["openai", "gemini", "aiohttp_gemini", "bedrock"] = "openai"
    max_retry: int = 3
    timeout: int = 30
    retry_interval: int = 10


class ModelInfoData(BaseModel):
    """模型信息数据"""
    name: str
    model_identifier: str
    api_provider: str
    price_in: float = 0.0
    price_out: float = 0.0
    force_stream_mode: bool = False
    max_context: int = 32768
    tool_call_compat: bool = False
    extra_params: dict[str, Any] = {}
    anti_truncation: bool = False


class TaskConfigData(BaseModel):
    """任务配置数据"""
    model_list: list[str] = []
    max_tokens: int = 800
    temperature: float = 0.7
    concurrency_count: int = 1
    embedding_dimension: int | None = None


class ModelTasksData(BaseModel):
    """模型任务配置数据（动态字段）"""
    model_config = {"extra": "allow"}   # 允许额外字段，兼容自定义任务

    utils: TaskConfigData | None = None
    utils_small: TaskConfigData | None = None
    actor: TaskConfigData | None = None
    sub_actor: TaskConfigData | None = None
    vlm: TaskConfigData | None = None
    voice: TaskConfigData | None = None
    video: TaskConfigData | None = None
    tool_use: TaskConfigData | None = None
    embedding: TaskConfigData | None = None


class ModelConfigData(BaseModel):
    """完整模型配置数据（用于 GET 返回）"""
    api_providers: list[APIProviderData]
    models: list[ModelInfoData]
    model_tasks: ModelTasksData


class ModelConfigUpdateRequest(BaseModel):
    """模型配置更新请求（完整替换）"""
    api_providers: list[APIProviderData]
    models: list[ModelInfoData]
    model_tasks: ModelTasksData


class ModelConfigRawResponse(BaseModel):
    """原始 TOML 内容响应"""
    success: bool
    content: str
    path: str


class ModelConfigSaveRawRequest(BaseModel):
    """原始 TOML 保存请求"""
    content: str


class ModelConfigBackupInfo(BaseModel):
    """备份信息"""
    name: str
    path: str
    created_at: str
    size: int


class ModelConfigBackupsResponse(BaseModel):
    """备份列表响应"""
    success: bool
    backups: list[ModelConfigBackupInfo]


class ModelConfigUpdateResponse(BaseModel):
    """更新响应"""
    success: bool
    message: str


class TaskSchemaItem(BaseModel):
    """单个任务的 Schema 信息"""
    key: str            # 任务键名，如 "utils"
    name: str           # 中文名称
    description: str    # 中文描述
    category: str       # 分类：core / media / memory / other


class TasksSchemaResponse(BaseModel):
    """任务 Schema 响应"""
    tasks: list[TaskSchemaItem]


class ModelTestRequest(BaseModel):
    """模型测试请求"""
    model_name: str


class ModelTestResponse(BaseModel):
    """模型测试响应"""
    success: bool
    connected: bool
    model_name: str
    response_time: float | None = None  # 响应时间（秒）
    response_text: str | None = None
    error: str | None = None


# ==================== 任务中文映射 ====================

# 任务中文名称和描述映射（key 为 ModelTasksSection 的字段名）
_TASK_META: dict[str, tuple[str, str, str]] = {
    # key: (中文名, 描述, 分类)
    "utils":                    ("通用工具模型",   "用于表情包模块、取名模块、关系模块等，MoFox 必需的模型",              "core"),
    "utils_small":              ("轻量工具模型",   "消耗量较大的组件使用，建议使用速度较快的小模型",                      "core"),
    "actor":                    ("动作器模型",     "负责决策机器人下一步动作的核心模型",                                  "core"),
    "sub_actor":                ("副动作器模型",   "辅助动作器，用于并行或补充决策",                                      "core"),
    "tool_use":                 ("工具调用模型",   "需要支持 Function Call / Tool Use 的模型",                            "core"),
    "vlm":                      ("图像识别模型",   "用于图像内容识别的视觉语言模型",                                      "media"),
    "voice":                    ("语音识别模型",   "用于语音消息识别的模型",                                              "media"),
    "video":                    ("视频分析模型",   "用于视频内容分析的模型",                                              "media"),
    "embedding":                ("嵌入模型",       "用于文本向量化的嵌入模型",                                            "memory"),
}

# 若从 model_tasks 配置中发现不在映射表内的任务键，则使用此兜底逻辑
def _task_meta_fallback(key: str) -> tuple[str, str, str]:
    return (key.replace("_", " ").title(), f"任务：{key}", "other")


def _build_tasks_schema() -> TasksSchemaResponse:
    """根据 ModelTasksSection 字段定义 + 中文映射生成任务 Schema"""
    from src.core.config.model_config import ModelTasksSection

    items: list[TaskSchemaItem] = []
    seen: set[str] = set()

    # 按 model_fields 顺序输出（保证稳定）
    for field_name in ModelTasksSection.model_fields:
        seen.add(field_name)
        name, desc, cat = _TASK_META.get(field_name, _task_meta_fallback(field_name))
        items.append(TaskSchemaItem(key=field_name, name=name, description=desc, category=cat))

    return TasksSchemaResponse(tasks=items)


# ==================== 内部工具函数 ====================


def _create_backup() -> Path | None:
    """创建当前 model.toml 的备份，最多保留 20 份"""
    if not MODEL_CONFIG_PATH.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"model_{ts}.toml"
    shutil.copy2(MODEL_CONFIG_PATH, backup_file)

    # 只保留最新的 20 个备份
    all_backups = sorted(
        BACKUP_DIR.glob("model_*.toml"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old in all_backups[20:]:
        try:
            old.unlink()
        except Exception:
            pass
    return backup_file


def _list_backups() -> list[ModelConfigBackupInfo]:
    """列出所有 model_*.toml 备份文件"""
    if not BACKUP_DIR.exists():
        return []
    result = []
    for f in sorted(
        BACKUP_DIR.glob("model_*.toml"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ):
        stat = f.stat()
        result.append(
            ModelConfigBackupInfo(
                name=f.name,
                path=str(f),
                created_at=datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                size=stat.st_size,
            )
        )
    return result


def _load_raw_toml() -> dict[str, Any]:
    """读取并解析 model.toml"""
    if not MODEL_CONFIG_PATH.exists():
        raise FileNotFoundError(f"配置文件不存在: {MODEL_CONFIG_PATH}")
    with open(MODEL_CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def _save_raw_toml(data: dict[str, Any]) -> None:
    """将数据写回 model.toml（使用 kernel 的带注释渲染器）"""
    from src.core.config.model_config import ModelConfig
    MODEL_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    content = _render_toml_with_signature(ModelConfig, data)
    MODEL_CONFIG_PATH.write_text(content, encoding="utf-8")


def _toml_dict_to_model_config_data(raw: dict[str, Any]) -> ModelConfigData:
    """将原始 TOML 字典转换为 ModelConfigData"""
    providers = [APIProviderData(**p) for p in raw.get("api_providers", [])]
    models = [ModelInfoData(**m) for m in raw.get("models", [])]

    raw_tasks = raw.get("model_tasks", {})
    tasks_kwargs: dict[str, Any] = {}
    for field_name, task_raw in raw_tasks.items():
        if isinstance(task_raw, dict):
            tasks_kwargs[field_name] = TaskConfigData(**task_raw)
    model_tasks = ModelTasksData(**tasks_kwargs)

    return ModelConfigData(
        api_providers=providers,
        models=models,
        model_tasks=model_tasks,
    )


def _model_config_data_to_toml_dict(data: ModelConfigUpdateRequest) -> dict[str, Any]:
    """将 ModelConfigUpdateRequest 转换为可写入 TOML 的字典"""
    result: dict[str, Any] = {}

    # api_providers
    result["api_providers"] = [p.model_dump() for p in data.api_providers]

    # models
    result["models"] = [m.model_dump() for m in data.models]

    # model_tasks - 将所有非 None 的任务都写入（包括通过 extra="allow" 传入的动态字段）
    tasks_dict: dict[str, Any] = {}
    # 遍历 model_dump 的结果，包含所有字段（含 extra fields）
    for field_name, task_data in data.model_tasks.model_dump().items():
        if task_data is not None:
            tasks_dict[field_name] = task_data
    result["model_tasks"] = tasks_dict

    return result


def _reload_model_config() -> None:
    """重新加载全局模型配置（热更新）"""
    try:
        from src.core.config.model_config import init_model_config
        init_model_config(str(MODEL_CONFIG_PATH))
    except Exception as e:
        logger.warning(f"热重载模型配置失败（不影响文件已保存）: {e}")


# ==================== Router ====================


class ModelConfigRouter(BaseRouter):
    """模型配置管理路由组件

    提供以下 API 端点：
    - GET  /config          获取当前模型配置（结构化）
    - PUT  /config          保存完整模型配置（结构化）
    - GET  /config/raw      获取原始 TOML 文本
    - POST /config/raw      保存原始 TOML 文本
    - GET  /config/backups  获取备份列表
    - POST /config/restore/{backup_name}  从备份恢复
    """

    router_name = "ModelConfigRouter"
    router_description = "模型配置管理接口"

    custom_route_path = "/webui/api/model-config"
    cors_origins = ["*"]

    def register_endpoints(self) -> None:
        """注册所有 HTTP 端点"""

        # -------- GET /tasks-schema --------
        @self.app.get("/tasks-schema", summary="获取任务 Schema（中文名称和描述）", response_model=TasksSchemaResponse)
        async def get_tasks_schema(_=VerifiedDep):
            """返回所有预定义任务的中文名称、描述和分类，供前端展示"""
            try:
                return _build_tasks_schema()
            except Exception as e:
                logger.error(f"获取任务 Schema 失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # -------- GET /config --------
        @self.app.get("/config", summary="获取当前模型配置", response_model=ModelConfigData)
        async def get_model_config_endpoint(_=VerifiedDep):
            """返回解析后的结构化模型配置"""
            try:
                raw = _load_raw_toml()
                return _toml_dict_to_model_config_data(raw)
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail="配置文件不存在")
            except Exception as e:
                logger.error(f"读取模型配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # -------- PUT /config --------
        @self.app.put("/config", summary="保存完整模型配置", response_model=ModelConfigUpdateResponse)
        async def update_model_config_endpoint(request: ModelConfigUpdateRequest, _=VerifiedDep):
            """覆盖写入完整模型配置，先创建备份"""
            try:
                _create_backup()
                toml_dict = _model_config_data_to_toml_dict(request)
                _save_raw_toml(toml_dict)
                _reload_model_config()
                return ModelConfigUpdateResponse(success=True, message="模型配置已保存")
            except Exception as e:
                logger.error(f"保存模型配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # -------- GET /config/raw --------
        @self.app.get("/config/raw", summary="获取原始 TOML 内容", response_model=ModelConfigRawResponse)
        async def get_config_raw(_=VerifiedDep):
            """获取 config/model.toml 的原始文本内容"""
            try:
                if not MODEL_CONFIG_PATH.exists():
                    raise HTTPException(status_code=404, detail="配置文件不存在")
                content = MODEL_CONFIG_PATH.read_text(encoding="utf-8")
                return ModelConfigRawResponse(
                    success=True,
                    content=content,
                    path=str(MODEL_CONFIG_PATH),
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"读取原始模型配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # -------- POST /config/raw --------
        @self.app.post("/config/raw", summary="保存原始 TOML 内容")
        async def save_config_raw(request: ModelConfigSaveRawRequest, _=VerifiedDep):
            """直接保存原始 TOML 文本到 config/model.toml，先验证语法"""
            try:
                try:
                    tomllib.loads(request.content)
                except tomllib.TOMLDecodeError as e:
                    raise HTTPException(status_code=400, detail=f"TOML 语法错误: {e}")
                _create_backup()
                MODEL_CONFIG_PATH.write_text(request.content, encoding="utf-8")
                _reload_model_config()
                return {"success": True, "message": "模型配置已保存"}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"保存原始模型配置失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # -------- GET /config/backups --------
        @self.app.get("/config/backups", summary="获取备份列表", response_model=ModelConfigBackupsResponse)
        async def get_backups(_=VerifiedDep):
            """获取 model.toml 的所有备份文件列表"""
            try:
                backups = _list_backups()
                return ModelConfigBackupsResponse(success=True, backups=backups)
            except Exception as e:
                logger.error(f"获取备份列表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # -------- POST /config/restore/{backup_name} --------
        @self.app.post("/config/restore/{backup_name}", summary="从备份恢复")
        async def restore_backup(backup_name: str, _=VerifiedDep):
            """从指定备份文件恢复模型配置"""
            try:
                backup_file = BACKUP_DIR / backup_name
                if not backup_file.exists():
                    raise HTTPException(status_code=404, detail=f"备份文件不存在: {backup_name}")
                _create_backup()
                shutil.copy2(backup_file, MODEL_CONFIG_PATH)
                _reload_model_config()
                return {"success": True, "message": f"已从 {backup_name} 恢复模型配置"}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"恢复备份失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # -------- POST /test --------
        @self.app.post("/test", summary="测试模型连通性", response_model=ModelTestResponse)
        async def test_model_connection(request: ModelTestRequest, _=VerifiedDep):
            """测试指定模型的 API 连通性
            
            发送简单请求测试模型是否可用。
            """
            import time
            from src.kernel.llm import LLMRequest
            from src.kernel.llm.payload import LLMPayload, Text
            from src.kernel.llm.roles import ROLE
            
            model_name = request.model_name
            
            try:
                # 从配置中获取模型 ModelSet
                config = get_model_config()
                
                try:
                    # 使用 get_model_set_by_name 直接获取配置好的 ModelSet
                    # 测试时使用较短的超时和单次重试
                    model_set = config.get_model_set_by_name(
                        model_name,
                        max_tokens=50,  # 测试只需要简短响应
                    )
                except KeyError as e:
                    return ModelTestResponse(
                        success=True,
                        connected=False,
                        model_name=model_name,
                        error=str(e)
                    )
                
                # 创建 LLM 请求
                llm_request = LLMRequest(
                    model_set=model_set,  # type: ignore[arg-type]
                    request_name=f"test_{model_name}",
                    enable_metrics=False,  # 测试请求不记录指标
                )
                
                # 添加简单的测试消息
                test_payload = LLMPayload(ROLE.USER, [Text("Hi")])
                llm_request.add_payload(test_payload)
                
                # 发送请求并计时
                start_time = time.time()
                response = await llm_request.send(auto_append_response=False, stream=False)
                response_text = await response
                elapsed = time.time() - start_time
                
                return ModelTestResponse(
                    success=True,
                    connected=True,
                    model_name=model_name,
                    response_time=round(elapsed, 3),  # 秒（保留 3 位小数）
                    response_text=str(response_text)[:200] if response_text else None,
                )
                
            except Exception as e:
                import traceback
                logger.error(f"测试模型 {model_name} 失败: {e}\n{traceback.format_exc()}")
                return ModelTestResponse(
                    success=True,
                    connected=False,
                    model_name=model_name,
                    error=str(e)
                )

    async def startup(self) -> None:
        logger.info(f"Model Config 路由已启动，路径: {self.custom_route_path}")

    async def shutdown(self) -> None:
        logger.info("Model Config 路由已关闭")
