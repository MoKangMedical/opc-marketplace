"""智能匹配API - 多维度供需匹配"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import json

from app.core.database import get_db
from app.models.models import User, Project, Match, MatchStatus

router = APIRouter()


def calculate_match_score(user: User, project: Project) -> dict:
    """计算用户与项目的匹配度（多维度）"""
    
    # 1. 技能匹配 (35%)
    user_skills = set(user.skills or [])
    required_skills = set(project.required_skills or [])
    if required_skills:
        skill_overlap = len(user_skills & required_skills)
        skill_score = skill_overlap / len(required_skills)
    else:
        skill_score = 0.5
    
    # 2. 行业匹配 (25%)
    user_industries = set(user.industries or [])
    if project.industry:
        industry_score = 1.0 if project.industry in user_industries else 0.3
    else:
        industry_score = 0.5
    
    # 3. 地区匹配 (15%)
    if user.location and project.location_preference:
        location_score = 1.0 if user.location == project.location_preference else 0.5
    else:
        location_score = 0.7
    
    # 4. 信誉评分 (15%)
    reputation_score = user.rating / 5.0
    
    # 5. 经验丰富度 (10%)
    experience_score = min(user.rating_count / 20, 1.0)
    
    # 综合评分
    total_score = (
        skill_score * 0.35 +
        industry_score * 0.25 +
        location_score * 0.15 +
        reputation_score * 0.15 +
        experience_score * 0.10
    )
    
    # 匹配原因
    reasons = []
    if skill_score > 0.7:
        matched = user_skills & required_skills
        reasons.append(f"技能高度匹配：{', '.join(matched)}")
    if industry_score > 0.8:
        reasons.append(f"行业经验匹配：{project.industry}")
    if reputation_score > 0.9:
        reasons.append(f"信誉评分优秀：{user.rating}/5.0")
    
    return {
        "skill_score": round(skill_score, 2),
        "industry_score": round(industry_score, 2),
        "location_score": round(location_score, 2),
        "reputation_score": round(reputation_score, 2),
        "experience_score": round(experience_score, 2),
        "total_score": round(total_score, 2),
        "reasons": reasons,
    }


@router.get("/project/{project_id}")
async def match_project(
    project_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """为项目匹配最佳供给方"""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取所有供给方
    result = await db.execute(
        select(User).where(
            User.is_active == True,
            User.role.in_(["supplier", "both"]),
        )
    )
    suppliers = result.scalars().all()
    
    # 计算匹配度
    matches = []
    for supplier in suppliers:
        score_info = calculate_match_score(supplier, project)
        matches.append({
            "user_id": supplier.id,
            "username": supplier.username,
            "display_name": supplier.display_name,
            "company": supplier.company,
            "skills": supplier.skills or [],
            "location": supplier.location,
            "rating": supplier.rating,
            "rating_count": supplier.rating_count,
            "match_scores": score_info,
        })
    
    # 按综合评分排序
    matches.sort(key=lambda x: x["match_scores"]["total_score"], reverse=True)
    
    return {
        "project_id": project_id,
        "project_title": project.title,
        "total_suppliers": len(suppliers),
        "top_matches": matches[:limit],
    }


@router.get("/user/{user_id}")
async def match_user(
    user_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """为用户匹配最佳项目"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 获取所有开放项目
    result = await db.execute(
        select(Project).where(Project.status == "open")
    )
    projects = result.scalars().all()
    
    matches = []
    for project in projects:
        score_info = calculate_match_score(user, project)
        matches.append({
            "project_id": project.id,
            "title": project.title,
            "industry": project.industry,
            "budget_min": project.budget_min,
            "budget_max": project.budget_max,
            "required_skills": project.required_skills or [],
            "match_scores": score_info,
        })
    
    matches.sort(key=lambda x: x["match_scores"]["total_score"], reverse=True)
    
    return {
        "user_id": user_id,
        "user_name": user.display_name,
        "total_projects": len(projects),
        "top_matches": matches[:limit],
    }


@router.post("/record")
async def record_match(
    project_id: int,
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
):
    """记录匹配结果"""
    project = await db.get(Project, project_id)
    supplier = await db.get(User, supplier_id)
    
    if not project or not supplier:
        raise HTTPException(status_code=404, detail="项目或用户不存在")
    
    score_info = calculate_match_score(supplier, project)
    
    match = Match(
        project_id=project_id,
        supplier_id=supplier_id,
        skill_score=score_info["skill_score"],
        experience_score=score_info["experience_score"],
        budget_score=score_info.get("budget_score", 0.5),
        location_score=score_info["location_score"],
        availability_score=score_info.get("availability_score", 0.5),
        total_score=score_info["total_score"],
        match_reasons=score_info["reasons"],
    )
    db.add(match)
    await db.commit()
    
    return {"message": "匹配记录已保存", "match_id": match.id, "score": score_info["total_score"]}
