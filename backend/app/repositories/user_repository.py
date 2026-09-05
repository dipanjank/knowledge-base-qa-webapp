from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.user import User
from app.repositories.base import GenericRepository


class UserRepository(GenericRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_username_or_email(self, username: str, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where((User.username == username) | (User.email == email))
        )
        return result.scalar_one_or_none()
