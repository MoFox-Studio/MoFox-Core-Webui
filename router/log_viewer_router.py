"""日志查看器路由组件

提供历史日志文件的查看、搜索和过滤 API 接口。

日志文件格式（文本格式）:
    [HH:MM:SS] display_name | LEVEL | message

支持功能:
- 获取日志文件列表
- 搜索/过滤日志条目（级别、模块名、关键词、正则、时间范围）
- 分页查询
- 获取文件中的 logger 列表
- 获取日志统计信息
"""

import gzip
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, Query
from pydantic import BaseModel

from src.kernel.logger import get_logger
from src.core.components.base.router import BaseRouter
from src.core.utils.security import VerifiedDep

logger = get_logger(name="LogViewer", color="#7DCFFF")

# 日志目录（相对于项目根目录）
_LOG_DIR = Path("logs")

# 日志行格式正则：[HH:MM:SS] display | LEVEL | message
_LOG_LINE_RE = re.compile(
    r"^\[(\d{2}:\d{2}:\d{2})\]\s+(.+?)\s+\|\s+(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+\|\s+(.*)$"
)

# 允许的日志级别
_VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


# ==================== 数据模型 ====================


class LogFileInfo(BaseModel):
    """日志文件信息"""
    name: str
    size: int
    size_human: str
    mtime: float
    mtime_human: str
    compressed: bool


class LogEntry(BaseModel):
    """单条日志条目"""
    timestamp: str          # HH:MM:SS 格式时间
    level: str
    logger_name: str        # display 名称（冒号前）
    logger_color: str | None = None  # Logger 颜色
    event: str              # 日志消息
    line_number: int        # 行号（1-based）
    file_name: str          # 所属文件名


class LoggerInfo(BaseModel):
    """Logger 信息"""
    display: str               # display 名称 (兼容旧字段名 name)
    name: str | None = None    # 内部名称
    color: str | None = None   # 颜色


class LogFilesResponse(BaseModel):
    success: bool
    files: list[LogFileInfo]


class LogSearchResponse(BaseModel):
    success: bool
    entries: list[LogEntry]
    total: int
    offset: int
    limit: int


class LogLoggersResponse(BaseModel):
    success: bool
    loggers: list[LoggerInfo]


class LogStatsResponse(BaseModel):
    success: bool
    total: int
    by_level: dict[str, int]
    by_logger: dict[str, int]


# ==================== 工具函数 ====================


def _human_size(size: int) -> str:
    """将字节数转换为人类可读的大小字符串"""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _get_log_files() -> list[Path]:
    """获取所有日志文件路径，按修改时间降序排列"""
    if not _LOG_DIR.exists():
        return []
    files = []
    for p in _LOG_DIR.iterdir():
        if p.is_file() and (p.suffix == ".log" or p.name.endswith(".log.gz")):
            files.append(p)
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def _open_log_file(file_path: Path):
    """打开日志文件（支持 gzip 压缩）"""
    if file_path.name.endswith(".gz"):
        return gzip.open(file_path, "rt", encoding="utf-8", errors="replace")
    return open(file_path, "r", encoding="utf-8", errors="replace")


def _parse_log_line(line: str, line_number: int, file_name: str) -> Optional[LogEntry]:
    """解析单行日志，返回 LogEntry 或 None（无法解析时）"""
    m = _LOG_LINE_RE.match(line.rstrip("\n"))
    if not m:
        return None
    timestamp, display, level, message = m.groups()
    return LogEntry(
        timestamp=timestamp,
        level=level.upper(),
        logger_name=display.strip(),
        event=message,
        line_number=line_number,
        file_name=file_name,
    )


