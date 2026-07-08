"""PageFileモジュールのユニットテスト"""

import re
from datetime import datetime
from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from wikidot.common import exceptions
from wikidot.module.client import Client
from wikidot.module.page import Page
from wikidot.module.page_file import PageFile, PageFileCollection
from wikidot.module.site import Site
from wikidot.module.user import User


def _client() -> Client:
    client: Any = object.__new__(Client)
    client.is_logged_in = False
    client.username = None
    client.me = None
    client.login_check = MagicMock()
    return client


def _page() -> Page:
    """HTTPなしで使う実Page"""
    site = Site(
        client=_client(),
        id=123456,
        title="Test Site",
        unix_name="test-site",
        domain="test.wikidot.com",
        ssl_supported=True,
    )
    site.amc_request = MagicMock()
    site.amc_request_with_retry = MagicMock()
    user = User(client=site.client, id=12345, name="test-user", unix_name="test-user")
    timestamp = datetime(2023, 1, 1, 12, 0, 0)
    return Page(
        site=site,
        fullname="test-page",
        name="test-page",
        category="_default",
        title="Test Page Title",
        children_count=0,
        comments_count=0,
        size=1000,
        rating=10,
        votes_count=5,
        rating_percent=0.5,
        revisions_count=3,
        parent_fullname=None,
        tags=["tag1", "tag2"],
        created_by=user,
        created_at=timestamp,
        updated_by=user,
        updated_at=timestamp,
        commented_by=None,
        commented_at=None,
        _id=12345,
    )


def _page_on_same_site(page: Page, fullname: str = "other-page") -> Page:
    other_page = _page()
    other_page.site = page.site
    other_page.fullname = fullname
    other_page.name = fullname
    other_page._id = 67890
    return other_page


def _page_file(
    page: Page,
    *,
    file_id: Any = 123,
    name: Any = "test.txt",
    url: Any = "https://example.com/test.txt",
    mime_type: Any = "text/plain",
    size: Any = 1024,
) -> PageFile:
    return PageFile(page=page, id=file_id, name=name, url=url, mime_type=mime_type, size=size)


def _mutate_retained_file_id(file: PageFile, file_id: object) -> None:
    file.id = cast(Any, file_id)


def _mutate_retained_file_name(file: PageFile, name: object) -> None:
    file.name = cast(Any, name)


