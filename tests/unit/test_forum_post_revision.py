"""ForumPostRevisionモジュールのユニットテスト"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

from wikidot.common import exceptions
from wikidot.module.client import Client
from wikidot.module.forum_post import ForumPost
from wikidot.module.forum_post_revision import ForumPostRevision, ForumPostRevisionCollection
from wikidot.module.forum_thread import ForumThread
from wikidot.module.site import Site
from wikidot.module.user import User

if TYPE_CHECKING:
    from wikidot.module.forum_post import ForumPost


def _client() -> Client:
    client: Any = object.__new__(Client)
    client.is_logged_in = False
    client.username = None
    client.me = None
    client.login_check = MagicMock()
    return client


def _user(client: Any) -> User:
    return User(client=client, id=12345, name="test-user", unix_name="test-user")


def _post_with_id(source_post: ForumPost, post_id: int) -> ForumPost:
    return ForumPost(
        thread=source_post.thread,
        id=post_id,
        title=f"Post {post_id}",
        text=source_post.text,
        element=source_post.element,
        created_by=source_post.created_by,
        created_at=source_post.created_at,
        edited_by=source_post.edited_by,
        edited_at=source_post.edited_at,
        _parent_id=source_post.parent_id,
    )


# ============================================================
# ForumPostRevisionCollectionテスト
# ============================================================


class TestForumPostRevisionCollectionInit:
    """ForumPostRevisionCollectionの初期化テスト"""

    def test_init_with_post_and_empty_revisions(self, mock_forum_post_no_http: ForumPost) -> None:
        """ポストと空のリビジョンリストで初期化できる"""
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, [])
        assert collection.post == mock_forum_post_no_http
        assert len(collection) == 0

    def test_init_empty_without_post_exposes_none_post(self) -> None:
        """空の親なしリビジョンコレクションはpost=Noneを保持する"""
        collection = ForumPostRevisionCollection(post=None, revisions=[])
        assert collection.post is None
        assert len(collection) == 0

    def test_init_with_post_and_revisions(self, mock_forum_post_no_http: ForumPost) -> None:
        """ポストとリビジョンリストで初期化できる"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, [revision])
        assert collection.post == mock_forum_post_no_http
        assert len(collection) == 1

    def test_init_rejects_revision_from_different_post(self, mock_forum_post_no_http: ForumPost) -> None:
        """明示親と異なるpostのrevisionは初期化時に拒否する"""
        revision = ForumPostRevision(
            post=_post_with_id(mock_forum_post_no_http, 5002),
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )

        with pytest.raises(ValueError, match="revisions must belong to the collection post"):
            ForumPostRevisionCollection(mock_forum_post_no_http, [revision])

    def test_init_rejects_mixed_post_revisions_when_post_is_inferred(self, mock_forum_post_no_http: ForumPost) -> None:
        """推論親と異なるpostのrevision混在も初期化時に拒否する"""
        revisions = [
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=0,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
            ),
            ForumPostRevision(
                post=_post_with_id(mock_forum_post_no_http, 5002),
                id=9002,
                rev_no=1,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
            ),
        ]

        with pytest.raises(ValueError, match="revisions must belong to the collection post"):
            ForumPostRevisionCollection(post=None, revisions=revisions)

    @pytest.mark.parametrize("post", [True, "5001", {"id": 5001}, object()])
    def test_init_rejects_malformed_posts(self, post: object) -> None:
        """明示されたpostはForumPostだけ受け付ける"""
        bad_post: Any = post

        with pytest.raises(ValueError, match="post must be a ForumPost"):
            ForumPostRevisionCollection(post=bad_post, revisions=[])

    @pytest.mark.parametrize("revisions", [True, False, "9001", ("9001",), 9001])
    def test_init_rejects_non_list_revisions(self, mock_forum_post_no_http: ForumPost, revisions: object) -> None:
        """リビジョンコレクションの初期化はlistまたはNoneだけ受け付ける"""
        bad_revisions: Any = revisions

        with pytest.raises(ValueError, match="revisions must be a list or None"):
            ForumPostRevisionCollection(mock_forum_post_no_http, bad_revisions)

    @pytest.mark.parametrize("revision", [None, True, "9001", {"id": 9001}])
    def test_init_rejects_non_revision_entries(self, mock_forum_post_no_http: ForumPost, revision: object) -> None:
        """リビジョンコレクションの初期化はForumPostRevision要素だけ受け付ける"""
        bad_revisions: Any = [revision]

        with pytest.raises(ValueError, match="revisions list entries must be ForumPostRevision"):
            ForumPostRevisionCollection(mock_forum_post_no_http, bad_revisions)


class TestForumPostRevisionCollectionFind:
    """ForumPostRevisionCollection.findのテスト"""

    def test_find_existing(self, mock_forum_post_no_http: ForumPost) -> None:
        """存在するリビジョンをIDで検索できる"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, [revision])
        found = collection.find(9001)
        assert found is not None
        assert found.id == 9001

    def test_find_nonexistent(self, mock_forum_post_no_http: ForumPost) -> None:
        """存在しないリビジョンを検索するとNoneを返す"""
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, [])
        found = collection.find(9999)
        assert found is None

    @pytest.mark.parametrize("revision_id", [None, True, "9001", 9001.0])
    def test_find_rejects_non_integer_ids(self, mock_forum_post_no_http: ForumPost, revision_id: object) -> None:
        """findは整数以外の検索IDを拒否する"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, [revision])

        bad_revision_id: Any = revision_id
        with pytest.raises(ValueError, match="id must be an integer"):
            collection.find(bad_revision_id)