def _read_all_entries(file_path: Path) -> list[LogEntry]:
    """读取文件的全部已解析日志条目"""
    entries: list[LogEntry] = []
    
    # 获取当前所有 logger 配置 (display -> color 映射)
    logger_map = {}
    try:
        from src.kernel.logger import get_all_loggers
        loggers = get_all_loggers()
        for _, log in loggers.items():
            if log.display:
                logger_map[log.display] = str(log.color)
    except Exception:
        pass

    try:
        with _open_log_file(file_path) as f:
            for line_no, line in enumerate(f, start=1):
                entry = _parse_log_line(line, line_no, file_path.name)
                if entry:
                    # 尝试注入颜色信息
                    if entry.logger_name in logger_map:
                        entry.logger_color = logger_map[entry.logger_name]
                    entries.append(entry)
    except Exception as exc:
        logger.warning(f"读取日志文件失败: {file_path.name} — {exc}")
    return entries


def _match_entry(
    entry: LogEntry,
    query: Optional[str],
    level: Optional[str],
    logger_name: Optional[str],
    start_time: Optional[str],
    end_time: Optional[str],
    regex: bool,
) -> bool:
    """判断一条日志条目是否匹配过滤条件"""
    # 级别过滤
    if level and entry.level != level.upper():
        return False

    # logger 名称过滤（模糊匹配）
    if logger_name and logger_name.lower() not in entry.logger_name.lower():
        return False

    # 时间范围过滤（HH:MM:SS 字典序比较）
    if start_time and entry.timestamp < start_time:
        return False
    if end_time and entry.timestamp > end_time:
        return False

    # 关键词/正则搜索
    if query:
        try:
            if regex:
                if not re.search(query, entry.event, re.IGNORECASE):
                    return False
            else:
                if query.lower() not in entry.event.lower():
                    return False
        except re.error:
            # 正则表达式无效时退回普通搜索
            if query.lower() not in entry.event.lower():
                return False

    return True


# ==================== 路由组件 ====================


