"""Pageモジュールのユニットテスト"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import httpx
import pytest
from bs4 import BeautifulSoup

from wikidot.common import exceptions
from wikidot.module.page import Page, PageCollection, SearchPagesQuery
from wikidot.module.page_source import PageSource

if TYPE_CHECKING:
    from wikidot.module.site import Site


# ============================================================
# SearchPagesQueryテスト
# ============================================================


class TestSearchPagesQuery:
    """SearchPagesQueryのテスト"""

    def test_default_values(self) -> None:
        """デフォルト値が正しく設定される"""
        query = SearchPagesQuery()
        # デフォルトは "*"
        assert query.category == "*"
        assert query.pagetype == "*"
        # Noneのデフォルト
        assert query.tags is None
        assert query.parent is None
        assert query.fullname is None
        assert query.rating is None
        assert query.votes is None
        assert query.created_by is None
        assert query.created_at is None
        assert query.updated_at is None
        # その他のデフォルト
        assert query.order == "created_at desc"
        assert query.offset == 0
        assert query.limit is None
        assert query.range is None

    def test_as_dict_basic(self) -> None:
        """基本的な値を辞書に変換できる"""
        query = SearchPagesQuery(
            category="_default",
            fullname="test-page",
            limit=10,
        )
        result = query.as_dict()
        assert result["category"] == "_default"
        assert result["fullname"] == "test-page"
        assert result["limit"] == 10

    def test_as_dict_with_tags_list(self) -> None:
        """タグリストが正しくスペース区切りに変換される"""
        query = SearchPagesQuery(tags=["tag1", "tag2", "tag3"])
        result = query.as_dict()
        assert result["tags"] == "tag1 tag2 tag3"

    def test_as_dict_with_tags_string(self) -> None:
        """文字列タグがそのまま保持される"""
        query = SearchPagesQuery(tags="tag1 tag2")
        result = query.as_dict()
        assert result["tags"] == "tag1 tag2"

    def test_as_dict_excludes_none(self) -> None:
        """None値は辞書に含まれない"""
        query = SearchPagesQuery(fullname="test-page", tags=None, parent=None)
        result = query.as_dict()
        # tagsとparentはNoneなので含まれない
        assert "tags" not in result
        assert "parent" not in result
        # fullnameは設定されているので含まれる
        assert "fullname" in result

    def test_as_dict_range(self) -> None:
        """rangeが正しく含まれる"""
        query = SearchPagesQuery(range="before")
        result = query.as_dict()
        assert "range" in result
        assert result["range"] == "before"

    def test_custom_values(self) -> None:
        """カスタム値が正しく設定される"""
        query = SearchPagesQuery(
            category="component",
            tags=["scp", "euclid"],
            parent="parent-page",
            rating=">=10",
            order="rating desc",
            limit=50,
            offset=20,
        )
        result = query.as_dict()
        assert result["category"] == "component"
        assert result["tags"] == "scp euclid"
        assert result["parent"] == "parent-page"
        assert result["rating"] == ">=10"
        assert result["order"] == "rating desc"
        assert result["limit"] == 50
        assert result["offset"] == 20


# ============================================================
# PageCollectionテスト
# ============================================================


class TestPageCollectionInit:
    """PageCollectionの初期化テスト"""

    def test_init_with_site_and_empty_pages(self, mock_site_no_http: Site) -> None:
        """サイトと空のページリストで初期化できる"""
        collection = PageCollection(mock_site_no_http, [])
        assert collection.site == mock_site_no_http
        assert len(collection) == 0

    def test_init_with_site_and_pages(self, mock_site_no_http: Site, mock_page_no_http: Page) -> None:
        """サイトとページリストで初期化できる"""
        collection = PageCollection(mock_site_no_http, [mock_page_no_http])
        assert collection.site == mock_site_no_http
        assert len(collection) == 1

    def test_find_existing_page(self, mock_site_no_http: Site, mock_page_no_http: Page) -> None:
        """存在するページをfullnameで検索できる"""
        collection = PageCollection(mock_site_no_http, [mock_page_no_http])
        found = collection.find("test-page")
        assert found is not None
        assert found.fullname == "test-page"

    def test_find_nonexistent_page(self, mock_site_no_http: Site) -> None:
        """存在しないページを検索するとNoneを返す"""
        collection = PageCollection(mock_site_no_http, [])
        found = collection.find("nonexistent")
        assert found is None


class TestPageCollectionParse:
    """PageCollection._parseのテスト"""

    def test_parse_single_page(self, mock_site_no_http: Site, page_listpages_single: dict[str, Any]) -> None:
        """単一ページをパースできる"""
        html_body = BeautifulSoup(page_listpages_single["body"], "lxml")
        pages = PageCollection._parse(mock_site_no_http, html_body)
        assert len(pages) == 1
        page = pages[0]
        assert page.fullname == "scp-001"
        assert page.title == "SCP-001"
        assert page.rating == 100

    def test_parse_multiple_pages(self, mock_site_no_http: Site, page_listpages_multiple: dict[str, Any]) -> None:
        """複数ページをパースできる"""
        html_body = BeautifulSoup(page_listpages_multiple["body"], "lxml")
        pages = PageCollection._parse(mock_site_no_http, html_body)
        assert len(pages) == 2
        assert pages[0].fullname == "scp-001"
        assert pages[1].fullname == "scp-002"
        assert pages[1].children_count == 1
        assert isinstance(pages[1].children_count, int)

    def test_parse_empty_result(self, mock_site_no_http: Site, page_listpages_empty: dict[str, Any]) -> None:
        """空結果をパースできる"""
        html_body = BeautifulSoup(page_listpages_empty["body"], "lxml")
        pages = PageCollection._parse(mock_site_no_http, html_body)
        assert len(pages) == 0

    def test_parse_with_pm_rating(self, mock_site_no_http: Site, page_listpages_pm_rating: dict[str, Any]) -> None:
        """PM評価システムを正しくパースする"""
        html_body = BeautifulSoup(page_listpages_pm_rating["body"], "lxml")
        pages = PageCollection._parse(mock_site_no_http, html_body)
        assert len(pages) == 1
        # Note: rating_percent is None for non-5star rating (no span.page-rate-list-pages-start)
        assert pages[0].rating == 75
        assert pages[0].votes_count == 10

    def test_parse_with_5star_rating_percent(
        self, mock_site_no_http: Site, page_listpages_pm_rating: dict[str, Any]
    ) -> None:
        """5-star rating_percentの%付き値をパースする"""
        body = page_listpages_pm_rating["body"].replace(
            '<span class="set rating"><span class="name">rating</span> <span class="value">75</span></span>',
            '<span class="set rating"><span class="page-rate-list-pages-start"></span>'
            '<span class="name">rating</span> <span class="value">4.0</span></span>',
        )
        html_body = BeautifulSoup(body, "lxml")

        pages = PageCollection._parse(mock_site_no_http, html_body)

        assert pages[0].rating == 4.0
        assert pages[0].rating_percent == 0.75

    def test_parse_missing_optional_fields(
        self, mock_site_no_http: Site, page_listpages_missing_fields: dict[str, Any]
    ) -> None:
        """オプションフィールドがなくてもパースできる"""
        html_body = BeautifulSoup(page_listpages_missing_fields["body"], "lxml")
        pages = PageCollection._parse(mock_site_no_http, html_body)
        assert len(pages) == 1
        assert pages[0].tags == []
        # 値が空の場合はNoneになる（実際のWikidotレスポンスでは値spanがない）
        assert pages[0].parent_fullname is None
        assert pages[0].rating_percent is None

    def test_parse_no_element_exception(self, mock_site_no_http: Site, page_listpages_invalid: dict[str, Any]) -> None:
        """必須要素がない場合にNoElementExceptionを送出"""
        html_body = BeautifulSoup(page_listpages_invalid["body"], "lxml")
        with pytest.raises(exceptions.NoElementException):
            PageCollection._parse(mock_site_no_http, html_body)


class TestPageCollectionSearchPages:
    """PageCollection.search_pagesのテスト"""

    def test_search_pages_basic(self, mock_site_no_http: Site, page_listpages_single: dict[str, Any]) -> None:
        """基本的なページ検索ができる"""
        mock_response = MagicMock()
        mock_response.json.return_value = page_listpages_single
        mock_site_no_http.amc_request = MagicMock(return_value=[mock_response])

        pages = PageCollection.search_pages(mock_site_no_http, SearchPagesQuery())
        assert len(pages) == 1
        assert pages[0].fullname == "scp-001"

    def test_search_pages_retries_transient_first_page_failures(
        self, mock_site_no_http: Site, page_listpages_single: dict[str, Any]
    ) -> None:
        """初回ListPagesページの一時失敗はretryする"""
        mock_response = MagicMock()
        mock_response.json.return_value = page_listpages_single
        mock_site_no_http.amc_request = MagicMock(
            side_effect=[
                (RuntimeError("temporary failure"),),
                (mock_response,),
            ]
        )

        pages = PageCollection.search_pages(mock_site_no_http, SearchPagesQuery())

        assert len(pages) == 1
        assert pages[0].fullname == "scp-001"
        assert mock_site_no_http.amc_request.call_count == 2

    def test_search_pages_raises_when_first_page_retry_is_exhausted(self, mock_site_no_http: Site) -> None:
        """初回ListPagesページのretryを使い切った場合はoffset付きで失敗する"""
        mock_site_no_http.client.amc_client.config.retry_max_retries = 1
        mock_site_no_http.amc_request = MagicMock(return_value=(RuntimeError("temporary failure"),))

        with pytest.raises(exceptions.UnexpectedException, match="offset: 500"):
            PageCollection.search_pages(mock_site_no_http, SearchPagesQuery(offset=500))

        assert mock_site_no_http.amc_request.call_count == 2

    def test_search_pages_preserves_private_site_status_mapping(self, mock_site_no_http: Site) -> None:
        """private siteのnot_okは従来どおりForbiddenExceptionに変換する"""
        mock_site_no_http.amc_request = MagicMock(
            return_value=(exceptions.WikidotStatusCodeException("not ok", "not_ok"),)
        )

        with pytest.raises(exceptions.ForbiddenException, match="target site may be private"):
            PageCollection.search_pages(mock_site_no_http, SearchPagesQuery())

        mock_site_no_http.amc_request.assert_called_once()

    def test_search_pages_with_query(self, mock_site_no_http: Site, page_listpages_single: dict[str, Any]) -> None:
        """クエリパラメータを指定して検索できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = page_listpages_single
        mock_site_no_http.amc_request = MagicMock(return_value=[mock_response])

        query = SearchPagesQuery(
            category="scp",
            tags=["euclid"],
            limit=10,
        )
        PageCollection.search_pages(mock_site_no_http, query)

        # amc_requestが正しいパラメータで呼ばれたか確認
        call_args = mock_site_no_http.amc_request.call_args
        request_body = call_args[0][0][0]
        assert request_body["category"] == "scp"
        assert request_body["tags"] == "euclid"
        assert request_body["limit"] == 10

    def test_search_pages_forbidden(self, mock_site_no_http: Site) -> None:
        """アクセス禁止時に空のコレクションを返す"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "body": '<p class="error-block">You are not allowed to access this page.</p>',
        }
        mock_site_no_http.amc_request = MagicMock(return_value=[mock_response])

        pages = PageCollection.search_pages(mock_site_no_http, SearchPagesQuery())
        assert len(pages) == 0

    def test_search_pages_ignores_pager_without_numeric_targets(
        self, mock_site_no_http: Site, page_listpages_single: dict[str, Any]
    ) -> None:
        """数値ページがないpagerでは単一ページとして扱う"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            **page_listpages_single,
            "body": page_listpages_single["body"] + '<div class="pager"><span class="target">next</span></div>',
        }
        mock_site_no_http.amc_request = MagicMock(return_value=[mock_response])

        pages = PageCollection.search_pages(mock_site_no_http, SearchPagesQuery())

        assert len(pages) == 1
        mock_site_no_http.amc_request.assert_called_once()

    def test_search_pages_pagination_preserves_query_offset(
        self, mock_site_no_http: Site, page_listpages_single: dict[str, Any]
    ) -> None:
        """ページネーション時に初期offsetから続くページを取得する"""
        first_response = MagicMock()
        first_response.json.return_value = {
            **page_listpages_single,
            "body": page_listpages_single["body"]
            + '<div class="pager"><span class="target">1</span><span class="target"><a>2</a></span></div>',
        }
        second_response = MagicMock()
        second_response.json.return_value = page_listpages_single
        mock_site_no_http.amc_request = MagicMock(side_effect=[[first_response], [second_response]])

        PageCollection.search_pages(mock_site_no_http, SearchPagesQuery(offset=500, perPage=100))

        second_page_body = mock_site_no_http.amc_request.call_args_list[1].args[0][0]
        assert second_page_body["offset"] == 600

    def test_search_pages_additional_pager_requests_use_retry(
        self, mock_site_no_http: Site, page_listpages_single: dict[str, Any]
    ) -> None:
        """追加ListPagesページはretry付きAMCで取得する"""
        first_response = MagicMock()
        first_response.json.return_value = {
            **page_listpages_single,
            "body": page_listpages_single["body"]
            + '<div class="pager"><span class="target">1</span><span class="target"><a>2</a></span></div>',
        }
        second_response = MagicMock()
        second_response.json.return_value = page_listpages_single
        mock_site_no_http.amc_request = MagicMock(return_value=[first_response])
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(second_response,))

        pages = PageCollection.search_pages(mock_site_no_http, SearchPagesQuery(offset=500, perPage=100))

        assert len(pages) == 2
        mock_site_no_http.amc_request.assert_called_once()
        mock_site_no_http.amc_request_with_retry.assert_called_once()
        second_page_body = mock_site_no_http.amc_request_with_retry.call_args.args[0][0]
        assert second_page_body["offset"] == 600

    def test_search_pages_failed_retry_additional_page_raises(
        self, mock_site_no_http: Site, page_listpages_single: dict[str, Any]
    ) -> None:
        """retry後も追加ListPagesページを取得できない場合は部分結果を返さない"""
        first_response = MagicMock()
        first_response.json.return_value = {
            **page_listpages_single,
            "body": page_listpages_single["body"]
            + '<div class="pager"><span class="target">1</span><span class="target"><a>2</a></span></div>',
        }
        mock_site_no_http.amc_request = MagicMock(return_value=[first_response])
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(None,))

        with pytest.raises(exceptions.UnexpectedException, match="offset: 600"):
            PageCollection.search_pages(mock_site_no_http, SearchPagesQuery(offset=500, perPage=100))

        mock_site_no_http.amc_request.assert_called_once()
        mock_site_no_http.amc_request_with_retry.assert_called_once()

    def test_search_pages_limit_within_first_page_skips_additional_pager_requests(
        self, mock_site_no_http: Site, page_listpages_multiple: dict[str, Any]
    ) -> None:
        """limitが1ページ目で満たされる場合は追加ページを取得しない"""
        response = MagicMock()
        response.json.return_value = {
            **page_listpages_multiple,
            "body": page_listpages_multiple["body"]
            + '<div class="pager"><span class="target">1</span><span class="target"><a>2</a></span></div>',
        }
        mock_site_no_http.amc_request = MagicMock(return_value=[response])

        pages = PageCollection.search_pages(mock_site_no_http, SearchPagesQuery(limit=1, perPage=2))

        assert len(pages) == 1
        assert pages[0].fullname == "scp-001"
        mock_site_no_http.amc_request.assert_called_once()

    def test_search_pages_zero_limit_returns_empty_without_request(self, mock_site_no_http: Site) -> None:
        """limit=0ではリクエストせず空のコレクションを返す"""
        mock_site_no_http.amc_request = MagicMock()

        pages = PageCollection.search_pages(mock_site_no_http, SearchPagesQuery(limit=0))

        assert len(pages) == 0
        mock_site_no_http.amc_request.assert_not_called()

    def test_search_pages_limit_caps_additional_pager_requests(
        self, mock_site_no_http: Site, page_listpages_multiple: dict[str, Any]
    ) -> None:
        """limitに必要なページ数だけ追加ページを取得する"""
        first_response = MagicMock()
        first_response.json.return_value = {
            **page_listpages_multiple,
            "body": page_listpages_multiple["body"]
            + (
                '<div class="pager"><span class="target">1</span><span class="target"><a>2</a></span>'
                '<span class="target"><a>3</a></span></div>'
            ),
        }
        second_response = MagicMock()
        second_response.json.return_value = page_listpages_multiple
        mock_site_no_http.amc_request = MagicMock(side_effect=[[first_response], [second_response]])

        pages = PageCollection.search_pages(mock_site_no_http, SearchPagesQuery(limit=3, perPage=2))

        assert len(pages) == 3
        second_call_bodies = mock_site_no_http.amc_request.call_args_list[1].args[0]
        assert len(second_call_bodies) == 1
        assert second_call_bodies[0]["offset"] == 2


