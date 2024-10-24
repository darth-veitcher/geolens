"""
Tests for the database service layer.
"""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from geolens.database.models import Location, ArchitecturalFeature
from geolens.services.database import DatabaseService

pytestmark = pytest.mark.asyncio

async def get_notre_dame_id(session: AsyncSession) -> int:
    """Helper function to get Notre-Dame location ID."""
    stmt = select(Location.id).where(Location.name == 'Notre-Dame Cathedral')
    result = await session.execute(stmt)
    location_id = result.scalar_one_or_none()
    if location_id is None:
        raise ValueError("Notre-Dame Cathedral not found in database")
    return location_id

async def test_find_locations_near(db_session: AsyncSession):
    """Test finding locations near a point."""
    service = DatabaseService(db_session)
    
    locations = await service.find_locations_near(
        lat=48.8529,
        lon=2.3488,
        distance_meters=10000
    )
    
    assert locations is not None
    names = [loc.name for loc in locations]
    assert "Notre-Dame Cathedral" in names

async def test_find_similar_architecture(db_session: AsyncSession):
    """Test finding architecturally similar features."""
    service = DatabaseService(db_session)
    
    location_id = await get_notre_dame_id(db_session)
    stmt = select(ArchitecturalFeature.id).where(
        ArchitecturalFeature.location_id == location_id
    )
    result = await db_session.execute(stmt)
    feature_id = result.scalar_one()
    
    similar = await service.find_similar_architecture(
        feature_id=feature_id,
        similarity_threshold=0.5
    )
    
    assert similar is not None
    assert len(similar) > 0

async def test_find_historical_timeline(db_session: AsyncSession):
    """Test retrieving historical timeline for a location."""
    service = DatabaseService(db_session)
    
    location_id = await get_notre_dame_id(db_session)
    events = await service.find_historical_timeline(
        location_id=location_id
    )
    
    assert events is not None
    assert len(events) > 0
    assert all(event.location_id == location_id for event in events)

async def test_find_architectural_influences(db_session: AsyncSession):
    """Test finding architectural influences."""
    service = DatabaseService(db_session)
    
    location_id = await get_notre_dame_id(db_session)
    influences = await service.find_architectural_influences(
        location_id=location_id
    )
    
    assert influences is not None
    assert len(influences) > 0