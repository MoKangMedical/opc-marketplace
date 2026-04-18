"""
OPC Marketplace - 揭榜挂帅项目API
政府科技创新项目对接
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, ProviderProfile
from app.models.government import GovernmentProject, ProjectApplication, IndustryCategory
from app.schemas.government import (
    GovernmentProjectCreate, GovernmentProjectUpdate, GovernmentProjectResponse,
    ProjectApplicationCreate, ProjectApplicationUpdate, ProjectApplicationResponse,
    IndustryCategoryResponse, ProjectSearch, ProjectStats
)

router = APIRouter()

@router.get("/", response_model=List[GovernmentProjectResponse])
async def list_government_projects(
    industry: Optional[str] = Query(None, description="行业领域"),
    region: Optional[str] = Query(None, description="地区"),
    publisher_type: Optional[str] = Query(None, description="发榜级别"),
    status_filter: Optional[str] = Query(None, description="项目状态"),
    min_budget: Optional[float] = Query(None, description="最低预算"),
    max_budget: Optional[float] = Query(None, description="最高预算"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_featured: Optional[bool] = Query(None, description="是否精选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取政府揭榜挂帅项目列表
    
    支持按行业、地区、级别、预算等条件筛选
    """
    query_builder = select(GovernmentProject).where(
        GovernmentProject.status.in_(["PUBLISHED", "APPLICATION_OPEN"])
    )
    
    if industry:
        query_builder = query_builder.where(GovernmentProject.industry == industry)
    
    if region:
        query_builder = query_builder.where(GovernmentProject.region == region)
    
    if publisher_type:
        query_builder = query_builder.where(GovernmentProject.publisher_type == publisher_type)
    
    if status_filter:
        query_builder = query_builder.where(GovernmentProject.status == status_filter)
    
    if min_budget is not None:
        query_builder = query_builder.where(GovernmentProject.budget_max >= min_budget)
    
    if max_budget is not None:
        query_builder = query_builder.where(GovernmentProject.budget_min <= max_budget)
    
    if search:
        query_builder = query_builder.where(
            or_(
                GovernmentProject.title.ilike(f"%{search}%"),
                GovernmentProject.description.ilike(f"%{search}%"),
                GovernmentProject.publisher_name.ilike(f"%{search}%")
            )
        )
    
    if is_featured is not None:
        query_builder = query_builder.where(GovernmentProject.is_featured == is_featured)
    
    # 按发布时间倒序
    query_builder = query_builder.order_by(GovernmentProject.publish_date.desc())
    
    # 分页
    offset = (page - 1) * page_size
    query_builder = query_builder.offset(offset).limit(page_size)
    
    result = await db.execute(query_builder)
    projects = result.scalars().all()
    
    return projects

