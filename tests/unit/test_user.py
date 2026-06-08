"""Userモジュールのユニットテスト"""

from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_httpx import HTTPXMock

from wikidot.common.exceptions import NoElementException, NotFoundException
from wikidot.connector.ajax import AjaxModuleConnectorConfig, AjaxRequestHeader
from wikidot.module.client import Client
from wikidot.module.user import (
    AnonymousUser,
    DeletedUser,
    GuestUser,
    User,
    UserCollection,
    WikidotUser,
)


def create_lookup_client() -> Any:
    client = object.__new__(Client)
    client.amc_client = MagicMock()
    client.amc_client.config = AjaxModuleConnectorConfig(retry_interval=0)
    client.amc_client.header = AjaxRequestHeader()
    return client


class TestUserDataclasses:
    """ユーザーデータクラスのテスト"""

    def test_user_str(self, mock_client_no_http: MagicMock) -> None:
        """User.__str__が正しい文字列を返す"""
        user = User(
            client=mock_client_no_http,
            id=12345,
            name="test-user",
            unix_name="test-user",
            avatar_url="http://example.com/avatar.png",
        )

        result = str(user)

        assert "User(" in result
        assert "id=12345" in result
        assert "name=test-user" in result

    def test_deleted_user_defaults(self, mock_client_no_http: MagicMock) -> None:
        """DeletedUserのデフォルト値が正しい"""
        user = DeletedUser(client=mock_client_no_http, id=99999)

        assert user.name == "account deleted"
        assert user.unix_name == "account_deleted"
        assert user.avatar_url is None

    def test_anonymous_user_defaults(self, mock_client_no_http: MagicMock) -> None:
        """AnonymousUserのデフォルト値が正しい"""
        user = AnonymousUser(client=mock_client_no_http, ip="192.168.1.1")

        assert user.name == "Anonymous"
        assert user.unix_name == "anonymous"
        assert user.id is None
        assert user.avatar_url is None

    def test_guest_user_defaults(self, mock_client_no_http: MagicMock) -> None:
        """GuestUserのデフォルト値が正しい"""
        user = GuestUser(
            client=mock_client_no_http,
            name="Guest Name",
            avatar_url="http://gravatar.com/avatar/abc",
        )

        assert user.id is None
        assert user.unix_name is None
        assert user.ip is None

    def test_wikidot_user_defaults(self, mock_client_no_http: MagicMock) -> None:
        """WikidotUserのデフォルト値が正しい"""
        user = WikidotUser(client=mock_client_no_http)

        assert user.name == "Wikidot"
        assert user.unix_name == "wikidot"
        assert user.id is None
        assert user.avatar_url is None

    def test_anonymous_user_allows_missing_ip(self, mock_client_no_http: MagicMock) -> None:
        user = AnonymousUser(client=mock_client_no_http)

        assert user.ip is None

    def test_user_accepts_valid_optional_scalar_fields(self, mock_client_no_http: MagicMock) -> None:
        user = User(
            client=mock_client_no_http,
            id=None,
            name=None,
            unix_name=None,
            avatar_url=None,
            ip=None,
        )

        assert user.id is None
        assert user.name is None
        assert user.unix_name is None
        assert user.avatar_url is None
        assert user.ip is None

    def test_regular_user_rejects_ip(self, mock_client_no_http: MagicMock) -> None:
        with pytest.raises(ValueError, match="ip must be None"):
            User(client=mock_client_no_http, ip="192.168.1.1")

    @pytest.mark.parametrize("user_id", [True, "12345", 12345.0, object()])
    def test_user_rejects_malformed_id(self, mock_client_no_http: MagicMock, user_id: object) -> None:
        bad_user_id: Any = user_id

        with pytest.raises(ValueError, match="id must be an integer or None"):
            User(client=mock_client_no_http, id=bad_user_id)

    @pytest.mark.parametrize("client", [None, True, "test-client", {"username": "test-user"}, object()])
    @pytest.mark.parametrize(
        "factory",
        [
            lambda client: User(client=client, id=12345, name="test-user", unix_name="test-user"),
            lambda client: DeletedUser(client=client, id=99999),
            lambda client: AnonymousUser(client=client, ip="192.168.1.1"),
            lambda client: GuestUser(client=client, name="Guest Name", avatar_url="http://gravatar.com/avatar/abc"),
            lambda client: WikidotUser(client=client),
        ],
    )
    def test_user_subclasses_reject_malformed_client(self, client: object, factory: Any) -> None:
        with pytest.raises(ValueError, match="client must be a Client"):
            factory(client)

    @pytest.mark.parametrize(
        ("field", "value", "message"),
        [
            ("name", True, "name must be a string or None"),
            ("name", 12345, "name must be a string or None"),
            ("unix_name", True, "unix_name must be a string or None"),
            ("unix_name", ["test-user"], "unix_name must be a string or None"),
            ("avatar_url", True, "avatar_url must be a string or None"),
            ("avatar_url", {"url": "http://example.com/avatar.png"}, "avatar_url must be a string or None"),
            ("ip", True, "ip must be a string or None"),
            ("ip", 192168001001, "ip must be a string or None"),
        ],
    )
    def test_user_rejects_malformed_optional_text_fields(
        self, mock_client_no_http: MagicMock, field: str, value: object, message: str
    ) -> None:
        user_kwargs: dict[str, Any] = {field: value}

        with pytest.raises(ValueError, match=message):
            User(client=mock_client_no_http, **user_kwargs)

    @pytest.mark.parametrize(
        ("factory", "message"),
        [
            (lambda client: DeletedUser(client=client, name="deleted"), "name must be account deleted"),
            (lambda client: DeletedUser(client=client, unix_name="deleted"), "unix_name must be account_deleted"),
            (
                lambda client: DeletedUser(client=client, avatar_url="http://example.com/avatar.png"),
                "avatar_url must be None",
            ),
            (lambda client: DeletedUser(client=client, ip="192.168.1.1"), "ip must be None"),
            (lambda client: AnonymousUser(client=client, id=12345), "id must be None"),
            (lambda client: AnonymousUser(client=client, name="Anon"), "name must be Anonymous"),
            (lambda client: AnonymousUser(client=client, unix_name="anon"), "unix_name must be anonymous"),
            (
                lambda client: AnonymousUser(client=client, avatar_url="http://example.com/avatar.png"),
                "avatar_url must be None",
            ),
            (lambda client: GuestUser(client=client, id=12345), "id must be None"),
            (lambda client: GuestUser(client=client, unix_name="guest"), "unix_name must be None"),
            (lambda client: GuestUser(client=client, ip="192.168.1.1"), "ip must be None"),
            (lambda client: WikidotUser(client=client, id=12345), "id must be None"),
            (lambda client: WikidotUser(client=client, name="System"), "name must be Wikidot"),
            (lambda client: WikidotUser(client=client, unix_name="system"), "unix_name must be wikidot"),
            (
                lambda client: WikidotUser(client=client, avatar_url="http://example.com/avatar.png"),
                "avatar_url must be None",
            ),
            (lambda client: WikidotUser(client=client, ip="192.168.1.1"), "ip must be None"),
        ],
    )
    def test_special_user_subclasses_reject_identity_overrides(
        self, mock_client_no_http: MagicMock, factory: Any, message: str
    ) -> None:
        with pytest.raises(ValueError, match=message):
            factory(mock_client_no_http)


