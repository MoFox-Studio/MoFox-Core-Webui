"""统计数据路由组件

提供仪表盘统计数据API接口
"""

import asyncio
import aiohttp
import psutil
import time
from datetime import datetime, timedelta
from typing import Literal, Optional

from fastapi import HTTPException
from pydantic import BaseModel

from src.kernel.logger import get_logger
from src.core.components.base.router import BaseRouter
from src.core.utils.security import VerifiedDep
from src.core.managers import get_plugin_manager, get_stream_manager
from src.core.components.registry import get_global_registry
from src.core.components.state_manager import get_global_state_manager
from src.core.components.types import ComponentState, ComponentType
from src.app.plugin_system.api import message_api

logger = get_logger(name="WebUI_Stats", color="cyan")

# 记录启动时间
_start_time = time.time()

# 初始化CPU使用率监控
try:
    _process = psutil.Process()
    _process.cpu_percent()  # 初始化调用
except Exception:
    _process = None


# ==================== 响应模型 ====================


class PluginStatsResponse(BaseModel):
    """插件统计响应"""
    loaded: int
    failed: int
    total: int


class ComponentStatsResponse(BaseModel):
    """组件统计响应"""
    total: int
    active: int
    inactive: int
    by_type: dict[str, dict[str, int]]


class SystemStatsResponse(BaseModel):
    """系统统计响应"""
    uptime_seconds: float
    memory_usage_mb: float
    total_memory_mb: float
    cpu_percent: float


class ChatStatsResponse(BaseModel):
    """聊天流统计响应"""
    total_streams: int
    active_streams: int
    private_streams: int
    group_streams: int


class DashboardOverviewResponse(BaseModel):
    """仪表盘总览响应"""
    plugins: PluginStatsResponse
    components: ComponentStatsResponse
    chats: ChatStatsResponse
    system: SystemStatsResponse


class PluginDetailResponse(BaseModel):
    """插件详情响应"""
    name: str
    version: str
    author: str
    description: str
    components_count: int


class PluginListResponse(BaseModel):
    """插件列表响应"""
    plugins: list[PluginDetailResponse]
    total: int


class PluginListItemResponse(BaseModel):
    """插件列表项响应"""
    name: str
    version: str
    author: str
    description: str
    components_count: int
    error: Optional[str] = None


class PluginsByStatusResponse(BaseModel):
    """按状态分组的插件列表响应"""
    loaded: list[PluginListItemResponse]
    failed: list[PluginListItemResponse]


class ComponentItemResponse(BaseModel):
    """组件项响应"""
    name: str
    plugin_name: str
    type: str
    state: str


class ComponentsByTypeResponse(BaseModel):
    """按类型分组的组件列表响应"""
    component_type: str
    components: list[ComponentItemResponse]
    total: int
    active: int
    inactive: int


class DailyQuoteResponse(BaseModel):
    """每日名言响应"""
    quote: str
    author: str
    category: str
    date: str


class MessageStatsDataPoint(BaseModel):
    """消息统计数据点"""
    timestamp: str
    received: int
    sent: int


class MessageStatsResponse(BaseModel):
    """消息统计响应"""
    data_points: list[MessageStatsDataPoint]
    total_received: int
    total_sent: int
    period: str


# 一言API类型映射
HITOKOTO_TYPE_MAP = {
    "a": "动画",
    "b": "漫画",
    "c": "游戏",
    "d": "文学",
    "e": "原创",
    "f": "来自网络",
    "g": "其他",
    "h": "影视",
    "i": "诗词",
    "j": "网易云",
    "k": "哲学",
    "l": "抖机灵",
}


# ==================== HTTP路由组件 ====================


