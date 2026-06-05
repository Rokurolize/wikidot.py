"""PageFileモジュールのユニットテスト"""

from unittest.mock import MagicMock

import pytest

from wikidot.common import exceptions
from wikidot.module.page_file import PageFile, PageFileCollection


class TestPageFileCollection:
    """PageFileCollectionのテスト"""

    def test_init_with_page(self):
        """ページを指定して初期化"""
        page = MagicMock()

        collection = PageFileCollection(page=page, files=[])

        assert collection.page == page
        assert len(collection) == 0

    def test_init_infers_page_from_files(self):
        """ファイルリストからページを推測"""
        page = MagicMock()
        file1 = PageFile(page=page, id=1, name="test.txt", url="", mime_type="", size=0)

        collection = PageFileCollection(page=None, files=[file1])

        assert collection.page == page

    def test_init_with_files(self):
        """ファイルリストを指定して初期化"""
        page = MagicMock()
        file1 = PageFile(page=page, id=1, name="test.txt", url="", mime_type="", size=100)
        file2 = PageFile(page=page, id=2, name="image.png", url="", mime_type="", size=200)

        collection = PageFileCollection(page=page, files=[file1, file2])

        assert len(collection) == 2

    def test_iter(self):
        """イテレーション"""
        page = MagicMock()
        file1 = PageFile(page=page, id=1, name="a.txt", url="", mime_type="", size=0)
        file2 = PageFile(page=page, id=2, name="b.txt", url="", mime_type="", size=0)

        collection = PageFileCollection(page=page, files=[file1, file2])

        files = list(collection)
        assert len(files) == 2
        assert files[0].name == "a.txt"
        assert files[1].name == "b.txt"

    def test_find_existing_by_id(self):
        """IDで存在するファイルを検索"""
        page = MagicMock()
        file1 = PageFile(page=page, id=123, name="test.txt", url="", mime_type="", size=0)
        file2 = PageFile(page=page, id=456, name="other.txt", url="", mime_type="", size=0)

        collection = PageFileCollection(page=page, files=[file1, file2])

        result = collection.find(123)

        assert result is not None
        assert result.name == "test.txt"

    def test_find_nonexistent_by_id(self):
        """存在しないIDの検索でNone"""
        page = MagicMock()
        file1 = PageFile(page=page, id=123, name="test.txt", url="", mime_type="", size=0)

        collection = PageFileCollection(page=page, files=[file1])

        result = collection.find(999)

        assert result is None

    def test_find_by_name_existing(self):
        """名前で存在するファイルを検索"""
        page = MagicMock()
        file1 = PageFile(page=page, id=1, name="image.png", url="", mime_type="", size=0)
        file2 = PageFile(page=page, id=2, name="document.pdf", url="", mime_type="", size=0)

        collection = PageFileCollection(page=page, files=[file1, file2])

        result = collection.find_by_name("document.pdf")

        assert result is not None
        assert result.id == 2

    def test_find_by_name_nonexistent(self):
        """存在しない名前の検索でNone"""
        page = MagicMock()
        file1 = PageFile(page=page, id=1, name="image.png", url="", mime_type="", size=0)

        collection = PageFileCollection(page=page, files=[file1])

        result = collection.find_by_name("nonexistent.txt")

        assert result is None


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

    def test_acquire_skips_cached_page_files(self):
        """取得済みpage.filesは直接取得でも再取得しない"""
        page = MagicMock()
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
        site.amc_request_with_retry = MagicMock(return_value=(None,))

        collection = PageFileCollection.acquire(page)

        assert collection is cached_collection
        site.amc_request.assert_not_called()
        site.amc_request_with_retry.assert_not_called()

    def test_acquire_uses_retry_aware_amc(self):
        """直接ファイル取得でもリトライ対応AMCを使う"""
        page = MagicMock()
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
        page = MagicMock()
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
        page = MagicMock()
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

    def test_acquire_success(self):
        """ファイル取得成功"""
        page = MagicMock()
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
        page = MagicMock()
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
        page = MagicMock()
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

    def test_acquire_requires_file_mime_title(self):
        """構造的に有効な添付ファイル行でMIME titleが欠落した場合は文脈付きで失敗する"""
        page = MagicMock()
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
        page = MagicMock()
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

    def test_acquire_requires_file_link_href(self):
        """構造的に有効な添付ファイル行でhrefが欠落した場合は文脈付きで失敗する"""
        page = MagicMock()
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

    def test_acquire_skips_malformed_file_row_id(self):
        """不正なfile-row IDはパース対象から除外する"""
        page = MagicMock()
        page.id = 12345
        site = MagicMock()
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

        collection = PageFileCollection.acquire(page)

        assert len(collection) == 1
        assert collection[0].id == 101
        assert collection[0].name == "good.txt"

    def test_acquire_empty(self):
        """ファイルなしの場合"""
        page = MagicMock()
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
        page = MagicMock()
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

    def test_acquire_skips_invalid_rows(self):
        """無効な行はスキップ"""
        page = MagicMock()
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

        collection = PageFileCollection.acquire(page)

        assert len(collection) == 1
        assert collection[0].name == "valid.txt"

    def test_acquire_ignores_nested_file_rows(self):
        """添付ファイル行内のネストした表は構造的なファイル行として扱わない"""
        page = MagicMock()
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
        page = MagicMock()

        file = PageFile(
            page=page,
            id=123,
            name="test.txt",
            url="https://example.com/test.txt",
            mime_type="text/plain",
            size=1024,
        )

        assert file.page == page
        assert file.id == 123
        assert file.name == "test.txt"
        assert file.url == "https://example.com/test.txt"
        assert file.mime_type == "text/plain"
        assert file.size == 1024

    def test_str(self):
        """文字列表現"""
        page = MagicMock()

        file = PageFile(
            page=page,
            id=123,
            name="test.txt",
            url="https://example.com/test.txt",
            mime_type="text/plain",
            size=1024,
        )

        result = str(file)

        assert "PageFile" in result
        assert "id=123" in result
        assert "name=test.txt" in result
        assert "size=1024" in result
