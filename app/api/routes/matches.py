"""
OPC Marketplace - 匹配路由
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, require_client, require_provider
from app.models.user import User, ClientProfile, ProviderProfile, ProviderSkill
from app.models.project import Project, Match, Proposal, Skill
from app.schemas.project import (
    MatchCreate, MatchUpdate, MatchResponse, MatchListResponse,
    ProposalCreate, ProposalUpdate, ProposalResponse, ProposalListResponse
)
from app.services.matching import MatchingService

router = APIRouter()

@router.post("/", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def create_match(
    match_data: MatchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    创建匹配记录
    
    - **project_id**: 项目ID
    - **provider_id**: 供给方ID
    - **match_score**: 匹配分数（0-100）
    - **match_reasons**: 匹配原因
    """
    # 检查项目是否存在
    result = await db.execute(select(Project).where(Project.id == match_data.project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查供给方是否存在
    result = await db.execute(select(ProviderProfile).where(ProviderProfile.id == match_data.provider_id))
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供给方不存在"
        )
    
    # 检查是否已存在匹配
    result = await db.execute(
        select(Match)
        .where(
            Match.project_id == match_data.project_id,
            Match.provider_id == match_data.provider_id
        )
    )
    existing_match = result.scalar_one_or_none()
    
    if existing_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="匹配记录已存在"
        )
    
    # 创建匹配记录
    match = Match(**match_data.dict())
    db.add(match)
    await db.commit()
    await db.refresh(match)
    
    # 加载关联数据
    result = await db.execute(
        select(Match)
        .options(
            selectinload(Match.project),
            selectinload(Match.provider).selectinload(ProviderProfile.user)
        )
        .where(Match.id == match.id)
    )
    match = result.scalar_one()
    
    return match