class TestForumPostRevisionCollectionFindByRevNo:
    """ForumPostRevisionCollection.find_by_rev_noのテスト"""

    def test_find_by_rev_no_existing(self, mock_forum_post_no_http: ForumPost) -> None:
        """存在するリビジョンをリビジョン番号で検索できる"""
        revisions = [
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=0,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
            ),
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9002,
                rev_no=1,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
            ),
        ]
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, revisions)
        found = collection.find_by_rev_no(1)
        assert found is not None
        assert found.id == 9002
        assert found.rev_no == 1

    def test_find_by_rev_no_nonexistent(self, mock_forum_post_no_http: ForumPost) -> None:
        """存在しないリビジョン番号を検索するとNoneを返す"""
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, [])
        found = collection.find_by_rev_no(99)
        assert found is None

    @pytest.mark.parametrize("rev_no", [None, True, "1", 1.0])
    def test_find_by_rev_no_rejects_non_integer_revision_numbers(
        self, mock_forum_post_no_http: ForumPost, rev_no: object
    ) -> None:
        """find_by_rev_noは整数以外のリビジョン番号を拒否する"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9002,
            rev_no=1,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, [revision])

        bad_rev_no: Any = rev_no
        with pytest.raises(ValueError, match="rev_no must be an integer"):
            collection.find_by_rev_no(bad_rev_no)


class TestForumPostRevisionCollectionParse:
    """ForumPostRevisionCollection._parseのテスト"""

    def test_parse_success(self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]) -> None:
        """リビジョン一覧を正常にパースできる"""
        html = BeautifulSoup(forum_post_revisions["body"], "lxml")
        revisions = ForumPostRevisionCollection._parse(mock_forum_post_no_http, html)
        # API returns newest first (9003, 9002, 9001), _parse reverses to oldest first
        assert len(revisions) == 3
        # 古い順にソートされていることを確認
        assert revisions[0].id == 9001
        assert revisions[1].id == 9002
        assert revisions[2].id == 9003

    def test_parse_rev_no(self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]) -> None:
        """リビジョン番号が正しく設定される"""
        html = BeautifulSoup(forum_post_revisions["body"], "lxml")
        revisions = ForumPostRevisionCollection._parse(mock_forum_post_no_http, html)
        assert revisions[0].rev_no == 0  # 初版
        assert revisions[1].rev_no == 1
        assert revisions[2].rev_no == 2

    def test_parse_single(
        self, mock_forum_post_no_http: ForumPost, forum_post_revisions_single: dict[str, Any]
    ) -> None:
        """単一リビジョンをパースできる"""
        html = BeautifulSoup(forum_post_revisions_single["body"], "lxml")
        revisions = ForumPostRevisionCollection._parse(mock_forum_post_no_http, html)
        assert len(revisions) == 1
        assert revisions[0].rev_no == 0

    def test_parse_uses_revision_cells_for_metadata(self, mock_forum_post_no_http: ForumPost) -> None:
        """行内のネスト要素ではなくリビジョン表のセルからメタデータを読む"""
        html = BeautifulSoup(
            """
            <div class="title">Post Revisions</div>
            <table class="table">
                <tr>
                    <td>
                        <div class="preview">
                            <span class="printuser">
                                <a href="http://www.wikidot.com/user:info/wrong-user"
                                   onclick="WIKIDOT.page.listeners.userInfo(11111); return false;">wrong_user</a>
                            </span>
                            <span class="odate time_1700000500">17 Dec 2025, 12:08</span>
                            <a href="javascript:;"
                               onclick="WIKIDOT.modules.ForumViewThreadModule.listeners.showRevision(event, 9999)">
                                Wrong revision
                            </a>
                        </div>
                        <span class="printuser">
                            <a href="http://www.wikidot.com/user:info/test-user"
                               onclick="WIKIDOT.page.listeners.userInfo(12345); return false;">test_user</a>
                        </span>
                    </td>
                    <td>
                        <span class="odate time_1700000000">17 Dec 2025, 12:00</span>
                    </td>
                    <td>
                        <a href="javascript:;"
                           onclick="WIKIDOT.modules.ForumViewThreadModule.listeners.showRevision(event, 9001)">
                            View revision
                        </a>
                    </td>
                </tr>
            </table>
            """,
            "lxml",
        )

        revisions = ForumPostRevisionCollection._parse(mock_forum_post_no_http, html)

        assert len(revisions) == 1
        assert revisions[0].id == 9001
        assert revisions[0].created_by.name == "test_user"
        assert revisions[0].created_by.unix_name == "test-user"
        assert revisions[0].created_at == datetime.fromtimestamp(1700000000)


class TestForumPostRevisionCollectionAcquireAll:
    """ForumPostRevisionCollection.acquire_allのテスト"""

    @pytest.mark.parametrize("post", [None, True, "5001"])
    def test_acquire_all_rejects_non_post_before_fetch(self, post: object) -> None:
        """単一postがForumPostでない場合は取得前に拒否する"""
        bad_post: Any = post

        with pytest.raises(ValueError, match="post must be a ForumPost"):
            ForumPostRevisionCollection.acquire_all(bad_post)

    def test_acquire_all_rejects_mutated_thread_before_fetch(self, mock_forum_post_no_http: ForumPost) -> None:
        """単一postのmutateされた非ForumThread親は取得前に拒否する"""
        bad_thread: Any = MagicMock()
        mock_forum_post_no_http.thread = bad_thread

        with pytest.raises(ValueError, match="thread must be a ForumThread"):
            ForumPostRevisionCollection.acquire_all(mock_forum_post_no_http)

        bad_thread.site.amc_request_with_retry.assert_not_called()
        assert mock_forum_post_no_http._revisions is None

    def test_acquire_all_retries_transient_fetch_failures(
        self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]
    ) -> None:
        """リビジョン一覧取得の一時失敗をretryする"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_post_revisions
        mock_forum_post_no_http.thread.site.amc_request = MagicMock(return_value=[RuntimeError("transient")])
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumPostRevisionCollection.acquire_all(mock_forum_post_no_http)

        assert len(collection) == 3
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "moduleName": "forum/sub/ForumPostRevisionsModule",
                    "postId": 5001,
                }
            ]
        )

    def test_acquire_all_raises_when_retry_is_exhausted(self, mock_forum_post_no_http: ForumPost) -> None:
        """リビジョン一覧取得のretryを使い切った場合はsite/post付きで失敗する"""
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(None,))

        with pytest.raises(
            exceptions.UnexpectedException,
            match="Cannot retrieve forum post revisions for site: test-site, post: 5001",
        ):
            ForumPostRevisionCollection.acquire_all(mock_forum_post_no_http)

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "moduleName": "forum/sub/ForumPostRevisionsModule",
                    "postId": 5001,
                }
            ]
        )

    def test_acquire_all_missing_response_body_includes_site_and_post_context(
        self, mock_forum_post_no_http: ForumPost
    ) -> None:
        """リビジョン一覧レスポンスのbody欠損はsite/post付きNoElementException"""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match="Forum post revision list response body is not found for site: test-site, post: 5001",
        ):
            ForumPostRevisionCollection.acquire_all(mock_forum_post_no_http)

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "moduleName": "forum/sub/ForumPostRevisionsModule",
                    "postId": 5001,
                }
            ]
        )

    def test_acquire_all_malformed_response_body_type_includes_site_post_and_type_context(
        self, mock_forum_post_no_http: ForumPost
    ) -> None:
        """リビジョン一覧レスポンスのbody型異常はsite/post/type付きNoElementException"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": ["not", "html"]}
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                "Forum post revision list response body is malformed for site: test-site, post: 5001 "
                "\\(field=body, expected=str, actual=list\\)"
            ),
        ):
            ForumPostRevisionCollection.acquire_all(mock_forum_post_no_http)

        assert mock_forum_post_no_http._revisions is None
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "moduleName": "forum/sub/ForumPostRevisionsModule",
                    "postId": 5001,
                }
            ]
        )

    def test_acquire_all_malformed_revision_id_includes_post_row_and_value_context(
        self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]
    ) -> None:
        """リビジョンID異常値は行を黙って落とさずsite/post/row/value付きで失敗する"""
        malformed_body = forum_post_revisions["body"].replace(
            "showRevision(event, 9003)",
            "showRevision(event, latest)",
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {**forum_post_revisions, "body": malformed_body}
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum post revision ID is malformed for site: test-site, post: 5001 "
                r"\(row=1, field=revision_id, "
                r"value=WIKIDOT\.modules\.ForumViewThreadModule\.listeners\.showRevision\(event, latest\)\)"
            ),
        ):
            ForumPostRevisionCollection.acquire_all(mock_forum_post_no_http)

        assert mock_forum_post_no_http._revisions is None
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()

    def test_acquire_all_malformed_odate_includes_post_row_and_value_context(
        self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]
    ) -> None:
        """リビジョン日時異常値はraw ValueErrorではなくsite/post/row/value付きで失敗する"""
        malformed_body = forum_post_revisions["body"].replace("time_1700000300", "time_latest", 1)
        mock_response = MagicMock()
        mock_response.json.return_value = {**forum_post_revisions, "body": malformed_body}
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum post revision timestamp is malformed for site: test-site, post: 5001 "
                r"\(row=1, field=created_at, value=time_latest\)"
            ),
        ):
            ForumPostRevisionCollection.acquire_all(mock_forum_post_no_http)

        assert mock_forum_post_no_http._revisions is None
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()

    def test_acquire_all_malformed_user_includes_post_row_and_value_context(
        self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]
    ) -> None:
        """リビジョンユーザー異常値はraw ValueErrorではなくsite/post/row/value付きで失敗する"""
        malformed_body = forum_post_revisions["body"].replace("userInfo(99999)", "userInfo(latest)", 1)
        mock_response = MagicMock()
        mock_response.json.return_value = {**forum_post_revisions, "body": malformed_body}
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum post revision user is malformed for site: test-site, post: 5001 "
                r"\(row=1, field=created_by, value=WIKIDOT\.page\.listeners\.userInfo\(latest\); return false;\)"
            ),
        ):
            ForumPostRevisionCollection.acquire_all(mock_forum_post_no_http)

        assert mock_forum_post_no_http._revisions is None
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()

    def test_acquire_all_skips_cached_post_revisions(self, mock_forum_post_no_http: ForumPost) -> None:
        """取得済みpost.revisionsは単一post取得でも再取得しない"""
        cached_revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        cached_collection = ForumPostRevisionCollection(mock_forum_post_no_http, [cached_revision])
        mock_forum_post_no_http._revisions = cached_collection
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(None,))

        collection = ForumPostRevisionCollection.acquire_all(mock_forum_post_no_http)

        assert collection is cached_collection
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_not_called()

    def test_acquire_all(self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]) -> None:
        """リビジョン一覧を取得できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_post_revisions
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumPostRevisionCollection.acquire_all(mock_forum_post_no_http)
        assert len(collection) == 3

    def test_acquire_all_populates_post_revisions_cache(
        self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]
    ) -> None:
        """直接取得したpost revision一覧はpost.revisionsのキャッシュとして保持する"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_post_revisions
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumPostRevisionCollection.acquire_all(mock_forum_post_no_http)

        assert mock_forum_post_no_http._revisions is collection
        assert mock_forum_post_no_http.revisions is collection
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once()


class TestForumPostRevisionCollectionAcquireAllForPosts:
    """ForumPostRevisionCollection.acquire_all_for_postsのテスト"""

    @staticmethod
    def _post_with_id(source_post: ForumPost, post_id: int) -> ForumPost:
        return ForumPost(
            thread=source_post.thread,
            id=post_id,
            title=f"Post {post_id}",
            text=source_post.text,
            element=source_post.element,
            created_by=source_post.created_by,
            created_at=source_post.created_at,
            edited_by=source_post.edited_by,
            edited_at=source_post.edited_at,
            _parent_id=source_post.parent_id,
        )

    def test_acquire_all_for_posts_rejects_non_list_posts_before_fetch(self) -> None:
        """postsがlistでない場合は取得前に拒否する"""
        bad_posts: Any = "5001"

        with pytest.raises(ValueError, match="posts must be a list"):
            ForumPostRevisionCollection.acquire_all_for_posts(bad_posts)

    @pytest.mark.parametrize("bad_post", [None, True, "5001"])
    def test_acquire_all_for_posts_rejects_non_post_entries_before_fetch(
        self, mock_forum_post_no_http: ForumPost, bad_post: object
    ) -> None:
        """postsの要素がForumPostでない場合は取得前に拒否する"""
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock()
        bad_posts: Any = [mock_forum_post_no_http, bad_post]

        with pytest.raises(ValueError, match="posts list entries must be ForumPost"):
            ForumPostRevisionCollection.acquire_all_for_posts(bad_posts)

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_not_called()

    @pytest.mark.parametrize("with_html", [None, "false", 0, 1])
    def test_acquire_all_for_posts_rejects_non_bool_with_html_before_fetch(
        self, mock_forum_post_no_http: ForumPost, with_html: Any
    ) -> None:
        """with_htmlがboolでない場合は取得前に拒否する"""
        cached_revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        mock_forum_post_no_http._revisions = ForumPostRevisionCollection(mock_forum_post_no_http, [cached_revision])
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock()

        with pytest.raises(ValueError, match="with_html must be a boolean"):
            ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http], with_html=with_html)

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_not_called()

    def test_acquire_all_for_posts_retries_transient_fetch_failures(
        self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]
    ) -> None:
        """複数postのリビジョン一覧取得の一時失敗をretryする"""
        post2 = self._post_with_id(mock_forum_post_no_http, 5002)
        response1 = MagicMock()
        response1.json.return_value = forum_post_revisions
        response2 = MagicMock()
        response2.json.return_value = forum_post_revisions
        mock_forum_post_no_http.thread.site.amc_request = MagicMock(return_value=[RuntimeError("transient"), response2])
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(response1, response2))

        result = ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http, post2])

        assert set(result) == {5001, 5002}
        assert len(result[5001]) == 3
        assert len(result[5002]) == 3
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once()

    def test_acquire_all_for_posts_populates_post_revisions_cache(
        self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]
    ) -> None:
        """複数post取得で直接取得したrevision一覧はpost.revisionsのキャッシュとして保持する"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_post_revisions
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        result = ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http])
        collection = result[mock_forum_post_no_http.id]

        assert mock_forum_post_no_http._revisions is collection
        assert mock_forum_post_no_http.revisions is collection
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once()

    def test_acquire_all_for_posts_deduplicates_duplicate_post_ids(
        self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]
    ) -> None:
        """重複したpost IDのリビジョン一覧取得は1回にまとめる"""
        duplicate_post = self._post_with_id(mock_forum_post_no_http, mock_forum_post_no_http.id)
        response = MagicMock()
        response.json.return_value = forum_post_revisions
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(response,))

        result = ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http, duplicate_post])

        assert set(result) == {5001}
        assert len(result[5001]) == 3
        assert result[5001].post == mock_forum_post_no_http
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "moduleName": "forum/sub/ForumPostRevisionsModule",
                    "postId": mock_forum_post_no_http.id,
                }
            ]
        )

    def test_acquire_all_for_posts_reuses_later_cached_duplicate_post_revisions(
        self, mock_forum_post_no_http: ForumPost
    ) -> None:
        """後続の重複postが持つ取得済みリビジョン一覧を先頭postへ再利用する"""
        cached_duplicate_post = self._post_with_id(mock_forum_post_no_http, mock_forum_post_no_http.id)
        cached_revision = ForumPostRevision(
            post=cached_duplicate_post,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
            _html="<p>Cached revision HTML</p>",
        )
        cached_collection = ForumPostRevisionCollection(cached_duplicate_post, [cached_revision])
        cached_duplicate_post._revisions = cached_collection
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock()

        result = ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http, cached_duplicate_post])

        assert set(result) == {mock_forum_post_no_http.id}
        copied_collection = result[mock_forum_post_no_http.id]
        assert copied_collection is not cached_collection
        assert copied_collection.post is mock_forum_post_no_http
        assert len(copied_collection) == 1
        copied_revision = copied_collection[0]
        assert copied_revision is not cached_revision
        assert copied_revision.post is mock_forum_post_no_http
        assert copied_revision.id == cached_revision.id
        assert copied_revision.rev_no == cached_revision.rev_no
        assert copied_revision.created_by == cached_revision.created_by
        assert copied_revision.created_at == cached_revision.created_at
        assert copied_revision.html == "<p>Cached revision HTML</p>"
        assert cached_revision.post is cached_duplicate_post
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_not_called()

    def test_acquire_all_for_posts_rejects_mixed_site_posts_before_fetch(
        self, mock_forum_post_no_http: ForumPost
    ) -> None:
        """複数siteのpost混在は先頭siteへ誤送信せず取得前に拒否する"""
        other_site = Site(
            client=mock_forum_post_no_http.thread.site.client,
            id=654321,
            title="Other Site",
            unix_name="other-site",
            domain="other-site.wikidot.com",
            ssl_supported=True,
        )
        other_thread = ForumThread(
            site=other_site,
            id=3002,
            title="Other Site Thread",
            description=mock_forum_post_no_http.thread.description,
            created_by=mock_forum_post_no_http.thread.created_by,
            created_at=mock_forum_post_no_http.thread.created_at,
            post_count=mock_forum_post_no_http.thread.post_count,
            category=mock_forum_post_no_http.thread.category,
        )
        other_post = ForumPost(
            thread=other_thread,
            id=5002,
            title="Other Site Post",
            text=mock_forum_post_no_http.text,
            element=mock_forum_post_no_http.element,
            created_by=mock_forum_post_no_http.created_by,
            created_at=mock_forum_post_no_http.created_at,
            edited_by=mock_forum_post_no_http.edited_by,
            edited_at=mock_forum_post_no_http.edited_at,
            _parent_id=mock_forum_post_no_http.parent_id,
        )
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock()
        other_site.amc_request = MagicMock()
        other_site.amc_request_with_retry = MagicMock()

        with pytest.raises(ValueError, match="posts must belong to the same Site"):
            ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http, other_post])

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_not_called()
        other_site.amc_request.assert_not_called()
        other_site.amc_request_with_retry.assert_not_called()
        assert mock_forum_post_no_http._revisions is None
        assert other_post._revisions is None

    def test_acquire_all_for_posts_skips_cached_post_revisions(
        self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]
    ) -> None:
        """取得済みpost.revisionsは再取得せず未取得postだけを取得する"""
        cached_revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        cached_collection = ForumPostRevisionCollection(mock_forum_post_no_http, [cached_revision])
        mock_forum_post_no_http._revisions = cached_collection
        uncached_post = self._post_with_id(mock_forum_post_no_http, 5002)
        response = MagicMock()
        response.json.return_value = forum_post_revisions
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(
            side_effect=lambda requests: tuple(response for _ in requests)
        )

        result = ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http, uncached_post])

        assert result[mock_forum_post_no_http.id] is cached_collection
        assert len(result[uncached_post.id]) == 3
        assert result[uncached_post.id].post == uncached_post
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "moduleName": "forum/sub/ForumPostRevisionsModule",
                    "postId": uncached_post.id,
                }
            ]
        )

    def test_acquire_all_for_posts_all_cached_skips_fetch(self, mock_forum_post_no_http: ForumPost) -> None:
        """すべて取得済みならリビジョン一覧取得を行わない"""
        cached_revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        cached_collection = ForumPostRevisionCollection(mock_forum_post_no_http, [cached_revision])
        mock_forum_post_no_http._revisions = cached_collection
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock()

        result = ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http])

        assert result == {mock_forum_post_no_http.id: cached_collection}
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_not_called()

    def test_acquire_all_for_posts_with_html_reuses_cached_revision_list(
        self, mock_forum_post_no_http: ForumPost, forum_post_revision_content: dict[str, Any]
    ) -> None:
        """with_html=Trueでも取得済みリストは再取得せずHTMLだけ取得する"""
        cached_revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        cached_collection = ForumPostRevisionCollection(mock_forum_post_no_http, [cached_revision])
        mock_forum_post_no_http._revisions = cached_collection
        html_response = MagicMock()
        html_response.json.return_value = forum_post_revision_content
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(html_response,))

        result = ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http], with_html=True)

        assert result == {mock_forum_post_no_http.id: cached_collection}
        assert cached_revision.html == str(forum_post_revision_content["content"])
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "moduleName": "forum/sub/ForumPostRevisionModule",
                    "revisionId": cached_revision.id,
                }
            ]
        )

    def test_acquire_all_for_posts_with_html_rejects_mutated_cached_revision_post_thread_before_fetch(
        self, mock_forum_post_no_http: ForumPost
    ) -> None:
        """with_html=Trueはcached revision.postの非ForumThread親をHTML取得前に拒否する"""
        revision_post = self._post_with_id(mock_forum_post_no_http, 5002)
        cached_revision = ForumPostRevision(
            post=revision_post,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        cached_collection = ForumPostRevisionCollection(mock_forum_post_no_http, [])
        cached_collection.append(cached_revision)
        mock_forum_post_no_http._revisions = cached_collection
        bad_thread: Any = MagicMock()
        revision_post.thread = bad_thread
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock()

        with pytest.raises(ValueError, match="thread must be a ForumThread"):
            ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http], with_html=True)

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_not_called()
        bad_thread.site.amc_request_with_retry.assert_not_called()
        assert cached_revision.is_html_acquired() is False

    def test_acquire_all_for_posts_with_html_rejects_mixed_site_cached_revisions_before_fetch(
        self, mock_forum_post_no_http: ForumPost
    ) -> None:
        """with_html=Trueは複数siteのcached revisionを先頭siteへ誤送信しない"""
        other_site = Site(
            client=mock_forum_post_no_http.thread.site.client,
            id=654321,
            title="Other Site",
            unix_name="other-site",
            domain="other-site.wikidot.com",
            ssl_supported=True,
        )
        other_thread = ForumThread(
            site=other_site,
            id=3002,
            title="Other Site Thread",
            description=mock_forum_post_no_http.thread.description,
            created_by=mock_forum_post_no_http.thread.created_by,
            created_at=mock_forum_post_no_http.thread.created_at,
            post_count=mock_forum_post_no_http.thread.post_count,
            category=mock_forum_post_no_http.thread.category,
        )
        other_post = ForumPost(
            thread=other_thread,
            id=5002,
            title="Other Site Post",
            text=mock_forum_post_no_http.text,
            element=mock_forum_post_no_http.element,
            created_by=mock_forum_post_no_http.created_by,
            created_at=mock_forum_post_no_http.created_at,
            edited_by=mock_forum_post_no_http.edited_by,
            edited_at=mock_forum_post_no_http.edited_at,
            _parent_id=mock_forum_post_no_http.parent_id,
        )
        cached_revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        other_cached_revision = ForumPostRevision(
            post=other_post,
            id=9002,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        mock_forum_post_no_http._revisions = ForumPostRevisionCollection(mock_forum_post_no_http, [cached_revision])
        other_post._revisions = ForumPostRevisionCollection(other_post, [other_cached_revision])
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock()
        other_site.amc_request = MagicMock()
        other_site.amc_request_with_retry = MagicMock()

        with pytest.raises(ValueError, match="posts must belong to the same Site"):
            ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http, other_post], with_html=True)

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_not_called()
        other_site.amc_request.assert_not_called()
        other_site.amc_request_with_retry.assert_not_called()
        assert cached_revision.is_html_acquired() is False
        assert other_cached_revision.is_html_acquired() is False

    def test_acquire_all_for_posts_raises_when_retry_is_exhausted(
        self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]
    ) -> None:
        """複数postのリビジョン一覧取得のretryを使い切った場合はsite/post付きで失敗する"""
        post2 = self._post_with_id(mock_forum_post_no_http, 5002)
        response1 = MagicMock()
        response1.json.return_value = forum_post_revisions
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(response1, None))

        with pytest.raises(
            exceptions.UnexpectedException,
            match="Cannot retrieve forum post revisions for site: test-site, post: 5002",
        ):
            ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http, post2])

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once()

    def test_acquire_all_for_posts_missing_response_body_includes_site_and_post_context(
        self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]
    ) -> None:
        """複数postのリビジョン一覧レスポンスbody欠損はsite/post付きNoElementException"""
        post2 = self._post_with_id(mock_forum_post_no_http, 5002)
        response1 = MagicMock()
        response1.json.return_value = forum_post_revisions
        response2 = MagicMock()
        response2.json.return_value = {}
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(response1, response2))

        with pytest.raises(
            exceptions.NoElementException,
            match="Forum post revision list response body is not found for site: test-site, post: 5002",
        ):
            ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http, post2])

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once()

    def test_acquire_all_for_posts_malformed_response_body_type_includes_site_post_and_type_context(
        self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]
    ) -> None:
        """複数postのリビジョン一覧レスポンスbody型異常は対象post付きで失敗する"""
        post2 = self._post_with_id(mock_forum_post_no_http, 5002)
        response1 = MagicMock()
        response1.json.return_value = forum_post_revisions
        response2 = MagicMock()
        response2.json.return_value = {"body": ["not", "html"]}
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(response1, response2))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                "Forum post revision list response body is malformed for site: test-site, post: 5002 "
                "\\(field=body, expected=str, actual=list\\)"
            ),
        ):
            ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http, post2])

        assert mock_forum_post_no_http._revisions is None
        assert post2._revisions is None
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once()

    def test_acquire_all_for_posts_with_html_retries_transient_html_failures(
        self,
        mock_forum_post_no_http: ForumPost,
        forum_post_revisions_single: dict[str, Any],
        forum_post_revision_content: dict[str, Any],
    ) -> None:
        """with_html=TrueのリビジョンHTML取得もretryする"""
        list_response = MagicMock()
        list_response.json.return_value = forum_post_revisions_single
        html_response = MagicMock()
        html_response.json.return_value = forum_post_revision_content
        mock_forum_post_no_http.thread.site.amc_request = MagicMock(return_value=[RuntimeError("transient")])
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(
            side_effect=[(list_response,), (html_response,)]
        )

        result = ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http], with_html=True)

        assert result[5001][0].is_html_acquired()
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        assert mock_forum_post_no_http.thread.site.amc_request_with_retry.call_count == 2

    def test_acquire_all_for_posts_with_html_missing_response_content_includes_context(
        self,
        mock_forum_post_no_http: ForumPost,
        forum_post_revisions_single: dict[str, Any],
    ) -> None:
        """with_html=Trueのcontent欠損も空HTMLではなくsite/post/revision/field付きで失敗する"""
        list_response = MagicMock()
        list_response.json.return_value = forum_post_revisions_single
        html_response = MagicMock()
        html_response.json.return_value = {}
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(
            side_effect=[(list_response,), (html_response,)]
        )

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                "Forum post revision HTML response content is not found "
                "for site: test-site, post: 5001, revision: 9001, field=content"
            ),
        ):
            ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http], with_html=True)

        assert mock_forum_post_no_http._revisions is None
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        assert mock_forum_post_no_http.thread.site.amc_request_with_retry.call_count == 2

    def test_acquire_all_for_posts_with_html_deduplicates_duplicate_revision_ids(
        self,
        mock_forum_post_no_http: ForumPost,
        forum_post_revisions: dict[str, Any],
        forum_post_revision_content: dict[str, Any],
    ) -> None:
        """with_html=Trueの重複したrevision IDのHTML取得は1回にまとめる"""
        duplicate_revision_response = {
            **forum_post_revisions,
            "body": forum_post_revisions["body"].replace("showRevision(event, 9002)", "showRevision(event, 9001)"),
        }
        list_response = MagicMock()
        list_response.json.return_value = duplicate_revision_response
        html_response1 = MagicMock()
        html_response1.json.return_value = forum_post_revision_content
        html_response2 = MagicMock()
        html_response2.json.return_value = forum_post_revision_content
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(
            side_effect=[(list_response,), (html_response1, html_response2)]
        )

        result = ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http], with_html=True)

        revisions = result[5001]
        assert [revision.id for revision in revisions] == [9001, 9001, 9003]
        assert all(revision.is_html_acquired() for revision in revisions)
        assert [revision.html for revision in revisions] == [
            str(forum_post_revision_content["content"]),
            str(forum_post_revision_content["content"]),
            str(forum_post_revision_content["content"]),
        ]
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        assert mock_forum_post_no_http.thread.site.amc_request_with_retry.call_args_list[1].args == (
            [
                {
                    "moduleName": "forum/sub/ForumPostRevisionModule",
                    "revisionId": 9001,
                },
                {
                    "moduleName": "forum/sub/ForumPostRevisionModule",
                    "revisionId": 9003,
                },
            ],
        )