class TestUserFromName:
    """User.from_name のテスト"""

    def test_from_name_success(self, httpx_mock: HTTPXMock, user_profile_html: str) -> None:
        """ユーザー名からユーザーを取得できる"""
        client = create_lookup_client()
        httpx_mock.add_response(
            url="https://www.wikidot.com/user:info/test-user",
            text=user_profile_html,
        )

        result = User.from_name(client, "test-user")

        assert result is not None
        assert isinstance(result, User)
        assert result.id == 12345
        assert result.name == "test-user"

    def test_from_name_not_found_no_raise(self, httpx_mock: HTTPXMock, user_profile_not_found_html: str) -> None:
        """ユーザーが見つからない場合Noneを返す"""
        client = create_lookup_client()
        httpx_mock.add_response(
            url="https://www.wikidot.com/user:info/nonexistent",
            text=user_profile_not_found_html,
        )

        result = User.from_name(client, "nonexistent", raise_when_not_found=False)

        assert result is None

    def test_from_name_not_found_raise(self, httpx_mock: HTTPXMock, user_profile_not_found_html: str) -> None:
        """ユーザーが見つからない場合NotFoundException"""
        client = create_lookup_client()
        httpx_mock.add_response(
            url="https://www.wikidot.com/user:info/nonexistent",
            text=user_profile_not_found_html,
        )

        with pytest.raises(NotFoundException):
            User.from_name(client, "nonexistent", raise_when_not_found=True)

    def test_from_name_rejects_non_string_name_before_request(
        self, mock_client_no_http: MagicMock, httpx_mock: HTTPXMock
    ) -> None:
        """ユーザー名が文字列でない場合はリクエスト前に拒否"""
        bad_name: Any = {"name": "test-user"}

        with pytest.raises(ValueError, match="name must be a string"):
            User.from_name(mock_client_no_http, bad_name)

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("name", ["", "   "])
    def test_from_name_rejects_blank_name_before_request(
        self, mock_client_no_http: MagicMock, httpx_mock: HTTPXMock, name: str
    ) -> None:
        """ユーザー名が空の場合はリクエスト前に拒否"""
        with pytest.raises(ValueError, match="name must not be empty"):
            User.from_name(mock_client_no_http, name)

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("raise_when_not_found", [None, "false", 0, 1])
    def test_from_name_rejects_non_bool_raise_when_not_found_before_request(
        self, mock_client_no_http: MagicMock, httpx_mock: HTTPXMock, raise_when_not_found: Any
    ) -> None:
        """raise_when_not_foundはboolだけ受け付ける"""
        with pytest.raises(ValueError, match="raise_when_not_found must be a boolean"):
            User.from_name(mock_client_no_http, "test-user", raise_when_not_found=raise_when_not_found)

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("client", [None, True, "test-client", {"username": "test-user"}, object()])
    def test_from_name_rejects_malformed_client_before_request(self, httpx_mock: HTTPXMock, client: object) -> None:
        """clientがClientでない場合はリクエスト前に拒否"""
        bad_client: Any = client

        with pytest.raises(ValueError, match="client must be a Client"):
            User.from_name(bad_client, "test-user")

        assert httpx_mock.get_requests() == []


