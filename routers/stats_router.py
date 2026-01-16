"""
统计数据路由组件
提供仪表盘统计数据API接口
"""

import aiohttp
import time
from datetime import datetime, timedelta
from typing import  Literal, Optional

import psutil
from pydantic import BaseModel

from src.chat.utils.statistic import StatisticOutputTask
from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.plugin_system import BaseRouterComponent
from src.plugin_system.apis import chat_api, plugin_info_api, schedule_api
from src.plugin_system.base.component_types import ComponentType

logger = get_logger("WebUIAuth.StatsRouter")

# 记录启动时间
_start_time = time.time()

# 初始化CPU使用率监控（第一次调用会返回0，之后才有准确值）
try:
    _process = psutil.Process()
    _process.cpu_percent()  # 初始化调用
except Exception:
    _process = None

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
    total_memory_mb: float
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


class ScheduleActivityResponse(BaseModel):
    """日程活动响应"""

    time_range: str
    activity: str


class ScheduleResponse(BaseModel):
    """日程响应"""

    date: str
    activities: list[ScheduleActivityResponse]
    current_activity: Optional[ScheduleActivityResponse] = None


class MonthlyPlanResponse(BaseModel):
    """月度计划响应"""

    plans: list[str]
    total: int
    month: str


class DailyQuoteResponse(BaseModel):
    """每日名言响应"""

    quote: str
    author: str
    category: str
    date: str


class LLMStatsResponse(BaseModel):
    """LLM 统计响应"""

    total_requests: int
    total_cost: float
    total_tokens: int
    input_tokens: int
    output_tokens: int


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


class PluginListItemResponse(BaseModel):
    """插件列表项响应"""

    name: str
    display_name: str
    version: str
    author: str
    enabled: bool
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
    description: str
    enabled: bool


