"""
日志查看器路由组件
提供日志文件读取、搜索、筛选等 API 接口
"""

import gzip
import json
import re
import tarfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from src.common.logger import get_logger
from src.common.log_broadcaster import get_log_broadcaster
from src.common.security import VerifiedDep
from src.config.config import PROJECT_ROOT
from src.plugin_system import BaseRouterComponent

logger = get_logger("WebUI.LogViewerRouter")

# 日志目录
LOG_DIR = Path(PROJECT_ROOT) / "logs"

# 从 logger.py 导入颜色和别名配置
DEFAULT_MODULE_COLORS = {}
DEFAULT_MODULE_ALIASES = {}
try:
    from src.common.logger import (
        DEFAULT_MODULE_ALIASES,
        DEFAULT_MODULE_COLORS,
    )
except ImportError:
    pass


# ==================== 请求/响应模型 ====================


@dataclass
class LogEntry:
    """日志条目"""

    timestamp: str
    level: str
    logger_name: str
    event: str
    color: Optional[str] = None
    alias: Optional[str] = None
    extra: Optional[dict] = None
    line_number: int = 0
    file_name: str = ""


class LogFileInfo(BaseModel):
    """日志文件信息"""

    name: str
    size: int
    size_human: str
    mtime: float
    mtime_human: str
    compressed: bool


class LogFilesResponse(BaseModel):
    """日志文件列表响应"""

    success: bool
    files: list[LogFileInfo]


class LogEntryResponse(BaseModel):
    """日志条目响应"""

    timestamp: str
    level: str
    logger_name: str
    event: str
    color: Optional[str] = None
    alias: Optional[str] = None
    extra: Optional[dict] = None
    line_number: int
    file_name: str


class LogSearchResponse(BaseModel):
    """日志搜索响应"""

    success: bool
    entries: list[LogEntryResponse]
    total: int
    offset: int
    limit: int


class LoggerInfo(BaseModel):
    """Logger 信息"""

    name: str
    alias: str
    color: str


class LogStatsResponse(BaseModel):
    """日志统计响应"""

    success: bool
    total: int
    by_level: dict[str, int]
    by_logger: dict[str, int]


class LogLoggersResponse(BaseModel):
    """Logger 列表响应"""

    success: bool
    loggers: list[LoggerInfo]


# ==================== 核心工具类 ====================