class TestPageCollectionAcquire:
    """PageCollection._acquire_*メソッドのテスト"""

    @staticmethod
    def _other_page(mock_site_no_http: Site, mock_page_no_http: Page) -> Page:
        return Page(
            site=mock_site_no_http,
            fullname="other-page",
            name="other-page",
            category="_default",
            title="Other Page",
            children_count=0,
            comments_count=0,
            size=1000,
            rating=10,
            votes_count=5,
            rating_percent=0.0,
            revisions_count=3,
            parent_fullname=None,
            tags=["tag1"],
            created_by=mock_page_no_http.created_by,
            created_at=mock_page_no_http.created_at,
            updated_by=mock_page_no_http.updated_by,
            updated_at=mock_page_no_http.updated_at,
            commented_by=None,
            commented_at=None,
        )

    @staticmethod
    def _patch_batched_page_id_request(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
        first_id_response = httpx.Response(200, text="WIKIREQUEST.info.pageId = 111;")
        second_id_response = httpx.Response(200, text="WIKIREQUEST.info.pageId = 222;")
        request = MagicMock(return_value=[first_id_response, second_id_response])
        monkeypatch.setattr("wikidot.module.page.RequestUtil.request", request)
        return request

    @staticmethod
    def _assert_batched_page_id_request(request: MagicMock) -> None:
        request.assert_called_once()
        assert request.call_args.args[2] == [
            "https://test-site.wikidot.com/test-page/norender/true/noredirect/true",
            "https://test-site.wikidot.com/other-page/norender/true/noredirect/true",
        ]

    @staticmethod
    def _json_response(body: dict[str, Any]) -> MagicMock:
        response = MagicMock()
        response.json.return_value = body
        return response

    def test_acquire_page_ids_deduplicates_duplicate_page_urls(
        self, monkeypatch: pytest.MonkeyPatch, mock_site_no_http: Site, mock_page_no_http: Page
    ) -> None:
        """同じ未取得ページURLのpage_id lookupは1回だけ行い重複ページへ反映する"""
        duplicate_page = self._other_page(mock_site_no_http, mock_page_no_http)
        duplicate_page.fullname = mock_page_no_http.fullname
        duplicate_page.name = mock_page_no_http.name
        duplicate_page.category = mock_page_no_http.category
        collection = PageCollection(mock_site_no_http, [mock_page_no_http, duplicate_page])
        response = httpx.Response(200, text="WIKIREQUEST.info.pageId = 333;")
        request = MagicMock(return_value=[response])
        monkeypatch.setattr("wikidot.module.page.RequestUtil.request", request)

        collection.get_page_ids()

        request.assert_called_once()
        assert request.call_args.args[2] == [
            "https://test-site.wikidot.com/test-page/norender/true/noredirect/true",
        ]
        assert mock_page_no_http.id == 333
        assert duplicate_page.id == 333

    def test_acquire_sources_success(
        self, mock_site_no_http: Site, mock_page_with_id: Page, page_viewsource: dict[str, Any]
    ) -> None:
        """ソースを正常に取得できる"""
        collection = PageCollection(mock_site_no_http, [mock_page_with_id])

        mock_response = MagicMock()
        mock_response.json.return_value = page_viewsource
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection.get_page_sources()
        mock_site_no_http.amc_request.assert_not_called()
        mock_site_no_http.amc_request_with_retry.assert_called_once()
        assert mock_page_with_id._source is not None
        # フィクスチャの内容に合わせて検証
        assert "page content" in mock_page_with_id._source.wiki_text

    def test_acquire_sources_preserves_multiline_source_text(
        self, mock_site_no_http: Site, mock_page_with_id: Page
    ) -> None:
        """ViewSourceModuleの折り返しタブを複数行で正しく除去する"""
        collection = PageCollection(mock_site_no_http, [mock_page_with_id])
        body = {"body": '<div class="page-source">\n\t+ Source from viewsource\n\t\n\tFoundation line.\n</div>'}

        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(self._json_response(body),))

        collection.get_page_sources()

        assert mock_page_with_id._source is not None
        assert mock_page_with_id._source.wiki_text == "+ Source from viewsource\n\nFoundation line."

    def test_acquire_sources_batches_missing_page_ids(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_site_no_http: Site,
        mock_page_no_http: Page,
        page_viewsource: dict[str, Any],
    ) -> None:
        """ID未取得ページのsource取得ではpage_id取得をまとめて行う"""
        second_page = self._other_page(mock_site_no_http, mock_page_no_http)
        collection = PageCollection(mock_site_no_http, [mock_page_no_http, second_page])

        request = self._patch_batched_page_id_request(monkeypatch)

        source_responses = []
        for _ in collection:
            source_responses.append(self._json_response(page_viewsource))
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=tuple(source_responses))

        collection.get_page_sources()

        self._assert_batched_page_id_request(request)
        mock_site_no_http.amc_request.assert_not_called()
        request_bodies = mock_site_no_http.amc_request_with_retry.call_args.args[0]
        assert [body["page_id"] for body in request_bodies] == [111, 222]

    def test_acquire_sources_skips_failed_retry_response(
        self, mock_site_no_http: Site, mock_page_with_id: Page, page_viewsource: dict[str, Any]
    ) -> None:
        """source取得の一部失敗は成功ページを保持し失敗ページを未取得にする"""
        second_page = self._other_page(mock_site_no_http, mock_page_with_id)
        second_page.id = 222
        collection = PageCollection(mock_site_no_http, [mock_page_with_id, second_page])

        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(self._json_response(page_viewsource), None))

        collection.get_page_sources()

        mock_site_no_http.amc_request.assert_not_called()
        assert mock_page_with_id._source is not None
        assert second_page._source is None

    def test_acquire_sources_preserves_later_successes_when_parse_fails(
        self, mock_site_no_http: Site, mock_page_with_id: Page
    ) -> None:
        """途中のsource解析失敗でも同じbatch内の後続成功sourceは保持する"""
        second_page = self._other_page(mock_site_no_http, mock_page_with_id)
        second_page.id = 222
        second_page.fullname = "malformed-page"
        third_page = self._other_page(mock_site_no_http, mock_page_with_id)
        third_page.id = 333
        third_page.fullname = "later-page"
        collection = PageCollection(mock_site_no_http, [mock_page_with_id, second_page, third_page])

        first_body = {"body": '<div class="page-source">\n\tfirst source\n</div>'}
        malformed_body = {"body": "<div>missing source wrapper</div>"}
        third_body = {"body": '<div class="page-source">\n\tthird source\n</div>'}
        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(
            return_value=(
                self._json_response(first_body),
                self._json_response(malformed_body),
                self._json_response(third_body),
            )
        )

        with pytest.raises(exceptions.NoElementException, match="malformed-page"):
            collection.get_page_sources()

        mock_site_no_http.amc_request.assert_not_called()
        assert mock_page_with_id._source is not None
        assert mock_page_with_id._source.wiki_text == "first source"
        assert second_page._source is None
        assert third_page._source is not None
        assert third_page._source.wiki_text == "third source"

    def test_acquire_sources_skips_already_acquired_pages(
        self, mock_site_no_http: Site, mock_page_with_id: Page, page_viewsource: dict[str, Any]
    ) -> None:
        """取得済みsourceがあるページは再取得せず未取得ページだけ取得する"""
        second_page = self._other_page(mock_site_no_http, mock_page_with_id)
        second_page.id = 222
        mock_page_with_id._source = PageSource(mock_page_with_id, "cached content")
        collection = PageCollection(mock_site_no_http, [mock_page_with_id, second_page])

        def retry_source_requests(request_bodies: list[dict[str, Any]]) -> tuple[MagicMock, ...]:
            return tuple(self._json_response(page_viewsource) for _ in request_bodies)

        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(side_effect=retry_source_requests)

        collection.get_page_sources()

        mock_site_no_http.amc_request.assert_not_called()
        request_bodies = mock_site_no_http.amc_request_with_retry.call_args.args[0]
        assert [body["page_id"] for body in request_bodies] == [222]
        assert mock_page_with_id._source is not None
        assert mock_page_with_id._source.wiki_text == "cached content"
        assert second_page._source is not None

    def test_acquire_sources_deduplicates_duplicate_page_ids(
        self, mock_site_no_http: Site, mock_page_with_id: Page, page_viewsource: dict[str, Any]
    ) -> None:
        """同じpage_idの未取得sourceは1回だけ取得し重複ページへ反映する"""
        duplicate_page = self._other_page(mock_site_no_http, mock_page_with_id)
        duplicate_page.id = mock_page_with_id.id
        collection = PageCollection(mock_site_no_http, [mock_page_with_id, duplicate_page])

        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(self._json_response(page_viewsource),))

        collection.get_page_sources()

        mock_site_no_http.amc_request.assert_not_called()
        request_bodies = mock_site_no_http.amc_request_with_retry.call_args.args[0]
        assert [body["page_id"] for body in request_bodies] == [mock_page_with_id.id]
        assert mock_page_with_id._source is not None
        assert duplicate_page._source is not None
        assert mock_page_with_id._source.wiki_text == duplicate_page._source.wiki_text

    def test_acquire_revisions_batches_missing_page_ids(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_site_no_http: Site,
        mock_page_no_http: Page,
        page_revisionlist: dict[str, Any],
    ) -> None:
        """ID未取得ページのrevision取得ではpage_id取得をまとめて行う"""
        second_page = self._other_page(mock_site_no_http, mock_page_no_http)
        collection = PageCollection(mock_site_no_http, [mock_page_no_http, second_page])
        request = self._patch_batched_page_id_request(monkeypatch)
        mock_site_no_http.amc_request_with_retry = MagicMock(
            return_value=tuple(self._json_response(page_revisionlist) for _ in collection)
        )

        collection.get_page_revisions()

        self._assert_batched_page_id_request(request)
        request_bodies = mock_site_no_http.amc_request_with_retry.call_args.args[0]
        assert [body["page_id"] for body in request_bodies] == [111, 222]

    def test_acquire_revisions_success(
        self, mock_site_no_http: Site, mock_page_with_id: Page, page_revisionlist: dict[str, Any]
    ) -> None:
        """リビジョン一覧を正常に取得できる"""
        collection = PageCollection(mock_site_no_http, [mock_page_with_id])

        mock_response = MagicMock()
        mock_response.json.return_value = page_revisionlist
        mock_site_no_http.amc_request = MagicMock(return_value=[mock_response])

        collection.get_page_revisions()
        assert mock_page_with_id._revisions is not None
        # フィクスチャには3つのリビジョン
        assert len(mock_page_with_id._revisions) == 3

    def test_acquire_revisions_skips_already_acquired_pages(
        self, mock_site_no_http: Site, mock_page_with_id: Page, page_revisionlist: dict[str, Any]
    ) -> None:
        """取得済みrevisionがあるページは再取得せず未取得ページだけ取得する"""
        second_page = self._other_page(mock_site_no_http, mock_page_with_id)
        second_page.id = 222
        cached_revisions = MagicMock()
        mock_page_with_id._revisions = cached_revisions
        collection = PageCollection(mock_site_no_http, [mock_page_with_id, second_page])

        def retry_revision_requests(request_bodies: list[dict[str, Any]]) -> tuple[MagicMock, ...]:
            return tuple(self._json_response(page_revisionlist) for _ in request_bodies)

        mock_site_no_http.amc_request_with_retry = MagicMock(side_effect=retry_revision_requests)

        collection.get_page_revisions()

        request_bodies = mock_site_no_http.amc_request_with_retry.call_args.args[0]
        assert [body["page_id"] for body in request_bodies] == [222]
        assert mock_page_with_id._revisions is cached_revisions
        assert second_page._revisions is not None

    def test_acquire_revisions_deduplicates_duplicate_page_ids(
        self, mock_site_no_http: Site, mock_page_with_id: Page, page_revisionlist: dict[str, Any]
    ) -> None:
        """同じpage_idの未取得revision一覧は1回だけ取得し重複ページへ反映する"""
        duplicate_page = self._other_page(mock_site_no_http, mock_page_with_id)
        duplicate_page.id = mock_page_with_id.id
        collection = PageCollection(mock_site_no_http, [mock_page_with_id, duplicate_page])

        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(self._json_response(page_revisionlist),))

        collection.get_page_revisions()

        mock_site_no_http.amc_request.assert_not_called()
        request_bodies = mock_site_no_http.amc_request_with_retry.call_args.args[0]
        assert [body["page_id"] for body in request_bodies] == [mock_page_with_id.id]
        assert mock_page_with_id._revisions is not None
        assert duplicate_page._revisions is not None
        assert len(mock_page_with_id._revisions) == len(duplicate_page._revisions)
        assert mock_page_with_id._revisions[0].page is mock_page_with_id
        assert duplicate_page._revisions[0].page is duplicate_page

    def test_acquire_revisions_missing_cells_raises(
        self,
        mock_site_no_http: Site,
        mock_page_with_id: Page,
    ) -> None:
        """履歴行の列が足りない場合はNoElementException"""
        collection = PageCollection(mock_site_no_http, [mock_page_with_id])

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": '<table class="page-history"><tr id="revision-row-1"><td>1.</td></tr></table>'
        }
        mock_site_no_http.amc_request = MagicMock(return_value=[mock_response])

        with pytest.raises(exceptions.NoElementException, match="revision cells"):
            collection.get_page_revisions()

    def test_acquire_votes_success(
        self, mock_site_no_http: Site, mock_page_with_id: Page, page_whorated: dict[str, Any]
    ) -> None:
        """投票情報を正常に取得できる"""
        collection = PageCollection(mock_site_no_http, [mock_page_with_id])

        mock_response = MagicMock()
        mock_response.json.return_value = page_whorated
        mock_site_no_http.amc_request = MagicMock(return_value=[mock_response])

        collection.get_page_votes()
        assert mock_page_with_id._votes is not None

    def test_acquire_votes_batches_missing_page_ids(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_site_no_http: Site,
        mock_page_no_http: Page,
        page_whorated: dict[str, Any],
    ) -> None:
        """ID未取得ページのvote取得ではpage_id取得をまとめて行う"""
        second_page = self._other_page(mock_site_no_http, mock_page_no_http)
        collection = PageCollection(mock_site_no_http, [mock_page_no_http, second_page])
        request = self._patch_batched_page_id_request(monkeypatch)
        mock_site_no_http.amc_request_with_retry = MagicMock(
            return_value=tuple(self._json_response(page_whorated) for _ in collection)
        )

        collection.get_page_votes()

        self._assert_batched_page_id_request(request)
        request_bodies = mock_site_no_http.amc_request_with_retry.call_args.args[0]
        assert [body["pageId"] for body in request_bodies] == [111, 222]

    def test_acquire_votes_skips_already_acquired_pages(
        self, mock_site_no_http: Site, mock_page_with_id: Page, page_whorated: dict[str, Any]
    ) -> None:
        """取得済みvoteがあるページは再取得せず未取得ページだけ取得する"""
        second_page = self._other_page(mock_site_no_http, mock_page_with_id)
        second_page.id = 222
        cached_votes = MagicMock()
        mock_page_with_id._votes = cached_votes
        collection = PageCollection(mock_site_no_http, [mock_page_with_id, second_page])

        def retry_vote_requests(request_bodies: list[dict[str, Any]]) -> tuple[MagicMock, ...]:
            return tuple(self._json_response(page_whorated) for _ in request_bodies)

        mock_site_no_http.amc_request_with_retry = MagicMock(side_effect=retry_vote_requests)

        collection.get_page_votes()

        request_bodies = mock_site_no_http.amc_request_with_retry.call_args.args[0]
        assert [body["pageId"] for body in request_bodies] == [222]
        assert mock_page_with_id._votes is cached_votes
        assert second_page._votes is not None

    def test_acquire_votes_deduplicates_duplicate_page_ids(
        self, mock_site_no_http: Site, mock_page_with_id: Page, page_whorated: dict[str, Any]
    ) -> None:
        """同じpage_idの未取得vote一覧は1回だけ取得し重複ページへ反映する"""
        duplicate_page = self._other_page(mock_site_no_http, mock_page_with_id)
        duplicate_page.id = mock_page_with_id.id
        collection = PageCollection(mock_site_no_http, [mock_page_with_id, duplicate_page])

        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(self._json_response(page_whorated),))

        collection.get_page_votes()

        mock_site_no_http.amc_request.assert_not_called()
        request_bodies = mock_site_no_http.amc_request_with_retry.call_args.args[0]
        assert [body["pageId"] for body in request_bodies] == [mock_page_with_id.id]
        assert mock_page_with_id._votes is not None
        assert duplicate_page._votes is not None
        assert len(mock_page_with_id._votes) == len(duplicate_page._votes)
        assert mock_page_with_id._votes[0].page is mock_page_with_id
        assert duplicate_page._votes[0].page is duplicate_page

    def test_acquire_files_batches_missing_page_ids(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_site_no_http: Site,
        mock_page_no_http: Page,
    ) -> None:
        """ID未取得ページのfile取得ではpage_id取得をまとめて行う"""
        second_page = self._other_page(mock_site_no_http, mock_page_no_http)
        collection = PageCollection(mock_site_no_http, [mock_page_no_http, second_page])
        request = self._patch_batched_page_id_request(monkeypatch)
        mock_site_no_http.amc_request_with_retry = MagicMock(
            return_value=tuple(self._json_response({"body": "<div>No files</div>"}) for _ in collection)
        )

        collection.get_page_files()

        self._assert_batched_page_id_request(request)
        request_bodies = mock_site_no_http.amc_request_with_retry.call_args.args[0]
        assert [body["page_id"] for body in request_bodies] == [111, 222]

    def test_acquire_files_skips_already_acquired_pages(self, mock_site_no_http: Site, mock_page_with_id: Page) -> None:
        """取得済みfileがあるページは再取得せず未取得ページだけ取得する"""
        second_page = self._other_page(mock_site_no_http, mock_page_with_id)
        second_page.id = 222
        cached_files = MagicMock()
        mock_page_with_id._files = cached_files
        collection = PageCollection(mock_site_no_http, [mock_page_with_id, second_page])

        def file_requests(request_bodies: list[dict[str, Any]]) -> tuple[MagicMock, ...]:
            return tuple(self._json_response({"body": "<div>No files</div>"}) for _ in request_bodies)

        mock_site_no_http.amc_request_with_retry = MagicMock(side_effect=file_requests)

        collection.get_page_files()

        request_bodies = mock_site_no_http.amc_request_with_retry.call_args.args[0]
        assert [body["page_id"] for body in request_bodies] == [222]
        assert mock_page_with_id._files is cached_files
        assert second_page._files is not None

    def test_acquire_files_skips_failed_retry_response(self, mock_site_no_http: Site, mock_page_with_id: Page) -> None:
        """file取得の一部失敗は成功ページを保持し失敗ページを未取得にする"""
        second_page = self._other_page(mock_site_no_http, mock_page_with_id)
        second_page.id = 222
        collection = PageCollection(mock_site_no_http, [mock_page_with_id, second_page])

        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(
            return_value=(self._json_response({"body": "<div>No files</div>"}), None)
        )

        collection.get_page_files()

        mock_site_no_http.amc_request.assert_not_called()
        mock_site_no_http.amc_request_with_retry.assert_called_once()
        assert mock_page_with_id._files is not None
        assert second_page._files is None

    def test_acquire_files_deduplicates_duplicate_page_ids(
        self, mock_site_no_http: Site, mock_page_with_id: Page
    ) -> None:
        """同じpage_idの未取得file一覧は1回だけ取得し重複ページへ反映する"""
        duplicate_page = self._other_page(mock_site_no_http, mock_page_with_id)
        duplicate_page.id = mock_page_with_id.id
        collection = PageCollection(mock_site_no_http, [mock_page_with_id, duplicate_page])
        body = {
            "body": """
                <table class="page-files">
                    <tbody>
                        <tr id="file-row-100">
                            <td><a href="/local--files/test-page/image.png">image.png</a></td>
                            <td><span title="image/png">PNG</span></td>
                            <td>1.5 kB</td>
                        </tr>
                    </tbody>
                </table>
            """
        }

        mock_site_no_http.amc_request = MagicMock()
        mock_site_no_http.amc_request_with_retry = MagicMock(return_value=(self._json_response(body),))

        collection.get_page_files()

        mock_site_no_http.amc_request.assert_not_called()
        request_bodies = mock_site_no_http.amc_request_with_retry.call_args.args[0]
        assert [body["page_id"] for body in request_bodies] == [mock_page_with_id.id]
        assert mock_page_with_id._files is not None
        assert duplicate_page._files is not None
        assert len(mock_page_with_id._files) == len(duplicate_page._files) == 1
        assert mock_page_with_id._files[0].page is mock_page_with_id
        assert duplicate_page._files[0].page is duplicate_page


