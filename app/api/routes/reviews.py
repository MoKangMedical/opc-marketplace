"""
OPC Marketplace - 评价路由
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, ClientProfile, ProviderProfile
from app.models.project import Project, Review
from app.schemas.project import (
    ReviewCreate, ReviewUpdate, ReviewResponse, ReviewListResponse,
    ReviewStats
)

router = APIRouter()

@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    创建评价
    
    - **project_id**: 项目ID
    - **reviewee_id**: 被评价用户ID
    - **rating**: 总体评分（1-5）
    - **communication_rating**: 沟通评分（1-5）
    - **quality_rating**: 质量评分（1-5）
    - **timeliness_rating**: 及时性评分（1-5）
    - **would_recommend**: 是否推荐
    """
    # 检查项目是否存在
    result = await db.execute(select(Project).where(Project.id == review_data.project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查被评价用户是否存在
    result = await db.execute(select(User).where(User.id == review_data.reviewee_id))
    reviewee = result.scalar_one_or_none()
    
    if not reviewee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="被评价用户不存在"
        )
    
    # 检查是否已评价
    result = await db.execute(
        select(Review)
        .where(
            Review.project_id == review_data.project_id,
            Review.reviewer_id == current_user.id,
            Review.reviewee_id == review_data.reviewee_id
        )
    )
    existing_review = result.scalar_one_or_none()
    
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已评价过该项目"
        )
    
    # 检查权限：只有项目参与者可以评价
    # 这里简化处理，实际应该检查用户是否是项目的需求方或供给方
    
    # 创建评价
    review = Review(
        reviewer_id=current_user.id,
        **review_data.dict()
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    
    # 更新供给方的平均评分
    if reviewee.user_type == "PROVIDER":
        await update_provider_rating(reviewee.id, db)
    
    # 加载关联数据
    result = await db.execute(
        select(Review)
        .options(
            selectinload(Review.project),
            selectinload(Review.reviewer),
            selectinload(Review.reviewee)
        )
        .where(Review.id == review.id)
    )
    review = result.scalar_one()
    
    return review

@router.get("/", response_model=ReviewListResponse)
async def list_reviews(
    project_id: Optional[str] = Query(None, description="项目ID"),
    reviewer_id: Optional[str] = Query(None, description="评价者ID"),
    reviewee_id: Optional[str] = Query(None, description="被评价者ID"),
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="最小评分"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取评价列表
    
    支持按项目、评价者、被评价者、评分等条件筛选
    """
    # 构建查询
    query_builder = select(Review)
    
    # 项目过滤
    if project_id:
        query_builder = query_builder.where(Review.project_id == project_id)
    
    # 评价者过滤
    if reviewer_id:
        query_builder = query_builder.where(Review.reviewer_id == reviewer_id)
    
    # 被评价者过滤
    if reviewee_id:
        query_builder = query_builder.where(Review.reviewee_id == reviewee_id)
    
    # 评分过滤
    if min_rating is not None:
        query_builder = query_builder.where(Review.rating >= min_rating)
    
    # 按创建时间倒序
    query_builder = query_builder.order_by(Review.created_at.desc())
    
    # 计算总数
    count_result = await db.execute(query_builder)
    total = len(count_result.scalars().all())
    
    # 分页
    offset = (page - 1) * page_size
    query_builder = query_builder.offset(offset).limit(page_size)
    
    # 执行查询
    result = await db.execute(query_builder)
    reviews = result.scalars().all()
    
    # 加载关联数据
    review_ids = [r.id for r in reviews]
    if review_ids:
        result = await db.execute(
            select(Review)
            .options(
                selectinload(Review.project),
                selectinload(Review.reviewer),
                selectinload(Review.reviewee)
            )
            .where(Review.id.in_(review_ids))
            .order_by(Review.created_at.desc())
        )
        reviews = result.scalars().all()
    
    return {
        "reviews": reviews,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/my-reviews", response_model=ReviewListResponse)
async def get_my_reviews(
    review_type: str = Query("received", description="评价类型：given-我给出的，received-我收到的"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取我的评价"""
    # 构建查询
    if review_type == "given":
        query_builder = select(Review).where(Review.reviewer_id == current_user.id)
    else:  # received
        query_builder = select(Review).where(Review.reviewee_id == current_user.id)
    
    # 按创建时间倒序
    query_builder = query_builder.order_by(Review.created_at.desc())
    
    # 计算总数
    count_result = await db.execute(query_builder)
    total = len(count_result.scalars().all())
    
    # 分页
    offset = (page - 1) * page_size
    query_builder = query_builder.offset(offset).limit(page_size)
    
    # 执行查询
    result = await db.execute(query_builder)
    reviews = result.scalars().all()
    
    # 加载关联数据
    review_ids = [r.id for r in reviews]
    if review_ids:
        result = await db.execute(
            select(Review)
            .options(
                selectinload(Review.project),
                selectinload(Review.reviewer),
                selectinload(Review.reviewee)
            )
            .where(Review.id.in_(review_ids))
            .order_by(Review.created_at.desc())
        )
        reviews = result.scalars().all()
    
    return {
        "reviews": reviews,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取评价详情"""
    result = await db.execute(
        select(Review)
        .options(
            selectinload(Review.project),
            selectinload(Review.reviewer),
            selectinload(Review.reviewee)
        )
        .where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评价不存在"
        )
    
    return review

@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: str,
    review_data: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """更新评价"""
    # 获取评价
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评价不存在"
        )
    
    # 检查权限
    if review.reviewer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此评价"
        )
    
    # 更新评价
    for field, value in review_data.dict(exclude_unset=True).items():
        setattr(review, field, value)
    
    await db.commit()
    await db.refresh(review)
    
    # 更新供给方的平均评分
    if review.reviewee.user_type == "PROVIDER":
        await update_provider_rating(review.reviewee.id, db)
    
    return review

@router.delete("/{review_id}")
async def delete_review(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """删除评价"""
    # 获取评价
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评价不存在"
        )
    
    # 检查权限
    if review.reviewer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此评价"
        )
    
    # 删除评价
    reviewee_id = review.reviewee_id
    await db.delete(review)
    await db.commit()
    
    # 更新供给方的平均评分
    result = await db.execute(select(User).where(User.id == reviewee_id))
    reviewee = result.scalar_one_or_none()
    if reviewee and reviewee.user_type == "PROVIDER":
        await update_provider_rating(reviewee.id, db)
    
    return {"message": "评价已删除"}

@router.get("/stats/{user_id}", response_model=ReviewStats)
async def get_user_review_stats(
    user_id: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取用户的评价统计"""
    # 总评价数
    result = await db.execute(
        select(func.count(Review.id)).where(Review.reviewee_id == user_id)
    )
    total_reviews = result.scalar()
    
    if total_reviews == 0:
        return {
            "total_reviews": 0,
            "average_rating": 0,
            "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "average_communication": 0,
            "average_quality": 0,
            "average_timeliness": 0,
            "recommendation_rate": 0
        }
    
    # 平均评分
    result = await db.execute(
        select(func.avg(Review.rating)).where(Review.reviewee_id == user_id)
    )
    average_rating = result.scalar() or 0
    
    # 评分分布
    rating_distribution = {}
    for rating in range(1, 6):
        result = await db.execute(
            select(func.count(Review.id))
            .where(
                Review.reviewee_id == user_id,
                Review.rating == rating
            )
        )
        rating_distribution[rating] = result.scalar()
    
    # 各项平均分
    result = await db.execute(
        select(func.avg(Review.communication_rating)).where(Review.reviewee_id == user_id)
    )
    average_communication = result.scalar() or 0
    
    result = await db.execute(
        select(func.avg(Review.quality_rating)).where(Review.reviewee_id == user_id)
    )
    average_quality = result.scalar() or 0
    
    result = await db.execute(
        select(func.avg(Review.timeliness_rating)).where(Review.reviewee_id == user_id)
    )
    average_timeliness = result.scalar() or 0
    
    # 推荐率
    result = await db.execute(
        select(func.count(Review.id))
        .where(
            Review.reviewee_id == user_id,
            Review.would_recommend == True
        )
    )
    recommend_count = result.scalar()
    recommendation_rate = (recommend_count / total_reviews * 100) if total_reviews > 0 else 0
    
    return {
        "total_reviews": total_reviews,
        "average_rating": float(average_rating),
        "rating_distribution": rating_distribution,
        "average_communication": float(average_communication),
        "average_quality": float(average_quality),
        "average_timeliness": float(average_timeliness),
        "recommendation_rate": recommendation_rate
    }

async def update_provider_rating(user_id: str, db: AsyncSession):
    """更新供给方的平均评分"""
    # 获取供给方资料
    result = await db.execute(
        select(ProviderProfile).where(ProviderProfile.user_id == user_id)
    )
    provider_profile = result.scalar_one_or_none()
    
    if not provider_profile:
        return
    
    # 计算平均评分
    result = await db.execute(
        select(func.avg(Review.rating)).where(Review.reviewee_id == user_id)
    )
    average_rating = result.scalar() or 0
    
    # 更新供给方资料
    provider_profile.average_rating = average_rating
    await db.commit()