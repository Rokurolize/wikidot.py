"""Siteモジュールのユニットテスト"""

from typing import Any
from unittest.mock import MagicMock, create_autospec, patch

import httpx
import pytest
from pytest_httpx import HTTPXMock

from wikidot.common.exceptions import (
    LoginRequiredException,
    NoElementException,
    NotFoundException,
    TargetErrorException,
    UnexpectedException,
    WikidotStatusCodeException,
)
from wikidot.module.client import Client
from wikidot.module.page import Page, PageCollection
from wikidot.module.site import PagePublishResult, Site


def create_mock_client(is_logged_in: bool = True) -> MagicMock:
    """Clientクラスのモックを作成（isinstance()チェックを通過する）"""
    mock_client = create_autospec(Client, instance=True)
    mock_client.is_logged_in = is_logged_in
    if is_logged_in:
        mock_client.login_check.return_value = None
    else:
        mock_client.login_check.side_effect = LoginRequiredException("Login required")
    mock_client.amc_client = MagicMock()
    mock_client.amc_client.config.request_timeout = 30.0
    mock_client.amc_client.config.retry_batch_size = 50
    mock_client.amc_client.config.retry_max_retries = 3
    return mock_client


class TestSiteDataclass:
    """Siteデータクラスのテスト"""

    def test_site_str(self, mock_site_no_http: Site) -> None:
        """__str__が正しい文字列を返す"""
        result = str(mock_site_no_http)

        assert "Site(" in result
        assert "id=123456" in result
        assert "title=Test Site" in result
        assert "unix_name=test-site" in result

    def test_site_url_with_ssl(self, mock_client_no_http: MagicMock) -> None:
        """SSL対応サイトのURLはhttps"""
        site = Site(
            client=mock_client_no_http,
            id=1,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )

        assert site.url == "https://test.wikidot.com"

    def test_site_url_without_ssl(self, mock_client_no_http: MagicMock) -> None:
        """SSL非対応サイトのURLはhttp"""
        site = Site(
            client=mock_client_no_http,
            id=1,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=False,
        )

        assert site.url == "http://test.wikidot.com"

    def test_site_has_accessors(self, mock_site_no_http: Site) -> None:
        """Siteはpages/page/forumアクセサを持つ"""
        assert hasattr(mock_site_no_http, "pages")
        assert hasattr(mock_site_no_http, "page")
        assert hasattr(mock_site_no_http, "forum")