class TestUserCollection:
    """UserCollection のテスト"""

    @pytest.mark.parametrize("users", [True, False, "1", ("1",), 1])
    def test_init_rejects_non_list_users(self, users: Any) -> None:
        """UserCollection初期化時のusersはlistまたはNoneだけ受け付ける"""
        with pytest.raises(ValueError, match="users must be a list or None"):
            UserCollection(users)

    @pytest.mark.parametrize("user", [None, True, "1", {"id": 1}])
    def test_init_rejects_non_user_entries(self, user: Any) -> None:
        """UserCollection初期化時のusers要素はAbstractUserだけ受け付ける"""
        with pytest.raises(ValueError, match="users list entries must be AbstractUser"):
            UserCollection([user])

    def test_from_names_rejects_non_list_names_before_request(
        self, mock_client_no_http: MagicMock, httpx_mock: HTTPXMock
    ) -> None:
        """一括取得の入力がリストでない場合はリクエスト前に拒否"""
        bad_names: Any = {"name": "bad-user"}

        with pytest.raises(ValueError, match="names must be a list"):
            UserCollection.from_names(mock_client_no_http, bad_names)

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("client", [None, True, "test-client", {"username": "test-user"}, object()])
    def test_from_names_rejects_malformed_client_before_request(self, httpx_mock: HTTPXMock, client: object) -> None:
        """一括取得のclientがClientでない場合はリクエスト前に拒否"""
        bad_client: Any = client

        with pytest.raises(ValueError, match="client must be a Client"):
            UserCollection.from_names(bad_client, ["test-user"])

        assert httpx_mock.get_requests() == []

    def test_from_names_rejects_non_string_name_before_request(
        self, mock_client_no_http: MagicMock, httpx_mock: HTTPXMock
    ) -> None:
        """一括取得のユーザー名が文字列でない場合はリクエスト前に拒否"""
        bad_name: Any = {"name": "bad-user"}

        with pytest.raises(ValueError, match="names list entries must be strings"):
            UserCollection.from_names(mock_client_no_http, ["ok-user", bad_name])

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("name", ["", "   "])
    def test_from_names_rejects_blank_name_before_request(
        self, mock_client_no_http: MagicMock, httpx_mock: HTTPXMock, name: str
    ) -> None:
        """一括取得のユーザー名が空の場合はリクエスト前に拒否"""
        with pytest.raises(ValueError, match="names list entries must not be empty"):
            UserCollection.from_names(mock_client_no_http, ["ok-user", name])

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("raise_when_not_found", [None, "false", 0, 1])
    def test_from_names_rejects_non_bool_raise_when_not_found_before_request(
        self, mock_client_no_http: MagicMock, httpx_mock: HTTPXMock, raise_when_not_found: Any
    ) -> None:
        """一括取得のraise_when_not_foundはboolだけ受け付ける"""
        with pytest.raises(ValueError, match="raise_when_not_found must be a boolean"):
            UserCollection.from_names(mock_client_no_http, ["test-user"], raise_when_not_found=raise_when_not_found)

        assert httpx_mock.get_requests() == []

    def test_from_names_multiple(self, httpx_mock: HTTPXMock) -> None:
        """複数ユーザーを一度に取得できる"""
        client = create_lookup_client()
        html1 = """
        <!DOCTYPE html>
        <html>
        <head><title>user1 - Wikidot</title></head>
        <body>
        <div id="user-info">
            <h1 class="profile-title">user1</h1>
            <a class="btn btn-default btn-xs" href="http://www.wikidot.com/userkarma.php/111">
                Karma
            </a>
        </div>
        </body>
        </html>
        """
        html2 = """
        <!DOCTYPE html>
        <html>
        <head><title>user2 - Wikidot</title></head>
        <body>
        <div id="user-info">
            <h1 class="profile-title">user2</h1>
            <a class="btn btn-default btn-xs" href="http://www.wikidot.com/userkarma.php/222">
                Karma
            </a>
        </div>
        </body>
        </html>
        """
        httpx_mock.add_response(
            url="https://www.wikidot.com/user:info/user1",
            text=html1,
        )
        httpx_mock.add_response(
            url="https://www.wikidot.com/user:info/user2",
            text=html2,
        )

        result = UserCollection.from_names(client, ["user1", "user2"])

        assert len(result) == 2
        names = [u.name for u in result]
        assert "user1" in names
        assert "user2" in names

    def test_from_names_skip_not_found(self, httpx_mock: HTTPXMock, user_profile_not_found_html: str) -> None:
        """見つからないユーザーをスキップできる"""
        client = create_lookup_client()
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>exists - Wikidot</title></head>
        <body>
        <div id="user-info">
            <h1 class="profile-title">exists</h1>
            <a class="btn btn-default btn-xs" href="http://www.wikidot.com/account/messages#/new/333">
                PM
            </a>
        </div>
        </body>
        </html>
        """
        httpx_mock.add_response(
            url="https://www.wikidot.com/user:info/exists",
            text=html,
        )
        httpx_mock.add_response(
            url="https://www.wikidot.com/user:info/nonexistent",
            text=user_profile_not_found_html,
        )

        result = UserCollection.from_names(client, ["exists", "nonexistent"], raise_when_not_found=False)

        assert len(result) == 1
        assert result[0].name == "exists"

    def test_from_names_extracts_id_from_href_with_query(self, httpx_mock: HTTPXMock) -> None:
        """クエリ付きID URLからユーザーIDを抽出できる"""
        client = create_lookup_client()
        html = """
        <!DOCTYPE html>
        <html>
        <body>
        <div id="user-info">
            <h1 class="profile-title">user-query</h1>
            <a class="btn btn-default btn-xs" href="http://www.wikidot.com/userkarma.php/444?tab=karma">
                Karma
            </a>
        </div>
        </body>
        </html>
        """
        httpx_mock.add_response(
            url="https://www.wikidot.com/user:info/user-query",
            text=html,
        )

        result = UserCollection.from_names(client, ["user-query"])

        assert len(result) == 1
        assert result[0].id == 444

    def test_from_names_preserves_profile_title_text_spacing(self, httpx_mock: HTTPXMock) -> None:
        """プロフィール名内の装飾タグや隣接要素のテキストを連結しない"""
        client = create_lookup_client()
        html = """
        <!DOCTYPE html>
        <html>
        <body>
        <div id="user-info">
            <h1 class="profile-title"><span>First <em>Part</em></span><span>User</span></h1>
            <a class="btn btn-default btn-xs" href="http://www.wikidot.com/userkarma.php/555">
                Karma
            </a>
        </div>
        </body>
        </html>
        """
        httpx_mock.add_response(
            url="https://www.wikidot.com/user:info/first-part-user",
            text=html,
        )

        result = UserCollection.from_names(client, ["first-part-user"])

        assert len(result) == 1
        assert result[0].id == 555
        assert result[0].name == "First Part User"
        assert result[0].unix_name == "first-part-user"

    def test_from_names_missing_id_element(self, httpx_mock: HTTPXMock) -> None:
        """ID要素がない場合NoElementException"""
        client = create_lookup_client()
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>bad - Wikidot</title></head>
        <body>
        <div id="user-info">
            <h1 class="profile-title">bad</h1>
            <!-- ID要素がない -->
        </div>
        </body>
        </html>
        """
        httpx_mock.add_response(
            url="https://www.wikidot.com/user:info/bad",
            text=html,
        )

        with pytest.raises(
            NoElementException,
            match=r"User ID element not found for requested user: bad \(index=1\)",
        ):
            UserCollection.from_names(client, ["bad"])

    def test_from_names_malformed_id_href_raises(self, httpx_mock: HTTPXMock) -> None:
        """IDを含まないhrefはNoElementException"""
        client = create_lookup_client()
        html = """
        <!DOCTYPE html>
        <html>
        <body>
        <div id="user-info">
            <h1 class="profile-title">bad</h1>
            <a class="btn btn-default btn-xs" href="http://www.wikidot.com/userkarma.php/not-a-number">
                Karma
            </a>
        </div>
        </body>
        </html>
        """
        httpx_mock.add_response(
            url="https://www.wikidot.com/user:info/bad",
            text=html,
        )

        with pytest.raises(
            NoElementException,
            match=(
                r"User ID is malformed for requested user: bad "
                r"\(index=1, field=user_id, value=http://www\.wikidot\.com/userkarma\.php/not-a-number\)"
            ),
        ):
            UserCollection.from_names(client, ["bad"])

    def test_from_names_missing_name_element(self, httpx_mock: HTTPXMock) -> None:
        """名前要素がない場合NoElementException"""
        client = create_lookup_client()
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>bad - Wikidot</title></head>
        <body>
        <div id="user-info">
            <!-- 名前要素がない -->
            <a class="btn btn-default btn-xs" href="http://www.wikidot.com/account/messages#/new/123">
                PM
            </a>
        </div>
        </body>
        </html>
        """
        httpx_mock.add_response(
            url="https://www.wikidot.com/user:info/bad",
            text=html,
        )

        with pytest.raises(
            NoElementException,
            match=r"User name element not found for requested user: bad \(index=1\)",
        ):
            UserCollection.from_names(client, ["bad"])

    def test_iteration(self, mock_client_no_http: MagicMock) -> None:
        """UserCollectionはイテレート可能"""
        users = UserCollection(
            [
                User(client=mock_client_no_http, id=1, name="a", unix_name="a"),
                User(client=mock_client_no_http, id=2, name="b", unix_name="b"),
            ]
        )

        names = [u.name for u in users]

        assert names == ["a", "b"]
