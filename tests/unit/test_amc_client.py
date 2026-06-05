"""AMCクライアントのユニットテスト"""

import copy
from typing import Any

import pytest
from pytest_httpx import HTTPXMock

from wikidot.common.exceptions import (
    AMCHttpStatusCodeException,
    ForbiddenException,
    NotFoundException,
    ResponseDataException,
    WikidotStatusCodeException,
)
from wikidot.connector.ajax import (
    AjaxModuleConnectorClient,
    AjaxModuleConnectorConfig,
    AjaxRequestHeader,
)


class TestAjaxRequestHeader:
    """AjaxRequestHeaderのテスト"""

    def test_default_values(self) -> None:
        """デフォルト値が正しく設定される"""
        header = AjaxRequestHeader()

        assert header.content_type == "application/x-www-form-urlencoded; charset=UTF-8"
        assert header.user_agent == "WikidotPy"
        assert header.referer == "https://www.wikidot.com/"
        assert header.cookie == {"wikidot_token7": 123456}

    def test_custom_values(self) -> None:
        """カスタム値が正しく設定される"""
        header = AjaxRequestHeader(
            content_type="text/plain",
            user_agent="CustomAgent",
            referer="https://example.com/",
            cookie={"session": "abc123"},
        )

        assert header.content_type == "text/plain"
        assert header.user_agent == "CustomAgent"
        assert header.referer == "https://example.com/"
        assert "session" in header.cookie
        assert "wikidot_token7" in header.cookie

    @pytest.mark.parametrize("name", ["", " ", "bad name", "bad=name", "bad;name", "bad\nname"])
    def test_custom_cookie_rejects_invalid_cookie_names(self, name: str) -> None:
        """初期Cookie名が不正な場合は拒否される"""
        with pytest.raises(ValueError, match="cookie name must be a non-empty string without whitespace, '=' or ';'"):
            AjaxRequestHeader(cookie={name: "value"})

    @pytest.mark.parametrize("value", ["bad value", "bad;value", "bad\nvalue", "bad\tvalue"])
    def test_custom_cookie_rejects_invalid_cookie_values(self, value: str) -> None:
        """初期Cookie値がヘッダ構文を壊す場合は拒否される"""
        with pytest.raises(ValueError, match="cookie value must serialize without whitespace or ';'"):
            AjaxRequestHeader(cookie={"session": value})

    def test_set_cookie(self) -> None:
        """Cookieを追加できる"""
        header = AjaxRequestHeader()
        header.set_cookie("new_cookie", "value")

        assert header.cookie["new_cookie"] == "value"

    def test_set_cookie_preserves_integer_and_equals_values(self) -> None:
        """既存の数値トークン値と=を含む不透明な値は保持される"""
        header = AjaxRequestHeader()

        header.set_cookie("wikidot_token7", 987654)
        header.set_cookie("session", "abc=def")

        assert header.cookie["wikidot_token7"] == 987654
        assert header.cookie["session"] == "abc=def"
        assert "wikidot_token7=987654" in header.get_header()["Cookie"]
        assert "session=abc=def" in header.get_header()["Cookie"]

    @pytest.mark.parametrize("name", ["", " ", "bad name", "bad=name", "bad;name", "bad\nname"])
    def test_set_cookie_rejects_invalid_cookie_names_without_mutating_header(self, name: str) -> None:
        """不正なCookie名はヘッダ状態を変更する前に拒否される"""
        header = AjaxRequestHeader()
        before = copy.deepcopy(header.cookie)

        with pytest.raises(ValueError, match="cookie name must be a non-empty string without whitespace, '=' or ';'"):
            header.set_cookie(name, "value")

        assert header.cookie == before

    @pytest.mark.parametrize("value", ["bad value", "bad;value", "bad\nvalue", "bad\tvalue"])
    def test_set_cookie_rejects_invalid_cookie_values_without_mutating_header(self, value: str) -> None:
        """不正なCookie値はヘッダ状態を変更する前に拒否される"""
        header = AjaxRequestHeader()
        before = copy.deepcopy(header.cookie)

        with pytest.raises(ValueError, match="cookie value must serialize without whitespace or ';'"):
            header.set_cookie("session", value)

        assert header.cookie == before

    def test_set_cookie_rejects_non_string_cookie_name(self) -> None:
        """Cookie名は文字列だけを受け付ける"""
        header = AjaxRequestHeader()

        with pytest.raises(TypeError, match="cookie name must be str"):
            header.set_cookie(123, "value")

    def test_delete_cookie(self) -> None:
        """Cookieを削除できる"""
        header = AjaxRequestHeader(cookie={"to_delete": "value"})
        header.delete_cookie("to_delete")

        assert "to_delete" not in header.cookie

    @pytest.mark.parametrize("name", ["", "bad\nname"])
    def test_delete_cookie_rejects_invalid_cookie_names(self, name: str) -> None:
        """不正なCookie名は削除操作でも拒否される"""
        header = AjaxRequestHeader()

        with pytest.raises(ValueError, match="cookie name must be a non-empty string without whitespace, '=' or ';'"):
            header.delete_cookie(name)

    def test_delete_missing_cookie_is_noop(self) -> None:
        """存在しないCookie削除は例外にしない"""
        header = AjaxRequestHeader()

        header.delete_cookie("missing")

        assert header.cookie == {"wikidot_token7": 123456}

    def test_get_header(self) -> None:
        """HTTPヘッダ辞書を取得できる"""
        header = AjaxRequestHeader()
        result = header.get_header()

        assert "Content-Type" in result
        assert "User-Agent" in result
        assert "Referer" in result
        assert "Cookie" in result
        assert "wikidot_token7=123456" in result["Cookie"]


