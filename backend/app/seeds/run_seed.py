import asyncio
import logging
from sqlalchemy.future import select

from app.database import AsyncSessionLocal, init_db
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.services.auth_service import get_password_hash
from app.seeds.synthetic_data import seed_synthetic_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run():
    logger.info("Initializing database...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check if default organization exists
        org_res = await session.execute(
            select(Organization).where(Organization.slug == "memorial-health")
        )
        org = org_res.scalars().first()

        if not org:
            org = Organization(
                name="Memorial Regional Health System",
                slug="memorial-health",
                domain="hospital.org",
            )
            session.add(org)
            await session.flush()
            logger.info(f"Created organization: {org.name} ({org.id})")

        # Check if default admin user exists
        user_res = await session.execute(
            select(User).where(User.email == "admin@hospital.org")
        )
        admin = user_res.scalars().first()

        if not admin:
            admin = User(
                organization_id=org.id,
                email="admin@hospital.org",
                hashed_password=get_password_hash("Hospital123!"),
                full_name="Dr. Sarah Mitchell",
                role=UserRole.ADMIN,
                is_active=True,
            )
            session.add(admin)
            await session.flush()
            logger.info("Created default admin user: admin@hospital.org / Hospital123!")

        # Check if claims already exist
        await session.commit()

        # Seed synthetic cohort
        logger.info("Seeding 20 synthetic patients, 30 claims, documents, and 4 scenarios...")
        await seed_synthetic_data(session, org.id, admin.id)
        logger.info("Seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(run())