@router.get("/", response_model=MatchListResponse)
async def list_matches(
    project_id: Optional[str] = Query(None, description="项目ID"),
    provider_id: Optional[str] = Query(None, description="供给方ID"),
    status_filter: Optional[str] = Query(None, description="匹配状态"),
    min_score: Optional[float] = Query(None, description="最小匹配分数"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取匹配记录列表
    
    支持按项目、供给方、状态、分数等条件筛选
    """
    # 构建查询
    query_builder = select(Match)
    
    # 项目过滤
    if project_id:
        query_builder = query_builder.where(Match.project_id == project_id)
    
    # 供给方过滤
    if provider_id:
        query_builder = query_builder.where(Match.provider_id == provider_id)
    
    # 状态过滤
    if status_filter:
        query_builder = query_builder.where(Match.status == status_filter)
    
    # 分数过滤
    if min_score is not None:
        query_builder = query_builder.where(Match.match_score >= min_score)
    
    # 按匹配分数倒序
    query_builder = query_builder.order_by(Match.match_score.desc())
    
    # 计算总数
    count_result = await db.execute(query_builder)
    total = len(count_result.scalars().all())
    
    # 分页
    offset = (page - 1) * page_size
    query_builder = query_builder.offset(offset).limit(page_size)
    
    # 执行查询
    result = await db.execute(query_builder)
    matches = result.scalars().all()
    
    # 加载关联数据
    match_ids = [m.id for m in matches]
    if match_ids:
        result = await db.execute(
            select(Match)
            .options(
                selectinload(Match.project),
                selectinload(Match.provider).selectinload(ProviderProfile.user)
            )
            .where(Match.id.in_(match_ids))
            .order_by(Match.match_score.desc())
        )
        matches = result.scalars().all()
    
    return {
        "matches": matches,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/my-matches", response_model=MatchListResponse)
async def get_my_matches(
    status_filter: Optional[str] = Query(None, description="匹配状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(require_provider),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取当前供给方的匹配记录"""
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
    
    # 构建查询
    query_builder = select(Match).where(Match.provider_id == provider_profile.id)
    
    # 状态过滤
    if status_filter:
        query_builder = query_builder.where(Match.status == status_filter)
    
    # 按创建时间倒序
    query_builder = query_builder.order_by(Match.created_at.desc())
    
    # 计算总数
    count_result = await db.execute(query_builder)
    total = len(count_result.scalars().all())
    
    # 分页
    offset = (page - 1) * page_size
    query_builder = query_builder.offset(offset).limit(page_size)
    
    # 执行查询
    result = await db.execute(query_builder)
    matches = result.scalars().all()
    
    # 加载关联数据
    match_ids = [m.id for m in matches]
    if match_ids:
        result = await db.execute(
            select(Match)
            .options(selectinload(Match.project))
            .where(Match.id.in_(match_ids))
            .order_by(Match.created_at.desc())
        )
        matches = result.scalars().all()
    
    return {
        "matches": matches,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取匹配记录详情"""
    result = await db.execute(
        select(Match)
        .options(
            selectinload(Match.project),
            selectinload(Match.provider).selectinload(ProviderProfile.user),
            selectinload(Match.proposal)
        )
        .where(Match.id == match_id)
    )
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="匹配记录不存在"
        )
    
    return match

@router.put("/{match_id}", response_model=MatchResponse)
async def update_match(
    match_id: str,
    match_data: MatchUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """更新匹配记录"""
    # 获取匹配记录
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="匹配记录不存在"
        )
    
    # 检查权限
    # 这里简化处理，实际应该检查用户是否是项目发布者或匹配的供给方
    
    # 更新匹配记录
    for field, value in match_data.dict(exclude_unset=True).items():
        setattr(match, field, value)
    
    await db.commit()
    await db.refresh(match)
    
    return match

@router.post("/{match_id}/accept")
async def accept_match(
    match_id: str,
    current_user: User = Depends(require_provider),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """接受匹配（仅限供给方）"""
    # 获取匹配记录
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="匹配记录不存在"
        )
    
    # 获取供给方资料
    result = await db.execute(
        select(ProviderProfile).where(ProviderProfile.user_id == current_user.id)
    )
    provider_profile = result.scalar_one_or_none()
    
    if not provider_profile or match.provider_id != provider_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此匹配记录"
        )
    
    # 更新匹配状态
    match.status = "ACCEPTED"
    await db.commit()
    
    return {"message": "匹配已接受"}

@router.post("/{match_id}/reject")
async def reject_match(
    match_id: str,
    current_user: User = Depends(require_provider),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """拒绝匹配（仅限供给方）"""
    # 获取匹配记录
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="匹配记录不存在"
        )
    
    # 获取供给方资料
    result = await db.execute(
        select(ProviderProfile).where(ProviderProfile.user_id == current_user.id)
    )
    provider_profile = result.scalar_one_or_none()
    
    if not provider_profile or match.provider_id != provider_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此匹配记录"
        )
    
    # 更新匹配状态
    match.status = "REJECTED"
    await db.commit()
    
    return {"message": "匹配已拒绝"}

@router.post("/{match_id}/proposal", response_model=ProposalResponse)
async def create_proposal(
    match_id: str,
    proposal_data: ProposalCreate,
    current_user: User = Depends(require_provider),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """创建提案（仅限供给方）"""
    # 获取匹配记录
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="匹配记录不存在"
        )
    
    # 获取供给方资料
    result = await db.execute(
        select(ProviderProfile).where(ProviderProfile.user_id == current_user.id)
    )
    provider_profile = result.scalar_one_or_none()
    
    if not provider_profile or match.provider_id != provider_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此匹配记录"
        )
    
    # 检查是否已存在提案
    if match.proposal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已存在提案"
        )
    
    # 创建提案
    proposal = Proposal(
        match_id=match_id,
        provider_id=provider_profile.id,
        project_id=match.project_id,
        **proposal_data.dict()
    )
    db.add(proposal)
    
    # 更新匹配状态
    match.status = "PROPOSED"
    
    await db.commit()
    await db.refresh(proposal)
    
    return proposal

@router.post("/auto-match/{project_id}", response_model=List[dict])
async def auto_match_project(
    project_id: str,
    current_user: User = Depends(require_client),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """自动匹配项目（仅限需求方）"""
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
            detail="无权操作此项目"
        )
    
    # 使用匹配服务进行自动匹配
    matching_service = MatchingService(db)
    matches = await matching_service.auto_match_project(project)
    
    return matches

@router.get("/stats/overview")
async def get_match_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取匹配统计信息"""
    # 总匹配数
    result = await db.execute(select(func.count(Match.id)))
    total_matches = result.scalar()
    
    # 已接受匹配数
    result = await db.execute(
        select(func.count(Match.id)).where(Match.status == "ACCEPTED")
    )
    accepted_matches = result.scalar()
    
    # 待处理匹配数
    result = await db.execute(
        select(func.count(Match.id)).where(Match.status.in_(["SUGGESTED", "VIEWED", "INTERESTED"]))
    )
    pending_matches = result.scalar()
    
    # 平均匹配分数
    result = await db.execute(select(func.avg(Match.match_score)))
    average_score = result.scalar() or 0
    
    return {
        "total_matches": total_matches,
        "accepted_matches": accepted_matches,
        "pending_matches": pending_matches,
        "average_score": float(average_score),
        "acceptance_rate": (accepted_matches / total_matches * 100) if total_matches > 0 else 0
    }