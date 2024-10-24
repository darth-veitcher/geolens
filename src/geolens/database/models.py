"""
SQLAlchemy models for GeoLens.
"""
from datetime import datetime
from typing import Optional, List

from geoalchemy2 import Geography
from sqlalchemy import String, Integer, Float, DateTime, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .types import Vector

class Base(DeclarativeBase):
    """Base class for all models"""
    pass

class Location(Base):
    """Physical location with spatial coordinates."""
    __tablename__ = "locations"
    __table_args__ = {"schema": "geolens"}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    location_type: Mapped[str] = mapped_column(String, nullable=False)
    geometry: Mapped[Geography] = mapped_column(Geography(geometry_type='POINT', srid=4326))
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    architectural_features: Mapped[List["ArchitecturalFeature"]] = relationship(back_populates="location")
    historical_events: Mapped[List["HistoricalEvent"]] = relationship(back_populates="location")
    outgoing_relationships: Mapped[List["Relationship"]] = relationship(
        back_populates="from_location",
        foreign_keys="[Relationship.from_location_id]"
    )
    incoming_relationships: Mapped[List["Relationship"]] = relationship(
        back_populates="to_location",
        foreign_keys="[Relationship.to_location_id]"
    )

class ArchitecturalFeature(Base):
    """Architectural features with vector embeddings for similarity search."""
    __tablename__ = "architectural_features"
    __table_args__ = (
        Index(
            'idx_architectural_features_embedding',
            'embedding',
            postgresql_using='ivfflat',
            postgresql_with={'lists': '100'},
            postgresql_ops={'embedding': 'vector_cosine_ops'}
        ),
        {"schema": "geolens"}
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("geolens.locations.id"))
    style: Mapped[str] = mapped_column(String, nullable=False)
    year_built: Mapped[Optional[int]] = mapped_column(Integer)
    architect: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String)
    embedding = mapped_column(Vector(384))
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    location: Mapped["Location"] = relationship(back_populates="architectural_features")

class HistoricalEvent(Base):
    """Historical events with temporal data and vector embeddings."""
    __tablename__ = "historical_events"
    __table_args__ = (
        Index(
            'idx_historical_events_embedding',
            'embedding',
            postgresql_using='ivfflat',
            postgresql_with={'lists': '100'},
            postgresql_ops={'embedding': 'vector_cosine_ops'}
        ),
        {"schema": "geolens"}
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("geolens.locations.id"))
    event_date: Mapped[datetime] = mapped_column(Date)
    event_type: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    embedding = mapped_column(Vector(384))
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    location: Mapped["Location"] = relationship(back_populates="historical_events")

class Relationship(Base):
    """Relationships between locations for graph analysis."""
    __tablename__ = "relationships"
    __table_args__ = {"schema": "geolens"}

    id: Mapped[int] = mapped_column(primary_key=True)
    from_location_id: Mapped[int] = mapped_column(ForeignKey("geolens.locations.id"))
    to_location_id: Mapped[int] = mapped_column(ForeignKey("geolens.locations.id"))
    relationship_type: Mapped[str] = mapped_column(String, nullable=False)
    strength: Mapped[Optional[float]] = mapped_column(Float)
    evidence: Mapped[Optional[str]] = mapped_column(String)
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    from_location: Mapped["Location"] = relationship(
        back_populates="outgoing_relationships",
        foreign_keys=[from_location_id]
    )
    to_location: Mapped["Location"] = relationship(
        back_populates="incoming_relationships",
        foreign_keys=[to_location_id]
    )