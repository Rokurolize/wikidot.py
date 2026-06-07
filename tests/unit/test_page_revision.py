"""
ページリビジョンモジュールのユニットテスト

PageRevision, PageRevisionCollectionクラスをテストする。
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from wikidot.common.exceptions import NoElementException, UnexpectedException
from wikidot.module.page import Page
from wikidot.module.page_revision import PageRevision, PageRevisionCollection
from wikidot.module.page_source import PageSource
from wikidot.module.user import User


@pytest.fixture
def mock_page(mock_page_no_http):
    """HTTPなしで使う実Page"""
    page = mock_page_no_http
    page.site.amc_request = MagicMock()
    page.site.amc_request_with_retry = MagicMock()
    return page


@pytest.fixture
def mock_user(mock_page):
    """モックユーザー"""
    return User(
        client=mock_page.site.client,
        id=12345,
        name="test-user",
        unix_name="test-user",
        avatar_url="http://example.com/avatar.png",
    )


@pytest.fixture
def sample_revision(mock_page, mock_user):
    """サンプルリビジョン"""
    return PageRevision(
        page=mock_page,
        id=100,
        rev_no=1,
        created_by=mock_user,
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        comment="Initial revision",
    )


def _page_on_same_site(page: Page, fullname: str = "other-page") -> Page:
    return Page(
        site=page.site,
        fullname=fullname,
        name=fullname,
        category="_default",
        title="Other Page",
        children_count=0,
        comments_count=0,
        size=1000,
        rating=10,
        votes_count=5,
        rating_percent=None,
        revisions_count=3,
        parent_fullname=None,
        tags=["tag1", "tag2"],
        created_by=None,
        created_at=None,
        updated_by=None,
        updated_at=None,
        commented_by=None,
        commented_at=None,
    )


class TestPageRevisionCollection:
    """PageRevisionCollectionクラスのテスト"""

    def test_init_empty(self):
        """空のコレクションの初期化"""
        collection = PageRevisionCollection()
        assert len(collection) == 0
        assert collection.page is None

    def test_init_with_page(self, mock_page, sample_revision):
        """ページを指定した初期化"""
        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision])
        assert len(collection) == 1
        assert collection.page == mock_page

    def test_init_with_page_and_empty_revisions(self, mock_page):
        """空のリビジョンリストでも指定したページを保持する"""
        collection = PageRevisionCollection(page=mock_page, revisions=[])
        assert len(collection) == 0
        assert collection.page == mock_page

    @pytest.mark.parametrize("page", [True, "test-page", {"fullname": "test-page"}, object()])
    def test_init_rejects_malformed_pages(self, page: object) -> None:
        """明示されたpageはPageだけ受け付ける"""
        bad_page: Any = page

        with pytest.raises(ValueError, match="page must be a Page"):
            PageRevisionCollection(page=bad_page, revisions=[])

    @pytest.mark.parametrize("revisions", [True, False, "100", ("100",), 100])
    def test_init_rejects_non_list_revisions(self, mock_page, revisions: object) -> None:
        """リビジョンコレクションの初期化はlistまたはNoneだけ受け付ける"""
        bad_revisions: Any = revisions

        with pytest.raises(ValueError, match="revisions must be a list or None"):
            PageRevisionCollection(page=mock_page, revisions=bad_revisions)

    @pytest.mark.parametrize("revision", [None, True, "100", {"id": 100}])
    def test_init_rejects_non_revision_entries(self, mock_page, revision: object) -> None:
        """リビジョンコレクションの初期化はPageRevision要素だけ受け付ける"""
        bad_revisions: Any = [revision]

        with pytest.raises(ValueError, match="revisions list entries must be PageRevision"):
            PageRevisionCollection(page=mock_page, revisions=bad_revisions)

    def test_init_infers_page_from_revision(self, sample_revision):
        """リビジョンからページを推測"""
        collection = PageRevisionCollection(revisions=[sample_revision])
        assert collection.page == sample_revision.page

    def test_iter(self, sample_revision):
        """イテレータのテスト"""
        collection = PageRevisionCollection(revisions=[sample_revision])
        revisions = list(collection)
        assert len(revisions) == 1
        assert revisions[0] == sample_revision

    def test_find_existing(self, sample_revision):
        """存在するリビジョンの検索"""
        collection = PageRevisionCollection(revisions=[sample_revision])
        result = collection.find(100)
        assert result == sample_revision

    def test_find_not_existing(self, sample_revision):
        """存在しないリビジョンの検索"""
        collection = PageRevisionCollection(revisions=[sample_revision])
        result = collection.find(999)
        assert result is None

    @pytest.mark.parametrize("revision_id", [None, True, "100", 100.0])
    def test_find_rejects_non_integer_ids(self, sample_revision, revision_id):
        """findは整数以外の検索IDを拒否する"""
        collection = PageRevisionCollection(revisions=[sample_revision])

        with pytest.raises(ValueError, match="id must be an integer"):
            collection.find(revision_id)

    def test_get_sources_requires_page(self):
        """get_sourcesはpageが必要"""
        collection = PageRevisionCollection()
        with pytest.raises(ValueError) as exc_info:
            collection.get_sources()
        assert "Page is not set" in str(exc_info.value)

    @pytest.mark.parametrize("bad_revision", [None, True, "100"])
    def test_get_sources_rejects_non_revision_entries_before_fetch(self, mock_page, sample_revision, bad_revision):
        """get_sourcesはPageRevision以外の要素を送信前に拒否する"""
        bad_revision_entry: Any = bad_revision
        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision])
        collection.append(bad_revision_entry)

        with pytest.raises(ValueError, match="revisions list entries must be PageRevision"):
            collection.get_sources()

        mock_page.site.amc_request.assert_not_called()
        mock_page.site.amc_request_with_retry.assert_not_called()

    def test_get_sources_success(self, mock_page, sample_revision):
        """get_sourcesの成功ケース"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": '<div class="page-source">Test wiki text</div>'}
        mock_page.site.amc_request_with_retry.return_value = [mock_response]

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision])
        result = collection.get_sources()

        assert result == collection
        assert sample_revision._source is not None
        assert sample_revision._source.wiki_text == "Test wiki text"

    def test_get_sources_preserves_multiline_source_text(self, mock_page, sample_revision):
        """ViewSourceModuleの折り返しタブを複数行で正しく除去する"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": '<div class="page-source">\n\t+ Source from revision\n\t\n\tFoundation line.\n</div>'
        }
        mock_page.site.amc_request_with_retry.return_value = [mock_response]

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision])
        collection.get_sources()

        assert sample_revision._source is not None
        assert sample_revision._source.wiki_text == "+ Source from revision\n\nFoundation line."

    def test_get_sources_missing_wiki_text_includes_site_page_and_revision_context(self, mock_page, sample_revision):
        """source解析失敗はsite、対象ページ、リビジョンIDを含める"""
        mock_page.site.unix_name = "test-site"
        mock_page.fullname = "test-page"
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": "<div>missing source wrapper</div>"}
        mock_page.site.amc_request_with_retry.return_value = [mock_response]

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision])

        with pytest.raises(
            NoElementException,
            match=r"Wiki text element not found for site: test-site, page: test-page, revision: 100",
        ):
            collection.get_sources()

        assert sample_revision._source is None

    def test_get_sources_missing_response_body_includes_site_page_and_revision_context(
        self, mock_page, sample_revision
    ):
        """source response body欠落はsite、対象ページ、リビジョンIDを含める"""
        mock_page.site.unix_name = "test-site"
        mock_page.fullname = "test-page"
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_page.site.amc_request_with_retry.return_value = [mock_response]

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision])

        with pytest.raises(
            NoElementException,
            match=r"Page revision source response body is not found for site: test-site, page: test-page, revision: 100",
        ):
            collection.get_sources()

        assert sample_revision._source is None
        mock_page.site.amc_request.assert_not_called()
        mock_page.site.amc_request_with_retry.assert_called_once_with(
            [{"moduleName": "history/PageSourceModule", "revision_id": 100}]
        )

    def test_get_sources_malformed_response_body_type_includes_site_page_revision_and_type_context(
        self, mock_page, sample_revision
    ):
        """source response body型不正はsite、対象ページ、リビジョンID、型を含める"""
        mock_page.site.unix_name = "test-site"
        mock_page.fullname = "test-page"
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": ["not", "html"]}
        mock_page.site.amc_request_with_retry.return_value = [mock_response]

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision])

        with pytest.raises(
            NoElementException,
            match=(
                r"Page revision source response body is malformed for site: test-site, page: test-page, "
                r"revision: 100 \(field=body, expected=str, actual=list\)"
            ),
        ):
            collection.get_sources()

        assert sample_revision._source is None
        mock_page.site.amc_request.assert_not_called()
        mock_page.site.amc_request_with_retry.assert_called_once_with(
            [{"moduleName": "history/PageSourceModule", "revision_id": 100}]
        )

    def test_get_sources_skips_failed_retry_response(self, mock_page, sample_revision, mock_user):
        """source取得の一部失敗は成功リビジョンを保持し失敗リビジョンを未取得にする"""
        second_revision = PageRevision(
            page=mock_page,
            id=101,
            rev_no=2,
            created_by=mock_user,
            created_at=datetime(2023, 1, 2, 12, 0, 0),
            comment="Second revision",
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": '<div class="page-source">Test wiki text</div>'}
        mock_page.site.amc_request = MagicMock(return_value=[mock_response, None])
        mock_page.site.amc_request_with_retry = MagicMock(return_value=(mock_response, None))

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision, second_revision])
        collection.get_sources()

        mock_page.site.amc_request.assert_not_called()
        mock_page.site.amc_request_with_retry.assert_called_once_with(
            [
                {"moduleName": "history/PageSourceModule", "revision_id": 100},
                {"moduleName": "history/PageSourceModule", "revision_id": 101},
            ]
        )
        assert sample_revision._source is not None
        assert second_revision._source is None

    def test_get_sources_skips_already_acquired(self, mock_page, sample_revision):
        """既に取得済みのソースはスキップ"""
        sample_revision._source = MagicMock()

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision])
        result = collection.get_sources()

        mock_page.site.amc_request.assert_not_called()
        assert result == collection

    def test_get_sources_rejects_revision_from_different_page_before_fetch(self, mock_page, mock_user):
        """get_sourcesはコレクションページと異なるリビジョンを送信前に拒否する"""
        other_page = _page_on_same_site(mock_page)
        other_revision = PageRevision(
            page=other_page,
            id=101,
            rev_no=2,
            created_by=mock_user,
            created_at=datetime(2023, 1, 2, 12, 0, 0),
            comment="Other page revision",
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": '<div class="page-source">Wrong page source</div>'}
        mock_page.site.amc_request_with_retry.return_value = (mock_response,)

        collection = PageRevisionCollection(page=mock_page, revisions=[other_revision])

        with pytest.raises(ValueError, match="revisions must belong to the collection page"):
            collection.get_sources()

        mock_page.site.amc_request.assert_not_called()
        mock_page.site.amc_request_with_retry.assert_not_called()
        assert other_revision._source is None

    def test_get_sources_deduplicates_duplicate_revision_ids(self, mock_page, sample_revision, mock_user):
        """重複リビジョンIDはソース取得を1回だけ行い、各エントリへ反映する"""
        duplicate_revision = PageRevision(
            page=mock_page,
            id=sample_revision.id,
            rev_no=2,
            created_by=mock_user,
            created_at=datetime(2023, 1, 2, 12, 0, 0),
            comment="Duplicate revision entry",
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": '<div class="page-source">Shared wiki text</div>'}
        mock_page.site.amc_request_with_retry.return_value = (mock_response,)

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision, duplicate_revision])
        result = collection.get_sources()

        assert result == collection
        mock_page.site.amc_request_with_retry.assert_called_once_with(
            [{"moduleName": "history/PageSourceModule", "revision_id": sample_revision.id}]
        )
        assert sample_revision._source is not None
        assert duplicate_revision._source is not None
        assert sample_revision._source.wiki_text == "Shared wiki text"
        assert duplicate_revision._source.wiki_text == "Shared wiki text"
        assert mock_response.json.call_count == 1

    def test_get_sources_reuses_cached_duplicate_revision_source(self, mock_page, sample_revision, mock_user):
        """取得済みの重複リビジョンソースを未取得の同一IDリビジョンへ再利用する"""
        sample_revision._source = PageSource(page=mock_page, wiki_text="cached revision source")
        duplicate_revision = PageRevision(
            page=mock_page,
            id=sample_revision.id,
            rev_no=2,
            created_by=mock_user,
            created_at=datetime(2023, 1, 2, 12, 0, 0),
            comment="Duplicate revision entry",
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": '<div class="page-source">Fetched wiki text</div>'}
        mock_page.site.amc_request_with_retry.return_value = (mock_response,)

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision, duplicate_revision])
        result = collection.get_sources()

        assert result == collection
        assert duplicate_revision._source is not None
        assert duplicate_revision._source.wiki_text == "cached revision source"
        mock_page.site.amc_request.assert_not_called()
        mock_page.site.amc_request_with_retry.assert_not_called()

    def test_get_htmls_requires_page(self):
        """get_htmlsはpageが必要"""
        collection = PageRevisionCollection()
        with pytest.raises(ValueError) as exc_info:
            collection.get_htmls()
        assert "Page is not set" in str(exc_info.value)

    @pytest.mark.parametrize("bad_revision", [None, True, "100"])
    def test_get_htmls_rejects_non_revision_entries_before_fetch(self, mock_page, sample_revision, bad_revision):
        """get_htmlsはPageRevision以外の要素を送信前に拒否する"""
        bad_revision_entry: Any = bad_revision
        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision])
        collection.append(bad_revision_entry)

        with pytest.raises(ValueError, match="revisions list entries must be PageRevision"):
            collection.get_htmls()

        mock_page.site.amc_request.assert_not_called()
        mock_page.site.amc_request_with_retry.assert_not_called()

    def test_get_htmls_success(self, mock_page, sample_revision):
        """get_htmlsの成功ケース"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": "onclick=\"document.getElementById('page-version-info').style.display='none'\">close</a>\n\t</div>\n\n\n\n<p>Test HTML content</p>"
        }
        mock_page.site.amc_request_with_retry.return_value = [mock_response]

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision])
        result = collection.get_htmls()

        assert result == collection
        assert sample_revision._html is not None
        assert "<p>Test HTML content</p>" in sample_revision._html

    def test_get_htmls_tolerates_separator_whitespace(self, mock_page, sample_revision):
        """閉じるリンク後の空白差があってもHTMLを取得できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": "onclick=\"document.getElementById('page-version-info').style.display='none'\">close</a>\n"
            "   </div>\n<p>Test HTML content</p>"
        }
        mock_page.site.amc_request_with_retry.return_value = [mock_response]

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision])
        collection.get_htmls()

        assert sample_revision._html == "<p>Test HTML content</p>"

    def test_get_htmls_missing_response_body_includes_site_page_and_revision_context(self, mock_page, sample_revision):
        """HTML response body欠落はsite、対象ページ、リビジョンIDを含める"""
        mock_page.site.unix_name = "test-site"
        mock_page.fullname = "test-page"
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_page.site.amc_request_with_retry.return_value = [mock_response]

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision])

        with pytest.raises(
            NoElementException,
            match=r"Page revision HTML response body is not found for site: test-site, page: test-page, revision: 100",
        ):
            collection.get_htmls()

        assert sample_revision._html is None
        mock_page.site.amc_request.assert_not_called()
        mock_page.site.amc_request_with_retry.assert_called_once_with(
            [{"moduleName": "history/PageVersionModule", "revision_id": 100}]
        )

    def test_get_htmls_malformed_response_body_type_includes_site_page_revision_and_type_context(
        self, mock_page, sample_revision
    ):
        """HTML response body型不正はsite、対象ページ、リビジョンID、型を含める"""
        mock_page.site.unix_name = "test-site"
        mock_page.fullname = "test-page"
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": ["not", "html"]}
        mock_page.site.amc_request_with_retry.return_value = [mock_response]

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision])

        with pytest.raises(
            NoElementException,
            match=(
                r"Page revision HTML response body is malformed for site: test-site, page: test-page, "
                r"revision: 100 \(field=body, expected=str, actual=list\)"
            ),
        ):
            collection.get_htmls()

        assert sample_revision._html is None
        mock_page.site.amc_request.assert_not_called()
        mock_page.site.amc_request_with_retry.assert_called_once_with(
            [{"moduleName": "history/PageVersionModule", "revision_id": 100}]
        )

    def test_get_htmls_skips_failed_retry_response(self, mock_page, sample_revision, mock_user):
        """HTML取得の一部失敗は成功リビジョンを保持し失敗リビジョンを未取得にする"""
        second_revision = PageRevision(
            page=mock_page,
            id=101,
            rev_no=2,
            created_by=mock_user,
            created_at=datetime(2023, 1, 2, 12, 0, 0),
            comment="Second revision",
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": "<p>Test HTML content</p>"}
        mock_page.site.amc_request = MagicMock(return_value=[mock_response, None])
        mock_page.site.amc_request_with_retry = MagicMock(return_value=(mock_response, None))

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision, second_revision])
        collection.get_htmls()

        mock_page.site.amc_request.assert_not_called()
        mock_page.site.amc_request_with_retry.assert_called_once_with(
            [
                {"moduleName": "history/PageVersionModule", "revision_id": 100},
                {"moduleName": "history/PageVersionModule", "revision_id": 101},
            ]
        )
        assert sample_revision._html == "<p>Test HTML content</p>"
        assert second_revision._html is None

    def test_get_htmls_without_separator_uses_body(self, mock_page, sample_revision):
        """区切りリンクがない場合はbody全体をHTMLとして保持する"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": "<p>Direct HTML content</p>"}
        mock_page.site.amc_request_with_retry.return_value = [mock_response]

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision])
        collection.get_htmls()

        assert sample_revision._html == "<p>Direct HTML content</p>"

    def test_get_htmls_deduplicates_duplicate_revision_ids(self, mock_page, sample_revision, mock_user):
        """重複リビジョンIDはHTML取得を1回だけ行い、各エントリへ反映する"""
        duplicate_revision = PageRevision(
            page=mock_page,
            id=sample_revision.id,
            rev_no=2,
            created_by=mock_user,
            created_at=datetime(2023, 1, 2, 12, 0, 0),
            comment="Duplicate revision entry",
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": "<p>Shared HTML content</p>"}
        mock_page.site.amc_request_with_retry.return_value = (mock_response,)

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision, duplicate_revision])
        result = collection.get_htmls()

        assert result == collection
        mock_page.site.amc_request_with_retry.assert_called_once_with(
            [{"moduleName": "history/PageVersionModule", "revision_id": sample_revision.id}]
        )
        assert sample_revision._html == "<p>Shared HTML content</p>"
        assert duplicate_revision._html == "<p>Shared HTML content</p>"
        assert mock_response.json.call_count == 1

    def test_get_htmls_reuses_cached_duplicate_revision_html(self, mock_page, sample_revision, mock_user):
        """取得済みの重複リビジョンHTMLを未取得の同一IDリビジョンへ再利用する"""
        sample_revision._html = "<p>Cached revision HTML</p>"
        duplicate_revision = PageRevision(
            page=mock_page,
            id=sample_revision.id,
            rev_no=2,
            created_by=mock_user,
            created_at=datetime(2023, 1, 2, 12, 0, 0),
            comment="Duplicate revision entry",
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": "<p>Fetched HTML content</p>"}
        mock_page.site.amc_request_with_retry.return_value = (mock_response,)

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision, duplicate_revision])
        result = collection.get_htmls()

        assert result == collection
        assert duplicate_revision._html == "<p>Cached revision HTML</p>"
        mock_page.site.amc_request.assert_not_called()
        mock_page.site.amc_request_with_retry.assert_not_called()

    def test_get_htmls_skips_already_acquired(self, mock_page, sample_revision):
        """既に取得済みのHTMLはスキップ"""
        sample_revision._html = "<p>Already acquired</p>"

        collection = PageRevisionCollection(page=mock_page, revisions=[sample_revision])
        result = collection.get_htmls()

        mock_page.site.amc_request.assert_not_called()
        assert result == collection

    def test_get_htmls_rejects_revision_from_different_page_before_fetch(self, mock_page, mock_user):
        """get_htmlsはコレクションページと異なるリビジョンを送信前に拒否する"""
        other_page = _page_on_same_site(mock_page)
        other_revision = PageRevision(
            page=other_page,
            id=101,
            rev_no=2,
            created_by=mock_user,
            created_at=datetime(2023, 1, 2, 12, 0, 0),
            comment="Other page revision",
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": "<p>Wrong page HTML</p>"}
        mock_page.site.amc_request_with_retry.return_value = (mock_response,)

        collection = PageRevisionCollection(page=mock_page, revisions=[other_revision])

        with pytest.raises(ValueError, match="revisions must belong to the collection page"):
            collection.get_htmls()

        mock_page.site.amc_request.assert_not_called()
        mock_page.site.amc_request_with_retry.assert_not_called()
        assert other_revision._html is None


class TestPageRevision:
    """PageRevisionクラスのテスト"""

    @pytest.mark.parametrize("page", [None, True, "test-page", {"fullname": "test-page"}, object()])
    def test_init_rejects_malformed_pages(self, mock_user, page: object) -> None:
        """PageRevisionは実Page以外の親ページを受け付けない"""
        bad_page: Any = page

        with pytest.raises(ValueError, match="page must be a Page"):
            PageRevision(
                page=bad_page,
                id=100,
                rev_no=1,
                created_by=mock_user,
                created_at=datetime(2023, 1, 1, 12, 0, 0),
                comment="Initial revision",
            )

    @pytest.mark.parametrize("revision_id", [None, True, "100", 100.0])
    def test_init_rejects_malformed_ids(self, mock_page, mock_user, revision_id: object) -> None:
        """PageRevisionは整数IDだけ受け付ける"""
        bad_revision_id: Any = revision_id

        with pytest.raises(ValueError, match="id must be an integer"):
            PageRevision(
                page=mock_page,
                id=bad_revision_id,
                rev_no=1,
                created_by=mock_user,
                created_at=datetime(2023, 1, 1, 12, 0, 0),
                comment="Initial revision",
            )

    @pytest.mark.parametrize("rev_no", [None, True, "1", 1.0])
    def test_init_rejects_malformed_revision_numbers(self, mock_page, mock_user, rev_no: object) -> None:
        """PageRevisionは整数のリビジョン番号だけ受け付ける"""
        bad_rev_no: Any = rev_no

        with pytest.raises(ValueError, match="rev_no must be an integer"):
            PageRevision(
                page=mock_page,
                id=100,
                rev_no=bad_rev_no,
                created_by=mock_user,
                created_at=datetime(2023, 1, 1, 12, 0, 0),
                comment="Initial revision",
            )

    @pytest.mark.parametrize("comment", [None, True, 1, []])
    def test_init_rejects_malformed_comments(self, mock_page, mock_user, comment: object) -> None:
        """PageRevisionは文字列のコメントだけ受け付ける"""
        bad_comment: Any = comment

        with pytest.raises(ValueError, match="comment must be a string"):
            PageRevision(
                page=mock_page,
                id=100,
                rev_no=1,
                created_by=mock_user,
                created_at=datetime(2023, 1, 1, 12, 0, 0),
                comment=bad_comment,
            )

    @pytest.mark.parametrize("created_by", [None, True, 12345, "test-user", {"id": 12345}])
    def test_init_rejects_malformed_creators(self, mock_page, created_by: object) -> None:
        """PageRevisionはAbstractUserの作成者だけ受け付ける"""
        bad_created_by: Any = created_by

        with pytest.raises(ValueError, match="created_by must be an AbstractUser"):
            PageRevision(
                page=mock_page,
                id=100,
                rev_no=1,
                created_by=bad_created_by,
                created_at=datetime(2023, 1, 1, 12, 0, 0),
                comment="Initial revision",
            )

    @pytest.mark.parametrize("created_at", [None, True, 1700000000, "2023-01-01", []])
    def test_init_rejects_malformed_created_at(self, mock_page, mock_user, created_at: object) -> None:
        """PageRevisionはdatetimeの作成日時だけ受け付ける"""
        bad_created_at: Any = created_at

        with pytest.raises(ValueError, match="created_at must be a datetime"):
            PageRevision(
                page=mock_page,
                id=100,
                rev_no=1,
                created_by=mock_user,
                created_at=bad_created_at,
                comment="Initial revision",
            )

    def test_is_source_acquired_false(self, sample_revision):
        """ソース未取得の確認"""
        assert sample_revision.is_source_acquired() is False

    def test_is_source_acquired_true(self, sample_revision):
        """ソース取得済みの確認"""
        sample_revision._source = MagicMock()
        assert sample_revision.is_source_acquired() is True

    @pytest.mark.parametrize(
        "source",
        [
            True,
            100,
            "cached revision source",
            ["cached revision source"],
            {"wiki_text": "cached revision source"},
            object(),
        ],
    )
    def test_init_rejects_malformed_source_cache(self, mock_page, mock_user, source: object) -> None:
        """PageRevisionの初期sourceキャッシュはPageSourceまたはNoneだけ受け付ける"""
        bad_source: Any = source

        with pytest.raises(ValueError, match="revision.source must be PageSource"):
            PageRevision(
                page=mock_page,
                id=100,
                rev_no=1,
                created_by=mock_user,
                created_at=datetime(2023, 1, 1, 12, 0, 0),
                comment="Initial revision",
                _source=bad_source,
            )

    def test_init_accepts_valid_source_cache(self, mock_page, mock_user) -> None:
        """有効なPageSourceキャッシュを初期化時に保持できる"""
        source = PageSource(page=mock_page, wiki_text="cached revision source")

        revision = PageRevision(
            page=mock_page,
            id=100,
            rev_no=1,
            created_by=mock_user,
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            comment="Initial revision",
            _source=source,
        )

        assert revision.source == source
        assert revision.is_source_acquired() is True
        mock_page.site.amc_request_with_retry.assert_not_called()

    @pytest.mark.parametrize(
        "html",
        [True, 100, ["<p>Cached HTML</p>"], {"html": "<p>Cached HTML</p>"}, object()],
    )
    def test_init_rejects_malformed_html_cache(self, mock_page, mock_user, html: object) -> None:
        """PageRevisionの初期HTMLキャッシュは文字列またはNoneだけ受け付ける"""
        bad_html: Any = html

        with pytest.raises(ValueError, match="revision.html must be a string"):
            PageRevision(
                page=mock_page,
                id=100,
                rev_no=1,
                created_by=mock_user,
                created_at=datetime(2023, 1, 1, 12, 0, 0),
                comment="Initial revision",
                _html=bad_html,
            )

    def test_init_accepts_valid_html_cache(self, mock_page, mock_user) -> None:
        """有効なHTMLキャッシュを初期化時に保持できる"""
        revision = PageRevision(
            page=mock_page,
            id=100,
            rev_no=1,
            created_by=mock_user,
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            comment="Initial revision",
            _html="<p>Cached HTML</p>",
        )

        assert revision.html == "<p>Cached HTML</p>"
        assert revision.is_html_acquired() is True
        mock_page.site.amc_request_with_retry.assert_not_called()

    def test_is_html_acquired_false(self, sample_revision):
        """HTML未取得の確認"""
        assert sample_revision.is_html_acquired() is False

    def test_is_html_acquired_true(self, sample_revision):
        """HTML取得済みの確認"""
        sample_revision._html = "<p>Test</p>"
        assert sample_revision.is_html_acquired() is True

    def test_source_property_lazy_load(self, mock_page, sample_revision):
        """sourceプロパティの遅延読み込み"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": '<div class="page-source">Lazy loaded text</div>'}
        mock_page.site.amc_request_with_retry.return_value = [mock_response]

        result = sample_revision.source

        mock_page.site.amc_request.assert_not_called()
        mock_page.site.amc_request_with_retry.assert_called_once()
        assert result is not None

    def test_source_property_raises_when_retry_is_exhausted(self, mock_page, sample_revision):
        """sourceプロパティは再試行失敗をNoneとして返さない"""
        mock_page.site.unix_name = "test-site"
        mock_page.fullname = "test-page"
        mock_page.site.amc_request_with_retry.return_value = (None,)

        with pytest.raises(
            UnexpectedException,
            match="Cannot retrieve page revision source for site: test-site, page: test-page, revision: 100",
        ):
            _ = sample_revision.source

        mock_page.site.amc_request.assert_not_called()
        mock_page.site.amc_request_with_retry.assert_called_once_with(
            [{"moduleName": "history/PageSourceModule", "revision_id": 100}]
        )

    def test_source_property_uses_cache(self, sample_revision):
        """sourceプロパティがキャッシュを使用"""
        mock_source = MagicMock()
        sample_revision._source = mock_source

        result = sample_revision.source

        assert result == mock_source

    def test_source_setter(self, sample_revision):
        """sourceセッター"""
        source = PageSource(page=sample_revision.page, wiki_text="cached revision source")
        sample_revision.source = source
        assert sample_revision._source == source

    @pytest.mark.parametrize("source", [None, True, "cached revision source", {"wiki_text": "cached revision source"}])
    def test_source_setter_rejects_invalid_sources(self, sample_revision, source):
        """sourceセッターはPageSource以外を受け付けない"""
        cached_source = PageSource(page=sample_revision.page, wiki_text="cached revision source")
        sample_revision.source = cached_source

        with pytest.raises(ValueError, match="revision.source must be PageSource"):
            sample_revision.source = source

        assert sample_revision.source == cached_source

    def test_html_property_lazy_load(self, mock_page, sample_revision):
        """htmlプロパティの遅延読み込み"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": "onclick=\"document.getElementById('page-version-info').style.display='none'\">close</a>\n\t</div>\n\n\n\n<p>Lazy HTML</p>"
        }
        mock_page.site.amc_request_with_retry.return_value = [mock_response]

        result = sample_revision.html

        mock_page.site.amc_request.assert_not_called()
        mock_page.site.amc_request_with_retry.assert_called_once()
        assert result is not None

    def test_html_property_raises_when_retry_is_exhausted(self, mock_page, sample_revision):
        """htmlプロパティは再試行失敗をNoneとして返さない"""
        mock_page.site.unix_name = "test-site"
        mock_page.fullname = "test-page"
        mock_page.site.amc_request_with_retry.return_value = (None,)

        with pytest.raises(
            UnexpectedException,
            match="Cannot retrieve page revision HTML for site: test-site, page: test-page, revision: 100",
        ):
            _ = sample_revision.html

        mock_page.site.amc_request.assert_not_called()
        mock_page.site.amc_request_with_retry.assert_called_once_with(
            [{"moduleName": "history/PageVersionModule", "revision_id": 100}]
        )

    def test_html_property_uses_cache(self, sample_revision):
        """htmlプロパティがキャッシュを使用"""
        sample_revision._html = "<p>Cached HTML</p>"

        result = sample_revision.html

        assert result == "<p>Cached HTML</p>"

    def test_html_setter(self, sample_revision):
        """htmlセッター"""
        sample_revision.html = "<p>New HTML</p>"
        assert sample_revision._html == "<p>New HTML</p>"

    @pytest.mark.parametrize("html", [None, True, 1, ["<p>New HTML</p>"]])
    def test_html_setter_rejects_invalid_html(self, sample_revision, html):
        """htmlセッターは文字列以外を受け付けない"""
        sample_revision.html = "<p>Cached HTML</p>"

        with pytest.raises(ValueError, match="revision.html must be a string"):
            sample_revision.html = html

        assert sample_revision.html == "<p>Cached HTML</p>"
