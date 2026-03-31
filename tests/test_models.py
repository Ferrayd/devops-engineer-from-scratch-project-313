from app.models import ShortenedLink


class TestShortenedLinkModel:
    def test_create_link(self):
        link = ShortenedLink(short_name="test", original_url="https://example.com")

        assert link.short_name == "test"
        assert link.original_url == "https://example.com"
        assert link.created_at is not None

    def test_link_repr(self):
        link = ShortenedLink(short_name="test", original_url="https://example.com")

        repr_str = repr(link)
        assert "test" in repr_str
        assert "Link" in repr_str
