"""RequestUtilのユニットテスト

リトライ機構を持つHTTPリクエスト関数のテストを行う。
"""

from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from wikidot.connector.ajax import AjaxModuleConnectorConfig
from wikidot.util.requestutil import RequestUtil


class TestRequestUtilEmpty:
    """空URL入力のテスト"""

    def test_empty_get_urls_returns_empty_without_client_config(self):
        """URLがないGETはクライアント設定なしで空結果を返す"""
        result = RequestUtil.request(object(), "GET", [])

        assert result == []

    def test_empty_post_urls_returns_empty_without_client_config(self):
        """URLがないPOSTはクライアント設定なしで空結果を返す"""
        result = RequestUtil.request(object(), "POST", [])

        assert result == []

    def test_empty_urls_still_validate_method(self):
        """URLがない場合も不正なHTTPメソッドは握りつぶさない"""
        with pytest.raises(ValueError, match="Invalid method"):
            RequestUtil.request(object(), "DELETE", [])

    @pytest.mark.parametrize("method", ["GET", "POST"])
    @pytest.mark.parametrize("return_exceptions", [None, "false", 0, 1])
    def test_empty_urls_reject_non_bool_return_exceptions_before_client_config(
        self, method: str, return_exceptions: Any
    ) -> None:
        """return_exceptionsは空URL短絡前に真偽値として検証する"""
        with pytest.raises(ValueError, match="return_exceptions must be a boolean"):
            RequestUtil.request(object(), method, [], return_exceptions=return_exceptions)


class TestRequestUtilClientReuse:
    """HTTPクライアント再利用のテスト"""

    @pytest.mark.parametrize("method", ["GET", "POST"])
    def test_batch_reuses_one_async_client(self, monkeypatch, method):
        """複数URLのバッチでAsyncClientをURLごとに作り直さない"""
        created_clients = []

        class FakeAsyncClient:
            def __init__(self, *, timeout):
                self.timeout = timeout
                created_clients.append(self)

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return None

            async def get(self, url, *, headers=None):
                return httpx.Response(200, request=httpx.Request("GET", url))

            async def post(self, url, *, headers=None):
                return httpx.Response(200, request=httpx.Request("POST", url))

        monkeypatch.setattr("wikidot.util.requestutil.httpx.AsyncClient", FakeAsyncClient)

        mock_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(
            attempt_limit=1,
            retry_interval=0.01,
        )

        results = RequestUtil.request(
            mock_client,
            method,
            ["https://example.com/test1", "https://example.com/test2"],
        )

        assert len(results) == 2
        assert len(created_clients) == 1


class TestRequestUtilGet:
    """RequestUtil.request GETメソッドのテスト"""

    def test_get_success(self, httpx_mock):
        """GET成功"""
        httpx_mock.add_response(url="https://example.com/test1", status_code=200)
        httpx_mock.add_response(url="https://example.com/test2", status_code=200)

        mock_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(
            attempt_limit=3,
            retry_interval=0.01,
        )

        results = RequestUtil.request(
            mock_client,
            "GET",
            ["https://example.com/test1", "https://example.com/test2"],
        )

        assert len(results) == 2
        assert all(isinstance(r, httpx.Response) for r in results)
        assert all(r.status_code == 200 for r in results)

    def test_get_sends_client_headers(self, httpx_mock):
        """Wikidot宛てGET時にクライアントのCookieヘッダを送る"""
        httpx_mock.add_response(url="https://test.wikidot.com/test", status_code=200)

        mock_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(
            attempt_limit=3,
            retry_interval=0.01,
        )
        mock_client.amc_client.header.get_header.return_value = {"Cookie": "WIKIDOT_SESSION_ID=abc;"}

        RequestUtil.request(mock_client, "GET", ["https://test.wikidot.com/test"])

        assert httpx_mock.get_requests()[0].headers["Cookie"] == "WIKIDOT_SESSION_ID=abc;"

    def test_get_does_not_send_client_headers_to_non_wikidot(self, httpx_mock):
        """非Wikidot宛てGETではセッションCookieを送らない"""
        httpx_mock.add_response(url="https://example.com/test", status_code=200)

        mock_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(
            attempt_limit=3,
            retry_interval=0.01,
        )
        mock_client.amc_client.header.get_header.return_value = {"Cookie": "WIKIDOT_SESSION_ID=abc;"}

        RequestUtil.request(mock_client, "GET", ["https://example.com/test"])

        assert "Cookie" not in httpx_mock.get_requests()[0].headers

    def test_get_retry_on_5xx(self, httpx_mock):
        """GET 5xxエラー後リトライ成功"""
        httpx_mock.add_response(url="https://example.com/test", status_code=500)
        httpx_mock.add_response(url="https://example.com/test", status_code=200)

        mock_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(
            attempt_limit=3,
            retry_interval=0.01,
        )

        results = RequestUtil.request(
            mock_client,
            "GET",
            ["https://example.com/test"],
        )

        assert len(results) == 1
        assert results[0].status_code == 200

    def test_get_no_retry_on_4xx(self, httpx_mock):
        """GET 4xxエラーはリトライしない"""
        httpx_mock.add_response(url="https://example.com/test", status_code=404)

        mock_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(
            attempt_limit=3,
            retry_interval=0.01,
        )

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            RequestUtil.request(
                mock_client,
                "GET",
                ["https://example.com/test"],
            )

        assert exc_info.value.response.status_code == 404

    def test_get_return_exceptions(self, httpx_mock):
        """return_exceptions=Trueで例外を返す"""
        httpx_mock.add_response(url="https://example.com/test", status_code=404)

        mock_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(
            attempt_limit=3,
            retry_interval=0.01,
        )

        results = RequestUtil.request(
            mock_client,
            "GET",
            ["https://example.com/test"],
            return_exceptions=True,
        )

        assert len(results) == 1
        assert isinstance(results[0], httpx.HTTPStatusError)

    def test_get_retry_on_timeout(self, httpx_mock):
        """GETタイムアウト後リトライ成功"""
        httpx_mock.add_exception(httpx.TimeoutException("Timeout"))
        httpx_mock.add_response(url="https://example.com/test", status_code=200)

        mock_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(
            attempt_limit=3,
            retry_interval=0.01,
        )

        results = RequestUtil.request(
            mock_client,
            "GET",
            ["https://example.com/test"],
        )

        assert len(results) == 1
        assert results[0].status_code == 200


