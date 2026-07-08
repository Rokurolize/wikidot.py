from unittest.mock import MagicMock

import pytest

from wikidot.common.decorators import login_required
from wikidot.module.client import Client


def test_login_required_uses_keyword_client() -> None:
    client = object.__new__(Client)
    client.login_check = MagicMock()

    @login_required
    def run(*, client: Client) -> str:
        return "ok"

    assert run(client=client) == "ok"
    client.login_check.assert_called_once_with()


def test_login_required_uses_positional_client() -> None:
    client = object.__new__(Client)
    client.login_check = MagicMock()

    @login_required
    def run(client: Client) -> str:
        return "ok"

    assert run(client) == "ok"
    client.login_check.assert_called_once_with()


def test_login_required_ignores_non_client_keyword_before_positional_client() -> None:
    client = object.__new__(Client)
    client.login_check = MagicMock()

    @login_required
    def run(positional_client: Client, *, client: object) -> str:
        return "ok"

    assert run(client, client=object()) == "ok"
    client.login_check.assert_called_once_with()


def test_login_required_uses_self_client() -> None:
    client = object.__new__(Client)
    client.login_check = MagicMock()

    class Subject:
        def __init__(self) -> None:
            self.client = client

        @login_required
        def run(self) -> str:
            return "ok"

    assert Subject().run() == "ok"
    client.login_check.assert_called_once_with()


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


def test_login_required_raises_when_client_is_not_found() -> None:
    @login_required
    def run() -> str:
        return "ok"

    with pytest.raises(ValueError, match="Client is not found"):
        run()


def test_login_required_raises_for_self_without_client_attributes() -> None:
    class Subject:
        @login_required
        def run(self) -> str:
            return "ok"

    with pytest.raises(ValueError, match="Client is not found"):
        Subject().run()


def test_login_required_ignores_nested_non_client_attributes() -> None:
    class SiteHolder:
        def __init__(self) -> None:
            self.client = object()

    class Subject:
        def __init__(self) -> None:
            self.site = SiteHolder()

        @login_required
        def run(self) -> str:
            return "ok"

    with pytest.raises(ValueError, match="Client is not found"):
        Subject().run()