# ============================================================
# Pageテスト
# ============================================================


class TestPageProperties:
    """Pageのプロパティテスト"""

    def test_get_url(self, mock_page_no_http: Page) -> None:
        """URLが正しく生成される"""
        url = mock_page_no_http.get_url()
        assert url == "https://test-site.wikidot.com/test-page"

    def test_id_property_acquired(self, mock_page_with_id: Page) -> None:
        """取得済みIDが返される"""
        assert mock_page_with_id.id == 12345

    def test_source_property_auto_acquire(self, mock_page_with_id: Page, page_viewsource: dict[str, Any]) -> None:
        """ソースが未取得の場合自動取得する"""
        mock_response = MagicMock()
        mock_response.json.return_value = page_viewsource
        mock_page_with_id.site.amc_request = MagicMock(return_value=[mock_response])

        source = mock_page_with_id.source
        assert "page content" in source.wiki_text

    def test_refresh_source_forces_remote_source_fetch(
        self, mock_page_with_id: Page, page_viewsource: dict[str, Any]
    ) -> None:
        """キャッシュ済みsourceがあっても明示的に再取得できる"""
        mock_page_with_id._source = PageSource(mock_page_with_id, "cached source")
        mock_response = MagicMock()
        mock_response.json.return_value = page_viewsource
        mock_page_with_id.site.amc_request = MagicMock()
        mock_page_with_id.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        source = mock_page_with_id.refresh_source()

        mock_page_with_id.site.amc_request.assert_not_called()
        mock_page_with_id.site.amc_request_with_retry.assert_called_once_with(
            [{"moduleName": "viewsource/ViewSourceModule", "page_id": 12345}]
        )
        assert source == mock_page_with_id.source
        assert "page content" in source.wiki_text

    def test_revisions_property(self, mock_page_with_id: Page, page_revisionlist: dict[str, Any]) -> None:
        """リビジョンプロパティが正しく動作する"""
        mock_response = MagicMock()
        mock_response.json.return_value = page_revisionlist
        mock_page_with_id.site.amc_request = MagicMock()
        mock_page_with_id.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        revisions = mock_page_with_id.revisions

        mock_page_with_id.site.amc_request.assert_not_called()
        mock_page_with_id.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "moduleName": "history/PageRevisionListModule",
                    "page_id": 12345,
                    "options": {"all": True},
                    "perpage": 100000000,
                }
            ]
        )
        assert len(revisions) == 3

    def test_revisions_property_raises_when_retry_is_exhausted(self, mock_page_with_id: Page) -> None:
        """リビジョン取得リトライが尽きた場合は空履歴に見せかけない"""
        mock_page_with_id.site.amc_request = MagicMock()
        mock_page_with_id.site.amc_request_with_retry = MagicMock(return_value=(None,))

        with pytest.raises(exceptions.NotFoundException, match="Cannot find page revisions"):
            _ = mock_page_with_id.revisions

        mock_page_with_id.site.amc_request.assert_not_called()
        mock_page_with_id.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "moduleName": "history/PageRevisionListModule",
                    "page_id": 12345,
                    "options": {"all": True},
                    "perpage": 100000000,
                }
            ]
        )
        assert mock_page_with_id._revisions is None

    def test_latest_revision(self, mock_page_with_id: Page, page_revisionlist: dict[str, Any]) -> None:
        """最新リビジョンを取得できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = page_revisionlist
        mock_page_with_id.site.amc_request = MagicMock(return_value=[mock_response])
        mock_page_with_id.revisions_count = 3

        latest = mock_page_with_id.latest_revision
        assert latest.rev_no == 3

    def test_latest_revision_not_found(self, mock_page_with_id: Page) -> None:
        """最新リビジョンが見つからない場合に例外"""
        from wikidot.module.page import PageRevision, PageRevisionCollection

        # revisions_countと一致しないrev_noのリビジョンを設定
        mock_page_with_id.revisions_count = 5
        mock_page_with_id._revisions = PageRevisionCollection(
            mock_page_with_id,
            [
                PageRevision(
                    page=mock_page_with_id,
                    id=100,
                    rev_no=1,
                    created_by=None,
                    created_at=None,
                    comment="",
                )
            ],
        )

        with pytest.raises(exceptions.NotFoundException):
            _ = mock_page_with_id.latest_revision

    def test_discussion_retries_transient_fetch_failures(
        self, monkeypatch: pytest.MonkeyPatch, mock_page_with_id: Page
    ) -> None:
        """ページコメントスレッドID取得の一時失敗はretryする"""
        from wikidot.module.forum_thread import ForumThread

        mock_response = MagicMock()
        mock_response.json.return_value = {"body": "WIKIDOT.forumThreadId = 3001;"}
        mock_page_with_id.site.amc_request = MagicMock(
            side_effect=[
                (RuntimeError("temporary failure"),),
                (mock_response,),
            ]
        )
        fetched_thread = MagicMock()
        get_from_id = MagicMock(return_value=fetched_thread)
        monkeypatch.setattr(ForumThread, "get_from_id", get_from_id)

        discussion = mock_page_with_id.discussion

        assert discussion is fetched_thread
        assert mock_page_with_id.site.amc_request.call_count == 2
        get_from_id.assert_called_once_with(mock_page_with_id.site, 3001)

    def test_discussion_raises_when_retry_is_exhausted(self, mock_page_with_id: Page) -> None:
        """コメントスレッドID取得リトライが尽きた場合は未確認扱いのまま明示的に失敗する"""
        mock_page_with_id.site.client.amc_client.config.retry_max_retries = 1
        mock_page_with_id.site.amc_request = MagicMock(return_value=(RuntimeError("temporary failure"),))

        with pytest.raises(exceptions.UnexpectedException, match="Cannot retrieve page discussion: test-page"):
            _ = mock_page_with_id.discussion

        assert mock_page_with_id.site.amc_request.call_count == 2
        assert mock_page_with_id._discussion_checked is False

    def test_files_property_auto_acquire_empty_response(self, mock_page_with_id: Page) -> None:
        """ファイルなしの正常レスポンスは空のコレクションとして扱う"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": "<div>No files</div>"}
        mock_page_with_id.site.amc_request = MagicMock()
        mock_page_with_id.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        files = mock_page_with_id.files

        mock_page_with_id.site.amc_request.assert_not_called()
        mock_page_with_id.site.amc_request_with_retry.assert_called_once_with(
            [{"moduleName": "files/PageFilesModule", "page_id": 12345}]
        )
        assert files is mock_page_with_id._files
        assert files.page is mock_page_with_id
        assert len(files) == 0

    def test_files_property_raises_when_retry_is_exhausted(self, mock_page_with_id: Page) -> None:
        """ファイル取得リトライが尽きた場合は空リストに見せかけない"""
        mock_page_with_id.site.amc_request = MagicMock()
        mock_page_with_id.site.amc_request_with_retry = MagicMock(return_value=(None,))

        with pytest.raises(exceptions.NotFoundException, match="Cannot find page files"):
            _ = mock_page_with_id.files

        mock_page_with_id.site.amc_request.assert_not_called()
        mock_page_with_id.site.amc_request_with_retry.assert_called_once_with(
            [{"moduleName": "files/PageFilesModule", "page_id": 12345}]
        )
        assert mock_page_with_id._files is None


