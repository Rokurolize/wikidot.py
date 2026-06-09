"""SiteMemberモジュールのユニットテスト"""

from datetime import datetime, timezone
from typing import Any
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
from wikidot.connector.ajax import AjaxModuleConnectorConfig
from wikidot.module.client import Client
from wikidot.module.site import Site
from wikidot.module.site_member import SiteMember
from wikidot.module.user import User


def _client() -> Client:
    client: Any = object.__new__(Client)
    client.is_logged_in = False
    client.username = None
    client.me = None
    client.login_check = MagicMock()
    return client


def _member_user(user_id: int = 12345, name: str = "TestUser", client: Any | None = None) -> User:
    return User(client=client if client is not None else _client(), id=user_id, name=name, unix_name="test-user")


def _site(client: Any | None = None) -> Any:
    site: Any = Site(
        client=client if client is not None else _client(),
        id=123456,
        title="Test Site",
        unix_name="test-site",
        domain="test-site.wikidot.com",
        ssl_supported=True,
    )
    site.amc_request = MagicMock()
    site.amc_request_with_retry = MagicMock()
    return site


class TestSiteMemberDataclass:
    """SiteMemberデータクラスのテスト"""

    def test_init(self):
        """初期化のテスト"""
        site = _site()
        user = _member_user(client=site.client)
        joined_at = datetime.now(timezone.utc)

        member = SiteMember(site=site, user=user, joined_at=joined_at)

        assert member.site == site
        assert member.user == user
        assert member.joined_at == joined_at

    def test_init_without_joined_at(self):
        """joined_atなしでの初期化"""
        site = _site()
        user = _member_user(client=site.client)

        member = SiteMember(site=site, user=user, joined_at=None)

        assert member.joined_at is None

    @pytest.mark.parametrize("site", [None, True, "test-site", {"unix_name": "test-site"}, object()])
    def test_init_rejects_malformed_sites(self, site: object):
        """SiteMember.siteがSiteでなければ初期化時に拒否する"""
        user = _member_user()
        bad_site: Any = site

        with pytest.raises(ValueError, match="site must be a Site"):
            SiteMember(site=bad_site, user=user, joined_at=None)

    @pytest.mark.parametrize("user", [None, True, "TestUser", {"id": 12345}, object()])
    def test_init_rejects_malformed_users(self, user: object):
        """SiteMember.userがAbstractUserでなければ初期化時に拒否する"""
        site = _site()
        bad_user: Any = user

        with pytest.raises(ValueError, match="member.user must be an AbstractUser"):
            SiteMember(site=site, user=bad_user, joined_at=None)

    def test_init_rejects_user_from_different_client(self) -> None:
        """SiteMember.userはsiteと同じClientだけ受け付ける"""
        site = _site()
        user = _member_user(client=_client())

        with pytest.raises(ValueError, match="member.user must belong to the site"):
            SiteMember(site=site, user=user, joined_at=None)

    @pytest.mark.parametrize("joined_at", [True, 1700000000, "2024-01-01", []])
    def test_init_rejects_malformed_joined_at(self, joined_at: object) -> None:
        """SiteMember.joined_atはdatetimeまたはNoneだけ受け付ける"""
        site = _site()
        user = _member_user(client=site.client)
        bad_joined_at: Any = joined_at

        with pytest.raises(ValueError, match="joined_at must be a datetime or None"):
            SiteMember(site=site, user=user, joined_at=bad_joined_at)


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
        site = _site()
        mock_user = _member_user(client=site.client)

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
        site = _site()
        mock_user = _member_user(client=site.client)

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
        site = _site()
        mock_user = _member_user(client=site.client)

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
        site = _site()
        mock_user = _member_user(client=site.client)

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
        site = _site()
        real_joined_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

        with (
            patch("wikidot.module.site_member.user_parser") as mock_user_parser,
            patch("wikidot.module.site_member.odate_parser") as mock_odate_parser,
        ):
            mock_user_parser.side_effect = lambda _client, elem: _member_user(
                name=elem.get_text(strip=True), client=_client
            )
            mock_odate_parser.return_value = real_joined_at

            members = SiteMember._parse(site, html)

            assert len(members) == 1
            assert members[0].user.name == "Real User"
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
        site = _site()
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
            mock_user_parser.return_value = _member_user(client=site.client)

            members = SiteMember.get(site, "")

            assert len(members) == 1
            site.amc_request.assert_not_called()
            site.amc_request_with_retry.assert_called_once()

    def test_get_members_retries_transient_first_page_failures(self):
        """メンバー一覧の初回取得は一時的なAMC失敗を再試行する"""
        mock_client = _client()
        mock_client.amc_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(retry_batch_size=50, retry_max_retries=3)
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
            mock_user_parser.return_value = _member_user(client=site.client)

            members = SiteMember.get(site, "")

        assert len(members) == 1
        assert mock_client.amc_client.request.call_count == 2
        assert [call.args[1] for call in mock_client.amc_client.request.call_args_list] == [True, True]

    def test_get_members_raises_when_first_page_retry_is_exhausted(self):
        """初回ページの再試行失敗はsite/group/page付きで失敗する"""
        site = _site()
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
        site = _site()
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

    def test_get_members_malformed_response_body_type_includes_context(self):
        """初回ページのbody型異常はsite/group/page/type付きで失敗する"""
        site = _site()
        site.unix_name = "test-site"
        response = MagicMock()
        response.json.return_value = {"body": ["not", "html"]}
        site.amc_request_with_retry.return_value = (response,)

        with (
            patch("wikidot.module.site_member.user_parser") as mock_user_parser,
            pytest.raises(
                NoElementException,
                match=(
                    "Site member list response body is malformed for site: test-site, "
                    "group: members, page: 1 \\(field=body, expected=str, actual=list\\)"
                ),
            ),
        ):
            SiteMember.get(site, "")

        site.amc_request.assert_not_called()
        mock_user_parser.assert_not_called()

    def test_get_members_with_pagination(self):
        """ページネーション付きのメンバー取得"""
        site = _site()

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
            mock_user_parser.return_value = _member_user(client=site.client)

            members = SiteMember.get(site, "")

            assert len(members) == 2
            site.amc_request.assert_not_called()
            assert site.amc_request_with_retry.call_count == 2

    def test_get_members_raises_when_paginated_retry_is_exhausted(self):
        """ページネーション中の再試行失敗は部分的な一覧を返さない"""
        site = _site()
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
            mock_user_parser.return_value = _member_user(client=site.client)
            SiteMember.get(site, "")

        site.amc_request.assert_not_called()

    def test_get_members_missing_paginated_response_body_includes_context(self):
        """ページネーション中のbody欠落はsite/group/page付きで失敗する"""
        site = _site()
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
            mock_user_parser.return_value = _member_user(client=site.client)
            SiteMember.get(site, "")

        site.amc_request.assert_not_called()
        assert mock_user_parser.call_count == 1

    def test_get_members_malformed_user_includes_site_group_page_row_and_value_context(self):
        """メンバー行のprintuser異常値はsite/group/page/row/value付きで失敗する"""
        site = _site()
        site.unix_name = "test-site"
        response = self._members_response(
            """
                <table>
                    <tr>
                        <td><span class="printuser">
                            <a onclick="WIKIDOT.page.listeners.userInfo(latest); return false;" href="#">User1</a>
                        </span></td>
                    </tr>
                </table>
            """
        )
        site.amc_request_with_retry.return_value = (response,)

        with pytest.raises(
            NoElementException,
            match=(
                r"Site member user is malformed for site: test-site, group: members, page: 1, row: 1, "
                r"field=user, value=WIKIDOT\.page\.listeners\.userInfo\(latest\); return false;"
            ),
        ):
            SiteMember.get(site, "")

        site.amc_request.assert_not_called()

    def test_get_members_malformed_joined_at_includes_site_group_page_row_and_value_context(self):
        """メンバー行のodate異常値はsite/group/page/row/value付きで失敗する"""
        site = _site()
        site.unix_name = "test-site"
        response = self._members_response(
            """
                <table>
                    <tr>
                        <td><span class="printuser">
                            <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">User1</a>
                        </span></td>
                        <td><span class="odate time_latest">invalid</span></td>
                    </tr>
                </table>
            """
        )
        site.amc_request_with_retry.return_value = (response,)

        with (
            patch("wikidot.module.site_member.user_parser") as mock_user_parser,
            pytest.raises(
                NoElementException,
                match=(
                    r"Site member joined_at is malformed for site: test-site, group: members, page: 1, row: 1, "
                    r"field=joined_at, value=time_latest"
                ),
            ),
        ):
            mock_user_parser.return_value = _member_user(client=site.client)
            SiteMember.get(site, "")

        site.amc_request.assert_not_called()

    def test_get_members_ignores_non_numeric_pager_links(self):
        """数値ページがないpagerでは単一ページとして扱う"""
        site = _site()
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
            mock_user_parser.return_value = _member_user(client=site.client)

            members = SiteMember.get(site, "")

            assert len(members) == 1
            site.amc_request.assert_not_called()
            site.amc_request_with_retry.assert_called_once()

    def test_get_members_ignores_member_row_pager_markup(self):
        """メンバー行内のpager風マークアップをページネーションとして扱わない"""
        site = _site()
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
            mock_user_parser.return_value = _member_user(client=site.client)

            members = SiteMember.get(site, "")

        assert len(members) == 1
        site.amc_request.assert_not_called()
        site.amc_request_with_retry.assert_called_once()

    def test_get_admins_group(self):
        """管理者グループ取得"""
        site = _site()
        response = MagicMock()
        response.json.return_value = {"body": "<table></table>"}
        site.amc_request_with_retry.return_value = (response,)

        SiteMember.get(site, "admins")

        call_args = site.amc_request_with_retry.call_args[0][0][0]
        assert call_args["group"] == "admins"

    def test_get_moderators_group(self):
        """モデレーターグループ取得"""
        site = _site()
        response = MagicMock()
        response.json.return_value = {"body": "<table></table>"}
        site.amc_request_with_retry.return_value = (response,)

        SiteMember.get(site, "moderators")

        call_args = site.amc_request_with_retry.call_args[0][0][0]
        assert call_args["group"] == "moderators"

    def test_get_invalid_group_raises(self):
        """無効なグループでValueError"""
        site = _site()

        with pytest.raises(ValueError, match="Invalid group"):
            SiteMember.get(site, "invalid_group")

    @pytest.mark.parametrize("site", [None, True, "test-site", {"unix_name": "test-site"}, object()])
    def test_get_rejects_malformed_site_before_request(self, site: object):
        """SiteMember.getは不正なsiteをリクエスト前に拒否する"""
        bad_site: Any = site

        with pytest.raises(ValueError, match="site must be a Site"):
            SiteMember.get(bad_site, "")

    def test_get_default_group(self):
        """デフォルトグループ（None）"""
        site = _site()
        response = MagicMock()
        response.json.return_value = {"body": "<table></table>"}
        site.amc_request_with_retry.return_value = (response,)

        SiteMember.get(site, None)

        call_args = site.amc_request_with_retry.call_args[0][0][0]
        assert call_args["group"] == ""


