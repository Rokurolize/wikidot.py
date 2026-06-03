"""ForumThreadモジュールのユニットテスト"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

from wikidot.common import exceptions
from wikidot.module.forum_thread import ForumThread, ForumThreadCollection

if TYPE_CHECKING:
    from wikidot.module.forum_category import ForumCategory
    from wikidot.module.site import Site


# ============================================================
# ForumThreadCollectionテスト
# ============================================================


class TestForumThreadCollectionInit:
    """ForumThreadCollectionの初期化テスト"""

    def test_init_with_site_and_empty_threads(self, mock_site_no_http: Site) -> None:
        """サイトと空のスレッドリストで初期化できる"""
        collection = ForumThreadCollection(mock_site_no_http, [])
        assert collection.site == mock_site_no_http
        assert len(collection) == 0

    def test_init_with_site_and_threads(self, mock_site_no_http: Site, mock_forum_thread_no_http: ForumThread) -> None:
        """サイトとスレッドリストで初期化できる"""
        collection = ForumThreadCollection(mock_site_no_http, [mock_forum_thread_no_http])
        assert collection.site == mock_site_no_http
        assert len(collection) == 1

    def test_find_existing(self, mock_site_no_http: Site, mock_forum_thread_no_http: ForumThread) -> None:
        """存在するスレッドをIDで検索できる"""
        collection = ForumThreadCollection(mock_site_no_http, [mock_forum_thread_no_http])
        found = collection.find(3001)
        assert found is not None
        assert found.id == 3001

    def test_find_nonexistent(self, mock_site_no_http: Site) -> None:
        """存在しないスレッドを検索するとNoneを返す"""
        collection = ForumThreadCollection(mock_site_no_http, [])
        found = collection.find(9999)
        assert found is None


class TestForumThreadCollectionParseListInCategory:
    """ForumThreadCollection._parse_list_in_categoryのテスト"""

    def test_parse_success(self, mock_site_no_http: Site, forum_threads_in_category: dict[str, Any]) -> None:
        """カテゴリ内スレッド一覧を正常にパースできる"""
        html = BeautifulSoup(forum_threads_in_category["body"], "lxml")
        collection = ForumThreadCollection._parse_list_in_category(mock_site_no_http, html)
        assert len(collection) == 2

    def test_parse_fields(self, mock_site_no_http: Site, forum_threads_in_category: dict[str, Any]) -> None:
        """スレッドの各フィールドが正しくパースされる"""
        html = BeautifulSoup(forum_threads_in_category["body"], "lxml")
        collection = ForumThreadCollection._parse_list_in_category(mock_site_no_http, html)

        # 1つ目のスレッドを検証
        thread = collection[0]
        assert thread.id == 3001
        assert thread.title == "Test Thread"
        assert thread.description == "Test thread description"
        assert thread.post_count == 5

        # 2つ目のスレッドを検証
        thread2 = collection[1]
        assert thread2.id == 3002
        assert thread2.title == "Another Thread"

    def test_parse_with_category(
        self,
        mock_site_no_http: Site,
        mock_forum_category_no_http: ForumCategory,
        forum_threads_in_category: dict[str, Any],
    ) -> None:
        """カテゴリを指定してパースできる"""
        html = BeautifulSoup(forum_threads_in_category["body"], "lxml")
        collection = ForumThreadCollection._parse_list_in_category(mock_site_no_http, html, mock_forum_category_no_http)
        assert collection[0].category == mock_forum_category_no_http

    def test_parse_ignores_description_metadata_markup(
        self, mock_site_no_http: Site, forum_threads_in_category: dict[str, Any]
    ) -> None:
        """スレッド説明内のユーザー・日時風マークアップを作成者情報として扱わない"""
        description_with_metadata = (
            '<div class="description">Test thread description '
            '<span class="printuser"><a href="http://www.wikidot.com/user:info/content-user" '
            'onclick="WIKIDOT.page.listeners.userInfo(99999); return false;">content_user</a></span> '
            '<span class="odate time_1700000500">17 Dec 2025</span></div>'
        )
        body = forum_threads_in_category["body"].replace(
            '<div class="description">Test thread description</div>',
            description_with_metadata,
            1,
        )
        html = BeautifulSoup(body, "lxml")

        collection = ForumThreadCollection._parse_list_in_category(mock_site_no_http, html)

        assert collection[0].created_by.name == "test_user"
        assert int(collection[0].created_at.timestamp()) == 1700000000


class TestForumThreadCollectionParseThreadPage:
    """ForumThreadCollection._parse_thread_pageのテスト"""

    def test_parse_success(self, mock_site_no_http: Site, forum_thread_detail: dict[str, Any]) -> None:
        """スレッド詳細ページを正常にパースできる"""
        html = BeautifulSoup(forum_thread_detail["body"], "lxml")
        thread = ForumThreadCollection._parse_thread_page(mock_site_no_http, html)
        assert thread is not None
        assert thread.id == 3001

    def test_parse_fields(self, mock_site_no_http: Site, forum_thread_detail: dict[str, Any]) -> None:
        """スレッド詳細の各フィールドが正しくパースされる"""
        html = BeautifulSoup(forum_thread_detail["body"], "lxml")
        thread = ForumThreadCollection._parse_thread_page(mock_site_no_http, html)

        assert thread.id == 3001
        assert thread.title == "Test Thread Title"
        assert thread.description == "Test thread description"
        assert thread.post_count == 5

    def test_parse_empty_breadcrumb_title_raises(
        self, mock_site_no_http: Site, forum_thread_detail: dict[str, Any]
    ) -> None:
        """パンくずにタイトルがない場合NoElementException"""
        html = BeautifulSoup(forum_thread_detail["body"], "lxml")
        breadcrumb = html.select_one("div.forum-breadcrumbs")
        assert breadcrumb is not None
        breadcrumb.clear()

        with pytest.raises(exceptions.NoElementException, match="Thread title"):
            ForumThreadCollection._parse_thread_page(mock_site_no_http, html)


class TestForumThreadCollectionAcquireAll:
    """ForumThreadCollection.acquire_all_in_categoryのテスト"""

    def test_category_threads_retries_transient_first_page_failures(
        self, mock_forum_category_no_http: ForumCategory, forum_threads_in_category: dict[str, Any]
    ) -> None:
        """category.threadsは一時的なAMC失敗を再試行してスレッドを返す"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_threads_in_category
        amc_request = MagicMock(
            side_effect=[
                (RuntimeError("temporary failure"),),
                (mock_response,),
            ]
        )
        mock_forum_category_no_http.site.client.amc_client.request = amc_request

        collection = mock_forum_category_no_http.threads

        assert len(collection) == 2
        assert all(thread.category == mock_forum_category_no_http for thread in collection)
        assert amc_request.call_count == 2

    def test_acquire_all_single_page(
        self, mock_forum_category_no_http: ForumCategory, forum_threads_in_category: dict[str, Any]
    ) -> None:
        """単一ページのスレッド一覧を取得できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_threads_in_category
        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)
        assert len(collection) == 2
        assert all(thread.category == mock_forum_category_no_http for thread in collection)

    def test_acquire_all_ignores_nested_thread_tables(
        self, mock_forum_category_no_http: ForumCategory, forum_threads_in_category: dict[str, Any]
    ) -> None:
        """スレッド説明内の入れ子テーブルを別スレッドとして扱わない"""
        nested_thread_table = (
            '<div class="description">Test thread description'
            '<table class="table"><tr class="head"><td>Thread</td><td>Started</td><td>Posts</td></tr>'
            '<tr><td class="name"><div class="title"><a href="/forum/t-9999/fake-thread">Fake Thread</a></div>'
            '<div class="description">Nested fake thread</div></td><td class="started">by: '
            '<span class="printuser"><a href="http://www.wikidot.com/user:info/fake-user" '
            'onclick="WIKIDOT.page.listeners.userInfo(99999); return false;">fake_user</a></span> '
            '<span class="odate time_1700000500">17 Dec 2025</span></td><td class="posts">999</td></tr>'
            "</table></div>"
        )
        body = forum_threads_in_category["body"].replace(
            '<div class="description">Test thread description</div>',
            nested_thread_table,
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body}
        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)

        assert [thread.id for thread in collection] == [3001, 3002]
        assert collection[0].post_count == 5
        assert collection[1].post_count == 3

    def test_acquire_all_pagination(
        self, mock_forum_category_no_http: ForumCategory, forum_threads_in_category: dict[str, Any]
    ) -> None:
        """複数ページのスレッド一覧を取得できる（ページャーあり）"""
        # ページャー付きのレスポンスを作成
        body_with_pager = forum_threads_in_category["body"] + '<div class="pager"><a>1</a><a>2</a><a>next</a></div>'
        first_response = MagicMock()
        first_response.json.return_value = {"status": "ok", "body": body_with_pager}

        second_response = MagicMock()
        second_response.json.return_value = forum_threads_in_category

        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(
            side_effect=[(first_response,), (second_response,)]
        )

        collection = ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)
        # 最初のページで2件 + 2ページ目で2件 = 4件
        assert len(collection) == 4
        assert all(thread.category == mock_forum_category_no_http for thread in collection)

    def test_acquire_all_ignores_non_numeric_pager_links(
        self, mock_forum_category_no_http: ForumCategory, forum_threads_in_category: dict[str, Any]
    ) -> None:
        """数値ページがないpagerでは単一ページとして扱う"""
        first_response = MagicMock()
        body_with_pager = forum_threads_in_category["body"] + '<div class="pager"><a>next</a></div>'
        first_response.json.return_value = {"status": "ok", "body": body_with_pager}

        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(return_value=(first_response,))

        collection = ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)

        assert len(collection) == 2
        mock_forum_category_no_http.site.amc_request_with_retry.assert_called_once()

    def test_acquire_all_raises_when_paginated_retry_is_exhausted(
        self, mock_forum_category_no_http: ForumCategory, forum_threads_in_category: dict[str, Any]
    ) -> None:
        """カテゴリ内スレッド一覧の追加ページ再試行が尽きた場合は明示的に失敗する"""
        body_with_pager = forum_threads_in_category["body"] + '<div class="pager"><a>1</a><a>2</a></div>'
        first_response = MagicMock()
        first_response.json.return_value = {"status": "ok", "body": body_with_pager}

        mock_forum_category_no_http.site.amc_request = MagicMock()
        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(side_effect=[(first_response,), (None,)])

        with pytest.raises(exceptions.UnexpectedException, match="Cannot retrieve forum threads page: 2"):
            ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)

        mock_forum_category_no_http.site.amc_request.assert_not_called()


class TestForumThreadCollectionAcquireFromIds:
    """ForumThreadCollection.acquire_from_thread_idsのテスト"""

    def test_site_get_threads_empty_input_skips_fetch(self, mock_site_no_http: Site) -> None:
        """空のスレッドIDリストはAMC取得なしで空コレクションを返す"""
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock()

        collection = mock_site_no_http.get_threads([])

        assert isinstance(collection, ForumThreadCollection)
        assert collection.site == mock_site_no_http
        assert len(collection) == 0
        mock_site_no_http.amc_request.assert_not_called()
        mock_site_no_http.amc_request_with_retry.assert_not_called()

    def test_acquire_from_ids_success(self, mock_site_no_http: Site, forum_thread_detail: dict[str, Any]) -> None:
        """スレッドIDからスレッド情報を取得できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_thread_detail
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumThreadCollection.acquire_from_thread_ids(mock_site_no_http, [3001])
        assert len(collection) == 1
        assert collection[0].id == 3001
        mock_site_no_http.amc_request.assert_not_called()

    def test_site_get_threads_retries_transient_fetch_failures(
        self, mock_site_no_http: Site, forum_thread_detail: dict[str, Any]
    ) -> None:
        """サイトのスレッド取得が一時的なAMC失敗をリトライする"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_thread_detail
        amc_request = MagicMock(side_effect=[(RuntimeError("temporary failure"),), (mock_response,)])
        mock_site_no_http.client.amc_client.request = amc_request

        collection = mock_site_no_http.get_threads([3001])

        assert len(collection) == 1
        assert collection[0].id == 3001
        assert amc_request.call_count == 2

    def test_acquire_from_ids_deduplicates_duplicate_thread_ids(
        self, mock_site_no_http: Site, forum_thread_detail: dict[str, Any]
    ) -> None:
        """重複スレッドIDは詳細取得を1回だけ行い、返却順は入力どおりに保つ"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_thread_detail
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumThreadCollection.acquire_from_thread_ids(mock_site_no_http, [3001, 3001])

        assert [thread.id for thread in collection] == [3001, 3001]
        assert mock_site_no_http.amc_request_with_retry.call_args.args[0] == [
            {"t": 3001, "moduleName": "forum/ForumViewThreadModule"}
        ]
        mock_site_no_http.amc_request.assert_not_called()

    def test_acquire_from_ids_raises_when_retry_is_exhausted(self, mock_site_no_http: Site) -> None:
        """スレッド詳細取得のリトライが尽きた場合は明示的に例外を出す"""
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(None,))

        with pytest.raises(exceptions.UnexpectedException, match="Cannot retrieve forum thread: 3001"):
            ForumThreadCollection.acquire_from_thread_ids(mock_site_no_http, [3001])

        mock_site_no_http.amc_request.assert_not_called()


