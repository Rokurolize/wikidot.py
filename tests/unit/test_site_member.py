"""SiteMemberモジュールのユニットテスト"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from wikidot.common.exceptions import (
    LoginRequiredException,
    NoElementException,
    TargetErrorException,
    UnexpectedException,
    WikidotStatusCodeException,
)
from wikidot.module.site import Site
from wikidot.module.site_member import SiteMember


class TestSiteMemberDataclass:
    """SiteMemberデータクラスのテスト"""

    def test_init(self):
        """初期化のテスト"""
        site = MagicMock()
        user = MagicMock()
        joined_at = datetime.now(timezone.utc)

        member = SiteMember(site=site, user=user, joined_at=joined_at)

        assert member.site == site
        assert member.user == user
        assert member.joined_at == joined_at

    def test_init_without_joined_at(self):
        """joined_atなしでの初期化"""
        site = MagicMock()
        user = MagicMock()

        member = SiteMember(site=site, user=user, joined_at=None)

        assert member.joined_at is None


class TestSiteMemberParse:
    """SiteMember._parseのテスト"""

    def test_parse_single_member(self):
        """1人のメンバーをパース"""
        html = BeautifulSoup(
            """
            <table>
                <tr>
                    <td><span class="printuser">
                        <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">Test User</a>
                    </span></td>
                    <td><span class="odate time_123456789">2024-01-01</span></td>
                </tr>
            </table>
            """,
            "lxml",
        )
        site = MagicMock()
        mock_user = MagicMock()

        with (
            patch("wikidot.module.site_member.user_parser") as mock_user_parser,
            patch("wikidot.module.site_member.odate_parser") as mock_odate_parser,
        ):
            mock_user_parser.return_value = mock_user
            mock_odate_parser.return_value = datetime(2024, 1, 1, tzinfo=timezone.utc)

            members = SiteMember._parse(site, html)

            assert len(members) == 1
            assert members[0].site == site
            assert members[0].user == mock_user
            assert members[0].joined_at == datetime(2024, 1, 1, tzinfo=timezone.utc)

    def test_parse_member_without_joined_at(self):
        """joined_atなしのメンバーをパース"""
        html = BeautifulSoup(
            """
            <table>
                <tr>
                    <td><span class="printuser">
                        <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">Test User</a>
                    </span></td>
                </tr>
            </table>
            """,
            "lxml",
        )
        site = MagicMock()
        mock_user = MagicMock()

        with patch("wikidot.module.site_member.user_parser") as mock_user_parser:
            mock_user_parser.return_value = mock_user

            members = SiteMember._parse(site, html)

            assert len(members) == 1
            assert members[0].joined_at is None

    def test_parse_skips_rows_without_printuser(self):
        """printuserがない行はスキップ"""
        html = BeautifulSoup(
            """
            <table>
                <tr>
                    <td>Header</td>
                </tr>
                <tr>
                    <td><span class="printuser">
                        <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">Test User</a>
                    </span></td>
                </tr>
            </table>
            """,
            "lxml",
        )
        site = MagicMock()
        mock_user = MagicMock()

        with patch("wikidot.module.site_member.user_parser") as mock_user_parser:
            mock_user_parser.return_value = mock_user

            members = SiteMember._parse(site, html)

            assert len(members) == 1

    def test_parse_skips_header_rows_without_tds(self):
        """thだけのヘッダ行はスキップ"""
        html = BeautifulSoup(
            """
            <table>
                <tr>
                    <th>User</th>
                    <th>Joined</th>
                </tr>
                <tr>
                    <td><span class="printuser">
                        <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">Test User</a>
                    </span></td>
                </tr>
            </table>
            """,
            "lxml",
        )
        site = MagicMock()
        mock_user = MagicMock()

        with patch("wikidot.module.site_member.user_parser") as mock_user_parser:
            mock_user_parser.return_value = mock_user

            members = SiteMember._parse(site, html)

            assert len(members) == 1

    def test_parse_ignores_nested_member_tables(self):
        """ネストしたメンバー風テーブルは構造上のメンバーとして扱わない"""
        html = BeautifulSoup(
            """
            <table>
                <tr>
                    <td>
                        <table>
                            <tr>
                                <td><span class="printuser">
                                    <a onclick="WIKIDOT.page.listeners.userInfo(99999)" href="#">Fake User</a>
                                </span></td>
                                <td><span class="odate time_111111111">Fake Date</span></td>
                            </tr>
                        </table>
                        <span class="printuser">
                            <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">Real User</a>
                        </span>
                    </td>
                    <td><span class="odate time_123456789">2024-01-01</span></td>
                </tr>
            </table>
            """,
            "lxml",
        )
        site = MagicMock()
        real_joined_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

        with (
            patch("wikidot.module.site_member.user_parser") as mock_user_parser,
            patch("wikidot.module.site_member.odate_parser") as mock_odate_parser,
        ):
            mock_user_parser.side_effect = lambda _client, elem: elem.get_text(strip=True)
            mock_odate_parser.return_value = real_joined_at

            members = SiteMember._parse(site, html)

            assert len(members) == 1
            assert members[0].user == "Real User"
            assert members[0].joined_at == real_joined_at


class TestSiteMemberGet:
    """SiteMember.getのテスト"""

    @staticmethod
    def _members_response(body: str) -> MagicMock:
        response = MagicMock()
        response.json.return_value = {"body": body}
        return response

    def test_get_members_single_page(self):
        """単一ページのメンバー取得"""
        site = MagicMock()
        response = self._members_response(
            """
                <table>
                    <tr>
                        <td><span class="printuser">
                            <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">User1</a>
                        </span></td>
                    </tr>
                </table>
            """
        )
        site.amc_request_with_retry.return_value = (response,)

        with patch("wikidot.module.site_member.user_parser") as mock_user_parser:
            mock_user_parser.return_value = MagicMock()

            members = SiteMember.get(site, "")

            assert len(members) == 1
            site.amc_request.assert_not_called()
            site.amc_request_with_retry.assert_called_once()

    def test_get_members_retries_transient_first_page_failures(self):
        """メンバー一覧の初回取得は一時的なAMC失敗を再試行する"""
        mock_client = MagicMock()
        mock_client.amc_client = MagicMock()
        mock_client.amc_client.config.retry_batch_size = 50
        mock_client.amc_client.config.retry_max_retries = 3
        site = Site(
            client=mock_client,
            id=123456,
            title="Test",
            unix_name="test",
            domain="test.wikidot.com",
            ssl_supported=True,
        )
        response = self._members_response(
            """
                <table>
                    <tr>
                        <td><span class="printuser">
                            <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">User1</a>
                        </span></td>
                    </tr>
                </table>
            """
        )
        mock_client.amc_client.request.side_effect = [
            (RuntimeError("temporary failure"),),
            (response,),
        ]

        with patch("wikidot.module.site_member.user_parser") as mock_user_parser:
            mock_user_parser.return_value = MagicMock()

            members = SiteMember.get(site, "")

        assert len(members) == 1
        assert mock_client.amc_client.request.call_count == 2
        assert [call.args[1] for call in mock_client.amc_client.request.call_args_list] == [True, True]

    def test_get_members_raises_when_first_page_retry_is_exhausted(self):
        """初回ページの再試行失敗はsite/group/page付きで失敗する"""
        site = MagicMock()
        site.unix_name = "test-site"
        site.amc_request_with_retry.return_value = (None,)

        with pytest.raises(
            UnexpectedException,
            match="Cannot retrieve site members for site: test-site, group: members, page: 1",
        ):
            SiteMember.get(site, "")

        site.amc_request.assert_not_called()

    def test_get_members_missing_first_page_response_body_includes_context(self):
        """初回ページのbody欠落はsite/group/page付きで失敗する"""
        site = MagicMock()
        site.unix_name = "test-site"
        response = MagicMock()
        response.json.return_value = {}
        site.amc_request_with_retry.return_value = (response,)

        with (
            patch("wikidot.module.site_member.user_parser") as mock_user_parser,
            pytest.raises(
                NoElementException,
                match="Site member list response body is not found for site: test-site, group: members, page: 1",
            ),
        ):
            SiteMember.get(site, "")

        site.amc_request.assert_not_called()
        mock_user_parser.assert_not_called()

    def test_get_members_with_pagination(self):
        """ページネーション付きのメンバー取得"""
        site = MagicMock()

        first_response = MagicMock()
        first_response.json.return_value = {
            "body": """
                <table>
                    <tr>
                        <td><span class="printuser">
                            <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">User1</a>
                        </span></td>
                    </tr>
                </table>
                <div class="pager">
                    <a href="#">1</a>
                    <a href="#">2</a>
                    <a href="#">next</a>
                </div>
            """
        }

        second_response = MagicMock()
        second_response.json.return_value = {
            "body": """
                <table>
                    <tr>
                        <td><span class="printuser">
                            <a onclick="WIKIDOT.page.listeners.userInfo(67890)" href="#">User2</a>
                        </span></td>
                    </tr>
                </table>
            """
        }

        site.amc_request_with_retry.side_effect = [(first_response,), (second_response,)]

        with patch("wikidot.module.site_member.user_parser") as mock_user_parser:
            mock_user_parser.return_value = MagicMock()

            members = SiteMember.get(site, "")

            assert len(members) == 2
            site.amc_request.assert_not_called()
            assert site.amc_request_with_retry.call_count == 2

    def test_get_members_raises_when_paginated_retry_is_exhausted(self):
        """ページネーション中の再試行失敗は部分的な一覧を返さない"""
        site = MagicMock()
        site.unix_name = "test-site"
        first_response = self._members_response(
            """
                <table>
                    <tr>
                        <td><span class="printuser">
                            <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">User1</a>
                        </span></td>
                    </tr>
                </table>
                <div class="pager">
                    <a href="#">1</a>
                    <a href="#">2</a>
                </div>
            """
        )
        site.amc_request_with_retry.side_effect = [(first_response,), (None,)]

        with (
            patch("wikidot.module.site_member.user_parser") as mock_user_parser,
            pytest.raises(
                UnexpectedException,
                match="Cannot retrieve site members for site: test-site, group: members, page: 2",
            ),
        ):
            mock_user_parser.return_value = MagicMock()
            SiteMember.get(site, "")

        site.amc_request.assert_not_called()

    def test_get_members_missing_paginated_response_body_includes_context(self):
        """ページネーション中のbody欠落はsite/group/page付きで失敗する"""
        site = MagicMock()
        site.unix_name = "test-site"
        first_response = self._members_response(
            """
                <table>
                    <tr>
                        <td><span class="printuser">
                            <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">User1</a>
                        </span></td>
                    </tr>
                </table>
                <div class="pager">
                    <a href="#">1</a>
                    <a href="#">2</a>
                </div>
            """
        )
        second_response = MagicMock()
        second_response.json.return_value = {}
        site.amc_request_with_retry.side_effect = [(first_response,), (second_response,)]

        with (
            patch("wikidot.module.site_member.user_parser") as mock_user_parser,
            pytest.raises(
                NoElementException,
                match="Site member list response body is not found for site: test-site, group: members, page: 2",
            ),
        ):
            mock_user_parser.return_value = MagicMock()
            SiteMember.get(site, "")

        site.amc_request.assert_not_called()
        assert mock_user_parser.call_count == 1

    def test_get_members_ignores_non_numeric_pager_links(self):
        """数値ページがないpagerでは単一ページとして扱う"""
        site = MagicMock()
        response = MagicMock()
        response.json.return_value = {
            "body": """
                <table>
                    <tr>
                        <td><span class="printuser">
                            <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">User1</a>
                        </span></td>
                    </tr>
                </table>
                <div class="pager"><a href="#">next</a></div>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with patch("wikidot.module.site_member.user_parser") as mock_user_parser:
            mock_user_parser.return_value = MagicMock()

            members = SiteMember.get(site, "")

            assert len(members) == 1
            site.amc_request.assert_not_called()
            site.amc_request_with_retry.assert_called_once()

    def test_get_members_ignores_member_row_pager_markup(self):
        """メンバー行内のpager風マークアップをページネーションとして扱わない"""
        site = MagicMock()
        response = self._members_response(
            """
                <table>
                    <tr>
                        <td>
                            <span class="printuser">
                                <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">User1</a>
                            </span>
                            <div class="pager">
                                <a href="#">1</a>
                                <a href="#">2</a>
                            </div>
                        </td>
                    </tr>
                </table>
            """
        )
        site.amc_request_with_retry.return_value = (response,)

        with patch("wikidot.module.site_member.user_parser") as mock_user_parser:
            mock_user_parser.return_value = MagicMock()

            members = SiteMember.get(site, "")

        assert len(members) == 1
        site.amc_request.assert_not_called()
        site.amc_request_with_retry.assert_called_once()

    def test_get_admins_group(self):
        """管理者グループ取得"""
        site = MagicMock()
        response = MagicMock()
        response.json.return_value = {"body": "<table></table>"}
        site.amc_request_with_retry.return_value = (response,)

        SiteMember.get(site, "admins")

        call_args = site.amc_request_with_retry.call_args[0][0][0]
        assert call_args["group"] == "admins"

    def test_get_moderators_group(self):
        """モデレーターグループ取得"""
        site = MagicMock()
        response = MagicMock()
        response.json.return_value = {"body": "<table></table>"}
        site.amc_request_with_retry.return_value = (response,)

        SiteMember.get(site, "moderators")

        call_args = site.amc_request_with_retry.call_args[0][0][0]
        assert call_args["group"] == "moderators"

    def test_get_invalid_group_raises(self):
        """無効なグループでValueError"""
        site = MagicMock()

        with pytest.raises(ValueError, match="Invalid group"):
            SiteMember.get(site, "invalid_group")

    def test_get_default_group(self):
        """デフォルトグループ（None）"""
        site = MagicMock()
        response = MagicMock()
        response.json.return_value = {"body": "<table></table>"}
        site.amc_request_with_retry.return_value = (response,)

        SiteMember.get(site, None)

        call_args = site.amc_request_with_retry.call_args[0][0][0]
        assert call_args["group"] == ""


