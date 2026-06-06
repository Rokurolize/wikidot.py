"""ForumCategoryモジュールのユニットテスト"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

from wikidot.common import exceptions
from wikidot.common.exceptions import UnexpectedException
from wikidot.module.forum_category import ForumCategory, ForumCategoryCollection
from wikidot.module.forum_thread import ForumThread, ForumThreadCollection

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

    @pytest.mark.parametrize("categories", [True, False, "1001", ("1001",), 1001])
    def test_init_rejects_non_list_categories(self, mock_site_no_http: Site, categories: object) -> None:
        """カテゴリコレクションの初期化はlistまたはNoneだけ受け付ける"""
        bad_categories: Any = categories

        with pytest.raises(ValueError, match="categories must be a list or None"):
            ForumCategoryCollection(mock_site_no_http, bad_categories)

    @pytest.mark.parametrize("category", [None, True, "1001", {"id": 1001}])
    def test_init_rejects_non_category_entries(self, mock_site_no_http: Site, category: object) -> None:
        """カテゴリコレクションの初期化はForumCategoryだけ受け付ける"""
        with pytest.raises(ValueError, match="categories list entries must be ForumCategory"):
            ForumCategoryCollection(mock_site_no_http, [category])  # type: ignore[list-item]

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

    @pytest.mark.parametrize("bad_id", [None, True, "1001", 1001.0])
    def test_find_rejects_non_integer_ids(
        self, mock_site_no_http: Site, mock_forum_category_no_http: ForumCategory, bad_id: object
    ) -> None:
        """整数以外のカテゴリID検索キーを拒否する"""
        collection = ForumCategoryCollection(mock_site_no_http, [mock_forum_category_no_http])
        bad_id_value: Any = bad_id

        with pytest.raises(ValueError, match="id must be an integer"):
            collection.find(bad_id_value)


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

    def test_acquire_all_preserves_description_text_spacing(
        self, mock_site_no_http: Site, forum_start: dict[str, Any]
    ) -> None:
        """カテゴリ説明の段落や装飾要素間の空白を保持する"""
        body = forum_start["body"].replace(
            '<div class="description">Test category description</div>',
            '<div class="description"><p>First <span>part</span></p><p>Second part</p></div>',
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body}
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumCategoryCollection.acquire_all(mock_site_no_http)

        assert collection[0].description == "First part Second part"

    def test_acquire_all_preserves_title_text_spacing(
        self, mock_site_no_http: Site, forum_start: dict[str, Any]
    ) -> None:
        """カテゴリタイトルの段落や装飾要素間の空白を保持する"""
        body = forum_start["body"].replace(
            '<div class="title"><a href="/forum/c-1001/test-category">Test Category</a></div>',
            '<div class="title"><a href="/forum/c-1001/test-category"><p>First <span>part</span></p><p>Second part</p></a></div>',
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body}
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumCategoryCollection.acquire_all(mock_site_no_http)

        assert collection[0].title == "First part Second part"

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

    def test_acquire_all_malformed_row_includes_site_context(self, mock_site_no_http: Site) -> None:
        """カテゴリ行が壊れている場合はサイト名と行位置を含めて失敗する"""
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
                                        <div class="description">Test description</div>
                                    </td>
                                    <td class="threads">10</td>
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

        with pytest.raises(
            exceptions.NoElementException,
            match=r"Category row is malformed for site: test-site \(row=1, cells=2\)",
        ):
            ForumCategoryCollection.acquire_all(mock_site_no_http)

    @pytest.mark.parametrize(
        ("valid_cell", "malformed_cell", "expected_match"),
        [
            (
                '<td class="threads">10</td>',
                '<td class="threads">not-a-number</td>',
                r"Thread count is malformed for site: test-site \(row=1, field=threads, value=not-a-number\)",
            ),
            (
                '<td class="posts">50</td>',
                '<td class="posts">bad-count</td>',
                r"Post count is malformed for site: test-site \(row=1, field=posts, value=bad-count\)",
            ),
        ],
    )
    def test_acquire_all_malformed_count_includes_site_context(
        self,
        mock_site_no_http: Site,
        forum_start: dict[str, Any],
        valid_cell: str,
        malformed_cell: str,
        expected_match: str,
    ) -> None:
        """カテゴリ件数が壊れている場合はサイト名、行位置、値を含めて失敗する"""
        body = forum_start["body"].replace(valid_cell, malformed_cell, 1)
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": body}
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(exceptions.NoElementException, match=expected_match):
            ForumCategoryCollection.acquire_all(mock_site_no_http)

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

        with pytest.raises(UnexpectedException, match="Cannot retrieve forum categories for site: test-site"):
            ForumCategoryCollection.acquire_all(mock_site_no_http)

        mock_site_no_http.amc_request.assert_not_called()

    def test_acquire_all_missing_response_body_includes_site_context(self, mock_site_no_http: Site) -> None:
        """カテゴリ一覧応答のbody欠落時はサイト名付きで失敗する"""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match="Forum category list response body is not found for site: test-site",
        ):
            ForumCategoryCollection.acquire_all(mock_site_no_http)

        mock_site_no_http.amc_request.assert_not_called()

    def test_acquire_all_malformed_response_body_type_includes_site_context(self, mock_site_no_http: Site) -> None:
        """カテゴリ一覧応答のbody型が壊れている場合はサイト名と型情報付きで失敗する"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "body": ["not html"]}
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=r"Forum category list response body is malformed for site: test-site "
            r"\(field=body, expected=str, actual=list\)",
        ):
            ForumCategoryCollection.acquire_all(mock_site_no_http)

        mock_site_no_http.amc_request.assert_not_called()


