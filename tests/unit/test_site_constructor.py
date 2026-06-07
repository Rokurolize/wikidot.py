"""Site constructor validation tests."""

from typing import Any

import pytest

from wikidot.module.site import Site


def _site(mock_client_no_http: Any, **overrides: Any) -> Site:
    values: dict[str, Any] = {
        "id": 123456,
        "title": "Test Site",
        "unix_name": "test-site",
        "domain": "test-site.wikidot.com",
        "ssl_supported": True,
    }
    values.update(overrides)

    return Site(
        client=mock_client_no_http,
        id=values["id"],
        title=values["title"],
        unix_name=values["unix_name"],
        domain=values["domain"],
        ssl_supported=values["ssl_supported"],
    )


class TestSiteInit:
    """Site initialization validation."""

    def test_init_accepts_valid_metadata(self, mock_client_no_http: Any) -> None:
        site = _site(mock_client_no_http)

        assert site.id == 123456
        assert site.title == "Test Site"
        assert site.unix_name == "test-site"
        assert site.domain == "test-site.wikidot.com"
        assert site.ssl_supported is True
        assert site.url == "https://test-site.wikidot.com"

    @pytest.mark.parametrize(
        ("field", "value", "message"),
        [
            ("id", None, "id must be an integer"),
            ("id", True, "id must be an integer"),
            ("id", False, "id must be an integer"),
            ("id", "123456", "id must be an integer"),
            ("id", 123456.0, "id must be an integer"),
            ("title", None, "title must be a string"),
            ("title", True, "title must be a string"),
            ("title", 123456, "title must be a string"),
            ("title", [], "title must be a string"),
            ("unix_name", None, "unix_name must be a string"),
            ("unix_name", True, "unix_name must be a string"),
            ("unix_name", 123456, "unix_name must be a string"),
            ("unix_name", [], "unix_name must be a string"),
            ("domain", None, "domain must be a string"),
            ("domain", True, "domain must be a string"),
            ("domain", 123456, "domain must be a string"),
            ("domain", [], "domain must be a string"),
            ("ssl_supported", None, "ssl_supported must be a boolean"),
            ("ssl_supported", "true", "ssl_supported must be a boolean"),
            ("ssl_supported", 1, "ssl_supported must be a boolean"),
            ("ssl_supported", [], "ssl_supported must be a boolean"),
        ],
    )
    def test_init_rejects_malformed_metadata(
        self, mock_client_no_http: Any, field: str, value: Any, message: str
    ) -> None:
        with pytest.raises(ValueError, match=message):
            _site(mock_client_no_http, **{field: value})

    @pytest.mark.parametrize(
        ("field", "value", "message"),
        [
            ("domain", None, "domain must be a string"),
            ("domain", True, "domain must be a string"),
            ("ssl_supported", 1, "ssl_supported must be a boolean"),
            ("ssl_supported", "true", "ssl_supported must be a boolean"),
        ],
    )
    def test_url_rejects_mutated_metadata(self, mock_client_no_http: Any, field: str, value: Any, message: str) -> None:
        site = _site(mock_client_no_http)
        setattr(site, field, value)

        with pytest.raises(ValueError, match=message):
            _ = site.url
