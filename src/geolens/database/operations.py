"""
Common database operations.
"""
from typing import TypeVar, Type, Optional, List, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from geolens.database.models import Base

T = TypeVar('T', bound=Base)

async def get_by_id(
    session: AsyncSession,
    model: Type[T],
    id: int
) -> Optional[T]:
    """Get a single record by ID."""
    stmt = select(model).where(model.id == id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_all(
    session: AsyncSession,
    model: Type[T],
    *,
    offset: int = 0,
    limit: int = 100,
    order_by: Any = None
) -> List[T]:
    """Get all records with pagination."""
    stmt = select(model).offset(offset).limit(limit)
    if order_by is not None:
        stmt = stmt.order_by(order_by)
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def create(
    session: AsyncSession,
    model: Type[T],
    **kwargs
) -> T:
    """Create a new record."""
    instance = model(**kwargs)
    session.add(instance)
    await session.flush()
    return instance

async def delete(
    session: AsyncSession,
    model: Type[T],
    id: int
) -> bool:
    """Delete a record by ID."""
    instance = await get_by_id(session, model, id)
    if instance:
        await session.delete(instance)
        return True
    return False