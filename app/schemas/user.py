"""
OPC Marketplace - 用户相关的Pydantic模式
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from enum import Enum

class UserType(str, Enum):
    CLIENT = "CLIENT"
    PROVIDER = "PROVIDER"

class CompanySize(str, Enum):
    STARTUP = "STARTUP"
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"
    ENTERPRISE = "ENTERPRISE"

class Availability(str, Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    UNAVAILABLE = "UNAVAILABLE"

class ProficiencyLevel(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"

# 基础模式
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    user_type: UserType

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    company_name: Optional[str] = None
    industry: Optional[str] = None
    professional_title: Optional[str] = None
    bio: Optional[str] = None
    years_of_experience: Optional[int] = None
    hourly_rate: Optional[float] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserResponse(UserInDB):
    client_profile: Optional["ClientProfileResponse"] = None
    provider_profile: Optional["ProviderProfileResponse"] = None

# 需求方资料模式
class ClientProfileBase(BaseModel):
    company_name: Optional[str] = None
    company_size: Optional[CompanySize] = None
    industry: str
    website: Optional[str] = None
    description: Optional[str] = None
    budget_range: Optional[Dict[str, Any]] = None
    preferred_project_types: Optional[List[str]] = None
    location: Optional[str] = None
    timezone: Optional[str] = None

class ClientProfileCreate(ClientProfileBase):
    pass

class ClientProfileUpdate(ClientProfileBase):
    pass

class ClientProfileResponse(ClientProfileBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 供给方资料模式
class ProviderProfileBase(BaseModel):
    professional_title: str = Field(..., min_length=2, max_length=255)
    bio: str = Field(..., min_length=10)
    years_of_experience: int = Field(..., ge=0)
    hourly_rate: float = Field(..., ge=0)
    availability: Availability = Availability.AVAILABLE
    portfolio_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    twitter_url: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    languages: Optional[List[str]] = None
    work_preferences: Optional[Dict[str, bool]] = None

class ProviderProfileCreate(ProviderProfileBase):
    pass

class ProviderProfileUpdate(ProviderProfileBase):
    pass

class ProviderProfileResponse(ProviderProfileBase):
    id: str
    user_id: str
    completed_projects: int
    success_rate: float
    average_rating: float
    created_at: datetime
    updated_at: datetime
    skills: Optional[List["ProviderSkillResponse"]] = None
    industry_expertise: Optional[List["IndustryExpertiseResponse"]] = None
    
    class Config:
        from_attributes = True

# 技能模式
class ProviderSkillBase(BaseModel):
    skill_id: str
    proficiency_level: ProficiencyLevel
    years_of_experience: int = Field(..., ge=0)

class ProviderSkillCreate(ProviderSkillBase):
    pass

class ProviderSkillUpdate(BaseModel):
    proficiency_level: Optional[ProficiencyLevel] = None
    years_of_experience: Optional[int] = Field(None, ge=0)

class ProviderSkillResponse(ProviderSkillBase):
    id: str
    provider_id: str
    created_at: datetime
    skill: Optional["SkillResponse"] = None
    
    class Config:
        from_attributes = True

# 行业专长模式
class IndustryExpertiseBase(BaseModel):
    industry: str
    years_experience: int = Field(..., ge=0)
    description: Optional[str] = None

class IndustryExpertiseCreate(IndustryExpertiseBase):
    pass

class IndustryExpertiseUpdate(IndustryExpertiseBase):
    pass

class IndustryExpertiseResponse(IndustryExpertiseBase):
    id: str
    provider_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# 用户资料更新模式
class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    client_profile: Optional[ClientProfileUpdate] = None
    provider_profile: Optional[ProviderProfileUpdate] = None

# 令牌模式
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class TokenRefresh(BaseModel):
    refresh_token: str

# 密码相关模式
class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v

# 用户搜索模式
class UserSearch(BaseModel):
    query: Optional[str] = None
    user_type: Optional[UserType] = None
    skill_ids: Optional[List[str]] = None
    min_experience: Optional[int] = None
    max_hourly_rate: Optional[float] = None
    location: Optional[str] = None
    availability: Optional[Availability] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

class UserSearchResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# 通知模式
class NotificationBase(BaseModel):
    title: str
    message: str
    notification_type: str
    related_id: Optional[str] = None

class NotificationCreate(NotificationBase):
    user_id: str

class NotificationResponse(NotificationBase):
    id: str
    user_id: str
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True