"""PageVotesモジュールのユニットテスト"""

from unittest.mock import MagicMock

import pytest

from wikidot.module.page_votes import PageVote, PageVoteCollection
from wikidot.module.user import User


class TestPageVoteCollection:
    """PageVoteCollectionのテスト"""

    @staticmethod
    def _user(user_id: int, name: str = "test-user") -> User:
        return User(client=MagicMock(), id=user_id, name=name, unix_name=name)

    def test_init_with_page_and_votes(self):
        """ページと投票リストで初期化"""
        page = MagicMock()
        vote1 = MagicMock(spec=PageVote)
        vote2 = MagicMock(spec=PageVote)

        collection = PageVoteCollection(page, [vote1, vote2])

        assert collection.page == page
        assert len(collection) == 2

    def test_init_with_empty_votes(self):
        """空の投票リストで初期化"""
        page = MagicMock()

        collection = PageVoteCollection(page, [])

        assert collection.page == page
        assert len(collection) == 0

    def test_iter(self):
        """イテレーション"""
        page = MagicMock()
        user1 = self._user(1, "user-one")
        user2 = self._user(2, "user-two")
        vote1 = PageVote(page=page, user=user1, value=1)
        vote2 = PageVote(page=page, user=user2, value=-1)

        collection = PageVoteCollection(page, [vote1, vote2])

        votes = list(collection)
        assert len(votes) == 2
        assert votes[0].value == 1
        assert votes[1].value == -1

    def test_find_existing_vote(self):
        """存在する投票を検索"""
        page = MagicMock()
        user1 = self._user(12345, "user-one")
        user2 = self._user(67890, "user-two")
        vote1 = PageVote(page=page, user=user1, value=1)
        vote2 = PageVote(page=page, user=user2, value=-1)

        collection = PageVoteCollection(page, [vote1, vote2])

        search_user = self._user(12345, "search-user")

        result = collection.find(search_user)

        assert result.value == 1
        assert result.user.id == 12345

    def test_find_nonexistent_vote_raises(self):
        """存在しない投票の検索でValueError"""
        page = MagicMock()
        page.__str__ = lambda x: "TestPage"
        user1 = self._user(12345, "user-one")
        vote1 = PageVote(page=page, user=user1, value=1)

        collection = PageVoteCollection(page, [vote1])

        search_user = self._user(99999, "unknown-user")

        with pytest.raises(ValueError, match="has not voted"):
            collection.find(search_user)

    @pytest.mark.parametrize("user", [None, True, "12345", {"id": 12345}])
    def test_find_rejects_non_user_values(self, user: object) -> None:
        """findの検索対象はAbstractUserだけ受け付ける"""
        page = MagicMock()
        collection = PageVoteCollection(page, [PageVote(page=page, user=self._user(1), value=1)])

        with pytest.raises(ValueError, match="user must be an AbstractUser"):
            collection.find(user)

    @pytest.mark.parametrize(
        "user",
        [
            User(client=MagicMock(), id=None, name="missing-id", unix_name="missing-id"),
            User(client=MagicMock(), id=True, name="bool-id", unix_name="bool-id"),
            User(client=MagicMock(), id="12345", name="string-id", unix_name="string-id"),
        ],
    )
    def test_find_rejects_users_without_integer_id(self, user: User) -> None:
        """findの検索対象user.idはbool以外の整数だけ受け付ける"""
        page = MagicMock()
        collection = PageVoteCollection(page, [PageVote(page=page, user=self._user(1), value=1)])

        with pytest.raises(ValueError, match="user.id must be an integer"):
            collection.find(user)


class TestPageVote:
    """PageVoteのテスト"""

    def test_init(self):
        """初期化"""
        page = MagicMock()
        user = MagicMock()

        vote = PageVote(page=page, user=user, value=1)

        assert vote.page == page
        assert vote.user == user
        assert vote.value == 1

    def test_positive_vote(self):
        """正の投票"""
        page = MagicMock()
        user = MagicMock()

        vote = PageVote(page=page, user=user, value=1)

        assert vote.value == 1

    def test_negative_vote(self):
        """負の投票"""
        page = MagicMock()
        user = MagicMock()

        vote = PageVote(page=page, user=user, value=-1)

        assert vote.value == -1

    def test_numeric_vote(self):
        """数値投票（5段階評価など）"""
        page = MagicMock()
        user = MagicMock()

        vote = PageVote(page=page, user=user, value=5)

        assert vote.value == 5