class TestSitePagesAccessor:
    """Site.pagesアクセサのテスト"""

    @staticmethod
    def _page(site: Site, fullname: str, page_id: int) -> Page:
        category, name = fullname.split(":", 1) if ":" in fullname else ("_default", fullname)
        page = Page(
            site=site,
            fullname=fullname,
            name=name,
            category=category,
            title=fullname,
            children_count=0,
            comments_count=0,
            size=0,
            rating=0,
            votes_count=0,
            rating_percent=None,
            revisions_count=0,
            parent_fullname=None,
            tags=[],
            created_by=None,
            created_at=None,
            updated_by=None,
            updated_at=None,
            commented_by=None,
            commented_at=None,
        )
        page.id = page_id
        return page

    @staticmethod
    def _source_response(wiki_text: str) -> MagicMock:
        response = MagicMock()
        response.json.return_value = {"body": f'<div class="page-source">\n\t{wiki_text}\n</div>'}
        return response

    def test_iter_search_fetches_bounded_offset_pages(self, mock_site_no_http: Site) -> None:
        """iter_searchはlimit内でoffsetを進めながらページを逐次取得する"""
        search_calls = []

        def search_pages(site: Site, query) -> PageCollection:
            search_calls.append(query)
            pages = [MagicMock(name=f"page-{query.offset + index}") for index in range(query.limit or 0)]
            return PageCollection(site, pages)

        with patch.object(PageCollection, "search_pages", side_effect=search_pages):
            pages = list(
                mock_site_no_http.pages.iter_search(
                    category="_default",
                    tags="scp",
                    perPage=2,
                    limit=5,
                )
            )

        assert len(pages) == 5
        assert [query.offset for query in search_calls] == [0, 2, 4]
        assert [query.limit for query in search_calls] == [2, 2, 1]
        assert [query.perPage for query in search_calls] == [2, 2, 2]
        assert [query.category for query in search_calls] == ["_default", "_default", "_default"]
        assert [query.tags for query in search_calls] == ["scp", "scp", "scp"]

    def test_iter_search_stops_after_short_page_without_limit(self, mock_site_no_http: Site) -> None:
        """limit未指定では最後の短いページで逐次取得を終了する"""
        search_calls = []
        counts_by_offset = {10: 2, 12: 2, 14: 1}

        def search_pages(site: Site, query) -> PageCollection:
            search_calls.append(query)
            pages = [MagicMock(name=f"page-{query.offset + index}") for index in range(counts_by_offset[query.offset])]
            return PageCollection(site, pages)

        with patch.object(PageCollection, "search_pages", side_effect=search_pages):
            pages = list(mock_site_no_http.pages.iter_search(parent="parent-page", offset=10, perPage=2))

        assert len(pages) == 5
        assert [query.offset for query in search_calls] == [10, 12, 14]
        assert [query.limit for query in search_calls] == [2, 2, 2]
        assert [query.parent for query in search_calls] == ["parent-page", "parent-page", "parent-page"]

    def test_iter_sources_yields_sources_in_search_order(self, mock_site_no_http: Site) -> None:
        """iter_sourcesは検索順を保ったままsourceを分割取得して結果を返す"""
        pages = [
            self._page(mock_site_no_http, "page-one", 101),
            self._page(mock_site_no_http, "page-two", 102),
            self._page(mock_site_no_http, "page-three", 103),
        ]

        def search_pages(site: Site, query) -> PageCollection:
            assert query.tags == "scp"
            assert query.limit == 3
            assert query.perPage == 3
            return PageCollection(site, pages)

        def source_responses(request_bodies: list[dict[str, Any]]) -> tuple[MagicMock, ...]:
            return tuple(self._source_response(f"source {body['page_id']}") for body in request_bodies)

        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(side_effect=source_responses)

        with patch.object(PageCollection, "search_pages", side_effect=search_pages):
            results = list(
                mock_site_no_http.pages.iter_sources(
                    tags="scp",
                    perPage=3,
                    limit=3,
                    source_batch_size=2,
                )
            )

        assert [result.ok for result in results] == [True, True, True]
        assert [result.page for result in results] == pages
        assert [result.source.wiki_text if result.source is not None else None for result in results] == [
            "source 101",
            "source 102",
            "source 103",
        ]
        assert [result.error for result in results] == [None, None, None]
        assert [len(call.args[0]) for call in mock_site_no_http.amc_request_with_retry.call_args_list] == [2, 1]
        mock_site_no_http.amc_request.assert_not_called()

    def test_iter_sources_falls_back_and_reports_page_failures(self, mock_site_no_http: Site) -> None:
        """iter_sourcesはbatch失敗分だけ小さいbatchで再試行しページ単位の失敗を返す"""
        pages = [
            self._page(mock_site_no_http, "page-one", 201),
            self._page(mock_site_no_http, "page-two", 202),
            self._page(mock_site_no_http, "page-three", 203),
        ]
        requested_page_ids = []

        def search_pages(site: Site, query) -> PageCollection:
            return PageCollection(site, pages)

        def source_responses(request_bodies: list[dict[str, Any]]) -> tuple[MagicMock | None, ...]:
            page_ids = [body["page_id"] for body in request_bodies]
            requested_page_ids.append(page_ids)
            if page_ids == [201, 202, 203]:
                return (self._source_response("source 201"), None, None)
            if page_ids == [202]:
                return (self._source_response("source 202 fallback"),)
            if page_ids == [203]:
                return (None,)
            raise AssertionError(f"Unexpected source request ids: {page_ids}")

        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(side_effect=source_responses)

        with patch.object(PageCollection, "search_pages", side_effect=search_pages):
            results = list(
                mock_site_no_http.pages.iter_sources(
                    limit=3,
                    perPage=3,
                    source_batch_size=3,
                    fallback_batch_size=1,
                )
            )

        assert requested_page_ids == [[201, 202, 203], [202], [203]]
        assert [result.page for result in results] == pages
        assert [result.ok for result in results] == [True, True, False]
        assert [result.source.wiki_text if result.source is not None else None for result in results] == [
            "source 201",
            "source 202 fallback",
            None,
        ]
        assert isinstance(results[2].error, NotFoundException)
        assert "page-three" in str(results[2].error)
        mock_site_no_http.amc_request.assert_not_called()

    def test_iter_sources_retries_missing_pages_when_fallback_batch_is_large(self, mock_site_no_http: Site) -> None:
        """fallback_batch_sizeが大きくても未取得ページは再試行する"""
        pages = [
            self._page(mock_site_no_http, "page-one", 301),
            self._page(mock_site_no_http, "page-two", 302),
        ]
        requested_page_ids = []

        def search_pages(site: Site, query) -> PageCollection:
            return PageCollection(site, pages)

        def source_responses(request_bodies: list[dict[str, Any]]) -> tuple[MagicMock | None, ...]:
            page_ids = [body["page_id"] for body in request_bodies]
            requested_page_ids.append(page_ids)
            if page_ids == [301, 302]:
                return (self._source_response("source 301"), None)
            if page_ids == [302]:
                return (self._source_response("source 302 fallback"),)
            raise AssertionError(f"Unexpected source request ids: {page_ids}")

        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(side_effect=source_responses)

        with patch.object(PageCollection, "search_pages", side_effect=search_pages):
            results = list(
                mock_site_no_http.pages.iter_sources(
                    limit=2,
                    perPage=2,
                    source_batch_size=2,
                    fallback_batch_size=10,
                )
            )

        assert requested_page_ids == [[301, 302], [302]]
        assert [result.ok for result in results] == [True, True]
        assert [result.source.wiki_text if result.source is not None else None for result in results] == [
            "source 301",
            "source 302 fallback",
        ]
        mock_site_no_http.amc_request.assert_not_called()

    def test_iter_sources_result_exposes_wiki_text(self, mock_site_no_http: Site) -> None:
        """PageSourceResultからsource本文を直接読める"""
        pages = [
            self._page(mock_site_no_http, "page-one", 351),
            self._page(mock_site_no_http, "page-two", 352),
        ]

        def search_pages(site: Site, query) -> PageCollection:
            return PageCollection(site, pages)

        def source_responses(request_bodies: list[dict[str, Any]]) -> tuple[MagicMock | None, ...]:
            page_ids = [body["page_id"] for body in request_bodies]
            if page_ids == [351, 352]:
                return (self._source_response("source 351"), None)
            if page_ids == [352]:
                return (None,)
            raise AssertionError(f"Unexpected source request ids: {page_ids}")

        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(side_effect=source_responses)

        with patch.object(PageCollection, "search_pages", side_effect=search_pages):
            results = list(
                mock_site_no_http.pages.iter_sources(
                    limit=2,
                    perPage=2,
                    source_batch_size=2,
                    fallback_batch_size=1,
                )
            )

        assert [result.wiki_text for result in results] == ["source 351", None]
        mock_site_no_http.amc_request.assert_not_called()

    def test_iter_sources_reports_parse_failures_without_losing_other_pages(self, mock_site_no_http: Site) -> None:
        """source解析失敗はページ単位の失敗にし、同じ検索内の他ページは継続する"""
        pages = [
            self._page(mock_site_no_http, "page-one", 401),
            self._page(mock_site_no_http, "page-two", 402),
            self._page(mock_site_no_http, "page-three", 403),
        ]
        requested_page_ids = []

        def search_pages(site: Site, query) -> PageCollection:
            return PageCollection(site, pages)

        malformed_response = MagicMock()
        malformed_response.json.return_value = {"body": "<div>missing source wrapper</div>"}

        def source_responses(request_bodies: list[dict[str, Any]]) -> tuple[MagicMock, ...]:
            page_ids = [body["page_id"] for body in request_bodies]
            requested_page_ids.append(page_ids)
            if page_ids == [401, 402, 403]:
                return (self._source_response("source 401"), malformed_response, self._source_response("source 403"))
            if page_ids == [402]:
                return (malformed_response,)
            if page_ids == [403]:
                return (self._source_response("source 403 fallback"),)
            raise AssertionError(f"Unexpected source request ids: {page_ids}")

        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(side_effect=source_responses)

        with patch.object(PageCollection, "search_pages", side_effect=search_pages):
            results = list(
                mock_site_no_http.pages.iter_sources(
                    limit=3,
                    perPage=3,
                    source_batch_size=3,
                    fallback_batch_size=1,
                )
            )

        assert requested_page_ids == [[401, 402, 403], [402], [403]]
        assert [result.ok for result in results] == [True, False, True]
        assert [result.source.wiki_text if result.source is not None else None for result in results] == [
            "source 401",
            None,
            "source 403 fallback",
        ]
        assert isinstance(results[1].error, NoElementException)
        assert "page-two" in str(results[1].error)
        mock_site_no_http.amc_request.assert_not_called()


