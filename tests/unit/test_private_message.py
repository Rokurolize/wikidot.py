"""
プライベートメッセージモジュールのユニットテスト

PrivateMessage, PrivateMessageCollection, PrivateMessageInbox, PrivateMessageSentBoxクラスをテストする。
"""

from datetime import datetime
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
def mock_user():
    """モックユーザー"""
    user = MagicMock()
    user.id = 12345
    user.name = "test-user"
    return user


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

    def test_from_ids_success(self, mock_client):
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
            mock_user_parser.return_value = MagicMock()
            with patch("wikidot.module.private_message.odate_parser") as mock_odate_parser:
                mock_odate_parser.return_value = datetime(2023, 1, 1, 12, 0, 0)

                result = PrivateMessageCollection.from_ids(mock_client, [1])

                assert len(result) == 1
                assert result[0].id == 1

    def test_from_ids_ignores_body_header_markup(self, mock_client):
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
        sender = MagicMock()
        recipient = MagicMock()

        with (
            patch("wikidot.module.private_message.user_parser", side_effect=[sender, recipient]) as mock_user_parser,
            patch("wikidot.module.private_message.odate_parser") as mock_odate_parser,
        ):
            mock_odate_parser.return_value = datetime(2023, 1, 1, 12, 0, 0)

            result = PrivateMessageCollection.from_ids(mock_client, [1])

        assert len(result) == 1
        assert result[0].sender == sender
        assert result[0].recipient == recipient
        assert result[0].subject == "Test Subject"
        assert "Test Body" in result[0].body
        assert mock_user_parser.call_count == 2

    def test_from_ids_preserves_body_text_spacing(self, mock_client):
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
        sender = MagicMock()
        recipient = MagicMock()

        with (
            patch("wikidot.module.private_message.user_parser", side_effect=[sender, recipient]),
            patch("wikidot.module.private_message.odate_parser") as mock_odate_parser,
        ):
            mock_odate_parser.return_value = datetime(2023, 1, 1, 12, 0, 0)

            result = PrivateMessageCollection.from_ids(mock_client, [1])

        assert len(result) == 1
        assert result[0].body == "First message Second message"

    def test_from_ids_preserves_subject_text_spacing(self, mock_client):
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
        sender = MagicMock()
        recipient = MagicMock()

        with (
            patch("wikidot.module.private_message.user_parser", side_effect=[sender, recipient]),
            patch("wikidot.module.private_message.odate_parser") as mock_odate_parser,
        ):
            mock_odate_parser.return_value = datetime(2023, 1, 1, 12, 0, 0)

            result = PrivateMessageCollection.from_ids(mock_client, [1])

        assert len(result) == 1
        assert result[0].subject == "First Part Subject"

    def test_from_ids_retries_transient_detail_failures(self, mock_client):
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
            mock_user_parser.return_value = MagicMock()
            with patch("wikidot.module.private_message.odate_parser") as mock_odate_parser:
                mock_odate_parser.return_value = datetime(2023, 1, 1, 12, 0, 0)

                result = PrivateMessageCollection.from_ids(mock_client, [1])

        assert len(result) == 1
        assert mock_client.amc_client.request.call_count == 2

    def test_from_ids_deduplicates_duplicate_message_ids_preserving_order(self, mock_client):
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
            mock_user_parser.return_value = MagicMock()
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


class TestPrivateMessage:
    """PrivateMessageクラスのテスト"""

    def test_str_representation(self, sample_message):
        """文字列表現のテスト"""
        result = str(sample_message)
        assert "PrivateMessage(" in result
        assert "id=1" in result

    def test_from_id(self, mock_client):
        """from_idのテスト"""
        with patch.object(
            PrivateMessageCollection,
            "from_ids",
            return_value=PrivateMessageCollection([MagicMock()]),
        ) as mock_from_ids:
            result = PrivateMessage.from_id(mock_client, 123)

            mock_from_ids.assert_called_once_with(mock_client, [123])
            assert result is not None

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
