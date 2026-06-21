"""userパーサーのユニットテスト"""

from typing import Any
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

from wikidot.module.user import AnonymousUser, DeletedUser, GuestUser, User, WikidotUser
from wikidot.util.parser.user import user_parse


class TestUserParserRegularUser:
    """通常ユーザーのパーステスト"""

    def test_parse_regular_user(self, mock_client_no_http: MagicMock, printuser_regular_html: str) -> None:
        """通常のprintuser要素をパースできる"""
        soup = BeautifulSoup(printuser_regular_html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        result = user_parse(mock_client_no_http, elem)

        assert isinstance(result, User)
        assert result.id == 12345
        assert result.name == "test-user"
        assert result.unix_name == "test-user"
        # パーサーはIDからavatar_urlを生成する
        assert result.avatar_url == "http://www.wikidot.com/avatar.php?userid=12345"

    def test_parse_user_extracts_onclick_id(self, mock_client_no_http: MagicMock) -> None:
        """onclick属性からユーザーIDを抽出できる"""
        html = '<span class="printuser"><a href="http://www.wikidot.com/user:info/another-user" onclick="WIKIDOT.page.listeners.userInfo(99999); return false;">another-user</a></span>'
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        result = user_parse(mock_client_no_http, elem)

        assert isinstance(result, User)
        assert result.id == 99999
        assert result.name == "another-user"

    def test_parse_regular_user_with_malformed_onclick_id_raises(self, mock_client_no_http: MagicMock) -> None:
        """通常ユーザーのuserInfo値が非数値ならraw欠落扱いにしない"""
        html = '<span class="printuser"><a href="http://www.wikidot.com/user:info/bad-user" onclick="WIKIDOT.page.listeners.userInfo(latest); return false;">bad-user</a></span>'
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        with pytest.raises(ValueError, match="user id is malformed: latest"):
            user_parse(mock_client_no_http, elem)

    def test_parse_regular_user_rejects_non_ascii_digit_onclick_id(self, mock_client_no_http: MagicMock) -> None:
        """通常ユーザーのuserInfo値はASCII数字だけを受け入れる"""
        fullwidth_user_id = "\uff11\uff12\uff13\uff14\uff15"
        html = (
            '<span class="printuser"><a href="http://www.wikidot.com/user:info/fullwidth-user" '
            f'onclick="WIKIDOT.page.listeners.userInfo({fullwidth_user_id}); return false;">'
            "fullwidth-user</a></span>"
        )
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        with pytest.raises(ValueError) as exc_info:
            user_parse(mock_client_no_http, elem)

        assert str(exc_info.value) == f"user id is malformed: {fullwidth_user_id}"

    def test_parse_regular_user_rejects_trailing_onclick_action_text(self, mock_client_no_http: MagicMock) -> None:
        """通常ユーザーのonclickは既知のuserInfo文だけを受け入れる"""
        onclick = "WIKIDOT.page.listeners.userInfo(12345); return false; extraAction()"
        html = (
            '<span class="printuser"><a href="http://www.wikidot.com/user:info/trailing-user" '
            f'onclick="{onclick}">trailing-user</a></span>'
        )
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        with pytest.raises(ValueError) as exc_info:
            user_parse(mock_client_no_http, elem)

        assert str(exc_info.value) == f"user onclick is malformed: {onclick}"

    def test_parse_regular_user_preserves_display_name_text_spacing(self, mock_client_no_http: MagicMock) -> None:
        """装飾要素を含む表示名の語境界を保持する"""
        html = """
        <span class="printuser">
            <a href="http://www.wikidot.com/user:info/first-part-user"
               onclick="WIKIDOT.page.listeners.userInfo(12345); return false;">
                <span>First <em>Part</em></span><span>User</span>
            </a>
        </span>
        """
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        result = user_parse(mock_client_no_http, elem)

        assert isinstance(result, User)
        assert result.name == "First Part User"
        assert result.unix_name == "first-part-user"

    def test_parse_https_user_url(self, mock_client_no_http: MagicMock) -> None:
        """httpsのuser:info URLからunix nameを抽出できる"""
        html = '<span class="printuser"><a href="https://www.wikidot.com/user:info/secure-user" onclick="WIKIDOT.page.listeners.userInfo(22222); return false;">secure-user</a></span>'
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        result = user_parse(mock_client_no_http, elem)

        assert isinstance(result, User)
        assert result.unix_name == "secure-user"

    def test_parse_regular_user_without_href_raises(self, mock_client_no_http: MagicMock) -> None:
        """hrefなし通常ユーザーは空のunix_nameを作らず失敗する"""
        html = '<span class="printuser"><a onclick="WIKIDOT.page.listeners.userInfo(12345); return false;">test-user</a></span>'
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        with pytest.raises(ValueError, match="user href is not found"):
            user_parse(mock_client_no_http, elem)

    @pytest.mark.parametrize("onclick", ["", "WIKIDOT.page.listeners.userInfo(); return false;"])
    def test_parse_regular_user_without_onclick_id_raises(
        self, mock_client_no_http: MagicMock, onclick: str
    ) -> None:
        html = (
            '<span class="printuser"><a href="http://www.wikidot.com/user:info/missing-id" '
            f'onclick="{onclick}">missing-id</a></span>'
        )
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        expected = "user onclick is malformed" if "userInfo(" in onclick else "user id is not found"
        with pytest.raises(ValueError, match=expected):
            user_parse(mock_client_no_http, elem)

    @pytest.mark.parametrize(
        "href",
        [
            "/user:info/test-user/extra",
            "http://example.com/user:info/test-user",
            "javascript:;",
        ],
    )
    def test_parse_regular_user_with_malformed_href_raises(self, mock_client_no_http: MagicMock, href: str) -> None:
        """通常ユーザーのhrefがuser:info経路でない場合はraw値付きで失敗する"""
        html = (
            f'<span class="printuser"><a href="{href}" '
            'onclick="WIKIDOT.page.listeners.userInfo(12345); return false;">test-user</a></span>'
        )
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        with pytest.raises(ValueError) as exc_info:
            user_parse(mock_client_no_http, elem)

        assert str(exc_info.value) == f"user href is malformed: {href}"


class TestUserParserDeletedUser:
    """削除済みユーザーのパーステスト"""

    def test_parse_deleted_user_string(self, mock_client_no_http: MagicMock) -> None:
        result = user_parse(mock_client_no_http, "(user deleted)")

        assert isinstance(result, DeletedUser)
        assert result.id == 0

    def test_parse_non_deleted_string_raises(self, mock_client_no_http: MagicMock) -> None:
        with pytest.raises(ValueError, match="elem must be bs4.Tag except DeletedUser"):
            user_parse(mock_client_no_http, "not deleted")

    def test_parse_non_tag_input_raises(self, mock_client_no_http: MagicMock) -> None:
        elem: Any = object()

        with pytest.raises(ValueError, match="elem must be bs4.Tag except DeletedUser"):
            user_parse(mock_client_no_http, elem)

    def test_parse_deleted_user_with_id(self, mock_client_no_http: MagicMock, printuser_deleted_html: str) -> None:
        """data-id付き削除済みユーザーをパースできる"""
        soup = BeautifulSoup(printuser_deleted_html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        result = user_parse(mock_client_no_http, elem)

        assert isinstance(result, DeletedUser)
        assert result.id == 99999

    def test_parse_deleted_user_without_data_id(
        self, mock_client_no_http: MagicMock, printuser_deleted_no_id_html: str
    ) -> None:
        """data-idなし削除済みユーザーをパースできる（ID=0）"""
        soup = BeautifulSoup(printuser_deleted_no_id_html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        result = user_parse(mock_client_no_http, elem)

        assert isinstance(result, DeletedUser)
        assert result.id == 0

    def test_parse_deleted_user_with_malformed_data_id_raises(self, mock_client_no_http: MagicMock) -> None:
        """data-idが整数でない削除済みユーザーは文脈付きで失敗する"""
        html = '<span class="printuser deleted" data-id="latest">(account deleted)</span>'
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        with pytest.raises(ValueError, match="deleted user id is malformed: latest"):
            user_parse(mock_client_no_http, elem)

    def test_parse_deleted_user_rejects_non_ascii_digit_data_id(self, mock_client_no_http: MagicMock) -> None:
        """削除済みユーザーのdata-idはASCII数字だけを受け入れる"""
        fullwidth_user_id = "\uff11\uff12\uff13"
        html = f'<span class="printuser deleted" data-id="{fullwidth_user_id}">(account deleted)</span>'
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        with pytest.raises(ValueError) as exc_info:
            user_parse(mock_client_no_http, elem)

        assert str(exc_info.value) == f"deleted user id is malformed: {fullwidth_user_id}"

    def test_parse_deleted_user_with_negative_data_id_raises(self, mock_client_no_http: MagicMock) -> None:
        """data-idが負の削除済みユーザーはパーサー文脈付きで失敗する"""
        html = '<span class="printuser deleted" data-id="-1">(account deleted)</span>'
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        with pytest.raises(ValueError, match="deleted user id is malformed: -1"):
            user_parse(mock_client_no_http, elem)


class TestUserParserAnonymousUser:
    """匿名ユーザーのパーステスト"""

    def test_parse_anonymous_user_with_ip(self, mock_client_no_http: MagicMock, printuser_anonymous_html: str) -> None:
        """IP付き匿名ユーザーをパースできる"""
        soup = BeautifulSoup(printuser_anonymous_html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        result = user_parse(mock_client_no_http, elem)

        assert isinstance(result, AnonymousUser)
        # Wikidotは最後のオクテットをマスクして表示する
        assert result.ip == "192.168.1.x"

    def test_parse_anonymous_user_without_ip(
        self, mock_client_no_http: MagicMock, printuser_anonymous_no_ip_html: str
    ) -> None:
        """IPなし匿名ユーザーをパースできる"""
        soup = BeautifulSoup(printuser_anonymous_no_ip_html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        result = user_parse(mock_client_no_http, elem)

        assert isinstance(result, AnonymousUser)
        assert result.ip is None


class TestUserParserGuestUser:
    """ゲストユーザーのパーステスト"""

    def test_parse_guest_user(self, mock_client_no_http: MagicMock, printuser_guest_html: str) -> None:
        """Gravatarを持つゲストユーザーをパースできる"""
        soup = BeautifulSoup(printuser_guest_html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        result = user_parse(mock_client_no_http, elem)

        assert isinstance(result, GuestUser)
        assert result.name == "guest-user"
        assert result.avatar_url is not None
        assert "gravatar.com" in result.avatar_url

    def test_parse_guest_user_without_text(self, mock_client_no_http: MagicMock) -> None:
        """表示名が空のゲストユーザーでも例外にしない"""
        html = '<span class="printuser"><img src="https://www.gravatar.com/avatar/abc123" /></span>'
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        result = user_parse(mock_client_no_http, elem)

        assert isinstance(result, GuestUser)
        assert result.name == ""

    def test_parse_guest_user_preserves_display_name_text_spacing(self, mock_client_no_http: MagicMock) -> None:
        """ゲスト表示名内の装飾要素や空白を切り落とさない"""
        html = """
        <span class="printuser avatarhover">
            <a href="javascript:;">
                <img class="small" src="https://www.gravatar.com/avatar/abc123" alt="">
            </a>
            <span>First <em>Part</em></span><span>Guest</span> (ゲスト)
        </span>
        """
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        result = user_parse(mock_client_no_http, elem)

        assert isinstance(result, GuestUser)
        assert result.name == "First Part Guest"


class TestUserParserWikidotUser:
    """Wikidotシステムユーザーのパーステスト"""

    def test_parse_wikidot_user(self, mock_client_no_http: MagicMock, printuser_wikidot_html: str) -> None:
        """Wikidotシステムユーザーをパースできる"""
        soup = BeautifulSoup(printuser_wikidot_html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        result = user_parse(mock_client_no_http, elem)

        assert isinstance(result, WikidotUser)
        assert result.name == "Wikidot"


class TestUserParserEdgeCases:
    """エッジケースのテスト"""

    def test_parse_no_link_element_raises(self, mock_client_no_http: MagicMock) -> None:
        """リンク要素がない場合はValueErrorを発生させる"""
        html = '<span class="printuser">No links here</span>'
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        with pytest.raises(ValueError, match="link element"):
            user_parse(mock_client_no_http, elem)

    def test_parse_rejects_non_tag_link_result(self, mock_client_no_http: MagicMock, monkeypatch) -> None:
        soup = BeautifulSoup('<span class="printuser">broken</span>', "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None
        links: list[Any] = [object()]
        monkeypatch.setattr(elem, "find_all", lambda *args, **kwargs: links)

        with pytest.raises(ValueError, match="link element is not found"):
            user_parse(mock_client_no_http, elem)

    def test_parse_user_with_special_characters_in_name(self, mock_client_no_http: MagicMock) -> None:
        """特殊文字を含むユーザー名をパースできる"""
        html = '<span class="printuser"><a href="http://www.wikidot.com/user:info/user-name-123" onclick="WIKIDOT.page.listeners.userInfo(11111); return false;">user_name_123</a></span>'
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        result = user_parse(mock_client_no_http, elem)

        assert isinstance(result, User)
        assert result.name == "user_name_123"
        assert result.unix_name == "user-name-123"

    def test_parse_user_with_img_without_src(self, mock_client_no_http: MagicMock) -> None:
        """srcなしimgを含む通常ユーザーをパースできる"""
        html = """
        <span class="printuser">
            <a href="http://www.wikidot.com/user:info/test-user" onclick="WIKIDOT.page.listeners.userInfo(12345); return false;">
                <img class="small" alt="test-user" />
            </a>
            <a href="http://www.wikidot.com/user:info/test-user" onclick="WIKIDOT.page.listeners.userInfo(12345); return false;">test-user</a>
        </span>
        """
        soup = BeautifulSoup(html, "lxml")
        elem = soup.select_one("span.printuser")
        assert elem is not None

        result = user_parse(mock_client_no_http, elem)

        assert isinstance(result, User)
        assert result.id == 12345
