import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, cast

from bs4 import BeautifulSoup

from ..common.exceptions import NoElementException, NotFoundException
from ..util.requestutil import RequestUtil
from ..util.stringutil import StringUtil

if TYPE_CHECKING:
    from .client import Client


def _validate_user_name(field: str, value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    if value.strip() == "":
        raise ValueError(f"{field} must not be empty")
    return value


def _validate_user_names(names: object) -> list[str]:
    if not isinstance(names, list):
        raise ValueError("names must be a list")
    if any(not isinstance(name, str) for name in names):
        raise ValueError("names list entries must be strings")
    validated_names = cast(list[str], names)
    if any(name.strip() == "" for name in validated_names):
        raise ValueError("names list entries must not be empty")
    return validated_names


def _validate_raise_when_not_found(value: object) -> bool:
    if not isinstance(value, bool):
        raise ValueError("raise_when_not_found must be a boolean")
    return value


def _validate_user_lookup_client(client: object) -> "Client":
    from .client import Client

    if not isinstance(client, Client):
        raise ValueError("client must be a Client")
    return client


def _validate_user_client(client: object) -> "Client":
    from .client import Client

    if not isinstance(client, Client):
        raise ValueError("client must be a Client")
    return client


def _validate_user_id_field(field: str, value: object) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer or None")
    return value


def _validate_user_optional_text_field(field: str, value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string or None")
    return value


def _validate_user_expected_field(field: str, value: object, expected: object) -> None:
    if value != expected:
        raise ValueError(f"{field} must be {expected}")


def _validate_user_collection_users(users: object) -> list["AbstractUser"]:
    if users is None:
        return []
    if not isinstance(users, list):
        raise ValueError("users must be a list or None")
    if any(not isinstance(user, AbstractUser) for user in users):
        raise ValueError("users list entries must be AbstractUser")
    return cast(list["AbstractUser"], users)


def _profile_parse_context(name: str, index: int, **details: object) -> str:
    context = [f"index={index}"]
    context.extend(f"{key}={value}" for key, value in details.items())
    return f"for requested user: {StringUtil.to_unix(name)} ({', '.join(context)})"


class UserCollection(list["AbstractUser"]):
    """
    A class representing a collection of user objects

    A list extension class for storing and manipulating multiple user objects.
    Provides functionality for iteration operations and bulk retrieval from usernames.
    """

    def __init__(self, users: list["AbstractUser"] | None = None):
        """
        Initialize a user collection

        Parameters
        ----------
        users : list[AbstractUser] | None, default None
            Initial list of user objects
        """
        super().__init__(_validate_user_collection_users(users))

    def __iter__(self) -> Iterator["AbstractUser"]:
        """
        An iterator that returns user objects in the collection sequentially

        Returns
        -------
        Iterator[AbstractUser]
            Iterator of user objects
        """
        return super().__iter__()

    @staticmethod
    def from_names(client: "Client", names: list[str], raise_when_not_found: bool = False) -> "UserCollection":
        """
        Get a collection of user objects from a list of usernames

        Parameters
        ----------
        client : Client
            Client instance
        names : list[str]
            List of usernames to search for
        raise_when_not_found : bool, default False
            Whether to raise an exception when a user is not found (True: raise, False: do not raise)
            By default, does not raise and excludes the user from results

        Returns
        -------
        UserCollection
            Collection of user objects

        Raises
        ------
        NotFoundException
            When raise_when_not_found is True and a user is not found
        NoElementException
            When required elements are not found during user page parsing
        """
        names = _validate_user_names(names)
        raise_when_not_found = _validate_raise_when_not_found(raise_when_not_found)
        client = _validate_user_lookup_client(client)
        responses = RequestUtil.request(
            client,
            "GET",
            [f"https://www.wikidot.com/user:info/{StringUtil.to_unix(name)}" for name in names],
        )

        users: list[AbstractUser] = []

        for index, (name, response) in enumerate(zip(names, responses, strict=True), start=1):
            if isinstance(response, Exception):
                raise response

            parse_context = _profile_parse_context(name, index)
            html = BeautifulSoup(response.text, "lxml")

            # 存在チェック
            if html.select_one("div.error-block"):
                if raise_when_not_found:
                    raise NotFoundException(f"User not found: {response.url}")
                else:
                    continue

            # id取得
            user_id_elem = html.select_one("a.btn.btn-default.btn-xs")
            if user_id_elem is None:
                raise NoElementException(f"User ID element not found {parse_context}")
            user_id_href = user_id_elem.get("href")
            user_id_href_text = "" if user_id_href is None else str(user_id_href).strip()
            if not user_id_href_text:
                raise NoElementException(f"User ID is not found {parse_context}")
            user_id_match = re.search(r"(?:/new/|userkarma\.php/)(\d+)(?:[/?#].*)?$", user_id_href_text)
            if user_id_match is None:
                parse_context = _profile_parse_context(name, index, field="user_id", value=user_id_href_text)
                raise NoElementException(f"User ID is malformed {parse_context}")
            user_id = int(user_id_match.group(1))

            # name取得
            name_elem = html.select_one("h1.profile-title")
            if name_elem is None:
                raise NoElementException(f"User name element not found {parse_context}")
            name = name_elem.get_text(" ", strip=True)

            # avatar_url取得
            avatar_url = f"https://www.wikidot.com/avatar.php?userid={user_id}"

            users.append(
                User(
                    client=client,
                    id=user_id,
                    name=name,
                    unix_name=StringUtil.to_unix(name),
                    avatar_url=avatar_url,
                )
            )

        return UserCollection(users)


@dataclass
class AbstractUser:
    """
    Abstract base class for user objects

    Defines common attributes and functionality for all user types.
    Do not instantiate this class directly; use derived classes instead.

    Attributes
    ----------
    client : Client
        Client instance
    id : int | None
        User ID
    name : str | None
        Username
    unix_name : str | None
        UNIX-formatted name used in user URLs
    avatar_url : str | None
        URL of the user's avatar image
    ip : str | None
        User's IP address (only set for anonymous users)
    """

    client: "Client"
    id: int | None = None
    name: str | None = None
    unix_name: str | None = None
    avatar_url: str | None = None
    ip: str | None = None

    def __post_init__(self) -> None:
        self.id = _validate_user_id_field("id", self.id)
        self.name = _validate_user_optional_text_field("name", self.name)
        self.unix_name = _validate_user_optional_text_field("unix_name", self.unix_name)
        self.avatar_url = _validate_user_optional_text_field("avatar_url", self.avatar_url)
        self.ip = _validate_user_optional_text_field("ip", self.ip)
        self.client = _validate_user_client(self.client)

    def __str__(self) -> str:
        """
        String representation of the object

        Returns
        -------
        str
            String representation of the user object
        """
        return f"{self.__class__.__name__}(id={self.id}, name={self.name}, unix_name={self.unix_name})"


@dataclass
class User(AbstractUser):
    """
    A class representing a regular Wikidot user

    Represents a registered normal Wikidot user. Holds basic information such as user ID and username.

    Attributes
    ----------
    client : Client
        Client instance
    id : int | None
        User ID
    name : str | None
        Username
    unix_name : str | None
        UNIX-formatted name used in user URLs
    avatar_url : str | None
        URL of the user's avatar image
    ip : None
        User's IP address (None for regular users as it cannot be obtained)
    """

    # client: 'Client'
    # id: int | None
    # name: str | None
    # unix_name: str | None
    # avatar_url: str | None
    ip: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _validate_user_expected_field("ip", self.ip, None)

    @staticmethod
    def from_name(client: "Client", name: str, raise_when_not_found: bool = False) -> Optional["AbstractUser"]:
        """
        Get a user object from a username

        Parameters
        ----------
        client : Client
            Client instance
        name : str
            Username to search for
        raise_when_not_found : bool, default False
            Whether to raise an exception when a user is not found (True: raise, False: do not raise)
            By default, returns None without raising

        Returns
        -------
        AbstractUser
            User object

        Raises
        ------
        NotFoundException
            When raise_when_not_found is True and the user is not found
        NoElementException
            When required elements are not found during user page parsing
        IndexError
            When the user is not found (when raise_when_not_found is False)
        """
        name = _validate_user_name("name", name)
        raise_when_not_found = _validate_raise_when_not_found(raise_when_not_found)
        result = UserCollection.from_names(client, [name], raise_when_not_found)
        if len(result) == 0:
            if raise_when_not_found:
                raise NotFoundException(f"User not found: {name}")
            else:
                return None

        return result[0]


@dataclass
class DeletedUser(AbstractUser):
    """
    A class representing a deleted Wikidot user

    Represents a user account that has been deleted.
    Deleted users are assigned a fixed name of "account deleted".

    Attributes
    ----------
    client : Client
        Client instance
    id : int | None
        User ID
    name : str
        Username (fixed as "account deleted" because the account is deleted)
    unix_name : str
        UNIX name of the user (fixed as "account_deleted" because the account is deleted)
    avatar_url : None
        URL of the user's avatar (None for deleted users)
    ip : None
        User's IP address (None as it cannot be obtained)
    """

    id: int | None = None
    name: str | None = "account deleted"
    unix_name: str | None = "account_deleted"
    avatar_url: str | None = None
    ip: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _validate_user_expected_field("name", self.name, "account deleted")
        _validate_user_expected_field("unix_name", self.unix_name, "account_deleted")
        _validate_user_expected_field("avatar_url", self.avatar_url, None)
        _validate_user_expected_field("ip", self.ip, None)


@dataclass
class AnonymousUser(AbstractUser):
    """
    A class representing an anonymous (unregistered) Wikidot user

    Represents an anonymous user who posted without registering.
    Has only an IP address as identification information.

    Attributes
    ----------
    client : Client
        Client instance
    id : None
        User ID (None for anonymous users)
    name : str
        Username (fixed as "Anonymous" for anonymous users)
    unix_name : str
        UNIX name of the user (fixed as "anonymous" for anonymous users)
    avatar_url : None
        URL of the user's avatar (None for anonymous users)
    ip : str
        User's IP address
    """

    id: int | None = None
    name: str | None = "Anonymous"
    unix_name: str | None = "anonymous"
    avatar_url: str | None = None
    ip: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _validate_user_expected_field("id", self.id, None)
        _validate_user_expected_field("name", self.name, "Anonymous")
        _validate_user_expected_field("unix_name", self.unix_name, "anonymous")
        _validate_user_expected_field("avatar_url", self.avatar_url, None)


@dataclass
class GuestUser(AbstractUser):
    """
    A class representing a guest Wikidot user who posted as a guest

    Represents a guest user who posted by entering only a name and email address.
    The username is optional but does not have an ID or UNIX name.

    Attributes
    ----------
    client : Client
        Client instance
    id : None
        User ID (None for guest users)
    name : str | None
        Username (name specified when posting as a guest)
    unix_name : None
        UNIX name of the user (None for guest users)
    avatar_url : str | None
        URL of the user's avatar (may be from Gravatar)
    ip : None
        User's IP address (None as it cannot be obtained)
    """

    id: int | None = None
    name: str | None = None
    unix_name: str | None = None
    avatar_url: str | None = None
    ip: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _validate_user_expected_field("id", self.id, None)
        _validate_user_expected_field("unix_name", self.unix_name, None)
        _validate_user_expected_field("ip", self.ip, None)


@dataclass
class WikidotUser(AbstractUser):
    """
    A class representing the Wikidot system user

    A special user for representing automatic posts and notifications by the Wikidot system.
    Has a fixed name of "Wikidot".

    Attributes
    ----------
    client : Client
        Client instance
    id : None
        User ID (None for system users)
    name : str
        Username (fixed as "Wikidot" for system users)
    unix_name : str
        UNIX name of the user (fixed as "wikidot" for system users)
    avatar_url : None
        URL of the user's avatar (None for system users)
    ip : None
        User's IP address (None as it cannot be obtained)
    """

    id: int | None = None
    name: str | None = "Wikidot"
    unix_name: str | None = "wikidot"
    avatar_url: str | None = None
    ip: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _validate_user_expected_field("id", self.id, None)
        _validate_user_expected_field("name", self.name, "Wikidot")
        _validate_user_expected_field("unix_name", self.unix_name, "wikidot")
        _validate_user_expected_field("avatar_url", self.avatar_url, None)
        _validate_user_expected_field("ip", self.ip, None)
