"""ForumCategoryモジュールのユニットテスト"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

from wikidot.common import exceptions
from wikidot.common.exceptions import UnexpectedException
from wikidot.module.forum_category import ForumCategory, ForumCategoryCollection

if TYPE_CHECKING:
    from wikidot.module.site import Site


# ============================================================
# ForumCategoryCollectionテスト
# ============================================================


class TestForumCategoryCollectionInit:
    """ForumCategoryCollectionの初期化テスト"""

    def test_init_with_site_and_empty_categories(self, mock_site_no_http: Site) -> None:
        """サイトと空のカテゴリリストで初期化できる"""
        collection = ForumCategoryCollection(mock_site_no_http, [])
        assert collection.site == mock_site_no_http
        assert len(collection) == 0

    def test_init_with_site_and_categories(
        self, mock_site_no_http: Site, mock_forum_category_no_http: ForumCategory
    ) -> None:
        """サイトとカテゴリリストで初期化できる"""
        collection = ForumCategoryCollection(mock_site_no_http, [mock_forum_category_no_http])
        assert collection.site == mock_site_no_http
        assert len(collection) == 1

    def test_find_existing(self, mock_site_no_http: Site, mock_forum_category_no_http: ForumCategory) -> None:
        """存在するカテゴリをIDで検索できる"""
        collection = ForumCategoryCollection(mock_site_no_http, [mock_forum_category_no_http])
        found = collection.find(1001)
        assert found is not None
        assert found.id == 1001

    def test_find_nonexistent(self, mock_site_no_http: Site) -> None:
        """存在しないカテゴリを検索するとNoneを返す"""
        collection = ForumCategoryCollection(mock_site_no_http, [])
        found = collection.find(9999)
        assert found is None


class TestForumCategoryCollectionAcquireAll:
    """ForumCategoryCollection.acquire_allのテスト"""

    def test_site_forum_categories_retries_transient_fetch_failures(
        self, mock_site_no_http: Site, forum_start: dict[str, Any]
    ) -> None:
        """site.forum.categoriesは一時的なAMC失敗を再試行してカテゴリを返す"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_start
        amc_request = MagicMock(
            side_effect=[
                (RuntimeError("temporary failure"),),
                (mock_response,),
            ]
        )
        mock_site_no_http.client.amc_client.request = amc_request

        collection = mock_site_no_http.forum.categories

        assert len(collection) == 2
        assert collection[0].id == 1001
        assert amc_request.call_count == 2

    def test_acquire_all_success(self, mock_site_no_http: Site, forum_start: dict[str, Any]) -> None:
        """カテゴリ一覧を正常に取得できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_start
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumCategoryCollection.acquire_all(mock_site_no_http)
        assert len(collection) == 2

    def test_acquire_all_parse_fields(self, mock_site_no_http: Site, forum_start: dict[str, Any]) -> None:
        """カテゴリの各フィールドが正しくパースされる"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_start
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumCategoryCollection.acquire_all(mock_site_no_http)

        # 1つ目のカテゴリを検証
        category = collection[0]
        assert category.id == 1001
        assert category.title == "Test Category"
        assert category.description == "Test category description"
        assert category.threads_count == 10
        assert category.posts_count == 50

        # 2つ目のカテゴリを検証
        category2 = collection[1]
        assert category2.id == 1002
        assert category2.title == "Another Category"

    def test_acquire_all_ignores_nested_category_tables(self, mock_site_no_http: Site) -> None:
        """カテゴリ説明内のネストテーブルをカテゴリ行として扱わない"""
        response_body = {
            "status": "ok",
            "body": """
                <div class="forum-start-box">
                    <div class="forum-group">
                        <div class="head"><div class="title">Test Group</div></div>
                        <div>
                            <table>
                                <tr class="head"><td>Category</td><td>Threads</td><td>Posts</td></tr>
                                <tr>
                                    <td class="name">
                                        <div class="title">
                                            <a href="/forum/c-1001/test-category">Test Category</a>
                                        </div>
                                        <div class="description">
                                            Real description
                                            <table>
                                                <tr class="head">
                                                    <td>Category</td><td>Threads</td><td>Posts</td>
                                                </tr>
                                                <tr>
                                                    <td class="name">
                                                        <div class="title">
                                                            <a href="/forum/c-9999/fake-category">Fake Category</a>
                                                        </div>
                                                        <div class="description">Fake nested category</div>
                                                    </td>
                                                    <td class="threads">999</td>
                                                    <td class="posts">888</td>
                                                </tr>
                                            </table>
                                        </div>
                                    </td>
                                    <td class="threads">10</td>
                                    <td class="posts">50</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                </div>
            """,
        }
        mock_response = MagicMock()
        mock_response.json.return_value = response_body
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumCategoryCollection.acquire_all(mock_site_no_http)

        assert [category.id for category in collection] == [1001]
        assert collection[0].threads_count == 10
        assert collection[0].posts_count == 50

    def test_acquire_all_empty(self, mock_site_no_http: Site, forum_start_empty: dict[str, Any]) -> None:
        """空のカテゴリ一覧を取得できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_start_empty
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumCategoryCollection.acquire_all(mock_site_no_http)
        assert len(collection) == 0

    def test_acquire_all_raises_when_retry_is_exhausted(self, mock_site_no_http: Site) -> None:
        """カテゴリ一覧取得の再試行が尽きた場合は明示的に失敗する"""
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(None,))

        with pytest.raises(UnexpectedException, match="Cannot retrieve forum categories"):
            ForumCategoryCollection.acquire_all(mock_site_no_http)

        mock_site_no_http.amc_request.assert_not_called()


# ============================================================
# ForumCategoryテスト
# ============================================================


class TestForumCategoryBasic:
    """ForumCategoryの基本テスト"""

    def test_str(self, mock_forum_category_no_http: ForumCategory) -> None:
        """__str__が正しい文字列を返す"""
        result = str(mock_forum_category_no_http)
        assert "ForumCategory" in result
        assert "id=1001" in result
        assert "Test Category" in result

    def test_threads_setter(self, mock_forum_category_no_http: ForumCategory) -> None:
        """threadsプロパティのsetterが動作する"""
        from wikidot.module.forum_thread import ForumThreadCollection

        threads = ForumThreadCollection(mock_forum_category_no_http.site)
        mock_forum_category_no_http.threads = threads
        assert mock_forum_category_no_http._threads == threads


class TestForumCategoryCreateThread:
    """ForumCategory.create_threadのテスト"""

    def test_create_thread_not_logged_in(self, mock_forum_category_no_http: ForumCategory) -> None:
        """ログインしていない場合に例外"""
        mock_forum_category_no_http.site.client.is_logged_in = False
        mock_forum_category_no_http.site.client.login_check = MagicMock(
            side_effect=exceptions.LoginRequiredException("Login required")
        )

        with pytest.raises(exceptions.LoginRequiredException):
            mock_forum_category_no_http.create_thread(
                title="Test Thread",
                description="Test description",
                source="Test content",
            )

    def test_create_thread_success(
        self,
        mock_forum_category_no_http: ForumCategory,
        forum_newthread_success: dict[str, Any],
        forum_thread_detail: dict[str, Any],
    ) -> None:
        """スレッド作成が成功する"""
        mock_forum_category_no_http.site.client.is_logged_in = True
        mock_forum_category_no_http.site.client.login_check = MagicMock()

        # 1回目: newThread, 2回目: get_from_id
        create_response = MagicMock()
        create_response.json.return_value = forum_newthread_success
        detail_response = MagicMock()
        detail_response.json.return_value = forum_thread_detail

        mock_forum_category_no_http.site.amc_request = MagicMock(side_effect=[[create_response], [detail_response]])

        thread = mock_forum_category_no_http.create_thread(
            title="Test Thread",
            description="Test description",
            source="Test content",
        )

        assert thread.id == 3001
        assert thread.category == mock_forum_category_no_http

    @pytest.mark.parametrize("response_body", [{}, {"threadId": "3001"}])
    def test_create_thread_missing_or_invalid_thread_id_raises(
        self,
        mock_forum_category_no_http: ForumCategory,
        response_body: dict[str, Any],
    ) -> None:
        """threadId欠損または型不正はNoElementException"""
        mock_forum_category_no_http.site.client.is_logged_in = True
        mock_forum_category_no_http.site.client.login_check = MagicMock()

        create_response = MagicMock()
        create_response.json.return_value = response_body
        mock_forum_category_no_http.site.amc_request = MagicMock(return_value=[create_response])

        with pytest.raises(exceptions.NoElementException, match="Thread ID"):
            mock_forum_category_no_http.create_thread(
                title="Test Thread",
                description="Test description",
                source="Test content",
            )
