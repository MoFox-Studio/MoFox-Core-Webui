"""
表情包管理路由组件

提供表情包的CRUD操作、批量管理、统计等功能
"""

import asyncio
import base64
import io
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel, Field
from sqlalchemy import and_, delete, func, or_, select, update

from src.chat.emoji_system.emoji_manager import get_emoji_manager
from src.chat.emoji_system.emoji_constants import EMOJI_DIR
from src.chat.utils.utils_image import get_image_manager, image_path_to_base64
from src.common.database.api.crud import CRUDBase
from src.common.database.compatibility import get_db_session
from src.common.database.core.models import Emoji
from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.config.config import global_config
from src.plugin_system import BaseRouterComponent

logger = get_logger("WebUI.EmojiRouter")


# ============================================================================
# Pydantic 模型
# ============================================================================


class EmojiItemResponse(BaseModel):
    """表情包列表项响应模型"""

    id: int
    hash: str
    description: str
    format: str
    is_registered: bool
    is_banned: bool
    usage_count: int
    query_count: int
    record_time: float
    thumbnail: Optional[str] = None


class EmojiDetailResponse(BaseModel):
    """表情包详情响应模型"""

    id: int
    hash: str
    description: str
    format: str
    full_path: str
    is_registered: bool
    is_banned: bool
    usage_count: int
    query_count: int
    last_used_time: Optional[float] = None
    record_time: float
    register_time: Optional[float] = None
    full_image: Optional[str] = None


class EmojiListResponse(BaseModel):
    """表情包列表响应模型"""

    items: list[EmojiItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class EmojiUpdateRequest(BaseModel):
    """表情包更新请求模型"""

    description: Optional[str] = None
    is_banned: Optional[bool] = None


class BatchOperationRequest(BaseModel):
    """批量操作请求模型"""

    action: str = Field(..., description="操作类型: delete, ban, unban")
    emoji_hashes: list[str] = Field(..., description="表情包哈希列表")


class BatchOperationResult(BaseModel):
    """批量操作结果"""

    hash: str
    success: bool
    error: Optional[str] = None


class BatchOperationResponse(BaseModel):
    """批量操作响应模型"""

    processed: int
    succeeded: int
    failed: int
    results: list[BatchOperationResult]


class EmojiStatsResponse(BaseModel):
    """表情包统计响应模型"""

    total_count: int
    registered_count: int
    banned_count: int
    total_usage: int
    top_used: list[dict[str, Any]]


# ============================================================================
# 辅助函数
# ============================================================================


async def generate_thumbnail(image_path: str, max_size: tuple = (200, 200)) -> str:
    """生成缩略图并返回Base64编码"""
    try:
        with Image.open(image_path) as img:
            # 检查是否是GIF动图
            is_gif = img.format == 'GIF' and getattr(img, 'is_animated', False)
            
            if is_gif:
                # GIF动图：返回原始base64
                buffer = io.BytesIO()
                with open(image_path, 'rb') as f:
                    buffer.write(f.read())
                img_base64 = base64.b64encode(buffer.getvalue()).decode()
                return f"data:image/gif;base64,{img_base64}"
            
            # 静态图片：生成缩略图
            # 保持宽高比缩放
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # 转换为RGB（处理RGBA、P等模式）
            if img.mode not in ('RGB', 'L'):
                if img.mode == 'RGBA':
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                elif img.mode == 'P':
                    # P模式（调色板模式）转RGB
                    img = img.convert('RGB')
                else:
                    # 其他模式统一转RGB
                    img = img.convert('RGB')

            # 转换为Base64
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85, optimize=True)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/jpeg;base64,{img_base64}"
    except Exception as e:
        logger.error(f"生成缩略图失败: {e}")
        return ""


async def get_emoji_by_hash(emoji_hash: str) -> Optional[Emoji]:
    """根据哈希值获取表情包"""
    async with get_db_session() as session:
        result = await session.execute(select(Emoji).where(Emoji.emoji_hash == emoji_hash))
        return result.scalar_one_or_none()


# ============================================================================
# 路由组件类
# ============================================================================