class TestSiteMemberChangeGroup:
    """SiteMember._change_groupのテスト"""

    def test_to_moderator_success(self):
        """モデレーター昇格成功"""
        site = MagicMock()
        user = MagicMock()
        user.id = 12345
        member = SiteMember(site=site, user=user, joined_at=None)

        member.to_moderator()

        call_args = site.amc_request.call_args[0][0][0]
        assert call_args["action"] == "ManageSiteMembershipAction"
        assert call_args["event"] == "toModerators"
        assert call_args["user_id"] == 12345

    def test_remove_moderator_success(self):
        """モデレーター降格成功"""
        site = MagicMock()
        user = MagicMock()
        user.id = 12345
        member = SiteMember(site=site, user=user, joined_at=None)

        member.remove_moderator()

        call_args = site.amc_request.call_args[0][0][0]
        assert call_args["event"] == "removeModerator"

    def test_to_admin_success(self):
        """管理者昇格成功"""
        site = MagicMock()
        user = MagicMock()
        user.id = 12345
        member = SiteMember(site=site, user=user, joined_at=None)

        member.to_admin()

        call_args = site.amc_request.call_args[0][0][0]
        assert call_args["event"] == "toAdmins"

    def test_remove_admin_success(self):
        """管理者降格成功"""
        site = MagicMock()
        user = MagicMock()
        user.id = 12345
        member = SiteMember(site=site, user=user, joined_at=None)

        member.remove_admin()

        call_args = site.amc_request.call_args[0][0][0]
        assert call_args["event"] == "removeAdmin"

    def test_change_group_already_moderator_error(self):
        """既にモデレーターの場合のエラー"""
        site = MagicMock()
        user = MagicMock()
        user.id = 12345
        user.name = "TestUser"
        member = SiteMember(site=site, user=user, joined_at=None)

        site.amc_request.side_effect = WikidotStatusCodeException(
            "already_moderator",
            "already_moderator",
        )

        with pytest.raises(TargetErrorException, match="already moderator"):
            member.to_moderator()

    def test_change_group_already_admin_error(self):
        """既に管理者の場合のエラー"""
        site = MagicMock()
        user = MagicMock()
        user.id = 12345
        user.name = "TestUser"
        member = SiteMember(site=site, user=user, joined_at=None)

        site.amc_request.side_effect = WikidotStatusCodeException(
            "already_admin",
            "already_admin",
        )

        with pytest.raises(TargetErrorException, match="already admin"):
            member.to_admin()

    def test_change_group_not_already_error(self):
        """権限を持っていない場合のエラー"""
        site = MagicMock()
        user = MagicMock()
        user.id = 12345
        user.name = "TestUser"
        member = SiteMember(site=site, user=user, joined_at=None)

        site.amc_request.side_effect = WikidotStatusCodeException(
            "not_already",
            "not_already",
        )

        with pytest.raises(TargetErrorException, match="not moderator/admin"):
            member.remove_moderator()

    def test_change_group_invalid_event_raises(self):
        """無効なイベントでValueError"""
        site = MagicMock()
        user = MagicMock()
        member = SiteMember(site=site, user=user, joined_at=None)

        with pytest.raises(ValueError, match="Invalid event"):
            member._change_group("invalidEvent")

    def test_change_group_not_logged_in_raises_before_request(self):
        """未ログイン時は権限変更リクエストを送らない"""
        site = MagicMock()
        site.client.login_check.side_effect = LoginRequiredException("Login required")
        user = MagicMock()
        user.id = 12345
        member = SiteMember(site=site, user=user, joined_at=None)

        with pytest.raises(LoginRequiredException):
            member.to_moderator()

        site.amc_request.assert_not_called()

    def test_change_group_other_error_reraises(self):
        """その他のエラーは再送出"""
        site = MagicMock()
        user = MagicMock()
        user.id = 12345
        member = SiteMember(site=site, user=user, joined_at=None)

        site.amc_request.side_effect = WikidotStatusCodeException(
            "some_other_error",
            "some_other_error",
        )

        with pytest.raises(WikidotStatusCodeException):
            member.to_moderator()
