import json
from sqlalchemy import TypeDecorator, JSON
from sqlalchemy.dialects.postgresql import ARRAY, FLOAT
try:
    from pgvector.sqlalchemy import Vector as PgVector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

class VectorType(TypeDecorator):
    """
    Polymorphic Vector Type:
    - Uses pgvector's Vector(dim) when on PostgreSQL
    - Falls back to JSON / Array representation on SQLite / local dev
    """
    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 1536, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and HAS_PGVECTOR:
            return dialect.type_descriptor(PgVector(self.dim))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql" and HAS_PGVECTOR:
            return value
        # For JSON / SQLite storage, ensure it's a list or valid JSON
        if isinstance(value, str):
            return json.loads(value)
        return list(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value