class TestPageFileCollection:
    """PageFileCollectionのテスト"""

    def test_init_with_page(self):
        """ページを指定して初期化"""
        page = _page()

        collection = PageFileCollection(page=page, files=[])

        assert collection.page == page
        assert len(collection) == 0

    def test_init_empty_without_page_exposes_none_page(self) -> None:
        """空の親なしファイルコレクションはpage=Noneを保持する"""
        collection = PageFileCollection(page=None, files=[])

        assert collection.page is None
        assert len(collection) == 0

    def test_init_infers_page_from_files(self):
        """ファイルリストからページを推測"""
        page = _page()
        file1 = PageFile(page=page, id=1, name="test.txt", url="", mime_type="", size=0)

        collection = PageFileCollection(page=None, files=[file1])

        assert collection.page == page

    @pytest.mark.parametrize("page", [True, "test-page", {"fullname": "test-page"}, object()])
    def test_init_rejects_malformed_pages(self, page: object) -> None:
        """明示されたpageはPageだけ受け付ける"""
        bad_page: Any = page

        with pytest.raises(ValueError, match="page must be a Page"):
            PageFileCollection(page=bad_page, files=[])

    def test_init_with_files(self):
        """ファイルリストを指定して初期化"""
        page = _page()
        file1 = PageFile(page=page, id=1, name="test.txt", url="", mime_type="", size=100)
        file2 = PageFile(page=page, id=2, name="image.png", url="", mime_type="", size=200)

        collection = PageFileCollection(page=page, files=[file1, file2])

        assert len(collection) == 2

    def test_init_rejects_file_from_different_page(self) -> None:
        page = _page()
        other_page = _page_on_same_site(page)
        file = _page_file(other_page)

        with pytest.raises(ValueError, match="files must belong to the collection page"):
            PageFileCollection(page=page, files=[file])

    def test_init_rejects_mixed_page_files_when_page_is_inferred(self) -> None:
        page = _page()
        other_page = _page_on_same_site(page)
        file1 = _page_file(page, file_id=1)
        file2 = _page_file(other_page, file_id=2)

        with pytest.raises(ValueError, match="files must belong to the collection page"):
            PageFileCollection(page=None, files=[file1, file2])

    @pytest.mark.parametrize("files", [True, False, "file", ("file",), 100])
    def test_init_rejects_non_list_files(self, files: object):
        """filesはlistまたはNoneだけ受け付ける"""
        page = _page()
        bad_files: Any = files

        with pytest.raises(ValueError, match="files must be a list or None"):
            PageFileCollection(page=page, files=bad_files)

    @pytest.mark.parametrize("file", [None, True, "file", {"id": 100}])
    def test_init_rejects_non_file_entries(self, file: object):
        """filesの要素はPageFileだけ受け付ける"""
        page = _page()
        bad_files: Any = [file]

        with pytest.raises(ValueError, match="files list entries must be PageFile"):
            PageFileCollection(page=page, files=bad_files)

    def test_iter(self):
        """イテレーション"""
        page = _page()
        file1 = PageFile(page=page, id=1, name="a.txt", url="", mime_type="", size=0)
        file2 = PageFile(page=page, id=2, name="b.txt", url="", mime_type="", size=0)

        collection = PageFileCollection(page=page, files=[file1, file2])

        files = list(collection)
        assert len(files) == 2
        assert files[0].name == "a.txt"
        assert files[1].name == "b.txt"

    def test_find_existing_by_id(self):
        """IDで存在するファイルを検索"""
        page = _page()
        file1 = PageFile(page=page, id=123, name="test.txt", url="", mime_type="", size=0)
        file2 = PageFile(page=page, id=456, name="other.txt", url="", mime_type="", size=0)

        collection = PageFileCollection(page=page, files=[file1, file2])

        result = collection.find(123)

        assert result is not None
        assert result.name == "test.txt"

    def test_find_nonexistent_by_id(self):
        """存在しないIDの検索でNone"""
        page = _page()
        file1 = PageFile(page=page, id=123, name="test.txt", url="", mime_type="", size=0)

        collection = PageFileCollection(page=page, files=[file1])

        result = collection.find(999)

        assert result is None

    def test_find_accepts_file_with_zero_retained_id(self) -> None:
        page = _page()
        file = _page_file(page, file_id=0)
        collection = PageFileCollection(page=page, files=[file])

        assert collection.find(0) is file

    @pytest.mark.parametrize("file_id", [None, True, "123", 123.0])
    def test_find_rejects_non_integer_ids(self, file_id):
        """findの検索IDはbool以外の整数だけ受け付ける"""
        page = _page()
        file1 = PageFile(page=page, id=1, name="test.txt", url="", mime_type="", size=0)
        collection = PageFileCollection(page=page, files=[file1])

        with pytest.raises(ValueError, match="id must be an integer"):
            collection.find(file_id)

    @pytest.mark.parametrize(
        ("retained_file_id", "lookup_id"),
        [
            (None, 1001),
            (True, 1),
            (False, 0),
            ("1001", 1001),
            (1001.0, 1001),
            ([], 1001),
        ],
    )
    def test_find_rejects_file_with_malformed_retained_ids(self, retained_file_id: object, lookup_id: int) -> None:
        page = _page()
        file = _page_file(page, file_id=1001)
        _mutate_retained_file_id(file, retained_file_id)
        collection = PageFileCollection(page=page, files=[file])

        with pytest.raises(ValueError, match="id must be an integer"):
            collection.find(lookup_id)

    def test_find_rejects_file_with_negative_retained_id(self) -> None:
        page = _page()
        file = _page_file(page, file_id=1001)
        _mutate_retained_file_id(file, -1)
        collection = PageFileCollection(page=page, files=[file])

        with pytest.raises(ValueError, match="id must be non-negative"):
            collection.find(1001)

    def test_find_by_name_existing(self):
        """名前で存在するファイルを検索"""
        page = _page()
        file1 = PageFile(page=page, id=1, name="image.png", url="", mime_type="", size=0)
        file2 = PageFile(page=page, id=2, name="document.pdf", url="", mime_type="", size=0)

        collection = PageFileCollection(page=page, files=[file1, file2])

        result = collection.find_by_name("document.pdf")

        assert result is not None
        assert result.id == 2

    def test_find_by_name_nonexistent(self):
        """存在しない名前の検索でNone"""
        page = _page()
        file1 = PageFile(page=page, id=1, name="image.png", url="", mime_type="", size=0)

        collection = PageFileCollection(page=page, files=[file1])

        result = collection.find_by_name("nonexistent.txt")

        assert result is None

    @pytest.mark.parametrize("file_name", [None, True, 123, 1.0])
    def test_find_by_name_rejects_non_string_names(self, file_name):
        """find_by_nameの検索名は文字列だけ受け付ける"""
        page = _page()
        file1 = PageFile(page=page, id=1, name="test.txt", url="", mime_type="", size=0)
        collection = PageFileCollection(page=page, files=[file1])

        with pytest.raises(ValueError, match="name must be a string"):
            collection.find_by_name(file_name)

    @pytest.mark.parametrize("file_name", ["", "   "])
    def test_find_by_name_rejects_blank_names(self, file_name: str) -> None:
        """find_by_nameの検索名はblank文字列を受け付けない"""
        page = _page()
        file1 = PageFile(page=page, id=1, name="test.txt", url="", mime_type="", size=0)
        collection = PageFileCollection(page=page, files=[file1])

        with pytest.raises(ValueError, match="name must not be empty"):
            collection.find_by_name(file_name)

    @pytest.mark.parametrize("file_name", [None, True, 123, 1.0, []])
    def test_find_by_name_rejects_malformed_retained_file_names(self, file_name: object) -> None:
        """find_by_nameは保持しているファイル名の破損も検索前に検証する"""
        page = _page()
        file = _page_file(page, file_id=1, name="document.pdf")
        _mutate_retained_file_name(file, file_name)
        collection = PageFileCollection(page=page, files=[file])

        with pytest.raises(ValueError, match="name must be a string"):
            collection.find_by_name("document.pdf")

    @pytest.mark.parametrize("file_name", ["", "   "])
    def test_find_by_name_rejects_blank_retained_file_names(self, file_name: str) -> None:
        """find_by_nameは保持しているblankファイル名の破損も検索前に検証する"""
        page = _page()
        file = _page_file(page, file_id=1, name="document.pdf")
        _mutate_retained_file_name(file, file_name)
        collection = PageFileCollection(page=page, files=[file])

        with pytest.raises(ValueError, match="name must not be empty"):
            collection.find_by_name("document.pdf")


