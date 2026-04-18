"""
OPC Marketplace - 项目路由
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user, require_client, require_provider
from app.models.user import User, ClientProfile, ProviderProfile
from app.models.project import (
    Project, ProjectMilestone, Match, Proposal, Skill, ProviderSkill
)
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse,
    ProjectMilestoneCreate, ProjectMilestoneUpdate, ProjectMilestoneResponse,
    ProjectSearch, ProjectStats
)

router = APIRouter()

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    创建新项目（仅限需求方）
    
    - **title**: 项目标题
    - **description**: 项目描述
    - **project_type**: 项目类型
    - **budget_type**: 预算类型
    - **budget_min**: 最小预算
    - **budget_max**: 最大预算
    - **required_skills**: 所需技能ID列表
    """
    # 获取需求方资料
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == current_user.id)
    )
    client_profile = result.scalar_one_or_none()
    
    if not client_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="需求方资料不存在"
        )
    
    # 创建项目
    project = Project(
        client_id=client_profile.id,
        **project_data.dict()
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    # 加载关联数据
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.client))
        .where(Project.id == project.id)
    )
    project = result.scalar_one()
    
    return project

@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    project_type: Optional[str] = Query(None, description="项目类型"),
    status_filter: Optional[str] = Query(None, description="项目状态"),
    min_budget: Optional[float] = Query(None, description="最小预算"),
    max_budget: Optional[float] = Query(None, description="最大预算"),
    skill_ids: Optional[List[str]] = Query(None, description="技能ID列表"),
    location_preference: Optional[str] = Query(None, description="地点偏好"),
    is_urgent: Optional[bool] = Query(None, description="是否紧急"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取项目列表
    
    支持按类型、状态、预算、技能等条件筛选
    """
    # 构建查询
    query_builder = select(Project).where(Project.status.in_(["OPEN", "IN_PROGRESS"]))
    
    # 类型过滤
    if project_type:
        query_builder = query_builder.where(Project.project_type == project_type)
    
    # 状态过滤
    if status_filter:
        query_builder = query_builder.where(Project.status == status_filter)
    
    # 预算过滤
    if min_budget is not None:
        query_builder = query_builder.where(Project.budget_max >= min_budget)
    
    if max_budget is not None:
        query_builder = query_builder.where(Project.budget_min <= max_budget)
    
    # 技能过滤
    if skill_ids:
        # 这里需要JSON查询，SQLite可能不支持，PostgreSQL支持
        # 简化处理：检查required_skills是否包含任一指定技能
        pass
    
    # 地点偏好过滤
    if location_preference:
        query_builder = query_builder.where(
            or_(
                Project.location_preference == location_preference,
                Project.location_preference == "ANY"
            )
        )
    
    # 紧急项目过滤
    if is_urgent is not None:
        query_builder = query_builder.where(Project.is_urgent == is_urgent)
    
    # 按创建时间倒序
    query_builder = query_builder.order_by(Project.created_at.desc())
    
    # 计算总数
    count_result = await db.execute(query_builder)
    total = len(count_result.scalars().all())
    
    # 分页
    offset = (page - 1) * page_size
    query_builder = query_builder.offset(offset).limit(page_size)
    
    # 执行查询
    result = await db.execute(query_builder)
    projects = result.scalars().all()
    
    # 加载关联数据
    project_ids = [p.id for p in projects]
    if project_ids:
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.client))
            .where(Project.id.in_(project_ids))
            .order_by(Project.created_at.desc())
        )
        projects = result.scalars().all()
    
    return {
        "projects": projects,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/my-projects", response_model=ProjectListResponse)
async def get_my_projects(
    status_filter: Optional[str] = Query(None, description="项目状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取当前用户发布的项目（仅限需求方）"""
    # 获取需求方资料
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == current_user.id)
    )
    client_profile = result.scalar_one_or_none()
    
    if not client_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="需求方资料不存在"
        )
    
    # 构建查询
    query_builder = select(Project).where(Project.client_id == client_profile.id)
    
    # 状态过滤
    if status_filter:
        query_builder = query_builder.where(Project.status == status_filter)
    
    # 按创建时间倒序
    query_builder = query_builder.order_by(Project.created_at.desc())
    
    # 计算总数
    count_result = await db.execute(query_builder)
    total = len(count_result.scalars().all())
    
    # 分页
    offset = (page - 1) * page_size
    query_builder = query_builder.offset(offset).limit(page_size)
    
    # 执行查询
    result = await db.execute(query_builder)
    projects = result.scalars().all()
    
    return {
        "projects": projects,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取项目详情"""
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.client),
            selectinload(Project.milestones),
            selectinload(Project.matches).selectinload(Match.provider),
            selectinload(Project.proposals).selectinload(Proposal.provider)
        )
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """更新项目（仅限项目发布者）"""
    # 获取项目
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查权限
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == current_user.id)
    )
    client_profile = result.scalar_one_or_none()
    
    if not client_profile or project.client_id != client_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此项目"
        )
    
    # 更新项目
    for field, value in project_data.dict(exclude_unset=True).items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    
    return project

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """删除项目（仅限项目发布者）"""
    # 获取项目
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查权限
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == current_user.id)
    )
    client_profile = result.scalar_one_or_none()
    
    if not client_profile or project.client_id != client_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权刪除此项目"
        )
    
    # 只能删除草稿状态的项目
    if project.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能删除草稿状态的项目"
        )
    
    # 删除项目
    await db.delete(project)
    await db.commit()
    
    return {"message": "项目已删除"}

@router.post("/{project_id}/publish")
async def publish_project(
    project_id: str,
    current_user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """发布项目（将草稿状态改为开放状态）"""
    # 获取项目
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查权限
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == current_user.id)
    )
    client_profile = result.scalar_one_or_none()
    
    if not client_profile or project.client_id != client_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权发布此项目"
        )
    
    # 只能发布草稿状态的项目
    if project.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能发布草稿状态的项目"
        )
    
    # 发布项目
    project.status = "OPEN"
    await db.commit()
    
    return {"message": "项目已发布"}

@router.post("/{project_id}/milestones", response_model=ProjectMilestoneResponse)
async def add_project_milestone(
    project_id: str,
    milestone_data: ProjectMilestoneCreate,
    current_user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """添加项目里程碑"""
    # 获取项目
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查权限
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == current_user.id)
    )
    client_profile = result.scalar_one_or_none()
    
    if not client_profile or project.client_id != client_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权添加里程碑"
        )
    
    # 创建里程碑
    milestone = ProjectMilestone(
        project_id=project_id,
        **milestone_data.dict()
    )
    db.add(milestone)
    await db.commit()
    await db.refresh(milestone)
    
    return milestone

@router.get("/{project_id}/matches", response_model=List[dict])
async def get_project_matches(
    project_id: str,
    current_user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取项目的匹配推荐"""
    # 获取项目
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查权限
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == current_user.id)
    )
    client_profile = result.scalar_one_or_none()
    
    if not client_profile or project.client_id != client_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看匹配推荐"
        )
    
    # 获取匹配的供给方
    # 这里简化处理，实际应该使用匹配算法
    result = await db.execute(
        select(ProviderProfile)
        .options(selectinload(ProviderProfile.skills).selectinload(ProviderSkill.skill))
        .where(ProviderProfile.availability == "AVAILABLE")
        .limit(10)
    )
    providers = result.scalars().all()
    
    # 构建匹配结果
    matches = []
    for provider in providers:
        # 计算简单的匹配分数
        match_score = calculate_simple_match_score(project, provider)
        
        matches.append({
            "provider_id": str(provider.id),
            "provider_name": provider.user.full_name if provider.user else "未知",
            "professional_title": provider.professional_title,
            "hourly_rate": float(provider.hourly_rate),
            "match_score": match_score,
            "skills": [ps.skill.name for ps in provider.skills] if provider.skills else []
        })
    
    # 按匹配分数排序
    matches.sort(key=lambda x: x["match_score"], reverse=True)
    
    return matches

