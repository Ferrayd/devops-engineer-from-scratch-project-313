import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from config import settings
from database import get_session
from main import app
from models import Link


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
    
    from sqlalchemy.ext.asyncio import sessionmaker
    
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def client(async_session):
    def get_session_override():
        return async_session
    
    app.dependency_overrides[get_session] = get_session_override
    
    from httpx import Client
    with Client(app=app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(async_session):
    def get_session_override():
        return async_session
    
    app.dependency_overrides[get_session] = get_session_override
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


class TestPagination:
    
    @pytest.mark.asyncio
    async def test_pagination_default_range(self, async_client, async_session):
        for i in range(1, 16):
            link = Link(
                original_url=f"https://example.com/url{i}",
                short_name=f"link{i}",
            )
            async_session.add(link)
        
        await async_session.commit()
        
        response = await async_client.get("/api/links")
        
        assert response.status_code == 200
        assert len(response.json()) == 10
        assert response.headers["Accept-Ranges"] == "links"
        assert response.headers["Content-Range"] == "links 0-9/15"
    
    @pytest.mark.asyncio
    async def test_pagination_first_page(self, async_client, async_session):
        for i in range(1, 21):
            link = Link(
                original_url=f"https://example.com/url{i}",
                short_name=f"link{i}",
            )
            async_session.add(link)
        
        await async_session.commit()
        
        response = await async_client.get("/api/links?range=[0,10]")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        assert data[0]["id"] == 1
        assert data[9]["id"] == 10
        assert response.headers["Content-Range"] == "links 0-9/20"
    
    @pytest.mark.asyncio
    async def test_pagination_second_page(self, async_client, async_session):
        for i in range(1, 21):
            link = Link(
                original_url=f"https://example.com/url{i}",
                short_name=f"link{i}",
            )
            async_session.add(link)
        
        await async_session.commit()
        
        response = await async_client.get("/api/links?range=[10,20]")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        assert data[0]["id"] == 11
        assert data[9]["id"] == 20
        assert response.headers["Content-Range"] == "links 10-19/20"
    
    @pytest.mark.asyncio
    async def test_pagination_partial_last_page(self, async_client, async_session):
        for i in range(1, 16):
            link = Link(
                original_url=f"https://example.com/url{i}",
                short_name=f"link{i}",
            )
            async_session.add(link)
        
        await async_session.commit()
        
        response = await async_client.get("/api/links?range=[5,15]")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        assert data[0]["id"] == 6
        assert data[9]["id"] == 15
        assert response.headers["Content-Range"] == "links 5-14/15"
    
    @pytest.mark.asyncio
    async def test_pagination_empty_list(self, async_client):
        response = await async_client.get("/api/links?range=[0,10]")
        
        assert response.status_code == 200
        assert response.json() == []
        assert response.headers["Content-Range"] == "links 0-0/0"
    
    @pytest.mark.asyncio
    async def test_pagination_invalid_range_format(self, async_client, async_session):
        link = Link(
            original_url="https://example.com/url",
            short_name="link",
        )
        async_session.add(link)
        await async_session.commit()
        
        response = await async_client.get("/api/links?range=invalid")
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.headers["Content-Range"] == "links 0-0/1"
    
    @pytest.mark.asyncio
    async def test_pagination_negative_start(self, async_client, async_session):
        for i in range(1, 6):
            link = Link(
                original_url=f"https://example.com/url{i}",
                short_name=f"link{i}",
            )
            async_session.add(link)
        
        await async_session.commit()
        
        response = await async_client.get("/api/links?range=[-5,10]")
        
        assert response.status_code == 200
        assert len(response.json()) == 5
        assert response.headers["Content-Range"] == "links 0-4/5"
    
    @pytest.mark.asyncio
    async def test_pagination_end_less_than_start(self, async_client, async_session):
        for i in range(1, 21):
            link = Link(
                original_url=f"https://example.com/url{i}",
                short_name=f"link{i}",
            )
            async_session.add(link)
        
        await async_session.commit()
        
        response = await async_client.get("/api/links?range=[5,3]")
        
        assert response.status_code == 200
        assert len(response.json()) == 10


class TestLinksWithPagination:
    
    @pytest.mark.asyncio
    async def test_create_and_paginate(self, async_client, async_session):
        for i in range(1, 26):
            link_data = {
                "original_url": f"https://example.com/url{i}",
                "short_name": f"link{i}",
            }
            response = await async_client.post("/api/links", json=link_data)
            assert response.status_code == 201
        
        page1 = await async_client.get("/api/links?range=[0,10]")
        assert page1.status_code == 200
        assert len(page1.json()) == 10
        assert page1.headers["Content-Range"] == "links 0-9/25"
        
        page2 = await async_client.get("/api/links?range=[10,20]")
        assert page2.status_code == 200
        assert len(page2.json()) == 10
        assert page2.headers["Content-Range"] == "links 10-19/25"
        
        page3 = await async_client.get("/api/links?range=[20,30]")
        assert page3.status_code == 200
        assert len(page3.json()) == 5
        assert page3.headers["Content-Range"] == "links 20-24/25"
    
    @pytest.mark.asyncio
    async def test_pagination_after_delete(self, async_client, async_session):
        ids = []
        for i in range(1, 16):
            link = Link(
                original_url=f"https://example.com/url{i}",
                short_name=f"link{i}",
            )
            async_session.add(link)
        
        await async_session.commit()
        
        response = await async_client.get("/api/links?range=[0,5]")
        first_id = response.json()[0]["id"]
        
        response = await async_client.get("/api/links?range=[0,20]")
        assert response.headers["Content-Range"] == "links 0-14/15"
        
        delete_response = await async_client.delete(f"/api/links/{first_id}")
        assert delete_response.status_code == 204
        
        response = await async_client.get("/api/links?range=[0,20]")
        assert response.headers["Content-Range"] == "links 0-13/14"