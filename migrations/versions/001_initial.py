"""Initial database setup

Revision ID: 001
Revises: 
Create Date: 2024-10-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, DDL
from geoalchemy2 import Geography

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Custom vector type for migrations
class Vector(sa.types.TypeDecorator):
    impl = sa.types.String
    cache_ok = True

    def __init__(self, dimensions):
        super().__init__()
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(sa.types.String())
    
    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else None

def upgrade() -> None:
    # Create schema
    op.execute('CREATE SCHEMA IF NOT EXISTS geolens')

    # Create extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis_topology')
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.execute('CREATE EXTENSION IF NOT EXISTS age')
    op.execute('CREATE EXTENSION IF NOT EXISTS btree_gist')
    
    # Create tables
    op.create_table('locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('location_type', sa.String(), nullable=False),
        sa.Column('geometry', Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('properties', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        schema='geolens',
        if_not_exists=True
    )
    
    # Create architectural_features table
    op.create_table('architectural_features',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('style', sa.String(), nullable=False),
        sa.Column('year_built', sa.Integer(), nullable=True),
        sa.Column('architect', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('properties', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['location_id'], ['geolens.locations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='geolens',
        if_not_exists=True
    )
    
    # After creating the table, alter the column type to vector
    op.execute(DDL(
        "ALTER TABLE geolens.architectural_features ALTER COLUMN embedding TYPE vector(384) USING embedding::vector(384)"
    ))
    
    # Create historical_events table
    op.create_table('historical_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('properties', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['location_id'], ['geolens.locations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='geolens',
        if_not_exists=True
    )
    
    # Alter the historical_events embedding column type
    op.execute(DDL(
        "ALTER TABLE geolens.historical_events ALTER COLUMN embedding TYPE vector(384) USING embedding::vector(384)"
    ))

    # Create relationships table
    op.create_table('relationships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_location_id', sa.Integer(), nullable=False),
        sa.Column('to_location_id', sa.Integer(), nullable=False),
        sa.Column('relationship_type', sa.String(), nullable=False),
        sa.Column('strength', sa.Float(), nullable=True),
        sa.Column('evidence', sa.String(), nullable=True),
        sa.Column('properties', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['from_location_id'], ['geolens.locations.id'], ),
        sa.ForeignKeyConstraint(['to_location_id'], ['geolens.locations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='geolens',
        if_not_exists=True
    )
    
    # Create indexes with IF NOT EXISTS
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_locations_geometry 
        ON geolens.locations USING gist (geometry)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_architectural_features_embedding 
        ON geolens.architectural_features USING ivfflat (embedding vector_cosine_ops)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_historical_events_embedding 
        ON geolens.historical_events USING ivfflat (embedding vector_cosine_ops)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_historical_events_date 
        ON geolens.historical_events (event_date)
    """)

def downgrade() -> None:
    # Drop indexes if they exist
    op.execute("DROP INDEX IF EXISTS geolens.idx_historical_events_date")
    op.execute("DROP INDEX IF EXISTS geolens.idx_historical_events_embedding")
    op.execute("DROP INDEX IF EXISTS geolens.idx_architectural_features_embedding")
    op.execute("DROP INDEX IF EXISTS geolens.idx_locations_geometry")
    
    # Drop tables
    op.drop_table('relationships', schema='geolens')
    op.drop_table('historical_events', schema='geolens')
    op.drop_table('architectural_features', schema='geolens')
    op.drop_table('locations', schema='geolens')