"""
模型统计路由组件
提供模型使用统计API接口
"""

import time
from datetime import datetime, timedelta
from typing import Any, Literal, Optional

from pydantic import BaseModel

from src.chat.utils.statistic import StatisticOutputTask
from src.chat.utils.statistic_keys import *  # noqa: F403
from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.manager.local_store_manager import local_storage
from src.plugin_system import BaseRouterComponent

logger = get_logger("WebUIAuth.ModelStatsRouter")


# ==================== 响应模型 ====================


class ModelUsageStatsResponse(BaseModel):
    """模型使用统计响应"""
    stats: dict[str, dict[str, int]]


class ModelDetailStatsResponse(BaseModel):
    """模型详细统计响应"""
    model_name: str
    total_calls: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_cost: float
    avg_tokens_per_call: float
    avg_time_per_call: float
    tps: float
    cost_per_ktok: float
    last_used: Optional[str] = None


class ModelStatsOverviewResponse(BaseModel):
    """模型统计总览响应"""
    total_models: int
    total_calls: int
    total_tokens: int
    total_cost: float
    most_used_model: Optional[str] = None
    most_expensive_model: Optional[str] = None


class ProviderStatsResponse(BaseModel):
    """提供商统计响应"""
    stats: dict[str, dict[str, Any]]


class ModuleStatsResponse(BaseModel):
    """模块统计响应"""
    stats: dict[str, dict[str, Any]]


class ChartDataResponse(BaseModel):
    """图表数据响应"""
    chart_data: dict[str, Any]


# ==================== HTTP路由组件 ====================