class TestAjaxModuleConnectorConfig:
    """AjaxModuleConnectorConfigのテスト"""

    def test_default_values(self) -> None:
        """デフォルト値が正しく設定される"""
        config = AjaxModuleConnectorConfig()

        assert config.request_timeout == 20
        assert config.attempt_limit == 5
        assert config.retry_interval == 1.0
        assert config.max_backoff == 60.0
        assert config.backoff_factor == 2.0
        assert config.semaphore_limit == 10

    def test_custom_values(self) -> None:
        """カスタム値が正しく設定される"""
        config = AjaxModuleConnectorConfig(
            request_timeout=30,
            attempt_limit=5,
            retry_interval=2.0,
            max_backoff=120.0,
            backoff_factor=3.0,
            semaphore_limit=20,
        )

        assert config.request_timeout == 30
        assert config.attempt_limit == 5
        assert config.retry_interval == 2.0
        assert config.max_backoff == 120.0
        assert config.backoff_factor == 3.0
        assert config.semaphore_limit == 20


class TestAjaxModuleConnectorClientInit:
    """AjaxModuleConnectorClient初期化のテスト"""

    def test_www_is_always_ssl(self, httpx_mock: HTTPXMock) -> None:
        """wwwサイトは常にSSL対応"""
        client = AjaxModuleConnectorClient(site_name="www")

        assert client.ssl_supported is True
        assert client.site_name == "www"

    def test_site_with_ssl_redirect(self, httpx_mock: HTTPXMock) -> None:
        """HTTPSリダイレクトがあるサイトはSSL対応"""
        httpx_mock.add_response(
            url="http://test-site.wikidot.com",
            status_code=301,
            headers={"Location": "https://test-site.wikidot.com"},
        )

        client = AjaxModuleConnectorClient(site_name="test-site")

        assert client.ssl_supported is True

    def test_site_without_ssl(self, httpx_mock: HTTPXMock) -> None:
        """HTTPSリダイレクトがないサイトはSSL非対応"""
        httpx_mock.add_response(
            url="http://test-site.wikidot.com",
            status_code=200,
        )

        client = AjaxModuleConnectorClient(site_name="test-site")

        assert client.ssl_supported is False

    def test_site_not_found(self, httpx_mock: HTTPXMock) -> None:
        """存在しないサイトはNotFoundException"""
        httpx_mock.add_response(
            url="http://nonexistent.wikidot.com",
            status_code=404,
        )

        with pytest.raises(NotFoundException):
            AjaxModuleConnectorClient(site_name="nonexistent")

    def test_invalid_site_name_rejected_before_request(self, httpx_mock: HTTPXMock) -> None:
        """ホストを逸脱し得るsite_nameはリクエスト前に拒否する"""
        with pytest.raises(ValueError, match="Invalid Wikidot site UNIX name"):
            AjaxModuleConnectorClient(site_name="127.0.0.1:8000#")

        assert httpx_mock.get_requests() == []


