"""QuickModuleのユニットテスト"""

from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from wikidot.util.quick_module import QMCPage, QMCUser, QuickModule


class TestQMCUser:
    """QMCUserデータクラスのテスト"""

    def test_init(self):
        """初期化"""
        user = QMCUser(id=12345, name="test-user")

        assert user.id == 12345
        assert user.name == "test-user"

    @pytest.mark.parametrize("user_id", [None, True, "12345", 12345.0, object()])
    def test_init_rejects_malformed_ids(self, user_id: object) -> None:
        """idは整数だけ受け付ける"""
        bad_user_id: Any = user_id

        with pytest.raises(ValueError, match="id must be an integer"):
            QMCUser(id=bad_user_id, name="test-user")

    @pytest.mark.parametrize("user_id", [-1, -100])
    def test_init_rejects_negative_ids(self, user_id: int) -> None:
        """idの負数は受け付けない"""
        with pytest.raises(ValueError, match="id must be non-negative"):
            QMCUser(id=user_id, name="test-user")

    def test_init_accepts_zero_id(self) -> None:
        """id=0は非負数として扱う"""
        user = QMCUser(id=0, name="test-user")

        assert user.id == 0

    @pytest.mark.parametrize("name", [None, True, 12345, [], object()])
    def test_init_rejects_malformed_names(self, name: object) -> None:
        """nameは文字列だけ受け付ける"""
        bad_name: Any = name

        with pytest.raises(ValueError, match="name must be a string"):
            QMCUser(id=12345, name=bad_name)

    @pytest.mark.parametrize("name", ["", "   "])
    def test_init_rejects_blank_names(self, name: str) -> None:
        """nameのblank値は受け付けない"""
        with pytest.raises(ValueError, match="name must not be empty"):
            QMCUser(id=12345, name=name)


class TestQMCPage:
    """QMCPageデータクラスのテスト"""

    def test_init(self):
        """初期化"""
        page = QMCPage(title="Test Page", unix_name="test-page")

        assert page.title == "Test Page"
        assert page.unix_name == "test-page"

    @pytest.mark.parametrize("title", [None, True, 12345, [], object()])
    def test_init_rejects_malformed_titles(self, title: object) -> None:
        """titleは文字列だけ受け付ける"""
        bad_title: Any = title

        with pytest.raises(ValueError, match="title must be a string"):
            QMCPage(title=bad_title, unix_name="test-page")

    @pytest.mark.parametrize("unix_name", [None, True, 12345, [], object()])
    def test_init_rejects_malformed_unix_names(self, unix_name: object) -> None:
        """unix_nameは文字列だけ受け付ける"""
        bad_unix_name: Any = unix_name

        with pytest.raises(ValueError, match="unix_name must be a string"):
            QMCPage(title="Test Page", unix_name=bad_unix_name)

    @pytest.mark.parametrize("unix_name", ["", "   "])
    def test_init_rejects_blank_unix_names(self, unix_name: str) -> None:
        """unix_nameのblank値は受け付けない"""
        with pytest.raises(ValueError, match="unix_name must not be empty"):
            QMCPage(title="Test Page", unix_name=unix_name)

    def test_init_allows_blank_titles(self) -> None:
        """titleのblank値は既存どおり受け付ける"""
        page = QMCPage(title="", unix_name="test-page")

        assert page.title == ""
        assert page.unix_name == "test-page"


