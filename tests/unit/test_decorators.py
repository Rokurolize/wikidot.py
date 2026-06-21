from unittest.mock import MagicMock

import pytest

from wikidot.common.decorators import login_required
from wikidot.module.client import Client


@pytest.mark.parametrize("direct_client", [None, object()])
def test_login_required_falls_back_to_nested_client_when_self_client_is_not_a_client(direct_client: object) -> None:
    client = object.__new__(Client)
    client.login_check = MagicMock()

    class SiteHolder:
        def __init__(self) -> None:
            self.client = client

    class Subject:
        def __init__(self) -> None:
            self.client = direct_client
            self.site = SiteHolder()

        @login_required
        def run(self) -> str:
            return "ok"

    assert Subject().run() == "ok"
    client.login_check.assert_called_once_with()
