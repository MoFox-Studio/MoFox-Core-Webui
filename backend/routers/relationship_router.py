"""
人物关系管理路由组件
提供用户关系查询和管理API接口
"""

from typing import Any, Optional
import orjson

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.common.database.api.crud import CRUDBase
from src.common.database.core.models import PersonInfo, UserRelationships
from src.common.database.core.session import get_db_session
from src.plugin_system import BaseRouterComponent

logger = get_logger("WebUI.RelationshipRouter")


# ==================== 请求模型 ====================


class UpdateRelationshipRequest(BaseModel):
    """更新关系请求"""

    relationship_score: float = Field(..., ge=0.0, le=1.0, description="关系分数 (0.0 - 1.0)")
    relationship_text: Optional[str] = Field(None, description="关系描述文本")


class UpdateImpressionRequest(BaseModel):
    """更新印象请求"""

    impression: Optional[str] = Field(None, description="详细印象")
    short_impression: Optional[str] = Field(None, description="简短印象")


# ==================== 响应模型 ====================


class PersonBasicInfoResponse(BaseModel):
    """用户基础信息响应"""

    person_id: str
    person_name: str
    nickname: Optional[str] = None
    know_times: int = 0
    know_since: Optional[str] = None
    last_know: Optional[str] = None
    attitude: Optional[int] = None  # 修正: 态度值是整数类型


class PersonCardResponse(BaseModel):
    """用户卡片信息响应（列表展示用）"""

    person_id: str
    person_name: str
    nickname: Optional[str] = None
    relationship_score: float = 0.0
    relationship_text: Optional[str] = None
    short_impression: Optional[str] = None
    know_times: int = 0
    last_know: Optional[str] = None


class PersonRelationshipResponse(BaseModel):
    """用户关系响应"""

    person_id: str
    person_name: str
    relationship_score: float
    relationship_text: Optional[str] = None


class PersonDetailResponse(BaseModel):
    """用户详情响应"""

    basic_info: PersonBasicInfoResponse
    relationship: PersonRelationshipResponse
    impression: str
    short_impression: str
    memory_points: list[dict[str, Any]]


