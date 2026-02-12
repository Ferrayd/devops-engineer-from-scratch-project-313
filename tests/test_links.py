import pytest


class TestLinksCreate:
    @pytest.mark.asyncio
    async def test_create_link_success(self, async_client):
        link_data = {
            "original_url": "https://example.com/long-url",
            "short_name": "exmpl",
        }
        response = await async_client.post("/api/links", json=link_data)

        assert response.status_code == 201
        data = response.json()
        assert data["original_url"] == "https://example.com/long-url"
        assert data["short_name"] == "exmpl"
        assert "exmpl" in data["short_url"]
        assert data["id"] is not None
        assert data["created_at"] is not None

    @pytest.mark.asyncio
    async def test_create_link_duplicate_short_name(self, async_client):
        link_data = {
            "original_url": "https://example.com/long-url",
            "short_name": "exmpl",
        }

        response1 = await async_client.post("/api/links", json=link_data)
        assert response1.status_code == 201

        response2 = await async_client.post("/api/links", json=link_data)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_link_invalid_url(self, async_client):
        link_data = {
            "original_url": "not-a-valid-url",
            "short_name": "test",
        }
        response = await async_client.post("/api/links", json=link_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_link_missing_fields(self, async_client):
        link_data = {"short_name": "test"}
        response = await async_client.post("/api/links", json=link_data)
        assert response.status_code == 422

        link_data = {"original_url": "https://example.com"}
        response = await async_client.post("/api/links", json=link_data)
        assert response.status_code == 422


class TestLinksRead:
    @pytest.mark.asyncio
    async def test_get_all_links_empty(self, async_client):
        response = await async_client.get("/api/links")
        assert response.status_code == 200
        assert response.json() == []
        assert response.headers["Content-Range"] == "links 0-0/0"

    @pytest.mark.asyncio
    async def test_get_all_links_with_pagination(self, async_client, sample_links):
        response = await async_client.get("/api/links?range=[0,3]")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert response.headers["Content-Range"] == "links 0-2/5"

    @pytest.mark.asyncio
    async def test_get_link_by_id_success(self, async_client, sample_links):
        link_id = sample_links[0].id
        response = await async_client.get(f"/api/links/{link_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == link_id
        assert data["short_name"] == "link1"
        assert data["original_url"] == "https://example.com/url1"

    @pytest.mark.asyncio
    async def test_get_link_by_id_not_found(self, async_client):
        response = await async_client.get("/api/links/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestLinksUpdate:
    @pytest.mark.asyncio
    async def test_update_link_success(self, async_client, sample_links):
        link_id = sample_links[0].id
        updated_data = {
            "original_url": "https://example.com/updated-url",
            "short_name": "updated",
        }
        response = await async_client.put(f"/api/links/{link_id}", json=updated_data)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == link_id
        assert data["original_url"] == "https://example.com/updated-url"
        assert data["short_name"] == "updated"

    @pytest.mark.asyncio
    async def test_update_link_duplicate_short_name(self, async_client, sample_links):
        link1_id = sample_links[0].id
        link2_short_name = sample_links[1].short_name

        update_data = {
            "original_url": "https://example.com/updated",
            "short_name": link2_short_name,
        }
        response = await async_client.put(f"/api/links/{link1_id}", json=update_data)

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_link_not_found(self, async_client):
        update_data = {
            "original_url": "https://example.com/url",
            "short_name": "url",
        }
        response = await async_client.put("/api/links/999", json=update_data)
        assert response.status_code == 404


class TestLinksDelete:
    @pytest.mark.asyncio
    async def test_delete_link_success(self, async_client, sample_links):
        link_id = sample_links[0].id

        response = await async_client.delete(f"/api/links/{link_id}")
        assert response.status_code == 204
        assert response.content == b""

        get_response = await async_client.get(f"/api/links/{link_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_link_not_found(self, async_client):
        response = await async_client.delete("/api/links/999")
        assert response.status_code == 404


class TestPagination:
    @pytest.mark.asyncio
    async def test_pagination_first_page(self, async_client, sample_links):
        response = await async_client.get("/api/links?range=[0,3]")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["id"] == 1
        assert data[2]["id"] == 3
        assert "0-2/5" in response.headers["Content-Range"]

    @pytest.mark.asyncio
    async def test_pagination_second_page(self, async_client, sample_links):
        response = await async_client.get("/api/links?range=[3,5]")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == 4
        assert data[1]["id"] == 5
        assert "3-4/5" in response.headers["Content-Range"]

    @pytest.mark.asyncio
    async def test_pagination_invalid_range_format(self, async_client, sample_links):
        response = await async_client.get("/api/links?range=invalid")
        assert response.status_code == 200
        assert len(response.json()) >= 1
        assert "Content-Range" in response.headers


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_404_not_found(self, async_client):
        response = await async_client.get("/api/links/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_409_conflict(self, async_client):
        link_data = {
            "original_url": "https://example.com/url",
            "short_name": "test",
        }
        await async_client.post("/api/links", json=link_data)
        response = await async_client.post("/api/links", json=link_data)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_422_validation_error(self, async_client):
        link_data = {
            "original_url": "invalid-url",
            "short_name": "test",
        }
        response = await async_client.post("/api/links", json=link_data)
        assert response.status_code == 422


class TestResponseFormat:
    @pytest.mark.asyncio
    async def test_link_response_has_all_fields(self, async_client):
        link_data = {
            "original_url": "https://example.com/long-url",
            "short_name": "test",
        }
        response = await async_client.post("/api/links", json=link_data)
        data = response.json()

        assert "id" in data
        assert "original_url" in data
        assert "short_name" in data
        assert "short_url" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_short_url_format(self, async_client):
        link_data = {
            "original_url": "https://example.com/long-url",
            "short_name": "mylink",
        }
        response = await async_client.post("/api/links", json=link_data)
        data = response.json()

        assert "mylink" in data["short_url"]
        assert data["short_url"].endswith("/mylink")

    @pytest.mark.asyncio
    async def test_list_response_is_array(self, async_client, sample_links):
        response = await async_client.get("/api/links")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_content_range_header_present(self, async_client, sample_links):
        response = await async_client.get("/api/links?range=[0,3]")
        assert "Content-Range" in response.headers
        content_range = response.headers["Content-Range"]
        assert "links" in content_range
        assert "-" in content_range
        assert "/" in content_range
