"""Page constructor validation tests."""

from typing import Any

import pytest

from wikidot.module.page import Page


def _page(mock_site_no_http: Any, **overrides: Any) -> Page:
    values: dict[str, Any] = {
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
        site=mock_site_no_http,
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

        assert page.fullname == "test-page"
        assert page.name == "test-page"
        assert page.category == "_default"
        assert page.title == "Test Page Title"

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