class PersonListResponse(BaseModel):
    """用户列表响应"""

    persons: list[PersonCardResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RelationshipReportResponse(BaseModel):
    """关系报告响应"""

    person_id: str
    report: str


class UpdateRelationshipResponse(BaseModel):
    """更新关系响应"""

    success: bool
    message: str


# ==================== 路由组件 ====================


class RelationshipRouterComponent(BaseRouterComponent):
    """
    人物关系管理路由组件
    
    提供以下API端点：
    - GET /relationship/person/{person_id}: 获取用户详情
    - PUT /relationship/person/{person_id}: 更新用户关系
    - GET /relationship/person/{person_id}/report: 获取关系报告
    - GET /relationship/search: 搜索用户
    - GET /relationship/stats: 获取关系统计
    - POST /relationship/cache/clear: 清理关系缓存
    """
    
    component_name = "relationship"
    component_description = "人物关系管理接口"
    
    def register_endpoints(self) -> None:
        """注册所有HTTP端点"""
        
        @self.router.get(
            "/list",
            response_model=PersonListResponse,
            summary="获取用户列表",
            description="获取所有用户的卡片信息，支持分页和平台筛选",
        )
        async def get_person_list(page: int = 1, page_size: int = 20, platform: Optional[str] = None, _=VerifiedDep):
            """获取用户列表"""
            logger.info(f"[get_person_list] 请求参数: page={page}, page_size={page_size}, platform={platform}")
            try:
                crud = CRUDBase(PersonInfo)
                
                # 获取总数
                if platform:
                    # 按平台筛选
                    total = await crud.count(platform=platform)
                    logger.info(f"[get_person_list] 平台 {platform} 中共有 {total} 个用户")
                else:
                    total = await crud.count()
                    logger.info(f"[get_person_list] 数据库中共有 {total} 个用户")
                
                # 计算分页
                total_pages = (total + page_size - 1) // page_size
                offset = (page - 1) * page_size
                
                # 使用原生SQL查询按最后交互时间排序
                logger.info(f"[get_person_list] 查询偏移量: offset={offset}, limit={page_size}")
                async with get_db_session() as session:
                    stmt = select(PersonInfo).order_by(PersonInfo.last_know.desc())
                    
                    # 如果指定了平台，添加筛选条件
                    if platform:
                        stmt = stmt.where(PersonInfo.platform == platform)
                        logger.debug(f"[get_person_list] 添加平台筛选: platform={platform}")
                    
                    stmt = stmt.limit(page_size).offset(offset)
                    result = await session.execute(stmt)
                    persons_data = result.scalars().all()
                    logger.info(f"[get_person_list] 查询到 {len(persons_data)} 个用户")
                    
                    # 批量查询关系数据
                    user_ids = [person.user_id for person in persons_data]
                    stmt_rel = select(UserRelationships).where(UserRelationships.user_id.in_(user_ids))
                    result_rel = await session.execute(stmt_rel)
                    relationships = result_rel.scalars().all()
                    
                    # 构建 user_id -> relationship 的映射
                    relationship_map = {rel.user_id: rel for rel in relationships}
                    logger.debug(f"[get_person_list] 查询到 {len(relationships)} 条关系数据")
                
                # 构建响应
                persons = []
                for person in persons_data:
                    # 从关系映射中获取关系分数
                    user_rel = relationship_map.get(person.user_id)
                    relationship_score = user_rel.relationship_score if user_rel else 0.0
                    relationship_text = person.relation_value if hasattr(person, 'relation_value') else None
                    
                    persons.append(PersonCardResponse(
                        person_id=person.person_id,
                        person_name=person.person_name or "未知用户",
                        nickname=person.nickname,
                        relationship_score=relationship_score,
                        relationship_text=relationship_text,
                        short_impression=person.short_impression,
                        know_times=int(person.know_times or 0),
                        last_know=str(person.last_know) if person.last_know else None
                    ))
                
                return PersonListResponse(
                    persons=persons,
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages
                )
                    
            except Exception as e:
                logger.error(f"获取用户列表失败: {e}")
                return PersonListResponse(
                    persons=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0
                )
        
        @self.router.get(
            "/person/{person_id}",
            response_model=PersonDetailResponse,
            summary="获取用户详情",
            description="获取指定用户的完整信息，包括基础信息、关系数据、印象和记忆点",
        )
        async def get_person_detail(person_id: str, _=VerifiedDep):
            """获取用户详情"""
            logger.info(f"[get_person_detail] 请求用户详情: person_id={person_id}")
            try:
                # 使用CRUD获取用户信息
                crud = CRUDBase(PersonInfo)
                logger.debug(f"[get_person_detail] 开始查询数据库...")
                person = await crud.get_by(person_id=person_id,use_cache = False)
                
                if not person:
                    logger.warning(f"[get_person_detail] 未找到用户: person_id={person_id}")
                    raise HTTPException(status_code=404, detail="用户不存在")
                
                logger.info(f"[get_person_detail] 找到用户: name={person.person_name}, platform={person.platform}, user_id={person.user_id},person.impression={person.impression},short={person.short_impression},{person.points}")

                # 获取印象
                impression = person.impression or "暂无印象"
                short_impression = person.short_impression or "暂无印象"

                # 解析记忆点
                memory_points = []
                if person.points:
                    try:
                        if isinstance(person.points, str):
                            points_data = orjson.loads(person.points)
                        else:
                            points_data = person.points
                        
                        # 限制返回10条
                        for p in points_data[:10]:
                            if isinstance(p, (list, tuple)) and len(p) >= 3:
                                memory_points.append({
                                    "content": p[0],
                                    "weight": float(p[1]),
                                    "timestamp": str(p[2])
                                })
                    except Exception as e:
                        logger.warning(f"解析记忆点失败: {e}")

                # 从UserRelationships获取关系数据
                relationship_score = 0.0
                relationship_text = None
                
                async with get_db_session() as session:
                    # 构建user_id: platform:user_id
                    stmt_rel = select(UserRelationships).where(UserRelationships.user_id == person.user_id)
                    result_rel = await session.execute(stmt_rel)
                    user_rel = result_rel.scalar_one_or_none()
                    
                    if user_rel:
                        relationship_score = user_rel.relationship_score
                        logger.debug(f"[get_person_detail] 找到关系数据: score={relationship_score}, text={relationship_text}")
                    else:
                        logger.debug(f"[get_person_detail] 未找到关系数据: user_id={person.user_id}")

                return PersonDetailResponse(
                    basic_info=PersonBasicInfoResponse(
                        person_id=person_id,
                        person_name=person.person_name or "未知用户",
                        nickname=person.nickname,
                        know_times=int(person.know_times or 0),
                        know_since=str(person.know_since) if person.know_since else None,
                        last_know=str(person.last_know) if person.last_know else None,
                        attitude=int(person.attitude) if person.attitude is not None else None
                    ),
                    relationship=PersonRelationshipResponse(
                        person_id=person_id,
                        person_name=person.person_name or "未知用户",
                        relationship_score=relationship_score,
                        relationship_text=person.relation_value if hasattr(person, 'relation_value') else None                    ),
                    impression=impression,
                    short_impression=short_impression,
                    memory_points=memory_points,
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取用户详情失败: {e}")
                raise HTTPException(status_code=500, detail=f"获取用户详情失败: {str(e)}")

        @self.router.put(
            "/person/{person_id}",
            response_model=UpdateRelationshipResponse,
            summary="更新用户关系",
            description="更新指定用户的关系分数和关系描述",
        )
        async def update_person_relationship(person_id: str, request: UpdateRelationshipRequest, _=VerifiedDep):
            """更新用户关系"""
            try:
                # 使用CRUD检查用户是否存在
                crud = CRUDBase(PersonInfo)
                person = await crud.get_by(person_id=person_id, use_cache=False)
                
                if not person:
                    return UpdateRelationshipResponse(success=False, message="用户不存在")

                # 更新UserRelationships表
                async with get_db_session() as session:
                    # 构建user_id: platform:user_id
                    stmt = select(UserRelationships).where(UserRelationships.user_id == person.user_id)
                    result = await session.execute(stmt)
                    user_rel = result.scalar_one_or_none()
                    
                    if user_rel:
                        # 更新现有记录
                        user_rel.relationship_score = request.relationship_score
                        if request.relationship_text is not None:
                            user_rel.relationship_text = request.relationship_text
                        user_rel.last_updated = __import__('time').time()
                        logger.info(f"更新用户关系: {person.user_id} -> score={request.relationship_score}")
                    else:
                        # 创建新记录
                        import time
                        new_rel = UserRelationships(
                            user_id=person.user_id,
                            user_name=person.person_name,
                            relationship_score=request.relationship_score,
                            relationship_text=request.relationship_text,
                            last_updated=time.time()
                        )
                        session.add(new_rel)
                        logger.info(f"创建用户关系: {person.user_id} -> score={request.relationship_score}")
                    
                    await session.commit()
                
                logger.info(f"用户 {person_id} 的关系更新成功")
                return UpdateRelationshipResponse(success=True, message="关系更新成功")
            except Exception as e:
                logger.error(f"更新用户关系失败: {e}")
                return UpdateRelationshipResponse(success=False, message=str(e))

        @self.router.put(
            "/person/{person_id}/impression",
            response_model=UpdateRelationshipResponse,
            summary="更新用户印象",
            description="更新指定用户的详细印象和简短印象",
        )
        async def update_person_impression(person_id: str, request: UpdateImpressionRequest, _=VerifiedDep):
            """更新用户印象"""
            try:
                from src.common.database.core.models import PersonInfo
                from src.common.database.core.session import get_db_session
                from sqlalchemy import select
                
                async with get_db_session() as session:
                    # 检查用户是否存在
                    stmt = select(PersonInfo).where(PersonInfo.person_id == person_id)
                    result = await session.execute(stmt)
                    person = result.scalar_one_or_none()
                    
                    if not person:
                        return UpdateRelationshipResponse(success=False, message="用户不存在")
                    
                    # 更新印象
                    if request.impression is not None:
                        person.impression = request.impression
                    if request.short_impression is not None:
                        person.short_impression = request.short_impression
                    
                    await session.commit()
                
                logger.info(f"用户 {person_id} 的印象更新成功")
                return UpdateRelationshipResponse(success=True, message="印象更新成功")
            except Exception as e:
                logger.error(f"更新用户印象失败: {e}")
                return UpdateRelationshipResponse(success=False, message=str(e))

        @self.router.put(
            "/person/{person_id}/points",
            response_model=UpdateRelationshipResponse,
            summary="更新用户记忆点",
            description="更新指定用户的记忆点列表",
        )
        async def update_person_points(person_id: str, points: list[dict[str, Any]], _=VerifiedDep):
            """更新用户记忆点"""
            try:
                from src.common.database.core.models import PersonInfo
                from src.common.database.core.session import get_db_session
                from sqlalchemy import select
                import orjson
                
                logger.info(f"开始更新用户 {person_id} 的记忆点，共 {len(points)} 个")
                
                async with get_db_session() as session:
                    # 检查用户是否存在
                    stmt = select(PersonInfo).where(PersonInfo.person_id == person_id)
                    result = await session.execute(stmt)
                    person = result.scalar_one_or_none()
                    
                    if not person:
                        logger.warning(f"用户 {person_id} 不存在")
                        return UpdateRelationshipResponse(success=False, message="用户不存在")
                    
                    # 转换为正确的格式 [(content, weight, timestamp), ...]
                    formatted_points = [
                        (point.get("content", ""), float(point.get("weight", 0)), point.get("timestamp", ""))
                        for point in points
                    ]
                    
                    # 序列化为JSON字符串存储
                    person.points = orjson.dumps(formatted_points).decode("utf-8")
                    
                    await session.commit()
                
                logger.info(f"用户 {person_id} 的记忆点更新成功")
                return UpdateRelationshipResponse(success=True, message="记忆点更新成功")
            except Exception as e:
                logger.error(f"更新用户记忆点失败: {e}", exc_info=True)
                return UpdateRelationshipResponse(success=False, message=str(e))

        @self.router.get(
            "/person/{person_id}/report",
            response_model=RelationshipReportResponse,
            summary="获取关系报告",
            description="生成指定用户的完整关系报告",
        )
        async def get_relationship_report(person_id: str, _=VerifiedDep):
            """获取关系报告"""
            try:
                crud = CRUDBase(PersonInfo)
                person = await crud.get_by(person_id=person_id,use_cache = False)
                
                if not person:
                    return {"error": "用户不存在"}
                
                # 从UserRelationships获取关系数据
                relationship_text = "无"
                relationship_score = 0.0
                async with get_db_session() as session:
                    user_rel_id = f"{person.platform}:{person.user_id}"
                    stmt_rel = select(UserRelationships).where(UserRelationships.user_id == user_rel_id)
                    result_rel = await session.execute(stmt_rel)
                    user_rel = result_rel.scalar_one_or_none()
                    if user_rel:
                        relationship_text = user_rel.relationship_text or "无"
                        relationship_score = user_rel.relationship_score
                
                # 生成简单的关系报告
                report = f"""用户: {person.person_name or '未知'}
昵称: {person.nickname or '无'}
认识次数: {person.know_times or 0}
印象: {person.impression or '暂无'}
关系分数: {relationship_score:.2f}
关系描述: {relationship_text}"""
                
                return RelationshipReportResponse(person_id=person_id, report=report)
            except Exception as e:
                logger.error(f"获取关系报告失败: {e}")
                return {"error": str(e)}

        @self.router.get(
            "/stats",
            summary="获取关系统计",
            description="获取系统关系统计信息",
        )
        async def get_relationship_stats(_=VerifiedDep):
            """获取关系统计"""
            try:
                crud = CRUDBase(PersonInfo)
                total_users = await crud.count()
                
                # 统计有印象的用户
                async with get_db_session() as session:
                    stmt = select(PersonInfo).where(PersonInfo.impression.isnot(None))
                    result = await session.execute(stmt)
                    users_with_impression = len(result.scalars().all())
                
                return {
                    "total_users": total_users,
                    "users_with_impression": users_with_impression,
                }
            except Exception as e:
                logger.error(f"获取关系统计失败: {e}")
                return {"error": str(e)}

        @self.router.post(
            "/cache/clear",
            summary="清理关系缓存",
            description="清理指定用户或全部用户的关系缓存",
        )
        async def clear_relationship_cache(person_id: Optional[str] = None, _=VerifiedDep):
            """清理关系缓存"""
            try:
                from src.common.database.optimization import get_cache
                cache = await get_cache()
                
                if person_id:
                    # 清理特定用户的缓存
                    await cache.delete(f"person_info:id:{person_id}")
                    logger.info(f"已清理用户 {person_id} 的缓存")
                else:
                    # 清理所有缓存
                    await cache.clear()
                    logger.info("已清理所有关系缓存")
                
                return {"success": True, "message": "缓存清理成功"}
            except Exception as e:
                logger.error(f"清理关系缓存失败: {e}")
                return {"error": str(e)}

        @self.router.get(
            "/platforms",
            summary="获取平台列表",
            description="获取所有用户的平台列表及每个平台的用户数",
        )
        async def get_platforms(_=VerifiedDep):
            """获取平台列表"""
            logger.info(f"[get_platforms] 请求获取平台列表")
            try:
                from sqlalchemy import func
                
                async with get_db_session() as session:
                    # 查询所有平台及其用户数
                    stmt = (
                        select(
                            PersonInfo.platform,
                            func.count(PersonInfo.id).label('count')
                        )
                        .group_by(PersonInfo.platform)
                        .order_by(func.count(PersonInfo.id).desc())
                    )
                    result = await session.execute(stmt)
                    platforms_data = result.all()
                    
                    platforms = [
                        {"platform": row[0], "count": row[1]}
                        for row in platforms_data
                    ]
                    
                    logger.info(f"[get_platforms] 找到 {len(platforms)} 个平台")
                    for p in platforms:
                        logger.debug(f"[get_platforms] 平台: {p['platform']}, 用户数: {p['count']}")
                    
                    return {"platforms": platforms}
            except Exception as e:
                logger.error(f"[get_platforms] 获取平台列表失败: {e}")
                return {"error": str(e)}

        @self.router.get(
            "/search",
            summary="搜索用户",
            description="根据用户名搜索用户",
        )
        async def search_person(query: str, _=VerifiedDep):
            """搜索用户"""
            logger.info(f"[search_person] 搜索用户: query={query}")
            try:
                crud = CRUDBase(PersonInfo)
                
                # 先按person_name搜索
                logger.debug(f"[search_person] 按 person_name 搜索...")
                person = await crud.get_by(person_name=query,use_cache = False)
                
                # 如果没找到，按nickname搜索
                if not person:
                    logger.debug(f"[search_person] person_name 未找到，尝试按 nickname 搜索...")
                    person = await crud.get_by(nickname=query,use_cache = False)
                
                if not person:
                    logger.warning(f"[search_person] 未找到用户: query={query}")
                    return {"error": "未找到用户"}
                
                logger.info(f"[search_person] 找到用户: person_id={person.person_id}, name={person.person_name}, platform={person.platform}")

                return PersonBasicInfoResponse(
                    person_id=person.person_id,
                    person_name=person.person_name or "",
                    nickname=person.nickname,
                    know_times=int(person.know_times or 0),
                    know_since=str(person.know_since) if person.know_since else None,
                    last_know=str(person.last_know) if person.last_know else None,
                    attitude=int(person.attitude) if person.attitude is not None else None
                )
            except Exception as e:
                logger.error(f"搜索用户失败: {e}")
                return {"error": str(e)}
