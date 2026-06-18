from unittest.mock import MagicMock

from wikidot.common.decorators import login_required
from wikidot.module.client import Client


def test_login_required_falls_back_to_nested_client_when_self_client_is_none() -> None:
    client = object.__new__(Client)
    client.login_check = MagicMock()

    class SiteHolder:
        def __init__(self) -> None:
            self.client = client

    class Subject:
        def __init__(self) -> None:
            self.client = None
            self.site = SiteHolder()

        @login_required
        def run(self) -> str:
            return "ok"

    assert Subject().run() == "ok"
    client.login_check.assert_called_once_with()
