"""
OPC Marketplace - 项目相关的Pydantic模式
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

class ProjectType(str, Enum):
    CONSULTING = "CONSULTING"
    DEVELOPMENT = "DEVELOPMENT"
    DESIGN = "DESIGN"
    CONTENT = "CONTENT"
    MARKETING = "MARKETING"
    DATA = "DATA"
    OTHER = "OTHER"

class BudgetType(str, Enum):
    FIXED = "FIXED"
    HOURLY = "HOURLY"
    MILESTONE = "MILESTONE"

class ProjectStatus(str, Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ExperienceLevel(str, Enum):
    JUNIOR = "JUNIOR"
    MID = "MID"
    SENIOR = "SENIOR"
    EXPERT = "EXPERT"

class LocationPreference(str, Enum):
    REMOTE = "REMOTE"
    ONSITE = "ONSITE"
    HYBRID = "HYBRID"
    ANY = "ANY"

class MatchStatus(str, Enum):
    SUGGESTED = "SUGGESTED"
    VIEWED = "VIEWED"
    INTERESTED = "INTERESTED"
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

class ProposalStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"

# 技能模式
class SkillBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class SkillCreate(SkillBase):
    pass

class SkillUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

class SkillResponse(SkillBase):
    id: str
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# 项目里程碑模式
class ProjectMilestoneBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    amount: float = Field(..., gt=0)
    due_date: Optional[datetime] = None

class ProjectMilestoneCreate(ProjectMilestoneBase):
    pass

class ProjectMilestoneUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    due_date: Optional[datetime] = None
    status: Optional[str] = None

class ProjectMilestoneResponse(ProjectMilestoneBase):
    id: str
    project_id: str
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 项目模式
class ProjectBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=20)
    project_type: ProjectType
    budget_type: BudgetType
    budget_min: float = Field(..., gt=0)
    budget_max: float = Field(..., gt=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    duration_estimate: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_experience: Optional[ExperienceLevel] = None
    location_preference: LocationPreference = LocationPreference.ANY
    is_urgent: bool = False
    deadline: Optional[datetime] = None
    attachments: Optional[List[str]] = None

    @validator('budget_max')
    def validate_budget(cls, v, values):
        if 'budget_min' in values and v < values['budget_min']:
            raise ValueError('最大预算必须大于最小预算')
        return v

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, min_length=20)
    project_type: Optional[ProjectType] = None
    budget_type: Optional[BudgetType] = None
    budget_min: Optional[float] = Field(None, gt=0)
    budget_max: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    duration_estimate: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_experience: Optional[ExperienceLevel] = None
    location_preference: Optional[LocationPreference] = None
    is_urgent: Optional[bool] = None
    deadline: Optional[datetime] = None
    attachments: Optional[List[str]] = None
    status: Optional[ProjectStatus] = None

    @validator('budget_max')
    def validate_budget(cls, v, values):
        if v is not None and 'budget_min' in values and values['budget_min'] is not None:
            if v < values['budget_min']:
                raise ValueError('最大预算必须大于最小预算')
        return v

class ProjectResponse(ProjectBase):
    id: str
    client_id: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    client: Optional["ClientProfileResponse"] = None
    milestones: Optional[List[ProjectMilestoneResponse]] = None
    matches: Optional[List["MatchResponse"]] = None
    proposals: Optional[List["ProposalResponse"]] = None
    
    class Config:
        from_attributes = True

class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class ProjectSearch(BaseModel):
    query: Optional[str] = None
    project_type: Optional[ProjectType] = None
    status: Optional[ProjectStatus] = None
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    skill_ids: Optional[List[str]] = None
    location_preference: Optional[LocationPreference] = None
    is_urgent: Optional[bool] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

class ProjectStats(BaseModel):
    total_projects: int
    open_projects: int
    in_progress_projects: int
    completed_projects: int
    total_budget: float
    average_budget: float

# 匹配模式
class MatchBase(BaseModel):
    project_id: str
    provider_id: str
    match_score: float = Field(..., ge=0, le=100)
    match_reasons: Optional[List[str]] = None
    proposed_budget: Optional[float] = None
    proposed_timeline: Optional[str] = None
    cover_letter: Optional[str] = None

class MatchCreate(MatchBase):
    pass

class MatchUpdate(BaseModel):
    status: Optional[MatchStatus] = None
    proposed_budget: Optional[float] = None
    proposed_timeline: Optional[str] = None
    cover_letter: Optional[str] = None

class MatchResponse(MatchBase):
    id: str
    status: MatchStatus
    created_at: datetime
    updated_at: datetime
    project: Optional[ProjectResponse] = None
    provider: Optional["ProviderProfileResponse"] = None
    proposal: Optional["ProposalResponse"] = None
    
    class Config:
        from_attributes = True

class MatchListResponse(BaseModel):
    matches: List[MatchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# 提案模式
class ProposalBase(BaseModel):
    cover_letter: str = Field(..., min_length=50)
    proposed_budget: float = Field(..., gt=0)
    proposed_timeline: str = Field(..., min_length=1)
    approach_description: str = Field(..., min_length=50)
    relevant_experience: Optional[str] = None
    attachments: Optional[List[str]] = None

class ProposalCreate(ProposalBase):
    pass

class ProposalUpdate(BaseModel):
    cover_letter: Optional[str] = Field(None, min_length=50)
    proposed_budget: Optional[float] = Field(None, gt=0)
    proposed_timeline: Optional[str] = Field(None, min_length=1)
    approach_description: Optional[str] = Field(None, min_length=50)
    relevant_experience: Optional[str] = None
    attachments: Optional[List[str]] = None
    status: Optional[ProposalStatus] = None

class ProposalResponse(ProposalBase):
    id: str
    match_id: str
    provider_id: str
    project_id: str
    status: ProposalStatus
    created_at: datetime
    updated_at: datetime
    match: Optional[MatchResponse] = None
    provider: Optional["ProviderProfileResponse"] = None
    project: Optional[ProjectResponse] = None
    
    class Config:
        from_attributes = True

class ProposalListResponse(BaseModel):
    proposals: List[ProposalResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# 评价模式
class ReviewBase(BaseModel):
    project_id: str
    reviewee_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    communication_rating: int = Field(..., ge=1, le=5)
    quality_rating: int = Field(..., ge=1, le=5)
    timeliness_rating: int = Field(..., ge=1, le=5)
    would_recommend: bool

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None
    communication_rating: Optional[int] = Field(None, ge=1, le=5)
    quality_rating: Optional[int] = Field(None, ge=1, le=5)
    timeliness_rating: Optional[int] = Field(None, ge=1, le=5)
    would_recommend: Optional[bool] = None

class ReviewResponse(ReviewBase):
    id: str
    reviewer_id: str
    created_at: datetime
    project: Optional[ProjectResponse] = None
    reviewer: Optional["UserResponse"] = None
    reviewee: Optional["UserResponse"] = None
    
    class Config:
        from_attributes = True

class ReviewListResponse(BaseModel):
    reviews: List[ReviewResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class ReviewStats(BaseModel):
    total_reviews: int
    average_rating: float
    rating_distribution: Dict[int, int]
    average_communication: float
    average_quality: float
    average_timeliness: float
    recommendation_rate: float

# 支付模式
class PaymentBase(BaseModel):
    project_id: str
    milestone_id: Optional[str] = None
    amount: float = Field(..., gt=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    payment_method: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    id: str
    payer_id: str
    payee_id: str
    transaction_id: Optional[str] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    project: Optional[ProjectResponse] = None
    
    class Config:
        from_attributes = True