class StatsRouter(BaseRouter):
    """统计数据路由组件
    
    提供以下API端点：
    - GET /overview: 获取仪表盘总览数据
    - GET /plugins: 获取插件列表
    - GET /plugins/{plugin_name}: 获取插件详情
    - GET /system: 获取系统状态
    - POST /system/restart: 重启Bot
    - POST /system/shutdown: 关闭Bot
    - GET /plugins-by-status: 按状态获取插件列表
    - GET /components-by-type/{type}: 按类型获取组件列表
    - GET /daily-quote: 获取每日名言
    - GET /message-stats: 获取消息收发统计
    - GET /chat-stats: 获取聊天流统计
    """
    
    router_name = "WebUI_Stats"
    router_description = "WebUI统计数据接口"
    
    custom_route_path = "/webui/api/stats"
    cors_origins = ["*"]
    
    def register_endpoints(self) -> None:
        """注册所有HTTP端点"""
        
        @self.app.get("/overview", summary="获取仪表盘总览数据", response_model=DashboardOverviewResponse)
        async def get_dashboard_overview(_=VerifiedDep):
            """获取仪表盘总览统计数据"""
            try:
                plugin_manager = get_plugin_manager()
                registry = get_global_registry()
                state_manager = get_global_state_manager()
                
                # 获取插件统计
                loaded_plugins = plugin_manager.get_all_plugins()
                failed_plugins = getattr(plugin_manager, '_failed_plugins', {})
                
                # 获取组件统计
                all_states = state_manager.get_all_states()
                active_count = sum(1 for state in all_states.values() if state == ComponentState.ACTIVE)
                inactive_count = len(all_states) - active_count
                
                # 按类型统计组件
                by_type = {}
                for comp_type in ComponentType:
                    if comp_type == ComponentType.PLUGIN:
                        continue
                    components = registry.get_by_type(comp_type)
                    type_active = 0
                    type_total = len(components)
                    for sig in components.keys():
                        if state_manager.get_state(sig) == ComponentState.ACTIVE:
                            type_active += 1
                    by_type[comp_type.value] = {
                        "total": type_total,
                        "active": type_active,
                        "inactive": type_total - type_active
                    }
                
                # 获取系统统计
                process = _process if _process else psutil.Process()
                memory_info = process.memory_info()
                total_memory = psutil.virtual_memory().total / (1024 * 1024)
                
                # 获取聊天流统计
                stream_manager = get_stream_manager()
                all_streams = getattr(stream_manager, '_streams', {})
                total_streams = len(all_streams)
                private_streams = sum(1 for s in all_streams.values() if getattr(s, 'chat_type', '') == 'private')
                group_streams = sum(1 for s in all_streams.values() if getattr(s, 'chat_type', '') in ('group', 'discuss'))
                active_streams = sum(1 for s in all_streams.values() if getattr(s, 'last_active_time', 0) and (time.time() - getattr(s, 'last_active_time', 0)) < 3600)
                
                return DashboardOverviewResponse(
                    plugins=PluginStatsResponse(
                        loaded=len(loaded_plugins),
                        failed=len(failed_plugins),
                        total=len(loaded_plugins) + len(failed_plugins)
                    ),
                    components=ComponentStatsResponse(
                        total=len(all_states),
                        active=active_count,
                        inactive=inactive_count,
                        by_type=by_type
                    ),
                    chats=ChatStatsResponse(
                        total_streams=total_streams,
                        active_streams=active_streams,
                        private_streams=private_streams,
                        group_streams=group_streams
                    ),
                    system=SystemStatsResponse(
                        uptime_seconds=time.time() - _start_time,
                        memory_usage_mb=memory_info.rss / (1024 * 1024),
                        total_memory_mb=total_memory,
                        cpu_percent=process.cpu_percent()
                    )
                )
            except Exception as e:
                logger.error(f"获取仪表盘数据失败: {e}")
                # 返回默认值
                return DashboardOverviewResponse(
                    plugins=PluginStatsResponse(loaded=0, failed=0, total=0),
                    components=ComponentStatsResponse(total=0, active=0, inactive=0, by_type={}),
                    chats=ChatStatsResponse(total_streams=0, active_streams=0, private_streams=0, group_streams=0),
                    system=SystemStatsResponse(uptime_seconds=0, memory_usage_mb=0, total_memory_mb=0, cpu_percent=0)
                )
        
        @self.app.get("/plugins", summary="获取插件列表", response_model=PluginListResponse)
        async def get_plugins_list(_=VerifiedDep):
            """获取所有已加载插件的详细信息列表"""
            try:
                plugin_manager = get_plugin_manager()
                registry = get_global_registry()
                plugins = []
                
                for name, plugin_instance in plugin_manager.get_all_plugins().items():
                    manifest = plugin_manager.get_manifest(name)
                    components = registry.get_by_plugin(name)
                    
                    plugins.append(PluginDetailResponse(
                        name=name,
                        version=manifest.version if manifest else "unknown",
                        author=manifest.author if manifest else "unknown",
                        description=manifest.description if manifest else "",
                        components_count=len(components)
                    ))
                
                return PluginListResponse(plugins=plugins, total=len(plugins))
            except Exception as e:
                logger.error(f"获取插件列表失败: {e}")
                return PluginListResponse(plugins=[], total=0)
        
        @self.app.get("/plugins/{plugin_name}", summary="获取插件详情")
        async def get_plugin_detail(plugin_name: str, _=VerifiedDep):
            """获取指定插件的详细信息"""
            try:
                plugin_manager = get_plugin_manager()
                registry = get_global_registry()
                
                plugin_instance = plugin_manager.get_plugin(plugin_name)
                if not plugin_instance:
                    return {"success": False, "error": f"插件 {plugin_name} 不存在"}
                
                manifest = plugin_manager.get_manifest(plugin_name)
                components = registry.get_by_plugin(plugin_name)
                
                return {
                    "success": True,
                    "plugin": {
                        "name": plugin_name,
                        "version": manifest.version if manifest else "unknown",
                        "author": manifest.author if manifest else "unknown",
                        "description": manifest.description if manifest else "",
                        "components": len(components),
                        "components_list": list(components.keys())
                    }
                }
            except Exception as e:
                logger.error(f"获取插件详情失败: {e}")
                return {"success": False, "error": str(e)}
        
        @self.app.get("/system", summary="获取系统状态")
        async def get_system_status(_=VerifiedDep):
            """获取系统运行状态"""
            try:
                process = _process if _process else psutil.Process()
                memory_info = process.memory_info()
                total_memory = psutil.virtual_memory().total
                
                uptime_seconds = time.time() - _start_time
                
                return {
                    "uptime_seconds": uptime_seconds,
                    "uptime_formatted": _format_uptime(uptime_seconds),
                    "memory_usage_mb": round(memory_info.rss / (1024 * 1024), 2),
                    "total_memory_mb": round(total_memory / (1024 * 1024), 2),
                    "memory_usage_formatted": _format_memory(memory_info.rss),
                    "cpu_percent": process.cpu_percent(),
                    "threads": process.num_threads()
                }
            except Exception as e:
                logger.error(f"获取系统状态失败: {e}")
                return {
                    "uptime_seconds": 0,
                    "uptime_formatted": "0秒",
                    "memory_usage_mb": 0,
                    "total_memory_mb": 0,
                    "memory_usage_formatted": "0 MB",
                    "cpu_percent": 0,
                    "threads": 0
                }
        
        @self.app.post("/system/restart", summary="重启Bot")
        async def restart_bot(_=VerifiedDep):
            """重启 Bot 进程"""
            try:
                import sys
                import os
                
                logger.warning("收到重启请求，准备重启 Bot...")
                
                async def do_restart():
                    await asyncio.sleep(1)
                    python = sys.executable
                    os.execl(python, python, *sys.argv)
                
                asyncio.create_task(do_restart())
                
                return {"success": True, "message": "Bot 将在 1 秒后重启"}
            except Exception as e:
                logger.error(f"重启 Bot 失败: {e}")
                return {"success": False, "error": str(e)}
        
        @self.app.post("/system/shutdown", summary="关闭Bot")
        async def shutdown_bot(_=VerifiedDep):
            """优雅关闭 Bot 进程"""
            try:
                import sys
                
                logger.warning("收到关闭请求，准备关闭 Bot...")
                
                async def do_shutdown():
                    await asyncio.sleep(1)
                    sys.exit(0)
                
                asyncio.create_task(do_shutdown())
                
                return {"success": True, "message": "Bot 将在 1 秒后关闭"}
            except Exception as e:
                logger.error(f"关闭 Bot 失败: {e}")
                return {"success": False, "error": str(e)}
        
        @self.app.get("/plugins-by-status", summary="按状态获取插件列表", response_model=PluginsByStatusResponse)
        async def get_plugins_by_status(_=VerifiedDep):
            """获取按状态分组的插件列表"""
            try:
                plugin_manager = get_plugin_manager()
                registry = get_global_registry()
                
                loaded = []
                for name, plugin_instance in plugin_manager.get_all_plugins().items():
                    manifest = plugin_manager.get_manifest(name)
                    components = registry.get_by_plugin(name)
                    
                    loaded.append(PluginListItemResponse(
                        name=name,
                        version=manifest.version if manifest else "unknown",
                        author=manifest.author if manifest else "unknown",
                        description=manifest.description if manifest else "",
                        components_count=len(components),
                        error=None
                    ))
                
                failed = []
                failed_plugins = getattr(plugin_manager, '_failed_plugins', {})
                for name, error in failed_plugins.items():
                    failed.append(PluginListItemResponse(
                        name=name,
                        version="unknown",
                        author="unknown",
                        description="",
                        components_count=0,
                        error=error
                    ))
                
                return PluginsByStatusResponse(loaded=loaded, failed=failed)
            except Exception as e:
                logger.error(f"获取插件状态列表失败: {e}")
                return PluginsByStatusResponse(loaded=[], failed=[])
        
        @self.app.get("/components-by-type/{component_type}", summary="按类型获取组件列表", response_model=ComponentsByTypeResponse)
        async def get_components_by_type(component_type: str, enabled_only: bool = False, _=VerifiedDep):
            """获取指定类型的组件列表"""
            try:
                registry = get_global_registry()
                state_manager = get_global_state_manager()
                
                # 将字符串转换为 ComponentType 枚举
                try:
                    comp_type = ComponentType(component_type)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"无效的组件类型: {component_type}")
                
                components_dict = registry.get_by_type(comp_type)
                components = []
                active_count = 0
                
                for signature, comp_cls in components_dict.items():
                    state = state_manager.get_state(signature)
                    is_active = state == ComponentState.ACTIVE
                    
                    if enabled_only and not is_active:
                        continue
                    
                    if is_active:
                        active_count += 1
                    
                    # 解析签名获取插件名和组件名
                    from src.core.components.types import parse_signature
                    sig_parts = parse_signature(signature)
                    
                    components.append(ComponentItemResponse(
                        name=sig_parts["component_name"],
                        plugin_name=sig_parts["plugin_name"],
                        type=component_type,
                        state=state.value
                    ))
                
                return ComponentsByTypeResponse(
                    component_type=component_type,
                    components=components,
                    total=len(components),
                    active=active_count,
                    inactive=len(components) - active_count
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取组件列表失败: {e}")
                return ComponentsByTypeResponse(
                    component_type=component_type,
                    components=[],
                    total=0,
                    active=0,
                    inactive=0
                )
        
        @self.app.get("/daily-quote", summary="获取每日名言", response_model=DailyQuoteResponse)
        async def get_daily_quote(_=VerifiedDep):
            """获取每日名言（通过网络API）
            
            使用一言API获取每日名言，如果失败则返回默认名言
            """
            try:
                today = datetime.now().strftime("%Y-%m-%d")
                
                # 尝试从一言API获取
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as client:
                    try:
                        async with client.get("https://v1.hitokoto.cn/?encode=json") as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                quote_type = data.get("type", "")
                                category = HITOKOTO_TYPE_MAP.get(quote_type, "其他")
                                
                                return DailyQuoteResponse(
                                    quote=data.get("hitokoto", "Stay hungry, stay foolish."),
                                    author=data.get("from_who") or data.get("from", "未知"),
                                    category=category,
                                    date=today
                                )
                    except Exception as e:
                        logger.debug(f"一言API请求失败: {e}")
                
                # 如果所有API都失败，返回默认名言
                return DailyQuoteResponse(
                    quote="Stay hungry, stay foolish.",
                    author="Steve Jobs",
                    category="励志",
                    date=today
                )
            except Exception as e:
                logger.error(f"获取每日名言失败: {e}")
                return DailyQuoteResponse(
                    quote="Stay hungry, stay foolish.",
                    author="Steve Jobs",
                    category="励志",
                    date=datetime.now().strftime("%Y-%m-%d")
                )
        
        @self.app.get("/message-stats", summary="获取消息收发统计")
        async def get_message_stats(
            period: Literal["last_hour", "last_24_hours", "last_7_days", "last_30_days"] = "last_24_hours",
            _=VerifiedDep
        ):
            """获取消息收发统计（按时间分组）
            
            Args:
                period: 时间段，支持 last_hour, last_24_hours, last_7_days, last_30_days
            """
            try:
                now = datetime.now()
                period_map = {
                    "last_hour": (timedelta(hours=1), timedelta(minutes=5), "%H:%M"),
                    "last_24_hours": (timedelta(days=1), timedelta(hours=1), "%m-%d %H:00"),
                    "last_7_days": (timedelta(days=7), timedelta(days=1), "%m-%d"),
                    "last_30_days": (timedelta(days=30), timedelta(days=1), "%m-%d"),
                }
                
                time_delta, interval, time_format = period_map.get(
                    period, (timedelta(days=1), timedelta(hours=1), "%m-%d %H:00")
                )
                start_time = now - time_delta
                
                # 初始化时间桶
                data_points = {}
                current = start_time
                while current <= now:
                    key = current.strftime(time_format)
                    data_points[key] = {"timestamp": key, "received": 0, "sent": 0}
                    current += interval
                
                # 获取Bot信息用于区分发送和接收
                from src.core.managers.adapter_manager import get_adapter_manager
                adapter_manager = get_adapter_manager()
                
                # 获取所有消息
                messages = await message_api.get_messages_by_time(
                    start_time=start_time.timestamp(),
                    end_time=now.timestamp(),
                    limit=0,
                    limit_mode="latest"
                )
                
                # 统计
                total_received = 0
                total_sent = 0
                
                for msg in messages:
                    msg_time = datetime.fromtimestamp(msg.get("time", 0))
                    bucket_key = msg_time.strftime(time_format)
                    
                    if bucket_key in data_points:
                        platform = msg.get("platform", "")
                        sender_id = msg.get("sender_id", "")
                        
                        # 判断是否为Bot发送的消息
                        is_bot = False
                        if platform:
                            try:
                                bot_info = await adapter_manager.get_bot_info_by_platform(platform)
                                if bot_info and str(bot_info.get("bot_id", "")) == sender_id:
                                    is_bot = True
                            except Exception:
                                pass
                        
                        if is_bot:
                            data_points[bucket_key]["sent"] += 1
                            total_sent += 1
                        else:
                            data_points[bucket_key]["received"] += 1
                            total_received += 1
                
                # 转换为列表
                sorted_points = sorted(data_points.values(), key=lambda x: x["timestamp"])
                
                return MessageStatsResponse(
                    data_points=[MessageStatsDataPoint(**p) for p in sorted_points],
                    total_received=total_received,
                    total_sent=total_sent,
                    period=period
                )
            except Exception as e:
                logger.error(f"获取消息统计失败: {e}")
                return MessageStatsResponse(
                    data_points=[],
                    total_received=0,
                    total_sent=0,
                    period=period
                )
        
        @self.app.get("/chat-stats", summary="获取聊天流统计")
        async def get_chat_stats(_=VerifiedDep):
            """获取聊天流统计信息"""
            try:
                stream_manager = get_stream_manager()
                
                # 访问内部的 _streams 字典
                all_streams = getattr(stream_manager, '_streams', {})
                
                total_streams = len(all_streams)
                private_streams = 0
                group_streams = 0
                active_streams = 0
                
                # 统计各类型流
                for stream in all_streams.values():
                    chat_type = getattr(stream, 'chat_type', 'private')
                    
                    if chat_type == 'private':
                        private_streams += 1
                    elif chat_type in ('group', 'discuss'):
                        group_streams += 1
                    
                    # 检查最近活跃时间（最近1小时内活跃）
                    last_active = getattr(stream, 'last_active_time', 0)
                    if last_active and (time.time() - last_active) < 3600:
                        active_streams += 1
                
                return ChatStatsResponse(
                    total_streams=total_streams,
                    active_streams=active_streams,
                    private_streams=private_streams,
                    group_streams=group_streams
                )
            except Exception as e:
                logger.error(f"获取聊天流统计失败: {e}")
                return ChatStatsResponse(
                    total_streams=0,
                    active_streams=0,
                    private_streams=0,
                    group_streams=0
                )
    
    async def startup(self) -> None:
        """路由启动钩子"""
        logger.info(f"Stats 路由已启动，路径: {self.custom_route_path}")
    
    async def shutdown(self) -> None:
        """路由关闭钩子"""
        logger.info("Stats 路由已关闭")


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
