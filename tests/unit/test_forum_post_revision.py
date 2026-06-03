"""ForumPostRevisionモジュールのユニットテスト"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

from wikidot.common import exceptions
from wikidot.module.forum_post import ForumPost
from wikidot.module.forum_post_revision import ForumPostRevision, ForumPostRevisionCollection

if TYPE_CHECKING:
    from wikidot.module.forum_post import ForumPost


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

    def test_init_with_post_and_revisions(self, mock_forum_post_no_http: ForumPost) -> None:
        """ポストとリビジョンリストで初期化できる"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=None,
            created_at=datetime.now(tz=timezone.utc),
        )
        collection = ForumPostRevisionCollection(mock_forum_post_no_http, [revision])
        assert collection.post == mock_forum_post_no_http
        assert len(collection) == 1


class TestForumPostRevisionCollectionFind:
    """ForumPostRevisionCollection.findのテスト"""

    def test_find_existing(self, mock_forum_post_no_http: ForumPost) -> None:
        """存在するリビジョンをIDで検索できる"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=None,
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


class TestForumPostRevisionCollectionFindByRevNo:
    """ForumPostRevisionCollection.find_by_rev_noのテスト"""

    def test_find_by_rev_no_existing(self, mock_forum_post_no_http: ForumPost) -> None:
        """存在するリビジョンをリビジョン番号で検索できる"""
        revisions = [
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=0,
                created_by=None,
                created_at=datetime.now(tz=timezone.utc),
            ),
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9002,
                rev_no=1,
                created_by=None,
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


class TestForumPostRevisionCollectionAcquireAll:
    """ForumPostRevisionCollection.acquire_allのテスト"""

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
        """リビジョン一覧取得のretryを使い切った場合はpost ID付きで失敗する"""
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(None,))

        with pytest.raises(exceptions.UnexpectedException, match="Cannot retrieve forum post revisions for post: 5001"):
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

    def test_acquire_all(self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]) -> None:
        """リビジョン一覧を取得できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_post_revisions
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumPostRevisionCollection.acquire_all(mock_forum_post_no_http)
        assert len(collection) == 3


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

    def test_acquire_all_for_posts_raises_when_retry_is_exhausted(
        self, mock_forum_post_no_http: ForumPost, forum_post_revisions: dict[str, Any]
    ) -> None:
        """複数postのリビジョン一覧取得のretryを使い切った場合はpost ID付きで失敗する"""
        post2 = self._post_with_id(mock_forum_post_no_http, 5002)
        response1 = MagicMock()
        response1.json.return_value = forum_post_revisions
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(response1, None))

        with pytest.raises(exceptions.UnexpectedException, match="Cannot retrieve forum post revisions for post: 5002"):
            ForumPostRevisionCollection.acquire_all_for_posts([mock_forum_post_no_http, post2])

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


class TestForumPostRevisionCollectionGetHtmls:
    """ForumPostRevisionCollection.get_htmlsのテスト"""

    def test_get_htmls_retries_transient_fetch_failures(
        self, mock_forum_post_no_http: ForumPost, forum_post_revision_content: dict[str, Any]
    ) -> None:
        """リビジョンHTML取得の一時失敗をretryする"""
        revisions = [
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=0,
                created_by=None,
                created_at=datetime.now(tz=timezone.utc),
            ),
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9002,
                rev_no=1,
                created_by=None,
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
                created_by=None,
                created_at=datetime.now(tz=timezone.utc),
            ),
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9002,
                rev_no=1,
                created_by=None,
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
                created_by=None,
                created_at=datetime.now(tz=timezone.utc),
            ),
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=1,
                created_by=None,
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

    def test_get_htmls(self, mock_forum_post_no_http: ForumPost, forum_post_revision_content: dict[str, Any]) -> None:
        """複数リビジョンのHTMLを一括取得できる"""
        revisions = [
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9001,
                rev_no=0,
                created_by=None,
                created_at=datetime.now(tz=timezone.utc),
            ),
            ForumPostRevision(
                post=mock_forum_post_no_http,
                id=9002,
                rev_no=1,
                created_by=None,
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
            created_by=None,
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
            created_by=None,
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
            created_by=None,
            created_at=datetime.now(tz=timezone.utc),
        )
        assert revision.is_html_acquired() is False

    def test_is_html_acquired_true(self, mock_forum_post_no_http: ForumPost) -> None:
        """HTML取得済み時にTrueを返す"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=None,
            created_at=datetime.now(tz=timezone.utc),
            _html="<p>Test</p>",
        )
        assert revision.is_html_acquired() is True


class TestForumPostRevisionHtml:
    """ForumPostRevision.htmlプロパティのテスト"""

    def test_html_property_cached(self, mock_forum_post_no_http: ForumPost) -> None:
        """htmlプロパティがキャッシュを返す"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=None,
            created_at=datetime.now(tz=timezone.utc),
            _html="<p>Cached HTML</p>",
        )
        assert revision.html == "<p>Cached HTML</p>"

    def test_html_setter(self, mock_forum_post_no_http: ForumPost) -> None:
        """htmlセッターが正しく動作する"""
        revision = ForumPostRevision(
            post=mock_forum_post_no_http,
            id=9001,
            rev_no=0,
            created_by=None,
            created_at=datetime.now(tz=timezone.utc),
        )
        revision.html = "<p>New HTML</p>"
        assert revision.html == "<p>New HTML</p>"
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
