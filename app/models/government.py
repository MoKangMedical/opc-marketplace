"""
OPC Marketplace - 揭榜挂帅项目模型
政府科技创新项目对接模块
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum, Text, Integer, JSON, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base

class GovernmentProject(Base):
    """政府揭榜挂帅项目模型"""
    __tablename__ = "government_projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 项目基本信息
    title = Column(String(500), nullable=False)  # 项目名称
    project_code = Column(String(100), unique=True, nullable=True)  # 项目编号
    description = Column(Text, nullable=False)  # 项目描述
    
    # 发榜方信息
    publisher_type = Column(Enum("NATIONAL", "PROVINCIAL", "MUNICIPAL", "DISTRICT", name="publisher_type_enum"), nullable=False)
    publisher_name = Column(String(255), nullable=False)  # 发榜单位
    publisher_department = Column(String(255), nullable=True)  # 发榜部门
    contact_person = Column(String(100), nullable=True)  # 联系人
    contact_phone = Column(String(50), nullable=True)  # 联系电话
    contact_email = Column(String(255), nullable=True)  # 联系邮箱
    
    # 项目分类
    industry = Column(String(100), nullable=False)  # 行业领域
    technology_field = Column(JSON, nullable=True)  # 技术领域 ["人工智能", "生物医药", "新能源"]
    project_category = Column(Enum(
        "TECH_RESEARCH", "PRODUCT_DEVELOPMENT", "TECH_BREAKTHROUGH", 
        "INDUSTRIAL_UPGRADE", "PUBLIC_SERVICE", "OTHER",
        name="project_category_enum"
    ), nullable=False)
    
    # 预算和周期
    budget_min = Column(Numeric(15, 2), nullable=False)  # 最低预算
    budget_max = Column(Numeric(15, 2), nullable=False)  # 最高预算
    currency = Column(String(3), default="CNY")
    funding_source = Column(String(100), nullable=True)  # 资金来源
    
    # 时间节点
    publish_date = Column(DateTime(timezone=True), nullable=False)  # 发布日期
    application_deadline = Column(DateTime(timezone=True), nullable=False)  # 申报截止日期
    project_duration = Column(String(100), nullable=True)  # 项目周期
    
    # 申报要求
    eligibility_requirements = Column(Text, nullable=True)  # 申报资格要求
    technical_requirements = Column(Text, nullable=True)  # 技术要求
    deliverables = Column(Text, nullable=True)  # 成果要求
    evaluation_criteria = Column(JSON, nullable=True)  # 评审标准
    
    # 申报材料
    required_documents = Column(JSON, nullable=True)  # 需要提交的材料
    
    # 项目状态
    status = Column(Enum(
        "DRAFT", "PUBLISHED", "APPLICATION_OPEN", "REVIEWING",
        "AWARDED", "IN_PROGRESS", "COMPLETED", "CANCELLED",
        name="gov_project_status_enum"
    ), default="PUBLISHED")
    
    # 附件和链接
    attachments = Column(JSON, nullable=True)  # 附件列表
    official_url = Column(String(500), nullable=True)  # 官方链接
    
    # 统计信息
    view_count = Column(Integer, default=0)  # 浏览次数
    application_count = Column(Integer, default=0)  # 申请数量
    
    # 元数据
    tags = Column(JSON, nullable=True)  # 标签
    region = Column(String(100), nullable=True)  # 所属地区
    is_featured = Column(Boolean, default=False)  # 是否精选
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    applications = relationship("ProjectApplication", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<GovernmentProject {self.title}>"


class ProjectApplication(Base):
    """项目申请记录"""
    __tablename__ = "project_applications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("government_projects.id"), nullable=False)
    applicant_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 申请信息
    team_name = Column(String(255), nullable=False)  # 申报团队名称
    team_introduction = Column(Text, nullable=False)  # 团队介绍
    technical_capability = Column(Text, nullable=False)  # 技术能力说明
    project_plan = Column(Text, nullable=False)  # 项目实施方案
    budget_plan = Column(Text, nullable=True)  # 预算方案
    
    # 申请材料
    documents = Column(JSON, nullable=True)  # 提交的材料
    
    # 申请状态
    status = Column(Enum(
        "DRAFT", "SUBMITTED", "UNDER_REVIEW", "SHORTLISTED",
        "ACCEPTED", "REJECTED", "WITHDRAWN",
        name="application_status_enum"
    ), default="DRAFT")
    
    # 评审信息
    review_score = Column(Numeric(5, 2), nullable=True)  # 评审分数
    review_comments = Column(Text, nullable=True)  # 评审意见
    
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    project = relationship("GovernmentProject", back_populates="applications")
    applicant = relationship("User", back_populates="gov_applications")
    
    def __repr__(self):
        return f"<ProjectApplication {self.project_id} - {self.applicant_id}>"


class IndustryCategory(Base):
    """行业分类"""
    __tablename__ = "industry_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("industry_categories.id"), nullable=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 自引用关系
    children = relationship("IndustryCategory", back_populates="parent")
    parent = relationship("IndustryCategory", back_populates="children", remote_side=[id])
    
    def __repr__(self):
        return f"<IndustryCategory {self.name}>"


class RegionCode(Base):
    """地区代码"""
    __tablename__ = "region_codes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    level = Column(Enum("NATIONAL", "PROVINCE", "CITY", "DISTRICT", name="region_level_enum"), nullable=False)
    parent_code = Column(String(20), nullable=True)
    
    def __repr__(self):
        return f"<RegionCode {self.name}>"