import os
import tempfile
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

os.environ.setdefault("MBA_DATABASE_URL", f"sqlite+aiosqlite:///{tempfile.gettempdir()}/mba_test.db")

from httpx import ASGITransport, AsyncClient

from app.db.base import Base
from app.db.init import init_database
from app.db.session import engine
from app.main import create_app


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await init_database()
    application = create_app()
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