class ComponentsByTypeResponse(BaseModel):
    """按类型分组的组件列表响应"""

    component_type: str
    components: list[ComponentItemResponse]
    total: int
    enabled: int
    disabled: int


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
                process = _process if _process else psutil.Process()
                memory_info = process.memory_info()
                total_memory = psutil.virtual_memory().total / (1024 * 1024)

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
                        total_memory_mb=total_memory,
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
                    system=SystemStatsResponse(uptime_seconds=0, memory_usage_mb=0, total_memory_mb=0, cpu_percent=0),
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
                    plugins.append(
                        PluginDetailResponse(
                            name=name,
                            display_name=info.get("display_name", name),
                            version=info.get("version", "unknown"),
                            author=info.get("author", "unknown"),
                            enabled=info.get("enabled", False),
                            components_count=len(info.get("components", [])),
                        )
                    )
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
                process = _process if _process else psutil.Process()
                memory_info = process.memory_info()
                total_memory = psutil.virtual_memory().total

                return {
                    "uptime_seconds": time.time() - _start_time,
                    "uptime_formatted": _format_uptime(time.time() - _start_time),
                    "memory_usage_mb": round(memory_info.rss / (1024 * 1024), 2),
                    "total_memory_mb": round(total_memory / (1024 * 1024), 2),
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
                    "total_memory_mb": 0,
                    "memory_usage_formatted": "0 MB",
                    "cpu_percent": 0,
                    "threads": 0,
                }

        @self.router.post("/system/restart", summary="重启Bot")
        async def restart_bot(_=VerifiedDep):
            """
            重启 Bot 进程
            """
            try:
                import asyncio
                import os
                import sys

                logger.warning("收到重启请求，准备重启 Bot...")

                # 异步执行重启，给前端时间接收响应
                async def do_restart():
                    await asyncio.sleep(5)  # 给前端一点时间接收响应
                    logger.info("正在重启 Bot...")
                    
                    # 使用 os.execv 重启当前进程
                    python = sys.executable
                    os.execv(python, [python] + sys.argv)

                # 创建后台任务执行重启
                asyncio.create_task(do_restart())
                
                return {"success": True, "message": "Bot 将在 1 秒后重启"}
            except Exception as e:
                logger.error(f"重启 Bot 失败: {e}")
                return {"success": False, "error": str(e)}

        @self.router.post("/system/shutdown", summary="关闭Bot")
        async def shutdown_bot(_=VerifiedDep):
            """
            优雅关闭 Bot 进程
            """
            try:
                import asyncio
                import os
                import signal

                logger.warning("收到关闭请求，准备关闭 Bot...")

                # 异步执行关闭，给前端时间接收响应
                async def do_shutdown():
                    await asyncio.sleep(1)  # 给前端一点时间接收响应
                    logger.info("正在关闭 Bot...")
                    
                    # 发送 SIGTERM 信号优雅关闭
                    os.kill(os.getpid(), signal.SIGTERM)

                # 创建后台任务执行关闭
                asyncio.create_task(do_shutdown())
                
                return {"success": True, "message": "Bot 将在 1 秒后关闭"}
            except Exception as e:
                logger.error(f"关闭 Bot 失败: {e}")
                return {"success": False, "error": str(e)}

        @self.router.get("/schedule", summary="获取今日日程")
        async def get_today_schedule(date: Optional[str] = None, _=VerifiedDep):
            """
            获取指定日期的日程安排

            Args:
                date: 日期字符串，格式为 YYYY-MM-DD，默认为今天
            """
            try:
                target_date = date or datetime.now().strftime("%Y-%m-%d")

                # 获取日程数据
                schedule_data = await schedule_api.ScheduleAPI.get_schedule(date=target_date)

                # 获取当前活动
                current = await schedule_api.ScheduleAPI.get_current_activity()

                activities = []
                if schedule_data:
                    for item in schedule_data:
                        activities.append(
                            ScheduleActivityResponse(
                                time_range=item.get("time_range", ""), activity=item.get("activity", "")
                            )
                        )

                current_activity = None
                if current:
                    current_activity = ScheduleActivityResponse(
                        time_range=current.get("time_range", ""), activity=current.get("activity", "")
                    )

                return ScheduleResponse(date=target_date, activities=activities, current_activity=current_activity)
            except Exception as e:
                logger.error(f"获取日程失败: {e}")
                return ScheduleResponse(
                    date=date or datetime.now().strftime("%Y-%m-%d"), activities=[], current_activity=None
                )

        @self.router.get("/daily-quote", summary="获取每日名言", response_model=DailyQuoteResponse)
        async def get_daily_quote(_=VerifiedDep):
            """
            获取每日名言（通过网络API）

            使用一言API获取每日名言，如果失败则使用备用API或返回默认名言
            """
            try:
                today = datetime.now().strftime("%Y-%m-%d")
                
                # 尝试从一言API获取
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as client:
                    try:
                        # 使用一言API (hitokoto.cn)
                        response = await client.get("https://v1.hitokoto.cn/", params={
                            "encode": "json"
                        })
                        
                        if response.status == 200:
                            data = await response.json()
                            # 获取类型并映射为中文
                            type_code = data.get("type", "g")
                            category = HITOKOTO_TYPE_MAP.get(type_code, "其他")
                            return DailyQuoteResponse(
                                quote=data.get("hitokoto", "Stay hungry, stay foolish."),
                                author=data.get("from_who") or data.get("from", "Unknown"),
                                category=category,
                                date=today
                            )
                    except Exception as e:
                        logger.warning(f"一言API调用失败: {e}")
                        
                    # 备用：尝试金山词霸每日一句
                    try:
                        response = await client.get("https://open.iciba.com/dsapi/")
                        if response.status == 200:
                            data = await response.json()
                            return DailyQuoteResponse(
                                quote=data.get("content", "Stay hungry, stay foolish."),
                                author=data.get("note", "金山词霸"),
                                category="励志",
                                date=today
                            )
                    except Exception as e:
                        logger.warning(f"金山词霸API调用失败: {e}")
                
                # 如果所有API都失败，返回默认名言
                return DailyQuoteResponse(
                    quote="Stay hungry, stay foolish.",
                    author="Steve Jobs",
                    category="励志",
                    date=today,
                )
            except Exception as e:
                logger.error(f"获取每日名言失败: {e}")
                return DailyQuoteResponse(
                    quote="Stay hungry, stay foolish.",
                    author="Steve Jobs",
                    category="励志",
                    date=datetime.now().strftime("%Y-%m-%d"),
                )

        @self.router.get("/monthly-plans", summary="获取月度计划")
        async def get_monthly_plans(month: Optional[str] = None, limit: int = 10, _=VerifiedDep):
            """
            获取月度计划

            Args:
                month: 月份字符串，格式为 YYYY-MM，默认为当月
                limit: 返回数量限制，默认10条
            """
            try:
                target_month = month or datetime.now().strftime("%Y-%m")

                # 获取月度计划数量
                plan_count = await schedule_api.ScheduleAPI.count_monthly_plans()

                # 获取月度计划列表
                plans_data = await schedule_api.ScheduleAPI.get_monthly_plans(random_count=limit)

                plans = []
                if plans_data:
                    for plan in plans_data:
                        if hasattr(plan, "plan_text"):
                            plans.append(plan.plan_text)
                        elif isinstance(plan, str):
                            plans.append(plan)

                return MonthlyPlanResponse(plans=plans, total=plan_count or 0, month=target_month)
            except Exception as e:
                logger.error(f"获取月度计划失败: {e}")
                return MonthlyPlanResponse(plans=[], total=0, month=month or datetime.now().strftime("%Y-%m"))

        @self.router.get("/llm-stats", summary="获取LLM使用统计")
        async def get_llm_stats(
            period: Literal["last_hour", "last_24_hours", "last_7_days", "last_30_days"] = "last_24_hours",
            _=VerifiedDep,
        ):
            """
            获取LLM使用统计

            Args:
                period: 时间段，支持 last_hour, last_24_hours, last_7_days, last_30_days
            """
            try:
                now = datetime.now()
                period_map = {
                    "last_hour": timedelta(hours=1),
                    "last_24_hours": timedelta(days=1),
                    "last_7_days": timedelta(days=7),
                    "last_30_days": timedelta(days=30),
                }
                start_time = now - period_map.get(period, timedelta(days=1))

                stats_data = await StatisticOutputTask._collect_model_request_for_period([("custom", start_time)])
                period_stats = stats_data.get("custom", {})

                if not period_stats:
                    return LLMStatsResponse(
                        total_requests=0, total_cost=0.0, total_tokens=0, input_tokens=0, output_tokens=0
                    )

                # 计算总的 token 数
                total_tokens = 0
                input_tokens = 0
                output_tokens = 0

                tokens_by_model = period_stats.get("tokens_by_model", {})
                in_tokens_by_model = period_stats.get("in_tokens_by_model", {})
                out_tokens_by_model = period_stats.get("out_tokens_by_model", {})

                for model_tokens in tokens_by_model.values():
                    total_tokens += model_tokens
                for model_tokens in in_tokens_by_model.values():
                    input_tokens += model_tokens
                for model_tokens in out_tokens_by_model.values():
                    output_tokens += model_tokens

                return LLMStatsResponse(
                    total_requests=period_stats.get("total_requests", 0),
                    total_cost=round(period_stats.get("total_cost", 0.0), 4),
                    total_tokens=total_tokens,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
            except Exception as e:
                logger.error(f"获取LLM统计失败: {e}")
                return LLMStatsResponse(
                    total_requests=0, total_cost=0.0, total_tokens=0, input_tokens=0, output_tokens=0
                )

        @self.router.get("/message-stats", summary="获取消息收发统计")
        async def get_message_stats(
            period: Literal["last_hour", "last_24_hours", "last_7_days", "last_30_days"] = "last_24_hours",
            _=VerifiedDep,
        ):
            """
            获取消息收发统计（按时间分组）

            Args:
                period: 时间段，支持 last_hour, last_24_hours, last_7_days, last_30_days
            """
            try:
                from src.common.database.api.query import QueryBuilder
                from src.common.database.core.models import Messages
                from src.config.config import global_config

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
                    data_points[key] = {"received": 0, "sent": 0}
                    current += interval

                bot_user_id = str(global_config.bot.qq_account)

                # 查询消息
                query_builder = (
                    QueryBuilder(Messages).no_cache().filter(time__gte=start_time.timestamp()).order_by("time")
                )

                total_received = 0
                total_sent = 0

                async for batch in query_builder.iter_batches(batch_size=1000, as_dict=True):
                    for msg in batch:
                        if not isinstance(msg, dict):
                            continue
                        msg_time = msg.get("time")
                        if not msg_time:
                            continue

                        msg_datetime = datetime.fromtimestamp(msg_time)
                        time_key = msg_datetime.strftime(time_format)

                        if time_key not in data_points:
                            continue

                        user_id = str(msg.get("user_id", ""))
                        if user_id == bot_user_id:
                            data_points[time_key]["sent"] += 1
                            total_sent += 1
                        else:
                            data_points[time_key]["received"] += 1
                            total_received += 1

                # 转换为列表
                result_points = [
                    MessageStatsDataPoint(timestamp=ts, received=counts["received"], sent=counts["sent"])
                    for ts, counts in sorted(data_points.items())
                ]

                return MessageStatsResponse(
                    data_points=result_points, total_received=total_received, total_sent=total_sent, period=period
                )
            except Exception as e:
                logger.error(f"获取消息统计失败: {e}")
                return MessageStatsResponse(data_points=[], total_received=0, total_sent=0, period=period)

        @self.router.get("/plugins-by-status", summary="按状态获取插件列表")
        def get_plugins_by_status(_=VerifiedDep):
            """
            获取按状态分组的插件列表（已加载和加载失败）
            """
            try:
                from src.plugin_system.core.plugin_manager import plugin_manager
                from src.plugin_system.core.component_registry import component_registry

                loaded_plugins = []
                failed_plugins = []

                # 获取已加载的插件
                for name in plugin_manager.list_loaded_plugins():
                    plugin_info = component_registry.get_plugin_info(name)
                    plugin_instance = plugin_manager.get_plugin_instance(name)

                    loaded_plugins.append(
                        PluginListItemResponse(
                            name=name,
                            display_name=plugin_info.display_name if plugin_info else name,
                            version=plugin_info.version if plugin_info else "unknown",
                            author=plugin_info.author if plugin_info else "unknown",
                            enabled=plugin_instance.enable_plugin if plugin_instance else False,
                            components_count=len(plugin_info.components) if plugin_info else 0,
                        )
                    )

                # 获取加载失败的插件
                for name, error in plugin_manager.failed_plugins.items():
                    failed_plugins.append(
                        PluginListItemResponse(
                            name=name,
                            display_name=name,
                            version="unknown",
                            author="unknown",
                            enabled=False,
                            components_count=0,
                            error=str(error) if error else "加载失败",
                        )
                    )

                return PluginsByStatusResponse(
                    loaded=loaded_plugins,
                    failed=failed_plugins,
                )
            except Exception as e:
                logger.error(f"获取插件列表失败: {e}")
                return PluginsByStatusResponse(loaded=[], failed=[])

        @self.router.get("/components-by-type/{component_type}", summary="按类型获取组件列表")
        def get_components_by_type(component_type: str, enabled_only: bool = False, _=VerifiedDep):
            """
            获取指定类型的组件列表

            Args:
                component_type: 组件类型名称
                enabled_only: 是否只返回已启用的组件
            """
            try:
                # 将字符串转换为 ComponentType 枚举
                try:
                    comp_type = ComponentType(component_type.lower())
                except ValueError:
                    return {"success": False, "error": f"未知的组件类型: {component_type}"}

                # 获取组件列表
                components_list = plugin_info_api.list_components(comp_type, enabled_only=enabled_only)

                # 统计数量
                total = len(components_list)
                enabled = sum(1 for c in components_list if c.get("enabled", False))
                disabled = total - enabled

                return ComponentsByTypeResponse(
                    component_type=component_type,
                    components=[
                        ComponentItemResponse(
                            name=c.get("name", ""),
                            plugin_name=c.get("plugin_name", ""),
                            description=c.get("description", ""),
                            enabled=c.get("enabled", False),
                        )
                        for c in components_list
                    ],
                    total=total,
                    enabled=enabled,
                    disabled=disabled,
                )
            except Exception as e:
                logger.error(f"获取组件列表失败: {e}")
                return {"success": False, "error": str(e)}


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