# ============================================================
# ForumThreadテスト
# ============================================================


class TestForumThreadBasic:
    """ForumThreadの基本テスト"""

    def test_str(self, mock_forum_thread_no_http: ForumThread) -> None:
        """__str__が正しい文字列を返す"""
        result = str(mock_forum_thread_no_http)
        assert "ForumThread" in result
        assert "id=3001" in result
        assert "Test Thread" in result

    def test_url_property(self, mock_forum_thread_no_http: ForumThread) -> None:
        """urlプロパティが正しいURLを返す"""
        url = mock_forum_thread_no_http.url
        assert "test-site.wikidot.com" in url
        assert "forum/t-3001" in url


class TestForumThreadPosts:
    """ForumThread.postsプロパティのテスト"""

    def test_posts_property_calls_acquire(self, mock_forum_thread_no_http: ForumThread) -> None:
        """postsプロパティがForumPostCollection.acquire_allを呼び出す"""
        from wikidot.module.forum_post import ForumPostCollection

        mock_posts = ForumPostCollection(mock_forum_thread_no_http)
        mock_forum_thread_no_http._posts = mock_posts

        result = mock_forum_thread_no_http.posts
        assert result == mock_posts

    def test_posts_setter(self, mock_forum_thread_no_http: ForumThread) -> None:
        """_postsに直接設定できる"""
        from wikidot.module.forum_post import ForumPostCollection

        posts = ForumPostCollection(mock_forum_thread_no_http)
        mock_forum_thread_no_http._posts = posts
        assert mock_forum_thread_no_http._posts == posts

    def test_posts_property_raises_when_retry_is_exhausted(self, mock_forum_thread_no_http: ForumThread) -> None:
        """postsプロパティはリトライ失敗を空コレクションとしてキャッシュしない"""
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(None,))

        with pytest.raises(
            exceptions.UnexpectedException,
            match="Cannot retrieve forum posts for thread 3001 page: 1",
        ):
            _ = mock_forum_thread_no_http.posts

        assert mock_forum_thread_no_http._posts is None
        mock_forum_thread_no_http.site.amc_request.assert_not_called()


