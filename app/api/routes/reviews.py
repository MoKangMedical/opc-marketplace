"""评价系统API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models.models import Review, User

router = APIRouter()


class ReviewCreate(BaseModel):
    reviewer_id: int
    reviewee_id: int
    project_id: Optional[int] = None
    rating: float
    content: Optional[str] = None
    quality_score: Optional[float] = None
    communication_score: Optional[float] = None
    timeliness_score: Optional[float] = None
    professionalism_score: Optional[float] = None


@router.post("/")
async def create_review(data: ReviewCreate, db: AsyncSession = Depends(get_db)):
    """提交评价"""
    if data.rating < 1 or data.rating > 5:
        raise HTTPException(status_code=400, detail="评分范围为1-5")
    
    review = Review(
        reviewer_id=data.reviewer_id,
        reviewee_id=data.reviewee_id,
        project_id=data.project_id,
        rating=data.rating,
        content=data.content,
        quality_score=data.quality_score,
        communication_score=data.communication_score,
        timeliness_score=data.timeliness_score,
        professionalism_score=data.professionalism_score,
    )
    db.add(review)
    
    # 更新被评价者的评分
    reviewee = await db.get(User, data.reviewee_id)
    if reviewee:
        total = reviewee.rating * reviewee.rating_count + data.rating
        reviewee.rating_count += 1
        reviewee.rating = round(total / reviewee.rating_count, 1)
    
    await db.commit()
    
    return {"message": "评价提交成功", "review_id": review.id, "new_rating": reviewee.rating}


@router.get("/user/{user_id}")
async def get_user_reviews(
    user_id: int,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """获取用户的评价列表"""
    result = await db.execute(
        select(Review)
        .where(Review.reviewee_id == user_id)
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    reviews = result.scalars().all()
    
    response = []
    for r in reviews:
        reviewer = await db.get(User, r.reviewer_id)
        response.append({
            "id": r.id,
            "reviewer_name": reviewer.display_name if reviewer else "匿名",
            "rating": r.rating,
            "content": r.content,
            "quality_score": r.quality_score,
            "communication_score": r.communication_score,
            "timeliness_score": r.timeliness_score,
            "professionalism_score": r.professionalism_score,
            "created_at": r.created_at.isoformat(),
        })
    
    return response


@router.get("/stats/{user_id}")
async def get_review_stats(user_id: int, db: AsyncSession = Depends(get_db)):
    """获取用户评价统计"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    result = await db.execute(
        select(
            func.avg(Review.quality_score),
            func.avg(Review.communication_score),
            func.avg(Review.timeliness_score),
            func.avg(Review.professionalism_score),
        ).where(Review.reviewee_id == user_id)
    )
    avg_scores = result.one()
    
    return {
        "user_id": user_id,
        "overall_rating": user.rating,
        "total_reviews": user.rating_count,
        "avg_quality": round(avg_scores[0] or 0, 1),
        "avg_communication": round(avg_scores[1] or 0, 1),
        "avg_timeliness": round(avg_scores[2] or 0, 1),
        "avg_professionalism": round(avg_scores[3] or 0, 1),
    }
