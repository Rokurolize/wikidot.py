"""Page constructor validation tests."""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from wikidot.module.client import Client
from wikidot.module.forum_thread import ForumThread
from wikidot.module.page import Page
from wikidot.module.page_file import PageFile, PageFileCollection
from wikidot.module.page_revision import PageRevision, PageRevisionCollection
from wikidot.module.page_source import PageSource
from wikidot.module.page_votes import PageVote, PageVoteCollection
from wikidot.module.user import User


def _client() -> Client:
    client: Any = object.__new__(Client)
    client.is_logged_in = False
    client.username = None
    client.me = None
    client.login_check = MagicMock()
    return client


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
        "_id": None,
        "_source": None,
        "_revisions": None,
        "_votes": None,
        "_metas": None,
        "_discussion": None,
        "_discussion_checked": False,
        "_files": None,
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
        _id=values["_id"],
        _source=values["_source"],
        _revisions=values["_revisions"],
        _votes=values["_votes"],
        _metas=values["_metas"],
        _discussion=values["_discussion"],
        _discussion_checked=values["_discussion_checked"],
        _files=values["_files"],
    )


def _page_revision(page: Page, revision_id: int = 100) -> PageRevision:
    return PageRevision(
        page=page,
        id=revision_id,
        rev_no=1,
        created_by=User(client=page.site.client, id=12345, name="test-user", unix_name="test-user"),
        created_at=datetime(2023, 1, 1),
        comment="cached revision",
    )


def _page_vote(page: Page, value: int = 1) -> PageVote:
    return PageVote(
        page=page,
        user=User(client=page.site.client, id=12345, name="test-user", unix_name="test-user"),
        value=value,
    )