class TestQuickModuleRequest:
    """QuickModule._requestのテスト"""

    def test_request_member_lookup(self, quickmodule_member_lookup: dict[str, Any]):
        """MemberLookupQModuleリクエスト"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = quickmodule_member_lookup

        with patch("httpx.get", return_value=mock_response) as mock_get:
            result = QuickModule._request("MemberLookupQModule", 123456, "test")

            mock_get.assert_called_once()
            call_url = mock_get.call_args[0][0]
            assert "MemberLookupQModule" in call_url
            assert "s=123456" in call_url
            assert "q=test" in call_url
            assert result == quickmodule_member_lookup

    def test_request_url_encodes_query(self, quickmodule_member_lookup: dict[str, Any]):
        """クエリ文字列をURLエンコードする"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = quickmodule_member_lookup

        with patch("httpx.get", return_value=mock_response) as mock_get:
            QuickModule._request("MemberLookupQModule", 123456, "a b&role=admin")

            call_url = mock_get.call_args[0][0]
            assert "q=a+b%26role%3Dadmin" in call_url

    def test_request_allows_zero_site_id(self, quickmodule_member_lookup: dict[str, Any]) -> None:
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = quickmodule_member_lookup

        with patch("httpx.get", return_value=mock_response) as mock_get:
            result = QuickModule._request("MemberLookupQModule", 0, "test")

        call_url = mock_get.call_args[0][0]
        assert "s=0" in call_url
        assert result == quickmodule_member_lookup

    def test_request_retries_transient_5xx(self, quickmodule_member_lookup: dict[str, Any]):
        """QuickModuleの一時的な5xxは再試行する"""
        transient_response = MagicMock()
        transient_response.status_code = httpx.codes.INTERNAL_SERVER_ERROR
        success_response = MagicMock()
        success_response.status_code = httpx.codes.OK
        success_response.json.return_value = quickmodule_member_lookup

        with (
            patch("httpx.get", side_effect=[transient_response, success_response]) as mock_get,
            patch("wikidot.util.http.time.sleep"),
        ):
            result = QuickModule._request("MemberLookupQModule", 123456, "test")

        assert result == quickmodule_member_lookup
        assert mock_get.call_count == 2

    def test_request_user_lookup(self, quickmodule_user_lookup: dict[str, Any]):
        """UserLookupQModuleリクエスト"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = quickmodule_user_lookup

        with patch("httpx.get", return_value=mock_response):
            result = QuickModule._request("UserLookupQModule", 123456, "test")

            assert result == quickmodule_user_lookup

    def test_request_page_lookup(self, quickmodule_page_lookup: dict[str, Any]):
        """PageLookupQModuleリクエスト"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = quickmodule_page_lookup

        with patch("httpx.get", return_value=mock_response):
            result = QuickModule._request("PageLookupQModule", 123456, "test")

            assert result == quickmodule_page_lookup

    def test_request_invalid_module_raises(self):
        """無効なモジュール名でValueError"""
        with pytest.raises(ValueError, match="Invalid module name"):
            QuickModule._request("InvalidModule", 123456, "test")

    @pytest.mark.parametrize(
        "lookup_func", [QuickModule.member_lookup, QuickModule.user_lookup, QuickModule.page_lookup]
    )
    @pytest.mark.parametrize("site_id", [None, True, "123456", 123456.0, object()])
    def test_lookup_rejects_malformed_site_ids_before_request(self, lookup_func: Any, site_id: object) -> None:
        """site_idの異常値はリクエスト前に拒否する"""
        bad_site_id: Any = site_id

        with (
            patch("httpx.get", side_effect=AssertionError("request reached")) as mock_get,
            pytest.raises(ValueError, match="site_id must be an integer"),
        ):
            lookup_func(bad_site_id, "test")

        mock_get.assert_not_called()

    @pytest.mark.parametrize(
        "lookup_func", [QuickModule.member_lookup, QuickModule.user_lookup, QuickModule.page_lookup]
    )
    @pytest.mark.parametrize("site_id", [-1, -100])
    def test_lookup_rejects_negative_site_ids_before_request(self, lookup_func: Any, site_id: int) -> None:
        """site_idの負数はリクエスト前に拒否する"""
        with (
            patch("httpx.get", side_effect=AssertionError("request reached")) as mock_get,
            pytest.raises(ValueError, match="site_id must be non-negative"),
        ):
            lookup_func(site_id, "test")

        mock_get.assert_not_called()

    @pytest.mark.parametrize(
        "lookup_func", [QuickModule.member_lookup, QuickModule.user_lookup, QuickModule.page_lookup]
    )
    @pytest.mark.parametrize("query", [None, True, 12345, [], object()])
    def test_lookup_rejects_malformed_queries_before_request(self, lookup_func: Any, query: object) -> None:
        """queryの異常値はリクエスト前に拒否する"""
        bad_query: Any = query

        with (
            patch("httpx.get", side_effect=AssertionError("request reached")) as mock_get,
            pytest.raises(ValueError, match="query must be a string"),
        ):
            lookup_func(123456, bad_query)

        mock_get.assert_not_called()

    @pytest.mark.parametrize("lookup_func", [QuickModule.member_lookup, QuickModule.user_lookup])
    @pytest.mark.parametrize("query", ["", "   "])
    def test_user_lookups_reject_blank_queries_before_request(self, lookup_func: Any, query: str) -> None:
        """ユーザー系lookupのblank queryはリクエスト前に拒否する"""
        with (
            patch("httpx.get", side_effect=AssertionError("request reached")) as mock_get,
            pytest.raises(ValueError, match="query must not be empty"),
        ):
            lookup_func(123456, query)

        mock_get.assert_not_called()

    def test_page_lookup_allows_blank_query(self, quickmodule_page_lookup_empty: dict[str, Any]) -> None:
        """PageLookupQModuleのblank queryは既存のリクエスト挙動を維持する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = quickmodule_page_lookup_empty

        with patch("httpx.get", return_value=mock_response) as mock_get:
            pages = QuickModule.page_lookup(123456, "")

        assert pages == []
        call_url = mock_get.call_args[0][0]
        assert "PageLookupQModule" in call_url
        assert "s=123456" in call_url
        assert "q=" in call_url

    def test_request_site_not_found(self):
        """サイトが見つからない場合ValueError"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.INTERNAL_SERVER_ERROR

        with (
            patch("httpx.get", return_value=mock_response),
            patch("wikidot.util.http.time.sleep"),
            pytest.raises(ValueError, match="Site is not found"),
        ):
            QuickModule._request("MemberLookupQModule", 999999, "test")

    def test_request_non_json_response_includes_module_site_context(self):
        """QuickModuleの非JSON応答はmodule/site文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.text = "raw private quickmodule body"
        mock_response.json.side_effect = ValueError("not json")

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(ValueError) as exc_info,
        ):
            QuickModule.member_lookup(123456, "private lookup")

        message = str(exc_info.value)
        assert message == "QuickModule response JSON is malformed for module: MemberLookupQModule, site_id=123456"
        assert "private lookup" not in message
        assert "raw private quickmodule body" not in message


class TestQuickModuleMemberLookup:
    """QuickModule.member_lookupのテスト"""

    def test_member_lookup_success(self, quickmodule_member_lookup: dict[str, Any]):
        """メンバー検索成功"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = quickmodule_member_lookup

        with patch("httpx.get", return_value=mock_response):
            users = QuickModule.member_lookup(123456, "test")

            assert len(users) == 2
            assert users[0].id == 12345
            assert users[0].name == "test-user"
            assert users[1].id == 67890
            assert users[1].name == "test-user-2"

    def test_member_lookup_empty(self, quickmodule_member_lookup_empty: dict[str, Any]):
        """メンバー検索（結果なし）"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = quickmodule_member_lookup_empty

        with patch("httpx.get", return_value=mock_response):
            users = QuickModule.member_lookup(123456, "nonexistent")

            assert len(users) == 0

    def test_member_lookup_missing_users_key_includes_module_site_and_field_context(self):
        """メンバー検索のusers欠落はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"status": "ok"}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule response key is missing for module: MemberLookupQModule, site_id=123456 "
                    r"\(field=users\)"
                ),
            ),
        ):
            QuickModule.member_lookup(123456, "test")

    def test_member_lookup_malformed_response_body_includes_module_site_and_type_context(self):
        """メンバー検索のレスポンス全体の形状異常はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = "users"

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule response body is malformed for module: MemberLookupQModule, site_id=123456 "
                    r"\(expected=dict, actual=str\)"
                ),
            ),
        ):
            QuickModule.member_lookup(123456, "test")

    def test_member_lookup_malformed_users_field_includes_module_site_field_and_type_context(self):
        """メンバー検索のusers形状異常はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"users": {"user_id": "12345", "name": "bad-user"}}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule response field is malformed for module: MemberLookupQModule, site_id=123456 "
                    r"\(field=users, expected=list, actual=dict\)"
                ),
            ),
        ):
            QuickModule.member_lookup(123456, "test")

    def test_member_lookup_missing_user_id_includes_module_site_row_and_field_context(self):
        """メンバー検索のuser_id欠落はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"users": [{"name": "bad-user"}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule row field is missing for module: MemberLookupQModule, site_id=123456 "
                    r"\(row=1, field=user_id\)"
                ),
            ),
        ):
            QuickModule.member_lookup(123456, "test")

    def test_member_lookup_malformed_user_id_includes_module_site_row_and_value_context(self):
        """メンバー検索のuser_id異常値はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"users": [{"user_id": "latest", "name": "bad-user"}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule user ID is malformed for module: MemberLookupQModule, site_id=123456 "
                    r"\(row=1, field=user_id, value=latest\)"
                ),
            ),
        ):
            QuickModule.member_lookup(123456, "test")

    def test_member_lookup_fullwidth_digit_user_id_includes_module_site_row_and_value_context(self) -> None:
        """メンバー検索の全角数字user_idはQuickModule文脈付きで失敗する"""
        fullwidth_user_id = "\uff11\uff12\uff13\uff14\uff15"
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"users": [{"user_id": fullwidth_user_id, "name": "bad-user"}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    rf"QuickModule user ID is malformed for module: MemberLookupQModule, site_id=123456 "
                    rf"\(row=1, field=user_id, value={fullwidth_user_id}\)"
                ),
            ),
        ):
            QuickModule.member_lookup(123456, "test")

    def test_member_lookup_negative_user_id_includes_module_site_row_and_value_context(self):
        """メンバー検索の負数user_idはQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"users": [{"user_id": "-1", "name": "bad-user"}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule user ID is malformed for module: MemberLookupQModule, site_id=123456 "
                    r"\(row=1, field=user_id, value=-1\)"
                ),
            ),
        ):
            QuickModule.member_lookup(123456, "test")

    def test_member_lookup_malformed_name_includes_module_site_row_field_and_type_context(self):
        """メンバー検索のname異常値はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"users": [{"user_id": "12345", "name": 12345}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule row field is malformed for module: MemberLookupQModule, site_id=123456 "
                    r"\(row=1, field=name, expected=str, actual=int\)"
                ),
            ),
        ):
            QuickModule.member_lookup(123456, "test")

    @pytest.mark.parametrize("name", ["", "   "])
    def test_member_lookup_blank_name_includes_module_site_row_and_field_context(self, name: str) -> None:
        """メンバー検索のblank nameはQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"users": [{"user_id": "12345", "name": name}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule row field is empty for module: MemberLookupQModule, site_id=123456 "
                    r"\(row=1, field=name\)"
                ),
            ),
        ):
            QuickModule.member_lookup(123456, "test")

    def test_member_lookup_malformed_row_includes_module_site_row_and_type_context(self):
        """メンバー検索の行形状異常はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"users": ["user_id"]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule row is malformed for module: MemberLookupQModule, site_id=123456 "
                    r"\(row=1, expected=dict, actual=str\)"
                ),
            ),
        ):
            QuickModule.member_lookup(123456, "test")


