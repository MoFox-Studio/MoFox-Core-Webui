"""
表达方式管理路由组件
提供表达方式查询和管理API接口
"""

from typing import Literal

from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.plugin_system import BaseRouterComponent
from src.plugin_system.apis import expression_api

logger = get_logger("WebUI.ExpressionRouter")


# ==================== 请求模型 ====================


class CreateExpressionRequest(BaseModel):
    """创建表达方式请求"""

    situation: str = Field(..., min_length=1, max_length=200, description="情境描述")
    style: str = Field(..., min_length=1, max_length=200, description="表达风格")
    chat_id: str = Field(..., description="聊天流ID")
    type: Literal["style", "grammar"] = Field(default="style", description="类型")
    count: float = Field(default=1.0, ge=0.0, le=5.0, description="权重")


class UpdateExpressionRequest(BaseModel):
    """更新表达方式请求"""

    situation: str | None = Field(None, min_length=1, max_length=200, description="情境描述")
    style: str | None = Field(None, min_length=1, max_length=200, description="表达风格")
    count: float | None = Field(None, ge=0.0, le=5.0, description="权重")
    type: Literal["style", "grammar"] | None = Field(None, description="类型")


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""

    expression_ids: list[int] = Field(..., description="要删除的表达方式ID列表")


class ImportExpressionsRequest(BaseModel):
    """导入表达方式请求"""

    data: str = Field(..., description="导入数据内容")
    format: Literal["json", "csv"] = Field(default="json", description="数据格式")
    chat_id: str | None = Field(None, description="目标聊天流ID")
    merge_strategy: Literal["skip", "replace", "merge"] = Field(default="skip", description="合并策略")


# ==================== 路由组件 ====================