# ============================================================
# ForumCategoryテスト
# ============================================================


class TestForumCategoryBasic:
    """ForumCategoryの基本テスト"""

    @pytest.mark.parametrize("category_id", [None, True, "1001", 1001.0])
    def test_init_rejects_non_integer_category_id(self, mock_site_no_http: Site, category_id: object) -> None:
        """整数以外のカテゴリIDを拒否する"""
        bad_category_id: Any = category_id

        with pytest.raises(ValueError, match="id must be an integer"):
            ForumCategory(
                site=mock_site_no_http,
                id=bad_category_id,
                title="Test Category",
                description="Test category description",
                threads_count=10,
                posts_count=50,
            )

    @pytest.mark.parametrize("threads_count", [None, True, "10", 10.0])
    def test_init_rejects_non_integer_threads_count(self, mock_site_no_http: Site, threads_count: object) -> None:
        """整数以外のスレッド数を拒否する"""
        bad_threads_count: Any = threads_count

        with pytest.raises(ValueError, match="threads_count must be an integer"):
            ForumCategory(
                site=mock_site_no_http,
                id=1001,
                title="Test Category",
                description="Test category description",
                threads_count=bad_threads_count,
                posts_count=50,
            )

    @pytest.mark.parametrize("posts_count", [None, True, "50", 50.0])
    def test_init_rejects_non_integer_posts_count(self, mock_site_no_http: Site, posts_count: object) -> None:
        """整数以外の投稿数を拒否する"""
        bad_posts_count: Any = posts_count

        with pytest.raises(ValueError, match="posts_count must be an integer"):
            ForumCategory(
                site=mock_site_no_http,
                id=1001,
                title="Test Category",
                description="Test category description",
                threads_count=10,
                posts_count=bad_posts_count,
            )

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

    @pytest.mark.parametrize("threads", [None, True, "3001", {"id": 3001}, []])
    def test_threads_setter_rejects_invalid_collections(
        self, mock_forum_category_no_http: ForumCategory, mock_forum_thread_no_http: ForumThread, threads: object
    ) -> None:
        """不正なthreads代入は既存のキャッシュを破壊しない"""
        cached_threads = ForumThreadCollection(mock_forum_category_no_http.site, [mock_forum_thread_no_http])
        mock_forum_category_no_http.threads = cached_threads
        bad_threads: Any = threads

        with pytest.raises(ValueError, match="category.threads must be ForumThreadCollection"):
            mock_forum_category_no_http.threads = bad_threads

        assert mock_forum_category_no_http.threads[0].id == 3001

    @pytest.mark.parametrize("thread", [None, True, "3001", {"id": 3001}])
    def test_threads_setter_rejects_invalid_collection_entries(
        self, mock_forum_category_no_http: ForumCategory, mock_forum_thread_no_http: ForumThread, thread: object
    ) -> None:
        """不正なthreads collection要素は既存のキャッシュを破壊しない"""
        cached_threads = ForumThreadCollection(mock_forum_category_no_http.site, [mock_forum_thread_no_http])
        mock_forum_category_no_http.threads = cached_threads
        bad_thread_entry: Any = thread
        bad_threads = ForumThreadCollection(mock_forum_category_no_http.site, [mock_forum_thread_no_http])
        bad_threads[0] = bad_thread_entry

        with pytest.raises(ValueError, match="category.threads list entries must be ForumThread"):
            mock_forum_category_no_http.threads = bad_threads

        assert mock_forum_category_no_http.threads[0].id == 3001


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

    def test_create_thread_success_invalidates_cached_threads(
        self,
        mock_forum_category_no_http: ForumCategory,
        mock_forum_thread_no_http: ForumThread,
        forum_newthread_success: dict[str, Any],
        forum_thread_detail: dict[str, Any],
    ) -> None:
        """スレッド作成成功後は古いthreads一覧キャッシュを使い回さない"""
        mock_forum_category_no_http.site.client.is_logged_in = True
        mock_forum_category_no_http.site.client.login_check = MagicMock()
        cached_threads = ForumThreadCollection(mock_forum_category_no_http.site, [mock_forum_thread_no_http])
        mock_forum_category_no_http.threads = cached_threads

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
        assert mock_forum_category_no_http._threads is None

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"title": 3}, "title must be a string"),
            ({"description": 3}, "description must be a string"),
            ({"source": 3}, "source must be a string"),
        ],
    )
    def test_create_thread_rejects_non_string_text_inputs_before_login(
        self,
        mock_forum_category_no_http: ForumCategory,
        kwargs: dict[str, object],
        message: str,
    ) -> None:
        """スレッド作成の文字列入力不正はログイン確認やAMCリクエスト前に拒否する"""
        mock_forum_category_no_http.site.client.login_check = MagicMock()
        mock_forum_category_no_http.site.amc_request = MagicMock()

        inputs: dict[str, Any] = {
            "title": "Test Thread",
            "description": "Test description",
            "source": "Test content",
            **kwargs,
        }
        with pytest.raises(ValueError, match=message):
            mock_forum_category_no_http.create_thread(**inputs)

        mock_forum_category_no_http.site.client.login_check.assert_not_called()
        mock_forum_category_no_http.site.amc_request.assert_not_called()

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

        with pytest.raises(
            exceptions.NoElementException,
            match=r"Thread ID is not found for site: test-site, category: 1001",
        ):
            mock_forum_category_no_http.create_thread(
                title="Test Thread",
                description="Test description",
                source="Test content",
            )

    def test_create_thread_boolean_thread_id_is_malformed_and_preserves_cache(
        self,
        mock_forum_category_no_http: ForumCategory,
        mock_forum_thread_no_http: ForumThread,
    ) -> None:
        """bool threadIdは生成結果不正として扱い古いthreadsキャッシュを保持する"""
        mock_forum_category_no_http.site.client.is_logged_in = True
        mock_forum_category_no_http.site.client.login_check = MagicMock()
        cached_threads = ForumThreadCollection(mock_forum_category_no_http.site, [mock_forum_thread_no_http])
        mock_forum_category_no_http.threads = cached_threads

        create_response = MagicMock()
        create_response.json.return_value = {"threadId": True, "status": "ok"}
        mock_forum_category_no_http.site.amc_request = MagicMock(return_value=[create_response])

        with pytest.raises(
            exceptions.NoElementException,
            match=r"Thread ID is not found for site: test-site, category: 1001",
        ):
            mock_forum_category_no_http.create_thread(
                title="Test Thread",
                description="Test description",
                source="Test content",
            )

        assert mock_forum_category_no_http.site.amc_request.call_count == 1
        assert mock_forum_category_no_http._threads is cached_threads

    def test_create_thread_missing_action_status_does_not_fetch_created_thread(
        self,
        mock_forum_category_no_http: ForumCategory,
        forum_thread_detail: dict[str, Any],
    ) -> None:
        """スレッド作成応答のstatus欠落は文脈付きで失敗し作成済みスレッドを取得しない"""
        mock_forum_category_no_http.site.client.is_logged_in = True
        mock_forum_category_no_http.site.client.login_check = MagicMock()

        create_response = MagicMock()
        create_response.json.return_value = {"threadId": 3001}
        detail_response = MagicMock()
        detail_response.json.return_value = forum_thread_detail
        mock_forum_category_no_http.site.amc_request = MagicMock(side_effect=[[create_response], [detail_response]])

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum category action response is malformed for site: test-site, category: 1001 "
                r"\(event=newThread, field=status\)"
            ),
        ):
            mock_forum_category_no_http.create_thread(
                title="Test Thread",
                description="Test description",
                source="Test content",
            )

        assert mock_forum_category_no_http.site.amc_request.call_count == 1
