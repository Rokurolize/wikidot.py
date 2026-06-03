"""ForumPostモジュールのユニットテスト"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

from wikidot.common import exceptions
from wikidot.module.forum_post import ForumPost, ForumPostCollection
from wikidot.module.forum_thread import ForumThread

# ============================================================
# ForumPostCollectionテスト
# ============================================================


class TestForumPostCollectionInit:
    """ForumPostCollectionの初期化テスト"""

    def test_init_with_thread_and_empty_posts(self, mock_forum_thread_no_http: ForumThread) -> None:
        """スレッドと空の投稿リストで初期化できる"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [])
        assert collection.thread == mock_forum_thread_no_http
        assert len(collection) == 0

    def test_init_with_thread_and_posts(
        self, mock_forum_thread_no_http: ForumThread, mock_forum_post_no_http: ForumPost
    ) -> None:
        """スレッドと投稿リストで初期化できる"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])
        assert collection.thread == mock_forum_thread_no_http
        assert len(collection) == 1

    def test_find_existing(self, mock_forum_thread_no_http: ForumThread, mock_forum_post_no_http: ForumPost) -> None:
        """存在する投稿をIDで検索できる"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])
        found = collection.find(5001)
        assert found is not None
        assert found.id == 5001

    def test_find_nonexistent(self, mock_forum_thread_no_http: ForumThread) -> None:
        """存在しない投稿を検索するとNoneを返す"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [])
        found = collection.find(9999)
        assert found is None


class TestForumPostCollectionParse:
    """ForumPostCollection._parseのテスト"""

    def test_parse_success(self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]) -> None:
        """投稿一覧を正常にパースできる"""
        html = BeautifulSoup(forum_posts_in_thread["body"], "lxml")
        posts = ForumPostCollection._parse(mock_forum_thread_no_http, html)
        assert len(posts) == 2

    def test_parse_fields(self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]) -> None:
        """投稿の各フィールドが正しくパースされる"""
        html = BeautifulSoup(forum_posts_in_thread["body"], "lxml")
        posts = ForumPostCollection._parse(mock_forum_thread_no_http, html)

        # 1つ目の投稿を検証
        post = posts[0]
        assert post.id == 5001
        assert post.title == "Test Post Title"
        assert "<p>Test post content</p>" in post.text

        # 2つ目の投稿を検証
        post2 = posts[1]
        assert post2.id == 5002
        assert post2.title == "Second Post"

    def test_parse_ignores_pseudo_posts(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_with_pseudo_post: dict[str, Any]
    ) -> None:
        """コンテンツ内の疑似ポストを無視してトップレベルの投稿のみをパースする"""
        html = BeautifulSoup(forum_posts_with_pseudo_post["body"], "lxml")
        posts = ForumPostCollection._parse(mock_forum_thread_no_http, html)

        # 疑似ポストを除いてトップレベルの投稿のみ（2件）
        assert len(posts) == 2
        assert posts[0].id == 5001
        assert posts[1].id == 5002

    def test_parse_pseudo_post_user_not_mixed(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_with_pseudo_post: dict[str, Any]
    ) -> None:
        """疑似ポスト内のユーザー情報が本物の投稿に混入しない"""
        html = BeautifulSoup(forum_posts_with_pseudo_post["body"], "lxml")
        posts = ForumPostCollection._parse(mock_forum_thread_no_http, html)

        # 1つ目の投稿者はtest_user_1（疑似ポスト内のtest_user_3/4ではない）
        assert posts[0].created_by.name == "test_user_1"
        # 2つ目の投稿者はtest_user_2
        assert posts[1].created_by.name == "test_user_2"

    def test_parse_ignores_pseudo_posts_with_post_id(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_with_pseudo_post: dict[str, Any]
    ) -> None:
        """post ID風のidを持つコンテンツ内疑似ポストも無視する"""
        body = forum_posts_with_pseudo_post["body"].replace(
            '<div class="collapsible-block post">',
            '<div class="collapsible-block post" id="post-9999">',
            1,
        )
        html = BeautifulSoup(body, "lxml")

        posts = ForumPostCollection._parse(mock_forum_thread_no_http, html)

        assert [post.id for post in posts] == [5001, 5002]


class TestForumPostCollectionAcquireAll:
    """ForumPostCollection.acquire_all_in_threadのテスト"""

    def test_acquire_all_single_page(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """単一ページの投稿一覧を取得できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_posts_in_thread
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)
        assert len(collection) == 2
        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_retries_transient_first_page_failures(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """一時的なAMC失敗後にスレッド内投稿一覧をリトライする"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_posts_in_thread
        amc_request = MagicMock(side_effect=[(RuntimeError("temporary failure"),), (mock_response,)])
        mock_forum_thread_no_http.site.client.amc_client.request = amc_request

        collection = ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        assert len(collection) == 2
        assert amc_request.call_count == 2

    def test_acquire_all_pagination(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """複数ページの投稿一覧を取得できる（ページャーあり）"""
        # ページャー付きのレスポンスを作成
        body_with_pager = (
            forum_posts_in_thread["body"]
            + '<div class="pager"><span class="target">1</span><span class="target">2</span><span class="target">next</span></div>'
        )
        first_response = MagicMock()
        first_response.json.return_value = {"status": "ok", "body": body_with_pager}

        second_response = MagicMock()
        second_response.json.return_value = forum_posts_in_thread

        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(
            side_effect=[(first_response,), (second_response,)]
        )

        collection = ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)
        # 最初のページで2件 + 2ページ目で2件 = 4件
        assert len(collection) == 4
        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_in_threads_deduplicates_duplicate_thread_ids(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """重複したthread IDの投稿一覧取得は1回にまとめる"""
        duplicate_thread = ForumThread(
            site=mock_forum_thread_no_http.site,
            id=mock_forum_thread_no_http.id,
            title="Duplicate Thread",
            description=mock_forum_thread_no_http.description,
            created_by=mock_forum_thread_no_http.created_by,
            created_at=mock_forum_thread_no_http.created_at,
            post_count=mock_forum_thread_no_http.post_count,
            category=mock_forum_thread_no_http.category,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = forum_posts_in_thread
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        result = ForumPostCollection.acquire_all_in_threads([mock_forum_thread_no_http, duplicate_thread])

        assert set(result) == {mock_forum_thread_no_http.id}
        assert len(result[mock_forum_thread_no_http.id]) == 2
        assert result[mock_forum_thread_no_http.id].thread == mock_forum_thread_no_http
        mock_forum_thread_no_http.site.amc_request.assert_not_called()
        mock_forum_thread_no_http.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "moduleName": "forum/ForumViewThreadPostsModule",
                    "pageNo": "1",
                    "t": str(mock_forum_thread_no_http.id),
                }
            ]
        )

    def test_acquire_all_ignores_non_numeric_pager_targets(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """数値ページがないpagerでは単一ページとして扱う"""
        body_with_pager = forum_posts_in_thread["body"] + '<div class="pager"><span class="target">next</span></div>'
        first_response = MagicMock()
        first_response.json.return_value = {"status": "ok", "body": body_with_pager}
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(first_response,))

        collection = ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        assert len(collection) == 2
        mock_forum_thread_no_http.site.amc_request.assert_not_called()
        mock_forum_thread_no_http.site.amc_request_with_retry.assert_called_once()

    def test_acquire_all_raises_when_first_page_retry_is_exhausted(
        self, mock_forum_thread_no_http: ForumThread
    ) -> None:
        """初回ページのリトライが尽きた場合は明示的に例外を出す"""
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(None,))

        with pytest.raises(
            exceptions.UnexpectedException,
            match="Cannot retrieve forum posts for thread 3001 page: 1",
        ):
            ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_raises_when_paginated_retry_is_exhausted(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """追加ページのリトライが尽きた場合は部分一覧を返さない"""
        body_with_pager = (
            forum_posts_in_thread["body"]
            + '<div class="pager"><span class="target">1</span><span class="target">2</span></div>'
        )
        first_response = MagicMock()
        first_response.json.return_value = {"status": "ok", "body": body_with_pager}

        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(side_effect=[(first_response,), (None,)])

        with pytest.raises(
            exceptions.UnexpectedException,
            match="Cannot retrieve forum posts for thread 3001 page: 2",
        ):
            ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        mock_forum_thread_no_http.site.amc_request.assert_not_called()


class TestForumPostCollectionGetSources:
    """ForumPostCollection.get_post_sourcesのテスト"""

    def test_get_post_sources_success(
        self,
        mock_forum_thread_no_http: ForumThread,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
    ) -> None:
        """ソースを正常に取得できる"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])

        mock_response = MagicMock()
        mock_response.json.return_value = forum_editpost_form
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        result = collection.get_post_sources()
        assert result == collection
        assert mock_forum_post_no_http._source is not None
        assert mock_forum_post_no_http._source == "Test source content in wikidot syntax"
        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_get_post_sources_retries_transient_fetch_failures(
        self,
        mock_forum_thread_no_http: ForumThread,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
    ) -> None:
        """一時的なAMC失敗後に投稿ソース取得をリトライする"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])

        mock_response = MagicMock()
        mock_response.json.return_value = forum_editpost_form
        amc_request = MagicMock(side_effect=[(RuntimeError("temporary failure"),), (mock_response,)])
        mock_forum_thread_no_http.site.client.amc_client.request = amc_request

        result = collection.get_post_sources()

        assert result == collection
        assert mock_forum_post_no_http._source == "Test source content in wikidot syntax"
        assert amc_request.call_count == 2

    def test_get_post_sources_skips_already_acquired(
        self, mock_forum_thread_no_http: ForumThread, mock_forum_post_no_http: ForumPost
    ) -> None:
        """既に取得済みのソースはスキップ"""
        mock_forum_post_no_http._source = "cached source"
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock()
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])

        result = collection.get_post_sources()
        mock_forum_thread_no_http.site.amc_request.assert_not_called()
        mock_forum_thread_no_http.site.amc_request_with_retry.assert_not_called()
        assert result == collection
        assert mock_forum_post_no_http._source == "cached source"

    def test_get_post_sources_empty_collection(self, mock_forum_thread_no_http: ForumThread) -> None:
        """空のコレクションでも動作する"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [])
        result = collection.get_post_sources()
        assert result == collection
        assert len(collection) == 0

    def test_get_post_sources_multiple_posts(
        self,
        mock_forum_thread_no_http: ForumThread,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
    ) -> None:
        """複数の投稿のソースを一括取得できる"""
        # 2つ目の投稿を作成
        post2 = ForumPost(
            thread=mock_forum_thread_no_http,
            id=5002,
            title="Second Post",
            text="<p>Second post content</p>",
            element=mock_forum_post_no_http.element,
            created_by=mock_forum_post_no_http.created_by,
            created_at=mock_forum_post_no_http.created_at,
        )

        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http, post2])

        mock_response1 = MagicMock()
        mock_response1.json.return_value = forum_editpost_form
        mock_response2 = MagicMock()
        mock_response2.json.return_value = forum_editpost_form
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response1, mock_response2))

        result = collection.get_post_sources()
        assert result == collection
        assert mock_forum_post_no_http._source is not None
        assert post2._source is not None
        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_get_post_sources_deduplicates_duplicate_post_ids(
        self,
        mock_forum_thread_no_http: ForumThread,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
    ) -> None:
        """重複した投稿IDのソース取得は1回にまとめる"""
        duplicate_post = ForumPost(
            thread=mock_forum_thread_no_http,
            id=mock_forum_post_no_http.id,
            title="Duplicate Post",
            text="<p>Duplicate post content</p>",
            element=mock_forum_post_no_http.element,
            created_by=mock_forum_post_no_http.created_by,
            created_at=mock_forum_post_no_http.created_at,
        )
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http, duplicate_post])

        mock_response = MagicMock()
        mock_response.json.return_value = forum_editpost_form
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        result = collection.get_post_sources()

        assert result == collection
        assert mock_forum_post_no_http._source == "Test source content in wikidot syntax"
        assert duplicate_post._source == "Test source content in wikidot syntax"
        mock_forum_thread_no_http.site.amc_request.assert_not_called()
        mock_forum_thread_no_http.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "moduleName": "forum/sub/ForumEditPostFormModule",
                    "threadId": mock_forum_thread_no_http.id,
                    "postId": mock_forum_post_no_http.id,
                }
            ]
        )

    def test_get_post_sources_skips_failed_retry_response(
        self, mock_forum_thread_no_http: ForumThread, mock_forum_post_no_http: ForumPost
    ) -> None:
        """リトライが尽きた投稿は未取得のまま残す"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(None,))

        result = collection.get_post_sources()

        assert result == collection
        assert mock_forum_post_no_http._source is None
        mock_forum_thread_no_http.site.amc_request.assert_not_called()


# ============================================================
# ForumPostテスト
# ============================================================


class TestForumPostBasic:
    """ForumPostの基本テスト"""

    def test_str(self, mock_forum_post_no_http: ForumPost) -> None:
        """__str__が正しい文字列を返す"""
        result = str(mock_forum_post_no_http)
        assert "ForumPost" in result
        assert "id=5001" in result
        assert "Test Post Title" in result

    def test_parent_id_property(self, mock_forum_post_no_http: ForumPost) -> None:
        """parent_idプロパティが正しい値を返す"""
        assert mock_forum_post_no_http.parent_id is None

        mock_forum_post_no_http._parent_id = 4999
        assert mock_forum_post_no_http.parent_id == 4999


class TestForumPostSource:
    """ForumPost.sourceプロパティのテスト"""

    def test_source_property_calls_api(
        self, mock_forum_post_no_http: ForumPost, forum_editpost_form: dict[str, Any]
    ) -> None:
        """sourceプロパティがAPIを呼び出す"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_editpost_form
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        source = mock_forum_post_no_http.source
        assert source == "Test source content in wikidot syntax"
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()

    def test_source_property_cached(self, mock_forum_post_no_http: ForumPost) -> None:
        """sourceプロパティがキャッシュされる"""
        mock_forum_post_no_http._source = "cached source"
        assert mock_forum_post_no_http.source == "cached source"

    def test_source_property_raises_when_retry_is_exhausted(self, mock_forum_post_no_http: ForumPost) -> None:
        """sourceプロパティはリトライ枯渇時に既存の未取得例外を返す"""
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(None,))

        with pytest.raises(exceptions.NoElementException, match="Source textarea is not found"):
            _ = mock_forum_post_no_http.source

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()


