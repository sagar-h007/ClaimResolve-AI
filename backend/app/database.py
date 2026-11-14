import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from app.config import settings

logger = logging.getLogger(__name__)

# Determine if we're using SQLite or Postgres
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# SQLite needs connect_args check_same_thread=False
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables and extensions."""
    async with engine.begin() as conn:
        if not is_sqlite:
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                logger.info("pgvector extension initialized.")
            except Exception as e:
                logger.warning(f"Could not enable pgvector extension: {e}")
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created.")

    # Auto-bootstrap default admin if database is brand new
    try:
        from app.models.organization import Organization
        from app.models.user import User, UserRole
        from app.services.auth_service import get_password_hash
        from sqlalchemy.future import select

        async with AsyncSessionLocal() as session:
            res = await session.execute(select(User).limit(1))
            if not res.scalars().first():
                org = Organization(
                    name="Memorial Regional Health System",
                    slug="memorial-health",
                    domain="hospital.org",
                )
                session.add(org)
                await session.flush()

                admin = User(
                    organization_id=org.id,
                    email="admin@hospital.org",
                    hashed_password=get_password_hash("Hospital123!"),
                    full_name="Dr. Sarah Mitchell",
                    role=UserRole.ADMIN,
                    is_active=True,
                )
                session.add(admin)
                await session.commit()
                logger.info("Auto-bootstrapped default admin: admin@hospital.org / Hospital123!")
    except Exception as e:
        logger.warning(f"Initial admin bootstrap check skipped: {e}")

