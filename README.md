# OPC Marketplace - 供需对接平台

连接市场需求和OPC（一人公司）供给的双边平台。

## 🚀 项目简介

OPC Marketplace 是一个专业的双边市场平台，旨在连接有项目需求的企业/个人与优秀的独立创业者（OPC - One Person Company）。

### 核心功能

- **智能匹配**：基于技能、经验、预算、地点等多维度智能匹配
- **项目管理**：完整的项目生命周期管理
- **用户系统**：需求方和供给方的完整用户系统
- **沟通协作**：项目沟通、提案和协作功能
- **评价系统**：项目完成后的评价和反馈
- **支付管理**：项目支付和里程碑管理

### 用户类型

1. **需求方（Client）**
   - 发布项目需求
   - 浏览和筛选供给方
   - 管理项目进度
   - 评价合作体验

2. **供给方（Provider）**
   - 创建专业资料
   - 展示技能和经验
   - 响应项目需求
   - 提交项目提案

## 🛠️ 技术栈

- **后端框架**：FastAPI
- **数据库**：SQLite (开发) / PostgreSQL (生产)
- **ORM**：SQLAlchemy (异步)
- **认证**：JWT + OAuth2
- **数据验证**：Pydantic
- **API文档**：OpenAPI / Swagger

## 📦 安装和运行

### 环境要求

- Python 3.9+
- pip

### 安装步骤

1. **克隆项目**
```bash
cd ~/Desktop/opc-marketplace
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置你的环境变量
```

5. **初始化数据库**
```bash
# 数据库会在首次启动时自动创建
```

6. **运行项目**
```bash
python -m app.main
```

或使用uvicorn：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 访问API

- **API文档**：http://localhost:8000/docs
- **ReDoc文档**：http://localhost:8000/redoc
- **API根路径**：http://localhost:8000/api/v1

## 📁 项目结构

```
opc-marketplace/
├── app/
│   ├── api/
│   │   ├── routes/          # API路由
│   │   │   ├── auth.py      # 认证路由
│   │   │   ├── users.py     # 用户路由
│   │   │   ├── projects.py  # 项目路由
│   │   │   ├── skills.py    # 技能路由
│   │   │   ├── matches.py   # 匹配路由
│   │   │   └── reviews.py   # 评价路由
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库配置
│   │   └── security.py      # 安全认证
│   ├── models/              # 数据库模型
│   │   ├── user.py          # 用户模型
│   │   ├── project.py       # 项目模型
│   │   └── __init__.py
│   ├── schemas/             # Pydantic模式
│   │   ├── user.py          # 用户模式
│   │   └── project.py       # 项目模式
│   ├── services/            # 业务逻辑
│   │   └── matching.py      # 匹配算法
│   ├── utils/               # 工具函数
│   └── main.py              # 主应用
├── tests/                   # 测试文件
├── alembic/                 # 数据库迁移
├── requirements.txt         # 依赖包
├── .env.example            # 环境配置示例
└── README.md               # 项目文档
```

## 🔧 API端点

### 认证相关
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新令牌
- `POST /api/v1/auth/password-reset` - 请求密码重置
- `POST /api/v1/auth/password-reset/confirm` - 确认密码重置

### 用户管理
- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新当前用户信息
- `GET /api/v1/users/me/client-profile` - 获取需求方资料
- `PUT /api/v1/users/me/client-profile` - 更新需求方资料
- `GET /api/v1/users/me/provider-profile` - 获取供给方资料
- `PUT /api/v1/users/me/provider-profile` - 更新供给方资料
- `POST /api/v1/users/me/skills` - 添加技能
- `GET /api/v1/users/search` - 搜索用户

### 项目管理
- `POST /api/v1/projects/` - 创建项目
- `GET /api/v1/projects/` - 获取项目列表
- `GET /api/v1/projects/my-projects` - 获取我的项目
- `GET /api/v1/projects/{project_id}` - 获取项目详情
- `PUT /api/v1/projects/{project_id}` - 更新项目
- `DELETE /api/v1/projects/{project_id}` - 删除项目
- `POST /api/v1/projects/{project_id}/publish` - 发布项目
- `POST /api/v1/projects/{project_id}/milestones` - 添加里程碑
- `GET /api/v1/projects/{project_id}/matches` - 获取项目匹配

### 技能管理
- `GET /api/v1/skills/` - 获取技能列表
- `POST /api/v1/skills/` - 创建技能
- `GET /api/v1/skills/categories` - 获取技能分类
- `GET /api/v1/skills/popular/list` - 获取热门技能

### 匹配管理
- `GET /api/v1/matches/` - 获取匹配列表
- `GET /api/v1/matches/my-matches` - 获取我的匹配
- `POST /api/v1/matches/auto-match/{project_id}` - 自动匹配项目
- `POST /api/v1/matches/{match_id}/accept` - 接受匹配
- `POST /api/v1/matches/{match_id}/proposal` - 创建提案

### 评价管理
- `POST /api/v1/reviews/` - 创建评价
- `GET /api/v1/reviews/` - 获取评价列表
- `GET /api/v1/reviews/my-reviews` - 获取我的评价
- `GET /api/v1/reviews/stats/{user_id}` - 获取用户评价统计

## 🧮 智能匹配算法

平台采用多维度智能匹配算法，基于以下因素计算匹配分数：

1. **技能匹配 (35%)**：项目所需技能与供给方技能的匹配度
2. **经验匹配 (25%)**：项目经验要求与供给方实际经验的匹配度
3. **预算匹配 (20%)**：项目预算与供给方费率的匹配度
4. **地点匹配 (10%)**：项目地点偏好与供给方位置的匹配度
5. **可用性匹配 (10%)**：供给方当前可用性状态

## 🔒 安全特性

- JWT令牌认证
- 密码加密存储
- CORS保护
- 输入数据验证
- SQL注入防护
- XSS防护

## 📊 数据库设计

平台包含以下核心数据表：

- **users** - 用户基础表
- **client_profiles** - 需求方资料表
- **provider_profiles** - 供给方资料表
- **skills** - 技能表
- **provider_skills** - 供给方技能关联表
- **projects** - 项目表
- **project_milestones** - 项目里程碑表
- **matches** - 匹配记录表
- **proposals** - 提案表
- **reviews** - 评价表
- **payments** - 支付记录表

## 🚀 部署指南

### 开发环境
```bash
python -m app.main
```

### 生产环境
```bash
# 使用gunicorn
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 或使用uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker部署
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

MIT License

## 📞 联系方式

- 项目地址：https://github.com/MoKangMedical/opc-marketplace
- 文档地址：https://mokangmedical.github.io/opc-legends/

---

**OPC Marketplace** - 连接需求与供给，赋能独立创业者