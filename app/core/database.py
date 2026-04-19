"""
数据库配置 - SQLite + aiosqlite
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

DATABASE_URL = "sqlite+aiosqlite:///./opc_marketplace.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 插入初始数据
    from app.core.seed_data import seed_database
    async with async_session() as session:
        await seed_database(session)


async def get_db():
    """获取数据库会话"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
