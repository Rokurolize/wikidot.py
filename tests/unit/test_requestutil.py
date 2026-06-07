"""RequestUtilのユニットテスト

リトライ機構を持つHTTPリクエスト関数のテストを行う。
"""

from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from wikidot.connector.ajax import AjaxModuleConnectorConfig, AjaxRequestHeader
from wikidot.module.client import Client
from wikidot.util.requestutil import RequestUtil


def _assert_response(result: httpx.Response | Exception) -> httpx.Response:
    assert isinstance(result, httpx.Response)
    return result


_DEFAULT_CONFIG = object()


def _mock_client(*, config: object = _DEFAULT_CONFIG, headers: dict[str, str] | None = None) -> Any:
    mock_client = object.__new__(Client)
    mock_client.amc_client = MagicMock()
    mock_client.amc_client.config = (
        AjaxModuleConnectorConfig(attempt_limit=3, retry_interval=0.01) if config is _DEFAULT_CONFIG else config
    )
    header: Any = AjaxRequestHeader()
    header.get_header = MagicMock(return_value={} if headers is None else headers)
    mock_client.amc_client.header = header
    return mock_client


class TestRequestUtilEmpty:
    """空URL入力のテスト"""

    def test_empty_get_urls_returns_empty_without_client_config(self):
        """URLがないGETはクライアント設定なしで空結果を返す"""
        client_without_config: Any = object()

        result = RequestUtil.request(client_without_config, "GET", [])

        assert result == []

    def test_empty_post_urls_returns_empty_without_client_config(self):
        """URLがないPOSTはクライアント設定なしで空結果を返す"""
        client_without_config: Any = object()

        result = RequestUtil.request(client_without_config, "POST", [])

        assert result == []

    def test_empty_urls_still_validate_method(self):
        """URLがない場合も不正なHTTPメソッドは握りつぶさない"""
        client_without_config: Any = object()

        with pytest.raises(ValueError, match="Invalid method"):
            RequestUtil.request(client_without_config, "DELETE", [])

    @pytest.mark.parametrize("method", ["GET", "POST"])
    @pytest.mark.parametrize("return_exceptions", [None, "false", 0, 1])
    def test_empty_urls_reject_non_bool_return_exceptions_before_client_config(
        self, method: str, return_exceptions: Any
    ) -> None:
        """return_exceptionsは空URL短絡前に真偽値として検証する"""
        client_without_config: Any = object()

        with pytest.raises(ValueError, match="return_exceptions must be a boolean"):
            RequestUtil.request(client_without_config, method, [], return_exceptions=return_exceptions)


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

        mock_client = _mock_client(
            config=AjaxModuleConnectorConfig(
                attempt_limit=1,
                retry_interval=0.01,
            )
        )

        results = RequestUtil.request(
            mock_client,
            method,
            ["https://example.com/test1", "https://example.com/test2"],
        )

        assert len(results) == 2
        assert len(created_clients) == 1


