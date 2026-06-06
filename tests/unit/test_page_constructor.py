"""Page constructor validation tests."""

from datetime import datetime
from typing import Any

import pytest

from wikidot.module.page import Page
from wikidot.module.user import User


def _page(mock_site_no_http: Any, **overrides: Any) -> Page:
    values: dict[str, Any] = {
        "site": mock_site_no_http,
        "fullname": "test-page",
        "name": "test-page",
        "category": "_default",
        "title": "Test Page Title",
        "children_count": 0,
        "comments_count": 0,
        "size": 1000,
        "rating": 10,
        "votes_count": 5,
        "rating_percent": None,
        "revisions_count": 3,
        "parent_fullname": None,
        "tags": ["tag1", "tag2"],
        "created_by": None,
        "created_at": None,
        "updated_by": None,
        "updated_at": None,
        "commented_by": None,
        "commented_at": None,
    }
    values.update(overrides)

    return Page(
        site=values["site"],
        fullname=values["fullname"],
        name=values["name"],
        category=values["category"],
        title=values["title"],
        children_count=values["children_count"],
        comments_count=values["comments_count"],
        size=values["size"],
        rating=values["rating"],
        votes_count=values["votes_count"],
        rating_percent=values["rating_percent"],
        revisions_count=values["revisions_count"],
        parent_fullname=values["parent_fullname"],
        tags=values["tags"],
        created_by=values["created_by"],
        created_at=values["created_at"],
        updated_by=values["updated_by"],
        updated_at=values["updated_at"],
        commented_by=values["commented_by"],
        commented_at=values["commented_at"],
    )


