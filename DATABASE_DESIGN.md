# 数据库模型设计

## 1. 用户系统

### User (用户基础表)
- id: UUID (主键)
- email: String (唯一)
- hashed_password: String
- full_name: String
- user_type: Enum (CLIENT, PROVIDER)
- is_active: Boolean
- is_verified: Boolean
- created_at: DateTime
- updated_at: DateTime

### ClientProfile (需求方资料)
- id: UUID (主键)
- user_id: UUID (外键 -> User)
- company_name: String (可选)
- company_size: Enum (STARTUP, SMALL, MEDIUM, LARGE, ENTERPRISE)
- industry: String
- website: String (可选)
- description: Text
- budget_range: JSON (min, max, currency)
- preferred_project_types: JSON
- location: String
- timezone: String

### ProviderProfile (OPC供给方资料)
- id: UUID (主键)
- user_id: UUID (外键 -> User)
- professional_title: String
- bio: Text
- years_of_experience: Integer
- hourly_rate: Decimal
- availability: Enum (AVAILABLE, BUSY, UNAVAILABLE)
- portfolio_url: String (可选)
- linkedin_url: String (可选)
- github_url: String (可选)
- twitter_url: String (可选)
- location: String
- timezone: String
- languages: JSON
- work_preferences: JSON (remote, hybrid, onsite)

## 2. 技能和专业领域

### Skill (技能表)
- id: UUID (主键)
- name: String (唯一)
- category: String
- description: Text
- is_verified: Boolean

### ProviderSkill (供给方技能关联)
- id: UUID (主键)
- provider_id: UUID (外键 -> ProviderProfile)
- skill_id: UUID (外键 -> Skill)
- proficiency_level: Enum (BEGINNER, INTERMEDIATE, ADVANCED, EXPERT)
- years_of_experience: Integer

### IndustryExpertise (行业专长)
- id: UUID (主键)
- provider_id: UUID (外键 -> ProviderProfile)
- industry: String
- years_experience: Integer
- description: Text

## 3. 项目和需求

### Project (项目/需求表)
- id: UUID (主键)
- client_id: UUID (外键 -> ClientProfile)
- title: String
- description: Text
- project_type: Enum (CONSULTING, DEVELOPMENT, DESIGN, CONTENT, MARKETING, DATA, OTHER)
- budget_type: Enum (FIXED, HOURLY, MILESTONE)
- budget_min: Decimal
- budget_max: Decimal
- currency: String (默认USD)
- duration_estimate: String
- required_skills: JSON (skill IDs)
- preferred_experience: Enum (JUNIOR, MID, SENIOR, EXPERT)
- location_preference: Enum (REMOTE, ONSITE, HYBRID, ANY)
- status: Enum (DRAFT, OPEN, IN_PROGRESS, COMPLETED, CANCELLED)
- created_at: DateTime
- updated_at: DateTime
- deadline: DateTime (可选)
- is_urgent: Boolean

### ProjectMilestone (项目里程碑)
- id: UUID (主键)
- project_id: UUID (外键 -> Project)
- title: String
- description: Text
- amount: Decimal
- due_date: DateTime
- status: Enum (PENDING, IN_PROGRESS, COMPLETED, PAID)
- completed_at: DateTime (可选)

## 4. 匹配和合作

### Match (匹配记录)
- id: UUID (主键)
- project_id: UUID (外键 -> Project)
- provider_id: UUID (外键 -> ProviderProfile)
- match_score: Float (0-100)
- match_reasons: JSON
- status: Enum (SUGGESTED, VIEWED, INTERESTED, PROPOSED, ACCEPTED, REJECTED)
- proposed_budget: Decimal
- proposed_timeline: String
- cover_letter: Text
- created_at: DateTime
- updated_at: DateTime

### Proposal (提案)
- id: UUID (主键)
- match_id: UUID (外键 -> Match)
- provider_id: UUID (外键 -> ProviderProfile)
- project_id: UUID (外键 -> Project)
- cover_letter: Text
- proposed_budget: Decimal
- proposed_timeline: String
- approach_description: Text
- relevant_experience: Text
- status: Enum (PENDING, ACCEPTED, REJECTED, WITHDRAWN)
- created_at: DateTime
- updated_at: DateTime

## 5. 沟通和协作

### Conversation (对话)
- id: UUID (主键)
- project_id: UUID (外键 -> Project, 可选)
- participants: JSON (user IDs)
- created_at: DateTime
- updated_at: DateTime

### Message (消息)
- id: UUID (主键)
- conversation_id: UUID (外键 -> Conversation)
- sender_id: UUID (外键 -> User)
- content: Text
- message_type: Enum (TEXT, FILE, PROPOSAL, SYSTEM)
- is_read: Boolean
- created_at: DateTime

## 6. 评价和反馈

### Review (评价表)
- id: UUID (主键)
- project_id: UUID (外键 -> Project)
- reviewer_id: UUID (外键 -> User)
- reviewee_id: UUID (外键 -> User)
- rating: Integer (1-5)
- comment: Text
- communication_rating: Integer (1-5)
- quality_rating: Integer (1-5)
- timeliness_rating: Integer (1-5)
- would_recommend: Boolean
- created_at: DateTime

## 7. 支付和财务

### Payment (支付记录)
- id: UUID (主键)
- project_id: UUID (外键 -> Project)
- milestone_id: UUID (外键 -> ProjectMilestone, 可选)
- payer_id: UUID (外键 -> User)
- payee_id: UUID (外键 -> User)
- amount: Decimal
- currency: String
- payment_method: String
- transaction_id: String
- status: Enum (PENDING, PROCESSING, COMPLETED, FAILED, REFUNDED)
- created_at: DateTime
- completed_at: DateTime (可选)

## 8. 平台管理

### PlatformSettings (平台设置)
- id: UUID (主键)
- key: String (唯一)
- value: JSON
- description: Text
- updated_at: DateTime

### Notification (通知)
- id: UUID (主键)
- user_id: UUID (外键 -> User)
- title: String
- message: Text
- notification_type: Enum (MATCH, PROPOSAL, MESSAGE, PAYMENT, SYSTEM)
- is_read: Boolean
- related_id: UUID (可选, 关联的项目/匹配等)
- created_at: DateTime