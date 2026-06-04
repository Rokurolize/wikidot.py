"""SiteApplicationモジュールのユニットテスト"""

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


def create_mock_client(is_logged_in: bool = True) -> MagicMock:
    """Clientクラスのモックを作成（isinstance()チェックを通過する）"""
    mock_client = create_autospec(Client, instance=True)
    mock_client.is_logged_in = is_logged_in
    if is_logged_in:
        mock_client.login_check.return_value = None
    else:
        mock_client.login_check.side_effect = LoginRequiredException("Login required")
    return mock_client


class TestSiteApplicationDataclass:
    """SiteApplicationデータクラスのテスト"""

    def test_init(self):
        """初期化"""
        site = MagicMock()
        user = MagicMock()

        app = SiteApplication(site=site, user=user, text="Please let me join")

        assert app.site == site
        assert app.user == user
        assert app.text == "Please let me join"

    def test_str(self):
        """文字列表現"""
        site = MagicMock()
        site.__str__ = lambda x: "TestSite"
        user = MagicMock()
        user.__str__ = lambda x: "TestUser"

        app = SiteApplication(site=site, user=user, text="Application text")

        result = str(app)
        assert "SiteApplication" in result
        assert "user=" in result
        assert "site=" in result
        assert "text=" in result


class TestSiteApplicationAcquireAll:
    """SiteApplication.acquire_allのテスト"""

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
            mock_user = MagicMock()
            mock_user_parser.return_value = mock_user

            applications = site.applications

        assert len(applications) == 1
        assert applications[0].user == mock_user
        assert applications[0].text == "I want to join this wiki"
        assert mock_client.amc_client.request.call_count == 2

    def test_acquire_all_success(self):
        """申請リスト取得成功"""
        mock_client = create_mock_client(is_logged_in=True)
        site = MagicMock()
        site.client = mock_client

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
            mock_user = MagicMock()
            mock_user_parser.return_value = mock_user

            applications = SiteApplication.acquire_all(site)

            assert len(applications) == 1
            assert applications[0].user == mock_user
            assert applications[0].text == "I want to join this wiki"
            assert response.json.call_count == 1

    def test_acquire_all_ignores_unrelated_tables(self):
        """申請と無関係なtableを誤って数えない"""
        mock_client = create_mock_client(is_logged_in=True)
        site = MagicMock()
        site.client = mock_client

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
            mock_user_parser.return_value = MagicMock()

            applications = SiteApplication.acquire_all(site)

            assert len(applications) == 1
            assert applications[0].text == "I want to join this wiki"

    def test_acquire_all_ignores_application_like_body_markup(self):
        """申請本文内の申請風HTMLを別申請として扱わない"""
        mock_client = create_mock_client(is_logged_in=True)
        site = MagicMock()
        site.client = mock_client

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
            mock_user = MagicMock()
            mock_user_parser.return_value = mock_user

            applications = SiteApplication.acquire_all(site)

        assert len(applications) == 1
        assert applications[0].user == mock_user
        assert "I want to join this wiki." in applications[0].text
        assert mock_user_parser.call_count == 1

    def test_acquire_all_preserves_application_text_spacing(self):
        """申請本文の段落や装飾要素間の空白を保持する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = MagicMock()
        site.client = mock_client

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
            mock_user_parser.return_value = MagicMock()

            applications = SiteApplication.acquire_all(site)

        assert applications[0].text == "First part Second part"

    def test_acquire_all_empty(self):
        """申請なしの場合"""
        mock_client = create_mock_client(is_logged_in=True)
        site = MagicMock()
        site.client = mock_client

        response = MagicMock()
        response.json.return_value = {"body": "<div>No applications</div>"}
        site.amc_request_with_retry.return_value = (response,)

        applications = SiteApplication.acquire_all(site)

        assert len(applications) == 0

    def test_acquire_all_raises_when_retry_is_exhausted(self):
        """申請リスト取得の再試行が尽きた場合は明示的に失敗する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = MagicMock()
        site.client = mock_client
        site.unix_name = "test-site"
        site.amc_request_with_retry.return_value = (None,)

        with pytest.raises(UnexpectedException, match="Cannot retrieve site applications for site: test-site"):
            SiteApplication.acquire_all(site)

        site.amc_request.assert_not_called()

    def test_acquire_all_missing_response_body_includes_site_context(self):
        """申請リスト応答のbody欠落時はサイト名付きで失敗する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = MagicMock()
        site.client = mock_client
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

    def test_acquire_all_forbidden(self):
        """権限がない場合ForbiddenException"""
        mock_client = create_mock_client(is_logged_in=True)
        site = MagicMock()
        site.client = mock_client

        response = MagicMock()
        response.json.return_value = {"body": '<a onclick="WIKIDOT.page.listeners.loginClick(event)">Login</a>'}
        site.amc_request_with_retry.return_value = (response,)

        with pytest.raises(ForbiddenException, match="not allowed"):
            SiteApplication.acquire_all(site)

    def test_acquire_all_not_logged_in(self):
        """未ログインでLoginRequiredException"""
        mock_client = create_mock_client(is_logged_in=False)
        site = MagicMock()
        site.client = mock_client

        with pytest.raises(LoginRequiredException):
            SiteApplication.acquire_all(site)

    def test_acquire_all_length_mismatch(self):
        """ユーザー要素とテキスト要素の数が不一致の場合はサイト名と件数を含めて失敗する"""
        mock_client = create_mock_client(is_logged_in=True)
        site = MagicMock()
        site.client = mock_client
        site.unix_name = "test-site"

        response = MagicMock()
        response.json.return_value = {
            "body": """
                <div>
                    <h3><span class="printuser">
                        <a onclick="WIKIDOT.page.listeners.userInfo(12345)" href="#">User1</a>
                    </span></h3>
                    <h3><span class="printuser">
                        <a onclick="WIKIDOT.page.listeners.userInfo(67890)" href="#">User2</a>
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
        site = MagicMock()
        site.client = mock_client
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
        site = MagicMock()
        site.client = mock_client
        user = MagicMock()
        user.id = 12345

        app = SiteApplication(site=site, user=user, text="")
        app.accept()

        call_args = site.amc_request.call_args[0][0][0]
        assert call_args["action"] == "ManageSiteMembershipAction"
        assert call_args["type"] == "accept"
        assert call_args["user_id"] == 12345

    def test_decline_success(self):
        """拒否成功"""
        mock_client = create_mock_client(is_logged_in=True)
        site = MagicMock()
        site.client = mock_client
        user = MagicMock()
        user.id = 12345

        app = SiteApplication(site=site, user=user, text="")
        app.decline()

        call_args = site.amc_request.call_args[0][0][0]
        assert call_args["type"] == "decline"
        assert call_args["text"] == "your application has been declined"

    def test_process_invalid_action(self):
        """無効なアクションでValueError"""
        mock_client = create_mock_client(is_logged_in=True)
        site = MagicMock()
        site.client = mock_client
        user = MagicMock()

        app = SiteApplication(site=site, user=user, text="")

        with pytest.raises(ValueError, match="Invalid action"):
            app._process("invalid")

    def test_process_not_logged_in(self):
        """未ログインでLoginRequiredException"""
        mock_client = create_mock_client(is_logged_in=False)
        site = MagicMock()
        site.client = mock_client
        user = MagicMock()

        app = SiteApplication(site=site, user=user, text="")

        with pytest.raises(LoginRequiredException):
            app.accept()

    def test_process_application_not_found(self):
        """申請が見つからない場合NotFoundException"""
        mock_client = create_mock_client(is_logged_in=True)
        site = MagicMock()
        site.client = mock_client
        user = MagicMock()
        user.id = 12345
        user.__str__ = lambda x: "TestUser"

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
        site = MagicMock()
        site.client = mock_client
        user = MagicMock()
        user.id = 12345

        site.amc_request.side_effect = WikidotStatusCodeException(
            "other_error",
            "other_error",
        )

        app = SiteApplication(site=site, user=user, text="")

        with pytest.raises(WikidotStatusCodeException):
            app.accept()
