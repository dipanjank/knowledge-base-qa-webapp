import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI

from app.config import settings
from app.database import async_session
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.routers import admin, auth
from app.utils.auth import hash_password

logger = logging.getLogger(__name__)


async def _seed_admin() -> None:
    async with async_session() as session:
        repo = UserRepository(session)
        existing = await repo.get_one(role="admin")
        if existing is not None:
            return
        await repo.create(
            User(
                username=settings.admin_username,
                email=settings.admin_email,
                password_hash=hash_password(settings.admin_password),
                role="admin",
            )
        )
        logger.info("Admin user '%s' seeded", settings.admin_username)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _seed_admin()
    yield


app = FastAPI(title="Knowledge Base QA", version="0.1.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(admin.router)


@app.get("/api/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
