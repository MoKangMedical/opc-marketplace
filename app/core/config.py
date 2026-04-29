"""
OPC Marketplace - 配置管理
"""

import os
from typing import List, Union
from pydantic import AnyHttpUrl, BaseSettings, validator
from functools import lru_cache

class Settings(BaseSettings):
    # 项目基本信息
    PROJECT_NAME: str = "OPC Marketplace"
    API_V1_STR: str = "/api/v1"
    
    # 环境配置
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./opc_marketplace.db"
    DATABASE_TEST_URL: str = "sqlite+aiosqlite:///./test.db"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "https://mokangmedical.github.io"
    ]
    
    # 受信任主机
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "*"]
    
    # 密码配置
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 100
    
    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"]
    
    # 邮件配置（可选）
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@opc-marketplace.com"
    EMAILS_FROM_NAME: str = "OPC Marketplace"
    
    # Redis配置（可选）
    REDIS_URL: str = "redis://localhost:6379"
    
    # 匹配算法配置
    MATCH_SCORE_WEIGHTS: dict = {
        "skill_match": 0.35,
        "experience_match": 0.25,
        "budget_match": 0.20,
        "location_match": 0.10,
        "availability_match": 0.10
    }
    
    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # 缓存配置
    CACHE_EXPIRE_MINUTES: int = 30
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_allowed_hosts(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """获取配置设置（带缓存）"""
    return Settings()

settings = get_settings()

# 环境特定配置
if settings.ENVIRONMENT == "production":
    settings.DEBUG = False
    settings.DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)
    settings.SECRET_KEY = os.getenv("SECRET_KEY", settings.SECRET_KEY)
elif settings.ENVIRONMENT == "testing":
    settings.DATABASE_URL = settings.DATABASE_TEST_URL