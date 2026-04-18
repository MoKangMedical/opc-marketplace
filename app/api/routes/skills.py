"""
OPC Marketplace - 技能路由
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.project import Skill
from app.schemas.project import SkillCreate, SkillUpdate, SkillResponse

router = APIRouter()

@router.get("/", response_model=List[SkillResponse])
async def list_skills(
    category: Optional[str] = Query(None, description="技能分类"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取技能列表
    
    支持按分类和关键词搜索
    """
    # 构建查询
    query_builder = select(Skill)
    
    # 分类过滤
    if category:
        query_builder = query_builder.where(Skill.category == category)
    
    # 关键词搜索
    if search:
        query_builder = query_builder.where(
            or_(
                Skill.name.ilike(f"%{search}%"),
                Skill.description.ilike(f"%{search}%")
            )
        )
    
    # 按名称排序
    query_builder = query_builder.order_by(Skill.name)
    
    # 分页
    offset = (page - 1) * page_size
    query_builder = query_builder.offset(offset).limit(page_size)
    
    # 执行查询
    result = await db.execute(query_builder)
    skills = result.scalars().all()
    
    return skills

@router.get("/categories", response_model=List[str])
async def get_skill_categories(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取所有技能分类"""
    result = await db.execute(
        select(Skill.category)
        .distinct()
        .order_by(Skill.category)
    )
    categories = [row[0] for row in result.fetchall()]
    
    return categories

@router.post("/", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    创建新技能
    
    - **name**: 技能名称
    - **category**: 技能分类
    - **description**: 技能描述（可选）
    """
    # 检查技能是否已存在
    result = await db.execute(select(Skill).where(Skill.name == skill_data.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="技能已存在"
        )
    
    # 创建技能
    skill = Skill(**skill_data.dict())
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    
    return skill

@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取技能详情"""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="技能不存在"
        )
    
    return skill

@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    skill_data: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """更新技能"""
    # 获取技能
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="技能不存在"
        )
    
    # 检查名称是否重复
    if skill_data.name and skill_data.name != skill.name:
        result = await db.execute(select(Skill).where(Skill.name == skill_data.name))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="技能名称已存在"
            )
    
    # 更新技能
    for field, value in skill_data.dict(exclude_unset=True).items():
        setattr(skill, field, value)
    
    await db.commit()
    await db.refresh(skill)
    
    return skill

@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """删除技能"""
    # 获取技能
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="技能不存在"
        )
    
    # 检查是否有关联的供给方
    from app.models.user import ProviderSkill
    result = await db.execute(
        select(ProviderSkill).where(ProviderSkill.skill_id == skill_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该技能已被使用，无法删除"
        )
    
    # 删除技能
    await db.delete(skill)
    await db.commit()
    
    return {"message": "技能已删除"}

@router.get("/{skill_id}/providers", response_model=List[dict])
async def get_skill_providers(
    skill_id: str,
    min_proficiency: Optional[str] = Query(None, description="最低熟练度"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取掌握该技能的供给方列表"""
    # 检查技能是否存在
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="技能不存在"
        )
    
    # 构建查询
    from app.models.user import ProviderProfile, ProviderSkill
    query_builder = (
        select(ProviderProfile)
        .join(ProviderSkill, ProviderProfile.id == ProviderSkill.provider_id)
        .where(ProviderSkill.skill_id == skill_id)
    )
    
    # 熟练度过滤
    proficiency_map = {"BEGINNER": 1, "INTERMEDIATE": 2, "ADVANCED": 3, "EXPERT": 4}
    if min_proficiency:
        min_level = proficiency_map.get(min_proficiency, 0)
        query_builder = query_builder.where(
            ProviderSkill.proficiency_level.in_([
                level for level, value in proficiency_map.items() 
                if value >= min_level
            ])
        )
    
    # 分页
    offset = (page - 1) * page_size
    query_builder = query_builder.offset(offset).limit(page_size)
    
    # 执行查询
    result = await db.execute(query_builder)
    providers = result.scalars().all()
    
    # 构建返回结果
    provider_list = []
    for provider in providers:
        # 获取该技能的熟练度
        result = await db.execute(
            select(ProviderSkill)
            .where(
                ProviderSkill.provider_id == provider.id,
                ProviderSkill.skill_id == skill_id
            )
        )
        provider_skill = result.scalar_one_or_none()
        
        provider_list.append({
            "provider_id": str(provider.id),
            "professional_title": provider.professional_title,
            "proficiency_level": provider_skill.proficiency_level if provider_skill else None,
            "years_of_experience": provider_skill.years_of_experience if provider_skill else None,
            "hourly_rate": float(provider.hourly_rate),
            "availability": provider.availability
        })
    
    return provider_list

@router.post("/bulk", response_model=List[SkillResponse])
async def create_skills_bulk(
    skills_data: List[SkillCreate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    批量创建技能
    
    - **skills**: 技能列表
    """
    created_skills = []
    
    for skill_data in skills_data:
        # 检查技能是否已存在
        result = await db.execute(select(Skill).where(Skill.name == skill_data.name))
        existing_skill = result.scalar_one_or_none()
        
        if existing_skill:
            # 如果已存在，添加到结果中
            created_skills.append(existing_skill)
        else:
            # 创建新技能
            skill = Skill(**skill_data.dict())
            db.add(skill)
            await db.flush()
            created_skills.append(skill)
    
    await db.commit()
    
    # 刷新所有技能
    for skill in created_skills:
        await db.refresh(skill)
    
    return created_skills

@router.get("/popular/list", response_model=List[dict])
async def get_popular_skills(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取热门技能"""
    from app.models.user import ProviderSkill
    from sqlalchemy import func
    
    # 统计每个技能的供给方数量
    result = await db.execute(
        select(
            Skill.id,
            Skill.name,
            Skill.category,
            func.count(ProviderSkill.provider_id).label("provider_count")
        )
        .outerjoin(ProviderSkill, Skill.id == ProviderSkill.skill_id)
        .group_by(Skill.id, Skill.name, Skill.category)
        .order_by(func.count(ProviderSkill.provider_id).desc())
        .limit(limit)
    )
    
    popular_skills = []
    for row in result.fetchall():
        popular_skills.append({
            "skill_id": str(row[0]),
            "name": row[1],
            "category": row[2],
            "provider_count": row[3]
        })
    
    return popular_skills