class TestPageWriteMethods:
    """Pageの書き込み系メソッドテスト"""

    def test_destroy_success(self, mock_page_with_id: Page, page_delete_success: dict[str, Any]) -> None:
        """ページを正常に削除できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = page_delete_success
        mock_page_with_id.site.amc_request = MagicMock(return_value=[mock_response])
        mock_page_with_id.site.client.is_logged_in = True
        mock_page_with_id.site.client.login_check = MagicMock()

        # 例外が発生しなければOK
        mock_page_with_id.destroy()
        mock_page_with_id.site.amc_request.assert_called_once()

    def test_destroy_not_logged_in(self, mock_page_with_id: Page) -> None:
        """ログインしていない場合に例外"""
        mock_page_with_id.site.client.is_logged_in = False
        mock_page_with_id.site.client.login_check = MagicMock(
            side_effect=exceptions.LoginRequiredException("Login required")
        )

        with pytest.raises(exceptions.LoginRequiredException):
            mock_page_with_id.destroy()

    def test_commit_tags_success(self, mock_page_with_id: Page, page_savetags_success: dict[str, Any]) -> None:
        """タグを正常に保存できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = page_savetags_success
        mock_page_with_id.site.amc_request = MagicMock(return_value=[mock_response])
        mock_page_with_id.site.client.is_logged_in = True
        mock_page_with_id.site.client.login_check = MagicMock()

        result = mock_page_with_id.commit_tags()
        assert result == mock_page_with_id

    def test_commit_tags_not_logged_in(self, mock_page_with_id: Page) -> None:
        """ログインしていない場合に例外"""
        mock_page_with_id.site.client.is_logged_in = False
        mock_page_with_id.site.client.login_check = MagicMock(
            side_effect=exceptions.LoginRequiredException("Login required")
        )

        with pytest.raises(exceptions.LoginRequiredException):
            mock_page_with_id.commit_tags()

    def test_set_parent_success(self, mock_page_with_id: Page, page_setparent_success: dict[str, Any]) -> None:
        """親ページを正常に設定できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = page_setparent_success
        mock_page_with_id.site.amc_request = MagicMock(return_value=[mock_response])
        mock_page_with_id.site.client.is_logged_in = True
        mock_page_with_id.site.client.login_check = MagicMock()

        result = mock_page_with_id.set_parent("parent-page")
        assert result.parent_fullname == "parent-page"

    def test_set_parent_clear(self, mock_page_with_id: Page, page_setparent_success: dict[str, Any]) -> None:
        """親ページをクリアできる"""
        mock_response = MagicMock()
        mock_response.json.return_value = page_setparent_success
        mock_page_with_id.site.amc_request = MagicMock(return_value=[mock_response])
        mock_page_with_id.site.client.is_logged_in = True
        mock_page_with_id.site.client.login_check = MagicMock()

        result = mock_page_with_id.set_parent(None)
        assert result.parent_fullname is None

    def test_rename_success(self, mock_page_with_id: Page, page_rename_success: dict[str, Any]) -> None:
        """ページ名を正常に変更できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = page_rename_success
        mock_page_with_id.site.amc_request = MagicMock(return_value=[mock_response])
        mock_page_with_id.site.client.is_logged_in = True
        mock_page_with_id.site.client.login_check = MagicMock()

        result = mock_page_with_id.rename("new-page-name")
        assert result.fullname == "new-page-name"
        assert result.name == "new-page-name"
        assert result.category == "_default"

    def test_rename_with_category(self, mock_page_with_id: Page, page_rename_success: dict[str, Any]) -> None:
        """カテゴリ付きでページ名を変更できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = page_rename_success
        mock_page_with_id.site.amc_request = MagicMock(return_value=[mock_response])
        mock_page_with_id.site.client.is_logged_in = True
        mock_page_with_id.site.client.login_check = MagicMock()

        result = mock_page_with_id.rename("component:new-name")
        assert result.fullname == "component:new-name"
        assert result.name == "new-name"
        assert result.category == "component"

    def test_vote_positive(self, mock_page_with_id: Page, page_ratepage_success: dict[str, Any]) -> None:
        """正の投票ができる"""
        mock_response = MagicMock()
        mock_response.json.return_value = page_ratepage_success
        mock_page_with_id.site.amc_request = MagicMock(return_value=[mock_response])
        mock_page_with_id.site.client.is_logged_in = True
        mock_page_with_id.site.client.login_check = MagicMock()

        new_rating = mock_page_with_id.vote(1)
        assert new_rating == 11
        assert mock_page_with_id.rating == 11

    def test_vote_negative(self, mock_page_with_id: Page) -> None:
        """負の投票ができる"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "type": "P", "points": 9}
        mock_page_with_id.site.amc_request = MagicMock(return_value=[mock_response])
        mock_page_with_id.site.client.is_logged_in = True
        mock_page_with_id.site.client.login_check = MagicMock()

        new_rating = mock_page_with_id.vote(-1)
        assert new_rating == 9

    def test_vote_invalid_value_raises(self, mock_page_with_id: Page) -> None:
        """1/-1以外の投票値は送信前に拒否する"""
        mock_page_with_id.site.amc_request = MagicMock()

        with pytest.raises(ValueError, match="Vote value must be 1 or -1"):
            mock_page_with_id.vote(0)

        mock_page_with_id.site.amc_request.assert_not_called()

    def test_vote_not_logged_in(self, mock_page_with_id: Page) -> None:
        """ログインしていない場合に例外"""
        mock_page_with_id.site.client.is_logged_in = False
        mock_page_with_id.site.client.login_check = MagicMock(
            side_effect=exceptions.LoginRequiredException("Login required")
        )

        with pytest.raises(exceptions.LoginRequiredException):
            mock_page_with_id.vote(1)

    def test_cancel_vote_success(self, mock_page_with_id: Page, page_cancelvote_success: dict[str, Any]) -> None:
        """投票キャンセルができる"""
        mock_response = MagicMock()
        mock_response.json.return_value = page_cancelvote_success
        mock_page_with_id.site.amc_request = MagicMock(return_value=[mock_response])
        mock_page_with_id.site.client.is_logged_in = True
        mock_page_with_id.site.client.login_check = MagicMock()

        new_rating = mock_page_with_id.cancel_vote()
        assert new_rating == 10
        assert mock_page_with_id.rating == 10

    def test_metas_getter_parses_decoded_flexible_markup(self, mock_page_with_id: Page) -> None:
        """metaタグ取得はHTMLエンティティと属性順の揺れを扱える"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": (
                '&lt;meta content="Tom &amp;amp; Jerry" name="description"/&gt;'
                '&lt;meta name="empty" content=""/&gt;'
                '&lt;meta name="quoted" content="a &quot;quote&quot;"/&gt;'
                '<meta name="literal" content="literal &amp; value"/>'
            )
        }
        mock_page_with_id._metas = None
        mock_page_with_id.site.amc_request = MagicMock()
        mock_page_with_id.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        metas = mock_page_with_id.metas

        assert metas == {
            "description": "Tom & Jerry",
            "empty": "",
            "quoted": 'a "quote"',
            "literal": "literal & value",
        }
        mock_page_with_id.site.amc_request.assert_not_called()
        mock_page_with_id.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "pageId": 12345,
                    "moduleName": "edit/EditMetaModule",
                }
            ]
        )

    def test_metas_getter_retries_transient_fetch_failures(self, mock_page_with_id: Page) -> None:
        """metaタグ取得の一時失敗はretryする"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": '&lt;meta name="description" content="retry ok"/&gt;'}
        mock_page_with_id._metas = None
        mock_page_with_id.site.amc_request = MagicMock(
            side_effect=[
                (RuntimeError("temporary failure"),),
                (mock_response,),
            ]
        )

        metas = mock_page_with_id.metas

        assert metas == {"description": "retry ok"}
        assert mock_page_with_id.site.amc_request.call_count == 2

    def test_metas_getter_raises_when_retry_is_exhausted(self, mock_page_with_id: Page) -> None:
        """metaタグ取得リトライが尽きた場合は未取得扱いのまま明示的に失敗する"""
        mock_page_with_id._metas = None
        mock_page_with_id.site.client.amc_client.config.retry_max_retries = 1
        mock_page_with_id.site.amc_request = MagicMock(return_value=(RuntimeError("temporary failure"),))

        with pytest.raises(exceptions.UnexpectedException, match="Cannot retrieve page metas: test-page"):
            _ = mock_page_with_id.metas

        assert mock_page_with_id.site.amc_request.call_count == 2
        assert mock_page_with_id._metas is None

    def test_metas_setter_batches_changes(self, mock_page_with_id: Page) -> None:
        """metaタグの削除・追加・更新は1つのAMCバッチで送信する"""
        mock_page_with_id._metas = {
            "remove": "old",
            "keep": "same",
            "change": "old",
        }
        mock_page_with_id.site.client.login_check = MagicMock()
        mock_page_with_id.site.amc_request = MagicMock()

        mock_page_with_id.metas = {
            "keep": "same",
            "add": "new",
            "change": "new",
        }

        mock_page_with_id.site.amc_request.assert_called_once()
        mock_page_with_id.site.client.login_check.assert_called_once()
        request_bodies = mock_page_with_id.site.amc_request.call_args.args[0]
        assert request_bodies == [
            {
                "metaName": "remove",
                "action": "WikiPageAction",
                "event": "deleteMetaTag",
                "pageId": 12345,
                "moduleName": "edit/EditMetaModule",
            },
            {
                "metaName": "add",
                "metaContent": "new",
                "action": "WikiPageAction",
                "event": "saveMetaTag",
                "pageId": 12345,
                "moduleName": "edit/EditMetaModule",
            },
            {
                "metaName": "change",
                "metaContent": "new",
                "action": "WikiPageAction",
                "event": "saveMetaTag",
                "pageId": 12345,
                "moduleName": "edit/EditMetaModule",
            },
        ]
        assert mock_page_with_id._metas == {"keep": "same", "add": "new", "change": "new"}

    def test_set_metadata_batches_tags_parent_and_metas(self, mock_page_with_id: Page) -> None:
        """タグ・親・metaタグ更新を1つのAMCバッチで送信する"""
        mock_page_with_id.tags = ["old-tag"]
        mock_page_with_id.parent_fullname = "old-parent"
        mock_page_with_id._metas = {
            "remove": "old",
            "keep": "same",
            "change": "old",
        }
        mock_page_with_id.site.client.login_check = MagicMock()
        mock_page_with_id.site.amc_request = MagicMock()

        result = mock_page_with_id.set_metadata(
            tags=["tag-one", "tag-two"],
            parent_fullname="new-parent",
            metas={
                "keep": "same",
                "add": "new",
                "change": "new",
            },
        )

        assert result == mock_page_with_id
        mock_page_with_id.site.client.login_check.assert_called_once()
        mock_page_with_id.site.amc_request.assert_called_once()
        request_bodies = mock_page_with_id.site.amc_request.call_args.args[0]
        assert request_bodies == [
            {
                "tags": "tag-one tag-two",
                "action": "WikiPageAction",
                "event": "saveTags",
                "pageId": 12345,
                "moduleName": "Empty",
            },
            {
                "action": "WikiPageAction",
                "event": "setParentPage",
                "moduleName": "Empty",
                "pageId": "12345",
                "parentName": "new-parent",
            },
            {
                "metaName": "remove",
                "action": "WikiPageAction",
                "event": "deleteMetaTag",
                "pageId": 12345,
                "moduleName": "edit/EditMetaModule",
            },
            {
                "metaName": "add",
                "metaContent": "new",
                "action": "WikiPageAction",
                "event": "saveMetaTag",
                "pageId": 12345,
                "moduleName": "edit/EditMetaModule",
            },
            {
                "metaName": "change",
                "metaContent": "new",
                "action": "WikiPageAction",
                "event": "saveMetaTag",
                "pageId": 12345,
                "moduleName": "edit/EditMetaModule",
            },
        ]
        assert mock_page_with_id.tags == ["tag-one", "tag-two"]
        assert mock_page_with_id.parent_fullname == "new-parent"
        assert mock_page_with_id._metas == {"keep": "same", "add": "new", "change": "new"}

    def test_set_metadata_can_clear_parent(self, mock_page_with_id: Page) -> None:
        """parent_fullname=Noneを明示すると親ページをクリアする"""
        mock_page_with_id.parent_fullname = "old-parent"
        mock_page_with_id.site.client.login_check = MagicMock()
        mock_page_with_id.site.amc_request = MagicMock()

        mock_page_with_id.set_metadata(parent_fullname=None)

        mock_page_with_id.site.amc_request.assert_called_once_with(
            [
                {
                    "action": "WikiPageAction",
                    "event": "setParentPage",
                    "moduleName": "Empty",
                    "pageId": "12345",
                    "parentName": "",
                }
            ]
        )
        assert mock_page_with_id.parent_fullname is None


