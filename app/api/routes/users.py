"""用户管理API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.models.models import User, UserRole

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "both"
    display_name: Optional[str] = None
    company: Optional[str] = None
    bio: Optional[str] = None
    skills: List[str] = []
    industries: List[str] = []
    location: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    display_name: Optional[str]
    company: Optional[str]
    bio: Optional[str]
    skills: List[str]
    industries: List[str]
    location: Optional[str]
    rating: float
    rating_count: int
    is_verified: bool
    created_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[UserResponse])
async def list_users(
    role: Optional[str] = None,
    industry: Optional[str] = None,
    skill: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """获取用户列表，支持按角色、行业、技能筛选"""
    query = select(User).where(User.is_active == True)
    
    if role:
        query = query.where(User.role == role)
    if industry:
        query = query.where(User.industries.contains([industry]))
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            role=u.role.value,
            display_name=u.display_name,
            company=u.company,
            bio=u.bio,
            skills=u.skills or [],
            industries=u.industries or [],
            location=u.location,
            rating=u.rating,
            rating_count=u.rating_count,
            is_verified=u.is_verified,
            created_at=u.created_at.isoformat(),
        )
        for u in users
    ]


@router.get("/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """获取用户详情"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "company": user.company,
        "bio": user.bio,
        "skills": user.skills or [],
        "industries": user.industries or [],
        "location": user.location,
        "rating": user.rating,
        "rating_count": user.rating_count,
        "is_verified": user.is_verified,
    }


@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """注册新用户"""
    # 检查用户名和邮箱是否已存在
    existing = await db.execute(
        select(User).where(
            (User.username == user_data.username) | (User.email == user_data.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=user_data.password,  # 实际应用中需要hash
        role=UserRole(user_data.role),
        display_name=user_data.display_name,
        company=user_data.company,
        bio=user_data.bio,
        skills=user_data.skills,
        industries=user_data.industries,
        location=user_data.location,
        phone=user_data.phone,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        display_name=user.display_name,
        company=user.company,
        bio=user.bio,
        skills=user.skills or [],
        industries=user.industries or [],
        location=user.location,
        rating=user.rating,
        rating_count=user.rating_count,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat(),
    )
