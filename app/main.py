"""
OPC Marketplace - 揭榜挂帅供需对接平台
Complete FastAPI Backend
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os

from app.core.database import init_db, get_db
from app.api.routes import users, projects, matches, government, messages, reviews, a2a


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await init_db()
    print("🚀 OPC Marketplace 数据库初始化完成")
    yield
    print("👋 OPC Marketplace 关闭")


app = FastAPI(
    title="OPC Marketplace",
    description="揭榜挂帅 - 供需对接平台 | 连接政府科技创新需求与独立创业者",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件和模板
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# 注册路由
app.include_router(users.router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["项目管理"])
app.include_router(matches.router, prefix="/api/v1/matches", tags=["智能匹配"])
app.include_router(government.router, prefix="/api/v1/government", tags=["揭榜挂帅"])
app.include_router(messages.router, prefix="/api/v1/messages", tags=["消息系统"])
app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["评价系统"])
app.include_router(a2a.router, tags=["A2A超级个体"])


@app.get("/")
async def root():
    return {
        "platform": "OPC Marketplace",
        "tagline": "揭榜挂帅 - 供需对接平台",
        "version": "1.0.0",
        "modules": {
            "supply_demand": "供需对接",
            "government_projects": "揭榜挂帅",
            "smart_matching": "智能匹配",
            "messaging": "消息系统",
            "reviews": "评价系统",
        },
        "api_docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "platform": "OPC Marketplace"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