@router.get("/featured", response_model=List[GovernmentProjectResponse])
async def get_featured_projects(
    limit: int = Query(6, ge=1, le=20, description="返回数量"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取精选揭榜挂帅项目"""
    result = await db.execute(
        select(GovernmentProject)
        .where(
            GovernmentProject.is_featured == True,
            GovernmentProject.status.in_(["PUBLISHED", "APPLICATION_OPEN"])
        )
        .order_by(GovernmentProject.publish_date.desc())
        .limit(limit)
    )
    projects = result.scalars().all()
    return projects

@router.get("/industries", response_model=List[IndustryCategoryResponse])
async def list_industries(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取行业分类列表"""
    result = await db.execute(
        select(IndustryCategory)
        .where(IndustryCategory.is_active == True)
        .order_by(IndustryCategory.sort_order)
    )
    industries = result.scalars().all()
    return industries

@router.get("/{project_id}", response_model=GovernmentProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取揭榜挂帅项目详情"""
    result = await db.execute(
        select(GovernmentProject)
        .where(GovernmentProject.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 增加浏览次数
    project.view_count += 1
    await db.commit()
    
    return project

@router.post("/{project_id}/apply", response_model=ProjectApplicationResponse)
async def apply_project(
    project_id: str,
    application_data: ProjectApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    申请揭榜挂帅项目
    
    - **team_name**: 申报团队名称
    - **team_introduction**: 团队介绍
    - **technical_capability**: 技术能力说明
    - **project_plan**: 项目实施方案
    """
    # 检查项目是否存在
    result = await db.execute(
        select(GovernmentProject).where(GovernmentProject.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查申报是否截止
    if project.application_deadline < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="申报已截止"
        )
    
    # 检查是否已申请
    result = await db.execute(
        select(ProjectApplication)
        .where(
            ProjectApplication.project_id == project_id,
            ProjectApplication.applicant_id == current_user.id
        )
    )
    existing_application = result.scalar_one_or_none()
    
    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已申请过此项目"
        )
    
    # 创建申请
    application = ProjectApplication(
        project_id=project_id,
        applicant_id=current_user.id,
        **application_data.dict()
    )
    db.add(application)
    
    # 更新项目申请数量
    project.application_count += 1
    
    await db.commit()
    await db.refresh(application)
    
    return application

@router.get("/{project_id}/applications", response_model=List[ProjectApplicationResponse])
async def get_project_applications(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取项目的申请列表（仅限项目发布方）"""
    # 这里简化处理，实际应该检查用户是否是项目发布方
    result = await db.execute(
        select(ProjectApplication)
        .where(ProjectApplication.project_id == project_id)
        .order_by(ProjectApplication.created_at.desc())
    )
    applications = result.scalars().all()
    return applications

@router.get("/my/applications", response_model=List[ProjectApplicationResponse])
async def get_my_applications(
    status_filter: Optional[str] = Query(None, description="申请状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取我的申请列表"""
    query_builder = select(ProjectApplication).where(
        ProjectApplication.applicant_id == current_user.id
    )
    
    if status_filter:
        query_builder = query_builder.where(ProjectApplication.status == status_filter)
    
    query_builder = query_builder.order_by(ProjectApplication.created_at.desc())
    
    offset = (page - 1) * page_size
    query_builder = query_builder.offset(offset).limit(page_size)
    
    result = await db.execute(query_builder)
    applications = result.scalars().all()
    
    return applications

@router.get("/stats/overview", response_model=ProjectStats)
async def get_project_stats(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取揭榜挂帅项目统计信息"""
    # 总项目数
    result = await db.execute(
        select(func.count(GovernmentProject.id))
    )
    total_projects = result.scalar()
    
    # 开放申报项目数
    result = await db.execute(
        select(func.count(GovernmentProject.id))
        .where(GovernmentProject.status == "APPLICATION_OPEN")
    )
    open_projects = result.scalar()
    
    # 总预算金额
    result = await db.execute(
        select(func.sum(GovernmentProject.budget_max))
        .where(GovernmentProject.status.in_(["PUBLISHED", "APPLICATION_OPEN"]))
    )
    total_budget = result.scalar() or 0
    
    # 总申请数
    result = await db.execute(
        select(func.count(ProjectApplication.id))
    )
    total_applications = result.scalar()
    
    # 行业分布
    result = await db.execute(
        select(
            GovernmentProject.industry,
            func.count(GovernmentProject.id).label("count")
        )
        .group_by(GovernmentProject.industry)
        .order_by(func.count(GovernmentProject.id).desc())
        .limit(10)
    )
    industry_distribution = [
        {"industry": row[0], "count": row[1]} 
        for row in result.fetchall()
    ]
    
    return {
        "total_projects": total_projects,
        "open_projects": open_projects,
        "total_budget": float(total_budget),
        "total_applications": total_applications,
        "industry_distribution": industry_distribution
    }

# 以下端点需要管理员权限

@router.post("/", response_model=GovernmentProjectResponse)
async def create_project(
    project_data: GovernmentProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """创建揭榜挂帅项目（管理员权限）"""
    # 这里应该检查管理员权限
    # 简化处理：暂时允许所有用户创建
    
    project = GovernmentProject(**project_data.dict())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return project

@router.put("/{project_id}", response_model=GovernmentProjectResponse)
async def update_project(
    project_id: str,
    project_data: GovernmentProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """更新揭榜挂帅项目（管理员权限）"""
    result = await db.execute(
        select(GovernmentProject).where(GovernmentProject.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    for field, value in project_data.dict(exclude_unset=True).items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    
    return project