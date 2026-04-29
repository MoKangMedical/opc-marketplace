"""
OPC Marketplace - 认证路由
"""

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, decode_token, validate_password_strength
)
from app.models.user import User, ClientProfile, ProviderProfile
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, Token, TokenRefresh,
    PasswordReset, PasswordResetConfirm, PasswordChange
)

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    用户注册
    
    - **email**: 邮箱地址
    - **password**: 密码（至少8位，包含大小写字母和数字）
    - **full_name**: 全名
    - **user_type**: 用户类型（CLIENT或PROVIDER）
    """
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册"
        )
    
    # 验证密码强度
    if not validate_password_strength(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码强度不足，需要至少8位，包含大小写字母和数字"
        )
    
    # 创建用户
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        user_type=user_data.user_type
    )
    db.add(user)
    await db.flush()
    
    # 创建对应的用户资料
    if user_data.user_type == "CLIENT":
        client_profile = ClientProfile(
            user_id=user.id,
            industry=user_data.industry or "其他",
            company_name=user_data.company_name
        )
        db.add(client_profile)
    elif user_data.user_type == "PROVIDER":
        provider_profile = ProviderProfile(
            user_id=user.id,
            professional_title=user_data.professional_title or "自由职业者",
            bio=user_data.bio or "",
            years_of_experience=user_data.years_of_experience or 0,
            hourly_rate=user_data.hourly_rate or 0
        )
        db.add(provider_profile)
    
    await db.commit()
    await db.refresh(user)
    
    return user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    用户登录
    
    - **username**: 邮箱地址
    - **password**: 密码
    """
    # 验证用户
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    
    # 创建访问令牌和刷新令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    刷新访问令牌
    
    - **refresh_token**: 刷新令牌
    """
    # 解码刷新令牌
    payload = decode_token(token_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    # 获取用户
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )
    
    # 创建新的令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }

@router.post("/password-reset")
async def request_password_reset(
    password_reset: PasswordReset,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    请求密码重置
    
    - **email**: 注册邮箱
    """
    # 检查用户是否存在
    result = await db.execute(select(User).where(User.email == password_reset.email))
    user = result.scalar_one_or_none()
    
    if not user:
        # 为了安全，即使用户不存在也返回成功
        return {"message": "如果该邮箱已注册，您将收到密码重置邮件"}
    
    # TODO: 发送密码重置邮件
    # 这里应该发送包含重置链接的邮件
    
    return {"message": "如果该邮箱已注册，您将收到密码重置邮件"}

@router.post("/password-reset/confirm")
async def confirm_password_reset(
    password_reset_confirm: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    确认密码重置
    
    - **token**: 重置令牌
    - **new_password**: 新密码
    """
    # 验证令牌
    from app.core.security import verify_password_reset_token
    email = verify_password_reset_token(password_reset_confirm.token)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效或过期的重置令牌"
        )
    
    # 获取用户
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户不存在"
        )
    
    # 验证新密码强度
    if not validate_password_strength(password_reset_confirm.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码强度不足"
        )
    
    # 更新密码
    user.hashed_password = get_password_hash(password_reset_confirm.new_password)
    await db.commit()
    
    return {"message": "密码重置成功"}

@router.post("/password-change")
async def change_password(
    password_change: PasswordChange,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    修改密码（需要登录）
    
    - **current_password**: 当前密码
    - **new_password**: 新密码
    """
    # 获取当前用户（需要登录）
    from app.core.security import get_current_user
    from fastapi import Depends
    
    # 注意：这个端点需要在路由中添加认证依赖
    # 这里简化处理，实际应该通过依赖注入获取当前用户
    return {"message": "密码修改功能需要在路由中添加认证依赖"}