from src.auth.schemas import UserCreate
from src.auth.service import UserManager, get_user_db
from src.database import session_maker
from src.config import settings

async def create_first_admin(email, password: str = settings.FIRST_ADMIN_PASSWORD):
    async with session_maker() as session:
        user_db = None
        async for db in get_user_db(session):
            user_db = db
            break

        manager = UserManager(user_db)

        try:
            await manager.get_by_email(email)
            return None
        except:
            pass

        user = await manager.create(
            UserCreate(
                email=email,
                password=password,
                is_superuser=True,
                is_verified=True,
                score=0,
            )
        )
        return user