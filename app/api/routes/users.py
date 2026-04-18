"""
OPC Marketplace - 用户路由
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user, require_client, require_provider
from app.models.user import User, ClientProfile, ProviderProfile, ProviderSkill, IndustryExpertise
from app.models.project import Skill
from app.schemas.user import (
    UserResponse, UserProfileUpdate, ClientProfileUpdate, ProviderProfileUpdate,
    ProviderSkillCreate, ProviderSkillUpdate, IndustryExpertiseCreate, IndustryExpertiseUpdate,
    UserSearch, UserSearchResponse
)

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取当前用户资料"""
    # 加载关联数据
    if current_user.user_type == "CLIENT":
        result = await db.execute(
            select(User)
            .options(selectinload(User.client_profile))
            .where(User.id == current_user.id)
        )
    else:
        result = await db.execute(
            select(User)
            .options(selectinload(User.provider_profile).selectinload(ProviderProfile.skills))
            .where(User.id == current_user.id)
        )
    
    user = result.scalar_one()
    return user

@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """更新当前用户资料"""
    # 更新用户基本信息
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name
    
    # 更新用户类型特定资料
    if current_user.user_type == "CLIENT" and profile_data.client_profile:
        # 更新需求方资料
        result = await db.execute(
            select(ClientProfile).where(ClientProfile.user_id == current_user.id)
        )
        client_profile = result.scalar_one_or_none()
        
        if client_profile:
            for field, value in profile_data.client_profile.dict(exclude_unset=True).items():
                setattr(client_profile, field, value)
    
    elif current_user.user_type == "PROVIDER" and profile_data.provider_profile:
        # 更新供给方资料
        result = await db.execute(
            select(ProviderProfile).where(ProviderProfile.user_id == current_user.id)
        )
        provider_profile = result.scalar_one_or_none()
        
        if provider_profile:
            for field, value in profile_data.provider_profile.dict(exclude_unset=True).items():
                setattr(provider_profile, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user

@router.get("/me/client-profile", response_model=ClientProfileUpdate)
async def get_client_profile(
    current_user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取需求方资料（仅限需求方）"""
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="需求方资料不存在"
        )
    
    return profile

@router.put("/me/client-profile", response_model=ClientProfileUpdate)
async def update_client_profile(
    profile_data: ClientProfileUpdate,
    current_user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """更新需求方资料（仅限需求方）"""
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        # 创建新资料
        profile = ClientProfile(user_id=current_user.id, **profile_data.dict())
        db.add(profile)
    else:
        # 更新现有资料
        for field, value in profile_data.dict(exclude_unset=True).items():
            setattr(profile, field, value)
    
    await db.commit()
    await db.refresh(profile)
    
    return profile

@router.get("/me/provider-profile", response_model=ProviderProfileUpdate)
async def get_provider_profile(
    current_user: User = Depends(require_provider),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取供给方资料（仅限供给方）"""
    result = await db.execute(
        select(ProviderProfile)
        .options(
            selectinload(ProviderProfile.skills).selectinload(ProviderSkill.skill),
            selectinload(ProviderProfile.industry_expertise)
        )
        .where(ProviderProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供给方资料不存在"
        )
    
    return profile

@router.put("/me/provider-profile", response_model=ProviderProfileUpdate)
async def update_provider_profile(
    profile_data: ProviderProfileUpdate,
    current_user: User = Depends(require_provider),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """更新供给方资料（仅限供给方）"""
    result = await db.execute(
        select(ProviderProfile).where(ProviderProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        # 创建新资料
        profile = ProviderProfile(user_id=current_user.id, **profile_data.dict())
        db.add(profile)
    else:
        # 更新现有资料
        for field, value in profile_data.dict(exclude_unset=True).items():
            setattr(profile, field, value)
    
    await db.commit()
    await db.refresh(profile)
    
    return profile

@router.post("/me/skills", response_model=ProviderSkillUpdate)
async def add_provider_skill(
    skill_data: ProviderSkillCreate,
    current_user: User = Depends(require_provider),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """添加技能（仅限供给方）"""
    # 检查技能是否存在
    result = await db.execute(select(Skill).where(Skill.id == skill_data.skill_id))
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="技能不存在"
        )
    
    # 获取供给方资料
    result = await db.execute(
        select(ProviderProfile).where(ProviderProfile.user_id == current_user.id)
    )
    provider_profile = result.scalar_one_or_none()
    
    if not provider_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供给方资料不存在"
        )
    
    # 检查是否已添加该技能
    result = await db.execute(
        select(ProviderSkill)
        .where(
            ProviderSkill.provider_id == provider_profile.id,
            ProviderSkill.skill_id == skill_data.skill_id
        )
    )
    existing_skill = result.scalar_one_or_none()
    
    if existing_skill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已添加该技能"
        )
    
    # 添加技能
    provider_skill = ProviderSkill(
        provider_id=provider_profile.id,
        **skill_data.dict()
    )
    db.add(provider_skill)
    await db.commit()
    await db.refresh(provider_skill)
    
    return provider_skill

@router.put("/me/skills/{skill_id}", response_model=ProviderSkillUpdate)
async def update_provider_skill(
    skill_id: str,
    skill_data: ProviderSkillUpdate,
    current_user: User = Depends(require_provider),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """更新技能（仅限供给方）"""
    # 获取供给方资料
    result = await db.execute(
        select(ProviderProfile).where(ProviderProfile.user_id == current_user.id)
    )
    provider_profile = result.scalar_one_or_none()
    
    if not provider_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供给方资料不存在"
        )
    
    # 获取技能记录
    result = await db.execute(
        select(ProviderSkill)
        .where(
            ProviderSkill.provider_id == provider_profile.id,
            ProviderSkill.skill_id == skill_id
        )
    )
    provider_skill = result.scalar_one_or_none()
    
    if not provider_skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="技能记录不存在"
        )
    
    # 更新技能
    for field, value in skill_data.dict(exclude_unset=True).items():
        setattr(provider_skill, field, value)
    
    await db.commit()
    await db.refresh(provider_skill)
    
    return provider_skill

@router.delete("/me/skills/{skill_id}")
async def remove_provider_skill(
    skill_id: str,
    current_user: User = Depends(require_provider),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """删除技能（仅限供给方）"""
    # 获取供给方资料
    result = await db.execute(
        select(ProviderProfile).where(ProviderProfile.user_id == current_user.id)
    )
    provider_profile = result.scalar_one_or_none()
    
    if not provider_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供给方资料不存在"
        )
    
    # 获取技能记录
    result = await db.execute(
        select(ProviderSkill)
        .where(
            ProviderSkill.provider_id == provider_profile.id,
            ProviderSkill.skill_id == skill_id
        )
    )
    provider_skill = result.scalar_one_or_none()
    
    if not provider_skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="技能记录不存在"
        )
    
    # 删除技能
    await db.delete(provider_skill)
    await db.commit()
    
    return {"message": "技能已删除"}

@router.post("/me/industry-expertise", response_model=IndustryExpertiseUpdate)
async def add_industry_expertise(
    expertise_data: IndustryExpertiseCreate,
    current_user: User = Depends(require_provider),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """添加行业专长（仅限供给方）"""
    # 获取供给方资料
    result = await db.execute(
        select(ProviderProfile).where(ProviderProfile.user_id == current_user.id)
    )
    provider_profile = result.scalar_one_or_none()
    
    if not provider_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供给方资料不存在"
        )
    
    # 添加行业专长
    industry_expertise = IndustryExpertise(
        provider_id=provider_profile.id,
        **expertise_data.dict()
    )
    db.add(industry_expertise)
    await db.commit()
    await db.refresh(industry_expertise)
    
    return industry_expertise

@router.get("/search", response_model=UserSearchResponse)
async def search_users(
    query: Optional[str] = Query(None, description="搜索关键词"),
    user_type: Optional[str] = Query(None, description="用户类型"),
    skill_ids: Optional[List[str]] = Query(None, description="技能ID列表"),
    min_experience: Optional[int] = Query(None, description="最小经验年限"),
    max_hourly_rate: Optional[float] = Query(None, description="最大小时费率"),
    location: Optional[str] = Query(None, description="地点"),
    availability: Optional[str] = Query(None, description="可用性"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    搜索用户
    
    支持按关键词、用户类型、技能、经验、费率等条件搜索
    """
    # 构建查询
    query_builder = select(User).where(User.is_active == True)
    
    # 用户类型过滤
    if user_type:
        query_builder = query_builder.where(User.user_type == user_type)
    
    # 关键词搜索
    if query:
        query_builder = query_builder.where(
            or_(
                User.full_name.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%")
            )
        )
    
    # 计算总数
    count_result = await db.execute(query_builder)
    total = len(count_result.scalars().all())
    
    # 分页
    offset = (page - 1) * page_size
    query_builder = query_builder.offset(offset).limit(page_size)
    
    # 执行查询
    result = await db.execute(query_builder)
    users = result.scalars().all()
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """根据ID获取用户信息"""
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.client_profile),
            selectinload(User.provider_profile).selectinload(ProviderProfile.skills)
        )
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return user