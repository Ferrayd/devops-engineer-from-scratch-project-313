import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_session
from app.main import app
from app.models import ShortenedLink


@pytest.fixture
async def client(async_session):

    def get_session_override():
        return async_session

    app.dependency_overrides[get_session] = get_session_override

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


class TestCreateLink:

    @pytest.mark.asyncio
    async def test_create_link_success(self, client, async_session):
        payload = {"original_url": "https://example.com/article", "short_name": "test123"}
        response = await client.post("/api/links", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["short_name"] == "test123"
        assert data["original_url"] == "https://example.com/article"
        assert data["short_url"] == "/r/test123"
        assert data["id"] is not None

    @pytest.mark.asyncio
    async def test_create_link_missing_fields(self, client):
        response = await client.post("/api/links", json={})

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_link_missing_original_url(self, client):
        payload = {"short_name": "test123"}
        response = await client.post("/api/links", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_link_missing_short_name(self, client):
        payload = {"original_url": "https://example.com/article"}
        response = await client.post("/api/links", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_link_duplicate_short_name(self, client, async_session):
        link1 = ShortenedLink(short_name="duplicate", original_url="https://example.com/first")
        async_session.add(link1)
        await async_session.commit()

        payload = {"original_url": "https://example.com/second", "short_name": "duplicate"}
        response = await client.post("/api/links", json=payload)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_link_empty_url(self, client):
        payload = {"original_url": "", "short_name": "test123"}
        response = await client.post("/api/links", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_link_empty_short_name(self, client):
        payload = {"original_url": "https://example.com", "short_name": ""}
        response = await client.post("/api/links", json=payload)

        assert response.status_code == 422


class TestGetLinks:

    @pytest.mark.asyncio
    async def test_get_links_empty(self, client):
        response = await client.get("/api/links")

        assert response.status_code == 200
        assert response.json() == []
        assert response.headers.get("Content-Range") == "items 0-0/0"

    @pytest.mark.asyncio
    async def test_get_links_with_data(self, client, async_session):
        for i in range(3):
            link = ShortenedLink(short_name=f"link{i}", original_url=f"https://example.com/{i}")
            async_session.add(link)
        await async_session.commit()

        response = await client.get("/api/links")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert response.headers.get("Content-Range") == "items 0-3/3"

    @pytest.mark.asyncio
    async def test_get_links_with_range(self, client, async_session):
        for i in range(5):
            link = ShortenedLink(short_name=f"link{i}", original_url=f"https://example.com/{i}")
            async_session.add(link)
        await async_session.commit()

        response = await client.get("/api/links?range=[0,2]")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert response.headers.get("Content-Range") == "items 0-2/5"


class TestGetLink:

    @pytest.mark.asyncio
    async def test_get_link_success(self, client, async_session):
        link = ShortenedLink(short_name="test", original_url="https://example.com")
        async_session.add(link)
        await async_session.commit()
        await async_session.refresh(link)

        response = await client.get(f"/api/links/{link.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == link.id
        assert data["short_name"] == "test"
        assert data["original_url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_get_link_not_found(self, client):
        response = await client.get("/api/links/999999")

        assert response.status_code == 404


class TestUpdateLink:

    @pytest.mark.asyncio
    async def test_update_link_success(self, client, async_session):
        link = ShortenedLink(short_name="old", original_url="https://example.com/old")
        async_session.add(link)
        await async_session.commit()
        await async_session.refresh(link)

        payload = {"original_url": "https://example.com/new", "short_name": "new"}
        response = await client.put(f"/api/links/{link.id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["short_name"] == "new"
        assert data["original_url"] == "https://example.com/new"

    @pytest.mark.asyncio
    async def test_update_link_not_found(self, client):
        payload = {"original_url": "https://example.com", "short_name": "test"}
        response = await client.put("/api/links/999999", json=payload)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_link_missing_fields(self, client, async_session):
        link = ShortenedLink(short_name="test", original_url="https://example.com")
        async_session.add(link)
        await async_session.commit()
        await async_session.refresh(link)

        response = await client.put(f"/api/links/{link.id}", json={})

        assert response.status_code == 422


class TestDeleteLink:

    @pytest.mark.asyncio
    async def test_delete_link_success(self, client, async_session):
        link = ShortenedLink(short_name="test", original_url="https://example.com")
        async_session.add(link)
        await async_session.commit()
        await async_session.refresh(link)

        response = await client.delete(f"/api/links/{link.id}")

        assert response.status_code == 204

        get_response = await client.get(f"/api/links/{link.id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_link_not_found(self, client):
        response = await client.delete("/api/links/999999")

        assert response.status_code == 404


class TestRedirect:

    @pytest.mark.asyncio
    async def test_redirect_success(self, client, async_session):
        link = ShortenedLink(short_name="google", original_url="https://google.com")
        async_session.add(link)
        await async_session.commit()

        response = await client.get("/r/google", follow_redirects=False)

        assert response.status_code == 301
        assert response.headers["location"] == "https://google.com"

    @pytest.mark.asyncio
    async def test_redirect_not_found(self, client):
        response = await client.get("/r/nonexistent")

        assert response.status_code == 404


class TestHealth:

    @pytest.mark.asyncio
    async def test_ping(self, client):
        response = await client.get("/ping")

        assert response.status_code == 200
        assert response.text == '"pong"'

    @pytest.mark.asyncio
    async def test_health(self, client):
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_root(self, client):
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