class TestRequestUtilConfigValidation:
    """RequestUtil.requestの設定値検証テスト"""

    @pytest.mark.parametrize("client", [None, True, "test-client", {"username": "test-user"}, object()])
    def test_rejects_malformed_client_before_config(self, httpx_mock, client: object) -> None:
        """非空URLリクエストはclientをAMC設定アクセス前に型検証する"""
        bad_client: Any = client

        with pytest.raises(ValueError, match="client must be a Client"):
            RequestUtil.request(bad_client, "GET", ["https://example.com/test"])

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("method", ["GET", "POST"])
    @pytest.mark.parametrize("header", [None, object(), {}, "header", True])
    def test_rejects_invalid_header_object_before_request(
        self,
        httpx_mock,
        method: str,
        header: Any,
    ) -> None:
        """直接URLリクエストもAMCヘッダオブジェクトをHTTP前に型検証する"""
        mock_client = _mock_client(config=AjaxModuleConnectorConfig(retry_interval=0))
        mock_client.amc_client.header = header

        with pytest.raises(ValueError, match="header must be AjaxRequestHeader"):
            RequestUtil.request(mock_client, method, ["https://test.wikidot.com/test"])

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("method", ["GET", "POST"])
    @pytest.mark.parametrize("config", [None, object(), {}, "config", True])
    def test_rejects_invalid_config_object_before_request(
        self,
        httpx_mock,
        method: str,
        config: Any,
    ) -> None:
        """直接URLリクエストもAMC設定オブジェクトをHTTP前に型検証する"""
        mock_client = _mock_client(config=config)

        with pytest.raises(ValueError, match="config must be AjaxModuleConnectorConfig"):
            RequestUtil.request(mock_client, method, ["https://example.com/test"])

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("method", ["GET", "POST"])
    @pytest.mark.parametrize("request_timeout", [None, True, "1", 0, -0.1])
    def test_rejects_invalid_request_timeout_before_request(
        self,
        httpx_mock,
        method: str,
        request_timeout: Any,
    ) -> None:
        """request_timeoutはHTTPリクエスト前に正の数値として検証する"""
        config = AjaxModuleConnectorConfig(retry_interval=0)
        config.request_timeout = request_timeout
        mock_client = _mock_client(config=config)

        with pytest.raises(ValueError, match="request_timeout must be a positive number"):
            RequestUtil.request(mock_client, method, ["https://example.com/test"])

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("method", ["GET", "POST"])
    @pytest.mark.parametrize("field", ["attempt_limit", "semaphore_limit"])
    @pytest.mark.parametrize("value", [None, True, "1", 0, -1, 1.5])
    def test_rejects_invalid_positive_integer_config_before_request(
        self,
        httpx_mock,
        method: str,
        field: str,
        value: Any,
    ) -> None:
        """attempt/semaphore設定はHTTPリクエスト前に正の整数として検証する"""
        config = AjaxModuleConnectorConfig(retry_interval=0)
        setattr(config, field, value)
        mock_client = _mock_client(config=config)

        with pytest.raises(ValueError, match=rf"{field} must be a positive integer"):
            RequestUtil.request(mock_client, method, ["https://example.com/test"])

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("method", ["GET", "POST"])
    @pytest.mark.parametrize("field", ["retry_interval", "max_backoff", "backoff_factor"])
    @pytest.mark.parametrize("value", [None, True, "1", -0.1])
    def test_rejects_invalid_retry_number_config_before_request(
        self,
        httpx_mock,
        method: str,
        field: str,
        value: Any,
    ) -> None:
        """retry/backoff設定はHTTPリクエスト前に非負の数値として検証する"""
        config = AjaxModuleConnectorConfig(retry_interval=0)
        setattr(config, field, value)
        mock_client = _mock_client(config=config)

        with pytest.raises(ValueError, match=rf"{field} must be a non-negative number"):
            RequestUtil.request(mock_client, method, ["https://example.com/test"])

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("method", ["GET", "POST"])
    def test_accepts_zero_backoff_controls(self, httpx_mock, method: str) -> None:
        """backoff関連の0設定は既存の即時リトライ用途として許可する"""
        httpx_mock.add_response(url="https://example.com/test", status_code=200, method=method)

        mock_client = _mock_client(
            config=AjaxModuleConnectorConfig(
                retry_interval=0,
                max_backoff=0,
                backoff_factor=0,
            )
        )

        results = RequestUtil.request(mock_client, method, ["https://example.com/test"])

        assert len(results) == 1
        assert _assert_response(results[0]).status_code == 200


class TestRequestUtilGet:
    """RequestUtil.request GETメソッドのテスト"""

    def test_get_success(self, httpx_mock):
        """GET成功"""
        httpx_mock.add_response(url="https://example.com/test1", status_code=200)
        httpx_mock.add_response(url="https://example.com/test2", status_code=200)

        mock_client = _mock_client()

        results = RequestUtil.request(
            mock_client,
            "GET",
            ["https://example.com/test1", "https://example.com/test2"],
        )

        assert len(results) == 2
        responses = [_assert_response(result) for result in results]
        assert all(response.status_code == 200 for response in responses)

    def test_get_sends_client_headers(self, httpx_mock):
        """Wikidot宛てGET時にクライアントのCookieヘッダを送る"""
        httpx_mock.add_response(url="https://test.wikidot.com/test", status_code=200)

        mock_client = _mock_client(headers={"Cookie": "WIKIDOT_SESSION_ID=abc;"})

        RequestUtil.request(mock_client, "GET", ["https://test.wikidot.com/test"])

        assert httpx_mock.get_requests()[0].headers["Cookie"] == "WIKIDOT_SESSION_ID=abc;"

    def test_get_does_not_send_client_headers_to_non_wikidot(self, httpx_mock):
        """非Wikidot宛てGETではセッションCookieを送らない"""
        httpx_mock.add_response(url="https://example.com/test", status_code=200)

        mock_client = _mock_client(headers={"Cookie": "WIKIDOT_SESSION_ID=abc;"})

        RequestUtil.request(mock_client, "GET", ["https://example.com/test"])

        assert "Cookie" not in httpx_mock.get_requests()[0].headers

    def test_get_retry_on_5xx(self, httpx_mock):
        """GET 5xxエラー後リトライ成功"""
        httpx_mock.add_response(url="https://example.com/test", status_code=500)
        httpx_mock.add_response(url="https://example.com/test", status_code=200)

        mock_client = _mock_client()

        results = RequestUtil.request(
            mock_client,
            "GET",
            ["https://example.com/test"],
        )

        assert len(results) == 1
        assert _assert_response(results[0]).status_code == 200

    def test_get_no_retry_on_4xx(self, httpx_mock):
        """GET 4xxエラーはリトライしない"""
        httpx_mock.add_response(url="https://example.com/test", status_code=404)

        mock_client = _mock_client()

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

        mock_client = _mock_client()

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

        mock_client = _mock_client()

        results = RequestUtil.request(
            mock_client,
            "GET",
            ["https://example.com/test"],
        )

        assert len(results) == 1
        assert _assert_response(results[0]).status_code == 200


