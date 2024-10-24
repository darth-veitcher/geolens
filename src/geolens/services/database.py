"""
Database service for GeoLens.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Location, ArchitecturalFeature, HistoricalEvent

class DatabaseService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_locations_near(
        self, 
        lat: float, 
        lon: float, 
        distance_meters: float = 5000,
        limit: int = 10
    ) -> List[Location]:
        """Find locations within a specified distance."""
        query = select(Location).where(
            text(
                "ST_DWithin(geometry::geography, "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, "
                ":distance)"
            )
        ).params(
            lat=lat,
            lon=lon,
            distance=distance_meters
        ).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def find_similar_architecture(
        self,
        feature_id: int,
        similarity_threshold: float = 0.7,
        limit: int = 10
    ) -> List[tuple[ArchitecturalFeature, float]]:
        """Find architecturally similar features."""
        query = text("""
            WITH feature AS (
                SELECT embedding
                FROM geolens.architectural_features
                WHERE id = :feature_id
            )
            SELECT 
                af.*,
                1 - (af.embedding <=> (SELECT embedding FROM feature)) as similarity
            FROM geolens.architectural_features af
            WHERE af.id != :feature_id
            AND 1 - (af.embedding <=> (SELECT embedding FROM feature)) > :threshold
            ORDER BY similarity DESC
            LIMIT :limit
        """)
        
        result = await self.session.execute(
            query,
            {
                "feature_id": feature_id,
                "threshold": similarity_threshold,
                "limit": limit
            }
        )
        
        return [(row, float(row.similarity)) for row in result]

    async def find_historical_timeline(
        self,
        location_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[HistoricalEvent]:
        """Get historical events for a location within a time range."""
        query = select(HistoricalEvent).where(
            HistoricalEvent.location_id == location_id
        )

        if start_date:
            query = query.where(HistoricalEvent.event_date >= start_date)
        if end_date:
            query = query.where(HistoricalEvent.event_date <= end_date)

        query = query.order_by(HistoricalEvent.event_date)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def find_architectural_influences(
        self,
        location_id: int,
        max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """Find architectural influences using graph traversal."""
        query = text("""
        WITH RECURSIVE influence_chain AS (
            -- Base case: direct influences
            SELECT 
                from_location_id,
                to_location_id,
                ARRAY[from_location_id] as path,
                1 as depth,
                strength
            FROM geolens.relationships
            WHERE from_location_id = :location_id
            AND relationship_type = 'influences'
            
            UNION ALL
            
            -- Recursive case: follow the chain of influence
            SELECT 
                r.from_location_id,
                r.to_location_id,
                ic.path || r.from_location_id,
                ic.depth + 1,
                ic.strength * r.strength
            FROM geolens.relationships r
            JOIN influence_chain ic ON r.from_location_id = ic.to_location_id
            WHERE r.relationship_type = 'influences'
            AND ic.depth < :max_depth
            AND NOT r.from_location_id = ANY(ic.path)  -- Prevent cycles
        )
        SELECT 
            l1.name as from_location,
            l2.name as to_location,
            ic.depth,
            ic.strength as influence_strength
        FROM influence_chain ic
        JOIN geolens.locations l1 ON ic.from_location_id = l1.id
        JOIN geolens.locations l2 ON ic.to_location_id = l2.id
        ORDER BY ic.depth, ic.strength DESC
        """)

        result = await self.session.execute(
            query, 
            {
                "location_id": location_id,
                "max_depth": max_depth
            }
        )
        
        return [
            {
                "from_location": row.from_location,
                "to_location": row.to_location,
                "depth": row.depth,
                "influence_strength": float(row.influence_strength)
            }
            for row in result
        ]