class TestPageFileCollectionParseSize:
    """PageFileCollection._parse_sizeのテスト"""

    def test_parse_bytes(self):
        """バイト単位のパース"""
        result = PageFileCollection._parse_size("500 Bytes")
        assert result == 500

    def test_parse_kilobytes(self):
        """キロバイト単位のパース"""
        result = PageFileCollection._parse_size("1.5 kB")
        assert result == 1500

    def test_parse_uppercase_kilobytes(self):
        """大文字KB表記のパース"""
        result = PageFileCollection._parse_size("1.5 KB")
        assert result == 1500

    def test_parse_singular_byte(self):
        """単数Byte表記のパース"""
        result = PageFileCollection._parse_size("1 Byte")
        assert result == 1

    def test_parse_megabytes(self):
        """メガバイト単位のパース"""
        result = PageFileCollection._parse_size("2 MB")
        assert result == 2000000

    def test_parse_gigabytes(self):
        """ギガバイト単位のパース"""
        result = PageFileCollection._parse_size("1 GB")
        assert result == 1000000000

    def test_parse_unknown_returns_zero(self):
        """不明な単位は0を返す"""
        result = PageFileCollection._parse_size("unknown")
        assert result == 0

    def test_parse_with_whitespace(self):
        """空白を含む文字列のパース"""
        result = PageFileCollection._parse_size("  100 Bytes  ")
        assert result == 100