class ExpressionRouterComponent(BaseRouterComponent):
    """
    表达方式管理路由组件
    
    提供以下API端点：
    - GET /expression/list: 获取表达方式列表
    - GET /expression/{id}: 获取表达方式详情
    - GET /expression/search/query: 搜索表达方式
    - GET /expression/statistics/overview: 获取统计信息
    - POST /expression/: 创建表达方式
    - PUT /expression/{id}: 更新表达方式
    - DELETE /expression/{id}: 删除表达方式
    - POST /expression/batch-delete: 批量删除
    - POST /expression/{id}/activate: 激活表达方式
    - GET /expression/sharing-groups/list: 获取共享组配置
    - GET /expression/related-chats/{chat_id}: 获取关联聊天流
    - GET /expression/export/data: 导出表达方式
    - POST /expression/import/data: 导入表达方式
    """
    
    component_name = "expression"
    component_description = "表达方式管理接口"

    def register_endpoints(self) -> None:
        """注册所有HTTP端点"""

        @self.router.get(
            "/chat-list",
            summary="获取聊天流列表",
            description="获取所有可用的聊天流列表"
        )
        async def get_chat_list(_= VerifiedDep):
            """获取聊天流列表"""
            try:
                from src.plugin_system.apis import chat_api
                
                streams = []
                if hasattr(chat_api, "get_streams"):
                    streams = chat_api.get_streams()
                elif hasattr(chat_api, "get_all_streams"):
                    streams = chat_api.get_all_streams()
                
                result = []
                for stream in streams:
                    # 兼容对象和字典
                    s_id = stream.get("stream_id") if isinstance(stream, dict) else getattr(stream, "stream_id", "")
                    s_name = stream.get("name") if isinstance(stream, dict) else getattr(stream, "name", "")
                    s_platform = stream.get("platform") if isinstance(stream, dict) else getattr(stream, "platform", "")
                    s_type = stream.get("type") if isinstance(stream, dict) else getattr(stream, "type", "")
                    
                    if s_id:
                        result.append({
                            "id": s_id,
                            "name": s_name or s_id,
                            "platform": s_platform,
                            "type": s_type
                        })
                return result
            except Exception as e:
                logger.error(f"获取聊天流列表失败: {e}")
                return []

        @self.router.get(
            "/list",
            summary="获取表达方式列表",
            description="获取表达方式列表，支持分页、筛选和排序"
        )
        async def get_expression_list(
            _= VerifiedDep,
            chat_id: str | None = Query(None, description="聊天流ID筛选"),
            type: Literal["style", "grammar"] | None = Query(None, description="类型筛选"),
            page: int = Query(1, ge=1, description="页码"),
            page_size: int = Query(20, ge=1, le=100, description="每页数量"),
            sort_by: Literal["count", "last_active_time", "create_date"] = Query("last_active_time", description="排序字段"),
            sort_order: Literal["asc", "desc"] = Query("desc", description="排序顺序"),
        ):
            """获取表达方式列表"""
            try:
                result = await expression_api.get_expression_list(
                    chat_id=chat_id, type=type, page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order
                )
                return result
            except Exception as e:
                logger.error(f"获取表达方式列表失败: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.get(
            "/{expression_id}",
            summary="获取表达方式详情",
            description="获取指定表达方式的完整信息"
        )
        async def get_expression_detail(expression_id: int, _= VerifiedDep):
            """获取表达方式详情"""
            try:
                result = await expression_api.get_expression_detail(expression_id)
                if not result:
                    raise HTTPException(status_code=404, detail="表达方式不存在")
                return result
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取表达方式详情失败: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.get(
            "/search/query",
            summary="搜索表达方式",
            description="根据关键词搜索表达方式"
        )
        async def search_expressions(
            _= VerifiedDep,
            keyword: str = Query(..., min_length=1, description="搜索关键词"),
            search_field: Literal["situation", "style", "both"] = Query("both", description="搜索范围"),
            chat_id: str | None = Query(None, description="限定聊天流"),
            type: Literal["style", "grammar"] | None = Query(None, description="限定类型"),
            limit: int = Query(50, ge=1, le=200, description="最大返回数量"),
        ):
            """搜索表达方式"""
            try:
                results = await expression_api.search_expressions(
                    keyword=keyword, search_field=search_field, chat_id=chat_id, type=type, limit=limit
                )
                return {"results": results, "total": len(results)}
            except Exception as e:
                logger.error(f"搜索表达方式失败: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.get(
            "/statistics/overview",
            summary="获取统计信息",
            description="获取表达方式的统计信息"
        )
        async def get_statistics(_= VerifiedDep, chat_id: str | None = Query(None, description="聊天流ID")):
            """获取统计信息"""
            try:
                return await expression_api.get_expression_statistics(chat_id)
            except Exception as e:
                logger.error(f"获取统计信息失败: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.post(
            "/",
            summary="创建表达方式",
            description="手动创建新的表达方式"
        )
        async def create_expression(request: CreateExpressionRequest, _= VerifiedDep):
            """创建表达方式"""
            try:
                result = await expression_api.create_expression(
                    situation=request.situation,
                    style=request.style,
                    chat_id=request.chat_id,
                    type=request.type,
                    count=request.count,
                )
                return result
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e)) from e
            except Exception as e:
                logger.error(f"创建表达方式失败: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.put(
            "/{expression_id}",
            summary="更新表达方式",
            description="更新指定表达方式的信息"
        )
        async def update_expression(expression_id: int, request: UpdateExpressionRequest, _= VerifiedDep):
            """更新表达方式"""
            try:
                success = await expression_api.update_expression(
                    expression_id=expression_id,
                    situation=request.situation,
                    style=request.style,
                    count=request.count,
                    type=request.type,
                )
                if not success:
                    raise HTTPException(status_code=404, detail="表达方式不存在")
                return {"success": True}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"更新表达方式失败: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.delete(
            "/{expression_id}",
            summary="删除表达方式",
            description="删除指定的表达方式"
        )
        async def delete_expression(expression_id: int, _= VerifiedDep):
            """删除表达方式"""
            try:
                success = await expression_api.delete_expression(expression_id)
                if not success:
                    raise HTTPException(status_code=404, detail="表达方式不存在")
                return {"success": True}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"删除表达方式失败: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.post(
            "/batch-delete",
            summary="批量删除表达方式",
            description="批量删除多个表达方式"
        )
        async def batch_delete(request: BatchDeleteRequest, _= VerifiedDep):
            """批量删除"""
            try:
                deleted = await expression_api.batch_delete_expressions(request.expression_ids)
                return {"deleted": deleted}
            except Exception as e:
                logger.error(f"批量删除失败: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.post(
            "/{expression_id}/activate",
            summary="激活表达方式",
            description="增加表达方式的权重"
        )
        async def activate_expression(
            expression_id: int, _= VerifiedDep, increment: float = Query(0.1, ge=0.0, le=1.0, description="增加的权重值")
        ):
            """激活表达方式（增加权重）"""
            try:
                success = await expression_api.activate_expression(expression_id, increment)
                if not success:
                    raise HTTPException(status_code=404, detail="表达方式不存在")
                return {"success": True}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"激活表达方式失败: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e



        @self.router.get(
            "/sharing-groups/list",
            summary="获取共享组配置",
            description="获取所有共享组的配置信息"
        )
        async def get_sharing_groups(_= VerifiedDep):
            """获取共享组配置"""
            try:
                groups = await expression_api.get_sharing_groups()
                return {"groups": groups, "total": len(groups)}
            except Exception as e:
                logger.error(f"获取共享组失败: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.get(
            "/related-chats/{chat_id}",
            summary="获取关联聊天流",
            description="获取与指定聊天流共享表达方式的其他聊天流"
        )
        async def get_related_chats(chat_id: str, _= VerifiedDep):
            """获取关联聊天流"""
            try:
                related = await expression_api.get_related_chat_ids(chat_id)
                return {"chat_ids": related, "total": len(related)}
            except Exception as e:
                logger.error(f"获取关联聊天流失败: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.get(
            "/export/data",
            summary="导出表达方式",
            description="导出表达方式数据为JSON或CSV格式"
        )
        async def export_expressions(
            _= VerifiedDep,
            chat_id: str | None = Query(None, description="聊天流ID"),
            type: Literal["style", "grammar"] | None = Query(None, description="类型"),
            format: Literal["json", "csv"] = Query("json", description="格式"),
        ):
            """导出表达方式"""
            try:
                data = await expression_api.export_expressions(chat_id=chat_id, type=type, format=format)
                return {"data": data, "format": format}
            except Exception as e:
                logger.error(f"导出表达方式失败: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.post(
            "/import/data",
            summary="导入表达方式",
            description="从JSON或CSV文件导入表达方式数据"
        )
        async def import_expressions(request: ImportExpressionsRequest, _= VerifiedDep):
            """导入表达方式"""
            try:
                result = await expression_api.import_expressions(
                    data=request.data, format=request.format, chat_id=request.chat_id, merge_strategy=request.merge_strategy
                )
                return result
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e)) from e
            except Exception as e:
                logger.error(f"导入表达方式失败: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e