def calculate_simple_match_score(project: Project, provider: ProviderProfile) -> float:
    """计算简单的匹配分数"""
    score = 0.0
    
    # 预算匹配（30%）
    if project.budget_min and project.budget_max and provider.hourly_rate:
        # 假设项目预算是小时费率的100倍
        estimated_hours = project.budget_max / provider.hourly_rate if provider.hourly_rate > 0 else 0
        if 20 <= estimated_hours <= 200:  # 合理的工时范围
            score += 30
    
    # 技能匹配（40%）
    if project.required_skills and provider.skills:
        project_skills = set(project.required_skills)
        provider_skills = set(str(ps.skill_id) for ps in provider.skills)
        skill_match_ratio = len(project_skills.intersection(provider_skills)) / len(project_skills) if project_skills else 0
        score += skill_match_ratio * 40
    
    # 经验匹配（20%）
    if project.preferred_experience and provider.years_of_experience:
        experience_map = {"JUNIOR": 1, "MID": 3, "SENIOR": 5, "EXPERT": 8}
        required_exp = experience_map.get(project.preferred_experience, 0)
        if provider.years_of_experience >= required_exp:
            score += 20
    
    # 可用性（10%）
    if provider.availability == "AVAILABLE":
        score += 10
    
    return min(score, 100.0)

@router.get("/stats/overview", response_model=ProjectStats)
async def get_project_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取项目统计信息"""
    # 总项目数
    result = await db.execute(select(func.count(Project.id)))
    total_projects = result.scalar()
    
    # 开放项目数
    result = await db.execute(
        select(func.count(Project.id)).where(Project.status == "OPEN")
    )
    open_projects = result.scalar()
    
    # 进行中项目数
    result = await db.execute(
        select(func.count(Project.id)).where(Project.status == "IN_PROGRESS")
    )
    in_progress_projects = result.scalar()
    
    # 已完成项目数
    result = await db.execute(
        select(func.count(Project.id)).where(Project.status == "COMPLETED")
    )
    completed_projects = result.scalar()
    
    # 总预算金额
    result = await db.execute(
        select(func.sum(Project.budget_max)).where(Project.status.in_(["OPEN", "IN_PROGRESS"]))
    )
    total_budget = result.scalar() or 0
    
    # 平均项目预算
    result = await db.execute(
        select(func.avg((Project.budget_min + Project.budget_max) / 2))
        .where(Project.status.in_(["OPEN", "IN_PROGRESS"]))
    )
    average_budget = result.scalar() or 0
    
    return {
        "total_projects": total_projects,
        "open_projects": open_projects,
        "in_progress_projects": in_progress_projects,
        "completed_projects": completed_projects,
        "total_budget": float(total_budget),
        "average_budget": float(average_budget)
    }