class TestPageFileCollectionAcquire:
    """PageFileCollection.acquireのテスト"""

    @pytest.mark.parametrize("page", [None, True, "test-page", {"fullname": "test-page"}, object()])
    def test_acquire_rejects_malformed_page_before_fetch(self, page: object) -> None:
        """直接取得のpageはPageだけ受け付ける"""
        bad_page: Any = page

        with pytest.raises(ValueError, match="page must be a Page"):
            PageFileCollection.acquire(bad_page)

    def test_acquire_refreshes_cached_page_files(self):
        """直接取得は既存page.filesキャッシュを返さず再取得する"""
        page = _page()
        page.id = 12345
        site = MagicMock()
        site.url = "https://test.wikidot.com"
        page.site = site
        cached_file = PageFile(
            page=page,
            id=100,
            name="cached.txt",
            url="https://test.wikidot.com/local--files/test-page/cached.txt",
            mime_type="text/plain",
            size=100,
        )
        cached_collection = PageFileCollection(page=page, files=[cached_file])
        page._files = cached_collection
        site.amc_request = MagicMock()
        response = MagicMock()
        response.json.return_value = {"body": "<div>No files</div>"}
        site.amc_request_with_retry = MagicMock(return_value=(response,))

        collection = PageFileCollection.acquire(page)

        assert collection is not cached_collection
        assert page._files is collection
        assert len(collection) == 0
        site.amc_request.assert_not_called()
        site.amc_request_with_retry.assert_called_once_with([{"moduleName": "files/PageFilesModule", "page_id": 12345}])

    def test_acquire_uses_retry_aware_amc(self):
        """直接ファイル取得でもリトライ対応AMCを使う"""
        page = _page()
        page.id = 12345
        site = MagicMock()
        site.url = "https://test.wikidot.com"
        page.site = site

        response = MagicMock()
        response.json.return_value = {"body": "<div>No files</div>"}
        site.amc_request = MagicMock(return_value=[RuntimeError("transient")])
        site.amc_request_with_retry = MagicMock(return_value=(response,))

        collection = PageFileCollection.acquire(page)

        site.amc_request.assert_not_called()
        site.amc_request_with_retry.assert_called_once_with([{"moduleName": "files/PageFilesModule", "page_id": 12345}])
        assert len(collection) == 0
        assert collection.page == page

    def test_acquire_populates_page_files_cache(self, mock_page_with_id):
        """直接ファイル取得の成功結果はpage.filesキャッシュにも保存する"""
        response = MagicMock()
        response.json.return_value = {
            "body": """
                <table class="page-files">
                    <tbody>
                        <tr id="file-row-100">
                            <td><a href="/local--files/test-page/file1.txt">file1.txt</a></td>
                            <td><span title="text/plain">TXT</span></td>
                            <td>500 Bytes</td>
                        </tr>
                    </tbody>
                </table>
            """
        }
        mock_page_with_id.site.amc_request = MagicMock()
        mock_page_with_id.site.amc_request_with_retry = MagicMock(return_value=(response,))

        collection = PageFileCollection.acquire(mock_page_with_id)

        assert mock_page_with_id._files is collection
        assert mock_page_with_id.files is collection
        mock_page_with_id.site.amc_request.assert_not_called()
        mock_page_with_id.site.amc_request_with_retry.assert_called_once_with(
            [{"moduleName": "files/PageFilesModule", "page_id": mock_page_with_id.id}]
        )

    def test_acquire_raises_when_retry_is_exhausted(self):
        """直接ファイル取得リトライが尽きた場合は明示的に失敗する"""
        page = _page()
        page.id = 12345
        page.fullname = "test-page"
        site = MagicMock()
        site.unix_name = "test-site"
        page.site = site
        site.amc_request = MagicMock()
        site.amc_request_with_retry = MagicMock(return_value=(None,))

        with pytest.raises(
            exceptions.UnexpectedException,
            match="Cannot retrieve page files for site: test-site, page: test-page",
        ):
            PageFileCollection.acquire(page)

        site.amc_request.assert_not_called()
        site.amc_request_with_retry.assert_called_once_with([{"moduleName": "files/PageFilesModule", "page_id": 12345}])

    def test_acquire_missing_response_body_includes_page_context(self):
        """直接ファイル一覧応答のbody欠落時はsite/page付きで失敗する"""
        page = _page()
        page.id = 12345
        page.fullname = "test-page"
        site = MagicMock()
        site.unix_name = "test-site"
        page.site = site
        response = MagicMock()
        response.json.return_value = {}
        site.amc_request = MagicMock()
        site.amc_request_with_retry = MagicMock(return_value=(response,))

        with pytest.raises(
            exceptions.NoElementException,
            match="Page file list response body is not found for site: test-site, page: test-page",
        ):
            PageFileCollection.acquire(page)

        site.amc_request.assert_not_called()
        site.amc_request_with_retry.assert_called_once_with([{"moduleName": "files/PageFilesModule", "page_id": 12345}])

    def test_acquire_malformed_response_body_type_includes_page_context(self):
        """直接ファイル一覧応答のbody型異常はsite/page/type付きで失敗する"""
        page = _page()
        page.id = 12345
        page.fullname = "test-page"
        page._files = None
        site = MagicMock()
        site.unix_name = "test-site"
        page.site = site
        response = MagicMock()
        response.json.return_value = {"body": ["not", "html"]}
        site.amc_request = MagicMock()
        site.amc_request_with_retry = MagicMock(return_value=(response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                "Page file list response body is malformed for site: test-site, page: test-page "
                "\\(field=body, expected=str, actual=list\\)"
            ),
        ):
            PageFileCollection.acquire(page)

        assert page._files is None
        site.amc_request.assert_not_called()
        site.amc_request_with_retry.assert_called_once_with([{"moduleName": "files/PageFilesModule", "page_id": 12345}])

    def test_acquire_malformed_response_payload_type_includes_page_context(self):
        """直接ファイル一覧応答payload型異常はsite/page/type付きで失敗する"""
        page = _page()
        page.id = 12345
        page.fullname = "test-page"
        page._files = None
        site = MagicMock()
        site.unix_name = "test-site"
        page.site = site
        response = MagicMock()
        response.json.return_value = ["not", "a", "mapping"]
        site.amc_request = MagicMock()
        site.amc_request_with_retry = MagicMock(return_value=(response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                "Page file list response payload is malformed for site: test-site, page: test-page "
                "\\(expected=dict, actual=list\\)"
            ),
        ):
            PageFileCollection.acquire(page)

        assert page._files is None
        site.amc_request.assert_not_called()
        site.amc_request_with_retry.assert_called_once_with([{"moduleName": "files/PageFilesModule", "page_id": 12345}])

    def test_acquire_success(self):
        """ファイル取得成功"""
        page = _page()
        page.id = 12345
        site = MagicMock()
        site.url = "https://test.wikidot.com"
        page.site = site

        response = MagicMock()
        response.json.return_value = {
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
        site.amc_request_with_retry.return_value = (response,)

        collection = PageFileCollection.acquire(page)

        assert len(collection) == 1
        assert collection[0].id == 100
        assert collection[0].name == "image.png"
        assert collection[0].mime_type == "image/png"
        assert collection[0].size == 1500
        assert "test.wikidot.com" in collection[0].url

    def test_acquire_preserves_file_name_text_spacing(self):
        """装飾要素を含む添付ファイル名の語境界を保持する"""
        page = _page()
        page.id = 12345
        site = MagicMock()
        site.url = "https://test.wikidot.com"
        page.site = site

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <table class="page-files">
                    <tbody>
                        <tr id="file-row-100">
                            <td>
                                <a href="/local--files/test-page/first-second.txt">
                                    <span>First <em>part</em></span><span>Second part.txt</span>
                                </a>
                            </td>
                            <td><span title="text/plain">TXT</span></td>
                            <td>1 KB</td>
                        </tr>
                    </tbody>
                </table>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        collection = PageFileCollection.acquire(page)

        assert len(collection) == 1
        assert collection[0].name == "First part Second part.txt"

    def test_acquire_preserves_absolute_file_url(self):
        """絶対URLの添付ファイルhrefを壊さない"""
        page = _page()
        page.id = 12345
        site = MagicMock()
        site.url = "https://test.wikidot.com"
        page.site = site

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <table class="page-files">
                    <tbody>
                        <tr id="file-row-100">
                            <td><a href="https://cdn.example.com/file.txt">file.txt</a></td>
                            <td><span title="text/plain">TXT</span></td>
                            <td>1 KB</td>
                        </tr>
                    </tbody>
                </table>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        collection = PageFileCollection.acquire(page)

        assert collection[0].url == "https://cdn.example.com/file.txt"

    @pytest.mark.parametrize(
        "href",
        [
            "javascript:alert(1)",
            "mailto:file@example.com",
            "http:file.txt",
            "/",
            "#file.txt",
            "?file=file.txt",
        ],
    )
    def test_acquire_rejects_malformed_file_link_href_routes(self, href: str) -> None:
        """構造的に有効な添付ファイル行でhrefルートが壊れている場合は文脈付きで失敗する"""
        page = _page()
        page.id = 12345
        page.fullname = "test-page"
        site = MagicMock()
        site.url = "https://test.wikidot.com"
        site.unix_name = "test-site"
        page.site = site

        response = MagicMock()
        response.json.return_value = {
            "body": f"""
                <table class="page-files">
                    <tbody>
                        <tr id="file-row-100">
                            <td><a href="{href}">file.txt</a></td>
                            <td><span title="text/plain">TXT</span></td>
                            <td>1 KB</td>
                        </tr>
                    </tbody>
                </table>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Page file link href is malformed for site: test-site, page: test-page, "
                rf"file: file\.txt \(id=100, field=href, value={re.escape(href)}\)"
            ),
        ):
            PageFileCollection.acquire(page)

    def test_acquire_requires_file_mime_title(self):
        """構造的に有効な添付ファイル行でMIME titleが欠落した場合は文脈付きで失敗する"""
        page = _page()
        page.id = 12345
        page.fullname = "test-page"
        site = MagicMock()
        site.url = "https://test.wikidot.com"
        site.unix_name = "test-site"
        page.site = site

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <table class="page-files">
                    <tbody>
                        <tr id="file-row-100">
                            <td><a href="/local--files/test-page/file.txt">file.txt</a></td>
                            <td><span>TXT</span></td>
                            <td>1 KB</td>
                        </tr>
                    </tbody>
                </table>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Page file MIME type title is not found for site: test-site, page: test-page, "
                r"file: file\.txt \(id=100, field=mime_type\)"
            ),
        ):
            PageFileCollection.acquire(page)

    def test_acquire_requires_parseable_file_size(self):
        """構造的に有効な添付ファイル行でサイズ値が壊れている場合は文脈付きで失敗する"""
        page = _page()
        page.id = 12345
        page.fullname = "test-page"
        site = MagicMock()
        site.url = "https://test.wikidot.com"
        site.unix_name = "test-site"
        page.site = site

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <table class="page-files">
                    <tbody>
                        <tr id="file-row-100">
                            <td><a href="/local--files/test-page/file.txt">file.txt</a></td>
                            <td><span title="text/plain">TXT</span></td>
                            <td>unknown</td>
                        </tr>
                    </tbody>
                </table>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Page file size is malformed for site: test-site, page: test-page, "
                r"file: file\.txt \(id=100, field=size, value=unknown\)"
            ),
        ):
            PageFileCollection.acquire(page)

    def test_acquire_rejects_non_finite_file_size(self):
        """構造的に有効な添付ファイル行でサイズ値が非有限になる場合は文脈付きで失敗する"""
        page = _page()
        page.id = 12345
        page.fullname = "test-page"
        site = MagicMock()
        site.url = "https://test.wikidot.com"
        site.unix_name = "test-site"
        page.site = site
        size_text = f"{'9' * 400} GB"

        response = MagicMock()
        response.json.return_value = {
            "body": f"""
                <table class="page-files">
                    <tbody>
                        <tr id="file-row-100">
                            <td><a href="/local--files/test-page/file.txt">file.txt</a></td>
                            <td><span title="text/plain">TXT</span></td>
                            <td>{size_text}</td>
                        </tr>
                    </tbody>
                </table>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with pytest.raises(exceptions.NoElementException) as exc_info:
            PageFileCollection.acquire(page)

        message = str(exc_info.value)
        assert (
            "Page file size is malformed for site: test-site, page: test-page, "
            "file: file.txt (id=100, field=size, value="
        ) in message
        assert size_text in message

    def test_acquire_requires_file_link_href(self):
        """構造的に有効な添付ファイル行でhrefが欠落した場合は文脈付きで失敗する"""
        page = _page()
        page.id = 12345
        page.fullname = "test-page"
        site = MagicMock()
        site.url = "https://test.wikidot.com"
        site.unix_name = "test-site"
        page.site = site

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <table class="page-files">
                    <tbody>
                        <tr id="file-row-100">
                            <td><a>file.txt</a></td>
                            <td><span title="text/plain">TXT</span></td>
                            <td>1 KB</td>
                        </tr>
                    </tbody>
                </table>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Page file link href is not found for site: test-site, page: test-page, "
                r"file: file\.txt \(id=100, field=href\)"
            ),
        ):
            PageFileCollection.acquire(page)

    def test_acquire_requires_file_name(self):
        """構造的に有効な添付ファイル行でファイル名が欠落した場合は文脈付きで失敗する"""
        page = _page()
        page.id = 12345
        page.fullname = "test-page"
        site = MagicMock()
        site.url = "https://test.wikidot.com"
        site.unix_name = "test-site"
        page.site = site

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <table class="page-files">
                    <tbody>
                        <tr id="file-row-100">
                            <td><a href="/local--files/test-page/file.txt"></a></td>
                            <td><span title="text/plain">TXT</span></td>
                            <td>1 KB</td>
                        </tr>
                    </tbody>
                </table>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with pytest.raises(
            exceptions.NoElementException,
            match=r"Page file name is not found for site: test-site, page: test-page \(id=100, field=name\)",
        ):
            PageFileCollection.acquire(page)

    def test_acquire_malformed_file_row_id_includes_page_row_and_value_context(self):
        """不正なfile-row IDは行を黙って落とさずsite/page/row/value付きで失敗する"""
        page = _page()
        page.id = 12345
        page.fullname = "test-page"
        site = MagicMock()
        site.unix_name = "test-site"
        site.url = "https://test.wikidot.com"
        page.site = site

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <table class="page-files">
                    <tbody>
                        <tr id="file-row-not-a-number">
                            <td><a href="/local--files/test-page/bad.txt">bad.txt</a></td>
                            <td><span title="text/plain">TXT</span></td>
                            <td>1 KB</td>
                        </tr>
                        <tr id="file-row-101">
                            <td><a href="/local--files/test-page/good.txt">good.txt</a></td>
                            <td><span title="text/plain">TXT</span></td>
                            <td>1 KB</td>
                        </tr>
                    </tbody>
                </table>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Page file row ID is malformed for site: test-site, page: test-page "
                r"\(row=1, field=id, value=file-row-not-a-number\)"
            ),
        ):
            PageFileCollection.acquire(page)

    def test_acquire_rejects_non_ascii_digit_file_row_id(self):
        """file-row IDはUnicode数字を通常IDへ正規化しない"""
        page = _page()
        page.id = 12345
        page.fullname = "test-page"
        site = MagicMock()
        site.unix_name = "test-site"
        site.url = "https://test.wikidot.com"
        page.site = site

        fullwidth_file_id = "\uff11\uff10\uff10"
        response = MagicMock()
        response.json.return_value = {
            "body": f"""
                <table class="page-files">
                    <tbody>
                        <tr id="file-row-{fullwidth_file_id}">
                            <td><a href="/local--files/test-page/bad.txt">bad.txt</a></td>
                            <td><span title="text/plain">TXT</span></td>
                            <td>1 KB</td>
                        </tr>
                    </tbody>
                </table>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Page file row ID is malformed for site: test-site, page: test-page "
                rf"\(row=1, field=id, value=file-row-{re.escape(fullwidth_file_id)}\)"
            ),
        ):
            PageFileCollection.acquire(page)

    def test_acquire_empty(self):
        """ファイルなしの場合"""
        page = _page()
        page.id = 12345
        site = MagicMock()
        page.site = site

        response = MagicMock()
        response.json.return_value = {"body": "<div>No files</div>"}
        site.amc_request_with_retry.return_value = (response,)

        collection = PageFileCollection.acquire(page)

        assert len(collection) == 0
        assert collection.page == page

    def test_acquire_multiple_files(self):
        """複数ファイルの取得"""
        page = _page()
        page.id = 12345
        site = MagicMock()
        site.url = "https://test.wikidot.com"
        page.site = site

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <table class="page-files">
                    <tbody>
                        <tr id="file-row-100">
                            <td><a href="/local--files/test-page/file1.txt">file1.txt</a></td>
                            <td><span title="text/plain">TXT</span></td>
                            <td>500 Bytes</td>
                        </tr>
                        <tr id="file-row-101">
                            <td><a href="/local--files/test-page/file2.pdf">file2.pdf</a></td>
                            <td><span title="application/pdf">PDF</span></td>
                            <td>2 MB</td>
                        </tr>
                    </tbody>
                </table>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        collection = PageFileCollection.acquire(page)

        assert len(collection) == 2
        assert collection[0].name == "file1.txt"
        assert collection[1].name == "file2.pdf"

    def test_acquire_rejects_invalid_rows(self):
        """構造的に壊れたfile-rowは黙ってスキップしない"""
        page = _page()
        page.id = 12345
        site = MagicMock()
        site.url = "https://test.wikidot.com"
        page.site = site

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <table class="page-files">
                    <tbody>
                        <tr id="file-row-100">
                            <td><a href="/local--files/test-page/valid.txt">valid.txt</a></td>
                            <td><span title="text/plain">TXT</span></td>
                            <td>100 Bytes</td>
                        </tr>
                        <tr id="file-row-101">
                            <td>No link here</td>
                            <td></td>
                            <td></td>
                        </tr>
                        <tr id="file-row-102">
                            <td>Too few columns</td>
                        </tr>
                    </tbody>
                </table>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with pytest.raises(
            exceptions.NoElementException,
            match=r"Page file link is not found .*\(id=101, field=link\)",
        ):
            PageFileCollection.acquire(page)

    def test_acquire_ignores_nested_file_rows(self):
        """添付ファイル行内のネストした表は構造的なファイル行として扱わない"""
        page = _page()
        page.id = 12345
        site = MagicMock()
        site.url = "https://test.wikidot.com"
        page.site = site

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <table class="page-files">
                    <tbody>
                        <tr id="file-row-100">
                            <td>
                                <table>
                                    <tbody>
                                        <tr id="file-row-999">
                                            <td><a href="/local--files/test-page/fake.txt">fake.txt</a></td>
                                            <td><span title="text/fake">FAKE</span></td>
                                            <td>999 MB</td>
                                        </tr>
                                    </tbody>
                                </table>
                                <a href="/local--files/test-page/real.txt">real.txt</a>
                            </td>
                            <td><span title="text/plain">TXT</span></td>
                            <td>1 KB</td>
                        </tr>
                    </tbody>
                </table>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        collection = PageFileCollection.acquire(page)

        assert len(collection) == 1
        assert collection[0].id == 100
        assert collection[0].name == "real.txt"
        assert collection[0].mime_type == "text/plain"
        assert collection[0].size == 1000


class TestPageFile:
    """PageFileのテスト"""

    def test_init(self):
        """初期化"""
        page = _page()

        file = _page_file(page)

        assert file.page == page
        assert file.id == 123
        assert file.name == "test.txt"
        assert file.url == "https://example.com/test.txt"
        assert file.mime_type == "text/plain"
        assert file.size == 1024

    @pytest.mark.parametrize("page", [None, True, "test-page", {"fullname": "test-page"}, object()])
    def test_init_rejects_malformed_pages(self, page: object) -> None:
        """pageはPageだけ受け付ける"""
        bad_page: Any = page

        with pytest.raises(ValueError, match="page must be a Page"):
            PageFile(
                page=bad_page,
                id=123,
                name="test.txt",
                url="https://example.com/test.txt",
                mime_type="text/plain",
                size=1024,
            )

    @pytest.mark.parametrize("file_id", [None, True, "123", 123.0])
    def test_init_rejects_malformed_ids(self, file_id: object) -> None:
        """PageFileは整数IDだけ受け付ける"""
        page = _page()
        bad_file_id: Any = file_id

        with pytest.raises(ValueError, match="id must be an integer"):
            _page_file(page, file_id=bad_file_id)

    @pytest.mark.parametrize("file_id", [-1, -100])
    def test_init_rejects_negative_ids(self, file_id: int) -> None:
        """PageFile.idは負のIDを受け付けない"""
        page = _page()

        with pytest.raises(ValueError, match="id must be non-negative"):
            _page_file(page, file_id=file_id)

    def test_init_accepts_zero_id(self) -> None:
        """PageFile.idは0を非負IDとして保持できる"""
        page = _page()

        file = _page_file(page, file_id=0)

        assert file.id == 0

    @pytest.mark.parametrize(
        ("field", "value", "message"),
        [
            ("name", None, "name must be a string"),
            ("name", True, "name must be a string"),
            ("name", 123, "name must be a string"),
            ("name", [], "name must be a string"),
            ("url", None, "url must be a string"),
            ("url", True, "url must be a string"),
            ("url", 123, "url must be a string"),
            ("url", [], "url must be a string"),
            ("mime_type", None, "mime_type must be a string"),
            ("mime_type", True, "mime_type must be a string"),
            ("mime_type", 123, "mime_type must be a string"),
            ("mime_type", [], "mime_type must be a string"),
        ],
    )
    def test_init_rejects_malformed_text_fields(self, field: str, value: object, message: str) -> None:
        """PageFileは文字列のテキストフィールドだけ受け付ける"""
        page = _page()
        bad_value: Any = value

        with pytest.raises(ValueError, match=message):
            if field == "name":
                _page_file(page, name=bad_value)
            elif field == "url":
                _page_file(page, url=bad_value)
            else:
                _page_file(page, mime_type=bad_value)

    @pytest.mark.parametrize("name", ["", "   "])
    def test_init_rejects_blank_names(self, name: str) -> None:
        """PageFile.nameはblank文字列を受け付けない"""
        page = _page()

        with pytest.raises(ValueError, match="name must not be empty"):
            _page_file(page, name=name)

    def test_init_allows_blank_url_and_mime_type(self) -> None:
        """url/mime_typeのblank許容は既存フィクスチャ互換のため維持する"""
        page = _page()

        file = _page_file(page, url="", mime_type="")

        assert file.url == ""
        assert file.mime_type == ""

    @pytest.mark.parametrize("size", [None, True, "1024", 1024.0])
    def test_init_rejects_malformed_sizes(self, size: object) -> None:
        """PageFileは整数サイズだけ受け付ける"""
        page = _page()
        bad_size: Any = size

        with pytest.raises(ValueError, match="size must be an integer"):
            _page_file(page, size=bad_size)

    @pytest.mark.parametrize("size", [-1, -1024])
    def test_init_rejects_negative_sizes(self, size: int) -> None:
        """PageFile.sizeは負のバイト数を受け付けない"""
        page = _page()

        with pytest.raises(ValueError, match="size must be non-negative"):
            _page_file(page, size=size)

    def test_init_allows_zero_size(self) -> None:
        """PageFile.sizeは0バイト添付ファイルを保持できる"""
        page = _page()

        file = _page_file(page, size=0)

        assert file.size == 0

    def test_str(self):
        """文字列表現"""
        page = _page()

        file = _page_file(page)

        result = str(file)

        assert "PageFile" in result
        assert "id=123" in result
        assert "name=test.txt" in result
        assert "size=1024" in result