class LogReader:
    """日志文件读取器"""

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir

    def get_log_files(self) -> list[dict[str, Any]]:
        """获取所有日志文件列表"""
        files = []
        if not self.log_dir.exists():
            return files

        for f in sorted(self.log_dir.glob("app_*.log.jsonl*"), reverse=True):
            try:
                stat = f.stat()
                is_compressed = f.suffix == ".gz" or ".tar.gz" in f.name
                files.append(
                    {
                        "name": f.name,
                        "size": stat.st_size,
                        "size_human": self._human_size(stat.st_size),
                        "mtime": stat.st_mtime,
                        "mtime_human": datetime.fromtimestamp(stat.st_mtime).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "compressed": is_compressed,
                    }
                )
            except OSError:
                continue
        return files

    def _human_size(self, size: int) -> str:
        """转换为人类可读的文件大小"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def read_log_file(self, filename: str) -> list[LogEntry]:
        """读取日志文件内容"""
        filepath = self.log_dir / filename
        if not filepath.exists():
            return []

        entries = []
        try:
            # 处理压缩文件
            if ".tar.gz" in filename:
                entries = self._read_tar_gz(filepath)
            elif filename.endswith(".gz"):
                entries = self._read_gzip(filepath)
            else:
                entries = self._read_plain(filepath)
        except Exception as e:
            logger.error(f"读取日志文件 {filename} 时出错: {e}")

        return entries

    def _read_plain(self, filepath: Path) -> list[LogEntry]:
        """读取普通日志文件"""
        entries = []
        with open(filepath, encoding="utf-8", errors="replace") as f:
            for line_num, line in enumerate(f, 1):
                entry = self._parse_line(line, line_num, filepath.name)
                if entry:
                    entries.append(entry)
        return entries

    def _read_gzip(self, filepath: Path) -> list[LogEntry]:
        """读取 gzip 压缩的日志文件"""
        entries = []
        with gzip.open(filepath, "rt", encoding="utf-8", errors="replace") as f:
            for line_num, line in enumerate(f, 1):
                entry = self._parse_line(line, line_num, filepath.name)
                if entry:
                    entries.append(entry)
        return entries

    def _read_tar_gz(self, filepath: Path) -> list[LogEntry]:
        """读取 tar.gz 压缩的日志文件"""
        entries = []
        try:
            with tarfile.open(filepath, "r:gz") as tar:
                for member in tar.getmembers():
                    if member.isfile():
                        f = tar.extractfile(member)
                        if f:
                            content = f.read().decode("utf-8", errors="replace")
                            for line_num, line in enumerate(content.splitlines(), 1):
                                entry = self._parse_line(line, line_num, filepath.name)
                                if entry:
                                    entries.append(entry)
        except Exception as e:
            logger.error(f"读取 tar.gz 文件 {filepath} 时出错: {e}")
        return entries

    def _parse_line(
        self, line: str, line_num: int, filename: str
    ) -> Optional[LogEntry]:
        """解析单行日志"""
        line = line.strip()
        if not line:
            return None

        try:
            data = json.loads(line)
            logger_name = data.get("logger_name", "unknown")

            # 获取颜色和别名（优先使用日志中的，否则使用默认配置）
            color = data.get("color") or DEFAULT_MODULE_COLORS.get(logger_name)
            alias = data.get("alias") or DEFAULT_MODULE_ALIASES.get(logger_name)

            # 提取额外字段
            extra = {
                k: v
                for k, v in data.items()
                if k
                not in (
                    "timestamp",
                    "level",
                    "logger_name",
                    "event",
                    "color",
                    "alias",
                )
            }

            return LogEntry(
                timestamp=data.get("timestamp", ""),
                level=data.get("level", "info"),
                logger_name=logger_name,
                event=data.get("event", ""),
                color=color,
                alias=alias,
                extra=extra if extra else None,
                line_number=line_num,
                file_name=filename,
            )
        except json.JSONDecodeError:
            # 非 JSON 格式的行，尝试作为纯文本处理
            return LogEntry(
                timestamp="",
                level="info",
                logger_name="raw",
                event=line,
                line_number=line_num,
                file_name=filename,
            )

    def search_logs(
        self,
        filename: str,
        query: str = "",
        level: str = "",
        logger_name: str = "",
        start_time: str = "",
        end_time: str = "",
        limit: int = 1000,
        offset: int = 0,
        regex: bool = False,
    ) -> tuple[list[LogEntry], int]:
        """搜索和筛选日志"""
        entries = self.read_log_file(filename)

        # 如果没有筛选条件，直接返回分页结果
        if (
            not query
            and not level
            and not logger_name
            and not start_time
            and not end_time
        ):
            total = len(entries)
            return entries[offset : offset + limit], total

        # 编译正则表达式（如果需要）
        query_pattern = None
        query_lower = ""
        if query:
            if regex:
                try:
                    query_pattern = re.compile(query, re.IGNORECASE)
                except re.error:
                    query_pattern = None
            else:
                query_lower = query.lower()

        filtered = []
        for entry in entries:
            # 日志级别筛选
            if level and entry.level.lower() != level.lower():
                continue

            # Logger 名称筛选
            if logger_name and entry.logger_name.lower() != logger_name.lower():
                continue

            # 时间范围筛选
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue

            # 关键词搜索
            if query:
                if query_pattern:
                    if not (
                        query_pattern.search(entry.event)
                        or query_pattern.search(entry.logger_name)
                        or (entry.alias and query_pattern.search(entry.alias))
                    ):
                        continue
                else:
                    search_text = (
                        f"{entry.event} {entry.logger_name} {entry.alias or ''}".lower()
                    )
                    if query_lower not in search_text:
                        continue

            filtered.append(entry)

        total = len(filtered)
        return filtered[offset : offset + limit], total

    def get_loggers(self, filename: str) -> list[dict[str, str]]:
        """获取日志文件中的所有 logger"""
        entries = self.read_log_file(filename)
        loggers = {}
        for entry in entries:
            if entry.logger_name not in loggers:
                loggers[entry.logger_name] = {
                    "name": entry.logger_name,
                    "alias": entry.alias
                    or DEFAULT_MODULE_ALIASES.get(entry.logger_name, ""),
                    "color": entry.color
                    or DEFAULT_MODULE_COLORS.get(entry.logger_name, ""),
                }
        return sorted(loggers.values(), key=lambda x: x["name"])

    def get_stats(self, filename: str) -> dict[str, Any]:
        """获取日志统计信息"""
        entries = self.read_log_file(filename)

        level_counts = defaultdict(int)
        logger_counts = defaultdict(int)

        for entry in entries:
            level_counts[entry.level] += 1
            logger_counts[entry.logger_name] += 1

        return {
            "total": len(entries),
            "by_level": dict(level_counts),
            "by_logger": dict(sorted(logger_counts.items(), key=lambda x: -x[1])[:20]),
        }


# ==================== 路由组件 ====================


class LogViewerRouterComponent(BaseRouterComponent):
    """日志查看器路由组件"""

    component_name = "log_viewer"
    component_description = "日志查看器接口"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_reader = LogReader(LOG_DIR)

    def register_endpoints(self) -> None:
        """注册所有 HTTP 端点"""

        @self.router.get("/files", response_model=LogFilesResponse)
        async def get_log_files(_=VerifiedDep):
            """获取所有日志文件列表"""
            try:
                files = self.log_reader.get_log_files()
                return LogFilesResponse(success=True, files=files)
            except Exception as e:
                logger.error(f"获取日志文件列表失败: {e}")
                return LogFilesResponse(success=False, files=[])

        @self.router.get("/search", response_model=LogSearchResponse)
        async def search_logs(
            filename: str = Query(..., description="日志文件名"),
            query: str = Query("", description="搜索关键词"),
            level: str = Query("", description="日志级别"),
            logger_name: str = Query("", description="Logger 名称"),
            start_time: str = Query("", description="开始时间"),
            end_time: str = Query("", description="结束时间"),
            limit: int = Query(100, ge=1, le=1000, description="每页数量"),
            offset: int = Query(0, ge=0, description="偏移量"),
            regex: bool = Query(False, description="是否使用正则表达式"),
            _=VerifiedDep,
        ):
            """搜索和筛选日志"""
            try:
                entries, total = self.log_reader.search_logs(
                    filename=filename,
                    query=query,
                    level=level,
                    logger_name=logger_name,
                    start_time=start_time,
                    end_time=end_time,
                    limit=limit,
                    offset=offset,
                    regex=regex,
                )

                # 转换为响应模型
                entry_responses = [
                    LogEntryResponse(
                        timestamp=entry.timestamp,
                        level=entry.level,
                        logger_name=entry.logger_name,
                        event=entry.event,
                        color=entry.color,
                        alias=entry.alias,
                        extra=entry.extra,
                        line_number=entry.line_number,
                        file_name=entry.file_name,
                    )
                    for entry in entries
                ]

                return LogSearchResponse(
                    success=True,
                    entries=entry_responses,
                    total=total,
                    offset=offset,
                    limit=limit,
                )
            except Exception as e:
                logger.error(f"搜索日志失败: {e}")
                return LogSearchResponse(
                    success=False, entries=[], total=0, offset=0, limit=limit
                )

        @self.router.get("/loggers", response_model=LogLoggersResponse)
        async def get_loggers(
            filename: str = Query(..., description="日志文件名"), _=VerifiedDep
        ):
            """获取日志文件中的所有 logger"""
            try:
                loggers = self.log_reader.get_loggers(filename)
                return LogLoggersResponse(success=True, loggers=loggers)
            except Exception as e:
                logger.error(f"获取 logger 列表失败: {e}")
                return LogLoggersResponse(success=False, loggers=[])

        @self.router.get("/stats", response_model=LogStatsResponse)
        async def get_stats(
            filename: str = Query(..., description="日志文件名"), _=VerifiedDep
        ):
            """获取日志统计信息"""
            try:
                stats = self.log_reader.get_stats(filename)
                return LogStatsResponse(success=True, **stats)
            except Exception as e:
                logger.error(f"获取日志统计失败: {e}")
                return LogStatsResponse(
                    success=False, total=0, by_level={}, by_logger={}
                )

        @self.router.websocket("/realtime")
        async def websocket_realtime_logs(websocket: WebSocket):
            """WebSocket端点,用于实时推送日志"""
            await websocket.accept()
            logger.info("WebSocket客户端已连接")

            # 获取日志广播器
            broadcaster = get_log_broadcaster()

            # 定义日志回调函数
            async def send_log(log_record: dict[str, Any]):
                try:
                    await websocket.send_json(log_record)
                except Exception as e:
                    logger.debug(f"发送日志到WebSocket失败: {e}")

            # 订阅日志
            await broadcaster.subscribe(send_log)

            try:
                # 发送历史日志
                recent_logs = broadcaster.get_recent_logs(limit=100)
                for log in recent_logs:
                    try:
                        await websocket.send_json(log)
                    except Exception:
                        break

                # 保持连接,等待客户端消息或断开
                while True:
                    try:
                        # 接收客户端消息(用于心跳或控制命令)
                        data = await websocket.receive_text()
                        # 可以在这里处理客户端发送的控制命令
                        if data == "ping":
                            await websocket.send_text("pong")
                    except WebSocketDisconnect:
                        logger.info("WebSocket客户端已断开")
                        break
                    except Exception as e:
                        logger.error(f"WebSocket错误: {e}")
                        break
            finally:
                # 取消订阅
                await broadcaster.unsubscribe(send_log)
