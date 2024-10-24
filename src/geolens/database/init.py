"""
Database initialization and setup utilities.
"""
from typing import Optional
import asyncio
from datetime import datetime
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from .models import Base, Location, ArchitecturalFeature, HistoricalEvent, Relationship
from ..services.embeddings import get_embedding_service

async def init_database(engine: AsyncEngine) -> None:
    """Initialize database schema and extensions."""
    async with engine.begin() as conn:
        # Create extensions if they don't exist
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS age"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
        
        # Create schema if it doesn't exist
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS geolens"))
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

async def load_sample_data(session: AsyncSession) -> None:
    """Load sample data into the database."""
    # Check if data already exists
    result = await session.execute(
        select(Location).where(Location.name == "Notre-Dame Cathedral")
    )
    if result.scalar_one_or_none():
        return  # Data already exists
    
    embedding_service = get_embedding_service()
    
    # Notre-Dame Cathedral
    notre_dame = Location(
        name="Notre-Dame Cathedral",
        description="Medieval Catholic cathedral exemplifying French Gothic architecture.",
        location_type="religious",
        geometry=text("ST_SetSRID(ST_MakePoint(2.3488, 48.8529), 4326)")
    )
    session.add(notre_dame)
    await session.flush()

    # Notre-Dame architectural features
    feature_text = "French Gothic architecture with pioneering use of the rib vault and flying buttress, characterized by pointed arches, ribbed vaults, and flying buttresses. Known for its innovative architectural solutions and religious symbolism."
    notre_dame_features = ArchitecturalFeature(
        location_id=notre_dame.id,
        style="French Gothic",
        year_built=1163,
        architect="Unknown",
        description="Famous for its pioneering use of the rib vault and flying buttress.",
        embedding=embedding_service.get_embedding(feature_text)
    )
    session.add(notre_dame_features)

    # Historical events
    event_text = "Construction of Notre-Dame Cathedral begins under Bishop Maurice de Sully, marking the start of one of the most ambitious architectural projects of medieval Paris."
    construction_event = HistoricalEvent(
        location_id=notre_dame.id,
        event_date=datetime(1163, 1, 1).date(),
        event_type="construction",
        description="Construction begins under Bishop Maurice de Sully",
        embedding=embedding_service.get_embedding(event_text)
    )
    session.add(construction_event)

    # St Paul's Cathedral
    st_pauls = Location(
        name="St. Paul's Cathedral",
        description="Anglican cathedral with significant baroque influence.",
        location_type="religious",
        geometry=text("ST_SetSRID(ST_MakePoint(-0.0983, 51.5138), 4326)")
    )
    session.add(st_pauls)
    await session.flush()

    # St Paul's architectural features
    st_pauls_text = "English Baroque architecture with classical elements, featuring a massive dome inspired by St. Peter's Basilica. Shows Gothic influence in its vertical emphasis and religious symbolism."
    st_pauls_features = ArchitecturalFeature(
        location_id=st_pauls.id,
        style="English Baroque",
        year_built=1675,
        architect="Christopher Wren",
        description="Masterpiece of English Baroque architecture with its distinctive dome.",
        embedding=embedding_service.get_embedding(st_pauls_text)
    )
    session.add(st_pauls_features)

    # Add relationship
    relationship = Relationship(
        from_location_id=notre_dame.id,
        to_location_id=st_pauls.id,
        relationship_type="influences",
        strength=0.7,
        evidence="Gothic architectural elements adapted in the English context."
    )
    session.add(relationship)

    await session.commit()