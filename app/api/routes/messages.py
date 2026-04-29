"""消息系统API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.models.models import Message, User

router = APIRouter()


class MessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    content: str
    message_type: str = "text"
    related_project_id: Optional[int] = None


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    sender_name: Optional[str]
    receiver_id: int
    receiver_name: Optional[str]
    content: str
    message_type: str
    is_read: bool
    created_at: str

    class Config:
        from_attributes = True


@router.post("/", response_model=MessageResponse)
async def send_message(data: MessageCreate, db: AsyncSession = Depends(get_db)):
    """发送消息"""
    sender = await db.get(User, data.sender_id)
    receiver = await db.get(User, data.receiver_id)
    
    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    message = Message(
        sender_id=data.sender_id,
        receiver_id=data.receiver_id,
        content=data.content,
        message_type=data.message_type,
        related_project_id=data.related_project_id,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    return MessageResponse(
        id=message.id,
        sender_id=message.sender_id,
        sender_name=sender.display_name,
        receiver_id=message.receiver_id,
        receiver_name=receiver.display_name,
        content=message.content,
        message_type=message.message_type,
        is_read=message.is_read,
        created_at=message.created_at.isoformat(),
    )


@router.get("/conversation/{user1_id}/{user2_id}")
async def get_conversation(
    user1_id: int,
    user2_id: int,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """获取两个用户之间的对话"""
    result = await db.execute(
        select(Message)
        .where(
            or_(
                and_(Message.sender_id == user1_id, Message.receiver_id == user2_id),
                and_(Message.sender_id == user2_id, Message.receiver_id == user1_id),
            )
        )
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    messages = result.scalars().all()
    
    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "receiver_id": m.receiver_id,
            "content": m.content,
            "message_type": m.message_type,
            "is_read": m.is_read,
            "created_at": m.created_at.isoformat(),
        }
        for m in reversed(messages)
    ]


@router.get("/inbox/{user_id}")
async def get_inbox(
    user_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """获取用户收件箱（最新消息摘要）"""
    # 获取每个对话的最新消息
    result = await db.execute(
        select(Message)
        .where(
            or_(
                Message.sender_id == user_id,
                Message.receiver_id == user_id,
            )
        )
        .order_by(Message.created_at.desc())
        .limit(100)
    )
    messages = result.scalars().all()
    
    # 按对话分组
    conversations = {}
    for m in messages:
        other_id = m.receiver_id if m.sender_id == user_id else m.sender_id
        if other_id not in conversations:
            other_user = await db.get(User, other_id)
            conversations[other_id] = {
                "user_id": other_id,
                "user_name": other_user.display_name if other_user else "未知用户",
                "last_message": m.content,
                "last_message_time": m.created_at.isoformat(),
                "unread_count": 0,
            }
        if m.receiver_id == user_id and not m.is_read:
            conversations[other_id]["unread_count"] += 1
    
    return list(conversations.values())[:limit]


@router.put("/{message_id}/read")
async def mark_as_read(message_id: int, db: AsyncSession = Depends(get_db)):
    """标记消息为已读"""
    message = await db.get(Message, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    message.is_read = True
    await db.commit()
    return {"message": "已标记为已读"}


@router.get("/unread/{user_id}")
async def get_unread_count(user_id: int, db: AsyncSession = Depends(get_db)):
    """获取未读消息数"""
    result = await db.execute(
        select(func.count(Message.id)).where(
            Message.receiver_id == user_id,
            Message.is_read == False,
        )
    )
    return {"user_id": user_id, "unread_count": result.scalar()}
