import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from config import settings
from database import get_session
from main import app
from models import Link


project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
async def async_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def client(async_session):
    def get_session_override():
        return async_session

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(async_session):
    def get_session_override():
        return async_session

    app.dependency_overrides[get_session] = get_session_override

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_links(async_session):
    links = [
        Link(
            original_url=f"https://example.com/url{i}",
            short_name=f"link{i}",
        )
        for i in range(1, 6)
    ]

    for link in links:
        async_session.add(link)

    await async_session.commit()

    for link in links:
        await async_session.refresh(link)

    return links


@pytest.fixture
def test_settings():
    return settings