class TestForumPostRevisionCollectionGetHtmls:
    """ForumPostRevisionCollection.get_htmlsのテスト"""

    @pytest.mark.parametrize("bad_revision", [None, True, "9001"])
    def test_get_htmls_rejects_non_revision_entries_before_fetch(
        self, mock_forum_post_no_http: ForumPost, bad_revision: object
    ) -> None:
        """get_htmlsはForumPostRevision以外の要素を送信前に拒否する"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, [revision])
        bad_entry: Any = bad_revision
        collection.append(bad_entry)
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock()

        with pytest.raises(ValueError, match="revisions list entries must be ForumPostRevision"):
            collection.get_htmls()

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_not_called()

    def test_get_htmls_rejects_mutated_post_thread_before_fetch(self, mock_forum_post_no_http: ForumPost) -> None:
        """get_htmlsはmutateされた非ForumThread親を取得前に拒否する"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, [revision])
        bad_thread: Any = MagicMock()
        mock_forum_post_no_http.thread = bad_thread

        with pytest.raises(ValueError, match="thread must be a ForumThread"):
            collection.get_htmls()

        bad_thread.site.amc_request_with_retry.assert_not_called()
        assert revision.is_html_acquired() is False

    def test_get_htmls_rejects_mutated_target_revision_post_thread_before_fetch(
        self, mock_forum_post_no_http: ForumPost
    ) -> None:
        """get_htmlsは対象revision.postの非ForumThread親を取得前に拒否する"""
        revision_post = ForumPost(
            thread=mock_forum_post_no_http.thread,
            id=5002,
            title="Post 5002",
            text=mock_forum_post_no_http.text,
            element=mock_forum_post_no_http.element,
            created_by=mock_forum_post_no_http.created_by,
            created_at=mock_forum_post_no_http.created_at,
            edited_by=mock_forum_post_no_http.edited_by,
            edited_at=mock_forum_post_no_http.edited_at,
            _parent_id=mock_forum_post_no_http.parent_id,
        )
        revision = ForumPostRevision(
            post=revision_post,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, [])
        collection.append(revision)
        bad_thread: Any = MagicMock()
        revision_post.thread = bad_thread
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock()

        with pytest.raises(ValueError, match="thread must be a ForumThread"):
            collection.get_htmls()

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_not_called()
        bad_thread.site.amc_request_with_retry.assert_not_called()
        assert revision.is_html_acquired() is False

    def test_get_htmls_retries_transient_fetch_failures(
        self, mock_forum_post_no_http: ForumPost, forum_post_revision_content: dict[str, Any]
    ) -> None:
        """リビジョンHTML取得の一時失敗をretryする"""
        revisions = [
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=0,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
            ),
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9002,
                rev_no=1,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
            ),
        ]
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, revisions)

        response1 = MagicMock()
        response1.json.return_value = forum_post_revision_content
        response2 = MagicMock()
        response2.json.return_value = forum_post_revision_content
        mock_forum_post_no_http.thread.site.amc_request = MagicMock(return_value=[RuntimeError("transient"), response2])
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(response1, response2))

        result = collection.get_htmls()

        assert result == collection
        assert collection[0].is_html_acquired()
        assert collection[1].is_html_acquired()
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once()

    def test_get_htmls_skips_failed_retry_response(
        self, mock_forum_post_no_http: ForumPost, forum_post_revision_content: dict[str, Any]
    ) -> None:
        """retry後も失敗したHTMLだけ未取得のまま残す"""
        revisions = [
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=0,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
            ),
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9002,
                rev_no=1,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
            ),
        ]
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, revisions)

        response1 = MagicMock()
        response1.json.return_value = forum_post_revision_content
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(response1, None))

        result = collection.get_htmls()

        assert result == collection
        assert collection[0].is_html_acquired()
        assert collection[1].is_html_acquired() is False
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()

    def test_get_htmls_deduplicates_duplicate_revision_ids(
        self, mock_forum_post_no_http: ForumPost, forum_post_revision_content: dict[str, Any]
    ) -> None:
        """重複したrevision IDのHTML取得は1回にまとめる"""
        revisions = [
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=0,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
            ),
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=1,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
            ),
        ]
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, revisions)

        mock_response = MagicMock()
        mock_response.json.return_value = forum_post_revision_content
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        result = collection.get_htmls()

        assert result == collection
        assert collection[0].html == str(forum_post_revision_content["content"])
        assert collection[1].html == str(forum_post_revision_content["content"])
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "moduleName": "forum/sub/ForumPostRevisionModule",
                    "revisionId": 9001,
                }
            ]
        )

    def test_get_htmls_reuses_cached_duplicate_revision_html(self, mock_forum_post_no_http: ForumPost) -> None:
        """取得済みの重複revision HTMLを未取得の同一IDリビジョンへ再利用する"""
        revisions = [
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=0,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
                _html="<p>Cached revision HTML</p>",
            ),
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=1,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
            ),
        ]
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, revisions)

        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock()

        result = collection.get_htmls()

        assert result == collection
        assert collection[0].html == "<p>Cached revision HTML</p>"
        assert collection[1].html == "<p>Cached revision HTML</p>"
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_not_called()

    def test_get_htmls(self, mock_forum_post_no_http: ForumPost, forum_post_revision_content: dict[str, Any]) -> None:
        """複数リビジョンのHTMLを一括取得できる"""
        revisions = [
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=0,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
            ),
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9002,
                rev_no=1,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
            ),
        ]
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, revisions)

        mock_response1 = MagicMock()
        mock_response1.json.return_value = forum_post_revision_content
        mock_response2 = MagicMock()
        mock_response2.json.return_value = forum_post_revision_content
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(
            return_value=(mock_response1, mock_response2)
        )

        result = collection.get_htmls()
        assert result == collection
        assert collection[0].is_html_acquired()
        assert collection[1].is_html_acquired()

    def test_get_htmls_skips_acquired(self, mock_forum_post_no_http: ForumPost) -> None:
        """既に取得済みのリビジョンをスキップする"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
            _html="<p>Already acquired</p>",
        )
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, [revision])

        # amc_requestが呼ばれないことを確認
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        collection.get_htmls()
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()


# ============================================================
# ForumPostRevisionテスト
# ============================================================


class TestForumPostRevisionBasic:
    """ForumPostRevisionの基本テスト"""

    def test_str(self, mock_forum_post_no_http: ForumPost) -> None:
        """__str__が正しい文字列を返す"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        result = str(revision)
        assert "ForumPostRevision" in result
        assert "id=9001" in result
        assert "rev_no=0" in result

    def test_is_html_acquired_false(self, mock_forum_post_no_http: ForumPost) -> None:
        """HTML未取得時にFalseを返す"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        assert revision.is_html_acquired() is False

    def test_is_html_acquired_true(self, mock_forum_post_no_http: ForumPost) -> None:
        """HTML取得済み時にTrueを返す"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
            _html="<p>Test</p>",
        )
        assert revision.is_html_acquired() is True

    @pytest.mark.parametrize("html", [True, 9001, ["<p>Cached HTML</p>"], {"html": "<p>Cached HTML</p>"}, object()])
    def test_init_rejects_malformed_html_cache(self, mock_forum_post_no_http: ForumPost, html: object) -> None:
        """ForumPostRevisionの初期HTMLキャッシュは文字列またはNoneだけ受け付ける"""
        bad_html: Any = html

        with pytest.raises(ValueError, match="revision.html must be a string"):
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=0,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
                _html=bad_html,
            )

    def test_init_accepts_valid_html_cache(self, mock_forum_post_no_http: ForumPost) -> None:
        """有効な文字列HTMLキャッシュを初期化時に保持できる"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
            _html="<p>Cached HTML</p>",
        )

        assert revision.html == "<p>Cached HTML</p>"
        assert revision.is_html_acquired() is True

    @pytest.mark.parametrize("post", [None, True, "5001", {"id": 5001}, object()])
    def test_init_rejects_malformed_posts(self, mock_forum_post_no_http: ForumPost, post: object) -> None:
        """ForumPostRevisionの初期化はForumPostだけ受け付ける"""
        bad_post: Any = post

        with pytest.raises(ValueError, match="post must be a ForumPost"):
            ForumPostRevision(
                post=bad_post,
                id=9001,
                rev_no=0,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
            )

    @pytest.mark.parametrize("revision_id", [None, True, "9001", 9001.0])
    def test_init_rejects_malformed_ids(self, mock_forum_post_no_http: ForumPost, revision_id: object) -> None:
        """ForumPostRevisionの初期化は整数IDだけ受け付ける"""
        bad_revision_id: Any = revision_id

        with pytest.raises(ValueError, match="id must be an integer"):
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=bad_revision_id,
                rev_no=0,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
            )

    @pytest.mark.parametrize("rev_no", [None, True, "0", 0.0])
    def test_init_rejects_malformed_revision_numbers(self, mock_forum_post_no_http: ForumPost, rev_no: object) -> None:
        """ForumPostRevisionの初期化は整数のリビジョン番号だけ受け付ける"""
        bad_rev_no: Any = rev_no

        with pytest.raises(ValueError, match="rev_no must be an integer"):
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=bad_rev_no,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=datetime.now(tz=timezone.utc),
            )

    @pytest.mark.parametrize("created_by", [None, True, 9001, "test-user", {"id": 12345}])
    def test_init_rejects_malformed_creators(self, mock_forum_post_no_http: ForumPost, created_by: object) -> None:
        """ForumPostRevisionの初期化はAbstractUserの作成者だけ受け付ける"""
        bad_created_by: Any = created_by

        with pytest.raises(ValueError, match="created_by must be an AbstractUser"):
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=0,
                created_by=bad_created_by,
                created_at=datetime.now(tz=timezone.utc),
            )

    def test_init_rejects_created_by_from_different_client(self, mock_forum_post_no_http: ForumPost) -> None:
        """ForumPostRevisionは親postのsiteと異なるclientの作成者を拒否する"""
        other_client_user = _user(_client())

        with pytest.raises(ValueError, match="created_by must belong to the site"):
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=0,
                created_by=other_client_user,
                created_at=datetime.now(tz=timezone.utc),
            )

    @pytest.mark.parametrize("created_at", [None, True, 1700000000, "2023-11-14", []])
    def test_init_rejects_malformed_created_at(self, mock_forum_post_no_http: ForumPost, created_at: object) -> None:
        """ForumPostRevisionの初期化はdatetimeの作成日時だけ受け付ける"""
        bad_created_at: Any = created_at

        with pytest.raises(ValueError, match="created_at must be a datetime"):
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=0,
                created_by=_user(mock_forum_post_no_http.thread.site.client),
                created_at=bad_created_at,
            )


class TestForumPostRevisionHtml:
    """ForumPostRevision.htmlプロパティのテスト"""

    def test_html_property_cached(self, mock_forum_post_no_http: ForumPost) -> None:
        """htmlプロパティがキャッシュを返す"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
            _html="<p>Cached HTML</p>",
        )
        assert revision.html == "<p>Cached HTML</p>"

    def test_html_property_raises_when_retry_is_exhausted(self, mock_forum_post_no_http: ForumPost) -> None:
        """htmlプロパティは再試行失敗をNoneとして返さない"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(None,))

        with pytest.raises(
            exceptions.UnexpectedException,
            match="Cannot retrieve forum post revision HTML for site: test-site, post: 5001, revision: 9001",
        ):
            _ = revision.html

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once_with(
            [{"moduleName": "forum/sub/ForumPostRevisionModule", "revisionId": 9001}]
        )

    def test_html_property_rejects_mutated_post_thread_before_fetch(self, mock_forum_post_no_http: ForumPost) -> None:
        """未取得htmlはmutateされた非ForumThread親を取得前に拒否する"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        bad_thread: Any = MagicMock()
        mock_forum_post_no_http.thread = bad_thread

        with pytest.raises(ValueError, match="thread must be a ForumThread"):
            _ = revision.html

        bad_thread.site.amc_request_with_retry.assert_not_called()
        assert revision.is_html_acquired() is False

    def test_html_property_missing_response_content_includes_site_post_revision_and_field_context(
        self, mock_forum_post_no_http: ForumPost
    ) -> None:
        """HTML応答のcontent欠損は空HTMLではなくsite/post/revision/field付きで失敗する"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                "Forum post revision HTML response content is not found "
                "for site: test-site, post: 5001, revision: 9001, field=content"
            ),
        ):
            _ = revision.html

        assert revision.is_html_acquired() is False
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()

    def test_html_setter(self, mock_forum_post_no_http: ForumPost) -> None:
        """htmlセッターが正しく動作する"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        revision.html = "<p>New HTML</p>"
        assert revision.html == "<p>New HTML</p>"
        assert revision.is_html_acquired() is True

    @pytest.mark.parametrize("html", [None, True, 1, ["<p>New HTML</p>"]])
    def test_html_setter_rejects_invalid_html(self, mock_forum_post_no_http: ForumPost, html: object) -> None:
        """htmlセッターは文字列以外をキャッシュしない"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=_user(mock_forum_post_no_http.thread.site.client),
            created_at=datetime.now(tz=timezone.utc),
        )
        revision.html = "<p>Cached HTML</p>"
        bad_html: Any = html

        with pytest.raises(ValueError, match="revision.html must be a string"):
            revision.html = bad_html

        assert revision.html == "<p>Cached HTML</p>"
        assert revision.is_html_acquired() is True


# ============================================================
# ForumPost.has_revisionsテスト
# ============================================================


class TestForumPostHasRevisions:
    """ForumPost.has_revisionsプロパティのテスト"""

    def test_has_revisions_true(self, mock_forum_post_no_http: ForumPost) -> None:
        """edited_byがある場合にTrueを返す"""
        mock_forum_post_no_http.edited_by = MagicMock()
        assert mock_forum_post_no_http.has_revisions is True

    def test_has_revisions_false(self, mock_forum_post_no_http: ForumPost) -> None:
        """edited_byがNoneの場合にFalseを返す"""
        mock_forum_post_no_http.edited_by = None
        assert mock_forum_post_no_http.has_revisions is False


class TestForumPostRevisions:
    """ForumPost.revisionsプロパティのテスト"""

    def test_revisions_property(self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]) -> None:
        """revisionsプロパティがリビジョン一覧を返す"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_post_revisions
        mock_forum_post_no_http.thread.site.amc_request = MagicMock(return_value=[mock_response])

        revisions = mock_forum_post_no_http.revisions
        assert isinstance(revisions, ForumPostRevisionCollection)
        assert len(revisions) == 3

    def test_revisions_property_cached(
        self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]
    ) -> None:
        """revisionsプロパティがキャッシュされる"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_post_revisions
        mock_forum_post_no_http.thread.site.amc_request = MagicMock(return_value=[mock_response])

        # 最初の呼び出し
        revisions1 = mock_forum_post_no_http.revisions
        # 2回目の呼び出し
        revisions2 = mock_forum_post_no_http.revisions

        # 同じオブジェクトが返される
        assert revisions1 is revisions2
        # APIは1回だけ呼ばれる
        assert mock_forum_post_no_http.thread.site.amc_request.call_count == 1

    def test_revisions_property_rejects_mutated_thread_before_fetch(self, mock_forum_post_no_http: ForumPost) -> None:
        """未取得revisionsはmutateされた非ForumThread親を取得前に拒否する"""
        bad_thread: Any = MagicMock()
        mock_forum_post_no_http.thread = bad_thread

        with pytest.raises(ValueError, match="thread must be a ForumThread"):
            _ = mock_forum_post_no_http.revisions

        bad_thread.site.amc_request_with_retry.assert_not_called()
        assert mock_forum_post_no_http._revisions is None