class TestPageCreateOrEdit:
    """Page.create_or_editのテスト"""

    def test_create_new_page(
        self,
        mock_site_no_http: Site,
        page_pageedit_success: dict[str, Any],
        page_savepage_success: dict[str, Any],
        page_listpages_single: dict[str, Any],
    ) -> None:
        """新規ページを作成できる"""
        mock_site_no_http.client.is_logged_in = True
        mock_site_no_http.client.login_check = MagicMock()

        # ページロック取得 → 保存 → 検索 の順
        mock_lock_response = MagicMock()
        mock_lock_response.json.return_value = page_pageedit_success

        mock_save_response = MagicMock()
        mock_save_response.json.return_value = page_savepage_success

        mock_search_response = MagicMock()
        mock_search_response.json.return_value = page_listpages_single

        mock_site_no_http.amc_request = MagicMock(
            side_effect=[
                [mock_lock_response],
                [mock_save_response],
                [mock_search_response],
            ]
        )

        page = Page.create_or_edit(
            mock_site_no_http,
            "new-page",
            title="New Page Title",
            source="Page content",
        )
        assert page.fullname == "scp-001"
        assert page.title == "New Page Title"
        assert page.source.wiki_text == "Page content"

    def test_create_new_page_returns_saved_page_when_search_is_stale(
        self,
        mock_site_no_http: Site,
        page_pageedit_success: dict[str, Any],
        page_savepage_success: dict[str, Any],
        page_listpages_empty: dict[str, Any],
    ) -> None:
        """保存直後のListPagesに新規ページがまだ出なくても作成結果を返す"""
        mock_site_no_http.client.is_logged_in = True
        mock_site_no_http.client.login_check = MagicMock()

        mock_lock_response = MagicMock()
        mock_lock_response.json.return_value = page_pageedit_success

        mock_save_response = MagicMock()
        mock_save_response.json.return_value = page_savepage_success

        mock_search_response = MagicMock()
        mock_search_response.json.return_value = page_listpages_empty

        mock_site_no_http.amc_request = MagicMock(
            side_effect=[
                [mock_lock_response],
                [mock_save_response],
                [mock_search_response],
                [mock_search_response],
            ]
        )

        page = Page.create_or_edit(
            mock_site_no_http,
            "new-page",
            title="New Page Title",
            source="Page content",
        )

        assert page.fullname == "new-page"
        assert page.title == "New Page Title"
        assert page.source.wiki_text == "Page content"

    def test_edit_existing_page_stale_search_preserves_page_id(
        self,
        mock_site_no_http: Site,
        page_pageedit_existing: dict[str, Any],
        page_savepage_success: dict[str, Any],
        page_listpages_empty: dict[str, Any],
    ) -> None:
        """既存ページ編集後の検索が古くても既知のpage_idを保持する"""
        mock_site_no_http.client.is_logged_in = True
        mock_site_no_http.client.login_check = MagicMock()

        mock_lock_response = MagicMock()
        mock_lock_response.json.return_value = page_pageedit_existing

        mock_save_response = MagicMock()
        mock_save_response.json.return_value = page_savepage_success

        mock_search_response = MagicMock()
        mock_search_response.json.return_value = page_listpages_empty

        mock_site_no_http.amc_request = MagicMock(
            side_effect=[
                [mock_lock_response],
                [mock_save_response],
                [mock_search_response],
                [mock_search_response],
            ]
        )

        page = Page.create_or_edit(
            mock_site_no_http,
            "existing-page",
            page_id=12345,
            title="Updated Title",
            source="Updated content",
        )

        assert page.fullname == "existing-page"
        assert page._id == 12345
        assert page.source.wiki_text == "Updated content"

    def test_edit_locked_page(self, mock_site_no_http: Site, page_pageedit_locked: dict[str, Any]) -> None:
        """ロック済みページの編集で例外"""
        mock_site_no_http.client.is_logged_in = True
        mock_site_no_http.client.login_check = MagicMock()

        mock_response = MagicMock()
        mock_response.json.return_value = page_pageedit_locked
        mock_site_no_http.amc_request = MagicMock(return_value=[mock_response])

        with pytest.raises(exceptions.TargetErrorException):
            Page.create_or_edit(mock_site_no_http, "locked-page")

    def test_edit_without_page_id(self, mock_site_no_http: Site) -> None:
        """既存ページ編集時にpage_idがないと例外"""
        mock_site_no_http.client.is_logged_in = True
        mock_site_no_http.client.login_check = MagicMock()

        # page_revision_idがある = 既存ページ
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "lock_id": "abc",
            "lock_secret": "xyz",
            "page_revision_id": 100,  # 既存ページ
        }
        mock_site_no_http.amc_request = MagicMock(return_value=[mock_response])

        with pytest.raises(ValueError, match="page_id must be specified"):
            Page.create_or_edit(mock_site_no_http, "existing-page")

    def test_edit_raise_on_exists(self, mock_site_no_http: Site) -> None:
        """raise_on_exists=Trueで既存ページの場合に例外"""
        mock_site_no_http.client.is_logged_in = True
        mock_site_no_http.client.login_check = MagicMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "lock_id": "abc",
            "lock_secret": "xyz",
            "page_revision_id": 100,
        }
        mock_site_no_http.amc_request = MagicMock(return_value=[mock_response])

        with pytest.raises(exceptions.TargetExistsException):
            Page.create_or_edit(mock_site_no_http, "existing-page", raise_on_exists=True)

    def test_edit_not_logged_in(self, mock_site_no_http: Site) -> None:
        """ログインしていない場合に例外"""
        mock_site_no_http.client.is_logged_in = False
        mock_site_no_http.client.login_check = MagicMock(
            side_effect=exceptions.LoginRequiredException("Login required")
        )

        with pytest.raises(exceptions.LoginRequiredException):
            Page.create_or_edit(mock_site_no_http, "new-page")


