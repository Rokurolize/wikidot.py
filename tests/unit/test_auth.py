"""
認証モジュールのユニットテスト

HTTPAuthenticationクラスをテストする。
"""

from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from wikidot.common.exceptions import SessionCreateException
from wikidot.connector.ajax import AjaxModuleConnectorConfig
from wikidot.module.auth import HTTPAuthentication


class TestHTTPAuthentication:
    """HTTPAuthenticationクラスのテスト"""

    @staticmethod
    def _mock_client() -> MagicMock:
        mock_client = MagicMock()
        mock_client.amc_client.header.get_header.return_value = {}
        mock_client.amc_client.config = AjaxModuleConnectorConfig(retry_interval=0)
        return mock_client

    def test_login_success(self):
        """ログイン成功"""
        mock_client = self._mock_client()

        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.text = "Login successful"
        mock_response.cookies = {"WIKIDOT_SESSION_ID": "test-session-id"}

        with patch("wikidot.module.auth.httpx.post", return_value=mock_response):
            HTTPAuthentication.login(mock_client, "test-user", "test-password")

        mock_client.amc_client.header.set_cookie.assert_called_once_with("WIKIDOT_SESSION_ID", "test-session-id")

    @pytest.mark.parametrize(
        ("field", "value", "message"),
        [
            ("username", None, "username must be a string"),
            ("username", 123, "username must be a string"),
            ("username", True, "username must be a string"),
            ("password", None, "password must be a string"),
            ("password", 123, "password must be a string"),
            ("password", True, "password must be a string"),
        ],
    )
    def test_login_rejects_non_string_credentials_before_request(self, field: str, value: Any, message: str) -> None:
        """認証情報の型不正はHTTPリクエスト前に拒否する"""
        mock_client = self._mock_client()
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.text = "Login successful"
        mock_response.cookies = {"WIKIDOT_SESSION_ID": "test-session-id"}
        username: Any = value if field == "username" else "test-user"
        password: Any = value if field == "password" else "test-password"

        with (
            patch("wikidot.module.auth.httpx.post", return_value=mock_response) as mock_post,
            pytest.raises(ValueError, match=message),
        ):
            HTTPAuthentication.login(mock_client, username, password)

        mock_post.assert_not_called()
        mock_client.amc_client.header.set_cookie.assert_not_called()

    @pytest.mark.parametrize("config", [None, object(), {}, "config", True])
    def test_login_rejects_invalid_config_object_before_request(self, config: Any) -> None:
        """認証リクエスト前に不正な設定オブジェクトを拒否する"""
        mock_client = self._mock_client()
        mock_client.amc_client.config = config

        with (
            patch("wikidot.module.auth.httpx.post") as mock_post,
            pytest.raises(ValueError, match="config must be AjaxModuleConnectorConfig"),
        ):
            HTTPAuthentication.login(mock_client, "test-user", "test-password")

        mock_post.assert_not_called()
        mock_client.amc_client.header.get_header.assert_not_called()
        mock_client.amc_client.header.set_cookie.assert_not_called()

    def test_login_invalid_credentials(self):
        """認証失敗（ユーザー名/パスワード不一致）"""
        mock_client = self._mock_client()

        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.text = "The login and password do not match"

        with patch("wikidot.module.auth.httpx.post", return_value=mock_response):
            with pytest.raises(SessionCreateException) as exc_info:
                HTTPAuthentication.login(mock_client, "wrong-user", "wrong-password")

            assert "invalid username or password" in str(exc_info.value)

    def test_login_http_error(self):
        """ログイン失敗（HTTPエラー）"""
        mock_client = self._mock_client()

        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.INTERNAL_SERVER_ERROR

        with patch("wikidot.module.auth.httpx.post", return_value=mock_response):
            with pytest.raises(SessionCreateException) as exc_info:
                HTTPAuthentication.login(mock_client, "test-user", "test-password")

            assert "HTTP status code" in str(exc_info.value)

    def test_login_no_session_cookie(self):
        """ログイン失敗（セッションCookieなし）"""
        mock_client = self._mock_client()

        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.text = "Login successful"
        mock_response.cookies = {}  # セッションCookieなし

        with patch("wikidot.module.auth.httpx.post", return_value=mock_response):
            with pytest.raises(SessionCreateException) as exc_info:
                HTTPAuthentication.login(mock_client, "test-user", "test-password")

            assert "invalid cookies" in str(exc_info.value)

    def test_login_blank_session_cookie_fails_without_setting_cookie(self):
        """ログイン失敗（セッションCookieが空）"""
        mock_client = self._mock_client()

        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.text = "Login successful"
        mock_response.cookies = {"WIKIDOT_SESSION_ID": "   "}

        with patch("wikidot.module.auth.httpx.post", return_value=mock_response):
            with pytest.raises(SessionCreateException) as exc_info:
                HTTPAuthentication.login(mock_client, "test-user", "test-password")

            assert "WIKIDOT_SESSION_ID cookie is empty" in str(exc_info.value)

        mock_client.amc_client.header.set_cookie.assert_not_called()

    def test_logout(self):
        """ログアウト成功"""
        mock_client = MagicMock()

        HTTPAuthentication.logout(mock_client)

        mock_client.amc_client.request.assert_called_once()
        mock_client.amc_client.header.delete_cookie.assert_called_once_with("WIKIDOT_SESSION_ID")

    def test_logout_suppresses_errors(self):
        """ログアウト時のエラーが抑制される"""
        mock_client = MagicMock()
        mock_client.amc_client.request.side_effect = Exception("Network error")

        # エラーが発生しても例外が送出されない
        HTTPAuthentication.logout(mock_client)

        # Cookieの削除は常に実行される
        mock_client.amc_client.header.delete_cookie.assert_called_once_with("WIKIDOT_SESSION_ID")
