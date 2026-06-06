"""Clientアクセサのユニットテスト"""

from typing import Any
from unittest.mock import patch

import pytest

from wikidot.module.client import Client, ClientPrivateMessageAccessor, ClientSiteAccessor, ClientUserAccessor


class TestClientAccessorsInit:
    """Clientアクセサ初期化のテスト"""

    @pytest.mark.parametrize("accessor_cls", [ClientUserAccessor, ClientPrivateMessageAccessor, ClientSiteAccessor])
    def test_init_accepts_client(self, accessor_cls: Any) -> None:
        """Clientアクセサ初期化時のclientは保持する"""
        with patch("wikidot.module.client.AjaxModuleConnectorClient"):
            client = Client()

        accessor = accessor_cls(client)

        assert accessor.client is client

    @pytest.mark.parametrize("accessor_cls", [ClientUserAccessor, ClientPrivateMessageAccessor, ClientSiteAccessor])
    @pytest.mark.parametrize("client", [None, True, "test-client", {"username": "test-user"}, object()])
    def test_init_rejects_malformed_client(self, accessor_cls: Any, client: Any) -> None:
        """Clientアクセサ初期化時のclientはClientだけ受け付ける"""
        with pytest.raises(ValueError, match="client must be a Client"):
            accessor_cls(client)
