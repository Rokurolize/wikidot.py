"""
プライベートメッセージモジュールのユニットテスト

PrivateMessage, PrivateMessageCollection, PrivateMessageInbox, PrivateMessageSentBoxクラスをテストする。
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, create_autospec, patch

import pytest

from wikidot.common.exceptions import (
    ForbiddenException,
    LoginRequiredException,
    NoElementException,
    UnexpectedException,
    WikidotStatusCodeException,
)
from wikidot.module.client import Client
from wikidot.module.private_message import (
    PrivateMessage,
    PrivateMessageCollection,
    PrivateMessageInbox,
    PrivateMessageSentBox,
)
from wikidot.module.user import User


@pytest.fixture
def mock_client():
    """モッククライアント（Clientのspec付き）"""
    client = create_autospec(Client, instance=True)
    client.is_logged_in = True
    client.amc_client = MagicMock()
    client.amc_client.config.retry_batch_size = 50
    client.amc_client.config.retry_max_retries = 3
    return client


@pytest.fixture
def mock_user(mock_client):
    """テスト用の通常ユーザー"""
    return User(
        client=mock_client,
        id=12345,
        name="test-user",
        unix_name="test-user",
        avatar_url="https://www.wikidot.com/avatar.php?userid=12345",
    )


@pytest.fixture
def sender_user(mock_client):
    """テスト用の送信者ユーザー"""
    return User(
        client=mock_client,
        id=11111,
        name="sender",
        unix_name="sender",
        avatar_url="https://www.wikidot.com/avatar.php?userid=11111",
    )


@pytest.fixture
def recipient_user(mock_client):
    """テスト用の受信者ユーザー"""
    return User(
        client=mock_client,
        id=22222,
        name="recipient",
        unix_name="recipient",
        avatar_url="https://www.wikidot.com/avatar.php?userid=22222",
    )


@pytest.fixture
def sample_message(mock_client, mock_user):
    """サンプルメッセージ"""
    return PrivateMessage(
        client=mock_client,
        id=1,
        sender=mock_user,
        recipient=mock_user,
        subject="Test Subject",
        body="Test Body",
        created_at=datetime(2023, 1, 1, 12, 0, 0),
    )


class TestPrivateMessageCollection:
    """PrivateMessageCollectionクラスのテスト"""

    def test_str_representation(self, sample_message):
        """文字列表現のテスト"""
        collection = PrivateMessageCollection([sample_message])
        assert "1 messages" in str(collection)

    def test_iter(self, sample_message):
        """イテレータのテスト"""
        collection = PrivateMessageCollection([sample_message])
        messages = list(collection)
        assert len(messages) == 1
        assert messages[0] == sample_message

    @pytest.mark.parametrize("messages", [True, False, "1", ("1",), 1])
    def test_init_rejects_non_list_messages(self, messages: object):
        """メッセージコレクションの初期化はlistまたはNoneだけ受け付ける"""
        bad_messages: Any = messages

        with pytest.raises(ValueError, match="messages must be a list or None"):
            PrivateMessageCollection(bad_messages)

    @pytest.mark.parametrize("message", [None, True, "1", {"id": 1}])
    def test_init_rejects_non_message_entries(self, message: object):
        """メッセージコレクションの初期化はPrivateMessageだけ受け付ける"""
        with pytest.raises(ValueError, match="messages list entries must be PrivateMessage"):
            PrivateMessageCollection([message])  # type: ignore[list-item]

    def test_find_existing(self, sample_message):
        """存在するメッセージの検索"""
        collection = PrivateMessageCollection([sample_message])
        result = collection.find(1)
        assert result == sample_message

    def test_find_not_existing(self, sample_message):
        """存在しないメッセージの検索"""
        collection = PrivateMessageCollection([sample_message])
        result = collection.find(999)
        assert result is None

    @pytest.mark.parametrize("bad_id", [None, True, "1", 1.0])
    def test_find_rejects_non_integer_ids(self, sample_message, bad_id: object):
        """整数以外のメッセージID検索キーを拒否する"""
        collection = PrivateMessageCollection([sample_message])
        bad_id_value: Any = bad_id

        with pytest.raises(ValueError, match="id must be an integer"):
            collection.find(bad_id_value)

    def test_from_ids_requires_login(self, mock_client):
        """from_idsはログインが必要"""
        mock_client.is_logged_in = False
        mock_client.login_check.side_effect = LoginRequiredException("Not logged in")

        with pytest.raises(LoginRequiredException):
            PrivateMessageCollection.from_ids(mock_client, [1, 2, 3])

    def test_from_ids_empty_input_skips_login_and_fetch(self, mock_client):
        """空のメッセージIDリストはログイン確認もAMC取得も行わず空コレクションを返す"""
        mock_client.is_logged_in = False
        mock_client.login_check.side_effect = LoginRequiredException("Not logged in")

        result = PrivateMessageCollection.from_ids(mock_client, [])

        assert isinstance(result, PrivateMessageCollection)
        assert len(result) == 0
        mock_client.login_check.assert_not_called()
        mock_client.amc_client.request.assert_not_called()

    def test_from_ids_rejects_non_list_message_ids_before_login(self, mock_client):
        """リストでないメッセージID入力はログイン確認やAMCリクエスト前に拒否する"""
        message_ids: Any = "12"
        mock_client.login_check = MagicMock()
        mock_client.amc_client.request = MagicMock()

        with pytest.raises(ValueError, match="message_ids must be a list"):
            PrivateMessageCollection.from_ids(mock_client, message_ids)

        mock_client.login_check.assert_not_called()
        mock_client.amc_client.request.assert_not_called()

    @pytest.mark.parametrize("message_ids", [[None], [True], ["1"], [1.25]])
    def test_from_ids_rejects_non_integer_message_id_entries_before_login(self, mock_client, message_ids):
        """メッセージIDリスト内の非整数値はログイン確認やAMCリクエスト前に拒否する"""
        bad_message_ids: Any = message_ids
        mock_client.login_check = MagicMock()
        mock_client.amc_client.request = MagicMock()

        with pytest.raises(ValueError, match="message_ids list entries must be integers"):
            PrivateMessageCollection.from_ids(mock_client, bad_message_ids)

        mock_client.login_check.assert_not_called()
        mock_client.amc_client.request.assert_not_called()

    @pytest.mark.parametrize("client", [None, True, "test-client", {"username": "test-user"}, object()])
    def test_from_ids_rejects_malformed_client_before_login(self, client: object):
        """直接メッセージ取得はClient以外の親をログイン確認前に拒否する"""
        bad_client: Any = client

        with pytest.raises(ValueError, match="client must be a Client"):
            PrivateMessageCollection.from_ids(bad_client, [1])

    def test_from_ids_success(self, mock_client, mock_user):
        """from_idsの成功ケース"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": """
            <div class="pmessage">
                <div class="header">
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/sender" onclick="WIKIDOT.page.listeners.userInfo(11111); return false;">sender</a></span>
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/recipient" onclick="WIKIDOT.page.listeners.userInfo(22222); return false;">recipient</a></span>
                    <span class="subject">Test Subject</span>
                    <span class="odate time_1234567890">01 Jan 2023 12:00</span>
                </div>
                <div class="body">Test Body</div>
            </div>
            """
        }

        mock_client.amc_client.request.return_value = [mock_response]

        with patch("wikidot.module.private_message.user_parser") as mock_user_parser:
            mock_user_parser.return_value = mock_user
            with patch("wikidot.module.private_message.odate_parser") as mock_odate_parser:
                mock_odate_parser.return_value = datetime(2023, 1, 1, 12, 0, 0)

                result = PrivateMessageCollection.from_ids(mock_client, [1])

                assert len(result) == 1
                assert result[0].id == 1

    def test_from_ids_ignores_body_header_markup(self, mock_client, sender_user, recipient_user):
        """本文内のheader風マークアップを送受信者メタデータとして扱わない"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": """
            <div class="pmessage">
                <div class="header">
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/sender" onclick="WIKIDOT.page.listeners.userInfo(11111); return false;">sender</a></span>
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/recipient" onclick="WIKIDOT.page.listeners.userInfo(22222); return false;">recipient</a></span>
                    <span class="subject">Test Subject</span>
                    <span class="odate time_1234567890">01 Jan 2023 12:00</span>
                </div>
                <div class="body">
                    Test Body
                    <div class="header">
                        <span class="printuser"><a href="http://www.wikidot.com/user:info/content-user" onclick="WIKIDOT.page.listeners.userInfo(33333); return false;">content-user</a></span>
                    </div>
                </div>
            </div>
            """
        }
        mock_client.amc_client.request.return_value = [mock_response]

        with (
            patch(
                "wikidot.module.private_message.user_parser", side_effect=[sender_user, recipient_user]
            ) as mock_user_parser,
            patch("wikidot.module.private_message.odate_parser") as mock_odate_parser,
        ):
            mock_odate_parser.return_value = datetime(2023, 1, 1, 12, 0, 0)

            result = PrivateMessageCollection.from_ids(mock_client, [1])

        assert len(result) == 1
        assert result[0].sender == sender_user
        assert result[0].recipient == recipient_user
        assert result[0].subject == "Test Subject"
        assert "Test Body" in result[0].body
        assert mock_user_parser.call_count == 2

    def test_from_ids_preserves_body_text_spacing(self, mock_client, mock_user):
        """本文内の段落や装飾タグのテキストを連結しない"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": """
            <div class="pmessage">
                <div class="header">
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/sender" onclick="WIKIDOT.page.listeners.userInfo(11111); return false;">sender</a></span>
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/recipient" onclick="WIKIDOT.page.listeners.userInfo(22222); return false;">recipient</a></span>
                    <span class="subject">Test Subject</span>
                    <span class="odate time_1234567890">01 Jan 2023 12:00</span>
                </div>
                <div class="body"><p>First <span>message</span></p><p>Second message</p></div>
            </div>
            """
        }
        mock_client.amc_client.request.return_value = [mock_response]

        with (
            patch("wikidot.module.private_message.user_parser", side_effect=[mock_user, mock_user]),
            patch("wikidot.module.private_message.odate_parser") as mock_odate_parser,
        ):
            mock_odate_parser.return_value = datetime(2023, 1, 1, 12, 0, 0)

            result = PrivateMessageCollection.from_ids(mock_client, [1])

        assert len(result) == 1
        assert result[0].body == "First message Second message"

    def test_from_ids_preserves_subject_text_spacing(self, mock_client, mock_user):
        """件名内の装飾タグや隣接要素のテキストを連結しない"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": """
            <div class="pmessage">
                <div class="header">
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/sender" onclick="WIKIDOT.page.listeners.userInfo(11111); return false;">sender</a></span>
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/recipient" onclick="WIKIDOT.page.listeners.userInfo(22222); return false;">recipient</a></span>
                    <span class="subject"><span>First <em>Part</em></span><span>Subject</span></span>
                    <span class="odate time_1234567890">01 Jan 2023 12:00</span>
                </div>
                <div class="body">Test Body</div>
            </div>
            """
        }
        mock_client.amc_client.request.return_value = [mock_response]

        with (
            patch("wikidot.module.private_message.user_parser", side_effect=[mock_user, mock_user]),
            patch("wikidot.module.private_message.odate_parser") as mock_odate_parser,
        ):
            mock_odate_parser.return_value = datetime(2023, 1, 1, 12, 0, 0)

            result = PrivateMessageCollection.from_ids(mock_client, [1])

        assert len(result) == 1
        assert result[0].subject == "First Part Subject"

    def test_from_ids_retries_transient_detail_failures(self, mock_client, mock_user):
        """一時的なAMC失敗後にメッセージ詳細取得をリトライする"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": """
            <div class="pmessage">
                <div class="header">
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/sender" onclick="WIKIDOT.page.listeners.userInfo(11111); return false;">sender</a></span>
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/recipient" onclick="WIKIDOT.page.listeners.userInfo(22222); return false;">recipient</a></span>
                    <span class="subject">Test Subject</span>
                    <span class="odate time_1234567890">01 Jan 2023 12:00</span>
                </div>
                <div class="body">Test Body</div>
            </div>
            """
        }

        mock_client.amc_client.request.side_effect = [(RuntimeError("temporary failure"),), (mock_response,)]

        with patch("wikidot.module.private_message.user_parser") as mock_user_parser:
            mock_user_parser.return_value = mock_user
            with patch("wikidot.module.private_message.odate_parser") as mock_odate_parser:
                mock_odate_parser.return_value = datetime(2023, 1, 1, 12, 0, 0)

                result = PrivateMessageCollection.from_ids(mock_client, [1])

        assert len(result) == 1
        assert mock_client.amc_client.request.call_count == 2

    def test_from_ids_deduplicates_duplicate_message_ids_preserving_order(self, mock_client, mock_user):
        """from_idsは重複IDの公開順序を保ったまま詳細リクエストを重複排除する"""

        def message_response(subject: str) -> MagicMock:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "body": f"""
                <div class="pmessage">
                    <div class="header">
                        <span class="printuser"><a href="http://www.wikidot.com/user:info/sender" onclick="WIKIDOT.page.listeners.userInfo(11111); return false;">sender</a></span>
                        <span class="printuser"><a href="http://www.wikidot.com/user:info/recipient" onclick="WIKIDOT.page.listeners.userInfo(22222); return false;">recipient</a></span>
                        <span class="subject">{subject}</span>
                        <span class="odate time_1234567890">01 Jan 2023 12:00</span>
                    </div>
                    <div class="body">Test Body</div>
                </div>
                """
            }
            return mock_response

        first_response = message_response("First Subject")
        second_response = message_response("Second Subject")
        mock_client.amc_client.request.return_value = [first_response, second_response]

        with patch("wikidot.module.private_message.user_parser") as mock_user_parser:
            mock_user_parser.return_value = mock_user
            with patch("wikidot.module.private_message.odate_parser") as mock_odate_parser:
                mock_odate_parser.return_value = datetime(2023, 1, 1, 12, 0, 0)

                result = PrivateMessageCollection.from_ids(mock_client, [1, 1, 2])

        requested_bodies = mock_client.amc_client.request.call_args[0][0]
        assert [body["item"] for body in requested_bodies] == [1, 2]
        assert [message.id for message in result] == [1, 1, 2]
        assert [message.subject for message in result] == ["First Subject", "First Subject", "Second Subject"]
        assert result[0] is not result[1]
        assert first_response.json.call_count == 1
        assert second_response.json.call_count == 1
        assert mock_user_parser.call_count == 4
        assert mock_odate_parser.call_count == 2

    def test_from_ids_forbidden_error(self, mock_client):
        """from_idsでアクセス権限エラー"""
        from wikidot.common.exceptions import WikidotStatusCodeException

        mock_exception = WikidotStatusCodeException("no_message", "No message found")
        mock_exception.status_code = "no_message"

        mock_client.amc_client.request.return_value = [mock_exception]

        with pytest.raises(
            ForbiddenException,
            match="Failed to get private message for module: dashboard/messages/DMViewMessageModule, message: 1",
        ):
            PrivateMessageCollection.from_ids(mock_client, [1])

    def test_from_ids_raises_when_detail_retry_is_exhausted(self, mock_client):
        """メッセージ詳細のリトライが尽きた場合は明示的に例外を出す"""
        mock_client.amc_client.config.retry_max_retries = 1
        mock_client.amc_client.request.return_value = (RuntimeError("temporary failure"),)

        with pytest.raises(
            UnexpectedException,
            match=("Cannot retrieve private message for module: dashboard/messages/DMViewMessageModule, message: 1"),
        ):
            PrivateMessageCollection.from_ids(mock_client, [1])

        assert mock_client.amc_client.request.call_count == 2

    @pytest.mark.parametrize("batch_size", [None, True, False, "2", 1.5, 0, -1])
    def test_from_ids_rejects_invalid_retry_batch_size_before_request(self, mock_client, batch_size: object):
        """不正なリトライbatch_size設定はAMCリクエスト前に拒否する"""
        mock_client.amc_client.config.retry_batch_size = batch_size
        mock_client.amc_client.request = MagicMock()

        with pytest.raises(ValueError, match="batch_size must be a positive integer"):
            PrivateMessageCollection.from_ids(mock_client, [1])

        mock_client.amc_client.request.assert_not_called()

    @pytest.mark.parametrize("max_retries", [None, True, False, "1", -1, 1.5])
    def test_from_ids_rejects_invalid_retry_max_retries_before_request(self, mock_client, max_retries: object):
        """不正なリトライmax_retries設定はAMCリクエスト前に拒否する"""
        mock_client.amc_client.config.retry_max_retries = max_retries
        mock_client.amc_client.request = MagicMock()

        with pytest.raises(ValueError, match="max_retries must be a non-negative integer"):
            PrivateMessageCollection.from_ids(mock_client, [1])

        mock_client.amc_client.request.assert_not_called()

    def test_from_ids_uses_retry_defaults_when_config_attrs_are_missing(self, mock_client, mock_user):
        """リトライ設定属性がないconfigでは既存のデフォルト値を使う"""
        mock_client.amc_client.config = object()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": """
            <div class="pmessage">
                <div class="header">
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/sender" onclick="WIKIDOT.page.listeners.userInfo(11111); return false;">sender</a></span>
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/recipient" onclick="WIKIDOT.page.listeners.userInfo(22222); return false;">recipient</a></span>
                    <span class="subject">Test Subject</span>
                    <span class="odate time_1234567890">01 Jan 2023 12:00</span>
                </div>
                <div class="body">Test Body</div>
            </div>
            """
        }
        mock_client.amc_client.request.return_value = [mock_response]

        with patch("wikidot.module.private_message.user_parser") as mock_user_parser:
            mock_user_parser.return_value = mock_user
            with patch("wikidot.module.private_message.odate_parser") as mock_odate_parser:
                mock_odate_parser.return_value = datetime(2023, 1, 1, 12, 0, 0)

                result = PrivateMessageCollection.from_ids(mock_client, [1])

        assert len(result) == 1
        assert mock_client.amc_client.request.call_count == 1

    def test_from_ids_missing_sender_or_recipient_raises(self, mock_client):
        """送受信者要素が欠けたメッセージ詳細はNoElementException"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": """
            <div class="pmessage">
                <div class="header">
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/sender" onclick="WIKIDOT.page.listeners.userInfo(11111); return false;">sender</a></span>
                    <span class="subject">Test Subject</span>
                </div>
                <div class="body">Test Body</div>
            </div>
            """
        }
        mock_client.amc_client.request.return_value = [mock_response]

        with pytest.raises(
            NoElementException,
            match=(
                "Expected sender and recipient elements for module: dashboard/messages/DMViewMessageModule, message: 1"
            ),
        ):
            PrivateMessageCollection.from_ids(mock_client, [1])

    def test_from_ids_malformed_recipient_user_includes_module_message_field_and_value_context(self, mock_client):
        """メッセージ詳細の受信者値不正はparser例外ではなく文脈付きNoElementException"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": """
            <div class="pmessage">
                <div class="header">
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/sender" onclick="WIKIDOT.page.listeners.userInfo(11111); return false;">sender</a></span>
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/recipient" onclick="WIKIDOT.page.listeners.userInfo(latest); return false;">recipient</a></span>
                    <span class="subject">Test Subject</span>
                    <span class="odate time_1234567890">01 Jan 2023 12:00</span>
                </div>
                <div class="body">Test Body</div>
            </div>
            """
        }
        mock_client.amc_client.request.return_value = [mock_response]

        with pytest.raises(NoElementException) as exc_info:
            PrivateMessageCollection.from_ids(mock_client, [1])

        assert str(exc_info.value) == (
            "Message recipient user is malformed for module: dashboard/messages/DMViewMessageModule, "
            "message: 1, field=recipient, value=WIKIDOT.page.listeners.userInfo(latest); return false;"
        )

    def test_from_ids_missing_detail_response_body_includes_module_and_message_context(self, mock_client):
        """メッセージ詳細レスポンスのbody欠損はmodule/message文脈付きNoElementException"""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_client.amc_client.request.return_value = [mock_response]

        with pytest.raises(
            NoElementException,
            match=("Message response body is not found for module: dashboard/messages/DMViewMessageModule, message: 1"),
        ):
            PrivateMessageCollection.from_ids(mock_client, [1])

    def test_from_ids_malformed_detail_response_body_type_includes_module_message_and_type_context(self, mock_client):
        """メッセージ詳細レスポンスのbody型不正は低レベルparser例外ではなく文脈付きNoElementException"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": ["not-html"]}
        mock_client.amc_client.request.return_value = [mock_response]

        with pytest.raises(
            NoElementException,
            match=(
                r"Message response body is malformed for module: dashboard/messages/DMViewMessageModule, "
                r"message: 1 \(field=body, expected=str, actual=list\)"
            ),
        ):
            PrivateMessageCollection.from_ids(mock_client, [1])

    def test_from_ids_missing_odate_includes_module_message_and_field_context(self, mock_client):
        """メッセージ詳細の日時要素欠損はepoch補完ではなく文脈付きNoElementException"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": """
            <div class="pmessage">
                <div class="header">
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/sender" onclick="WIKIDOT.page.listeners.userInfo(11111); return false;">sender</a></span>
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/recipient" onclick="WIKIDOT.page.listeners.userInfo(22222); return false;">recipient</a></span>
                    <span class="subject">Test Subject</span>
                </div>
                <div class="body">Test Body</div>
            </div>
            """
        }
        mock_client.amc_client.request.return_value = [mock_response]

        with pytest.raises(
            NoElementException,
            match=(
                "Message odate element is not found for module: dashboard/messages/DMViewMessageModule, "
                "message: 1, field=odate"
            ),
        ):
            PrivateMessageCollection.from_ids(mock_client, [1])

    def test_from_ids_malformed_odate_includes_module_message_field_and_value_context(self, mock_client):
        """メッセージ詳細の日時値不正はparser例外ではなく文脈付きNoElementException"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": """
            <div class="pmessage">
                <div class="header">
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/sender" onclick="WIKIDOT.page.listeners.userInfo(11111); return false;">sender</a></span>
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/recipient" onclick="WIKIDOT.page.listeners.userInfo(22222); return false;">recipient</a></span>
                    <span class="subject">Test Subject</span>
                    <span class="odate time_latest">not a time</span>
                </div>
                <div class="body">Test Body</div>
            </div>
            """
        }
        mock_client.amc_client.request.return_value = [mock_response]

        with pytest.raises(
            NoElementException,
            match=(
                "Message odate value is malformed for module: dashboard/messages/DMViewMessageModule, "
                "message: 1, field=odate, value=time_latest"
            ),
        ):
            PrivateMessageCollection.from_ids(mock_client, [1])

    def test_from_ids_missing_subject_includes_module_message_and_field_context(self, mock_client):
        """メッセージ詳細の件名要素欠損は空文字補完ではなく文脈付きNoElementException"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": """
            <div class="pmessage">
                <div class="header">
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/sender" onclick="WIKIDOT.page.listeners.userInfo(11111); return false;">sender</a></span>
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/recipient" onclick="WIKIDOT.page.listeners.userInfo(22222); return false;">recipient</a></span>
                    <span class="odate time_1234567890">01 Jan 2023 12:00</span>
                </div>
                <div class="body">Test Body</div>
            </div>
            """
        }
        mock_client.amc_client.request.return_value = [mock_response]

        with pytest.raises(
            NoElementException,
            match=(
                "Message subject element is not found for module: dashboard/messages/DMViewMessageModule, "
                "message: 1, field=subject"
            ),
        ):
            PrivateMessageCollection.from_ids(mock_client, [1])

    def test_from_ids_missing_body_includes_module_message_and_field_context(self, mock_client):
        """メッセージ詳細の本文要素欠損は空文字補完ではなく文脈付きNoElementException"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": """
            <div class="pmessage">
                <div class="header">
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/sender" onclick="WIKIDOT.page.listeners.userInfo(11111); return false;">sender</a></span>
                    <span class="printuser"><a href="http://www.wikidot.com/user:info/recipient" onclick="WIKIDOT.page.listeners.userInfo(22222); return false;">recipient</a></span>
                    <span class="subject">Test Subject</span>
                    <span class="odate time_1234567890">01 Jan 2023 12:00</span>
                </div>
            </div>
            """
        }
        mock_client.amc_client.request.return_value = [mock_response]

        with pytest.raises(
            NoElementException,
            match=(
                "Message body element is not found for module: dashboard/messages/DMViewMessageModule, "
                "message: 1, field=body"
            ),
        ):
            PrivateMessageCollection.from_ids(mock_client, [1])

    def test_acquire_missing_first_page_response_body_includes_module_and_page_context(self, mock_client):
        """一覧初回ページレスポンスのbody欠損はmodule/page文脈付きNoElementException"""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_client.amc_client.request.return_value = [mock_response]

        with (
            patch.object(PrivateMessageCollection, "from_ids") as mock_from_ids,
            pytest.raises(
                NoElementException,
                match="Message list response body is not found for module: dashboard/messages/DMInboxModule, page: 1",
            ),
        ):
            PrivateMessageInbox.acquire(mock_client)

        mock_from_ids.assert_not_called()

    def test_acquire_malformed_first_page_response_body_type_includes_module_page_and_type_context(self, mock_client):
        """一覧初回ページレスポンスのbody型不正は低レベルparser例外ではなく文脈付きNoElementException"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": 123}
        mock_client.amc_client.request.return_value = [mock_response]

        with (
            patch.object(PrivateMessageCollection, "from_ids") as mock_from_ids,
            pytest.raises(
                NoElementException,
                match=(
                    r"Message list response body is malformed for module: dashboard/messages/DMInboxModule, "
                    r"page: 1 \(field=body, expected=str, actual=int\)"
                ),
            ),
        ):
            PrivateMessageInbox.acquire(mock_client)

        mock_from_ids.assert_not_called()

    def test_acquire_missing_message_href_raises(self, mock_client):
        """メッセージ行のdata-href欠損はNoElementException"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": '<table><tr class="message"></tr></table>'}
        mock_client.amc_client.request.return_value = [mock_response]

        with pytest.raises(
            NoElementException,
            match=r"Message data-href attribute is not found for module: dashboard/messages/DMInboxModule "
            r"\(page=1, row=1\)",
        ):
            PrivateMessageCollection._acquire(mock_client, "dashboard/messages/DMInboxModule")

    def test_acquire_malformed_message_href_raises(self, mock_client):
        """メッセージ行のdata-hrefにIDがなければNoElementException"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": '<table><tr class="message" data-href="/account/messages/view"></tr></table>'
        }
        mock_client.amc_client.request.return_value = [mock_response]

        with pytest.raises(
            NoElementException,
            match=r"Message ID is not found in data-href: /account/messages/view "
            r"for module: dashboard/messages/DMInboxModule \(page=1, row=1\)",
        ):
            PrivateMessageCollection._acquire(mock_client, "dashboard/messages/DMInboxModule")

    def test_acquire_ignores_non_numeric_pager_targets(self, mock_client):
        """数値ページがないpagerでは単一ページとして扱う"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": """
            <div class="pager"><span class="target">next</span></div>
            <table><tr class="message" data-href="/account/messages/view/123"></tr></table>
            """
        }
        mock_client.amc_client.request.return_value = [mock_response]

        with patch.object(
            PrivateMessageCollection, "from_ids", return_value=PrivateMessageCollection([])
        ) as mock_from_ids:
            PrivateMessageCollection._acquire(mock_client, "dashboard/messages/DMInboxModule")

        mock_from_ids.assert_called_once_with(mock_client, [123])

    def test_acquire_reuses_first_page_body_for_message_ids(self, mock_client):
        """1ページ目の一覧レスポンスbodyをページャ判定とメッセージID抽出で再利用する"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": """
            <div class="pager"><span class="target">next</span></div>
            <table><tr class="message" data-href="/account/messages/view/123"></tr></table>
            """
        }
        mock_client.amc_client.request.return_value = [mock_response]

        with patch.object(
            PrivateMessageCollection, "from_ids", return_value=PrivateMessageCollection([])
        ) as mock_from_ids:
            PrivateMessageInbox.acquire(mock_client)

        mock_from_ids.assert_called_once_with(mock_client, [123])
        assert mock_response.json.call_count == 1

    def test_acquire_ignores_message_row_pager_markup(self, mock_client):
        """メッセージ行内のpager風マークアップをページネーションとして扱わない"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": """
            <table>
                <tr class="message" data-href="/account/messages/view/123">
                    <td>
                        Test message preview
                        <div class="pager"><span class="target">1</span><span class="target">2</span></div>
                    </td>
                </tr>
            </table>
            """
        }
        mock_client.amc_client.request.return_value = [mock_response]

        with patch.object(
            PrivateMessageCollection, "from_ids", return_value=PrivateMessageCollection([])
        ) as mock_from_ids:
            PrivateMessageCollection._acquire(mock_client, "dashboard/messages/DMInboxModule")

        assert mock_client.amc_client.request.call_count == 1
        mock_from_ids.assert_called_once_with(mock_client, [123])

    def test_acquire_ignores_nested_message_row_markup(self, mock_client):
        """メッセージ行内のmessage行風マークアップを別メッセージとして扱わない"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": """
            <table>
                <tr class="message" data-href="/account/messages/view/123">
                    <td>
                        Test message preview
                        <table>
                            <tr class="message" data-href="/account/messages/view/999"></tr>
                        </table>
                    </td>
                </tr>
            </table>
            """
        }
        mock_client.amc_client.request.return_value = [mock_response]

        with patch.object(
            PrivateMessageCollection, "from_ids", return_value=PrivateMessageCollection([])
        ) as mock_from_ids:
            PrivateMessageCollection._acquire(mock_client, "dashboard/messages/DMInboxModule")

        mock_from_ids.assert_called_once_with(mock_client, [123])

    def test_acquire_retries_transient_first_page_failures(self, mock_client):
        """一時的なAMC失敗後にメッセージ一覧の初回ページをリトライする"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "body": '<table><tr class="message" data-href="/account/messages/view/123"></tr></table>'
        }
        mock_client.amc_client.request.side_effect = [(RuntimeError("temporary failure"),), (mock_response,)]

        with patch.object(
            PrivateMessageCollection, "from_ids", return_value=PrivateMessageCollection([])
        ) as mock_from_ids:
            PrivateMessageInbox.acquire(mock_client)

        assert mock_client.amc_client.request.call_count == 2
        mock_from_ids.assert_called_once_with(mock_client, [123])

    def test_acquire_raises_when_first_page_retry_is_exhausted(self, mock_client):
        """初回ページのリトライが尽きた場合はmodule/page付きで失敗する"""
        mock_client.amc_client.config.retry_max_retries = 1
        mock_client.amc_client.request.return_value = (RuntimeError("temporary failure"),)

        with (
            patch.object(PrivateMessageCollection, "from_ids") as mock_from_ids,
            pytest.raises(
                UnexpectedException,
                match="Cannot retrieve private messages for module: dashboard/messages/DMInboxModule, page: 1",
            ),
        ):
            PrivateMessageInbox.acquire(mock_client)

        mock_from_ids.assert_not_called()
        assert mock_client.amc_client.request.call_count == 2

    def test_acquire_deduplicates_message_ids_preserving_order(self, mock_client):
        """ページをまたいで重複したメッセージIDは詳細取得前に順序保持で重複排除する"""
        first_response = MagicMock()
        first_response.json.return_value = {
            "body": """
            <div class="pager"><span class="target">1</span><span class="target">2</span></div>
            <table>
                <tr class="message" data-href="/account/messages/view/123"></tr>
            </table>
            """
        }
        second_response = MagicMock()
        second_response.json.return_value = {
            "body": """
            <table>
                <tr class="message" data-href="/account/messages/view/123"></tr>
                <tr class="message" data-href="/account/messages/view/456"></tr>
            </table>
            """
        }
        mock_client.amc_client.request.side_effect = [(first_response,), (second_response,)]

        with patch.object(
            PrivateMessageCollection, "from_ids", return_value=PrivateMessageCollection([])
        ) as mock_from_ids:
            PrivateMessageCollection._acquire(mock_client, "dashboard/messages/DMInboxModule")

        mock_from_ids.assert_called_once_with(mock_client, [123, 456])

    def test_acquire_raises_when_paginated_retry_is_exhausted(self, mock_client):
        """追加ページのリトライが尽きた場合は部分一覧を返さない"""
        first_response = MagicMock()
        first_response.json.return_value = {
            "body": """
            <div class="pager"><span class="target">1</span><span class="target">2</span></div>
            <table><tr class="message" data-href="/account/messages/view/123"></tr></table>
            """
        }
        mock_client.amc_client.config.retry_max_retries = 1
        mock_client.amc_client.request.side_effect = [
            (first_response,),
            (RuntimeError("temporary failure"),),
            (RuntimeError("temporary failure"),),
        ]

        with (
            patch.object(PrivateMessageCollection, "from_ids") as mock_from_ids,
            pytest.raises(
                UnexpectedException,
                match="Cannot retrieve private messages for module: dashboard/messages/DMInboxModule, page: 2",
            ),
        ):
            PrivateMessageInbox.acquire(mock_client)

        mock_from_ids.assert_not_called()

    def test_acquire_missing_paginated_response_body_includes_module_and_page_context(self, mock_client):
        """一覧追加ページレスポンスのbody欠損はmodule/page文脈付きNoElementException"""
        first_response = MagicMock()
        first_response.json.return_value = {
            "body": """
            <div class="pager"><span class="target">1</span><span class="target">2</span></div>
            <table><tr class="message" data-href="/account/messages/view/123"></tr></table>
            """
        }
        second_response = MagicMock()
        second_response.json.return_value = {}
        mock_client.amc_client.request.side_effect = [(first_response,), (second_response,)]

        with (
            patch.object(PrivateMessageCollection, "from_ids") as mock_from_ids,
            pytest.raises(
                NoElementException,
                match="Message list response body is not found for module: dashboard/messages/DMInboxModule, page: 2",
            ),
        ):
            PrivateMessageInbox.acquire(mock_client)

        mock_from_ids.assert_not_called()


