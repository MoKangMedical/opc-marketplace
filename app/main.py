"""
OPC Marketplace - FastAPI Main Application
连接市场需求和OPC供给的双边平台
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
from typing import List

from app.core.config import settings
from app.core.database import engine, Base, get_db
from app.api import api_router
from app.core.security import get_current_user
from app.models.user import User

# 创建数据库表
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("🚀 OPC Marketplace API 已启动")
    yield
    # 关闭时清理
    print("👋 OPC Marketplace API 已关闭")

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    ## OPC Marketplace API
    
    连接市场需求和OPC（一人公司）供给的双边平台。
    
    ### 主要功能：
    - **用户管理**：需求方和供给方的注册、认证和资料管理
    - **项目管理**：需求发布、项目管理和状态跟踪
    - **智能匹配**：基于技能、经验和偏好的智能匹配算法
    - **沟通协作**：项目沟通、提案和协作功能
    - **评价系统**：项目完成后的评价和反馈
    
    ### 用户类型：
    - **需求方（Client）**：发布项目需求，寻找合适的OPC供给方
    - **供给方（Provider）**：展示技能和经验，响应项目需求
    """,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加受信任主机中间件
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    """根端点 - API状态检查"""
    return {
        "message": "欢迎使用 OPC Marketplace API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "opc-marketplace",
        "version": "1.0.0"
    }

@app.get("/api/v1/info")
async def api_info():
    """API信息端点"""
    return {
        "name": settings.PROJECT_NAME,
        "description": "连接市场需求和OPC供给的双边平台",
        "version": "1.0.0",
        "features": [
            "用户认证和授权",
            "项目需求管理",
            "OPC供给方资料",
            "智能匹配算法",
            "沟通协作",
            "评价系统"
        ],
        "user_types": ["需求方 (Client)", "供给方 (Provider)"]
    }

# 受保护的端点示例
@app.get("/api/v1/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """获取当前登录用户信息"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "user_type": current_user.user_type,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )