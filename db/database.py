import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from core.models import Base


class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./storybot.db")
        self.async_database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        
        # Sync engine for migrations
        self.engine = create_engine(
            self.database_url,
            connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {}
        )
        
        # Async engine for application
        self.async_engine = create_async_engine(
            self.async_database_url if "postgresql" in self.database_url else "sqlite+aiosqlite:///./storybot.db"
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        self.AsyncSessionLocal = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def get_session(self) -> Session:
        return self.SessionLocal()


# Global database manager instance
db_manager = DatabaseManager()


# Dependency for FastAPI or similar frameworks
def get_session() -> Session:
    return db_manager.get_session()


# Async session context manager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with db_manager.get_async_session() as session:
        yield session


def init_db():
    """Initialize database tables"""
    db_manager.create_tables()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")