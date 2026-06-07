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

    def test_init_empty_without_site_exposes_none_site(self) -> None:
        """空で親サイトも未指定ならsiteはNoneとして公開する"""
        collection = ForumThreadCollection()

        assert collection.site is None
        assert len(collection) == 0

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

    def test_init_infers_site_from_threads(self, mock_forum_thread_no_http: ForumThread) -> None:
        """サイト未指定時はスレッドからサイトを推測する"""
        collection = ForumThreadCollection(threads=[mock_forum_thread_no_http])
        assert collection.site == mock_forum_thread_no_http.site
        assert len(collection) == 1

    @pytest.mark.parametrize("threads", [True, False, "3001", ("3001",), 3001])
    def test_init_rejects_non_list_threads(self, mock_site_no_http: Site, threads: object) -> None:
        """スレッドコレクションの初期化はlistまたはNoneだけ受け付ける"""
        bad_threads: Any = threads

        with pytest.raises(ValueError, match="threads must be a list or None"):
            ForumThreadCollection(mock_site_no_http, bad_threads)

    @pytest.mark.parametrize("thread", [None, True, "3001", {"id": 3001}])
    def test_init_rejects_non_thread_entries(self, mock_site_no_http: Site, thread: object) -> None:
        """スレッドコレクションの初期化はForumThreadだけ受け付ける"""
        with pytest.raises(ValueError, match="threads list entries must be ForumThread"):
            ForumThreadCollection(mock_site_no_http, [thread])  # type: ignore[list-item]

    @pytest.mark.parametrize("site", [True, "test-site", {"unix_name": "test-site"}, object()])
    def test_init_rejects_malformed_sites(self, site: object) -> None:
        """明示されたsiteはSiteだけ受け付ける"""
        bad_site: Any = site

        with pytest.raises(ValueError, match="site must be a Site"):
            ForumThreadCollection(bad_site, threads=[])

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

    @pytest.mark.parametrize("bad_id", [None, True, "3001", 3001.0])
    def test_find_rejects_non_integer_ids(
        self, mock_site_no_http: Site, mock_forum_thread_no_http: ForumThread, bad_id: object
    ) -> None:
        """IDが整数でない場合は検索前に拒否する"""
        collection = ForumThreadCollection(mock_site_no_http, [mock_forum_thread_no_http])
        bad_find_id: Any = bad_id

        with pytest.raises(ValueError, match="id must be an integer"):
            collection.find(bad_find_id)


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

    @pytest.mark.parametrize("category", [None, True, "1001", {"id": 1001}, object()])
    def test_acquire_all_rejects_malformed_category_before_fetch(self, category: object) -> None:
        """直接カテゴリ内スレッド取得のcategory引数はForumCategoryだけ受け付ける"""
        bad_category: Any = category

        with pytest.raises(ValueError, match="category must be a ForumCategory"):
            ForumThreadCollection.acquire_all_in_category(bad_category)

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

    def test_acquire_all_populates_category_threads_cache(
        self, mock_forum_category_no_http: ForumCategory, forum_threads_in_category: dict[str, Any]
    ) -> None:
        """直接取得したカテゴリ内スレッド一覧はcategory.threadsのキャッシュとして保持する"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_threads_in_category
        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)

        assert mock_forum_category_no_http._threads is collection
        assert mock_forum_category_no_http.threads is collection
        mock_forum_category_no_http.site.amc_request_with_retry.assert_called_once()

    def test_acquire_all_missing_first_page_response_body_includes_context(
        self, mock_forum_category_no_http: ForumCategory
    ) -> None:
        """カテゴリ内スレッド一覧の初回body欠落はsite/category/page付きで失敗する"""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_forum_category_no_http.site.amc_request = MagicMock()
        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=r"Forum thread list response body is not found for site: test-site, category: 1001, page: 1",
        ):
            ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)

        mock_forum_category_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_malformed_first_page_response_body_type_includes_context(
        self, mock_forum_category_no_http: ForumCategory
    ) -> None:
        """カテゴリ内スレッド一覧の初回body型異常はsite/category/page/type付きで失敗する"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": ["not-html"]}
        mock_forum_category_no_http.site.amc_request = MagicMock()
        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum thread list response body is malformed for site: test-site, category: 1001, page: 1 "
                r"\(field=body, expected=str, actual=list\)"
            ),
        ):
            ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)

        mock_forum_category_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_skips_cached_category_threads(
        self, mock_forum_category_no_http: ForumCategory, mock_forum_thread_no_http: ForumThread
    ) -> None:
        """取得済みcategory.threadsは再取得しない"""
        cached_threads = ForumThreadCollection(mock_forum_category_no_http.site, [mock_forum_thread_no_http])
        mock_forum_category_no_http.threads = cached_threads
        mock_forum_category_no_http.site.amc_request = MagicMock()
        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(return_value=(None,))

        collection = ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)

        assert collection is cached_threads
        mock_forum_category_no_http.site.amc_request.assert_not_called()
        mock_forum_category_no_http.site.amc_request_with_retry.assert_not_called()

    def test_reload_threads_bypasses_cached_category_threads(
        self,
        mock_forum_category_no_http: ForumCategory,
        mock_forum_thread_no_http: ForumThread,
        forum_threads_in_category: dict[str, Any],
    ) -> None:
        """reload_threadsは取得済みthreadsを再利用せず再取得する"""
        cached_threads = ForumThreadCollection(mock_forum_category_no_http.site, [mock_forum_thread_no_http])
        mock_forum_category_no_http.threads = cached_threads
        response = MagicMock()
        response.json.return_value = forum_threads_in_category
        mock_forum_category_no_http.site.amc_request = MagicMock()
        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(return_value=(response,))

        collection = mock_forum_category_no_http.reload_threads()

        assert collection is not cached_threads
        assert mock_forum_category_no_http._threads is collection
        assert len(collection) == 2
        mock_forum_category_no_http.site.amc_request.assert_not_called()
        mock_forum_category_no_http.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "p": 1,
                    "c": mock_forum_category_no_http.id,
                    "moduleName": "forum/ForumViewCategoryModule",
                }
            ]
        )

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

    def test_acquire_all_ignores_description_pager_markup(
        self, mock_forum_category_no_http: ForumCategory, forum_threads_in_category: dict[str, Any]
    ) -> None:
        """スレッド説明内のpager風マークアップをページネーションとして扱わない"""
        body_with_description_pager = forum_threads_in_category["body"].replace(
            '<div class="description">Test thread description</div>',
            ('<div class="description">Test thread description<div class="pager"><a>1</a><a>2</a></div></div>'),
            1,
        )
        first_response = MagicMock()
        first_response.json.return_value = {"status": "ok", "body": body_with_description_pager}
        second_response = MagicMock()
        second_response.json.return_value = forum_threads_in_category
        mock_forum_category_no_http.site.amc_request = MagicMock()
        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(
            side_effect=[(first_response,), (second_response,)]
        )

        collection = ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)

        assert len(collection) == 2
        mock_forum_category_no_http.site.amc_request.assert_not_called()
        mock_forum_category_no_http.site.amc_request_with_retry.assert_called_once()

    def test_acquire_all_preserves_description_text_spacing(
        self, mock_forum_category_no_http: ForumCategory, forum_threads_in_category: dict[str, Any]
    ) -> None:
        """スレッド一覧説明内の段落や装飾タグのテキストを連結しない"""
        body_with_formatted_description = forum_threads_in_category["body"].replace(
            '<div class="description">Test thread description</div>',
            '<div class="description"><p>First <span>part</span></p><p>Second part</p></div>',
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body_with_formatted_description}
        mock_forum_category_no_http.site.amc_request = MagicMock()
        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)

        assert len(collection) == 2
        assert collection[0].description == "First part Second part"
        mock_forum_category_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_preserves_title_text_spacing(
        self, mock_forum_category_no_http: ForumCategory, forum_threads_in_category: dict[str, Any]
    ) -> None:
        """スレッド一覧タイトル内の段落や装飾タグのテキストを連結しない"""
        body_with_formatted_title = forum_threads_in_category["body"].replace(
            '<div class="title"><a href="/forum/t-3001/test-thread">Test Thread</a></div>',
            '<div class="title"><a href="/forum/t-3001/test-thread"><p>First <span>part</span></p><p>Second part</p></a></div>',
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body_with_formatted_title}
        mock_forum_category_no_http.site.amc_request = MagicMock()
        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)

        assert len(collection) == 2
        assert collection[0].title == "First part Second part"
        mock_forum_category_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_missing_name_cell_class_includes_category_context(
        self, mock_forum_category_no_http: ForumCategory, forum_threads_in_category: dict[str, Any]
    ) -> None:
        """スレッド一覧の構造セル欠損はサイト・カテゴリ・行を含めて失敗する"""
        body_with_bad_name_cell = forum_threads_in_category["body"].replace(
            '<td class="name">', '<td class="wrong">', 1
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body_with_bad_name_cell}
        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=r"Thread name element is not found for site: test-site \(category=1001, page=1, row=1, cells=4\)",
        ):
            ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)

    def test_acquire_all_malformed_post_count_includes_category_context(
        self, mock_forum_category_no_http: ForumCategory, forum_threads_in_category: dict[str, Any]
    ) -> None:
        """スレッド一覧の投稿数が壊れている場合はサイト・カテゴリ・行・値を含めて失敗する"""
        body_with_bad_count = forum_threads_in_category["body"].replace(
            '<td class="posts">5</td>',
            '<td class="posts">not-a-number</td>',
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body_with_bad_count}
        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Posts count is malformed for site: test-site "
                r"\(category=1001, page=1, row=1, field=posts, value=not-a-number\)"
            ),
        ):
            ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)

    def test_acquire_all_malformed_user_includes_category_page_row_and_value_context(
        self, mock_forum_category_no_http: ForumCategory, forum_threads_in_category: dict[str, Any]
    ) -> None:
        """スレッド一覧の作成者IDが壊れている場合はカテゴリ・ページ・行・値を含めて失敗する"""
        body_with_bad_user = forum_threads_in_category["body"].replace(
            "WIKIDOT.page.listeners.userInfo(12345); return false;",
            "WIKIDOT.page.listeners.userInfo(latest); return false;",
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body_with_bad_user}
        mock_forum_category_no_http.site.amc_request = MagicMock()
        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum thread list user is malformed for site: test-site "
                r"\(category=1001, page=1, row=1, field=created_by, "
                r"value=WIKIDOT\.page\.listeners\.userInfo\(latest\); return false;\)"
            ),
        ):
            ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)

        mock_forum_category_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_malformed_odate_includes_category_page_row_and_value_context(
        self, mock_forum_category_no_http: ForumCategory, forum_threads_in_category: dict[str, Any]
    ) -> None:
        """スレッド一覧の作成日時が壊れている場合はカテゴリ・ページ・行・値を含めて失敗する"""
        body_with_bad_odate = forum_threads_in_category["body"].replace(
            "odate time_1700000000",
            "odate time_latest",
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body_with_bad_odate}
        mock_forum_category_no_http.site.amc_request = MagicMock()
        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum thread list created_at is malformed for site: test-site "
                r"\(category=1001, page=1, row=1, field=created_at, value=time_latest\)"
            ),
        ):
            ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)

        mock_forum_category_no_http.site.amc_request.assert_not_called()

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

        with pytest.raises(
            exceptions.UnexpectedException,
            match=r"Cannot retrieve forum threads for site: test-site, category: 1001, page: 2",
        ):
            ForumThreadCollection.acquire_all_in_category(mock_forum_category_no_http)

        mock_forum_category_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_missing_paginated_response_body_includes_context(
        self, mock_forum_category_no_http: ForumCategory, forum_threads_in_category: dict[str, Any]
    ) -> None:
        """カテゴリ内スレッド一覧の追加body欠落はsite/category/page付きで失敗する"""
        body_with_pager = forum_threads_in_category["body"] + '<div class="pager"><a>1</a><a>2</a></div>'
        first_response = MagicMock()
        first_response.json.return_value = {"status": "ok", "body": body_with_pager}
        second_response = MagicMock()
        second_response.json.return_value = {}
        mock_forum_category_no_http.site.amc_request = MagicMock()
        mock_forum_category_no_http.site.amc_request_with_retry = MagicMock(
            side_effect=[(first_response,), (second_response,)]
        )

        with pytest.raises(
            exceptions.NoElementException,
            match=r"Forum thread list response body is not found for site: test-site, category: 1001, page: 2",
        ):
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

    def test_site_get_threads_rejects_non_list_thread_ids_before_fetch(self, mock_site_no_http: Site) -> None:
        """リストでないスレッドID入力はAMC取得前に拒否する"""
        thread_ids: Any = "3001"
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock()

        with pytest.raises(ValueError, match="thread_ids must be a list"):
            mock_site_no_http.get_threads(thread_ids)

        mock_site_no_http.amc_request.assert_not_called()
        mock_site_no_http.amc_request_with_retry.assert_not_called()

    @pytest.mark.parametrize("thread_ids", [[None], [True], ["3001"], [3001.5]])
    def test_acquire_from_ids_rejects_non_integer_thread_id_entries_before_fetch(
        self, mock_site_no_http: Site, thread_ids: list[Any]
    ) -> None:
        """スレッドIDリスト内の非整数値はAMC取得前に拒否する"""
        bad_thread_ids: Any = thread_ids
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock()

        with pytest.raises(ValueError, match="thread_ids list entries must be integers"):
            ForumThreadCollection.acquire_from_thread_ids(mock_site_no_http, bad_thread_ids)

        mock_site_no_http.amc_request.assert_not_called()
        mock_site_no_http.amc_request_with_retry.assert_not_called()

    @pytest.mark.parametrize("site", [None, True, "test-site", {"unix_name": "test-site"}, object()])
    def test_acquire_from_ids_rejects_malformed_site_before_fetch(self, site: object) -> None:
        """直接スレッド詳細取得のsite引数はSiteだけ受け付ける"""
        bad_site: Any = site

        with pytest.raises(ValueError, match="site must be a Site"):
            ForumThreadCollection.acquire_from_thread_ids(bad_site, [3001])

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

    def test_acquire_from_ids_ignores_description_statistics_markup(
        self, mock_site_no_http: Site, forum_thread_detail: dict[str, Any]
    ) -> None:
        """スレッド説明内のstatistics風マークアップを詳細メタデータとして扱わない"""
        fake_statistics = (
            "Test thread description"
            '<div class="statistics">Started by: '
            '<span class="printuser"><a href="http://www.wikidot.com/user:info/content-user" '
            'onclick="WIKIDOT.page.listeners.userInfo(99999); return false;">content_user</a></span><br/>'
            'Date: <span class="odate time_1700000500">17 Dec 2025</span><br/>'
            "Number of posts: 999<br/><br/></div>"
        )
        body = forum_thread_detail["body"].replace("Test thread description", fake_statistics, 1)
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body}
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumThreadCollection.acquire_from_thread_ids(mock_site_no_http, [3001])

        assert len(collection) == 1
        assert collection[0].created_by.name == "test_user"
        assert int(collection[0].created_at.timestamp()) == 1700000000
        assert collection[0].post_count == 5
        mock_site_no_http.amc_request.assert_not_called()

    def test_acquire_from_ids_preserves_formatted_description_text(
        self, mock_site_no_http: Site, forum_thread_detail: dict[str, Any]
    ) -> None:
        """スレッド説明内の装飾タグのテキストを欠落させない"""
        body = forum_thread_detail["body"].replace(
            "Test thread description",
            'Test <span class="wiki-formatting">thread</span> description',
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body}
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumThreadCollection.acquire_from_thread_ids(mock_site_no_http, [3001])

        assert len(collection) == 1
        assert collection[0].description == "Test thread description"
        assert collection[0].created_by.name == "test_user"
        assert collection[0].post_count == 5
        mock_site_no_http.amc_request.assert_not_called()

    def test_acquire_from_ids_preserves_breadcrumb_title_separator(
        self, mock_site_no_http: Site, forum_thread_detail: dict[str, Any]
    ) -> None:
        """スレッド名内のパンくず区切り文字をタイトルとして保持する"""
        body = forum_thread_detail["body"].replace("Test Thread Title", "Alpha » Beta", 1)
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body}
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumThreadCollection.acquire_from_thread_ids(mock_site_no_http, [3001])

        assert len(collection) == 1
        assert collection[0].title == "Alpha » Beta"
        assert collection[0].id == 3001
        mock_site_no_http.amc_request.assert_not_called()

    def test_acquire_from_ids_missing_description_block_includes_thread_context(
        self, mock_site_no_http: Site, forum_thread_detail: dict[str, Any]
    ) -> None:
        """スレッド詳細の構造欠損はサイト・要求スレッドIDを含めて失敗する"""
        body = forum_thread_detail["body"].replace('<div class="description-block">', '<div class="wrong-block">', 1)
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body}
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=r"Description block element is not found for site: test-site \(thread=3001\)",
        ):
            ForumThreadCollection.acquire_from_thread_ids(mock_site_no_http, [3001])

        mock_site_no_http.amc_request.assert_not_called()

    def test_acquire_from_ids_malformed_post_count_includes_thread_and_value_context(
        self, mock_site_no_http: Site, forum_thread_detail: dict[str, Any]
    ) -> None:
        """スレッド詳細の投稿数が壊れている場合はsite/thread/field/value文脈付きで失敗する"""
        body = forum_thread_detail["body"].replace("Number of posts: 5", "Number of posts: not-a-number", 1)
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body}
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Post count is malformed for site: test-site "
                r"\(thread=3001, field=posts, value=Number of posts: not-a-number\)"
            ),
        ):
            ForumThreadCollection.acquire_from_thread_ids(mock_site_no_http, [3001])

        mock_site_no_http.amc_request.assert_not_called()

    def test_acquire_from_ids_malformed_script_thread_id_includes_thread_and_value_context(
        self, mock_site_no_http: Site, forum_thread_detail: dict[str, Any]
    ) -> None:
        """スレッド詳細のscript内IDが壊れている場合はsite/thread/field/value文脈付きで失敗する"""
        body = forum_thread_detail["body"].replace(
            "WIKIDOT.forumThreadId = 3001;", "WIKIDOT.forumThreadId = latest;", 1
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body}
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum thread detail ID is malformed for site: test-site "
                r"\(thread=3001, field=thread_id, value=latest\)"
            ),
        ):
            ForumThreadCollection.acquire_from_thread_ids(mock_site_no_http, [3001])

        mock_site_no_http.amc_request.assert_not_called()

    def test_acquire_from_ids_malformed_user_includes_thread_and_value_context(
        self, mock_site_no_http: Site, forum_thread_detail: dict[str, Any]
    ) -> None:
        """スレッド詳細の作成者IDが壊れている場合はsite/thread/field/value文脈付きで失敗する"""
        body = forum_thread_detail["body"].replace(
            "WIKIDOT.page.listeners.userInfo(12345); return false;",
            "WIKIDOT.page.listeners.userInfo(latest); return false;",
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body}
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum thread detail user is malformed for site: test-site "
                r"\(thread=3001, field=created_by, "
                r"value=WIKIDOT\.page\.listeners\.userInfo\(latest\); return false;\)"
            ),
        ):
            ForumThreadCollection.acquire_from_thread_ids(mock_site_no_http, [3001])

        mock_site_no_http.amc_request.assert_not_called()

    def test_acquire_from_ids_malformed_odate_includes_thread_and_value_context(
        self, mock_site_no_http: Site, forum_thread_detail: dict[str, Any]
    ) -> None:
        """スレッド詳細の作成日時が壊れている場合はsite/thread/field/value文脈付きで失敗する"""
        body = forum_thread_detail["body"].replace(
            "odate time_1700000000",
            "odate time_latest",
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body}
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum thread detail created_at is malformed for site: test-site "
                r"\(thread=3001, field=created_at, value=time_latest\)"
            ),
        ):
            ForumThreadCollection.acquire_from_thread_ids(mock_site_no_http, [3001])

        mock_site_no_http.amc_request.assert_not_called()

    def test_acquire_from_ids_missing_response_body_includes_thread_context(self, mock_site_no_http: Site) -> None:
        """スレッド詳細のbody欠落はsite/thread付きで失敗する"""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=r"Forum thread detail response body is not found for site: test-site, thread: 3001",
        ):
            ForumThreadCollection.acquire_from_thread_ids(mock_site_no_http, [3001])

        mock_site_no_http.amc_request.assert_not_called()

    def test_acquire_from_ids_malformed_response_body_type_includes_thread_context(
        self, mock_site_no_http: Site
    ) -> None:
        """スレッド詳細のbody型異常はsite/thread/type付きで失敗する"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": ["not-html"]}
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum thread detail response body is malformed for site: test-site, thread: 3001 "
                r"\(field=body, expected=str, actual=list\)"
            ),
        ):
            ForumThreadCollection.acquire_from_thread_ids(mock_site_no_http, [3001])

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

        with pytest.raises(
            exceptions.UnexpectedException,
            match="Cannot retrieve forum thread for site: test-site, thread: 3001",
        ):
            ForumThreadCollection.acquire_from_thread_ids(mock_site_no_http, [3001])

        mock_site_no_http.amc_request.assert_not_called()


# ============================================================
# ForumThreadテスト
# ============================================================


class TestForumThreadBasic:
    """ForumThreadの基本テスト"""

    @pytest.mark.parametrize("site", [None, True, "test-site", {"unix_name": "test-site"}, object()])
    def test_init_rejects_malformed_sites(
        self,
        mock_forum_thread_no_http: ForumThread,
        site: object,
    ) -> None:
        """スレッドの親サイトはSiteだけ受け付ける"""
        bad_site: Any = site

        with pytest.raises(ValueError, match="site must be a Site"):
            ForumThread(
                site=bad_site,
                id=mock_forum_thread_no_http.id,
                title=mock_forum_thread_no_http.title,
                description=mock_forum_thread_no_http.description,
                created_by=mock_forum_thread_no_http.created_by,
                created_at=mock_forum_thread_no_http.created_at,
                post_count=mock_forum_thread_no_http.post_count,
                category=mock_forum_thread_no_http.category,
            )

    @pytest.mark.parametrize("thread_id", [None, True, "3001", 3001.0])
    def test_init_rejects_non_integer_thread_id(
        self,
        mock_forum_thread_no_http: ForumThread,
        thread_id: object,
    ) -> None:
        """スレッド初期化は整数以外のIDを拒否する"""
        bad_thread_id: Any = thread_id

        with pytest.raises(ValueError, match="thread_id must be an integer"):
            ForumThread(
                site=mock_forum_thread_no_http.site,
                id=bad_thread_id,
                title=mock_forum_thread_no_http.title,
                description=mock_forum_thread_no_http.description,
                created_by=mock_forum_thread_no_http.created_by,
                created_at=mock_forum_thread_no_http.created_at,
                post_count=mock_forum_thread_no_http.post_count,
                category=mock_forum_thread_no_http.category,
            )

    @pytest.mark.parametrize("title", [None, True, 3001, ["Test Thread"]])
    def test_init_rejects_non_string_title(
        self,
        mock_forum_thread_no_http: ForumThread,
        title: object,
    ) -> None:
        """文字列以外のスレッドタイトルを拒否する"""
        bad_title: Any = title

        with pytest.raises(ValueError, match="title must be a string"):
            ForumThread(
                site=mock_forum_thread_no_http.site,
                id=mock_forum_thread_no_http.id,
                title=bad_title,
                description=mock_forum_thread_no_http.description,
                created_by=mock_forum_thread_no_http.created_by,
                created_at=mock_forum_thread_no_http.created_at,
                post_count=mock_forum_thread_no_http.post_count,
                category=mock_forum_thread_no_http.category,
            )

    @pytest.mark.parametrize("description", [None, True, 3001, ["Test thread description"]])
    def test_init_rejects_non_string_description(
        self,
        mock_forum_thread_no_http: ForumThread,
        description: object,
    ) -> None:
        """文字列以外のスレッド説明を拒否する"""
        bad_description: Any = description

        with pytest.raises(ValueError, match="description must be a string"):
            ForumThread(
                site=mock_forum_thread_no_http.site,
                id=mock_forum_thread_no_http.id,
                title=mock_forum_thread_no_http.title,
                description=bad_description,
                created_by=mock_forum_thread_no_http.created_by,
                created_at=mock_forum_thread_no_http.created_at,
                post_count=mock_forum_thread_no_http.post_count,
                category=mock_forum_thread_no_http.category,
            )

    @pytest.mark.parametrize("post_count", [None, True, "5", 5.0])
    def test_init_rejects_non_integer_post_count(
        self,
        mock_forum_thread_no_http: ForumThread,
        post_count: object,
    ) -> None:
        """整数以外のスレッド投稿数を拒否する"""
        bad_post_count: Any = post_count

        with pytest.raises(ValueError, match="post_count must be an integer"):
            ForumThread(
                site=mock_forum_thread_no_http.site,
                id=mock_forum_thread_no_http.id,
                title=mock_forum_thread_no_http.title,
                description=mock_forum_thread_no_http.description,
                created_by=mock_forum_thread_no_http.created_by,
                created_at=mock_forum_thread_no_http.created_at,
                post_count=bad_post_count,
                category=mock_forum_thread_no_http.category,
            )

    @pytest.mark.parametrize("created_by", [None, True, 3001, "test_user", {"id": 12345}])
    def test_init_rejects_malformed_created_by(
        self,
        mock_forum_thread_no_http: ForumThread,
        created_by: object,
    ) -> None:
        """スレッド作成者はAbstractUserだけ受け付ける"""
        bad_created_by: Any = created_by

        with pytest.raises(ValueError, match="created_by must be an AbstractUser"):
            ForumThread(
                site=mock_forum_thread_no_http.site,
                id=mock_forum_thread_no_http.id,
                title=mock_forum_thread_no_http.title,
                description=mock_forum_thread_no_http.description,
                created_by=bad_created_by,
                created_at=mock_forum_thread_no_http.created_at,
                post_count=mock_forum_thread_no_http.post_count,
                category=mock_forum_thread_no_http.category,
            )

    @pytest.mark.parametrize("created_at", [None, True, 1700000000, "2023-11-14", []])
    def test_init_rejects_malformed_created_at(
        self,
        mock_forum_thread_no_http: ForumThread,
        created_at: object,
    ) -> None:
        """スレッド作成日時はdatetimeだけ受け付ける"""
        bad_created_at: Any = created_at

        with pytest.raises(ValueError, match="created_at must be a datetime"):
            ForumThread(
                site=mock_forum_thread_no_http.site,
                id=mock_forum_thread_no_http.id,
                title=mock_forum_thread_no_http.title,
                description=mock_forum_thread_no_http.description,
                created_by=mock_forum_thread_no_http.created_by,
                created_at=bad_created_at,
                post_count=mock_forum_thread_no_http.post_count,
                category=mock_forum_thread_no_http.category,
            )

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

    @pytest.mark.parametrize("category", [True, "1001", {"id": 1001}, object()])
    def test_init_rejects_malformed_categories(
        self,
        mock_forum_thread_no_http: ForumThread,
        category: object,
    ) -> None:
        """スレッドの親カテゴリはForumCategoryまたはNoneだけ受け付ける"""
        bad_category: Any = category

        with pytest.raises(ValueError, match="category must be a ForumCategory or None"):
            ForumThread(
                site=mock_forum_thread_no_http.site,
                id=mock_forum_thread_no_http.id,
                title=mock_forum_thread_no_http.title,
                description=mock_forum_thread_no_http.description,
                created_by=mock_forum_thread_no_http.created_by,
                created_at=mock_forum_thread_no_http.created_at,
                post_count=mock_forum_thread_no_http.post_count,
                category=bad_category,
            )

    @pytest.mark.parametrize("posts", [True, "5001", [], {"posts": []}, object()])
    def test_init_rejects_malformed_posts_cache(
        self,
        mock_forum_thread_no_http: ForumThread,
        posts: object,
    ) -> None:
        """スレッド投稿キャッシュはForumPostCollectionまたはNoneだけ受け付ける"""
        bad_posts: Any = posts

        with pytest.raises(ValueError, match="thread.posts must be ForumPostCollection or None"):
            ForumThread(
                site=mock_forum_thread_no_http.site,
                id=mock_forum_thread_no_http.id,
                title=mock_forum_thread_no_http.title,
                description=mock_forum_thread_no_http.description,
                created_by=mock_forum_thread_no_http.created_by,
                created_at=mock_forum_thread_no_http.created_at,
                post_count=mock_forum_thread_no_http.post_count,
                category=mock_forum_thread_no_http.category,
                _posts=bad_posts,
            )

    def test_init_accepts_valid_posts_cache(self, mock_forum_thread_no_http: ForumThread) -> None:
        """有効なスレッド投稿キャッシュは初期化時に保持する"""
        from wikidot.module.forum_post import ForumPostCollection

        posts = ForumPostCollection(mock_forum_thread_no_http, [])

        thread = ForumThread(
            site=mock_forum_thread_no_http.site,
            id=mock_forum_thread_no_http.id,
            title=mock_forum_thread_no_http.title,
            description=mock_forum_thread_no_http.description,
            created_by=mock_forum_thread_no_http.created_by,
            created_at=mock_forum_thread_no_http.created_at,
            post_count=mock_forum_thread_no_http.post_count,
            category=mock_forum_thread_no_http.category,
            _posts=posts,
        )

        assert thread.posts is posts

    def test_init_rejects_malformed_posts_cache_entries(
        self,
        mock_forum_thread_no_http: ForumThread,
    ) -> None:
        """スレッド投稿キャッシュ内の要素はForumPostだけ受け付ける"""
        from wikidot.module.forum_post import ForumPostCollection

        posts = ForumPostCollection(mock_forum_thread_no_http, [])
        bad_post: Any = object()
        posts.append(bad_post)

        with pytest.raises(ValueError, match="thread.posts list entries must be ForumPost"):
            ForumThread(
                site=mock_forum_thread_no_http.site,
                id=mock_forum_thread_no_http.id,
                title=mock_forum_thread_no_http.title,
                description=mock_forum_thread_no_http.description,
                created_by=mock_forum_thread_no_http.created_by,
                created_at=mock_forum_thread_no_http.created_at,
                post_count=mock_forum_thread_no_http.post_count,
                category=mock_forum_thread_no_http.category,
                _posts=posts,
            )

    @pytest.mark.parametrize("thread_id", [None, True, "3001"])
    def test_get_from_id_rejects_non_integer_thread_id_before_fetch(
        self, mock_site_no_http: Site, thread_id: Any
    ) -> None:
        """単一スレッドIDの非整数値はAMC取得前に拒否する"""
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock()

        with pytest.raises(ValueError, match="thread_id must be an integer"):
            ForumThread.get_from_id(mock_site_no_http, thread_id)

        mock_site_no_http.amc_request.assert_not_called()
        mock_site_no_http.amc_request_with_retry.assert_not_called()

    def test_site_get_thread_rejects_non_integer_thread_id_before_fetch(self, mock_site_no_http: Site) -> None:
        """サイトの単一スレッド取得でも非整数IDはAMC取得前に拒否する"""
        thread_id: Any = "3001"
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock()

        with pytest.raises(ValueError, match="thread_id must be an integer"):
            mock_site_no_http.get_thread(thread_id)

        mock_site_no_http.amc_request.assert_not_called()
        mock_site_no_http.amc_request_with_retry.assert_not_called()


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
            match="Cannot retrieve forum posts for site: test-site, thread: 3001, page: 1",
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

    def test_reply_success_updates_category_post_count_and_invalidates_threads(
        self,
        mock_forum_thread_no_http: ForumThread,
        mock_forum_category_no_http: ForumCategory,
        amc_ok_response: dict[str, Any],
    ) -> None:
        """返信成功後はカテゴリ側の投稿数とスレッド一覧キャッシュも更新する"""
        mock_forum_thread_no_http.category = mock_forum_category_no_http
        cached_threads = ForumThreadCollection(mock_forum_category_no_http.site, [mock_forum_thread_no_http])
        mock_forum_category_no_http.threads = cached_threads
        initial_category_post_count = mock_forum_category_no_http.posts_count
        mock_forum_thread_no_http.site.client.is_logged_in = True
        mock_forum_thread_no_http.site.client.login_check = MagicMock()

        mock_response = MagicMock()
        mock_response.json.return_value = amc_ok_response
        mock_forum_thread_no_http.site.amc_request = MagicMock(return_value=[mock_response])

        mock_forum_thread_no_http.reply(source="Test reply")

        assert mock_forum_category_no_http.posts_count == initial_category_post_count + 1
        assert mock_forum_category_no_http._threads is None

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

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"source": 3}, "source must be a string"),
            ({"title": 3}, "title must be a string"),
        ],
    )
    def test_reply_rejects_non_string_text_inputs_before_login(
        self,
        mock_forum_thread_no_http: ForumThread,
        kwargs: dict[str, object],
        message: str,
    ) -> None:
        """返信の文字列入力不正はログイン確認やAMCリクエスト前に拒否する"""
        mock_forum_thread_no_http.site.client.login_check = MagicMock()
        mock_forum_thread_no_http.site.amc_request = MagicMock()

        inputs: dict[str, Any] = {"source": "Test reply", "title": "", **kwargs}
        with pytest.raises(ValueError, match=message):
            mock_forum_thread_no_http.reply(**inputs)

        mock_forum_thread_no_http.site.client.login_check.assert_not_called()
        mock_forum_thread_no_http.site.amc_request.assert_not_called()

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

    @pytest.mark.parametrize("parent_post_id", [True, "5001", 5001.0, {"id": 5001}])
    def test_reply_rejects_invalid_parent_post_id_before_login(
        self,
        mock_forum_thread_no_http: ForumThread,
        mock_forum_category_no_http: ForumCategory,
        parent_post_id: object,
    ) -> None:
        """親投稿IDの不正値はログイン確認やAMCリクエスト前に拒否する"""
        mock_forum_thread_no_http.category = mock_forum_category_no_http
        cached_posts = MagicMock()
        cached_threads = ForumThreadCollection(mock_forum_category_no_http.site, [mock_forum_thread_no_http])
        mock_forum_thread_no_http._posts = cached_posts
        mock_forum_category_no_http.threads = cached_threads
        initial_post_count = mock_forum_thread_no_http.post_count
        initial_category_post_count = mock_forum_category_no_http.posts_count
        mock_forum_thread_no_http.site.client.login_check = MagicMock()
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        bad_parent_post_id: Any = parent_post_id

        with pytest.raises(ValueError, match="parent_post_id must be an integer or None"):
            mock_forum_thread_no_http.reply(source="Test reply", parent_post_id=bad_parent_post_id)

        mock_forum_thread_no_http.site.client.login_check.assert_not_called()
        mock_forum_thread_no_http.site.amc_request.assert_not_called()
        assert mock_forum_thread_no_http.post_count == initial_post_count
        assert mock_forum_thread_no_http._posts is cached_posts
        assert mock_forum_category_no_http.posts_count == initial_category_post_count
        assert mock_forum_category_no_http._threads is cached_threads

    def test_reply_missing_action_status_does_not_update_local_state(
        self, mock_forum_thread_no_http: ForumThread
    ) -> None:
        """返信応答のstatus欠落は文脈付きで失敗しローカル状態を更新しない"""
        mock_forum_thread_no_http.site.client.is_logged_in = True
        mock_forum_thread_no_http.site.client.login_check = MagicMock()
        initial_count = mock_forum_thread_no_http.post_count
        cached_posts = MagicMock()
        mock_forum_thread_no_http._posts = cached_posts

        malformed_response = MagicMock()
        malformed_response.json.return_value = {"body": ""}
        mock_forum_thread_no_http.site.amc_request = MagicMock(return_value=[malformed_response])

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum thread action response is malformed for site: test-site, thread: 3001 "
                r"\(event=savePost, field=status\)"
            ),
        ):
            mock_forum_thread_no_http.reply(source="Test reply")

        assert mock_forum_thread_no_http.post_count == initial_count
        assert mock_forum_thread_no_http._posts is cached_posts


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
