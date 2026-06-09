"""SiteApplicationモジュールのユニットテスト"""

from typing import Any
from unittest.mock import MagicMock, create_autospec, patch

import pytest

from wikidot.common.exceptions import (
    ForbiddenException,
    LoginRequiredException,
    NoElementException,
    NotFoundException,
    UnexpectedException,
    WikidotStatusCodeException,
)
from wikidot.connector.ajax import AjaxModuleConnectorConfig
from wikidot.module.client import Client
from wikidot.module.site import Site
from wikidot.module.site_application import SiteApplication
from wikidot.module.user import User


def create_mock_client(is_logged_in: bool = True) -> MagicMock:
    """Clientクラスのモックを作成（isinstance()チェックを通過する）"""
    mock_client = create_autospec(Client, instance=True)
    mock_client.is_logged_in = is_logged_in
    if is_logged_in:
        mock_client.login_check.return_value = None
    else:
        mock_client.login_check.side_effect = LoginRequiredException("Login required")
    return mock_client


def _application_user(client: Any | None = None, user_id: int = 12345, name: str = "TestUser") -> User:
    return User(client=client or create_mock_client(), id=user_id, name=name, unix_name="test-user")


def _site(client: Any | None = None) -> Any:
    site: Any = Site(
        client=client or create_mock_client(),
        id=123456,
        title="Test Site",
        unix_name="test-site",
        domain="test-site.wikidot.com",
        ssl_supported=True,
    )
    site.amc_request = MagicMock()
    site.amc_request_with_retry = MagicMock()
    return site


class TestSiteApplicationDataclass:
    """SiteApplicationデータクラスのテスト"""

    def test_init(self):
        """初期化"""
        site = _site()
        user = _application_user(site.client)

        app = SiteApplication(site=site, user=user, text="Please let me join")

        assert app.site == site
        assert app.user == user
        assert app.text == "Please let me join"

    def test_str(self):
        """文字列表現"""
        site = _site()
        user = _application_user(site.client)

        app = SiteApplication(site=site, user=user, text="Application text")

        result = str(app)
        assert "SiteApplication" in result
        assert "user=" in result
        assert "site=" in result
        assert "text=" in result

    @pytest.mark.parametrize("site", [None, True, "test-site", {"unix_name": "test-site"}, object()])
    def test_init_rejects_malformed_sites(self, site: object):
        """SiteApplication.siteがSiteでなければ初期化時に拒否する"""
        user = _application_user()
        bad_site: Any = site

        with pytest.raises(ValueError, match="site must be a Site"):
            SiteApplication(site=bad_site, user=user, text="")

    @pytest.mark.parametrize("user", [None, True, "TestUser", {"id": 12345}, object()])
    def test_init_rejects_malformed_users(self, user: object):
        """SiteApplication.userがAbstractUserでなければ初期化時に拒否する"""
        site = _site()
        bad_user: Any = user

        with pytest.raises(ValueError, match="application.user must be an AbstractUser"):
            SiteApplication(site=site, user=bad_user, text="")

    def test_init_rejects_user_from_different_client(self):
        """SiteApplication.userが別client由来なら初期化時に拒否する"""
        site = _site()
        other_client = create_mock_client()
        user = _application_user(other_client)

        with pytest.raises(ValueError, match="application.user must belong to the site"):
            SiteApplication(site=site, user=user, text="")

    @pytest.mark.parametrize("user_id", [-1, -100])
    def test_init_rejects_negative_user_id(self, user_id: int) -> None:
        """SiteApplication.userのIDが負数なら初期化時に拒否する"""
        site = _site()
        user = _application_user(site.client)
        user.id = user_id

        with pytest.raises(ValueError, match="application.user.id must be non-negative"):
            SiteApplication(site=site, user=user, text="")

    @pytest.mark.parametrize("retained_user_id", [True, False, "12345", 12345.0, []])
    def test_init_rejects_malformed_retained_user_id(self, retained_user_id: object) -> None:
        """SiteApplication.userの保持IDが不正型なら初期化時に拒否する"""
        site = _site()
        user = _application_user(site.client)
        bad_user_id: Any = retained_user_id
        user.id = bad_user_id

        with pytest.raises(ValueError, match="application.user.id must be an integer or None"):
            SiteApplication(site=site, user=user, text="")

    @pytest.mark.parametrize("retained_user_id", [None, 0])
    def test_init_accepts_optional_retained_user_id(self, retained_user_id: int | None) -> None:
        """SiteApplication.userの保持IDはNoneと0を有効な値として扱う"""
        site = _site()
        user = _application_user(site.client)
        user.id = retained_user_id

        app = SiteApplication(site=site, user=user, text="")

        assert app.user.id == retained_user_id

    def test_init_accepts_zero_user_id(self) -> None:
        """SiteApplication.userのIDは0を有効な値として扱う"""
        site = _site()
        user = _application_user(site.client, user_id=0)

        app = SiteApplication(site=site, user=user, text="")

        assert app.user.id == 0

    @pytest.mark.parametrize("text", [None, True, 123, ["Please let me join"], object()])
    def test_init_rejects_malformed_text(self, text: object):
        """SiteApplication.textが文字列でなければ初期化時に拒否する"""
        site = _site()
        user = _application_user(site.client)
        bad_text: Any = text

        with pytest.raises(ValueError, match="application.text must be a string"):
            SiteApplication(site=site, user=user, text=bad_text)