class TestRequestUtilPost:
    """RequestUtil.request POSTメソッドのテスト"""

    def test_post_success(self, httpx_mock):
        """POST成功"""
        httpx_mock.add_response(url="https://example.com/test", status_code=200, method="POST")

        mock_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(
            attempt_limit=3,
            retry_interval=0.01,
        )

        results = RequestUtil.request(
            mock_client,
            "POST",
            ["https://example.com/test"],
        )

        assert len(results) == 1
        assert results[0].status_code == 200

    def test_post_sends_client_headers(self, httpx_mock):
        """Wikidot宛てPOST時にクライアントのCookieヘッダを送る"""
        httpx_mock.add_response(url="https://test.wikidot.com/test", status_code=200, method="POST")

        mock_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(
            attempt_limit=3,
            retry_interval=0.01,
        )
        mock_client.amc_client.header.get_header.return_value = {"Cookie": "WIKIDOT_SESSION_ID=abc;"}

        RequestUtil.request(mock_client, "POST", ["https://test.wikidot.com/test"])

        assert httpx_mock.get_requests()[0].headers["Cookie"] == "WIKIDOT_SESSION_ID=abc;"

    def test_post_does_not_send_client_headers_to_non_wikidot(self, httpx_mock):
        """非Wikidot宛てPOSTではセッションCookieを送らない"""
        httpx_mock.add_response(url="https://example.com/test", status_code=200, method="POST")

        mock_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(
            attempt_limit=3,
            retry_interval=0.01,
        )
        mock_client.amc_client.header.get_header.return_value = {"Cookie": "WIKIDOT_SESSION_ID=abc;"}

        RequestUtil.request(mock_client, "POST", ["https://example.com/test"])

        assert "Cookie" not in httpx_mock.get_requests()[0].headers

    def test_post_retry_on_5xx(self, httpx_mock):
        """POST 5xxエラー後リトライ成功"""
        httpx_mock.add_response(url="https://example.com/test", status_code=500, method="POST")
        httpx_mock.add_response(url="https://example.com/test", status_code=200, method="POST")

        mock_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(
            attempt_limit=3,
            retry_interval=0.01,
        )

        results = RequestUtil.request(
            mock_client,
            "POST",
            ["https://example.com/test"],
        )

        assert len(results) == 1
        assert results[0].status_code == 200

    def test_post_no_retry_on_4xx(self, httpx_mock):
        """POST 4xxエラーはリトライしない"""
        httpx_mock.add_response(url="https://example.com/test", status_code=400, method="POST")

        mock_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(
            attempt_limit=3,
            retry_interval=0.01,
        )

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            RequestUtil.request(
                mock_client,
                "POST",
                ["https://example.com/test"],
            )

        assert exc_info.value.response.status_code == 400

    def test_post_retry_on_timeout(self, httpx_mock):
        """POSTタイムアウト後リトライ成功"""
        httpx_mock.add_exception(httpx.TimeoutException("Timeout"), method="POST")
        httpx_mock.add_response(url="https://example.com/test", status_code=200, method="POST")

        mock_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(
            attempt_limit=3,
            retry_interval=0.01,
        )

        results = RequestUtil.request(
            mock_client,
            "POST",
            ["https://example.com/test"],
        )

        assert len(results) == 1
        assert results[0].status_code == 200


class TestRequestUtilInvalidMethod:
    """無効なメソッドのテスト"""

    def test_invalid_method_raises(self):
        """無効なメソッドでValueError"""
        mock_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(
            attempt_limit=3,
            retry_interval=0.01,
        )

        with pytest.raises(ValueError) as exc_info:
            RequestUtil.request(
                mock_client,
                "DELETE",
                ["https://example.com/test"],
            )

        assert "Invalid method" in str(exc_info.value)
