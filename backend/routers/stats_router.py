"""
统计数据路由组件
提供仪表盘统计数据API接口
"""

import time
from typing import Any

import psutil
from pydantic import BaseModel

from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.plugin_system import BaseRouterComponent
from src.plugin_system.apis import chat_api, plugin_info_api

logger = get_logger("WebUIAuth.StatsRouter")

# 记录启动时间
_start_time = time.time()


# ==================== 响应模型 ====================

class PluginStatsResponse(BaseModel):
    """插件统计响应"""
    loaded: int
    registered: int
    failed: int
    enabled: int
    disabled: int


class ComponentStatsResponse(BaseModel):
    """组件统计响应"""
    total: int
    enabled: int
    disabled: int
    by_type: dict[str, dict[str, int]]


class ChatStatsResponse(BaseModel):
    """聊天流统计响应"""
    total_streams: int
    group_streams: int
    private_streams: int
    qq_streams: int


class SystemStatsResponse(BaseModel):
    """系统统计响应"""
    uptime_seconds: float
    memory_usage_mb: float
    cpu_percent: float


class DashboardOverviewResponse(BaseModel):
    """仪表盘总览响应"""
    plugins: PluginStatsResponse
    components: ComponentStatsResponse
    chats: ChatStatsResponse
    system: SystemStatsResponse


class PluginDetailResponse(BaseModel):
    """插件详情响应"""
    name: str
    display_name: str
    version: str
    author: str
    enabled: bool
    components_count: int


class PluginListResponse(BaseModel):
    """插件列表响应"""
    plugins: list[PluginDetailResponse]
    total: int


# ==================== HTTP路由组件 ====================

class WebUIStatsRouter(BaseRouterComponent):
    """
    WebUI统计数据路由组件
    
    提供以下API端点：
    - GET /overview: 获取仪表盘总览数据
    - GET /plugins: 获取插件列表
    - GET /plugins/{plugin_name}: 获取插件详情
    - GET /system: 获取系统状态
    """
    
    component_name = "stats"
    component_description = "WebUI统计数据接口"
    
    def register_endpoints(self) -> None:
        """注册所有HTTP端点"""
        
        @self.router.get("/overview", summary="获取仪表盘总览数据", response_model=DashboardOverviewResponse)
        def get_dashboard_overview(_=VerifiedDep):
            """
            获取仪表盘总览统计数据
            
            返回：
            - 插件统计：已加载、已注册、失败、启用、禁用数量
            - 组件统计：总数、启用数、禁用数、按类型分组
            - 聊天流统计：总数、群聊数、私聊数
            - 系统统计：运行时间、内存使用、CPU使用率
            """
            try:
                # 获取插件和组件统计
                state_stats = plugin_info_api.get_state_statistics()
                
                # 获取聊天流统计
                chat_stats = chat_api.get_streams_summary()
                
                # 获取系统统计
                process = psutil.Process()
                memory_info = process.memory_info()
                
                return DashboardOverviewResponse(
                    plugins=PluginStatsResponse(
                        loaded=state_stats["plugins"]["loaded"],
                        registered=state_stats["plugins"]["registered"],
                        failed=state_stats["plugins"]["failed"],
                        enabled=state_stats["plugins"]["enabled"],
                        disabled=state_stats["plugins"]["disabled"],
                    ),
                    components=ComponentStatsResponse(
                        total=state_stats["components"]["total"],
                        enabled=state_stats["components"]["enabled"],
                        disabled=state_stats["components"]["disabled"],
                        by_type=state_stats["components"]["by_type"],
                    ),
                    chats=ChatStatsResponse(
                        total_streams=chat_stats["total_streams"],
                        group_streams=chat_stats["group_streams"],
                        private_streams=chat_stats["private_streams"],
                        qq_streams=chat_stats["qq_streams"],
                    ),
                    system=SystemStatsResponse(
                        uptime_seconds=time.time() - _start_time,
                        memory_usage_mb=memory_info.rss / (1024 * 1024),
                        cpu_percent=process.cpu_percent(),
                    ),
                )
            except Exception as e:
                logger.error(f"获取仪表盘数据失败: {e}")
                # 返回默认值
                return DashboardOverviewResponse(
                    plugins=PluginStatsResponse(loaded=0, registered=0, failed=0, enabled=0, disabled=0),
                    components=ComponentStatsResponse(total=0, enabled=0, disabled=0, by_type={}),
                    chats=ChatStatsResponse(total_streams=0, group_streams=0, private_streams=0, qq_streams=0),
                    system=SystemStatsResponse(uptime_seconds=0, memory_usage_mb=0, cpu_percent=0),
                )
        
        @self.router.get("/plugins", summary="获取插件列表", response_model=PluginListResponse)
        def get_plugins_list(_=VerifiedDep):
            """
            获取所有已加载插件的详细信息列表
            """
            try:
                report = plugin_info_api.get_system_report()
                plugins = []
                for name, info in report.get("plugins", {}).items():
                    plugins.append(PluginDetailResponse(
                        name=name,
                        display_name=info.get("display_name", name),
                        version=info.get("version", "unknown"),
                        author=info.get("author", "unknown"),
                        enabled=info.get("enabled", False),
                        components_count=len(info.get("components", [])),
                    ))
                return PluginListResponse(plugins=plugins, total=len(plugins))
            except Exception as e:
                logger.error(f"获取插件列表失败: {e}")
                return PluginListResponse(plugins=[], total=0)
        
        @self.router.get("/plugins/{plugin_name}", summary="获取插件详情")
        def get_plugin_detail(plugin_name: str, _=VerifiedDep):
            """
            获取指定插件的详细信息
            """
            try:
                details = plugin_info_api.get_plugin_details(plugin_name)
                if details:
                    return {"success": True, "plugin": details}
                return {"success": False, "error": f"插件 {plugin_name} 不存在"}
            except Exception as e:
                logger.error(f"获取插件详情失败: {e}")
                return {"success": False, "error": str(e)}
        
        @self.router.get("/system", summary="获取系统状态")
        def get_system_status(_=VerifiedDep):
            """
            获取系统运行状态
            """
            try:
                process = psutil.Process()
                memory_info = process.memory_info()
                
                return {
                    "uptime_seconds": time.time() - _start_time,
                    "uptime_formatted": _format_uptime(time.time() - _start_time),
                    "memory_usage_mb": round(memory_info.rss / (1024 * 1024), 2),
                    "memory_usage_formatted": _format_memory(memory_info.rss),
                    "cpu_percent": process.cpu_percent(),
                    "threads": process.num_threads(),
                }
            except Exception as e:
                logger.error(f"获取系统状态失败: {e}")
                return {
                    "uptime_seconds": 0,
                    "uptime_formatted": "0秒",
                    "memory_usage_mb": 0,
                    "memory_usage_formatted": "0 MB",
                    "cpu_percent": 0,
                    "threads": 0,
                }


def _format_uptime(seconds: float) -> str:
    """格式化运行时间"""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}天")
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分钟")
    
    return "".join(parts) if parts else "刚刚启动"


def _format_memory(bytes_value: int) -> str:
    """格式化内存大小"""
    mb = bytes_value / (1024 * 1024)
    if mb >= 1024:
        return f"{mb / 1024:.2f} GB"
    return f"{mb:.2f} MB"