class LogViewerRouter(BaseRouter):
    """日志查看器路由组件

    提供以下 API 端点:
    - GET /files       获取日志文件列表
    - GET /search      搜索 / 分页查询日志条目
    - GET /loggers     获取文件中出现的 logger 列表
    - GET /stats       获取日志统计信息
    """

    router_name = "LogViewer"
    router_description = "历史日志查看器接口"

    custom_route_path = "/webui/api/log_viewer"
    cors_origins = ["*"]

    def register_endpoints(self) -> None:
        """注册所有 HTTP 端点"""

        # ── GET /files ────────────────────────────────────────────────
        @self.app.get("/files", summary="获取日志文件列表", response_model=LogFilesResponse)
        async def get_log_files(_=VerifiedDep):
            """返回 logs/ 目录下所有日志文件，按最新修改时间排序。"""
            try:
                result: list[LogFileInfo] = []
                for p in _get_log_files():
                    stat = p.stat()
                    result.append(LogFileInfo(
                        name=p.name,
                        size=stat.st_size,
                        size_human=_human_size(stat.st_size),
                        mtime=stat.st_mtime,
                        mtime_human=datetime.fromtimestamp(stat.st_mtime).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        compressed=p.name.endswith(".gz"),
                    ))
                return LogFilesResponse(success=True, files=result)
            except Exception as exc:
                logger.error(f"获取日志文件列表失败: {exc}")
                return LogFilesResponse(success=False, files=[])

        # ── GET /search ───────────────────────────────────────────────
        @self.app.get("/search", summary="搜索日志条目", response_model=LogSearchResponse)
        async def search_logs(
            filename: str = Query(..., description="日志文件名"),
            query: Optional[str] = Query(None, description="关键词或正则表达式"),
            level: Optional[str] = Query(None, description="日志级别过滤"),
            logger_name: Optional[str] = Query(None, description="logger 名称过滤（模糊）"),
            start_time: Optional[str] = Query(None, description="起始时间 HH:MM:SS"),
            end_time: Optional[str] = Query(None, description="结束时间 HH:MM:SS"),
            limit: int = Query(200, ge=1, le=2000, description="每页条数"),
            offset: int = Query(0, ge=0, description="偏移量"),
            regex: bool = Query(False, description="是否使用正则搜索"),
            _=VerifiedDep,
        ):
            """按条件搜索并分页返回日志条目。"""
            try:
                file_path = _LOG_DIR / filename
                if not file_path.exists() or not file_path.is_file():
                    raise HTTPException(status_code=404, detail=f"日志文件不存在: {filename}")

                # 安全检查：不允许路径遍历
                try:
                    file_path.resolve().relative_to(_LOG_DIR.resolve())
                except ValueError:
                    raise HTTPException(status_code=403, detail="非法的文件路径")

                # 级别合法性检查
                if level and level.upper() not in _VALID_LEVELS:
                    raise HTTPException(status_code=400, detail=f"非法的日志级别: {level}")

                all_entries = _read_all_entries(file_path)

                # 过滤
                filtered = [
                    e for e in all_entries
                    if _match_entry(e, query, level, logger_name, start_time, end_time, regex)
                ]

                total = len(filtered)
                page_entries = filtered[offset: offset + limit]

                return LogSearchResponse(
                    success=True,
                    entries=page_entries,
                    total=total,
                    offset=offset,
                    limit=limit,
                )
            except HTTPException:
                raise
            except Exception as exc:
                logger.error(f"搜索日志失败: {exc}")
                return LogSearchResponse(success=False, entries=[], total=0, offset=offset, limit=limit)

        # ── GET /loggers ──────────────────────────────────────────────
        @self.app.get("/loggers", summary="获取 logger 列表", response_model=LogLoggersResponse)
        async def get_loggers(
            filename: str = Query(..., description="日志文件名"),
            _=VerifiedDep,
        ):
            """返回指定日志文件中出现的所有 logger（display）名称，附带当前运行时颜色。"""
            try:
                file_path = _LOG_DIR / filename
                if not file_path.exists():
                    raise HTTPException(status_code=404, detail=f"日志文件不存在: {filename}")

                entries = _read_all_entries(file_path)
                seen: dict[str, int] = {}
                for e in entries:
                    seen[e.logger_name] = seen.get(e.logger_name, 0) + 1

                # 获取运行时 logger 信息
                from src.kernel.logger import get_all_loggers
                runtime_loggers = get_all_loggers()
                # 建立 display -> (name, color) 映射
                display_map = {}
                for log in runtime_loggers.values():
                    if log.display:
                        display_map[log.display] = (log.name, str(log.color))

                # 按出现次数降序
                loggers_list = []
                for display_name, _ in sorted(seen.items(), key=lambda x: -x[1]):
                    name_internal = None
                    color = None
                    if display_name in display_map:
                        name_internal, color = display_map[display_name]
                    
                    loggers_list.append(LoggerInfo(
                        display=display_name,
                        name=name_internal,
                        color=color
                    ))

                return LogLoggersResponse(success=True, loggers=loggers_list)
            except HTTPException:
                raise
            except Exception as exc:
                logger.error(f"获取 logger 列表失败: {exc}")
                return LogLoggersResponse(success=False, loggers=[])

        # ── GET /stats ────────────────────────────────────────────────
        @self.app.get("/stats", summary="获取日志统计信息", response_model=LogStatsResponse)
        async def get_log_stats(
            filename: str = Query(..., description="日志文件名"),
            _=VerifiedDep,
        ):
            """返回指定日志文件的统计信息（总条数、按级别、按 logger 分组）。"""
            try:
                file_path = _LOG_DIR / filename
                if not file_path.exists():
                    raise HTTPException(status_code=404, detail=f"日志文件不存在: {filename}")

                entries = _read_all_entries(file_path)

                by_level: dict[str, int] = {}
                by_logger: dict[str, int] = {}
                for e in entries:
                    by_level[e.level] = by_level.get(e.level, 0) + 1
                    by_logger[e.logger_name] = by_logger.get(e.logger_name, 0) + 1

                return LogStatsResponse(
                    success=True,
                    total=len(entries),
                    by_level=by_level,
                    by_logger=by_logger,
                )
            except HTTPException:
                raise
            except Exception as exc:
                logger.error(f"获取日志统计信息失败: {exc}")
                return LogStatsResponse(success=False, total=0, by_level={}, by_logger={})

    async def startup(self) -> None:
        logger.info(f"LogViewer 路由已启动，路径: {self.custom_route_path}")

    async def shutdown(self) -> None:
        logger.info("LogViewer 路由已关闭")
