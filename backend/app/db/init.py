from app.db.base import Base
from app.db.session import engine
from app.models import ALL_MODELS  # noqa: F401  (imported so metadata is populated)


async def init_database() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