class TestPrivateMessageInbox:
    """PrivateMessageInboxクラスのテスト"""

    def test_from_ids(self, mock_client):
        """from_idsのテスト"""
        with patch.object(
            PrivateMessageCollection, "from_ids", return_value=PrivateMessageCollection([])
        ) as mock_from_ids:
            result = PrivateMessageInbox.from_ids(mock_client, [1, 2])

            mock_from_ids.assert_called_once_with(mock_client, [1, 2])
            assert isinstance(result, PrivateMessageInbox)

    def test_acquire(self, mock_client):
        """acquireのテスト"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": "<div class='pager'></div>"}
        mock_client.amc_client.request.return_value = [mock_response]

        with patch.object(PrivateMessageCollection, "from_ids", return_value=PrivateMessageCollection([])):
            result = PrivateMessageInbox.acquire(mock_client)

            assert isinstance(result, PrivateMessageInbox)


class TestPrivateMessageSentBox:
    """PrivateMessageSentBoxクラスのテスト"""

    def test_from_ids(self, mock_client):
        """from_idsのテスト"""
        with patch.object(
            PrivateMessageCollection, "from_ids", return_value=PrivateMessageCollection([])
        ) as mock_from_ids:
            result = PrivateMessageSentBox.from_ids(mock_client, [1, 2])

            mock_from_ids.assert_called_once_with(mock_client, [1, 2])
            assert isinstance(result, PrivateMessageSentBox)

    def test_acquire(self, mock_client):
        """acquireのテスト"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": "<div class='pager'></div>"}
        mock_client.amc_client.request.return_value = [mock_response]

        with patch.object(PrivateMessageCollection, "from_ids", return_value=PrivateMessageCollection([])):
            result = PrivateMessageSentBox.acquire(mock_client)

            assert isinstance(result, PrivateMessageSentBox)