class TestSitePageAccessor:
    """Site.pageアクセサのテスト"""

    def test_get_falls_back_to_default_category_name(
        self,
        mock_site_no_http: Site,
        mock_page_no_http,
    ) -> None:
        """fullname APIではなく_default/name検索でページを取得する"""
        with patch.object(
            PageCollection,
            "search_pages",
            return_value=PageCollection(mock_site_no_http, [mock_page_no_http]),
        ) as mock_search:
            page = mock_site_no_http.page.get("test-page")

        assert page is mock_page_no_http
        query = mock_search.call_args_list[0].args[1]
        assert query.category == "_default"
        assert query.name == "test-page"

    def test_get_falls_back_to_direct_page_id_when_listpages_is_stale(self, mock_site_no_http: Site) -> None:
        """ListPagesにまだ出ないページは直接URLのpageIdで取得する"""

        def acquire_ids(_site: Site, pages: list) -> list:
            pages[0].id = 12345
            return pages

        with (
            patch.object(PageCollection, "search_pages", return_value=PageCollection(mock_site_no_http, [])),
            patch.object(PageCollection, "_acquire_page_ids", side_effect=acquire_ids),
        ):
            page = mock_site_no_http.page.get("new-page")

        assert page is not None
        assert page.fullname == "new-page"
        assert page.name == "new-page"
        assert page.category == "_default"
        assert page.id == 12345

    def test_get_returns_none_when_direct_page_id_probe_is_404(self, mock_site_no_http: Site) -> None:
        """ListPagesにも直接URLにもないページはNoneを返す"""
        request = httpx.Request("GET", "https://test-site.wikidot.com/missing")
        response = httpx.Response(404, request=request)
        not_found = httpx.HTTPStatusError("not found", request=request, response=response)

        with (
            patch.object(PageCollection, "search_pages", return_value=PageCollection(mock_site_no_http, [])),
            patch.object(PageCollection, "_acquire_page_ids", side_effect=not_found),
        ):
            page = mock_site_no_http.page.get("missing", raise_when_not_found=False)

        assert page is None

    def test_create_force_edit_updates_existing_page(self, mock_site_no_http: Site) -> None:
        """force_edit=Trueでは既存ページを編集する"""
        existing_page = MagicMock()
        existing_page.edit.return_value = existing_page
        login_check = MagicMock()
        mock_site_no_http.client.login_check = login_check
        mock_site_no_http.page.get = MagicMock(return_value=existing_page)

        page = mock_site_no_http.page.create(
            "test-page",
            title="Updated Title",
            source="Updated source",
            comment="Overwrite",
            force_edit=True,
        )

        assert page is existing_page
        login_check.assert_called_once()
        existing_page.edit.assert_called_once_with(
            title="Updated Title",
            source="Updated source",
            comment="Overwrite",
            force_edit=True,
        )

    def test_create_not_logged_in_raises_before_lookup(self, mock_site_no_http: Site) -> None:
        """未ログイン時はforce_editでもページ検索前に拒否する"""
        mock_site_no_http.client.login_check = MagicMock(side_effect=LoginRequiredException("Login required"))
        mock_site_no_http.page.get = MagicMock()

        with pytest.raises(LoginRequiredException):
            mock_site_no_http.page.create("test-page", force_edit=True)

        mock_site_no_http.page.get.assert_not_called()

    def test_publish_edits_existing_page_sets_metadata_and_verifies_source(self, mock_site_no_http: Site) -> None:
        """既存ページの保存、メタデータ更新、ソース検証を一つのpublish操作で実行する"""
        mock_site_no_http.client.login_check = MagicMock()
        saved_page = MagicMock()
        saved_page.id = 12345
        saved_page.refresh_source.return_value.wiki_text = "Saved source"
        existing_page = MagicMock()
        existing_page.edit.return_value = saved_page
        mock_site_no_http.page.get = MagicMock(return_value=existing_page)

        result = mock_site_no_http.page.publish(
            "test-page",
            title="Updated Title",
            source="Saved source",
            comment="Automated publish",
            tags=["published", "_hidden"],
            parent_fullname="parent-page",
            metas={"codex-source": "demo"},
            force_edit=True,
            verify_source=True,
        )

        mock_site_no_http.client.login_check.assert_called_once()
        existing_page.edit.assert_called_once_with(
            title="Updated Title",
            source="Saved source",
            comment="Automated publish",
            force_edit=True,
        )
        saved_page.set_metadata.assert_called_once_with(
            tags=["published", "_hidden"],
            parent_fullname="parent-page",
            metas={"codex-source": "demo"},
        )
        saved_page.refresh_source.assert_called_once_with()
        assert result.page is saved_page
        assert result.page_id == 12345
        assert result.source_matches is True
        assert result.tags_updated is True
        assert result.parent_updated is True
        assert result.metas_updated is True

    def test_publish_creates_missing_page_without_optional_steps(self, mock_site_no_http: Site) -> None:
        """未作成ページは作成し、任意のメタデータ更新やソース検証は省略できる"""
        mock_site_no_http.client.login_check = MagicMock()
        created_page = MagicMock()
        created_page.id = 67890
        mock_site_no_http.page.get = MagicMock(return_value=None)

        with patch.object(Page, "create_or_edit", return_value=created_page) as mock_create_or_edit:
            result = mock_site_no_http.page.publish(
                "new-page",
                title="New Title",
                source="New source",
                comment="Initial publish",
            )

        mock_create_or_edit.assert_called_once_with(
            site=mock_site_no_http,
            fullname="new-page",
            title="New Title",
            source="New source",
            comment="Initial publish",
            force_edit=False,
            raise_on_exists=True,
        )
        created_page.set_metadata.assert_not_called()
        created_page.refresh_source.assert_not_called()
        assert result.page is created_page
        assert result.page_id == 67890
        assert result.source_matches is None
        assert result.tags_updated is False
        assert result.parent_updated is False
        assert result.metas_updated is False

    def test_publish_result_reports_create_or_edit_outcome(self, mock_site_no_http: Site) -> None:
        """publishの戻り値は新規作成か既存編集かを判別できる"""
        mock_site_no_http.client.login_check = MagicMock()

        edited_page = MagicMock()
        edited_page.id = 11111
        existing_page = MagicMock()
        existing_page.edit.return_value = edited_page
        mock_site_no_http.page.get = MagicMock(return_value=existing_page)

        edited_result = mock_site_no_http.page.publish("existing-page")

        assert edited_result.created is False

        created_page = MagicMock()
        created_page.id = 22222
        mock_site_no_http.page.get = MagicMock(return_value=None)

        with patch.object(Page, "create_or_edit", return_value=created_page):
            created_result = mock_site_no_http.page.publish("new-page")

        assert created_result.created is True

    def test_publish_result_exposes_aggregate_operation_statuses(self) -> None:
        """publishの戻り値は集約した後続処理ステータスも判別できる"""
        page = MagicMock()

        verified_with_metadata = PagePublishResult(
            page=page,
            page_id=12345,
            source_matches=True,
            tags_updated=False,
            parent_updated=True,
            metas_updated=False,
        )
        skipped_optional_steps = PagePublishResult(
            page=page,
            page_id=67890,
            source_matches=None,
            tags_updated=False,
            parent_updated=False,
            metas_updated=False,
        )
        failed_source_check = PagePublishResult(
            page=page,
            page_id=13579,
            source_matches=False,
            tags_updated=False,
            parent_updated=False,
            metas_updated=True,
        )

        assert verified_with_metadata.metadata_updated is True
        assert verified_with_metadata.source_verified is True
        assert skipped_optional_steps.metadata_updated is False
        assert skipped_optional_steps.source_verified is False
        assert failed_source_check.metadata_updated is True
        assert failed_source_check.source_verified is False

    def test_publish_raises_when_verified_source_mismatches(self, mock_site_no_http: Site) -> None:
        """保存後のViewSourceModule取得結果が入力sourceと違う場合は例外にする"""
        mock_site_no_http.client.login_check = MagicMock()
        saved_page = MagicMock()
        saved_page.refresh_source.return_value.wiki_text = "Remote source"
        existing_page = MagicMock()
        existing_page.edit.return_value = saved_page
        mock_site_no_http.page.get = MagicMock(return_value=existing_page)

        with pytest.raises(UnexpectedException, match="Saved source verification failed for page: test-page"):
            mock_site_no_http.page.publish(
                "test-page",
                title="Updated Title",
                source="Expected source",
                verify_source=True,
            )

        saved_page.set_metadata.assert_not_called()
        saved_page.refresh_source.assert_called_once_with()

    def test_publish_verifies_source_with_custom_normalizer(self, mock_site_no_http: Site) -> None:
        """呼び出し側の正規化ルールで保存後ソースを検証できる"""
        mock_site_no_http.client.login_check = MagicMock()
        saved_page = MagicMock()
        saved_page.id = 12345
        saved_page.refresh_source.return_value.wiki_text = "\nSaved source\n"
        existing_page = MagicMock()
        existing_page.edit.return_value = saved_page
        mock_site_no_http.page.get = MagicMock(return_value=existing_page)

        def normalize_source(text: str) -> str:
            return "\n".join(line.rstrip() for line in text.strip().splitlines())

        result = mock_site_no_http.page.publish(
            "test-page",
            title="Updated Title",
            source="Saved source   \n\n",
            verify_source=True,
            source_normalizer=normalize_source,
        )

        saved_page.refresh_source.assert_called_once_with()
        assert result.source_matches is True

    def test_publish_retries_post_save_visibility_before_returning_page_id(self, mock_site_no_http: Site) -> None:
        """保存直後のページID取得が一時的に失敗したら指定回数だけ再試行する"""
        mock_site_no_http.client.login_check = MagicMock()
        mock_site_no_http.page.get = MagicMock(return_value=None)

        class EventuallyVisiblePage:
            def __init__(self) -> None:
                self.id_attempts = 0
                self.set_metadata = MagicMock()
                self.refresh_source = MagicMock()

            @property
            def id(self) -> int:
                self.id_attempts += 1
                if self.id_attempts == 1:
                    raise UnexpectedException("Cannot find page id: new-page")
                return 24680

        created_page = EventuallyVisiblePage()

        with patch.object(Page, "create_or_edit", return_value=created_page):
            result = mock_site_no_http.page.publish(
                "new-page",
                title="New Title",
                source="New source",
                post_save_visibility_attempts=3,
                post_save_visibility_interval=0,
            )

        assert created_page.id_attempts == 2
        assert result.page is created_page
        assert result.page_id == 24680


