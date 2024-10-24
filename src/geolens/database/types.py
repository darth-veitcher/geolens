"""
Custom SQLAlchemy types for GeoLens.
"""
from sqlalchemy.types import TypeDecorator, UserDefinedType

class Vector(UserDefinedType):
    """PostgreSQL vector type for pgvector extension."""
    
    def __init__(self, dimensions):
        self.dimensions = dimensions

    def get_col_spec(self, **kw):
        return f"vector({self.dimensions})"

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            return str(value)
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            return value
        return process