class TestForumThreadReply:
    """ForumThread.replyのテスト"""

    def test_reply_not_logged_in(self, mock_forum_thread_no_http: ForumThread) -> None:
        """ログインしていない場合に例外"""
        mock_forum_thread_no_http.site.client.is_logged_in = False
        mock_forum_thread_no_http.site.client.login_check = MagicMock(
            side_effect=exceptions.LoginRequiredException("Login required")
        )

        with pytest.raises(exceptions.LoginRequiredException):
            mock_forum_thread_no_http.reply(source="Test reply")

    def test_reply_success(self, mock_forum_thread_no_http: ForumThread, amc_ok_response: dict[str, Any]) -> None:
        """返信が成功する"""
        mock_forum_thread_no_http.site.client.is_logged_in = True
        mock_forum_thread_no_http.site.client.login_check = MagicMock()

        mock_response = MagicMock()
        mock_response.json.return_value = amc_ok_response
        mock_forum_thread_no_http.site.amc_request = MagicMock(return_value=[mock_response])

        initial_count = mock_forum_thread_no_http.post_count
        result = mock_forum_thread_no_http.reply(source="Test reply")

        assert result == mock_forum_thread_no_http
        assert mock_forum_thread_no_http.post_count == initial_count + 1
        assert mock_forum_thread_no_http._posts is None  # キャッシュがクリアされる

    def test_reply_with_title(self, mock_forum_thread_no_http: ForumThread, amc_ok_response: dict[str, Any]) -> None:
        """タイトル付きで返信できる"""
        mock_forum_thread_no_http.site.client.is_logged_in = True
        mock_forum_thread_no_http.site.client.login_check = MagicMock()

        mock_response = MagicMock()
        mock_response.json.return_value = amc_ok_response
        mock_forum_thread_no_http.site.amc_request = MagicMock(return_value=[mock_response])

        mock_forum_thread_no_http.reply(source="Test reply", title="Re: Test")

        # amc_requestの呼び出し引数を検証
        call_args = mock_forum_thread_no_http.site.amc_request.call_args[0][0][0]
        assert call_args["title"] == "Re: Test"

    def test_reply_to_parent_post(
        self, mock_forum_thread_no_http: ForumThread, amc_ok_response: dict[str, Any]
    ) -> None:
        """親投稿への返信ができる"""
        mock_forum_thread_no_http.site.client.is_logged_in = True
        mock_forum_thread_no_http.site.client.login_check = MagicMock()

        mock_response = MagicMock()
        mock_response.json.return_value = amc_ok_response
        mock_forum_thread_no_http.site.amc_request = MagicMock(return_value=[mock_response])

        mock_forum_thread_no_http.reply(source="Test reply", parent_post_id=5001)

        # amc_requestの呼び出し引数を検証
        call_args = mock_forum_thread_no_http.site.amc_request.call_args[0][0][0]
        assert call_args["parentId"] == "5001"


class TestForumThreadGetFromId:
    """ForumThread.get_from_idのテスト"""

    def test_get_from_id_success(self, mock_site_no_http: Site, forum_thread_detail: dict[str, Any]) -> None:
        """IDからスレッドを取得できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_thread_detail
        mock_site_no_http.amc_request = MagicMock(return_value=[mock_response])

        thread = ForumThread.get_from_id(mock_site_no_http, 3001)
        assert thread.id == 3001
        assert thread.title == "Test Thread Title"