class TestQuickModuleUserLookup:
    """QuickModule.user_lookupのテスト"""

    def test_user_lookup_success(self, quickmodule_user_lookup: dict[str, Any]):
        """ユーザー検索成功"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = quickmodule_user_lookup

        with patch("httpx.get", return_value=mock_response):
            users = QuickModule.user_lookup(123456, "test")

            assert len(users) == 1
            assert users[0].id == 12345
            assert users[0].name == "test-user"

    def test_user_lookup_missing_users_key_includes_module_site_and_field_context(self):
        """ユーザー検索のusers欠落はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"status": "ok"}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule response key is missing for module: UserLookupQModule, site_id=123456 "
                    r"\(field=users\)"
                ),
            ),
        ):
            QuickModule.user_lookup(123456, "test")

    def test_user_lookup_missing_name_includes_module_site_row_and_field_context(self):
        """ユーザー検索のname欠落はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"users": [{"user_id": "12345"}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule row field is missing for module: UserLookupQModule, site_id=123456 "
                    r"\(row=1, field=name\)"
                ),
            ),
        ):
            QuickModule.user_lookup(123456, "test")

    def test_user_lookup_malformed_user_id_includes_module_site_row_and_value_context(self):
        """ユーザー検索のuser_id異常値はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"users": [{"user_id": "latest", "name": "bad-user"}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule user ID is malformed for module: UserLookupQModule, site_id=123456 "
                    r"\(row=1, field=user_id, value=latest\)"
                ),
            ),
        ):
            QuickModule.user_lookup(123456, "test")

    def test_user_lookup_fullwidth_digit_user_id_includes_module_site_row_and_value_context(self) -> None:
        """ユーザー検索の全角数字user_idはQuickModule文脈付きで失敗する"""
        fullwidth_user_id = "\uff11\uff12\uff13\uff14\uff15"
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"users": [{"user_id": fullwidth_user_id, "name": "bad-user"}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    rf"QuickModule user ID is malformed for module: UserLookupQModule, site_id=123456 "
                    rf"\(row=1, field=user_id, value={fullwidth_user_id}\)"
                ),
            ),
        ):
            QuickModule.user_lookup(123456, "test")

    def test_user_lookup_negative_user_id_includes_module_site_row_and_value_context(self):
        """ユーザー検索の負数user_idはQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"users": [{"user_id": "-1", "name": "bad-user"}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule user ID is malformed for module: UserLookupQModule, site_id=123456 "
                    r"\(row=1, field=user_id, value=-1\)"
                ),
            ),
        ):
            QuickModule.user_lookup(123456, "test")

    def test_user_lookup_accepts_zero_user_id(self):
        """user_id=0は非負数として扱う"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"users": [{"user_id": "0", "name": "zero-user"}]}

        with patch("httpx.get", return_value=mock_response):
            users = QuickModule.user_lookup(123456, "test")

        assert len(users) == 1
        assert users[0].id == 0
        assert users[0].name == "zero-user"

    def test_user_lookup_malformed_name_includes_module_site_row_field_and_type_context(self):
        """ユーザー検索のname異常値はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"users": [{"user_id": "12345", "name": 12345}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule row field is malformed for module: UserLookupQModule, site_id=123456 "
                    r"\(row=1, field=name, expected=str, actual=int\)"
                ),
            ),
        ):
            QuickModule.user_lookup(123456, "test")

    @pytest.mark.parametrize("name", ["", "   "])
    def test_user_lookup_blank_name_includes_module_site_row_and_field_context(self, name: str) -> None:
        """ユーザー検索のblank nameはQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"users": [{"user_id": "12345", "name": name}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule row field is empty for module: UserLookupQModule, site_id=123456 "
                    r"\(row=1, field=name\)"
                ),
            ),
        ):
            QuickModule.user_lookup(123456, "test")