class TestSiteApplicationAcquireAll:
    """SiteApplication.acquire_allのテスト"""

    @pytest.mark.parametrize("site", [None, True, "test-site", {"unix_name": "test-site"}, object()])
    def test_acquire_all_rejects_malformed_site_before_login(self, site: object) -> None:
        """SiteApplication.acquire_allは不正なsiteをログイン確認前に拒否する"""
        bad_site: Any = site

        with pytest.raises(ValueError, match="site must be a Site"):
            SiteApplication.acquire_all(bad_site)

    def test_site_applications_retries_transient_fetch_failures(self):
        """site.applicationsは一時的なAMC失敗を再試行して申請を返す"""
        mock_client = create_mock_client(is_logged_in=True)
        mock_client.amc_client = MagicMock()
        mock_client.amc_client.config = AjaxModuleConnectorConfig(
            retry_batch_size=1,
            retry_max_retries=1,
        )
        site = Site(
            client=mock_client,
            id=123456,
            title="Test Site",
            unix_name="test-site",
            domain="test-site.wikidot.com",
            ssl_supported=True,
        )

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <div>
                    <h3><span class="printuser">
                        <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">User1</a>
                    </span></h3>
                    <table>
                        <tr>
                            <td>Label</td>
                            <td>I want to join this wiki</td>
                        </tr>
                    </table>
                </div>
            """
        }
        mock_client.amc_client.request.side_effect = [
            (RuntimeError("temporary failure"),),
            (response,),
        ]

        with patch("wikidot.module.site_application.user_parser") as mock_user_parser:
            mock_user = _application_user(mock_client)
            mock_user_parser.return_value = mock_user

            applications = site.applications

        assert len(applications) == 1
        assert applications[0].user == mock_user
        assert applications[0].text == "I want to join this wiki"
        assert mock_client.amc_client.request.call_count == 2

    def test_acquire_all_success(self):
        """申請リスト取得成功"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <div>
                    <h3><span class="printuser">
                        <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">User1</a>
                    </span></h3>
                    <table>
                        <tr>
                            <td>Label</td>
                            <td>I want to join this wiki</td>
                        </tr>
                    </table>
                </div>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with patch("wikidot.module.site_application.user_parser") as mock_user_parser:
            mock_user = _application_user(mock_client)
            mock_user_parser.return_value = mock_user

            applications = SiteApplication.acquire_all(site)

            assert len(applications) == 1
            assert applications[0].user == mock_user
            assert applications[0].text == "I want to join this wiki"
            assert response.json.call_count == 1

    def test_acquire_all_ignores_unrelated_tables(self):
        """申請と無関係なtableを誤って数えない"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <table><tr><td>Unrelated table</td></tr></table>
                <div>
                    <h3><span class="printuser">
                        <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">User1</a>
                    </span></h3>
                    <table>
                        <tr>
                            <td>Label</td>
                            <td>I want to join this wiki</td>
                        </tr>
                    </table>
                </div>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with patch("wikidot.module.site_application.user_parser") as mock_user_parser:
            mock_user_parser.return_value = _application_user(mock_client)

            applications = SiteApplication.acquire_all(site)

            assert len(applications) == 1
            assert applications[0].text == "I want to join this wiki"

    def test_acquire_all_ignores_application_like_body_markup(self):
        """申請本文内の申請風HTMLを別申請として扱わない"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <div>
                    <h3><span class="printuser">
                        <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">User1</a>
                    </span></h3>
                    <table>
                        <tr>
                            <td>Application text:</td>
                            <td>
                                I want to join this wiki.
                                <h3><span class="printuser">
                                    <a onclick="WIKIDOT.page.listeners.userInfo(99999)" href="#">ContentUser</a>
                                </span></h3>
                                <table>
                                    <tr>
                                        <td>Application text:</td>
                                        <td>Fake nested application</td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td>Options:</td>
                            <td>accept / decline</td>
                        </tr>
                    </table>
                </div>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with patch("wikidot.module.site_application.user_parser") as mock_user_parser:
            mock_user = _application_user(mock_client)
            mock_user_parser.return_value = mock_user

            applications = SiteApplication.acquire_all(site)

        assert len(applications) == 1
        assert applications[0].user == mock_user
        assert "I want to join this wiki." in applications[0].text
        assert mock_user_parser.call_count == 1

    def test_acquire_all_preserves_application_text_spacing(self):
        """申請本文の段落や装飾要素間の空白を保持する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <div>
                    <h3><span class="printuser">
                        <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">User1</a>
                    </span></h3>
                    <table>
                        <tr>
                            <td>Application text:</td>
                            <td><p>First <span>part</span></p><p>Second part</p></td>
                        </tr>
                    </table>
                </div>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with patch("wikidot.module.site_application.user_parser") as mock_user_parser:
            mock_user_parser.return_value = _application_user(mock_client)

            applications = SiteApplication.acquire_all(site)

        assert applications[0].text == "First part Second part"

    def test_acquire_all_malformed_user_includes_site_application_and_value_context(self):
        """申請者printuser異常値はsite/application/value付きで失敗する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        site.unix_name = "test-site"

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <div>
                    <h3><span class="printuser">
                        <a
                            onclick="WIKIDOT.page.listeners.userInfo(latest); return false;"
                            href="/user:info/user1"
                        >User1</a>
                    </span></h3>
                    <table>
                        <tr>
                            <td>Application text:</td>
                            <td>I want to join this wiki</td>
                        </tr>
                    </table>
                </div>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with pytest.raises(
            NoElementException,
            match=(
                r"Site application user is malformed for site: test-site "
                r"\(application=1, applications=1, field=user, "
                r"value=WIKIDOT\.page\.listeners\.userInfo\(latest\); return false;\)"
            ),
        ):
            SiteApplication.acquire_all(site)

        site.amc_request.assert_not_called()

    def test_acquire_all_empty(self):
        """申請なしの場合"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)

        response = MagicMock()
        response.json.return_value = {"body": "<div>No applications</div>"}
        site.amc_request_with_retry.return_value = (response,)

        applications = SiteApplication.acquire_all(site)

        assert len(applications) == 0

    def test_acquire_all_raises_when_retry_is_exhausted(self):
        """申請リスト取得の再試行が尽きた場合は明示的に失敗する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        site.unix_name = "test-site"
        site.amc_request_with_retry.return_value = (None,)

        with pytest.raises(UnexpectedException, match="Cannot retrieve site applications for site: test-site"):
            SiteApplication.acquire_all(site)

        site.amc_request.assert_not_called()

    def test_acquire_all_missing_response_body_includes_site_context(self):
        """申請リスト応答のbody欠落時はサイト名付きで失敗する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        site.unix_name = "test-site"

        response = MagicMock()
        response.json.return_value = {}
        site.amc_request_with_retry.return_value = (response,)

        with pytest.raises(
            NoElementException,
            match="Site application list response body is not found for site: test-site",
        ):
            SiteApplication.acquire_all(site)

        site.amc_request.assert_not_called()

    def test_acquire_all_malformed_response_body_type_includes_site_context(self):
        """申請リスト応答のbody型異常はサイト名と型付きで失敗する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        site.unix_name = "test-site"

        response = MagicMock()
        response.json.return_value = {"body": ["not", "html"]}
        site.amc_request_with_retry.return_value = (response,)

        with (
            patch("wikidot.module.site_application.user_parser") as mock_user_parser,
            pytest.raises(
                NoElementException,
                match=(
                    "Site application list response body is malformed for site: test-site "
                    "\\(field=body, expected=str, actual=list\\)"
                ),
            ),
        ):
            SiteApplication.acquire_all(site)

        site.amc_request.assert_not_called()
        mock_user_parser.assert_not_called()

    def test_acquire_all_forbidden(self):
        """権限がない場合ForbiddenException"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)

        response = MagicMock()
        response.json.return_value = {"body": '<a onclick="WIKIDOT.page.listeners.loginClick(event)">Login</a>'}
        site.amc_request_with_retry.return_value = (response,)

        with pytest.raises(ForbiddenException, match="not allowed"):
            SiteApplication.acquire_all(site)

    def test_acquire_all_not_logged_in(self):
        """未ログインでLoginRequiredException"""
        mock_client = create_mock_client(is_logged_in=False)
        site = _site(mock_client)

        with pytest.raises(LoginRequiredException):
            SiteApplication.acquire_all(site)

    def test_acquire_all_length_mismatch(self):
        """ユーザー要素とテキスト要素の数が不一致の場合はサイト名と件数を含めて失敗する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        site.unix_name = "test-site"

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <div>
                    <h3><span class="printuser">
                        <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="/user:info/user1">User1</a>
                    </span></h3>
                    <h3><span class="printuser">
                        <a onclick="WIKIDOT.page.listeners.userInfo(67890)" href="/user:info/user2">User2</a>
                    </span></h3>
                    <table>
                        <tr>
                            <td>Label</td>
                            <td>Only one table</td>
                        </tr>
                    </table>
                </div>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with pytest.raises(
            UnexpectedException,
            match="Length of application users and text tables are different for site: test-site "
            r"\(users=2, text_tables=1\)",
        ):
            SiteApplication.acquire_all(site)

    def test_acquire_all_missing_text_cell(self):
        """申請本文セルがない場合はサイト名と申請位置を含めて失敗する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        site.unix_name = "test-site"

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <div>
                    <h3><span class="printuser">
                        <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">User1</a>
                    </span></h3>
                    <table><tr><td>Label only</td></tr></table>
                </div>
            """
        }
        site.amc_request_with_retry.return_value = (response,)

        with pytest.raises(
            NoElementException,
            match="Application text cell is not found for site: test-site "
            r"\(application=1, applications=1, cells=1\)",
        ):
            SiteApplication.acquire_all(site)


