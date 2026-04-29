"""项目管理API"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.models.models import Project, ProjectApplication, User, ProjectStatus

router = APIRouter()


class ProjectCreate(BaseModel):
    title: str
    description: str
    category: str
    industry: str
    demander_id: int
    budget_min: int
    budget_max: int
    deadline: Optional[str] = None
    required_skills: List[str] = []
    is_urgent: bool = False


class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    industry: str
    demander_id: int
    demander_name: Optional[str] = None
    demander_company: Optional[str] = None
    supplier_id: Optional[int] = None
    budget_min: int
    budget_max: int
    deadline: Optional[str] = None
    required_skills: List[str]
    status: str
    is_urgent: bool
    is_featured: bool
    view_count: int
    application_count: int
    created_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    category: Optional[str] = None,
    industry: Optional[str] = None,
    status: Optional[str] = None,
    is_urgent: Optional[bool] = None,
    budget_min: Optional[int] = None,
    budget_max: Optional[int] = None,
    search: Optional[str] = None,
    sort: str = "newest",
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """获取项目列表，支持多维度筛选"""
    query = select(Project)
    
    if category:
        query = query.where(Project.category == category)
    if industry:
        query = query.where(Project.industry == industry)
    if status:
        query = query.where(Project.status == status)
    if is_urgent is not None:
        query = query.where(Project.is_urgent == is_urgent)
    if budget_min:
        query = query.where(Project.budget_max >= budget_min)
    if budget_max:
        query = query.where(Project.budget_min <= budget_max)
    if search:
        query = query.where(
            or_(
                Project.title.contains(search),
                Project.description.contains(search),
            )
        )
    
    # 排序
    if sort == "newest":
        query = query.order_by(Project.created_at.desc())
    elif sort == "budget_high":
        query = query.order_by(Project.budget_max.desc())
    elif sort == "budget_low":
        query = query.order_by(Project.budget_min.asc())
    elif sort == "deadline":
        query = query.order_by(Project.deadline.asc())
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    projects = result.scalars().all()
    
    # 获取需求方信息
    response = []
    for p in projects:
        demander = await db.get(User, p.demander_id) if p.demander_id else None
        response.append(ProjectResponse(
            id=p.id,
            title=p.title,
            description=p.description,
            category=p.category,
            industry=p.industry,
            demander_id=p.demander_id,
            demander_name=demander.display_name if demander else None,
            demander_company=demander.company if demander else None,
            supplier_id=p.supplier_id,
            budget_min=p.budget_min,
            budget_max=p.budget_max,
            deadline=p.deadline.isoformat() if p.deadline else None,
            required_skills=p.required_skills or [],
            status=p.status.value,
            is_urgent=p.is_urgent,
            is_featured=p.is_featured,
            view_count=p.view_count,
            application_count=p.application_count,
            created_at=p.created_at.isoformat(),
        ))
    
    return response


@router.get("/stats")
async def project_stats(db: AsyncSession = Depends(get_db)):
    """项目统计数据"""
    total = await db.execute(select(func.count(Project.id)))
    total_count = total.scalar()
    
    open_count = await db.execute(
        select(func.count(Project.id)).where(Project.status == ProjectStatus.OPEN)
    )
    
    budget_sum = await db.execute(select(func.sum(Project.budget_max)))
    total_budget = budget_sum.scalar() or 0
    
    industries = await db.execute(
        select(Project.industry, func.count(Project.id))
        .group_by(Project.industry)
    )
    
    return {
        "total_projects": total_count,
        "open_projects": open_count.scalar(),
        "total_budget": total_budget,
        "industries": {row[0]: row[1] for row in industries.all()},
    }


@router.get("/{project_id}")
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """获取项目详情"""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 增加浏览量
    project.view_count += 1
    await db.commit()
    
    demander = await db.get(User, project.demander_id) if project.demander_id else None
    supplier = await db.get(User, project.supplier_id) if project.supplier_id else None
    
    return {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "category": project.category,
        "industry": project.industry,
        "demander": {
            "id": demander.id,
            "name": demander.display_name,
            "company": demander.company,
            "rating": demander.rating,
        } if demander else None,
        "supplier": {
            "id": supplier.id,
            "name": supplier.display_name,
            "company": supplier.company,
        } if supplier else None,
        "budget_min": project.budget_min,
        "budget_max": project.budget_max,
        "deadline": project.deadline.isoformat() if project.deadline else None,
        "required_skills": project.required_skills or [],
        "status": project.status.value,
        "is_urgent": project.is_urgent,
        "is_featured": project.is_featured,
        "view_count": project.view_count,
        "application_count": project.application_count,
        "created_at": project.created_at.isoformat(),
    }


@router.post("/", response_model=ProjectResponse)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """发布新项目"""
    project = Project(
        title=data.title,
        description=data.description,
        category=data.category,
        industry=data.industry,
        demander_id=data.demander_id,
        budget_min=data.budget_min,
        budget_max=data.budget_max,
        deadline=datetime.fromisoformat(data.deadline) if data.deadline else None,
        required_skills=data.required_skills,
        is_urgent=data.is_urgent,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        title=project.title,
        description=project.description,
        category=project.category,
        industry=project.industry,
        demander_id=project.demander_id,
        budget_min=project.budget_min,
        budget_max=project.budget_max,
        deadline=project.deadline.isoformat() if project.deadline else None,
        required_skills=project.required_skills or [],
        status=project.status.value,
        is_urgent=project.is_urgent,
        is_featured=project.is_featured,
        view_count=0,
        application_count=0,
        created_at=project.created_at.isoformat(),
    )


@router.post("/{project_id}/apply")
async def apply_project(
    project_id: int,
    applicant_id: int,
    proposal: str,
    proposed_budget: int,
    db: AsyncSession = Depends(get_db),
):
    """申请承接项目"""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    application = ProjectApplication(
        project_id=project_id,
        applicant_id=applicant_id,
        proposal=proposal,
        proposed_budget=proposed_budget,
    )
    db.add(application)
    project.application_count += 1
    await db.commit()
    
    return {"message": "申请成功", "application_id": application.id}
