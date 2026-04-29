"""
OPC Marketplace - 揭榜挂帅项目Pydantic模式
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

class PublisherType(str, Enum):
    NATIONAL = "NATIONAL"  # 国家级
    PROVINCIAL = "PROVINCIAL"  # 省级
    MUNICIPAL = "MUNICIPAL"  # 市级
    DISTRICT = "DISTRICT"  # 区县级

class ProjectCategory(str, Enum):
    TECH_RESEARCH = "TECH_RESEARCH"  # 技术研究
    PRODUCT_DEVELOPMENT = "PRODUCT_DEVELOPMENT"  # 产品开发
    TECH_BREAKTHROUGH = "TECH_BREAKTHROUGH"  # 技术攻关
    INDUSTRIAL_UPGRADE = "INDUSTRIAL_UPGRADE"  # 产业升级
    PUBLIC_SERVICE = "PUBLIC_SERVICE"  # 公共服务
    OTHER = "OTHER"  # 其他

class GovProjectStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    APPLICATION_OPEN = "APPLICATION_OPEN"
    REVIEWING = "REVIEWING"
    AWARDED = "AWARDED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ApplicationStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SHORTLISTED = "SHORTLISTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"

# 政府项目模式
class GovernmentProjectBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    project_code: Optional[str] = None
    description: str = Field(..., min_length=20)
    publisher_type: PublisherType
    publisher_name: str = Field(..., min_length=2, max_length=255)
    publisher_department: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    industry: str = Field(..., min_length=2, max_length=100)
    technology_field: Optional[List[str]] = None
    project_category: ProjectCategory
    budget_min: float = Field(..., gt=0)
    budget_max: float = Field(..., gt=0)
    currency: str = "CNY"
    funding_source: Optional[str] = None
    publish_date: datetime
    application_deadline: datetime
    project_duration: Optional[str] = None
    eligibility_requirements: Optional[str] = None
    technical_requirements: Optional[str] = None
    deliverables: Optional[str] = None
    evaluation_criteria: Optional[Dict[str, Any]] = None
    required_documents: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
    official_url: Optional[str] = None
    tags: Optional[List[str]] = None
    region: Optional[str] = None

    @validator('budget_max')
    def validate_budget(cls, v, values):
        if 'budget_min' in values and v < values['budget_min']:
            raise ValueError('最高预算必须大于最低预算')
        return v

    @validator('application_deadline')
    def validate_deadline(cls, v, values):
        if 'publish_date' in values and v <= values['publish_date']:
            raise ValueError('申报截止日期必须晚于发布日期')
        return v

class GovernmentProjectCreate(GovernmentProjectBase):
    pass

class GovernmentProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=500)
    description: Optional[str] = Field(None, min_length=20)
    publisher_type: Optional[PublisherType] = None
    publisher_name: Optional[str] = Field(None, min_length=2, max_length=255)
    industry: Optional[str] = Field(None, min_length=2, max_length=100)
    technology_field: Optional[List[str]] = None
    project_category: Optional[ProjectCategory] = None
    budget_min: Optional[float] = Field(None, gt=0)
    budget_max: Optional[float] = Field(None, gt=0)
    application_deadline: Optional[datetime] = None
    eligibility_requirements: Optional[str] = None
    technical_requirements: Optional[str] = None
    deliverables: Optional[str] = None
    status: Optional[GovProjectStatus] = None
    is_featured: Optional[bool] = None
    tags: Optional[List[str]] = None
    region: Optional[str] = None

class GovernmentProjectResponse(GovernmentProjectBase):
    id: str
    status: GovProjectStatus
    view_count: int
    application_count: int
    is_featured: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 申请模式
class ProjectApplicationBase(BaseModel):
    team_name: str = Field(..., min_length=2, max_length=255)
    team_introduction: str = Field(..., min_length=50)
    technical_capability: str = Field(..., min_length=50)
    project_plan: str = Field(..., min_length=100)
    budget_plan: Optional[str] = None
    documents: Optional[Dict[str, Any]] = None

class ProjectApplicationCreate(ProjectApplicationBase):
    pass

class ProjectApplicationUpdate(BaseModel):
    team_name: Optional[str] = Field(None, min_length=2, max_length=255)
    team_introduction: Optional[str] = Field(None, min_length=50)
    technical_capability: Optional[str] = Field(None, min_length=50)
    project_plan: Optional[str] = Field(None, min_length=100)
    budget_plan: Optional[str] = None
    documents: Optional[Dict[str, Any]] = None
    status: Optional[ApplicationStatus] = None

class ProjectApplicationResponse(ProjectApplicationBase):
    id: str
    project_id: str
    applicant_id: str
    status: ApplicationStatus
    review_score: Optional[float] = None
    review_comments: Optional[str] = None
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    project: Optional[GovernmentProjectResponse] = None
    
    class Config:
        from_attributes = True

# 行业分类模式
class IndustryCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = None
    parent_id: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0

class IndustryCategoryResponse(IndustryCategoryBase):
    id: str
    is_active: bool
    created_at: datetime
    children: Optional[List["IndustryCategoryResponse"]] = None
    
    class Config:
        from_attributes = True

# 搜索和统计模式
class ProjectSearch(BaseModel):
    query: Optional[str] = None
    industry: Optional[str] = None
    region: Optional[str] = None
    publisher_type: Optional[PublisherType] = None
    status: Optional[GovProjectStatus] = None
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    is_featured: Optional[bool] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

class ProjectStats(BaseModel):
    total_projects: int
    open_projects: int
    total_budget: float
    total_applications: int
    industry_distribution: List[Dict[str, Any]]