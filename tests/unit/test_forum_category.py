"""ForumCategoryモジュールのユニットテスト"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock

import pytest

from wikidot.common import exceptions
from wikidot.common.exceptions import UnexpectedException
from wikidot.module.forum_category import ForumCategory, ForumCategoryCollection
from wikidot.module.forum_thread import ForumThread, ForumThreadCollection

if TYPE_CHECKING:
    from wikidot.module.site import Site


def _category_on_other_site(category: ForumCategory) -> ForumCategory:
    from wikidot.module.site import Site

    other_site = Site(
        client=category.site.client,
        id=654321,
        title="Other Site",
        unix_name="other-site",
        domain="other-site.wikidot.com",
        ssl_supported=True,
    )
    return ForumCategory(
        site=other_site,
        id=1002,
        title=category.title,
        description=category.description,
        threads_count=category.threads_count,
        posts_count=category.posts_count,
    )


def _category_with_id(source_category: ForumCategory, category_id: int) -> ForumCategory:
    return ForumCategory(
        site=source_category.site,
        id=category_id,
        title=f"Category {category_id}",
        description=source_category.description,
        threads_count=source_category.threads_count,
        posts_count=source_category.posts_count,
    )


def _thread_in_category(source_thread: ForumThread, category: ForumCategory, thread_id: int = 3002) -> ForumThread:
    return ForumThread(
        site=category.site,
        id=thread_id,
        title=f"Thread {thread_id}",
        description=source_thread.description,
        created_by=source_thread.created_by,
        created_at=source_thread.created_at,
        post_count=source_thread.post_count,
        category=category,
    )


def _mutate_retained_category_id(category: ForumCategory, category_id: object) -> None:
    category.id = cast(Any, category_id)


# ============================================================
# ForumCategoryCollectionテスト
# ============================================================


class TestForumCategoryCollectionInit:
    """ForumCategoryCollectionの初期化テスト"""

    def test_init_empty_without_site_exposes_none_site(self) -> None:
        """空で親サイトも未指定ならsiteはNoneとして公開する"""
        collection = ForumCategoryCollection()

        assert collection.site is None
        assert len(collection) == 0

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

    def test_init_rejects_category_from_different_site(
        self, mock_site_no_http: Site, mock_forum_category_no_http: ForumCategory
    ) -> None:
        """明示siteと異なるsiteのカテゴリは保持しない"""
        other_category = _category_on_other_site(mock_forum_category_no_http)

        with pytest.raises(ValueError, match="categories must belong to the collection site"):
            ForumCategoryCollection(mock_site_no_http, [other_category])

    def test_init_rejects_mixed_site_categories_when_site_is_inferred(
        self, mock_forum_category_no_http: ForumCategory
    ) -> None:
        """site未指定時も推測siteと異なるカテゴリは保持しない"""
        other_category = _category_on_other_site(mock_forum_category_no_http)

        with pytest.raises(ValueError, match="categories must belong to the collection site"):
            ForumCategoryCollection(categories=[mock_forum_category_no_http, other_category])

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

    @pytest.mark.parametrize("site", [True, "test-site", {"unix_name": "test-site"}, object()])
    def test_init_rejects_malformed_sites(self, site: object) -> None:
        """明示されたsiteはSiteだけ受け付ける"""
        bad_site: Any = site

        with pytest.raises(ValueError, match="site must be a Site"):
            ForumCategoryCollection(bad_site, categories=[])

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

    def test_find_accepts_category_with_zero_retained_id(
        self, mock_site_no_http: Site, mock_forum_category_no_http: ForumCategory
    ) -> None:
        """保持済みカテゴリID=0の検索は有効なIDとして扱う"""
        category = _category_with_id(mock_forum_category_no_http, 0)
        collection = ForumCategoryCollection(mock_site_no_http, [category])

        assert collection.find(0) is category

    @pytest.mark.parametrize(
        ("retained_id", "search_id"),
        [
            (None, 1001),
            (True, 1),
            (False, 0),
            ("1001", 1001),
            (1001.0, 1001),
            ([], 1001),
        ],
    )
    def test_find_rejects_category_with_malformed_retained_ids(
        self,
        mock_site_no_http: Site,
        mock_forum_category_no_http: ForumCategory,
        retained_id: object,
        search_id: int,
    ) -> None:
        """保持済みカテゴリIDは検索比較前に整数として検証する"""
        category = _category_with_id(mock_forum_category_no_http, search_id)
        _mutate_retained_category_id(category, retained_id)
        collection = ForumCategoryCollection(mock_site_no_http, [category])

        with pytest.raises(ValueError, match="id must be an integer"):
            collection.find(search_id)

    def test_find_rejects_category_with_negative_retained_id(
        self, mock_site_no_http: Site, mock_forum_category_no_http: ForumCategory
    ) -> None:
        """保持済みカテゴリIDは負数を検索比較対象にしない"""
        category = _category_with_id(mock_forum_category_no_http, 1001)
        _mutate_retained_category_id(category, -1)
        collection = ForumCategoryCollection(mock_site_no_http, [category])

        with pytest.raises(ValueError, match="id must be non-negative"):
            collection.find(1001)


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

    @pytest.mark.parametrize("site", [None, True, "test-site", {"unix_name": "test-site"}, object()])
    def test_acquire_all_rejects_malformed_site_before_request(self, site: object) -> None:
        """カテゴリ一覧取得の直接site引数はSiteだけ受け付ける"""
        bad_site: Any = site

        with pytest.raises(ValueError, match="site must be a Site"):
            ForumCategoryCollection.acquire_all(bad_site)

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

    @pytest.mark.parametrize(
        ("valid_cell", "negative_cell", "expected_match"),
        [
            (
                '<td class="threads">10</td>',
                '<td class="threads">-1</td>',
                r"Thread count must be non-negative for site: test-site \(row=1, field=threads, value=-1\)",
            ),
            (
                '<td class="posts">50</td>',
                '<td class="posts">-1</td>',
                r"Post count must be non-negative for site: test-site \(row=1, field=posts, value=-1\)",
            ),
        ],
    )
    def test_acquire_all_negative_count_includes_site_context(
        self,
        mock_site_no_http: Site,
        forum_start: dict[str, Any],
        valid_cell: str,
        negative_cell: str,
        expected_match: str,
    ) -> None:
        """カテゴリ件数が負数の場合はサイト名、行位置、値を含めて失敗する"""
        body = forum_start["body"].replace(valid_cell, negative_cell, 1)
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

    @pytest.mark.parametrize("site", [None, True, "test-site", {"unix_name": "test-site"}, object()])
    def test_init_rejects_malformed_sites(self, site: object) -> None:
        """ForumCategoryの親siteはSiteだけ受け付ける"""
        bad_site: Any = site

        with pytest.raises(ValueError, match="site must be a Site"):
            ForumCategory(
                site=bad_site,
                id=1001,
                title="Test Category",
                description="Test category description",
                threads_count=10,
                posts_count=50,
            )

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

    def test_init_rejects_negative_category_id(self, mock_site_no_http: Site) -> None:
        """負のカテゴリIDを拒否する"""
        with pytest.raises(ValueError, match="id must be non-negative"):
            ForumCategory(
                site=mock_site_no_http,
                id=-1,
                title="Test Category",
                description="Test category description",
                threads_count=10,
                posts_count=50,
            )

    def test_init_accepts_zero_category_id(self, mock_site_no_http: Site) -> None:
        """0のカテゴリIDは有効なIDとして保持する"""
        category = ForumCategory(
            site=mock_site_no_http,
            id=0,
            title="Test Category",
            description="Test category description",
            threads_count=10,
            posts_count=50,
        )

        assert category.id == 0

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

    @pytest.mark.parametrize(
        ("field_name", "overrides"),
        [
            ("threads_count", {"threads_count": -1}),
            ("posts_count", {"posts_count": -1}),
        ],
    )
    def test_init_rejects_negative_counts(
        self, mock_site_no_http: Site, field_name: str, overrides: dict[str, int]
    ) -> None:
        """負数のカテゴリ件数を拒否する"""
        category_data = {
            "site": mock_site_no_http,
            "id": 1001,
            "title": "Test Category",
            "description": "Test category description",
            "threads_count": 10,
            "posts_count": 50,
        }
        category_data.update(overrides)

        with pytest.raises(ValueError, match=f"{field_name} must be non-negative"):
            ForumCategory(**category_data)

    def test_init_allows_zero_counts(self, mock_site_no_http: Site) -> None:
        """0件のカテゴリ件数は有効な値として保持する"""
        category = ForumCategory(
            site=mock_site_no_http,
            id=1001,
            title="Test Category",
            description="Test category description",
            threads_count=0,
            posts_count=0,
        )

        assert category.threads_count == 0
        assert category.posts_count == 0

    @pytest.mark.parametrize("title", [None, True, 1001, ["Test Category"]])
    def test_init_rejects_non_string_title(self, mock_site_no_http: Site, title: object) -> None:
        """文字列以外のカテゴリタイトルを拒否する"""
        bad_title: Any = title

        with pytest.raises(ValueError, match="title must be a string"):
            ForumCategory(
                site=mock_site_no_http,
                id=1001,
                title=bad_title,
                description="Test category description",
                threads_count=10,
                posts_count=50,
            )

    @pytest.mark.parametrize("description", [None, True, 1001, ["Test category description"]])
    def test_init_rejects_non_string_description(self, mock_site_no_http: Site, description: object) -> None:
        """文字列以外のカテゴリ説明を拒否する"""
        bad_description: Any = description

        with pytest.raises(ValueError, match="description must be a string"):
            ForumCategory(
                site=mock_site_no_http,
                id=1001,
                title="Test Category",
                description=bad_description,
                threads_count=10,
                posts_count=50,
            )

    @pytest.mark.parametrize("threads", [True, "3001", {"threads": []}, [], object()])
    def test_init_rejects_malformed_threads_cache(self, mock_site_no_http: Site, threads: object) -> None:
        """ForumCategoryの初期キャッシュはForumThreadCollectionだけ受け付ける"""
        bad_threads: Any = threads

        with pytest.raises(ValueError, match="category.threads must be ForumThreadCollection or None"):
            ForumCategory(
                site=mock_site_no_http,
                id=1001,
                title="Test Category",
                description="Test category description",
                threads_count=10,
                posts_count=50,
                _threads=bad_threads,
            )

    def test_init_accepts_valid_threads_cache(
        self, mock_forum_category_no_http: ForumCategory, mock_forum_thread_no_http: ForumThread
    ) -> None:
        """有効なForumThreadCollectionキャッシュを初期化時に保持できる"""
        threads = ForumThreadCollection(mock_forum_category_no_http.site, [mock_forum_thread_no_http])

        category = ForumCategory(
            site=mock_forum_category_no_http.site,
            id=1001,
            title="Test Category",
            description="Test category description",
            threads_count=10,
            posts_count=50,
            _threads=threads,
        )

        assert category.threads is threads

    def test_init_accepts_threads_cache_with_zero_retained_category_ids(
        self, mock_forum_category_no_http: ForumCategory, mock_forum_thread_no_http: ForumThread
    ) -> None:
        """ゼロカテゴリIDを持つ同カテゴリthreads cacheは保持できる"""
        zero_category = _category_with_id(mock_forum_category_no_http, 0)
        thread = _thread_in_category(mock_forum_thread_no_http, zero_category)
        threads = ForumThreadCollection(zero_category.site, [thread])

        category = ForumCategory(
            site=zero_category.site,
            id=0,
            title=zero_category.title,
            description=zero_category.description,
            threads_count=zero_category.threads_count,
            posts_count=zero_category.posts_count,
            _threads=threads,
        )

        assert category.threads is threads

    def test_init_rejects_threads_cache_from_different_site(
        self,
        mock_forum_category_no_http: ForumCategory,
    ) -> None:
        """別サイト用のスレッドキャッシュは初期化時に拒否する"""
        threads = ForumThreadCollection(_category_on_other_site(mock_forum_category_no_http).site, [])

        with pytest.raises(ValueError, match="category.threads must belong to the category"):
            ForumCategory(
                site=mock_forum_category_no_http.site,
                id=mock_forum_category_no_http.id,
                title=mock_forum_category_no_http.title,
                description=mock_forum_category_no_http.description,
                threads_count=mock_forum_category_no_http.threads_count,
                posts_count=mock_forum_category_no_http.posts_count,
                _threads=threads,
            )

    def test_init_rejects_threads_cache_entry_from_different_category(
        self,
        mock_forum_category_no_http: ForumCategory,
        mock_forum_thread_no_http: ForumThread,
    ) -> None:
        """キャッシュ内の別カテゴリスレッドは初期化時に拒否する"""
        other_category = _category_with_id(mock_forum_category_no_http, 1002)
        threads = ForumThreadCollection(mock_forum_category_no_http.site, [mock_forum_thread_no_http])
        threads.append(_thread_in_category(mock_forum_thread_no_http, other_category))

        with pytest.raises(ValueError, match="category.threads must belong to the category"):
            ForumCategory(
                site=mock_forum_category_no_http.site,
                id=mock_forum_category_no_http.id,
                title=mock_forum_category_no_http.title,
                description=mock_forum_category_no_http.description,
                threads_count=mock_forum_category_no_http.threads_count,
                posts_count=mock_forum_category_no_http.posts_count,
                _threads=threads,
            )

    @pytest.mark.parametrize(
        ("retained_id", "valid_id"), [(True, 1), (False, 0), ("1001", 1001), (1001.0, 1001), ([], 1001)]
    )
    def test_init_rejects_threads_cache_entry_with_malformed_retained_category_ids(
        self,
        mock_forum_category_no_http: ForumCategory,
        mock_forum_thread_no_http: ForumThread,
        retained_id: object,
        valid_id: int,
    ) -> None:
        """キャッシュ内スレッドの保持カテゴリIDが不正なら初期化時に拒否する"""
        category = _category_with_id(mock_forum_category_no_http, valid_id)
        thread_category = _category_with_id(mock_forum_category_no_http, valid_id)
        thread = _thread_in_category(mock_forum_thread_no_http, thread_category)
        _mutate_retained_category_id(thread_category, retained_id)
        threads = ForumThreadCollection(category.site, [thread])

        with pytest.raises(ValueError, match="id must be an integer"):
            ForumCategory(
                site=category.site,
                id=category.id,
                title=category.title,
                description=category.description,
                threads_count=category.threads_count,
                posts_count=category.posts_count,
                _threads=threads,
            )

    def test_init_rejects_threads_cache_entry_with_negative_retained_category_id(
        self, mock_forum_category_no_http: ForumCategory, mock_forum_thread_no_http: ForumThread
    ) -> None:
        """キャッシュ内スレッドの保持カテゴリIDが負数なら初期化時に拒否する"""
        category = _category_with_id(mock_forum_category_no_http, 1001)
        thread_category = _category_with_id(mock_forum_category_no_http, 1001)
        thread = _thread_in_category(mock_forum_thread_no_http, thread_category)
        _mutate_retained_category_id(thread_category, -1)
        threads = ForumThreadCollection(category.site, [thread])

        with pytest.raises(ValueError, match="id must be non-negative"):
            ForumCategory(
                site=category.site,
                id=category.id,
                title=category.title,
                description=category.description,
                threads_count=category.threads_count,
                posts_count=category.posts_count,
                _threads=threads,
            )

    @pytest.mark.parametrize("thread", [None, True, "3001", {"id": 3001}])
    def test_init_rejects_malformed_threads_cache_entries(
        self, mock_forum_category_no_http: ForumCategory, mock_forum_thread_no_http: ForumThread, thread: object
    ) -> None:
        """ForumCategoryの初期キャッシュ要素はForumThreadだけ受け付ける"""
        bad_thread: Any = thread
        threads = ForumThreadCollection(mock_forum_category_no_http.site, [mock_forum_thread_no_http])
        threads[0] = bad_thread

        with pytest.raises(ValueError, match="category.threads list entries must be ForumThread"):
            ForumCategory(
                site=mock_forum_category_no_http.site,
                id=1001,
                title="Test Category",
                description="Test category description",
                threads_count=10,
                posts_count=50,
                _threads=threads,
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

    def test_threads_setter_rejects_collection_from_different_site(
        self,
        mock_forum_category_no_http: ForumCategory,
        mock_forum_thread_no_http: ForumThread,
    ) -> None:
        """別サイト用threads collection代入は既存のキャッシュを破壊しない"""
        cached_threads = ForumThreadCollection(mock_forum_category_no_http.site, [mock_forum_thread_no_http])
        mock_forum_category_no_http.threads = cached_threads
        bad_threads = ForumThreadCollection(_category_on_other_site(mock_forum_category_no_http).site, [])

        with pytest.raises(ValueError, match="category.threads must belong to the category"):
            mock_forum_category_no_http.threads = bad_threads

        assert mock_forum_category_no_http.threads is cached_threads

    def test_threads_setter_rejects_collection_entry_from_different_category(
        self,
        mock_forum_category_no_http: ForumCategory,
        mock_forum_thread_no_http: ForumThread,
    ) -> None:
        """別カテゴリスレッドを含むthreads collection代入は既存のキャッシュを破壊しない"""
        cached_threads = ForumThreadCollection(mock_forum_category_no_http.site, [mock_forum_thread_no_http])
        mock_forum_category_no_http.threads = cached_threads
        bad_threads = ForumThreadCollection(mock_forum_category_no_http.site, [mock_forum_thread_no_http])
        bad_threads.append(
            _thread_in_category(mock_forum_thread_no_http, _category_with_id(mock_forum_category_no_http, 1002))
        )

        with pytest.raises(ValueError, match="category.threads must belong to the category"):
            mock_forum_category_no_http.threads = bad_threads

        assert mock_forum_category_no_http.threads is cached_threads

    @pytest.mark.parametrize(
        ("retained_id", "valid_id"), [(True, 1), (False, 0), ("1001", 1001), (1001.0, 1001), ([], 1001)]
    )
    def test_threads_setter_rejects_malformed_retained_parent_category_ids(
        self,
        mock_forum_category_no_http: ForumCategory,
        mock_forum_thread_no_http: ForumThread,
        retained_id: object,
        valid_id: int,
    ) -> None:
        """保持済み親カテゴリIDが不正ならthreads代入は既存キャッシュを破壊しない"""
        category = _category_with_id(mock_forum_category_no_http, valid_id)
        cached_threads = ForumThreadCollection(
            category.site, [_thread_in_category(mock_forum_thread_no_http, category)]
        )
        category.threads = cached_threads
        replacement_category = _category_with_id(mock_forum_category_no_http, valid_id)
        replacement_threads = ForumThreadCollection(
            category.site, [_thread_in_category(mock_forum_thread_no_http, replacement_category)]
        )
        _mutate_retained_category_id(category, retained_id)

        with pytest.raises(ValueError, match="id must be an integer"):
            category.threads = replacement_threads

        assert category._threads is cached_threads

    def test_threads_setter_rejects_negative_retained_parent_category_id(
        self, mock_forum_category_no_http: ForumCategory, mock_forum_thread_no_http: ForumThread
    ) -> None:
        """保持済み親カテゴリIDが負数ならthreads代入は既存キャッシュを破壊しない"""
        category = _category_with_id(mock_forum_category_no_http, 1001)
        cached_threads = ForumThreadCollection(
            category.site, [_thread_in_category(mock_forum_thread_no_http, category)]
        )
        category.threads = cached_threads
        replacement_category = _category_with_id(mock_forum_category_no_http, 1001)
        replacement_threads = ForumThreadCollection(
            category.site, [_thread_in_category(mock_forum_thread_no_http, replacement_category)]
        )
        _mutate_retained_category_id(category, -1)

        with pytest.raises(ValueError, match="id must be non-negative"):
            category.threads = replacement_threads

        assert category._threads is cached_threads

    @pytest.mark.parametrize(
        ("retained_id", "valid_id"), [(True, 1), (False, 0), ("1001", 1001), (1001.0, 1001), ([], 1001)]
    )
    def test_threads_setter_rejects_entry_with_malformed_retained_category_ids(
        self,
        mock_forum_category_no_http: ForumCategory,
        mock_forum_thread_no_http: ForumThread,
        retained_id: object,
        valid_id: int,
    ) -> None:
        """代入threads内の保持カテゴリIDが不正なら既存キャッシュを破壊しない"""
        category = _category_with_id(mock_forum_category_no_http, valid_id)
        cached_threads = ForumThreadCollection(
            category.site, [_thread_in_category(mock_forum_thread_no_http, category)]
        )
        category.threads = cached_threads
        bad_category = _category_with_id(mock_forum_category_no_http, valid_id)
        _mutate_retained_category_id(bad_category, retained_id)
        bad_threads = ForumThreadCollection(
            category.site, [_thread_in_category(mock_forum_thread_no_http, bad_category)]
        )

        with pytest.raises(ValueError, match="id must be an integer"):
            category.threads = bad_threads

        assert category._threads is cached_threads

    def test_threads_setter_rejects_entry_with_negative_retained_category_id(
        self, mock_forum_category_no_http: ForumCategory, mock_forum_thread_no_http: ForumThread
    ) -> None:
        """代入threads内の保持カテゴリIDが負数なら既存キャッシュを破壊しない"""
        category = _category_with_id(mock_forum_category_no_http, 1001)
        cached_threads = ForumThreadCollection(
            category.site, [_thread_in_category(mock_forum_thread_no_http, category)]
        )
        category.threads = cached_threads
        bad_category = _category_with_id(mock_forum_category_no_http, 1001)
        _mutate_retained_category_id(bad_category, -1)
        bad_threads = ForumThreadCollection(
            category.site, [_thread_in_category(mock_forum_thread_no_http, bad_category)]
        )

        with pytest.raises(ValueError, match="id must be non-negative"):
            category.threads = bad_threads

        assert category._threads is cached_threads


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

    @pytest.mark.parametrize("thread_id", [-1, -100])
    def test_create_thread_negative_thread_id_is_malformed_and_preserves_cache(
        self,
        mock_forum_category_no_http: ForumCategory,
        mock_forum_thread_no_http: ForumThread,
        thread_id: int,
    ) -> None:
        """負数threadIdは生成結果不正として扱い古いthreadsキャッシュを保持する"""
        mock_forum_category_no_http.site.client.is_logged_in = True
        mock_forum_category_no_http.site.client.login_check = MagicMock()
        cached_threads = ForumThreadCollection(mock_forum_category_no_http.site, [mock_forum_thread_no_http])
        mock_forum_category_no_http.threads = cached_threads

        create_response = MagicMock()
        create_response.json.return_value = {"threadId": thread_id, "status": "ok"}
        mock_forum_category_no_http.site.amc_request = MagicMock(return_value=[create_response])

        with pytest.raises(
            exceptions.NoElementException,
            match=r"Thread ID must be non-negative for site: test-site, category: 1001",
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