class TestPrivateMessageMailboxAcquire:
    """Inbox/SentBox acquire共通のテスト"""

    @pytest.mark.parametrize("collection_cls", [PrivateMessageInbox, PrivateMessageSentBox])
    @pytest.mark.parametrize("client", [None, True, "test-client", {"username": "test-user"}, object()])
    def test_acquire_rejects_malformed_client_before_fetch(self, collection_cls: Any, client: object) -> None:
        bad_client: Any = client

        with (
            patch.object(PrivateMessageCollection, "_amc_request_with_retry") as mock_request,
            pytest.raises(ValueError, match="client must be a Client"),
        ):
            collection_cls.acquire(bad_client)

        mock_request.assert_not_called()


class TestPrivateMessage:
    """PrivateMessageクラスのテスト"""

    def test_str_representation(self, sample_message):
        """文字列表現のテスト"""
        result = str(sample_message)
        assert "PrivateMessage(" in result
        assert "id=1" in result

    @pytest.mark.parametrize("message_id", [None, True, "1", 1.25])
    def test_init_rejects_non_integer_message_id(self, mock_client, mock_user, message_id):
        """PrivateMessageの初期化は整数IDだけ受け付ける"""
        bad_message_id: Any = message_id

        with pytest.raises(ValueError, match="message_id must be an integer"):
            PrivateMessage(
                client=mock_client,
                id=bad_message_id,
                sender=mock_user,
                recipient=mock_user,
                subject="Test Subject",
                body="Test Body",
                created_at=datetime(2023, 1, 1, 12, 0, 0),
            )

    @pytest.mark.parametrize(
        ("field", "value", "message"),
        [
            ("sender", None, "sender must be an AbstractUser"),
            ("sender", True, "sender must be an AbstractUser"),
            ("sender", {"id": 12345}, "sender must be an AbstractUser"),
            ("recipient", None, "recipient must be an AbstractUser"),
            ("recipient", True, "recipient must be an AbstractUser"),
            ("recipient", {"id": 12345}, "recipient must be an AbstractUser"),
        ],
    )
    def test_init_rejects_malformed_message_users(self, mock_client, mock_user, field, value, message):
        """PrivateMessageの初期化は送受信者にAbstractUserだけ受け付ける"""
        inputs = {
            "client": mock_client,
            "id": 1,
            "sender": mock_user,
            "recipient": mock_user,
            "subject": "Test Subject",
            "body": "Test Body",
            "created_at": datetime(2023, 1, 1, 12, 0, 0),
            field: value,
        }

        with pytest.raises(ValueError, match=message):
            PrivateMessage(**inputs)

    @pytest.mark.parametrize(
        ("field", "value", "message"),
        [
            ("subject", None, "subject must be a string"),
            ("subject", True, "subject must be a string"),
            ("subject", 123, "subject must be a string"),
            ("body", None, "body must be a string"),
            ("body", True, "body must be a string"),
            ("body", 123, "body must be a string"),
        ],
    )
    def test_init_rejects_malformed_message_text_fields(self, mock_client, mock_user, field, value, message):
        """PrivateMessageの初期化は件名と本文に文字列だけ受け付ける"""
        inputs = {
            "client": mock_client,
            "id": 1,
            "sender": mock_user,
            "recipient": mock_user,
            "subject": "Test Subject",
            "body": "Test Body",
            "created_at": datetime(2023, 1, 1, 12, 0, 0),
            field: value,
        }

        with pytest.raises(ValueError, match=message):
            PrivateMessage(**inputs)

    @pytest.mark.parametrize("created_at", [None, True, 1700000000, "2023-01-01", []])
    def test_init_rejects_malformed_created_at(self, mock_client, mock_user, created_at):
        """PrivateMessageの初期化は作成日時にdatetimeだけ受け付ける"""
        bad_created_at: Any = created_at

        with pytest.raises(ValueError, match="created_at must be a datetime"):
            PrivateMessage(
                client=mock_client,
                id=1,
                sender=mock_user,
                recipient=mock_user,
                subject="Test Subject",
                body="Test Body",
                created_at=bad_created_at,
            )

    def test_from_id(self, mock_client, sample_message):
        """from_idのテスト"""
        with patch.object(
            PrivateMessageCollection,
            "from_ids",
            return_value=PrivateMessageCollection([sample_message]),
        ) as mock_from_ids:
            result = PrivateMessage.from_id(mock_client, 123)

            mock_from_ids.assert_called_once_with(mock_client, [123])
            assert result is not None

    @pytest.mark.parametrize("message_id", [None, True, "1"])
    def test_from_id_rejects_non_integer_message_id_before_login(self, mock_client, message_id):
        """単一メッセージIDの非整数値はログイン確認やAMCリクエスト前に拒否する"""
        bad_message_id: Any = message_id
        mock_client.login_check = MagicMock()
        mock_client.amc_client.request = MagicMock()

        with pytest.raises(ValueError, match="message_id must be an integer"):
            PrivateMessage.from_id(mock_client, bad_message_id)

        mock_client.login_check.assert_not_called()
        mock_client.amc_client.request.assert_not_called()

    def test_send_requires_login(self, mock_client, mock_user):
        """sendはログインが必要"""
        mock_client.is_logged_in = False
        mock_client.login_check.side_effect = LoginRequiredException("Not logged in")

        with pytest.raises(LoginRequiredException):
            PrivateMessage.send(mock_client, mock_user, "subject", "body")

    def test_send_success(self, mock_client, mock_user):
        """送信成功"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_client.amc_client.request.return_value = (mock_response,)

        PrivateMessage.send(mock_client, mock_user, "Test Subject", "Test Body")

        mock_client.amc_client.request.assert_called_once()
        call_args = mock_client.amc_client.request.call_args[0][0][0]
        assert call_args["source"] == "Test Body"
        assert call_args["subject"] == "Test Subject"
        assert call_args["to_user_id"] == mock_user.id
        assert call_args["event"] == "send"

    @pytest.mark.parametrize("client", [None, True, "test-client", {"username": "test-user"}, object()])
    def test_send_rejects_malformed_client_before_login(self, mock_user, client: object):
        """直接送信はClient以外の親をログイン確認前に拒否する"""
        bad_client: Any = client

        with pytest.raises(ValueError, match="client must be a Client"):
            PrivateMessage.send(bad_client, mock_user, "Test Subject", "Test Body")

    def test_send_rejects_non_user_recipient_before_login(self, mock_client):
        """送信先がUserでない場合はログイン確認やAMCリクエスト前に拒否する"""
        bad_recipient: Any = {"id": 12345, "name": "test-user"}
        mock_client.login_check = MagicMock()
        mock_client.amc_client.request = MagicMock()

        with pytest.raises(ValueError, match="recipient must be a User"):
            PrivateMessage.send(mock_client, bad_recipient, "Test Subject", "Test Body")

        mock_client.login_check.assert_not_called()
        mock_client.amc_client.request.assert_not_called()

    @pytest.mark.parametrize(
        ("recipient_kwargs", "message"),
        [
            ({"id": None, "name": "test-user"}, "recipient.id must be an integer"),
            ({"id": True, "name": "test-user"}, "recipient.id must be an integer"),
            ({"id": 12345, "name": None}, "recipient.name must be a string"),
        ],
    )
    def test_send_rejects_malformed_user_recipient_before_login(self, mock_client, recipient_kwargs, message):
        """送信先Userの必須フィールド不正はログイン確認やAMCリクエスト前に拒否する"""
        bad_recipient = User(
            client=mock_client,
            id=12345,
            name="test-user",
            unix_name="test-user",
            avatar_url="https://www.wikidot.com/avatar.php?userid=12345",
        )
        for field, value in recipient_kwargs.items():
            setattr(bad_recipient, field, value)
        mock_client.login_check = MagicMock()
        mock_client.amc_client.request = MagicMock()

        with pytest.raises(ValueError, match=message):
            PrivateMessage.send(mock_client, bad_recipient, "Test Subject", "Test Body")

        mock_client.login_check.assert_not_called()
        mock_client.amc_client.request.assert_not_called()

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"subject": 3}, "subject must be a string"),
            ({"body": 3}, "body must be a string"),
        ],
    )
    def test_send_rejects_non_string_text_inputs_before_login(self, mock_client, mock_user, kwargs, message):
        """送信の文字列入力不正はログイン確認やAMCリクエスト前に拒否する"""
        mock_client.login_check = MagicMock()
        mock_client.amc_client.request = MagicMock()

        inputs = {"subject": "Test Subject", "body": "Test Body", **kwargs}
        with pytest.raises(ValueError, match=message):
            PrivateMessage.send(mock_client, mock_user, **inputs)

        mock_client.login_check.assert_not_called()
        mock_client.amc_client.request.assert_not_called()

    def test_send_missing_action_status_includes_recipient_event_and_field_context(self, mock_client, mock_user):
        """送信応答のstatus欠落は文脈付きNoElementException"""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_client.amc_client.request.return_value = (mock_response,)

        with pytest.raises(
            NoElementException,
            match=(
                r"Private message send action response is malformed for recipient: test-user "
                r"\(id=12345, event=send, field=status\)"
            ),
        ):
            PrivateMessage.send(mock_client, mock_user, "Test Subject", "Test Body")

        assert mock_response.json.call_count == 1

    def test_send_explicit_non_ok_action_status_raises_status_exception(self, mock_client, mock_user):
        """送信応答の明示的な非ok statusはWikidotStatusCodeException"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "not_ok"}
        mock_client.amc_client.request.return_value = (mock_response,)

        with pytest.raises(WikidotStatusCodeException) as exc_info:
            PrivateMessage.send(mock_client, mock_user, "Test Subject", "Test Body")

        assert exc_info.value.status_code == "not_ok"