class TestAjaxModuleConnectorClientRequest:
    """AjaxModuleConnectorClient.requestのテスト"""

    def test_successful_request(self, httpx_mock: HTTPXMock) -> None:
        """成功するAMCリクエスト"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "ok", "body": "<div>test</div>", "CURRENT_TIMESTAMP": 1234567890},
        )

        client = AjaxModuleConnectorClient(site_name="www")
        responses = client.request([{"moduleName": "TestModule"}])

        assert len(responses) == 1
        assert responses[0].json()["status"] == "ok"

    def test_request_invalid_override_site_name_rejected(self, httpx_mock: HTTPXMock) -> None:
        """request時のsite_name上書きもリクエスト前に検証する"""
        client = AjaxModuleConnectorClient(site_name="www")

        with pytest.raises(ValueError, match="Invalid Wikidot site UNIX name"):
            client.request([{"moduleName": "TestModule"}], site_name="127.0.0.1:8000#")

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("return_exceptions", [None, "false", 0, 1])
    def test_request_rejects_non_bool_return_exceptions_before_request(
        self,
        httpx_mock: HTTPXMock,
        return_exceptions: Any,
    ) -> None:
        """return_exceptionsは真偽値だけを受け付ける"""
        client = AjaxModuleConnectorClient(site_name="www")

        with pytest.raises(ValueError, match="return_exceptions must be a boolean"):
            client.request([], return_exceptions=return_exceptions)

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("field", ["attempt_limit", "semaphore_limit"])
    @pytest.mark.parametrize("value", [None, True, "1", 0, -1, 1.5])
    def test_request_rejects_invalid_positive_integer_config_before_request(
        self,
        httpx_mock: HTTPXMock,
        field: str,
        value: Any,
    ) -> None:
        """AMC実行制御の整数設定はリクエスト前に検証する"""
        config = AjaxModuleConnectorConfig(retry_interval=0)
        setattr(config, field, value)
        client = AjaxModuleConnectorClient(site_name="www", config=config)

        with pytest.raises(ValueError, match=rf"{field} must be a positive integer"):
            client.request([{"moduleName": "TestModule"}])

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("request_timeout", [None, True, "1", 0, -0.1])
    def test_request_rejects_invalid_positive_timeout_config_before_request(
        self,
        httpx_mock: HTTPXMock,
        request_timeout: Any,
    ) -> None:
        """AMCのtimeout設定は正の数値だけを受け付ける"""
        config = AjaxModuleConnectorConfig(request_timeout=request_timeout, retry_interval=0)
        client = AjaxModuleConnectorClient(site_name="www", config=config)

        with pytest.raises(ValueError, match="request_timeout must be a positive number"):
            client.request([{"moduleName": "TestModule"}])

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("field", ["retry_interval", "max_backoff", "backoff_factor"])
    @pytest.mark.parametrize("value", [None, True, "1", -0.1])
    def test_request_rejects_invalid_retry_number_config_before_request(
        self,
        httpx_mock: HTTPXMock,
        field: str,
        value: Any,
    ) -> None:
        """AMCのretry/backoff設定は非負の数値だけを受け付ける"""
        config = AjaxModuleConnectorConfig(retry_interval=0)
        setattr(config, field, value)
        client = AjaxModuleConnectorClient(site_name="www", config=config)

        with pytest.raises(ValueError, match=rf"{field} must be a non-negative number"):
            client.request([{"moduleName": "TestModule"}])

        assert httpx_mock.get_requests() == []

    def test_request_accepts_zero_backoff_controls(self, httpx_mock: HTTPXMock) -> None:
        """backoff関連の0設定は既存の即時リトライ用途として許可する"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "ok", "body": ""},
        )

        config = AjaxModuleConnectorConfig(retry_interval=0, max_backoff=0, backoff_factor=0)
        client = AjaxModuleConnectorClient(site_name="www", config=config)
        responses = client.request([{"moduleName": "TestModule"}])

        assert len(responses) == 1
        assert responses[0].json()["status"] == "ok"

    def test_request_does_not_mutate_body(self, httpx_mock: HTTPXMock) -> None:
        """AMCトークン追加で呼び出し元のbodyを変更しない"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "ok", "body": ""},
        )

        body = {"moduleName": "TestModule"}
        client = AjaxModuleConnectorClient(site_name="www")
        client.request([body])

        assert body == {"moduleName": "TestModule"}
        assert b"wikidot_token7=123456" in httpx_mock.get_requests()[0].content

    def test_request_preserves_explicit_wikidot_token(self, httpx_mock: HTTPXMock) -> None:
        """呼び出し元が指定したwikidot_token7を上書きしない"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "ok", "body": ""},
        )

        body = {"moduleName": "TestModule", "wikidot_token7": 987654}
        client = AjaxModuleConnectorClient(site_name="www")
        client.request([body])

        assert body == {"moduleName": "TestModule", "wikidot_token7": 987654}
        assert b"wikidot_token7=987654" in httpx_mock.get_requests()[0].content
        assert b"wikidot_token7=123456" not in httpx_mock.get_requests()[0].content

    def test_request_uses_header_wikidot_token_by_default(self, httpx_mock: HTTPXMock) -> None:
        """body未指定時は現在のヘッダCookieのwikidot_token7を使う"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "ok", "body": ""},
        )

        client = AjaxModuleConnectorClient(site_name="www")
        client.header.set_cookie("wikidot_token7", 987654)
        client.request([{"moduleName": "TestModule"}])

        request = httpx_mock.get_requests()[0]
        assert "wikidot_token7=987654" in request.headers["Cookie"]
        assert b"wikidot_token7=987654" in request.content
        assert b"wikidot_token7=123456" not in request.content

    def test_multiple_requests(self, httpx_mock: HTTPXMock) -> None:
        """複数リクエストを並行処理"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "ok", "body": "1"},
        )
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "ok", "body": "2"},
        )

        client = AjaxModuleConnectorClient(site_name="www")
        responses = client.request(
            [
                {"moduleName": "Module1"},
                {"moduleName": "Module2"},
            ]
        )

        assert len(responses) == 2

    def test_retry_on_try_again(self, httpx_mock: HTTPXMock) -> None:
        """try_againでリトライ"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "try_again"},
        )
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "ok", "body": ""},
        )

        config = AjaxModuleConnectorConfig(retry_interval=0)
        client = AjaxModuleConnectorClient(site_name="www", config=config)
        responses = client.request([{"moduleName": "Test"}])

        assert len(httpx_mock.get_requests()) == 2
        assert responses[0].json()["status"] == "ok"

    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    def test_max_retry_exceeded(self, httpx_mock: HTTPXMock) -> None:
        """リトライ上限超過でWikidotStatusCodeException"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "try_again"},
        )

        config = AjaxModuleConnectorConfig(attempt_limit=2, retry_interval=0)
        client = AjaxModuleConnectorClient(site_name="www", config=config)

        with pytest.raises(WikidotStatusCodeException):
            client.request([{"moduleName": "Test"}])

    def test_no_permission_error(self, httpx_mock: HTTPXMock) -> None:
        """no_permissionでForbiddenException"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "no_permission"},
        )

        client = AjaxModuleConnectorClient(site_name="www")

        with pytest.raises(ForbiddenException):
            client.request([{"moduleName": "RestrictedModule"}])

    def test_other_error_status(self, httpx_mock: HTTPXMock) -> None:
        """その他のエラーステータスでWikidotStatusCodeException"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "some_error", "message": "Something went wrong"},
        )

        client = AjaxModuleConnectorClient(site_name="www")

        with pytest.raises(WikidotStatusCodeException):
            client.request([{"moduleName": "Test"}])

    def test_http_error_retry(self, httpx_mock: HTTPXMock) -> None:
        """HTTPエラーでリトライ"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            status_code=500,
        )
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "ok", "body": ""},
        )

        config = AjaxModuleConnectorConfig(retry_interval=0)
        client = AjaxModuleConnectorClient(site_name="www", config=config)
        client.request([{"moduleName": "Test"}])

        assert len(httpx_mock.get_requests()) == 2

    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    def test_http_error_max_retry(self, httpx_mock: HTTPXMock) -> None:
        """HTTPエラーでリトライ上限超過"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            status_code=500,
        )

        config = AjaxModuleConnectorConfig(attempt_limit=2, retry_interval=0)
        client = AjaxModuleConnectorClient(site_name="www", config=config)

        with pytest.raises(AMCHttpStatusCodeException):
            client.request([{"moduleName": "Test"}])

    def test_retry_on_non_json_response(self, httpx_mock: HTTPXMock) -> None:
        """非JSONレスポンスでリトライ"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            text="",  # 空レスポンス（JSONパースエラー）
        )
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "ok", "body": ""},
        )

        config = AjaxModuleConnectorConfig(retry_interval=0)
        client = AjaxModuleConnectorClient(site_name="www", config=config)
        responses = client.request([{"moduleName": "Test"}])

        assert len(httpx_mock.get_requests()) == 2
        assert responses[0].json()["status"] == "ok"

    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    def test_non_json_response_max_retry(self, httpx_mock: HTTPXMock) -> None:
        """非JSONレスポンスでリトライ上限超過"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            text="not a json",
        )

        config = AjaxModuleConnectorConfig(attempt_limit=2, retry_interval=0)
        client = AjaxModuleConnectorClient(site_name="www", config=config)

        with pytest.raises(ResponseDataException):
            client.request([{"moduleName": "Test"}])

    def test_retry_on_non_dict_json_response(self, httpx_mock: HTTPXMock) -> None:
        """辞書ではないJSONレスポンスでリトライ"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json=["not", "an", "object"],
        )
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "ok", "body": ""},
        )

        config = AjaxModuleConnectorConfig(retry_interval=0)
        client = AjaxModuleConnectorClient(site_name="www", config=config)
        responses = client.request([{"moduleName": "Test"}])

        assert len(httpx_mock.get_requests()) == 2
        assert responses[0].json()["status"] == "ok"

    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    def test_non_dict_json_response_max_retry(self, httpx_mock: HTTPXMock) -> None:
        """辞書ではないJSONレスポンスでリトライ上限超過"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json=["not", "an", "object"],
        )

        config = AjaxModuleConnectorConfig(attempt_limit=2, retry_interval=0)
        client = AjaxModuleConnectorClient(site_name="www", config=config)

        with pytest.raises(ResponseDataException):
            client.request([{"moduleName": "Test"}])

    def test_retry_on_empty_json_response(self, httpx_mock: HTTPXMock) -> None:
        """空JSONレスポンスでリトライ"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={},  # 空オブジェクト
        )
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "ok", "body": ""},
        )

        config = AjaxModuleConnectorConfig(retry_interval=0)
        client = AjaxModuleConnectorClient(site_name="www", config=config)
        responses = client.request([{"moduleName": "Test"}])

        assert len(httpx_mock.get_requests()) == 2
        assert responses[0].json()["status"] == "ok"

    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    def test_empty_response_max_retry(self, httpx_mock: HTTPXMock) -> None:
        """空レスポンスでリトライ上限超過"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={},
        )

        config = AjaxModuleConnectorConfig(attempt_limit=2, retry_interval=0)
        client = AjaxModuleConnectorClient(site_name="www", config=config)

        with pytest.raises(ResponseDataException):
            client.request([{"moduleName": "Test"}])

    def test_return_exceptions_mode(self, httpx_mock: HTTPXMock) -> None:
        """return_exceptions=Trueで例外を返す"""
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "ok", "body": ""},
        )
        httpx_mock.add_response(
            url="https://www.wikidot.com/ajax-module-connector.php",
            json={"status": "some_error"},
        )

        client = AjaxModuleConnectorClient(site_name="www")
        responses = client.request(
            [{"moduleName": "Good"}, {"moduleName": "Bad"}],
            return_exceptions=True,
        )

        assert len(responses) == 2
        # 順序は保証されないため、型でチェック
        types = [type(r).__name__ for r in responses]
        assert "Response" in types
        assert "WikidotStatusCodeException" in types

    def test_custom_site_name(self, httpx_mock: HTTPXMock) -> None:
        """サイト名を指定してリクエスト"""
        httpx_mock.add_response(
            url="http://other-site.wikidot.com",
            status_code=200,
        )
        httpx_mock.add_response(
            url="http://other-site.wikidot.com/ajax-module-connector.php",
            json={"status": "ok", "body": ""},
        )

        client = AjaxModuleConnectorClient(site_name="other-site")
        responses = client.request([{"moduleName": "Test"}])

        assert len(responses) == 1
