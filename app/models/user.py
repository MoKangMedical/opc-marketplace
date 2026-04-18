"""
OPC Marketplace - 用户模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum, Text, Integer, JSON, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

class User(Base):
    """用户基础模型"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    user_type = Column(Enum("CLIENT", "PROVIDER", name="user_type_enum"), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    client_profile = relationship("ClientProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    provider_profile = relationship("ProviderProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sent_messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    reviews_given = relationship("Review", back_populates="reviewer", foreign_keys="Review.reviewer_id")
    reviews_received = relationship("Review", back_populates="reviewee", foreign_keys="Review.reviewee_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>"

class ClientProfile(Base):
    """需求方资料模型"""
    __tablename__ = "client_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    company_name = Column(String(255), nullable=True)
    company_size = Column(Enum("STARTUP", "SMALL", "MEDIUM", "LARGE", "ENTERPRISE", name="company_size_enum"), nullable=True)
    industry = Column(String(100), nullable=False)
    website = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    budget_range = Column(JSON, nullable=True)  # {"min": 1000, "max": 50000, "currency": "USD"}
    preferred_project_types = Column(JSON, nullable=True)  # ["CONSULTING", "DEVELOPMENT", "DESIGN"]
    location = Column(String(255), nullable=True)
    timezone = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="client_profile")
    projects = relationship("Project", back_populates="client", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ClientProfile {self.company_name or self.user_id}>"

class ProviderProfile(Base):
    """OPC供给方资料模型"""
    __tablename__ = "provider_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    professional_title = Column(String(255), nullable=False)  # 例如："高级全栈开发工程师"
    bio = Column(Text, nullable=False)  # 个人简介
    years_of_experience = Column(Integer, nullable=False)
    hourly_rate = Column(Numeric(10, 2), nullable=False)  # 小时费率
    availability = Column(Enum("AVAILABLE", "BUSY", "UNAVAILABLE", name="availability_enum"), default="AVAILABLE")
    portfolio_url = Column(String(500), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    twitter_url = Column(String(500), nullable=True)
    location = Column(String(255), nullable=True)
    timezone = Column(String(50), nullable=True)
    languages = Column(JSON, nullable=True)  # ["中文", "English"]
    work_preferences = Column(JSON, nullable=True)  # {"remote": true, "hybrid": true, "onsite": false}
    completed_projects = Column(Integer, default=0)  # 完成项目数
    success_rate = Column(Numeric(5, 2), default=0)  # 成功率
    average_rating = Column(Numeric(3, 2), default=0)  # 平均评分
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="provider_profile")
    skills = relationship("ProviderSkill", back_populates="provider", cascade="all, delete-orphan")
    industry_expertise = relationship("IndustryExpertise", back_populates="provider", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="provider", cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="provider", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ProviderProfile {self.professional_title} - {self.user_id}>"

class ProviderSkill(Base):
    """供给方技能关联模型"""
    __tablename__ = "provider_skills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("provider_profiles.id"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    proficiency_level = Column(Enum("BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT", name="proficiency_level_enum"), nullable=False)
    years_of_experience = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    provider = relationship("ProviderProfile", back_populates="skills")
    skill = relationship("Skill", back_populates="provider_skills")
    
    def __repr__(self):
        return f"<ProviderSkill {self.provider_id} - {self.skill_id}>"

class IndustryExpertise(Base):
    """行业专长模型"""
    __tablename__ = "industry_expertise"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("provider_profiles.id"), nullable=False)
    industry = Column(String(100), nullable=False)
    years_experience = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    provider = relationship("ProviderProfile", back_populates="industry_expertise")
    
    def __repr__(self):
        return f"<IndustryExpertise {self.provider_id} - {self.industry}>"

class Notification(Base):
    """通知模型"""
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum("MATCH", "PROPOSAL", "MESSAGE", "PAYMENT", "SYSTEM", name="notification_type_enum"), nullable=False)
    is_read = Column(Boolean, default=False)
    related_id = Column(UUID(as_uuid=True), nullable=True)  # 关联的项目/匹配等ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification {self.title} - {self.user_id}>"