class TestPageEdit:
    """Page.editのテスト"""

    def test_edit_existing_page(
        self,
        mock_page_with_id: Page,
        page_pageedit_existing: dict[str, Any],
        page_savepage_success: dict[str, Any],
        page_listpages_single: dict[str, Any],
        page_viewsource: dict[str, Any],
    ) -> None:
        """既存ページを編集できる"""
        mock_page_with_id.site.client.is_logged_in = True
        mock_page_with_id.site.client.login_check = MagicMock()

        # source取得用
        mock_source_response = MagicMock()
        mock_source_response.json.return_value = page_viewsource

        # ページロック取得
        mock_lock_response = MagicMock()
        mock_lock_response.json.return_value = page_pageedit_existing

        # 保存
        mock_save_response = MagicMock()
        mock_save_response.json.return_value = page_savepage_success

        # 検索
        mock_search_response = MagicMock()
        mock_search_response.json.return_value = page_listpages_single

        mock_page_with_id.site.amc_request = MagicMock(
            side_effect=[
                [mock_source_response],  # source取得
                [mock_lock_response],  # ロック取得
                [mock_save_response],  # 保存
                [mock_search_response],  # 検索
            ]
        )

        page = mock_page_with_id.edit(title="Updated Title")
        assert page is not None
        assert page.title == "Updated Title"
        assert "page content" in page.source.wiki_text

    def test_edit_force_unlock(
        self,
        mock_page_with_id: Page,
        page_pageedit_existing: dict[str, Any],
        page_savepage_success: dict[str, Any],
        page_listpages_single: dict[str, Any],
    ) -> None:
        """強制アンロックして編集できる"""
        mock_page_with_id.site.client.is_logged_in = True
        mock_page_with_id.site.client.login_check = MagicMock()

        # sourceを直接渡すのでsource取得は不要
        mock_lock_response = MagicMock()
        mock_lock_response.json.return_value = page_pageedit_existing

        mock_save_response = MagicMock()
        mock_save_response.json.return_value = page_savepage_success

        mock_search_response = MagicMock()
        mock_search_response.json.return_value = page_listpages_single

        mock_page_with_id.site.amc_request = MagicMock(
            side_effect=[
                [mock_lock_response],  # ロック取得
                [mock_save_response],  # 保存
                [mock_search_response],  # 検索
            ]
        )

        mock_page_with_id.edit(source="New source", force_edit=True)

        # force_lock=yesが含まれていることを確認
        call_args_list = mock_page_with_id.site.amc_request.call_args_list
        lock_call = call_args_list[0]  # 1回目がロック取得
        assert lock_call[0][0][0].get("force_lock") == "yes"

    def test_edit_allows_empty_source(
        self,
        mock_page_with_id: Page,
        page_pageedit_existing: dict[str, Any],
        page_savepage_success: dict[str, Any],
        page_listpages_single: dict[str, Any],
    ) -> None:
        """空文字sourceを現在sourceで上書きしない"""
        mock_page_with_id.site.client.is_logged_in = True
        mock_page_with_id.site.client.login_check = MagicMock()

        mock_lock_response = MagicMock()
        mock_lock_response.json.return_value = page_pageedit_existing

        mock_save_response = MagicMock()
        mock_save_response.json.return_value = page_savepage_success

        mock_search_response = MagicMock()
        mock_search_response.json.return_value = page_listpages_single

        mock_page_with_id.site.amc_request = MagicMock(
            side_effect=[
                [mock_lock_response],
                [mock_save_response],
                [mock_search_response],
            ]
        )

        mock_page_with_id.edit(source="")

        call_args_list = mock_page_with_id.site.amc_request.call_args_list
        save_body = call_args_list[1][0][0][0]
        assert save_body["source"] == ""
