"""Ajaxモジュールのユニットテスト

ヘルパー関数のテストを行う。
AjaxRequestHeaderとAjaxModuleConnectorConfigのテストはtest_amc_client.pyに統合済み。
"""

import pytest

from wikidot.connector.ajax import (
    _calculate_backoff,
    _mask_sensitive_data,
)


class TestMaskSensitiveData:
    """_mask_sensitive_data関数のテスト"""

    def test_masks_password(self):
        """パスワードがマスクされる"""
        body = {"username": "test", "password": "secret123"}
        result = _mask_sensitive_data(body)
        assert result["username"] == "test"
        assert result["password"] == "***MASKED***"
        # 元の辞書は変更されない
        assert body["password"] == "secret123"

    def test_masks_login(self):
        """loginがマスクされる"""
        body = {"login": "secret"}
        result = _mask_sensitive_data(body)
        assert result["login"] == "***MASKED***"

    def test_masks_session_id(self):
        """WIKIDOT_SESSION_IDがマスクされる"""
        body = {"WIKIDOT_SESSION_ID": "abc123"}
        result = _mask_sensitive_data(body)
        assert result["WIKIDOT_SESSION_ID"] == "***MASKED***"

    def test_masks_wikidot_token(self):
        """wikidot_token7がマスクされる"""
        body = {"wikidot_token7": 123456}
        result = _mask_sensitive_data(body)
        assert result["wikidot_token7"] == "***MASKED***"

    def test_masks_page_lock_secret(self):
        """savePageで使うlock_secretがマスクされる"""
        body = {
            "action": "WikiPageAction",
            "lock_secret": "secret456",
            "nested": {"lock_secret": "nested-secret"},
        }

        result = _mask_sensitive_data(body)

        assert result["lock_secret"] == "***MASKED***"
        assert result["nested"]["lock_secret"] == "***MASKED***"
        assert body["lock_secret"] == "secret456"

    def test_preserves_non_sensitive_data(self):
        """機密でないデータは保持される"""
        body = {"moduleName": "test", "page_id": 123}
        result = _mask_sensitive_data(body)
        assert result["moduleName"] == "test"
        assert result["page_id"] == 123

    def test_masks_nested_sensitive_data_without_mutating_original(self):
        """ネストしたリクエストデータ内の機密値もマスクする"""
        body = {
            "moduleName": "test",
            "params": {
                "password": "secret123",
                "safe": "visible",
                "items": [
                    {"login": "private-user"},
                    {"WIKIDOT_SESSION_ID": "abc123"},
                    {"wikidot_token7": 987654},
                ],
            },
        }

        result = _mask_sensitive_data(body)

        assert result == {
            "moduleName": "test",
            "params": {
                "password": "***MASKED***",
                "safe": "visible",
                "items": [
                    {"login": "***MASKED***"},
                    {"WIKIDOT_SESSION_ID": "***MASKED***"},
                    {"wikidot_token7": "***MASKED***"},
                ],
            },
        }
        assert body["params"]["password"] == "secret123"
        assert body["params"]["items"][0]["login"] == "private-user"

    def test_masks_nested_user_content_fields_without_mutating_original(self):
        """ネストしたリクエストデータ内のユーザー作成内容もマスクする"""
        body = {
            "moduleName": "test",
            "source": "private source",
            "params": {
                "body": "private body",
                "text": "private text",
                "subject": "private subject",
                "title": "private title",
                "comment": "private comment",
                "comments": "private comments",
                "description": "private description",
                "safe": "visible",
                "items": [{"source": "nested private source"}],
            },
        }

        result = _mask_sensitive_data(body)

        assert result == {
            "moduleName": "test",
            "source": "***MASKED***",
            "params": {
                "body": "***MASKED***",
                "text": "***MASKED***",
                "subject": "***MASKED***",
                "title": "***MASKED***",
                "comment": "***MASKED***",
                "comments": "***MASKED***",
                "description": "***MASKED***",
                "safe": "visible",
                "items": [{"source": "***MASKED***"}],
            },
        }
        assert body["source"] == "private source"
        assert body["params"]["items"][0]["source"] == "nested private source"

    def test_empty_dict(self):
        """空の辞書でも動作する"""
        result = _mask_sensitive_data({})
        assert result == {}


class TestCalculateBackoff:
    """_calculate_backoff関数のテスト"""

    def test_first_retry(self):
        """最初のリトライ（retry_count=1）"""
        # 2^0 * 1.0 = 1.0（ジッターなしの場合）
        result = _calculate_backoff(1, 1.0, 2.0, 60.0)
        # ジッターがあるので範囲でチェック
        assert 1.0 <= result <= 1.1

    def test_second_retry(self):
        """2回目のリトライ（retry_count=2）"""
        # 2^1 * 1.0 = 2.0（ジッターなしの場合）
        result = _calculate_backoff(2, 1.0, 2.0, 60.0)
        assert 2.0 <= result <= 2.2

    def test_third_retry(self):
        """3回目のリトライ（retry_count=3）"""
        # 2^2 * 1.0 = 4.0（ジッターなしの場合）
        result = _calculate_backoff(3, 1.0, 2.0, 60.0)
        assert 4.0 <= result <= 4.4

    def test_respects_max_backoff(self):
        """max_backoffを超えない"""
        # 2^9 * 1.0 = 512.0 > 60.0
        result = _calculate_backoff(10, 1.0, 2.0, 60.0)
        assert result == 60.0

    def test_custom_base_interval(self):
        """カスタムのbase_interval"""
        # 2^1 * 2.0 = 4.0（ジッターなしの場合）
        result = _calculate_backoff(2, 2.0, 2.0, 60.0)
        assert 4.0 <= result <= 4.4

    def test_custom_backoff_factor(self):
        """カスタムのbackoff_factor"""
        # 3^2 * 1.0 = 9.0（ジッターなしの場合）
        result = _calculate_backoff(3, 1.0, 3.0, 60.0)
        assert 9.0 <= result <= 9.9

    @pytest.mark.parametrize("retry_count", [None, True, "1", 0, -1, 1.5])
    def test_rejects_invalid_retry_count(self, retry_count):
        """retry_countは正の整数だけを受け付ける"""
        with pytest.raises(ValueError, match="retry_count must be a positive integer"):
            _calculate_backoff(retry_count, 1.0, 2.0, 60.0)

    @pytest.mark.parametrize("field", ["base_interval", "backoff_factor", "max_backoff"])
    @pytest.mark.parametrize("value", [None, True, "1", -0.1])
    def test_rejects_invalid_numeric_backoff_options(self, field, value):
        """backoff設定値は非負の数値だけを受け付ける"""
        options = {
            "base_interval": 1.0,
            "backoff_factor": 2.0,
            "max_backoff": 60.0,
        }
        options[field] = value

        with pytest.raises(ValueError, match=rf"{field} must be a non-negative number"):
            _calculate_backoff(1, options["base_interval"], options["backoff_factor"], options["max_backoff"])