class TestSiteApplicationProcess:
    """SiteApplication._processのテスト"""

    def test_accept_success(self):
        """承認成功"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        site.amc_request.return_value = (mock_response,)
        user = User(client=mock_client, id=12345, name="TestUser")

        app = SiteApplication(site=site, user=user, text="")
        app.accept()

        call_args = site.amc_request.call_args[0][0][0]
        assert call_args["action"] == "ManageSiteMembershipAction"
        assert call_args["type"] == "accept"
        assert call_args["user_id"] == 12345
        assert mock_response.json.call_count == 1

    def test_accept_accepts_zero_user_id(self):
        """ゼロの申請者ユーザーIDは承認payloadにそのまま使える"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        site.amc_request.return_value = (mock_response,)
        user = User(client=mock_client, id=0, name="ZeroUser")

        app = SiteApplication(site=site, user=user, text="")
        app.accept()

        call_args = site.amc_request.call_args[0][0][0]
        assert call_args["user_id"] == 0

    def test_accept_success_invalidates_members_cache(self):
        """申請承認成功後はサイトメンバー一覧キャッシュを再取得させる"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        site.amc_request.return_value = (mock_response,)
        cached_members = [object()]
        cached_moderators = [object()]
        cached_admins = [object()]
        site._members = cached_members
        site._moderators = cached_moderators
        site._admins = cached_admins
        user = User(client=mock_client, id=12345, name="TestUser")

        app = SiteApplication(site=site, user=user, text="")
        app.accept()

        assert site._members is None
        assert site._moderators is cached_moderators
        assert site._admins is cached_admins

    def test_decline_success(self):
        """拒否成功"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        site.amc_request.return_value = (mock_response,)
        user = User(client=mock_client, id=12345, name="TestUser")

        app = SiteApplication(site=site, user=user, text="")
        app.decline()

        call_args = site.amc_request.call_args[0][0][0]
        assert call_args["type"] == "decline"
        assert call_args["text"] == "your application has been declined"
        assert mock_response.json.call_count == 1

    def test_decline_success_preserves_members_cache(self):
        """申請拒否成功後はメンバー一覧キャッシュを維持する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        site.amc_request.return_value = (mock_response,)
        cached_members = [object()]
        site._members = cached_members
        user = User(client=mock_client, id=12345, name="TestUser")

        app = SiteApplication(site=site, user=user, text="")
        app.decline()

        assert site._members is cached_members

    @pytest.mark.parametrize("user_id", [-1, -100])
    def test_decline_rejects_negative_user_id_before_login(self, user_id: int) -> None:
        """申請拒否は保持済み申請者IDが負数の場合にログイン確認前に拒否する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        cached_members = [object()]
        site._members = cached_members
        bad_user = User(client=mock_client, id=12345, name="TestUser")

        app = SiteApplication(site=site, user=bad_user, text="")
        app.user.id = user_id

        with pytest.raises(ValueError, match="application.user.id must be non-negative"):
            app.decline()

        mock_client.login_check.assert_not_called()
        site.amc_request.assert_not_called()
        assert site._members is cached_members

    def test_accept_rejects_non_user_before_login(self) -> None:
        """申請承認は申請者オブジェクト不正をログイン確認前に拒否する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        cached_members = [object()]
        site._members = cached_members
        bad_user: Any = {"id": 12345, "name": "TestUser"}

        app = SiteApplication(site=site, user=_application_user(mock_client), text="")
        app.user = bad_user

        with pytest.raises(ValueError, match="application.user must be an AbstractUser"):
            app.accept()

        mock_client.login_check.assert_not_called()
        site.amc_request.assert_not_called()
        assert site._members is cached_members

    def test_accept_rejects_malformed_site_before_login(self) -> None:
        """申請承認はサイトオブジェクト不正をログイン確認前に拒否する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        cached_members = [object()]
        site._members = cached_members
        bad_site = MagicMock()
        bad_site.client = mock_client
        bad_site.amc_request = MagicMock()

        app = SiteApplication(site=site, user=_application_user(mock_client), text="")
        app.site = bad_site

        with pytest.raises(ValueError, match="site must be a Site"):
            app.accept()

        mock_client.login_check.assert_not_called()
        bad_site.amc_request.assert_not_called()
        assert site._members is cached_members

    def test_accept_rejects_user_from_different_client_before_login(self) -> None:
        """申請承認は別client由来の申請者をログイン確認前に拒否する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        cached_members = [object()]
        site._members = cached_members
        other_client = create_mock_client()

        app = SiteApplication(site=site, user=_application_user(mock_client), text="")
        app.user = _application_user(other_client)

        with pytest.raises(ValueError, match="application.user must belong to the site"):
            app.accept()

        mock_client.login_check.assert_not_called()
        site.amc_request.assert_not_called()
        assert site._members is cached_members

    @pytest.mark.parametrize(
        ("user_kwargs", "message"),
        [
            ({"id": None, "name": "TestUser"}, "application.user.id must be an integer"),
            ({"id": True, "name": "TestUser"}, "application.user.id must be an integer"),
            ({"id": 12345, "name": None}, "application.user.name must be a string"),
        ],
    )
    def test_accept_rejects_malformed_user_before_login(self, user_kwargs: dict[str, Any], message: str) -> None:
        """申請承認は申請者ID/名前不正をログイン確認前に拒否する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        cached_members = [object()]
        site._members = cached_members
        bad_user = User(client=mock_client, id=12345, name="TestUser")
        app = SiteApplication(site=site, user=bad_user, text="")
        for field, value in user_kwargs.items():
            setattr(bad_user, field, value)

        with pytest.raises(ValueError, match=message):
            app.accept()

        mock_client.login_check.assert_not_called()
        site.amc_request.assert_not_called()
        assert site._members is cached_members

    @pytest.mark.parametrize("user_id", [-1, -100])
    def test_accept_rejects_negative_user_id_before_login(self, user_id: int) -> None:
        """申請承認は保持済み申請者IDが負数の場合にログイン確認前に拒否する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        cached_members = [object()]
        site._members = cached_members
        bad_user = User(client=mock_client, id=12345, name="TestUser")

        app = SiteApplication(site=site, user=bad_user, text="")
        app.user.id = user_id

        with pytest.raises(ValueError, match="application.user.id must be non-negative"):
            app.accept()

        mock_client.login_check.assert_not_called()
        site.amc_request.assert_not_called()
        assert site._members is cached_members

    def test_accept_missing_action_status_includes_site_user_event_type_and_field_context(self):
        """申請承認応答のstatus欠落は文脈付きNoElementException"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        site.unix_name = "test-site"
        cached_members = [object()]
        site._members = cached_members
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        site.amc_request.return_value = (mock_response,)
        user = User(client=mock_client, id=12345, name="TestUser")

        app = SiteApplication(site=site, user=user, text="")

        with pytest.raises(
            NoElementException,
            match=(
                r"Site application action response is malformed for site: test-site, user: TestUser "
                r"\(id=12345, event=acceptApplication, type=accept, field=status\)"
            ),
        ):
            app.accept()

        assert mock_response.json.call_count == 1
        assert site._members is cached_members

    def test_accept_malformed_action_status_type_includes_site_user_event_type_and_type_context(self):
        """申請承認応答のstatus型不正は文脈付きNoElementException"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        site.unix_name = "test-site"
        cached_members = [object()]
        site._members = cached_members
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": ["not-ok"]}
        site.amc_request.return_value = (mock_response,)
        user = User(client=mock_client, id=12345, name="TestUser")

        app = SiteApplication(site=site, user=user, text="")

        with pytest.raises(
            NoElementException,
            match=(
                r"Site application action response is malformed for site: test-site, user: TestUser "
                r"\(id=12345, event=acceptApplication, type=accept, field=status, expected=str, actual=list\)"
            ),
        ):
            app.accept()

        assert mock_response.json.call_count == 1
        assert site._members is cached_members

    def test_accept_explicit_non_ok_action_status_raises_status_exception(self):
        """申請承認応答の非ok statusは成功扱いしない"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        site.unix_name = "test-site"
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "other_error"}
        site.amc_request.return_value = (mock_response,)
        user = User(client=mock_client, id=12345, name="TestUser")

        app = SiteApplication(site=site, user=user, text="")

        with pytest.raises(WikidotStatusCodeException) as exc_info:
            app.accept()

        assert exc_info.value.status_code == "other_error"

    def test_process_invalid_action(self):
        """無効なアクションでValueError"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        user = User(client=mock_client, id=12345, name="TestUser")

        app = SiteApplication(site=site, user=user, text="")

        with pytest.raises(ValueError, match="Invalid action"):
            app._process("invalid")

    def test_process_not_logged_in(self):
        """未ログインでLoginRequiredException"""
        mock_client = create_mock_client(is_logged_in=False)
        site = _site(mock_client)
        user = User(client=mock_client, id=12345, name="TestUser")

        app = SiteApplication(site=site, user=user, text="")

        with pytest.raises(LoginRequiredException):
            app.accept()

    def test_process_application_not_found(self):
        """申請が見つからない場合NotFoundException"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        user = User(client=mock_client, id=12345, name="TestUser")

        site.amc_request.side_effect = WikidotStatusCodeException(
            "no_application",
            "no_application",
        )

        app = SiteApplication(site=site, user=user, text="")

        with pytest.raises(NotFoundException, match="Application not found"):
            app.accept()

    def test_process_other_error_reraises(self):
        """その他のエラーは再送出"""
        mock_client = create_mock_client(is_logged_in=True)
        site = _site(mock_client)
        user = User(client=mock_client, id=12345, name="TestUser")

        site.amc_request.side_effect = WikidotStatusCodeException(
            "other_error",
            "other_error",
        )

        app = SiteApplication(site=site, user=user, text="")

        with pytest.raises(WikidotStatusCodeException):
            app.accept()
