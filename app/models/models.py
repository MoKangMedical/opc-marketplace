"""
数据模型 - 用户、项目、匹配、消息、评价
"""

from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    SUPPLIER = "supplier"  # 供给方（有技术/能力）
    DEMANDER = "demander"  # 需求方（有项目/需求）
    BOTH = "both"  # 双重身份


class ProjectStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class GovProjectStatus(str, enum.Enum):
    RECRUITING = "recruiting"  # 招榜中
    APPLYING = "applying"  # 申报中
    EVALUATING = "evaluating"  # 评审中
    AWARDED = "awarded"  # 已揭榜
    COMPLETED = "completed"  # 已完成


class MatchStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"


# ==================== 用户表 ====================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.BOTH)
    
    # 个人/企业信息
    display_name = Column(String(200))
    company = Column(String(300))
    bio = Column(Text)
    avatar_url = Column(String(500))
    
    # 技能标签 (JSON数组)
    skills = Column(JSON, default=list)
    # 行业领域
    industries = Column(JSON, default=list)
    # 所在地区
    location = Column(String(200))
    # 联系方式
    phone = Column(String(50))
    website = Column(String(500))
    
    # 信誉评分
    rating = Column(Float, default=5.0)
    rating_count = Column(Integer, default=0)
    
    # 元数据
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    supply_projects = relationship("Project", back_populates="supplier", foreign_keys="Project.supplier_id")
    demand_projects = relationship("Project", back_populates="demander", foreign_keys="Project.demander_id")
    applications = relationship("ProjectApplication", back_populates="applicant")
    gov_applications = relationship("GovProjectApplication", back_populates="applicant")
    sent_messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    received_messages = relationship("Message", back_populates="receiver", foreign_keys="Message.receiver_id")
    reviews_given = relationship("Review", back_populates="reviewer", foreign_keys="Review.reviewer_id")
    reviews_received = relationship("Review", back_populates="reviewee", foreign_keys="Review.reviewee_id")


# ==================== 项目表（供需对接）====================
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # 项目类别
    industry = Column(String(100))  # 行业
    
    # 供需方
    demander_id = Column(Integer, ForeignKey("users.id"))
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 预算
    budget_min = Column(Integer)  # 万元
    budget_max = Column(Integer)  # 万元
    
    # 时间
    deadline = Column(DateTime)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # 要求
    required_skills = Column(JSON, default=list)
    required_experience = Column(String(200))
    location_preference = Column(String(200))
    
    # 状态
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.OPEN)
    is_urgent = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    # 附件/文档
    attachments = Column(JSON, default=list)
    
    # 统计
    view_count = Column(Integer, default=0)
    application_count = Column(Integer, default=0)
    
    # 匹配度（自动计算）
    match_score = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    demander = relationship("User", back_populates="demand_projects", foreign_keys=[demander_id])
    supplier = relationship("User", back_populates="supply_projects", foreign_keys=[supplier_id])
    applications = relationship("ProjectApplication", back_populates="project")
    matches = relationship("Match", back_populates="project")


# ==================== 项目申请表 ====================
class ProjectApplication(Base):
    __tablename__ = "project_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    applicant_id = Column(Integer, ForeignKey("users.id"))
    
    proposal = Column(Text)  # 申请方案
    proposed_budget = Column(Integer)  # 报价（万元）
    proposed_duration = Column(Integer)  # 预计工期（天）
    
    # 相关经验
    relevant_experience = Column(Text)
    portfolio_links = Column(JSON, default=list)
    
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="applications")
    applicant = relationship("User", back_populates="applications")


# ==================== 揭榜挂帅 - 政府项目 ====================
class GovProject(Base):
    __tablename__ = "gov_projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    
    # 发布方
    publisher = Column(String(300))  # 发布企业
    publisher_contact = Column(String(200))  # 联系人
    
    # 分类
    industry = Column(String(100))
    tags = Column(JSON, default=list)
    
    # 预算
    budget_min = Column(Integer)  # 万元
    budget_max = Column(Integer)  # 万元
    
    # 时间
    deadline = Column(DateTime)
    project_duration = Column(String(100))  # 项目周期
    
    # 技术要求
    tech_requirements = Column(Text)
    required_skills = Column(JSON, default=list)
    
    # 状态
    status = Column(SQLEnum(GovProjectStatus), default=GovProjectStatus.APPLYING)
    is_featured = Column(Boolean, default=False)
    
    # 来源
    source_url = Column(String(500))
    source_name = Column(String(200))
    
    # 统计
    view_count = Column(Integer, default=0)
    application_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications = relationship("GovProjectApplication", back_populates="project")


class GovProjectApplication(Base):
    __tablename__ = "gov_project_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("gov_projects.id"))
    applicant_id = Column(Integer, ForeignKey("users.id"))
    
    # 申报信息
    team_name = Column(String(200))
    team_members = Column(JSON, default=list)
    proposal = Column(Text)
    proposed_budget = Column(Integer)
    tech_approach = Column(Text)
    
    # 资质证明
    qualifications = Column(JSON, default=list)
    past_projects = Column(JSON, default=list)
    
    status = Column(String(50), default="submitted")
    score = Column(Float, default=0.0)  # 评审打分
    
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("GovProject", back_populates="applications")
    applicant = relationship("User", back_populates="gov_applications")


# ==================== 智能匹配记录 ====================
class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    supplier_id = Column(Integer, ForeignKey("users.id"))
    
    # 匹配分数（多维度）
    skill_score = Column(Float, default=0.0)  # 技能匹配
    experience_score = Column(Float, default=0.0)  # 经验匹配
    budget_score = Column(Float, default=0.0)  # 预算匹配
    location_score = Column(Float, default=0.0)  # 地区匹配
    availability_score = Column(Float, default=0.0)  # 可用性
    total_score = Column(Float, default=0.0)  # 综合评分
    
    # 匹配详情
    match_reasons = Column(JSON, default=list)  # 匹配原因
    
    status = Column(SQLEnum(MatchStatus), default=MatchStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="matches")


# ==================== 消息系统 ====================
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="text")  # text, file, system
    
    is_read = Column(Boolean, default=False)
    related_project_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="received_messages", foreign_keys=[receiver_id])


# ==================== 评价系统 ====================
class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    reviewee_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, nullable=True)
    
    rating = Column(Float, nullable=False)  # 1-5分
    content = Column(Text)
    
    # 细分评分
    quality_score = Column(Float)  # 质量
    communication_score = Column(Float)  # 沟通
    timeliness_score = Column(Float)  # 及时性
    professionalism_score = Column(Float)  # 专业度
    
    created_at = Column(DateTime, default=datetime.utcnow)

    reviewer = relationship("User", back_populates="reviews_given", foreign_keys=[reviewer_id])
    reviewee = relationship("User", back_populates="reviews_received", foreign_keys=[reviewee_id])
