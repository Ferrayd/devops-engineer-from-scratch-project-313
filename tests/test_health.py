import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealth:
    @pytest.mark.asyncio
    async def test_ping_returns_pong(self, client):
        response = await client.get("/ping")

        assert response.status_code == 200
        assert response.text == '"pong"'

    @pytest.mark.asyncio
    async def test_health_returns_healthy(self, client):
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "URL Shortener"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