class TestPageInit:
    """Page initialization validation."""

    def test_init_accepts_valid_identity_text(self, mock_site_no_http: Any) -> None:
        page = _page(mock_site_no_http)

        assert page.site == mock_site_no_http
        assert page.fullname == "test-page"
        assert page.name == "test-page"
        assert page.category == "_default"
        assert page.title == "Test Page Title"
        assert page.children_count == 0
        assert page.comments_count == 0
        assert page.size == 1000
        assert page.rating == 10
        assert page.votes_count == 5
        assert page.revisions_count == 3
        assert page.parent_fullname is None

    @pytest.mark.parametrize("rating", [10, 4.0])
    def test_init_accepts_valid_rating_numbers(self, mock_site_no_http: Any, rating: int | float) -> None:
        page = _page(mock_site_no_http, rating=rating)

        assert page.rating == rating

    @pytest.mark.parametrize(
        ("field", "value", "message"),
        [
            ("fullname", None, "fullname must be a string"),
            ("fullname", True, "fullname must be a string"),
            ("fullname", 123456, "fullname must be a string"),
            ("fullname", [], "fullname must be a string"),
            ("name", None, "name must be a string"),
            ("name", True, "name must be a string"),
            ("name", 123456, "name must be a string"),
            ("name", [], "name must be a string"),
            ("category", None, "category must be a string"),
            ("category", True, "category must be a string"),
            ("category", 123456, "category must be a string"),
            ("category", [], "category must be a string"),
            ("title", None, "title must be a string"),
            ("title", True, "title must be a string"),
            ("title", 123456, "title must be a string"),
            ("title", [], "title must be a string"),
        ],
    )
    def test_init_rejects_malformed_identity_text(
        self, mock_site_no_http: Any, field: str, value: Any, message: str
    ) -> None:
        with pytest.raises(ValueError, match=message):
            _page(mock_site_no_http, **{field: value})

    @pytest.mark.parametrize(
        ("field", "value", "message"),
        [
            ("children_count", None, "children_count must be an integer"),
            ("children_count", True, "children_count must be an integer"),
            ("children_count", "0", "children_count must be an integer"),
            ("children_count", 0.0, "children_count must be an integer"),
            ("comments_count", None, "comments_count must be an integer"),
            ("comments_count", True, "comments_count must be an integer"),
            ("comments_count", "0", "comments_count must be an integer"),
            ("comments_count", 0.0, "comments_count must be an integer"),
            ("size", None, "size must be an integer"),
            ("size", True, "size must be an integer"),
            ("size", "1000", "size must be an integer"),
            ("size", 1000.0, "size must be an integer"),
            ("votes_count", None, "votes_count must be an integer"),
            ("votes_count", True, "votes_count must be an integer"),
            ("votes_count", "5", "votes_count must be an integer"),
            ("votes_count", 5.0, "votes_count must be an integer"),
            ("revisions_count", None, "revisions_count must be an integer"),
            ("revisions_count", True, "revisions_count must be an integer"),
            ("revisions_count", "3", "revisions_count must be an integer"),
            ("revisions_count", 3.0, "revisions_count must be an integer"),
        ],
    )
    def test_init_rejects_malformed_counts(self, mock_site_no_http: Any, field: str, value: Any, message: str) -> None:
        with pytest.raises(ValueError, match=message):
            _page(mock_site_no_http, **{field: value})

    @pytest.mark.parametrize("rating", [None, True, "10", []])
    def test_init_rejects_malformed_rating(self, mock_site_no_http: Any, rating: Any) -> None:
        with pytest.raises(ValueError, match="rating must be an integer or float"):
            _page(mock_site_no_http, rating=rating)

    @pytest.mark.parametrize(
        ("parent_fullname", "expected"),
        [
            ("parent-page", "parent-page"),
            ("", None),
            (None, None),
        ],
    )
    def test_init_accepts_valid_parent_fullname(
        self, mock_site_no_http: Any, parent_fullname: str | None, expected: str | None
    ) -> None:
        page = _page(mock_site_no_http, parent_fullname=parent_fullname)

        assert page.parent_fullname == expected

    @pytest.mark.parametrize("parent_fullname", [True, 3, []])
    def test_init_rejects_malformed_parent_fullname(self, mock_site_no_http: Any, parent_fullname: Any) -> None:
        with pytest.raises(ValueError, match="parent_fullname must be a string or None"):
            _page(mock_site_no_http, parent_fullname=parent_fullname)

    @pytest.mark.parametrize("tags", [[], ["tag1", "_hidden"]])
    def test_init_accepts_valid_tags(self, mock_site_no_http: Any, tags: list[str]) -> None:
        page = _page(mock_site_no_http, tags=tags)

        assert page.tags == tags

    @pytest.mark.parametrize("tags", [None, "tag1 tag2", ("tag1",)])
    def test_init_rejects_non_list_tags(self, mock_site_no_http: Any, tags: Any) -> None:
        with pytest.raises(ValueError, match="tags must be a list"):
            _page(mock_site_no_http, tags=tags)

    @pytest.mark.parametrize("tags", [["tag1", 3], [True], [None]])
    def test_init_rejects_non_string_tag_entries(self, mock_site_no_http: Any, tags: Any) -> None:
        with pytest.raises(ValueError, match="tags list entries must be strings"):
            _page(mock_site_no_http, tags=tags)

    @pytest.mark.parametrize("site", [None, True, "test-site", {"unix_name": "test-site"}, object()])
    def test_init_rejects_malformed_site(self, mock_site_no_http: Any, site: Any) -> None:
        with pytest.raises(ValueError, match="site must be a Site"):
            _page(mock_site_no_http, site=site)

    def test_init_accepts_missing_user_and_timestamp_metadata(self, mock_site_no_http: Any) -> None:
        page = _page(mock_site_no_http)

        assert page.created_by is None
        assert page.created_at is None
        assert page.updated_by is None
        assert page.updated_at is None
        assert page.commented_by is None
        assert page.commented_at is None

    def test_init_accepts_valid_user_and_timestamp_metadata(self, mock_site_no_http: Any) -> None:
        user = User(client=mock_site_no_http.client, id=12345, name="test-user", unix_name="test-user")
        timestamp = datetime(2023, 1, 1, 12, 0, 0)

        page = _page(
            mock_site_no_http,
            created_by=user,
            created_at=timestamp,
            updated_by=user,
            updated_at=timestamp,
            commented_by=user,
            commented_at=timestamp,
        )

        assert page.created_by == user
        assert page.created_at == timestamp
        assert page.updated_by == user
        assert page.updated_at == timestamp
        assert page.commented_by == user
        assert page.commented_at == timestamp

    @pytest.mark.parametrize("field", ["created_by", "updated_by", "commented_by"])
    @pytest.mark.parametrize("value", [True, 12345, "test-user", {"id": 12345}, object()])
    def test_init_rejects_malformed_user_metadata(self, mock_site_no_http: Any, field: str, value: Any) -> None:
        with pytest.raises(ValueError, match=f"{field} must be an AbstractUser or None"):
            _page(mock_site_no_http, **{field: value})

    @pytest.mark.parametrize("field", ["created_at", "updated_at", "commented_at"])
    @pytest.mark.parametrize("value", [True, 1700000000, "2023-01-01", [], object()])
    def test_init_rejects_malformed_timestamp_metadata(self, mock_site_no_http: Any, field: str, value: Any) -> None:
        with pytest.raises(ValueError, match=f"{field} must be a datetime or None"):
            _page(mock_site_no_http, **{field: value})
