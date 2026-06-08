"""PageVotesモジュールのユニットテスト"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from wikidot.module.client import Client
from wikidot.module.page import Page
from wikidot.module.page_votes import PageVote, PageVoteCollection
from wikidot.module.site import Site
from wikidot.module.user import User


def _client() -> Client:
    client: Any = object.__new__(Client)
    client.is_logged_in = False
    client.username = None
    client.me = None
    client.login_check = MagicMock()
    return client


def _page() -> Page:
    """HTTPなしで使う実Page"""
    site = Site(
        client=_client(),
        id=123456,
        title="Test Site",
        unix_name="test-site",
        domain="test.wikidot.com",
        ssl_supported=True,
    )
    site.amc_request = MagicMock()
    site.amc_request_with_retry = MagicMock()
    user = User(client=site.client, id=12345, name="test-user", unix_name="test-user")
    timestamp = datetime(2023, 1, 1, 12, 0, 0)
    return Page(
        site=site,
        fullname="test-page",
        name="test-page",
        category="_default",
        title="Test Page Title",
        children_count=0,
        comments_count=0,
        size=1000,
        rating=10,
        votes_count=5,
        rating_percent=0.5,
        revisions_count=3,
        parent_fullname=None,
        tags=["tag1", "tag2"],
        created_by=user,
        created_at=timestamp,
        updated_by=user,
        updated_at=timestamp,
        commented_by=None,
        commented_at=None,
        _id=12345,
    )


def _page_on_same_site(page: Page, fullname: str = "other-page") -> Page:
    other_page = _page()
    other_page.site = page.site
    other_page.fullname = fullname
    other_page.name = fullname
    other_page._id = 67890
    return other_page


def _vote_user(page: Page, user_id: int = 12345, name: str = "test-user") -> User:
    return User(client=page.site.client, id=user_id, name=name, unix_name=name)


class TestPageVoteCollection:
    """PageVoteCollectionのテスト"""

    @staticmethod
    def _user(page: Page, user_id: int, name: str = "test-user") -> User:
        return User(client=page.site.client, id=user_id, name=name, unix_name=name)

    def test_init_with_page_and_votes(self):
        """ページと投票リストで初期化"""
        page = _page()
        user1 = self._user(page, 1, "user-one")
        user2 = self._user(page, 2, "user-two")
        vote1 = PageVote(page=page, user=user1, value=1)
        vote2 = PageVote(page=page, user=user2, value=-1)

        collection = PageVoteCollection(page, [vote1, vote2])

        assert collection.page == page
        assert len(collection) == 2

    def test_init_rejects_vote_from_different_page(self) -> None:
        """投票コレクションの要素はcollection pageに属する投票だけ受け付ける"""
        page = _page()
        other_page = _page_on_same_site(page)
        vote = PageVote(page=other_page, user=self._user(other_page, 1), value=1)

        with pytest.raises(ValueError, match="votes must belong to the collection page"):
            PageVoteCollection(page, [vote])

    @pytest.mark.parametrize("page", [None, True, "test-page", {"fullname": "test-page"}, object()])
    def test_init_rejects_malformed_pages(self, page: object) -> None:
        """投票コレクションの初期化は実Pageだけ受け付ける"""
        bad_page: Any = page

        with pytest.raises(ValueError, match="page must be a Page"):
            PageVoteCollection(bad_page, [])

    @pytest.mark.parametrize("votes", [None, True, "vote", ("vote",)])
    def test_init_rejects_non_list_votes(self, votes: object) -> None:
        """投票コレクションの初期化はlistだけ受け付ける"""
        page = _page()
        bad_votes: Any = votes

        with pytest.raises(ValueError, match="votes must be a list"):
            PageVoteCollection(page, bad_votes)

    @pytest.mark.parametrize("vote", [None, True, "vote", {"user": 1}])
    def test_init_rejects_non_vote_entries(self, vote: object) -> None:
        """投票コレクションの初期化はPageVote要素だけ受け付ける"""
        page = _page()
        bad_votes: Any = [vote]

        with pytest.raises(ValueError, match="votes list entries must be PageVote"):
            PageVoteCollection(page, bad_votes)

    def test_init_with_empty_votes(self):
        """空の投票リストで初期化"""
        page = _page()

        collection = PageVoteCollection(page, [])

        assert collection.page == page
        assert len(collection) == 0

    def test_iter(self):
        """イテレーション"""
        page = _page()
        user1 = self._user(page, 1, "user-one")
        user2 = self._user(page, 2, "user-two")
        vote1 = PageVote(page=page, user=user1, value=1)
        vote2 = PageVote(page=page, user=user2, value=-1)

        collection = PageVoteCollection(page, [vote1, vote2])

        votes = list(collection)
        assert len(votes) == 2
        assert votes[0].value == 1
        assert votes[1].value == -1

    def test_find_existing_vote(self):
        """存在する投票を検索"""
        page = _page()
        user1 = self._user(page, 12345, "user-one")
        user2 = self._user(page, 67890, "user-two")
        vote1 = PageVote(page=page, user=user1, value=1)
        vote2 = PageVote(page=page, user=user2, value=-1)

        collection = PageVoteCollection(page, [vote1, vote2])

        search_user = self._user(page, 12345, "search-user")

        result = collection.find(search_user)

        assert result.value == 1
        assert result.user.id == 12345

    def test_find_nonexistent_vote_raises(self):
        """存在しない投票の検索でValueError"""
        page = _page()
        user1 = self._user(page, 12345, "user-one")
        vote1 = PageVote(page=page, user=user1, value=1)

        collection = PageVoteCollection(page, [vote1])

        search_user = self._user(page, 99999, "unknown-user")

        with pytest.raises(ValueError, match="has not voted"):
            collection.find(search_user)

    @pytest.mark.parametrize("user", [None, True, "12345", {"id": 12345}])
    def test_find_rejects_non_user_values(self, user: object) -> None:
        """findの検索対象はAbstractUserだけ受け付ける"""
        page = _page()
        collection = PageVoteCollection(page, [PageVote(page=page, user=self._user(page, 1), value=1)])
        bad_user: Any = user

        with pytest.raises(ValueError, match="user must be an AbstractUser"):
            collection.find(bad_user)

    @pytest.mark.parametrize(
        ("user_id", "name"),
        [
            (None, "missing-id"),
            (True, "bool-id"),
            ("12345", "string-id"),
        ],
    )
    def test_find_rejects_users_without_integer_id(self, user_id: object, name: str) -> None:
        """findの検索対象user.idはbool以外の整数だけ受け付ける"""
        page = _page()
        collection = PageVoteCollection(page, [PageVote(page=page, user=self._user(page, 1), value=1)])
        bad_user_id: Any = user_id
        user = User(client=page.site.client, id=12345, name=name, unix_name=name)
        user.id = bad_user_id

        with pytest.raises(ValueError, match="user.id must be an integer"):
            collection.find(user)


class TestPageVote:
    """PageVoteのテスト"""

    def test_init(self):
        """初期化"""
        page = _page()
        user = _vote_user(page)

        vote = PageVote(page=page, user=user, value=1)

        assert vote.page == page
        assert vote.user == user
        assert vote.value == 1

    def test_positive_vote(self):
        """正の投票"""
        page = _page()
        user = _vote_user(page)

        vote = PageVote(page=page, user=user, value=1)

        assert vote.value == 1

    def test_negative_vote(self):
        """負の投票"""
        page = _page()
        user = _vote_user(page)

        vote = PageVote(page=page, user=user, value=-1)

        assert vote.value == -1

    def test_numeric_vote(self):
        """数値投票（5段階評価など）"""
        page = _page()
        user = _vote_user(page)

        vote = PageVote(page=page, user=user, value=5)

        assert vote.value == 5

    @pytest.mark.parametrize("user", [None, True, "test-user", {"id": 12345}, object()])
    def test_init_rejects_malformed_users(self, user: object) -> None:
        """投票の初期化はAbstractUserだけ受け付ける"""
        page = _page()
        bad_user: Any = user

        with pytest.raises(ValueError, match="user must be an AbstractUser"):
            PageVote(page=page, user=bad_user, value=1)

    def test_init_rejects_user_from_different_client(self) -> None:
        """投票ユーザーはページのsite clientに属するユーザーだけ受け付ける"""
        page = _page()
        user = User(client=_client(), id=12345, name="test-user", unix_name="test-user")

        with pytest.raises(ValueError, match="user must belong to the site"):
            PageVote(page=page, user=user, value=1)

    @pytest.mark.parametrize("value", [None, True, "1", 1.0, []])
    def test_init_rejects_malformed_values(self, value: object) -> None:
        """投票の初期化はbool以外の整数値だけ受け付ける"""
        page = _page()
        bad_value: Any = value

        with pytest.raises(ValueError, match="value must be an integer"):
            PageVote(page=page, user=_vote_user(page), value=bad_value)

    @pytest.mark.parametrize("page", [None, True, "test-page", {"fullname": "test-page"}, object()])
    def test_init_rejects_malformed_pages(self, page: object) -> None:
        """投票の初期化は実Pageだけ受け付ける"""
        bad_page: Any = page
        reference_page = _page()
        user = _vote_user(reference_page)

        with pytest.raises(ValueError, match="page must be a Page"):
            PageVote(page=bad_page, user=user, value=1)
