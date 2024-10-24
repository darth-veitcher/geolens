"""
Pytest configuration and fixtures for async database testing.
"""
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    AsyncEngine
)

from geolens.config import get_settings
from geolens.database.init import init_database, load_sample_data

settings = get_settings()

@pytest_asyncio.fixture(scope="function")
async def async_engine() -> AsyncEngine:
    """Create a test async engine."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    
    # Initialize database and load sample data
    async with engine.begin() as conn:
        await init_database(engine)
        async with AsyncSession(engine) as session:
            await load_sample_data(session)
    
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test."""
    async with AsyncSession(async_engine, expire_on_commit=False) as session:
        async with session.begin():
            yield session