class TestSiteFromUnixName:
    """Site.from_unix_name のテスト"""

    def test_from_unix_name_ssl_site(self, mock_client_no_http: MagicMock, httpx_mock: HTTPXMock) -> None:
        """SSL対応サイトを正しく取得できる"""
        html = """
        <html>
        <head><title>Test Site Title</title></head>
        <body>
        <script>
            WIKIREQUEST.info.siteId = 123456;
            WIKIREQUEST.info.siteUnixName = "test-site";
            WIKIREQUEST.info.domain = "test-site.wikidot.com";
        </script>
        </body>
        </html>
        """
        httpx_mock.add_response(
            url="http://test-site.wikidot.com",
            status_code=301,
            headers={"Location": "https://test-site.wikidot.com"},
        )
        httpx_mock.add_response(
            url="https://test-site.wikidot.com",
            text=html,
        )

        site = Site.from_unix_name(mock_client_no_http, "test-site")

        assert site.id == 123456
        assert site.title == "Test Site Title"
        assert site.unix_name == "test-site"
        assert site.domain == "test-site.wikidot.com"
        assert site.ssl_supported is True

    def test_from_unix_name_non_ssl_site(self, mock_client_no_http: MagicMock, httpx_mock: HTTPXMock) -> None:
        """SSL非対応サイトを正しく取得できる"""
        html = """
        <html>
        <head><title>Old Site</title></head>
        <body>
        <script>
            WIKIREQUEST.info.siteId = 999;
            WIKIREQUEST.info.siteUnixName = "old-site";
            WIKIREQUEST.info.domain = "old-site.wikidot.com";
        </script>
        </body>
        </html>
        """
        httpx_mock.add_response(
            url="http://old-site.wikidot.com",
            text=html,
        )

        site = Site.from_unix_name(mock_client_no_http, "old-site")

        assert site.id == 999
        assert site.ssl_supported is False

    def test_from_unix_name_not_found(self, mock_client_no_http: MagicMock, httpx_mock: HTTPXMock) -> None:
        """存在しないサイトはNotFoundException"""
        httpx_mock.add_response(
            url="http://nonexistent.wikidot.com",
            status_code=404,
        )

        with pytest.raises(NotFoundException):
            Site.from_unix_name(mock_client_no_http, "nonexistent")

    def test_from_unix_name_invalid_name_rejected_before_request(
        self, mock_client_no_http: MagicMock, httpx_mock: HTTPXMock
    ) -> None:
        """ホストを逸脱し得るunix_nameはリクエスト前に拒否する"""
        with pytest.raises(ValueError, match="Invalid Wikidot site UNIX name"):
            Site.from_unix_name(mock_client_no_http, "127.0.0.1:8000#")

        assert httpx_mock.get_requests() == []

    def test_from_unix_name_missing_site_id(self, mock_client_no_http: MagicMock, httpx_mock: HTTPXMock) -> None:
        """siteIdがない場合はUnexpectedException"""
        html = """
        <html>
        <head><title>Bad Site</title></head>
        <body>
        <script>
            WIKIREQUEST.info.siteUnixName = "bad-site";
            WIKIREQUEST.info.domain = "bad-site.wikidot.com";
        </script>
        </body>
        </html>
        """
        httpx_mock.add_response(
            url="http://bad-site.wikidot.com",
            text=html,
        )

        with pytest.raises(UnexpectedException) as exc_info:
            Site.from_unix_name(mock_client_no_http, "bad-site")

        assert "site id" in str(exc_info.value).lower()

    def test_from_unix_name_missing_title(self, mock_client_no_http: MagicMock, httpx_mock: HTTPXMock) -> None:
        """titleがない場合はUnexpectedException"""
        html = """
        <html>
        <head></head>
        <body>
        <script>
            WIKIREQUEST.info.siteId = 123;
            WIKIREQUEST.info.siteUnixName = "no-title";
            WIKIREQUEST.info.domain = "no-title.wikidot.com";
        </script>
        </body>
        </html>
        """
        httpx_mock.add_response(
            url="http://no-title.wikidot.com",
            text=html,
        )

        with pytest.raises(UnexpectedException) as exc_info:
            Site.from_unix_name(mock_client_no_http, "no-title")

        assert "title" in str(exc_info.value).lower()

    def test_from_unix_name_missing_unix_name(self, mock_client_no_http: MagicMock, httpx_mock: HTTPXMock) -> None:
        """siteUnixNameがない場合はUnexpectedException"""
        html = """
        <html>
        <head><title>Site</title></head>
        <body>
        <script>
            WIKIREQUEST.info.siteId = 123;
            WIKIREQUEST.info.domain = "site.wikidot.com";
        </script>
        </body>
        </html>
        """
        httpx_mock.add_response(
            url="http://site.wikidot.com",
            text=html,
        )

        with pytest.raises(UnexpectedException) as exc_info:
            Site.from_unix_name(mock_client_no_http, "site")

        assert "unix_name" in str(exc_info.value).lower()

    def test_from_unix_name_missing_domain(self, mock_client_no_http: MagicMock, httpx_mock: HTTPXMock) -> None:
        """domainがない場合はUnexpectedException"""
        html = """
        <html>
        <head><title>Site</title></head>
        <body>
        <script>
            WIKIREQUEST.info.siteId = 123;
            WIKIREQUEST.info.siteUnixName = "site";
        </script>
        </body>
        </html>
        """
        httpx_mock.add_response(
            url="http://site.wikidot.com",
            text=html,
        )

        with pytest.raises(UnexpectedException) as exc_info:
            Site.from_unix_name(mock_client_no_http, "site")

        assert "domain" in str(exc_info.value).lower()