class TestRequestUtilPost:
    """RequestUtil.request POSTメソッドのテスト"""

    def test_post_success(self, httpx_mock):
        """POST成功"""
        httpx_mock.add_response(url="https://example.com/test", status_code=200, method="POST")

        mock_client = _mock_client()

        results = RequestUtil.request(
            mock_client,
            "POST",
            ["https://example.com/test"],
        )

        assert len(results) == 1
        assert _assert_response(results[0]).status_code == 200

    def test_post_sends_client_headers(self, httpx_mock):
        """Wikidot宛てPOST時にクライアントのCookieヘッダを送る"""
        httpx_mock.add_response(url="https://test.wikidot.com/test", status_code=200, method="POST")

        mock_client = _mock_client(headers={"Cookie": "WIKIDOT_SESSION_ID=abc;"})

        RequestUtil.request(mock_client, "POST", ["https://test.wikidot.com/test"])

        assert httpx_mock.get_requests()[0].headers["Cookie"] == "WIKIDOT_SESSION_ID=abc;"

    def test_post_does_not_send_client_headers_to_non_wikidot(self, httpx_mock):
        """非Wikidot宛てPOSTではセッションCookieを送らない"""
        httpx_mock.add_response(url="https://example.com/test", status_code=200, method="POST")

        mock_client = _mock_client(headers={"Cookie": "WIKIDOT_SESSION_ID=abc;"})

        RequestUtil.request(mock_client, "POST", ["https://example.com/test"])

        assert "Cookie" not in httpx_mock.get_requests()[0].headers

    def test_post_retry_on_5xx(self, httpx_mock):
        """POST 5xxエラー後リトライ成功"""
        httpx_mock.add_response(url="https://example.com/test", status_code=500, method="POST")
        httpx_mock.add_response(url="https://example.com/test", status_code=200, method="POST")

        mock_client = _mock_client()

        results = RequestUtil.request(
            mock_client,
            "POST",
            ["https://example.com/test"],
        )

        assert len(results) == 1
        assert _assert_response(results[0]).status_code == 200

    def test_post_no_retry_on_4xx(self, httpx_mock):
        """POST 4xxエラーはリトライしない"""
        httpx_mock.add_response(url="https://example.com/test", status_code=400, method="POST")

        mock_client = _mock_client()

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

        mock_client = _mock_client()

        results = RequestUtil.request(
            mock_client,
            "POST",
            ["https://example.com/test"],
        )

        assert len(results) == 1
        assert _assert_response(results[0]).status_code == 200


class TestRequestUtilInvalidMethod:
    """無効なメソッドのテスト"""

    @pytest.mark.parametrize("method", [None, True, 1, object()])
    def test_rejects_non_string_method_before_url_handling(self, method: Any) -> None:
        """methodは大文字化する前に文字列として検証する"""
        client_without_config: Any = object()

        with pytest.raises(ValueError, match="method must be a string"):
            RequestUtil.request(client_without_config, method, [])

    def test_invalid_method_raises(self):
        """無効なメソッドでValueError"""
        mock_client = _mock_client()

        with pytest.raises(ValueError) as exc_info:
            RequestUtil.request(
                mock_client,
                "DELETE",
                ["https://example.com/test"],
            )

        assert "Invalid method" in str(exc_info.value)


class TestRequestUtilUrlValidation:
    """RequestUtil.requestのURL入力検証テスト"""

    @pytest.mark.parametrize("urls", [(), "https://example.com/test", {"url": "https://example.com/test"}, object()])
    def test_rejects_non_list_urls_before_client_config(self, urls: Any) -> None:
        """urlsは空判定やclient設定アクセスより前にlistとして検証する"""
        client_without_config: Any = object()

        with pytest.raises(ValueError, match="urls must be a list of strings"):
            RequestUtil.request(client_without_config, "GET", urls)

    @pytest.mark.parametrize("urls", [[123], [None], [True], [object()]])
    def test_rejects_non_string_url_entries_before_client_config(self, urls: Any) -> None:
        """urlsの各要素はclient設定アクセスより前に文字列として検証する"""
        client_without_config: Any = object()

        with pytest.raises(ValueError, match="urls must be a list of strings"):
            RequestUtil.request(client_without_config, "GET", urls)

    @pytest.mark.parametrize("url", ["", "not-a-url", "/relative/path", "ftp://example.com/test", "https://"])
    def test_rejects_malformed_url_strings_before_client_validation(self, url: str) -> None:
        """URL文字列はclient検証より前に絶対HTTP(S) URLとして検証する"""
        client_without_config: Any = object()

        with pytest.raises(ValueError, match=r"urls must be absolute HTTP\(S\) URLs"):
            RequestUtil.request(client_without_config, "GET", [url])