class TestQuickModulePageLookup:
    """QuickModule.page_lookupのテスト"""

    def test_page_lookup_success(self, quickmodule_page_lookup: dict[str, Any]):
        """ページ検索成功"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = quickmodule_page_lookup

        with patch("httpx.get", return_value=mock_response):
            pages = QuickModule.page_lookup(123456, "test")

            assert len(pages) == 2
            assert pages[0].unix_name == "test-page"
            assert pages[0].title == "Test Page"
            assert pages[1].unix_name == "scp-001"
            assert pages[1].title == "SCP-001"

    def test_page_lookup_empty(self, quickmodule_page_lookup_empty: dict[str, Any]):
        """ページ検索（結果なし）"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = quickmodule_page_lookup_empty

        with patch("httpx.get", return_value=mock_response):
            pages = QuickModule.page_lookup(123456, "nonexistent")

            assert len(pages) == 0

    def test_page_lookup_missing_pages_key_includes_module_site_and_field_context(self):
        """ページ検索のpages欠落はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"status": "ok"}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule response key is missing for module: PageLookupQModule, site_id=123456 "
                    r"\(field=pages\)"
                ),
            ),
        ):
            QuickModule.page_lookup(123456, "test")

    def test_page_lookup_malformed_response_body_includes_module_site_and_type_context(self):
        """ページ検索のレスポンス全体の形状異常はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = ["pages"]

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule response body is malformed for module: PageLookupQModule, site_id=123456 "
                    r"\(expected=dict, actual=list\)"
                ),
            ),
        ):
            QuickModule.page_lookup(123456, "test")

    def test_page_lookup_malformed_pages_field_includes_module_site_field_and_type_context(self):
        """ページ検索のpages形状異常はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"pages": {"title": "Bad Page", "unix_name": "bad-page"}}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule response field is malformed for module: PageLookupQModule, site_id=123456 "
                    r"\(field=pages, expected=list, actual=dict\)"
                ),
            ),
        ):
            QuickModule.page_lookup(123456, "test")

    def test_page_lookup_malformed_row_includes_module_site_row_and_type_context(self):
        """ページ検索の行形状異常はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"pages": ["title"]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule row is malformed for module: PageLookupQModule, site_id=123456 "
                    r"\(row=1, expected=dict, actual=str\)"
                ),
            ),
        ):
            QuickModule.page_lookup(123456, "test")

    def test_page_lookup_missing_title_includes_module_site_row_and_field_context(self):
        """ページ検索のtitle欠落はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"pages": [{"unix_name": "bad-page"}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule row field is missing for module: PageLookupQModule, site_id=123456 "
                    r"\(row=1, field=title\)"
                ),
            ),
        ):
            QuickModule.page_lookup(123456, "test")

    def test_page_lookup_malformed_title_includes_module_site_row_field_and_type_context(self):
        """ページ検索のtitle異常値はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"pages": [{"title": 12345, "unix_name": "bad-page"}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule row field is malformed for module: PageLookupQModule, site_id=123456 "
                    r"\(row=1, field=title, expected=str, actual=int\)"
                ),
            ),
        ):
            QuickModule.page_lookup(123456, "test")

    def test_page_lookup_allows_blank_title(self):
        """ページ検索のblank titleは既存どおり受け付ける"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"pages": [{"title": "", "unix_name": "untitled"}]}

        with patch("httpx.get", return_value=mock_response):
            pages = QuickModule.page_lookup(123456, "test")

        assert len(pages) == 1
        assert pages[0].title == ""
        assert pages[0].unix_name == "untitled"

    def test_page_lookup_missing_unix_name_includes_module_site_row_and_field_context(self):
        """ページ検索のunix_name欠落はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"pages": [{"title": "Bad Page"}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule row field is missing for module: PageLookupQModule, site_id=123456 "
                    r"\(row=1, field=unix_name\)"
                ),
            ),
        ):
            QuickModule.page_lookup(123456, "test")

    @pytest.mark.parametrize("unix_name", ["", "   "])
    def test_page_lookup_blank_unix_name_includes_module_site_row_and_field_context(self, unix_name: str):
        """ページ検索のblank unix_nameはQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"pages": [{"title": "Bad Page", "unix_name": unix_name}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule row field is empty for module: PageLookupQModule, site_id=123456 "
                    r"\(row=1, field=unix_name\)"
                ),
            ),
        ):
            QuickModule.page_lookup(123456, "test")

    def test_page_lookup_malformed_unix_name_includes_module_site_row_field_and_type_context(self):
        """ページ検索のunix_name異常値はQuickModule文脈付きで失敗する"""
        mock_response = MagicMock()
        mock_response.status_code = httpx.codes.OK
        mock_response.json.return_value = {"pages": [{"title": "Bad Page", "unix_name": ["bad-page"]}]}

        with (
            patch("httpx.get", return_value=mock_response),
            pytest.raises(
                ValueError,
                match=(
                    r"QuickModule row field is malformed for module: PageLookupQModule, site_id=123456 "
                    r"\(row=1, field=unix_name, expected=str, actual=list\)"
                ),
            ),
        ):
            QuickModule.page_lookup(123456, "test")