class EmojiManagerRouterComponent(BaseRouterComponent):
    """表情包管理路由组件"""

    component_name = "emoji"
    component_description = "表情包管理接口"

    def __init__(self):
        super().__init__()
        self.emoji_manager = get_emoji_manager()
        logger.info("表情包管理路由组件已初始化")

    def register_endpoints(self) -> None:
        """注册所有HTTP端点"""

        @self.router.get("/list", summary="获取表情包列表", description="分页获取表情包列表，支持搜索和筛选")
        async def get_emoji_list(
            _ =  VerifiedDep,
            page: int = Query(1, ge=1, description="页码"),
            page_size: int = Query(50, ge=1, le=200, description="每页数量"),
            search: str = Query("", description="搜索关键词"),
            sort_by: str = Query("record_time", description="排序字段"),
            sort_order: str = Query("desc", description="排序方向"),
            is_registered: Optional[bool] = Query(None, description="注册状态筛选"),
            is_banned: Optional[bool] = Query(None, description="禁用状态筛选"),
        ):
            """获取表情包列表"""
            try:
                # 打印接收到的参数
                
                async with get_db_session() as session:
                    # 构建查询
                    query = select(Emoji)

                    # 搜索过滤
                    if search:
                        query = query.where(Emoji.description.ilike(f"%{search}%"))

                    # 状态过滤
                    if is_registered is not None:
                        query = query.where(Emoji.is_registered == is_registered)

                    if is_banned is not None:
                        query = query.where(Emoji.is_banned == is_banned)

                    # 计算总数
                    count_query = select(func.count()).select_from(query.subquery())
                    total = await session.scalar(count_query)

                    # 排序
                    if hasattr(Emoji, sort_by):
                        order_column = getattr(Emoji, sort_by)
                        if sort_order == "desc":
                            query = query.order_by(order_column.desc())
                        else:
                            query = query.order_by(order_column.asc())

                    # 分页
                    offset = (page - 1) * page_size
                    query = query.offset(offset).limit(page_size)

                    # 执行查询
                    result = await session.execute(query)
                    emojis = result.scalars().all()

                    # 生成响应数据
                    items = []
                    for emoji in emojis:
                        # 生成缩略图
                        thumbnail = await generate_thumbnail(emoji.full_path)

                        items.append(
                            EmojiItemResponse(
                                id=emoji.id,
                                hash=emoji.emoji_hash,
                                description=emoji.description,
                                format=emoji.format,
                                is_registered=emoji.is_registered,
                                is_banned=emoji.is_banned,
                                usage_count=emoji.usage_count,
                                query_count=emoji.query_count,
                                record_time=emoji.record_time,
                                thumbnail=thumbnail,
                            )
                        )

                    return {
                        "success": True,
                        "data": {
                            "items": [item.model_dump() for item in items],
                            "total": total,
                            "page": page,
                            "page_size": page_size,
                            "total_pages": (total + page_size - 1) // page_size,
                        },
                    }

            except Exception as e:
                logger.error(f"获取表情包列表失败: {e}")
                raise HTTPException(status_code=500, detail=f"获取表情包列表失败: {str(e)}")

        @self.router.get("/{emoji_hash}", summary="获取表情包详情", description="根据哈希值获取表情包完整信息")
        async def get_emoji_detail(emoji_hash: str,_ =  VerifiedDep ):
            """获取表情包详情"""
            try:
                emoji = await get_emoji_by_hash(emoji_hash)
                logger.info(emoji)
                if not emoji:
                    raise HTTPException(status_code=404, detail="表情包不存在")

                # 获取完整图片（支持GIF动图）
                full_image = ""
                try:
                    # 获取图片格式
                    img_format = "JPEG"
                    try:
                        with Image.open(emoji.full_path) as img:
                            img_format = img.format
                    except Exception:
                        pass

                    # 读取文件内容
                    with open(emoji.full_path, 'rb') as f:
                        file_content = f.read()
                    
                    img_base64 = base64.b64encode(file_content).decode()
                    
                    # 确定 MIME type
                    mime_type = "image/jpeg" # 默认
                    if img_format:
                        fmt = img_format.upper()
                        if fmt == 'GIF':
                            mime_type = "image/gif"
                        elif fmt == 'PNG':
                            mime_type = "image/png"
                        elif fmt in ['JPEG', 'JPG']:
                            mime_type = "image/jpeg"
                        elif fmt == 'WEBP':
                            mime_type = "image/webp"
                        elif fmt == 'BMP':
                            mime_type = "image/bmp"
                    
                    full_image = f"data:{mime_type};base64,{img_base64}"

                except Exception as e:
                    logger.error(f"读取图片失败: {e}")
                    try:
                        full_image = image_path_to_base64(emoji.full_path)
                    except Exception:
                        full_image = ""

                detail = EmojiDetailResponse(
                    id=emoji.id,
                    hash=emoji.emoji_hash,
                    description=emoji.description,
                    format=emoji.format,
                    full_path=emoji.full_path,
                    is_registered=emoji.is_registered,
                    is_banned=emoji.is_banned,
                    usage_count=emoji.usage_count,
                    query_count=emoji.query_count,
                    last_used_time=emoji.last_used_time,
                    record_time=emoji.record_time,
                    register_time=emoji.register_time,
                    full_image=full_image,
                )

                return {"success": True, "data": detail.model_dump()}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取表情包详情失败: {e}")
                raise HTTPException(status_code=500, detail=f"获取表情包详情失败: {str(e)}")

        @self.router.post("/upload", summary="上传表情包", description="批量上传表情包文件")
        async def upload_emoji(_ =  VerifiedDep, files: list[UploadFile] = File(...)):
            """上传表情包"""
            try:
                if not files:
                    raise HTTPException(status_code=400, detail="未提供文件")

                # 确保目录存在
                emoji_dir = Path(EMOJI_DIR)
                emoji_dir.mkdir(parents=True, exist_ok=True)

                results = []
                uploaded = 0
                failed = 0

                for file in files:
                    try:
                        # 验证文件类型
                        if not file.content_type or not file.content_type.startswith("image/"):
                            results.append({"filename": file.filename, "success": False, "error": "不支持的文件类型"})
                            failed += 1
                            continue

                        # 读取文件内容
                        content = await file.read()

                        # 验证是否为有效图片
                        try:
                            img = Image.open(io.BytesIO(content))
                            img.verify()
                        except Exception:
                            results.append({"filename": file.filename, "success": False, "error": "无效的图片文件"})
                            failed += 1
                            continue

                        # 生成随机文件名，保留原始扩展名
                        import uuid
                        original_ext = Path(file.filename).suffix
                        new_filename = f"{uuid.uuid4().hex}{original_ext}"
                        file_path = emoji_dir / new_filename

                        # 保存文件
                        with open(file_path, "wb") as f:
                            f.write(content)

                        # 注册到数据库
                        success = await self.emoji_manager.register_emoji_by_filename(new_filename)

                        if success:
                            results.append(
                                {"filename": file.filename, "success": True, "message": "上传成功"}
                            )
                            uploaded += 1
                        else:
                            # 注册失败删除文件
                            if file_path.exists():
                                file_path.unlink()
                            results.append({"filename": file.filename, "success": False, "error": "注册失败"})
                            failed += 1

                    except Exception as e:
                        logger.error(f"处理文件 {file.filename} 失败: {e}")
                        results.append({"filename": file.filename, "success": False, "error": str(e)})
                        failed += 1

                # 分离成功和失败的结果
                success_results = [r for r in results if r["success"]]
                failed_results = [r for r in results if not r["success"]]

                return {
                    "success": True,
                    "data": {
                        "uploaded": uploaded,
                        "failed": failed,
                        "success": success_results,
                        "failed": failed_results
                    }
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"上传表情包失败: {e}")
                raise HTTPException(status_code=500, detail=f"上传表情包失败: {str(e)}")

        @self.router.delete("/{emoji_hash}", summary="删除表情包", description="根据哈希值删除表情包")
        async def delete_emoji(emoji_hash: str,_ =  VerifiedDep ):
            """删除表情包"""
            try:
                success = await self.emoji_manager.delete_emoji(emoji_hash)
                if not success:
                    raise HTTPException(status_code=404, detail="表情包不存在或删除失败")

                return {"success": True, "message": "表情包删除成功"}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"删除表情包失败: {e}")
                raise HTTPException(status_code=500, detail=f"删除表情包失败: {str(e)}")

        @self.router.patch("/{emoji_hash}", summary="更新表情包信息", description="更新表情包的描述、情感标签或禁用状态")
        async def update_emoji(emoji_hash: str, data: EmojiUpdateRequest,_ =  VerifiedDep):
            """更新表情包信息"""
            try:
                async with get_db_session() as session:
                    # 在当前 session 中查询 emoji
                    result = await session.execute(select(Emoji).where(Emoji.emoji_hash == emoji_hash))
                    emoji = result.scalar_one_or_none()
                    
                    if not emoji:
                        raise HTTPException(status_code=404, detail="表情包不存在")

                    # 构建更新数据
                    update_data = {}
                    if data.description is not None:
                        update_data["description"] = data.description
                    if data.is_banned is not None:
                        update_data["is_banned"] = data.is_banned

                    if update_data:
                        stmt = update(Emoji).where(Emoji.emoji_hash == emoji_hash).values(**update_data)
                        await session.execute(stmt)
                        await session.commit()

                        # 刷新对象以获取更新后的数据
                        await session.refresh(emoji)

                    return {
                        "success": True,
                        "data": {
                            "id": emoji.id,
                            "hash": emoji.emoji_hash,
                            "description": emoji.description,
                            "is_banned": emoji.is_banned,
                        },
                    }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"更新表情包失败: {e}")
                raise HTTPException(status_code=500, detail=f"更新表情包失败: {str(e)}")

        @self.router.post("/batch", summary="批量操作表情包", description="批量删除、禁用或启用表情包")
        async def batch_operation(request: BatchOperationRequest , _ =  VerifiedDep):
            """批量操作表情包"""
            try:
                if not request.emoji_hashes:
                    raise HTTPException(status_code=400, detail="未提供表情包哈希列表")

                results = []
                succeeded = 0
                failed = 0

                for emoji_hash in request.emoji_hashes:
                    try:
                        if request.action == "delete":
                            success = await self.emoji_manager.delete_emoji(emoji_hash)
                            if success:
                                results.append(BatchOperationResult(hash=emoji_hash, success=True))
                                succeeded += 1
                            else:
                                results.append(
                                    BatchOperationResult(hash=emoji_hash, success=False, error="删除失败")
                                )
                                failed += 1

                        elif request.action in ["ban", "unban"]:
                            async with get_db_session() as session:
                                is_banned = request.action == "ban"
                                stmt = update(Emoji).where(Emoji.emoji_hash == emoji_hash).values(is_banned=is_banned)
                                result = await session.execute(stmt)
                                await session.commit()

                                if result.rowcount > 0:
                                    results.append(BatchOperationResult(hash=emoji_hash, success=True))
                                    succeeded += 1
                                else:
                                    results.append(
                                        BatchOperationResult(hash=emoji_hash, success=False, error="表情包不存在")
                                    )
                                    failed += 1
                        else:
                            results.append(
                                BatchOperationResult(hash=emoji_hash, success=False, error="不支持的操作")
                            )
                            failed += 1

                    except Exception as e:
                        logger.error(f"处理表情包 {emoji_hash} 失败: {e}")
                        results.append(BatchOperationResult(hash=emoji_hash, success=False, error=str(e)))
                        failed += 1

                response = BatchOperationResponse(
                    processed=len(request.emoji_hashes),
                    succeeded=succeeded,
                    failed=failed,
                    results=results,
                )

                return {"success": True, "data": response.model_dump()}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"批量操作失败: {e}")
                raise HTTPException(status_code=500, detail=f"批量操作失败: {str(e)}")

        @self.router.get("/stats", summary="获取表情包统计", description="获取表情包的统计信息，包括总数、使用情况等")
        async def get_emoji_stats(_ =  VerifiedDep):
            """获取表情包统计信息"""
            try:
                async with get_db_session() as session:
                    # 总数统计
                    total_count = await session.scalar(select(func.count(Emoji.id)))
                    registered_count = await session.scalar(
                        select(func.count(Emoji.id)).where(Emoji.is_registered == True)
                    )
                    banned_count = await session.scalar(select(func.count(Emoji.id)).where(Emoji.is_banned == True))
                    total_usage = await session.scalar(select(func.sum(Emoji.usage_count))) or 0

                    # 最常用的表情包
                    top_used_result = await session.execute(
                        select(Emoji.emoji_hash, Emoji.description, Emoji.usage_count)
                        .order_by(Emoji.usage_count.desc())
                        .limit(10)
                    )
                    top_used = [
                        {"hash": row[0], "description": row[1], "usage_count": row[2]}
                        for row in top_used_result.all()
                    ]

                    stats = EmojiStatsResponse(
                        total_count=total_count,
                        registered_count=registered_count,
                        banned_count=banned_count,
                        total_usage=total_usage,
                        top_used=top_used,
                    )

                    return {"success": True, "data": stats.model_dump()}

            except Exception as e:
                logger.error(f"获取统计信息失败: {e}")
                raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