class TestSiteMemberChangeGroup:
    """SiteMember._change_groupのテスト"""

    @staticmethod
    def _user(user_id: int = 12345, name: str = "TestUser", client: Any | None = None) -> User:
        return _member_user(user_id=user_id, name=name, client=client)

    def test_to_moderator_success(self):
        """モデレーター昇格成功"""
        site = _site()
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        site.amc_request.return_value = (mock_response,)
        user = self._user(client=site.client)
        member = SiteMember(site=site, user=user, joined_at=None)

        member.to_moderator()

        call_args = site.amc_request.call_args[0][0][0]
        assert call_args["action"] == "ManageSiteMembershipAction"
        assert call_args["event"] == "toModerators"
        assert call_args["user_id"] == 12345

    def test_remove_moderator_success(self):
        """モデレーター降格成功"""
        site = _site()
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        site.amc_request.return_value = (mock_response,)
        user = self._user(client=site.client)
        member = SiteMember(site=site, user=user, joined_at=None)

        member.remove_moderator()

        call_args = site.amc_request.call_args[0][0][0]
        assert call_args["event"] == "removeModerator"

    def test_to_admin_success(self):
        """管理者昇格成功"""
        site = _site()
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        site.amc_request.return_value = (mock_response,)
        user = self._user(client=site.client)
        member = SiteMember(site=site, user=user, joined_at=None)

        member.to_admin()

        call_args = site.amc_request.call_args[0][0][0]
        assert call_args["event"] == "toAdmins"

    def test_remove_admin_success(self):
        """管理者降格成功"""
        site = _site()
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        site.amc_request.return_value = (mock_response,)
        user = self._user(client=site.client)
        member = SiteMember(site=site, user=user, joined_at=None)

        member.remove_admin()

        call_args = site.amc_request.call_args[0][0][0]
        assert call_args["event"] == "removeAdmin"

    @pytest.mark.parametrize(
        "method_name",
        ["to_moderator", "remove_moderator", "to_admin", "remove_admin"],
    )
    def test_change_group_accepts_zero_user_id(self, method_name: str) -> None:
        """ゼロのメンバーユーザーIDは権限変更payloadにそのまま使える"""
        site = _site()
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        site.amc_request.return_value = (mock_response,)
        user = self._user(user_id=0, client=site.client)
        member = SiteMember(site=site, user=user, joined_at=None)

        getattr(member, method_name)()

        call_args = site.amc_request.call_args[0][0][0]
        assert call_args["user_id"] == 0

    @pytest.mark.parametrize(
        ("method_name", "cleared_cache", "preserved_cache"),
        [
            ("to_moderator", "_moderators", "_admins"),
            ("remove_moderator", "_moderators", "_admins"),
            ("to_admin", "_admins", "_moderators"),
            ("remove_admin", "_admins", "_moderators"),
        ],
    )
    def test_change_group_success_invalidates_affected_role_cache(
        self, method_name: str, cleared_cache: str, preserved_cache: str
    ):
        """権限変更成功後は対象ロールのメンバー一覧キャッシュを再取得させる"""
        site = _site()
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        site.amc_request.return_value = (mock_response,)
        cached_members = [object()]
        cached_moderators = [object()]
        cached_admins = [object()]
        site._members = cached_members
        site._moderators = cached_moderators
        site._admins = cached_admins
        user = self._user(client=site.client)
        member = SiteMember(site=site, user=user, joined_at=None)

        getattr(member, method_name)()

        assert getattr(site, cleared_cache) is None
        assert getattr(site, preserved_cache) is (cached_admins if preserved_cache == "_admins" else cached_moderators)
        assert site._members is cached_members

    def test_change_group_already_moderator_error(self):
        """既にモデレーターの場合のエラー"""
        site = _site()
        user = self._user(client=site.client)
        member = SiteMember(site=site, user=user, joined_at=None)

        site.amc_request.side_effect = WikidotStatusCodeException(
            "already_moderator",
            "already_moderator",
        )

        with pytest.raises(TargetErrorException, match="already moderator"):
            member.to_moderator()

    def test_change_group_already_admin_error(self):
        """既に管理者の場合のエラー"""
        site = _site()
        user = self._user(client=site.client)
        member = SiteMember(site=site, user=user, joined_at=None)

        site.amc_request.side_effect = WikidotStatusCodeException(
            "already_admin",
            "already_admin",
        )

        with pytest.raises(TargetErrorException, match="already admin"):
            member.to_admin()

    def test_change_group_not_already_error(self):
        """権限を持っていない場合のエラー"""
        site = _site()
        user = self._user(client=site.client)
        member = SiteMember(site=site, user=user, joined_at=None)

        site.amc_request.side_effect = WikidotStatusCodeException(
            "not_already",
            "not_already",
        )

        with pytest.raises(TargetErrorException, match="not moderator/admin"):
            member.remove_moderator()

    def test_change_group_invalid_event_raises(self):
        """無効なイベントでValueError"""
        site = _site()
        user = self._user(client=site.client)
        member = SiteMember(site=site, user=user, joined_at=None)

        with pytest.raises(ValueError, match="Invalid event"):
            member._change_group("invalidEvent")

    def test_change_group_missing_action_status_includes_site_user_event_and_field_context(self):
        """権限変更応答のstatus欠落は文脈付きNoElementException"""
        site = _site()
        site.unix_name = "test-site"
        cached_moderators = [object()]
        cached_admins = [object()]
        site._moderators = cached_moderators
        site._admins = cached_admins
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        site.amc_request.return_value = (mock_response,)
        user = self._user(client=site.client)
        member = SiteMember(site=site, user=user, joined_at=None)

        with pytest.raises(
            NoElementException,
            match=(
                r"Site member action response is malformed for site: test-site, user: TestUser "
                r"\(id=12345, event=toModerators, field=status\)"
            ),
        ):
            member.to_moderator()

        assert mock_response.json.call_count == 1
        assert site._moderators is cached_moderators
        assert site._admins is cached_admins

    def test_change_group_not_logged_in_raises_before_request(self):
        """未ログイン時は権限変更リクエストを送らない"""
        site = _site()
        site.client.login_check.side_effect = LoginRequiredException("Login required")
        user = self._user(client=site.client)
        member = SiteMember(site=site, user=user, joined_at=None)

        with pytest.raises(LoginRequiredException):
            member.to_moderator()

        site.amc_request.assert_not_called()

    def test_change_group_other_error_reraises(self):
        """その他のエラーは再送出"""
        site = _site()
        user = self._user(client=site.client)
        member = SiteMember(site=site, user=user, joined_at=None)

        site.amc_request.side_effect = WikidotStatusCodeException(
            "some_other_error",
            "some_other_error",
        )

        with pytest.raises(WikidotStatusCodeException):
            member.to_moderator()

    def test_change_group_rejects_non_user_before_login(self):
        """SiteMember.userがAbstractUserでなければログイン確認前に拒否する"""
        site = _site()
        site.client.login_check = MagicMock()
        site.amc_request = MagicMock()
        bad_user: Any = {"id": 12345, "name": "TestUser"}
        member = SiteMember(site=site, user=self._user(client=site.client), joined_at=None)
        member.user = bad_user

        with pytest.raises(ValueError, match="member.user must be an AbstractUser"):
            member.to_moderator()

        site.client.login_check.assert_not_called()
        site.amc_request.assert_not_called()

    def test_change_group_rejects_malformed_site_before_login(self):
        """SiteMember.siteがSiteでなければログイン確認前に拒否する"""
        site = _site()
        member = SiteMember(site=site, user=self._user(client=site.client), joined_at=None)
        bad_site = MagicMock()
        bad_site.client.login_check = MagicMock()
        bad_site.amc_request = MagicMock()
        bad_site._moderators = [object()]
        bad_site._admins = [object()]
        malformed_site: Any = bad_site
        member.site = malformed_site

        with pytest.raises(ValueError, match="site must be a Site"):
            member.to_moderator()

        bad_site.client.login_check.assert_not_called()
        bad_site.amc_request.assert_not_called()
        assert bad_site._moderators
        assert bad_site._admins

    @pytest.mark.parametrize(
        ("user_kwargs", "message"),
        [
            ({"id": None, "name": "TestUser"}, "member.user.id must be an integer"),
            ({"id": True, "name": "TestUser"}, "member.user.id must be an integer"),
            ({"id": 12345, "name": None}, "member.user.name must be a string"),
        ],
    )
    def test_change_group_rejects_malformed_user_before_login(self, user_kwargs: dict[str, Any], message: str) -> None:
        """SiteMember.userの必須フィールド不正はログイン確認やAMCリクエスト前に拒否する"""
        site = _site()
        site.client.login_check = MagicMock()
        site.amc_request = MagicMock()
        bad_user = User(client=site.client, id=12345, name="TestUser", unix_name="test-user", avatar_url=None)
        for field, value in user_kwargs.items():
            setattr(bad_user, field, value)
        member = SiteMember(site=site, user=bad_user, joined_at=None)

        with pytest.raises(ValueError, match=message):
            member.to_moderator()

        site.client.login_check.assert_not_called()
        site.amc_request.assert_not_called()

    @pytest.mark.parametrize("user_id", [-1, -100])
    @pytest.mark.parametrize(
        "method_name",
        ["to_moderator", "remove_moderator", "to_admin", "remove_admin"],
    )
    def test_change_group_rejects_negative_user_id_before_login(self, method_name: str, user_id: int) -> None:
        """権限変更は保持済みメンバーIDが負数の場合にログイン確認前に拒否する"""
        site = _site()
        site.client.login_check = MagicMock()
        site.amc_request = MagicMock()
        cached_moderators = [object()]
        cached_admins = [object()]
        site._moderators = cached_moderators
        site._admins = cached_admins
        bad_user = self._user(client=site.client)
        bad_user.id = user_id
        member = SiteMember(site=site, user=bad_user, joined_at=None)

        with pytest.raises(ValueError, match="member.user.id must be non-negative"):
            getattr(member, method_name)()

        site.client.login_check.assert_not_called()
        site.amc_request.assert_not_called()
        assert site._moderators is cached_moderators
        assert site._admins is cached_admins

    def test_change_group_rejects_user_from_different_client_before_login(self) -> None:
        """権限変更時のSiteMember.userはsiteと同じClientだけ受け付ける"""
        site = _site()
        site.client.login_check = MagicMock()
        site.amc_request = MagicMock()
        member = SiteMember(site=site, user=self._user(client=site.client), joined_at=None)
        member.user = self._user(client=_client())

        with pytest.raises(ValueError, match="member.user must belong to the site"):
            member.to_moderator()

        site.client.login_check.assert_not_called()
        site.amc_request.assert_not_called()
