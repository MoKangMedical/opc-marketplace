"""揭榜挂帅 - 政府项目API"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.models.models import GovProject, GovProjectApplication, User, GovProjectStatus

router = APIRouter()


class GovProjectResponse(BaseModel):
    id: int
    title: str
    description: str
    publisher: str
    publisher_contact: str
    industry: str
    tags: List[str]
    budget_min: int
    budget_max: int
    deadline: Optional[str]
    tech_requirements: Optional[str]
    required_skills: List[str]
    status: str
    is_featured: bool
    view_count: int
    application_count: int
    created_at: str
    days_left: Optional[int] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[GovProjectResponse])
async def list_gov_projects(
    industry: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    budget_min: Optional[int] = None,
    sort: str = "deadline",
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """获取揭榜挂帅项目列表"""
    query = select(GovProject)
    
    if industry:
        query = query.where(GovProject.industry == industry)
    if status:
        query = query.where(GovProject.status == status)
    if budget_min:
        query = query.where(GovProject.budget_max >= budget_min)
    if search:
        query = query.where(
            or_(
                GovProject.title.contains(search),
                GovProject.description.contains(search),
                GovProject.publisher.contains(search),
            )
        )
    
    # 排序
    if sort == "deadline":
        query = query.order_by(GovProject.deadline.asc())
    elif sort == "budget":
        query = query.order_by(GovProject.budget_max.desc())
    elif sort == "newest":
        query = query.order_by(GovProject.created_at.desc())
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    projects = result.scalars().all()
    
    now = datetime.utcnow()
    response = []
    for p in projects:
        days_left = None
        if p.deadline:
            delta = p.deadline - now
            days_left = delta.days
        
        response.append(GovProjectResponse(
            id=p.id,
            title=p.title,
            description=p.description,
            publisher=p.publisher,
            publisher_contact=p.publisher_contact,
            industry=p.industry,
            tags=p.tags or [],
            budget_min=p.budget_min,
            budget_max=p.budget_max,
            deadline=p.deadline.isoformat() if p.deadline else None,
            tech_requirements=p.tech_requirements,
            required_skills=p.required_skills or [],
            status=p.status.value,
            is_featured=p.is_featured,
            view_count=p.view_count,
            application_count=p.application_count,
            created_at=p.created_at.isoformat(),
            days_left=days_left,
        ))
    
    return response


@router.get("/stats")
async def gov_project_stats(db: AsyncSession = Depends(get_db)):
    """揭榜挂帅统计数据"""
    total = await db.execute(select(func.count(GovProject.id)))
    total_count = total.scalar()
    
    budget_sum = await db.execute(select(func.sum(GovProject.budget_max)))
    total_budget = budget_sum.scalar() or 0
    
    industries = await db.execute(
        select(GovProject.industry, func.count(GovProject.id))
        .group_by(GovProject.industry)
    )
    
    publishers = await db.execute(
        select(func.count(GovProject.publisher.distinct()))
    )
    
    now = datetime.utcnow()
    deadline_result = await db.execute(
        select(GovProject).where(GovProject.deadline != None)
    )
    all_projects = deadline_result.scalars().all()
    
    recruiting = sum(1 for p in all_projects if p.deadline and p.deadline > now)
    expired = sum(1 for p in all_projects if p.deadline and p.deadline <= now)
    
    return {
        "total_projects": total_count,
        "total_budget": f"{total_budget // 1000}万" if total_budget >= 1000 else f"{total_budget}万",
        "total_budget_raw": total_budget,
        "industries_count": len(industries.all()),
        "publishers_count": publishers.scalar(),
        "recruiting": recruiting,
        "expired": expired,
        "by_industry": {row[0]: row[1] for row in industries.all()},
    }


@router.get("/{project_id}")
async def get_gov_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """获取揭榜挂帅项目详情"""
    project = await db.get(GovProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 增加浏览量
    project.view_count += 1
    await db.commit()
    
    now = datetime.utcnow()
    days_left = (project.deadline - now).days if project.deadline else None
    
    # 获取申请列表
    apps_result = await db.execute(
        select(GovProjectApplication).where(
            GovProjectApplication.project_id == project_id
        )
    )
    applications = apps_result.scalars().all()
    
    return {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "publisher": project.publisher,
        "publisher_contact": project.publisher_contact,
        "industry": project.industry,
        "tags": project.tags or [],
        "budget_min": project.budget_min,
        "budget_max": project.budget_max,
        "deadline": project.deadline.isoformat() if project.deadline else None,
        "days_left": days_left,
        "deadline_status": "已截止" if days_left and days_left < 0 else (
            f"还剩{days_left}天" if days_left and days_left <= 30 else None
        ),
        "tech_requirements": project.tech_requirements,
        "required_skills": project.required_skills or [],
        "status": project.status.value,
        "is_featured": project.is_featured,
        "view_count": project.view_count,
        "application_count": project.application_count,
        "applications_summary": [
            {
                "id": a.id,
                "team_name": a.team_name,
                "status": a.status,
                "score": a.score,
            }
            for a in applications
        ],
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


@router.post("/{project_id}/apply")
async def apply_gov_project(
    project_id: int,
    applicant_id: int,
    team_name: str,
    proposal: str,
    proposed_budget: int,
    tech_approach: str = "",
    db: AsyncSession = Depends(get_db),
):
    """申报揭榜挂帅项目"""
    project = await db.get(GovProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    now = datetime.utcnow()
    if project.deadline and project.deadline < now:
        raise HTTPException(status_code=400, detail="项目申报已截止")
    
    # 检查是否重复申报
    existing = await db.execute(
        select(GovProjectApplication).where(
            GovProjectApplication.project_id == project_id,
            GovProjectApplication.applicant_id == applicant_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="您已申报过此项目")
    
    application = GovProjectApplication(
        project_id=project_id,
        applicant_id=applicant_id,
        team_name=team_name,
        proposal=proposal,
        proposed_budget=proposed_budget,
        tech_approach=tech_approach,
        status="submitted",
    )
    db.add(application)
    project.application_count += 1
    await db.commit()
    
    return {
        "message": "申报成功",
        "application_id": application.id,
        "project_title": project.title,
        "deadline": project.deadline.isoformat() if project.deadline else None,
    }


@router.get("/industries/list")
async def list_industries(db: AsyncSession = Depends(get_db)):
    """获取所有行业分类"""
    result = await db.execute(
        select(GovProject.industry, func.count(GovProject.id))
        .group_by(GovProject.industry)
    )
    return {row[0]: row[1] for row in result.all()}