class WebUIModelStatsRouter(BaseRouterComponent):
    """
    WebUI模型统计路由组件

    提供以下API端点：
    - GET /model_usage: 获取模型使用统计（最近24小时）
    - GET /model_overview: 获取模型统计总览
    - GET /model_detail/{model_name}: 获取指定模型的详细统计
    """

    component_name = "model_stats"
    component_description = "WebUI模型统计接口"

    def register_endpoints(self) -> None:
        """注册所有HTTP端点"""

        @self.router.get("/model_usage", summary="获取模型使用统计", response_model=ModelUsageStatsResponse)
        async def get_model_usage_stats(time_range: str = "24h", _=VerifiedDep):
            """获取模型使用统计"""
            try:
                now = datetime.now()
                
                # 将时间范围转换为start_time
                if time_range == "all":
                    # 获取部署时间
                    deploy_time_ts = local_storage.get("deploy_time")
                    if deploy_time_ts:
                        start_time = datetime.fromtimestamp(float(deploy_time_ts)) # type: ignore
                    else:
                        # 如果没有部署时间记录，使用一个很早的时间
                        start_time = datetime(2000, 1, 1)
                        local_storage["deploy_time"] = now.timestamp()
                else:
                    time_map = {
                        "1h": timedelta(hours=1),
                        "24h": timedelta(days=1),
                        "7d": timedelta(days=7),
                        "30d": timedelta(days=30)
                    }
                    delta = time_map.get(time_range, timedelta(days=1))
                    start_time = now - delta
                
                stats_data = await StatisticOutputTask._collect_model_request_for_period([("custom", start_time)])
                period_stats = stats_data.get("custom", {})
                
                if not period_stats:
                    return ModelUsageStatsResponse(stats={"Debug: No Data": {"total_calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}})
                
                # 调试日志：查看数据结构
                logger.debug(f"StatisticOutputTask keys: {list(period_stats.keys())}")
                
                # 整合数据
                tokens_by_model = period_stats.get("tokens_by_model", {})
                in_tokens_by_model = period_stats.get("in_tokens_by_model", {})
                out_tokens_by_model = period_stats.get("out_tokens_by_model", {})
                # 尝试获取调用次数统计（如果存在）
                requests_by_model = period_stats.get("requests_by_model", {})
                
                result = {}
                
                # 获取所有涉及的模型名称
                all_models = set(tokens_by_model.keys()) | set(in_tokens_by_model.keys()) | set(out_tokens_by_model.keys())
                
                for model in all_models:
                    model_key = str(model) if model else "Unknown"
                    result[model_key] = {
                        "total_calls": requests_by_model.get(model, 0),
                        "prompt_tokens": in_tokens_by_model.get(model, 0),
                        "completion_tokens": out_tokens_by_model.get(model, 0),
                        "total_tokens": tokens_by_model.get(model, 0)
                    }
                    
                return ModelUsageStatsResponse(stats=result)
            except Exception as e:
                logger.error(f"获取模型使用统计失败: {e}", exc_info=True)
                return ModelUsageStatsResponse(stats={f"Error: {str(e)}": {"total_calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}})

        @self.router.get("/model_overview", summary="获取模型统计总览", response_model=ModelStatsOverviewResponse)
        async def get_model_overview(time_range: str = "24h", _=VerifiedDep):
            """获取模型统计总览"""
            try:
                now = datetime.now()
                
                if time_range == "all":
                    deploy_time_ts = local_storage.get("deploy_time")
                    if deploy_time_ts:
                        start_time = datetime.fromtimestamp(float(deploy_time_ts)) # type: ignore # type: ignore
                    else:
                        start_time = datetime(2000, 1, 1)
                        local_storage["deploy_time"] = now.timestamp()
                else:
                    time_map = {
                        "1h": timedelta(hours=1),
                        "24h": timedelta(days=1),
                        "7d": timedelta(days=7),
                        "30d": timedelta(days=30)
                    }
                    delta = time_map.get(time_range, timedelta(days=1))
                    start_time = now - delta
                
                stats_data = await StatisticOutputTask._collect_model_request_for_period([("custom", start_time)])
                period_stats = stats_data.get("custom", {})
                
                if not period_stats:
                    return ModelStatsOverviewResponse(
                        total_models=0,
                        total_calls=0,
                        total_tokens=0,
                        total_cost=0.0
                    )
                
                tokens_by_model = period_stats.get("tokens_by_model", {})
                requests_by_model = period_stats.get("requests_by_model", {})
                cost_by_model = period_stats.get("cost_by_model", {})
                
                total_models = len(tokens_by_model)
                total_calls = sum(requests_by_model.values())
                total_tokens = sum(tokens_by_model.values())
                total_cost = sum(cost_by_model.values())
                
                # 找出使用最多的模型
                most_used_model = max(requests_by_model.items(), key=lambda x: x[1])[0] if requests_by_model else None
                # 找出花费最多的模型
                most_expensive_model = max(cost_by_model.items(), key=lambda x: x[1])[0] if cost_by_model else None
                
                return ModelStatsOverviewResponse(
                    total_models=total_models,
                    total_calls=total_calls,
                    total_tokens=total_tokens,
                    total_cost=total_cost,
                    most_used_model=str(most_used_model) if most_used_model else None,
                    most_expensive_model=str(most_expensive_model) if most_expensive_model else None
                )
            except Exception as e:
                logger.error(f"获取模型统计总览失败: {e}", exc_info=True)
                return ModelStatsOverviewResponse(
                    total_models=0,
                    total_calls=0,
                    total_tokens=0,
                    total_cost=0.0
                )

        @self.router.get("/model_detail/{model_name}", summary="获取模型详细统计")
        async def get_model_detail(model_name: str, time_range: str = "24h", _=VerifiedDep):
            """获取指定模型的详细统计"""
            try:
                now = datetime.now()
                
                if time_range == "all":
                    deploy_time_ts = local_storage.get("deploy_time")
                    if deploy_time_ts:
                        start_time = datetime.fromtimestamp(float(deploy_time_ts)) # type: ignore
                    else:
                        start_time = datetime(2000, 1, 1)
                        local_storage["deploy_time"] = now.timestamp()
                else:
                    time_map = {
                        "1h": timedelta(hours=1),
                        "24h": timedelta(days=1),
                        "7d": timedelta(days=7),
                        "30d": timedelta(days=30)
                    }
                    delta = time_map.get(time_range, timedelta(days=1))
                    start_time = now - delta
                
                stats_data = await StatisticOutputTask._collect_model_request_for_period([("custom", start_time)])
                period_stats = stats_data.get("custom", {})
                
                if not period_stats:
                    return {"success": False, "error": "无统计数据"}
                
                tokens_by_model = period_stats.get("tokens_by_model", {})
                in_tokens_by_model = period_stats.get("in_tokens_by_model", {})
                out_tokens_by_model = period_stats.get("out_tokens_by_model", {})
                requests_by_model = period_stats.get("requests_by_model", {})
                cost_by_model = period_stats.get("cost_by_model", {})
                
                if model_name not in tokens_by_model:
                    return {"success": False, "error": f"未找到模型 {model_name} 的统计数据"}
                
                total_calls = requests_by_model.get(model_name, 0)
                total_tokens = tokens_by_model.get(model_name, 0)
                prompt_tokens = in_tokens_by_model.get(model_name, 0)
                completion_tokens = out_tokens_by_model.get(model_name, 0)
                total_cost = cost_by_model.get(model_name, 0.0)
                
                avg_tokens_per_call = total_tokens / total_calls if total_calls > 0 else 0
                avg_time_by_model = period_stats.get(AVG_TIME_COST_BY_MODEL, {})
                avg_time_per_call = avg_time_by_model.get(model_name, 0.0)
                
                tps_by_model = period_stats.get(TPS_BY_MODEL, {})
                tps = tps_by_model.get(model_name, 0.0)
                
                cost_per_ktok_by_model = period_stats.get(COST_PER_KTOK_BY_MODEL, {})
                cost_per_ktok = cost_per_ktok_by_model.get(model_name, 0.0)
                
                return ModelDetailStatsResponse(
                    model_name=model_name,
                    total_calls=total_calls,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    total_cost=total_cost,
                    avg_tokens_per_call=avg_tokens_per_call,
                    avg_time_per_call=avg_time_per_call,
                    tps=tps,
                    cost_per_ktok=cost_per_ktok
                )
            except Exception as e:
                logger.error(f"获取模型详细统计失败: {e}", exc_info=True)
                return {"success": False, "error": str(e)}

        @self.router.get("/provider_stats", summary="获取提供商统计", response_model=ProviderStatsResponse)
        async def get_provider_stats(time_range: str = "24h", _=VerifiedDep):
            """获取提供商统计数据"""
            try:
                now = datetime.now()
                
                if time_range == "all":
                    deploy_time_ts = local_storage.get("deploy_time")
                    if deploy_time_ts:
                        start_time = datetime.fromtimestamp(float(deploy_time_ts)) # type: ignore
                    else:
                        start_time = datetime(2000, 1, 1)
                        local_storage["deploy_time"] = now.timestamp()
                else:
                    time_map = {
                        "1h": timedelta(hours=1),
                        "24h": timedelta(days=1),
                        "7d": timedelta(days=7),
                        "30d": timedelta(days=30)
                    }
                    delta = time_map.get(time_range, timedelta(days=1))
                    start_time = now - delta
                
                stats_data = await StatisticOutputTask._collect_model_request_for_period([("custom", start_time)])
                period_stats = stats_data.get("custom", {})
                
                if not period_stats:
                    return ProviderStatsResponse(stats={})
                
                requests_by_provider = period_stats.get(REQ_CNT_BY_PROVIDER, {})
                tokens_by_provider = period_stats.get(TOTAL_TOK_BY_PROVIDER, {})
                cost_by_provider = period_stats.get(COST_BY_PROVIDER, {})
                avg_time_by_provider = period_stats.get(AVG_TIME_COST_BY_PROVIDER, {})
                tps_by_provider = period_stats.get(TPS_BY_PROVIDER, {})
                
                result = {}
                all_providers = set(requests_by_provider.keys()) | set(tokens_by_provider.keys())
                
                for provider in all_providers:
                    provider_key = str(provider) if provider else "Unknown"
                    result[provider_key] = {
                        "total_calls": requests_by_provider.get(provider, 0),
                        "total_tokens": tokens_by_provider.get(provider, 0),
                        "total_cost": cost_by_provider.get(provider, 0.0),
                        "avg_time": avg_time_by_provider.get(provider, 0.0),
                        "tps": tps_by_provider.get(provider, 0.0)
                    }
                
                return ProviderStatsResponse(stats=result)
            except Exception as e:
                logger.error(f"获取提供商统计失败: {e}", exc_info=True)
                return ProviderStatsResponse(stats={})

        @self.router.get("/module_stats", summary="获取模块统计", response_model=ModuleStatsResponse)
        async def get_module_stats(time_range: str = "24h", _=VerifiedDep):
            """获取模块统计数据"""
            try:
                now = datetime.now()
                
                if time_range == "all":
                    deploy_time_ts = local_storage.get("deploy_time")
                    if deploy_time_ts:
                        start_time = datetime.fromtimestamp(float(deploy_time_ts)) # type: ignore
                    else:
                        start_time = datetime(2000, 1, 1)
                        local_storage["deploy_time"] = now.timestamp()
                else:
                    time_map = {
                        "1h": timedelta(hours=1),
                        "24h": timedelta(days=1),
                        "7d": timedelta(days=7),
                        "30d": timedelta(days=30)
                    }
                    delta = time_map.get(time_range, timedelta(days=1))
                    start_time = now - delta
                
                stats_data = await StatisticOutputTask._collect_model_request_for_period([("custom", start_time)])
                period_stats = stats_data.get("custom", {})
                
                if not period_stats:
                    return ModuleStatsResponse(stats={})
                
                requests_by_module = period_stats.get(REQ_CNT_BY_MODULE, {})
                tokens_by_module = period_stats.get(TOTAL_TOK_BY_MODULE, {})
                cost_by_module = period_stats.get(COST_BY_MODULE, {})
                avg_time_by_module = period_stats.get(AVG_TIME_COST_BY_MODULE, {})
                
                result = {}
                all_modules = set(requests_by_module.keys()) | set(tokens_by_module.keys())
                
                for module in all_modules:
                    module_key = str(module) if module else "Unknown"
                    result[module_key] = {
                        "total_calls": requests_by_module.get(module, 0),
                        "total_tokens": tokens_by_module.get(module, 0),
                        "total_cost": cost_by_module.get(module, 0.0),
                        "avg_time": avg_time_by_module.get(module, 0.0)
                    }
                
                return ModuleStatsResponse(stats=result)
            except Exception as e:
                logger.error(f"获取模块统计失败: {e}", exc_info=True)
                return ModuleStatsResponse(stats={})

        @self.router.get("/chart_data", summary="获取图表数据", response_model=ChartDataResponse)
        async def get_chart_data(time_range: str = "24h", _=VerifiedDep):
            """获取用于前端图表展示的数据"""
            try:
                now = datetime.now()
                
                if time_range == "all":
                    deploy_time_ts = local_storage.get("deploy_time")
                    if deploy_time_ts:
                        start_time = datetime.fromtimestamp(float(deploy_time_ts)) # type: ignore
                    else:
                        start_time = datetime(2000, 1, 1)
                        local_storage["deploy_time"] = now.timestamp()
                else:
                    time_map = {
                        "1h": timedelta(hours=1),
                        "24h": timedelta(days=1),
                        "7d": timedelta(days=7),
                        "30d": timedelta(days=30)
                    }
                    delta = time_map.get(time_range, timedelta(days=1))
                    start_time = now - delta
                
                stats_data = await StatisticOutputTask._collect_model_request_for_period([("custom", start_time)])
                period_stats = stats_data.get("custom", {})
                
                if not period_stats:
                    return ChartDataResponse(chart_data={})
                
                # 提取图表数据
                chart_data = {
                    "pie_chart_cost_by_provider": period_stats.get(PIE_CHART_COST_BY_PROVIDER, {}),
                    "pie_chart_req_by_provider": period_stats.get(PIE_CHART_REQ_BY_PROVIDER, {}),
                    "pie_chart_cost_by_module": period_stats.get(PIE_CHART_COST_BY_MODULE, {}),
                    "bar_chart_cost_by_model": period_stats.get(BAR_CHART_COST_BY_MODEL, {}),
                    "bar_chart_req_by_model": period_stats.get(BAR_CHART_REQ_BY_MODEL, {}),
                    "bar_chart_token_comparison": period_stats.get(BAR_CHART_TOKEN_COMPARISON, {}),
                    "bar_chart_avg_response_time": period_stats.get(BAR_CHART_AVG_RESPONSE_TIME, {}),
                }
                
                # 如果图表数据为空，从原始统计数据构建
                if not chart_data["bar_chart_cost_by_model"]:
                    cost_by_model = period_stats.get(COST_BY_MODEL, {})
                    if cost_by_model:
                        chart_data["bar_chart_cost_by_model"] = {
                            "labels": list(cost_by_model.keys()),
                            "data": list(cost_by_model.values())
                        }
                
                if not chart_data["bar_chart_req_by_model"]:
                    req_by_model = period_stats.get(REQ_CNT_BY_MODEL, {})
                    if req_by_model:
                        chart_data["bar_chart_req_by_model"] = {
                            "labels": list(req_by_model.keys()),
                            "data": list(req_by_model.values())
                        }
                
                if not chart_data["pie_chart_cost_by_provider"]:
                    cost_by_provider = period_stats.get(COST_BY_PROVIDER, {})
                    if cost_by_provider:
                        chart_data["pie_chart_cost_by_provider"] = {
                            "labels": list(cost_by_provider.keys()),
                            "data": list(cost_by_provider.values())
                        }
                
                if not chart_data["bar_chart_avg_response_time"]:
                    avg_time_by_model = period_stats.get(AVG_TIME_COST_BY_MODEL, {})
                    if avg_time_by_model:
                        chart_data["bar_chart_avg_response_time"] = {
                            "labels": list(avg_time_by_model.keys()),
                            "data": list(avg_time_by_model.values())
                        }
                
                return ChartDataResponse(chart_data=chart_data)
            except Exception as e:
                logger.error(f"获取图表数据失败: {e}", exc_info=True)
                return ChartDataResponse(chart_data={})
