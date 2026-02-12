import pytest


class TestPing:
    @pytest.mark.asyncio
    async def test_ping_returns_pong(self, async_client):
        response = await async_client.get("/ping")
        assert response.status_code == 200
        assert response.json() == "pong"
    
    @pytest.mark.asyncio
    async def test_ping_method_get(self, async_client):
        response = await async_client.post("/ping")
        assert response.status_code in [405, 422]
    
    @pytest.mark.asyncio
    async def test_ping_response_type(self, async_client):
        response = await async_client.get("/ping")
        assert isinstance(response.json(), str)


class TestAPI:
    @pytest.mark.asyncio
    async def test_api_docs_available(self, async_client):
        docs_response = await async_client.get("/docs")
        assert docs_response.status_code == 200
        
        redoc_response = await async_client.get("/redoc")
        assert redoc_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_openapi_schema(self, async_client):
        response = await async_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "info" in data