def _page_file(page: Page, file_id: int = 100) -> PageFile:
    return PageFile(
        page=page,
        id=file_id,
        name="cached.txt",
        url=f"{page.site.url}/local--files/{page.fullname}/cached.txt",
        mime_type="text/plain",
        size=100,
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

    @pytest.mark.parametrize("rating_percent", [None, 0.0, 0.75, 1])
    def test_init_accepts_valid_rating_percent(
        self, mock_site_no_http: Any, rating_percent: int | float | None
    ) -> None:
        page = _page(mock_site_no_http, rating_percent=rating_percent)

        assert page.rating_percent == rating_percent

    @pytest.mark.parametrize("rating_percent", [True, "0.75", [], {}, object()])
    def test_init_rejects_malformed_rating_percent(self, mock_site_no_http: Any, rating_percent: Any) -> None:
        with pytest.raises(ValueError, match="rating_percent must be an integer, float, or None"):
            _page(mock_site_no_http, rating_percent=rating_percent)

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

    @pytest.mark.parametrize("field", ["created_by", "updated_by", "commented_by"])
    def test_init_rejects_user_metadata_from_different_client(self, mock_site_no_http: Any, field: str) -> None:
        user = User(client=_client(), id=12345, name="test-user", unix_name="test-user")

        with pytest.raises(ValueError, match=f"{field} must belong to the site"):
            _page(mock_site_no_http, **{field: user})

    @pytest.mark.parametrize("field", ["created_at", "updated_at", "commented_at"])
    @pytest.mark.parametrize("value", [True, 1700000000, "2023-01-01", [], object()])
    def test_init_rejects_malformed_timestamp_metadata(self, mock_site_no_http: Any, field: str, value: Any) -> None:
        with pytest.raises(ValueError, match=f"{field} must be a datetime or None"):
            _page(mock_site_no_http, **{field: value})

    @pytest.mark.parametrize("page_id", [None, 12345])
    def test_init_accepts_valid_optional_id(self, mock_site_no_http: Any, page_id: int | None) -> None:
        page = _page(mock_site_no_http, _id=page_id)

        assert page._id == page_id
        assert page.is_id_acquired() == (page_id is not None)
        if page_id is not None:
            assert page.id == page_id

    @pytest.mark.parametrize("page_id", [True, False, "12345", 12345.0, [], object()])
    def test_init_rejects_malformed_optional_id(self, mock_site_no_http: Any, page_id: Any) -> None:
        with pytest.raises(ValueError, match=r"page\.id must be an integer or None"):
            _page(mock_site_no_http, _id=page_id)

    def test_init_accepts_valid_optional_source(self, mock_site_no_http: Any) -> None:
        page_without_source = _page(mock_site_no_http)
        source_owner = _page(mock_site_no_http)
        source = PageSource(source_owner, "cached source")

        page_with_source = _page(mock_site_no_http, _source=source)

        assert page_without_source._source is None
        assert page_with_source._source == source
        assert page_with_source.source == source

    @pytest.mark.parametrize("source", [True, "cached source", {"wiki_text": "cached source"}, object()])
    def test_init_rejects_malformed_optional_source(self, mock_site_no_http: Any, source: Any) -> None:
        with pytest.raises(ValueError, match="page.source must be PageSource"):
            _page(mock_site_no_http, _source=source)

    def test_init_rejects_source_cache_from_different_page(self, mock_site_no_http: Any) -> None:
        source_owner = _page(mock_site_no_http, fullname="other-page", name="other-page")
        source = PageSource(source_owner, "cached source")

        with pytest.raises(ValueError, match=r"page\.source must belong to the page"):
            _page(mock_site_no_http, _source=source)

    def test_init_accepts_valid_optional_revisions(self, mock_site_no_http: Any) -> None:
        page_without_revisions = _page(mock_site_no_http)
        revisions_owner = _page(mock_site_no_http)
        revisions = PageRevisionCollection(revisions_owner, [])

        page_with_revisions = _page(mock_site_no_http, _revisions=revisions)

        assert page_without_revisions._revisions is None
        assert page_with_revisions._revisions == revisions
        assert page_with_revisions.revisions == revisions

    @pytest.mark.parametrize("revisions", [True, "cached revisions", [], {"revisions": []}, object()])
    def test_init_rejects_malformed_optional_revisions(self, mock_site_no_http: Any, revisions: Any) -> None:
        with pytest.raises(ValueError, match=r"page\.revisions must be PageRevisionCollection or None"):
            _page(mock_site_no_http, _revisions=revisions)

    def test_init_rejects_malformed_optional_revision_entries(self, mock_site_no_http: Any) -> None:
        revisions: Any = PageRevisionCollection(_page(mock_site_no_http), [])
        revisions.append(object())

        with pytest.raises(ValueError, match=r"page\.revisions list entries must be PageRevision"):
            _page(mock_site_no_http, _revisions=revisions)

    def test_init_rejects_revisions_cache_from_different_page(self, mock_site_no_http: Any) -> None:
        revisions = PageRevisionCollection(_page(mock_site_no_http, fullname="other-page", name="other-page"), [])

        with pytest.raises(ValueError, match=r"page\.revisions must belong to the page"):
            _page(mock_site_no_http, _revisions=revisions)

    def test_init_rejects_revisions_cache_entry_from_different_page(self, mock_site_no_http: Any) -> None:
        revisions_owner = _page(mock_site_no_http)
        revisions: Any = PageRevisionCollection(revisions_owner, [_page_revision(revisions_owner)])
        revisions[0] = _page_revision(_page(mock_site_no_http, fullname="other-page", name="other-page"), 101)

        with pytest.raises(ValueError, match=r"page\.revisions must belong to the page"):
            _page(mock_site_no_http, _revisions=revisions)

    def test_init_accepts_valid_optional_votes(self, mock_site_no_http: Any) -> None:
        page_without_votes = _page(mock_site_no_http)
        votes_owner = _page(mock_site_no_http)
        votes = PageVoteCollection(votes_owner, [])

        page_with_votes = _page(mock_site_no_http, _votes=votes)

        assert page_without_votes._votes is None
        assert page_with_votes._votes == votes
        assert page_with_votes.votes == votes

    @pytest.mark.parametrize("votes", [True, "cached votes", [], {"votes": []}, object()])
    def test_init_rejects_malformed_optional_votes(self, mock_site_no_http: Any, votes: Any) -> None:
        with pytest.raises(ValueError, match=r"page\.votes must be PageVoteCollection or None"):
            _page(mock_site_no_http, _votes=votes)

    def test_init_rejects_malformed_optional_vote_entries(self, mock_site_no_http: Any) -> None:
        votes: Any = PageVoteCollection(_page(mock_site_no_http), [])
        votes.append(object())

        with pytest.raises(ValueError, match=r"page\.votes list entries must be PageVote"):
            _page(mock_site_no_http, _votes=votes)

    def test_init_rejects_votes_cache_from_different_page(self, mock_site_no_http: Any) -> None:
        votes = PageVoteCollection(_page(mock_site_no_http, fullname="other-page", name="other-page"), [])

        with pytest.raises(ValueError, match=r"page\.votes must belong to the page"):
            _page(mock_site_no_http, _votes=votes)

    def test_init_rejects_votes_cache_entry_from_different_page(self, mock_site_no_http: Any) -> None:
        votes_owner = _page(mock_site_no_http)
        votes: Any = PageVoteCollection(votes_owner, [_page_vote(votes_owner)])
        votes[0] = _page_vote(_page(mock_site_no_http, fullname="other-page", name="other-page"), -1)

        with pytest.raises(ValueError, match=r"page\.votes must belong to the page"):
            _page(mock_site_no_http, _votes=votes)

    def test_init_accepts_valid_optional_files(self, mock_site_no_http: Any) -> None:
        page_without_files = _page(mock_site_no_http)
        files_owner = _page(mock_site_no_http)
        files = PageFileCollection(files_owner, [])

        page_with_files = _page(mock_site_no_http, _files=files)

        assert page_without_files._files is None
        assert page_with_files._files == files
        assert page_with_files.files == files

    @pytest.mark.parametrize("files", [True, "cached files", [], {"files": []}, object()])
    def test_init_rejects_malformed_optional_files(self, mock_site_no_http: Any, files: Any) -> None:
        with pytest.raises(ValueError, match=r"page\.files must be PageFileCollection or None"):
            _page(mock_site_no_http, _files=files)

    def test_init_rejects_malformed_optional_file_entries(self, mock_site_no_http: Any) -> None:
        files: Any = PageFileCollection(_page(mock_site_no_http), [])
        files.append(object())

        with pytest.raises(ValueError, match=r"page\.files list entries must be PageFile"):
            _page(mock_site_no_http, _files=files)

    def test_init_rejects_files_cache_from_different_page(self, mock_site_no_http: Any) -> None:
        files = PageFileCollection(_page(mock_site_no_http, fullname="other-page", name="other-page"), [])

        with pytest.raises(ValueError, match=r"page\.files must belong to the page"):
            _page(mock_site_no_http, _files=files)

    def test_init_rejects_files_cache_entry_from_different_page(self, mock_site_no_http: Any) -> None:
        files_owner = _page(mock_site_no_http)
        files: Any = PageFileCollection(files_owner, [_page_file(files_owner)])
        files[0] = _page_file(_page(mock_site_no_http, fullname="other-page", name="other-page"), 101)

        with pytest.raises(ValueError, match=r"page\.files must belong to the page"):
            _page(mock_site_no_http, _files=files)

    def test_init_accepts_valid_optional_metas(self, mock_site_no_http: Any) -> None:
        page_without_metas = _page(mock_site_no_http)
        metas = {"description": "cached description", "og:title": "Cached title"}

        page_with_metas = _page(mock_site_no_http, _metas=metas)

        assert page_without_metas._metas is None
        assert page_with_metas._metas == metas
        assert page_with_metas.metas == metas

    @pytest.mark.parametrize("metas", [True, "cached metas", [("description", "cached")], object()])
    def test_init_rejects_non_dict_optional_metas(self, mock_site_no_http: Any, metas: Any) -> None:
        with pytest.raises(ValueError, match="metas must be a dictionary"):
            _page(mock_site_no_http, _metas=metas)

    @pytest.mark.parametrize("metas", [{3: "description"}, {None: "description"}])
    def test_init_rejects_non_string_optional_meta_keys(self, mock_site_no_http: Any, metas: Any) -> None:
        with pytest.raises(ValueError, match="metas keys must be strings"):
            _page(mock_site_no_http, _metas=metas)

    @pytest.mark.parametrize("metas", [{"description": 3}, {"description": None}, {"description": object()}])
    def test_init_rejects_non_string_optional_meta_values(self, mock_site_no_http: Any, metas: Any) -> None:
        with pytest.raises(ValueError, match="metas values must be strings"):
            _page(mock_site_no_http, _metas=metas)

    def test_init_accepts_valid_optional_discussion(self, mock_site_no_http: Any) -> None:
        page_without_discussion = _page(mock_site_no_http)
        creator = User(client=mock_site_no_http.client, id=12345, name="test-user", unix_name="test-user")
        discussion = ForumThread(
            site=mock_site_no_http,
            id=3001,
            title="Discussion thread",
            description="Discussion thread description",
            created_by=creator,
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            post_count=0,
        )

        page_with_discussion = _page(mock_site_no_http, _discussion=discussion, _discussion_checked=True)
        page_without_thread = _page(mock_site_no_http, _discussion=None, _discussion_checked=True)

        assert page_without_discussion._discussion is None
        assert page_without_discussion._discussion_checked is False
        assert page_with_discussion._discussion == discussion
        assert page_with_discussion._discussion_checked is True
        assert page_with_discussion.discussion == discussion
        assert page_without_thread._discussion is None
        assert page_without_thread._discussion_checked is True
        assert page_without_thread.discussion is None

    @pytest.mark.parametrize("discussion", [True, "cached discussion", {"id": 3001}, object()])
    def test_init_rejects_malformed_optional_discussion(self, mock_site_no_http: Any, discussion: Any) -> None:
        with pytest.raises(ValueError, match=r"page\.discussion must be ForumThread or None"):
            _page(mock_site_no_http, _discussion=discussion)

    @pytest.mark.parametrize("discussion_checked", [None, "true", 1, 0, [], object()])
    def test_init_rejects_malformed_discussion_checked(self, mock_site_no_http: Any, discussion_checked: Any) -> None:
        with pytest.raises(ValueError, match=r"page\.discussion_checked must be a boolean"):
            _page(mock_site_no_http, _discussion_checked=discussion_checked)
