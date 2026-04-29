"""
OPC Marketplace - 项目和技能模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum, Text, Integer, JSON, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

class Skill(Base):
    """技能模型"""
    __tablename__ = "skills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(100), nullable=False)  # 例如："编程语言", "框架", "工具"
    description = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    provider_skills = relationship("ProviderSkill", back_populates="skill", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Skill {self.name}>"

class Project(Base):
    """项目/需求模型"""
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("client_profiles.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    project_type = Column(Enum("CONSULTING", "DEVELOPMENT", "DESIGN", "CONTENT", "MARKETING", "DATA", "OTHER", name="project_type_enum"), nullable=False)
    budget_type = Column(Enum("FIXED", "HOURLY", "MILESTONE", name="budget_type_enum"), nullable=False)
    budget_min = Column(Numeric(12, 2), nullable=False)
    budget_max = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    duration_estimate = Column(String(100), nullable=True)  # 例如："2-4周", "1-3个月"
    required_skills = Column(JSON, nullable=True)  # 技能ID列表
    preferred_experience = Column(Enum("JUNIOR", "MID", "SENIOR", "EXPERT", name="experience_level_enum"), nullable=True)
    location_preference = Column(Enum("REMOTE", "ONSITE", "HYBRID", "ANY", name="location_preference_enum"), default="ANY")
    status = Column(Enum("DRAFT", "OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED", name="project_status_enum"), default="DRAFT")
    is_urgent = Column(Boolean, default=False)
    deadline = Column(DateTime(timezone=True), nullable=True)
    attachments = Column(JSON, nullable=True)  # 附件URL列表
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    client = relationship("ClientProfile", back_populates="projects")
    milestones = relationship("ProjectMilestone", back_populates="project", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="project", cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="project", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="project", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="project", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project {self.title}>"

class ProjectMilestone(Base):
    """项目里程碑模型"""
    __tablename__ = "project_milestones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum("PENDING", "IN_PROGRESS", "COMPLETED", "PAID", name="milestone_status_enum"), default="PENDING")
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    project = relationship("Project", back_populates="milestones")
    payments = relationship("Payment", back_populates="milestone")
    
    def __repr__(self):
        return f"<ProjectMilestone {self.title}>"

class Match(Base):
    """匹配记录模型"""
    __tablename__ = "matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("provider_profiles.id"), nullable=False)
    match_score = Column(Numeric(5, 2), nullable=False)  # 0-100分
    match_reasons = Column(JSON, nullable=True)  # 匹配原因
    status = Column(Enum("SUGGESTED", "VIEWED", "INTERESTED", "PROPOSED", "ACCEPTED", "REJECTED", name="match_status_enum"), default="SUGGESTED")
    proposed_budget = Column(Numeric(12, 2), nullable=True)
    proposed_timeline = Column(String(100), nullable=True)
    cover_letter = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    project = relationship("Project", back_populates="matches")
    provider = relationship("ProviderProfile", back_populates="matches")
    proposal = relationship("Proposal", back_populates="match", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Match {self.project_id} - {self.provider_id}>"

class Proposal(Base):
    """提案模型"""
    __tablename__ = "proposals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), unique=True, nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("provider_profiles.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    cover_letter = Column(Text, nullable=False)
    proposed_budget = Column(Numeric(12, 2), nullable=False)
    proposed_timeline = Column(String(100), nullable=False)
    approach_description = Column(Text, nullable=False)  # 项目执行方案
    relevant_experience = Column(Text, nullable=True)  # 相关经验
    attachments = Column(JSON, nullable=True)  # 附件
    status = Column(Enum("PENDING", "ACCEPTED", "REJECTED", "WITHDRAWN", name="proposal_status_enum"), default="PENDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    match = relationship("Match", back_populates="proposal")
    provider = relationship("ProviderProfile", back_populates="proposals")
    project = relationship("Project", back_populates="proposals")
    
    def __repr__(self):
        return f"<Proposal {self.id} - {self.project_id}>"

class Conversation(Base):
    """对话模型"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    participants = Column(JSON, nullable=False)  # 用户ID列表
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    project = relationship("Project", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation {self.id}>"

class Message(Base):
    """消息模型"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(Enum("TEXT", "FILE", "PROPOSAL", "SYSTEM", name="message_type_enum"), default="TEXT")
    is_read = Column(Boolean, default=False)
    attachments = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")
    
    def __repr__(self):
        return f"<Message {self.id} - {self.sender_id}>"

class Review(Base):
    """评价模型"""
    __tablename__ = "reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reviewee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5分
    comment = Column(Text, nullable=True)
    communication_rating = Column(Integer, nullable=False)  # 沟通评分
    quality_rating = Column(Integer, nullable=False)  # 质量评分
    timeliness_rating = Column(Integer, nullable=False)  # 及时性评分
    would_recommend = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    project = relationship("Project", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews_given", foreign_keys=[reviewer_id])
    reviewee = relationship("User", back_populates="reviews_received", foreign_keys=[reviewee_id])
    
    def __repr__(self):
        return f"<Review {self.id} - {self.project_id}>"

class Payment(Base):
    """支付记录模型"""
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    milestone_id = Column(UUID(as_uuid=True), ForeignKey("project_milestones.id"), nullable=True)
    payer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    payee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    payment_method = Column(String(50), nullable=True)
    transaction_id = Column(String(255), nullable=True)
    status = Column(Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", "REFUNDED", name="payment_status_enum"), default="PENDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    project = relationship("Project", back_populates="payments")
    milestone = relationship("ProjectMilestone", back_populates="payments")
    payer = relationship("User", foreign_keys=[payer_id])
    payee = relationship("User", foreign_keys=[payee_id])
    
    def __repr__(self):
        return f"<Payment {self.id} - {self.amount}>"