class TestForumPostEdit:
    """ForumPost.editのテスト"""

    def test_edit_not_logged_in(self, mock_forum_post_no_http: ForumPost) -> None:
        """ログインしていない場合に例外"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = False
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock(
            side_effect=exceptions.LoginRequiredException("Login required")
        )

        with pytest.raises(exceptions.LoginRequiredException):
            mock_forum_post_no_http.edit(source="Updated source")

    def test_edit_success(
        self,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
        amc_ok_response: dict[str, Any],
    ) -> None:
        """編集が成功する"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()

        form_response = MagicMock()
        form_response.json.return_value = forum_editpost_form
        save_response = MagicMock()
        save_response.json.return_value = amc_ok_response

        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(form_response,))
        mock_forum_post_no_http.thread.site.amc_request = MagicMock(return_value=[save_response])

        result = mock_forum_post_no_http.edit(source="Updated source")

        assert result == mock_forum_post_no_http
        assert mock_forum_post_no_http._source == "Updated source"
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once()
        mock_forum_post_no_http.thread.site.amc_request.assert_called_once()

    def test_edit_retries_transient_form_fetch_failures(
        self,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
        amc_ok_response: dict[str, Any],
    ) -> None:
        """一時的なAMC失敗後に編集フォーム取得をリトライする"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()

        form_response = MagicMock()
        form_response.json.return_value = forum_editpost_form
        save_response = MagicMock()
        save_response.json.return_value = amc_ok_response
        amc_request = MagicMock(side_effect=[(RuntimeError("temporary failure"),), (form_response,), (save_response,)])
        mock_forum_post_no_http.thread.site.client.amc_client.request = amc_request

        result = mock_forum_post_no_http.edit(source="Updated source")

        assert result == mock_forum_post_no_http
        assert mock_forum_post_no_http._source == "Updated source"
        assert amc_request.call_count == 3

    def test_edit_raises_when_form_fetch_retry_is_exhausted(self, mock_forum_post_no_http: ForumPost) -> None:
        """編集フォーム取得のリトライが尽きた場合は保存しない"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(None,))
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()

        with pytest.raises(
            exceptions.UnexpectedException,
            match="Cannot retrieve forum post edit form: 5001",
        ):
            mock_forum_post_no_http.edit(source="Updated source")

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        assert mock_forum_post_no_http._source is None

    def test_edit_with_new_title(
        self,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
        amc_ok_response: dict[str, Any],
    ) -> None:
        """タイトル付きで編集できる"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()

        form_response = MagicMock()
        form_response.json.return_value = forum_editpost_form
        save_response = MagicMock()
        save_response.json.return_value = amc_ok_response

        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(form_response,))
        mock_forum_post_no_http.thread.site.amc_request = MagicMock(return_value=[save_response])

        mock_forum_post_no_http.edit(source="Updated source", title="New Title")

        assert mock_forum_post_no_http.title == "New Title"
        assert mock_forum_post_no_http._source == "Updated source"
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once()
        mock_forum_post_no_http.thread.site.amc_request.assert_called_once()