class TestSiteAmcRequest:
    """Site.amc_request のテスト"""

    def test_amc_request_delegates_to_client(self, mock_client_no_http: MagicMock) -> None:
        """amc_requestはクライアントのAMCクライアントに委譲する"""
        site = Site(
            client=mock_client_no_http,
            id=1,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )
        mock_client_no_http.amc_client.request = MagicMock(return_value=(MagicMock(),))

        site.amc_request([{"moduleName": "Test"}])

        mock_client_no_http.amc_client.request.assert_called_once()
        call_args = mock_client_no_http.amc_client.request.call_args
        assert call_args[0][0] == [{"moduleName": "Test"}]
        assert call_args[0][2] == "test"  # site_name
        assert call_args[0][3] is True  # ssl_supported


class TestSiteInviteUser:
    """Site.invite_user のテスト"""

    def test_invite_user_success(self, site_invite_member_success: dict[str, Any]) -> None:
        """ユーザー招待成功"""
        mock_client = create_mock_client(is_logged_in=True)
        site = Site(
            client=mock_client,
            id=123456,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = site_invite_member_success
        mock_client.amc_client.request.return_value = (mock_response,)

        mock_user = MagicMock()
        mock_user.id = 12345
        mock_user.name = "test-user"

        site.invite_user(mock_user, "Welcome message")

        mock_client.amc_client.request.assert_called_once()
        call_args = mock_client.amc_client.request.call_args[0][0][0]
        assert call_args["action"] == "ManageSiteMembershipAction"
        assert call_args["event"] == "inviteMember"
        assert call_args["user_id"] == 12345

    def test_invite_user_already_invited(self, site_invite_member_already_invited: dict[str, Any]) -> None:
        """既に招待済みでTargetErrorException"""
        mock_client = create_mock_client(is_logged_in=True)
        site = Site(
            client=mock_client,
            id=123456,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )

        mock_user = MagicMock()
        mock_user.id = 12345
        mock_user.name = "test-user"

        with patch.object(site, "amc_request") as mock_amc_request:
            mock_amc_request.side_effect = WikidotStatusCodeException(
                site_invite_member_already_invited["message"],
                "already_invited",
            )

            with pytest.raises(TargetErrorException, match="already invited"):
                site.invite_user(mock_user, "Welcome")

    def test_invite_user_already_member(self, site_invite_member_already_member: dict[str, Any]) -> None:
        """既にメンバーでTargetErrorException"""
        mock_client = create_mock_client(is_logged_in=True)
        site = Site(
            client=mock_client,
            id=123456,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )

        mock_user = MagicMock()
        mock_user.id = 12345
        mock_user.name = "test-user"

        with patch.object(site, "amc_request") as mock_amc_request:
            mock_amc_request.side_effect = WikidotStatusCodeException(
                site_invite_member_already_member["message"],
                "already_member",
            )

            with pytest.raises(TargetErrorException, match="already a member"):
                site.invite_user(mock_user, "Welcome")

    def test_invite_user_not_logged_in(self) -> None:
        """未ログインでLoginRequiredException"""
        mock_client = create_mock_client(is_logged_in=False)
        site = Site(
            client=mock_client,
            id=123456,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )

        mock_user = MagicMock()
        mock_user.id = 12345

        with pytest.raises(LoginRequiredException):
            site.invite_user(mock_user, "Welcome")

    def test_invite_user_other_error_reraises(self) -> None:
        """その他のエラーは再送出"""
        mock_client = create_mock_client(is_logged_in=True)
        site = Site(
            client=mock_client,
            id=123456,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )

        mock_user = MagicMock()
        mock_user.id = 12345
        mock_user.name = "test-user"

        with patch.object(site, "amc_request") as mock_amc_request:
            mock_amc_request.side_effect = WikidotStatusCodeException(
                "Some other error",
                "other_error",
            )

            with pytest.raises(WikidotStatusCodeException) as exc_info:
                site.invite_user(mock_user, "Welcome")

            assert exc_info.value.status_code == "other_error"


class TestSiteMemberLookup:
    """Site.member_lookup のテスト"""

    def test_member_lookup_found(self, quickmodule_member_lookup: dict[str, Any]) -> None:
        """メンバーが見つかる場合"""
        mock_client = create_mock_client()
        site = Site(
            client=mock_client,
            id=123456,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )

        with patch("wikidot.module.site.QuickModule.member_lookup") as mock_lookup:
            from wikidot.util.quick_module import QMCUser

            mock_lookup.return_value = [
                QMCUser(id=12345, name="test-user"),
                QMCUser(id=67890, name="test-user-2"),
            ]

            result = site.member_lookup("test-user")

            assert result is True
            mock_lookup.assert_called_once_with(123456, "test-user")

    def test_member_lookup_not_found(self, quickmodule_member_lookup_empty: dict[str, Any]) -> None:
        """メンバーが見つからない場合"""
        mock_client = create_mock_client()
        site = Site(
            client=mock_client,
            id=123456,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )

        with patch("wikidot.module.site.QuickModule.member_lookup") as mock_lookup:
            mock_lookup.return_value = []

            result = site.member_lookup("nonexistent")

            assert result is False

    def test_member_lookup_with_user_id_match(self) -> None:
        """ユーザーIDも一致する場合"""
        mock_client = create_mock_client()
        site = Site(
            client=mock_client,
            id=123456,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )

        with patch("wikidot.module.site.QuickModule.member_lookup") as mock_lookup:
            from wikidot.util.quick_module import QMCUser

            mock_lookup.return_value = [QMCUser(id=12345, name="test-user")]

            result = site.member_lookup("test-user", user_id=12345)

            assert result is True

    def test_member_lookup_with_user_id_mismatch(self) -> None:
        """ユーザーIDが不一致の場合"""
        mock_client = create_mock_client()
        site = Site(
            client=mock_client,
            id=123456,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )

        with patch("wikidot.module.site.QuickModule.member_lookup") as mock_lookup:
            from wikidot.util.quick_module import QMCUser

            mock_lookup.return_value = [QMCUser(id=12345, name="test-user")]

            result = site.member_lookup("test-user", user_id=99999)

            assert result is False


class TestSiteGetRecentChanges:
    """Site.get_recent_changes のテスト"""

    def test_get_recent_changes_success(self, site_changes: dict[str, Any]) -> None:
        """変更履歴取得成功"""
        mock_client = create_mock_client()
        site = Site(
            client=mock_client,
            id=123456,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = site_changes
        mock_client.amc_client.request.return_value = (mock_response,)

        with patch("wikidot.module.site.user_parser") as mock_user_parser:
            mock_user = MagicMock()
            mock_user_parser.return_value = mock_user

            changes = site.get_recent_changes()

            assert len(changes) == 2
            assert changes[0].page_fullname == "test:test-page"
            assert changes[0].page_title == "test:\nTest Page Title"
            assert changes[0].revision_no == 3
            assert "S" in changes[0].flags
            assert changes[0].comment == "Test edit comment"
            assert changes[1].page_fullname == "scp-001"
            assert changes[1].revision_no == 1
            assert "N" in changes[1].flags

    def test_get_recent_changes_empty(self, site_changes_empty: dict[str, Any]) -> None:
        """変更履歴が空の場合"""
        mock_client = create_mock_client()
        site = Site(
            client=mock_client,
            id=123456,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = site_changes_empty
        mock_client.amc_client.request.return_value = (mock_response,)

        changes = site.get_recent_changes()

        assert len(changes) == 0

    def test_get_recent_changes_with_limit(self, site_changes: dict[str, Any]) -> None:
        """limit指定時"""
        mock_client = create_mock_client()
        site = Site(
            client=mock_client,
            id=123456,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = site_changes
        mock_client.amc_client.request.return_value = (mock_response,)

        with patch("wikidot.module.site.user_parser") as mock_user_parser:
            mock_user = MagicMock()
            mock_user_parser.return_value = mock_user

            changes = site.get_recent_changes(limit=1)

            assert len(changes) == 1
            assert changes[0].page_fullname == "test:test-page"

    def test_get_recent_changes_retries_transient_amc_failures(self, site_changes: dict[str, Any]) -> None:
        """変更履歴取得は一時的なAMC失敗を再試行する"""
        mock_client = create_mock_client()
        site = Site(
            client=mock_client,
            id=123456,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = site_changes
        mock_client.amc_client.request.side_effect = [
            (RuntimeError("temporary failure"),),
            (mock_response,),
        ]

        with patch("wikidot.module.site.user_parser") as mock_user_parser:
            mock_user = MagicMock()
            mock_user_parser.return_value = mock_user

            changes = site.get_recent_changes(limit=1)

        assert len(changes) == 1
        assert changes[0].page_fullname == "test:test-page"
        assert mock_client.amc_client.request.call_count == 2
        assert [call.args[1] for call in mock_client.amc_client.request.call_args_list] == [True, True]

    def test_get_recent_changes_zero_limit_returns_empty(self) -> None:
        """limit=0ではリクエストせず空リストを返す"""
        mock_client = create_mock_client()
        site = Site(
            client=mock_client,
            id=123456,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )

        changes = site.get_recent_changes(limit=0)

        assert changes == []
        mock_client.amc_client.request.assert_not_called()

    def test_get_recent_changes_ignores_non_numeric_pager_links(self, site_changes: dict[str, Any]) -> None:
        """数値ページがないpagerでは単一ページとして扱う"""
        mock_client = create_mock_client()
        site = Site(
            client=mock_client,
            id=123456,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            **site_changes,
            "body": site_changes["body"].replace(
                '<div class="pager"><span class="pager-no">ページ 1</span><span class="current">1</span></div>',
                '<div class="pager"><a href="#">next</a></div>',
            ),
        }
        mock_client.amc_client.request.return_value = (mock_response,)

        with patch("wikidot.module.site.user_parser") as mock_user_parser:
            mock_user_parser.return_value = MagicMock()

            changes = site.get_recent_changes()

        assert len(changes) == 2
        mock_client.amc_client.request.assert_called_once()
