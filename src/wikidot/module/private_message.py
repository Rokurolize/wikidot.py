"""
Module for handling Wikidot private messages

This module provides classes and functionality related to Wikidot private messages (PM).
It enables operations such as sending messages, retrieving inbox/sent box, and viewing messages.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, cast

from bs4 import BeautifulSoup, Tag
from typing_extensions import Self

from ..common import exceptions
from ..common.decorators import login_required
from ..util.parser import odate as odate_parser
from ..util.parser import user as user_parser
from ._validation import validate_text_field
from .user import User

if TYPE_CHECKING:
    from .client import Client
    from .user import AbstractUser


def _validate_private_message_recipient(recipient: object) -> User:
    if not isinstance(recipient, User):
        raise ValueError("recipient must be a User")
    if not isinstance(recipient.id, int) or isinstance(recipient.id, bool):
        raise ValueError("recipient.id must be an integer")
    if not isinstance(recipient.name, str):
        raise ValueError("recipient.name must be a string")
    return recipient


def _validate_private_message_id(message_id: object) -> int:
    if not isinstance(message_id, int) or isinstance(message_id, bool):
        raise ValueError("message_id must be an integer")
    return message_id


def _validate_private_message_user(field: str, user: object) -> "AbstractUser":
    from .user import AbstractUser

    if not isinstance(user, AbstractUser):
        raise ValueError(f"{field} must be an AbstractUser")
    return user


def _validate_private_message_user_client(client: "Client", field: str, user: "AbstractUser") -> None:
    if user.client is not client:
        raise ValueError(f"{field} must belong to the client")


def _validate_private_message_created_at(created_at: object) -> datetime:
    if not isinstance(created_at, datetime):
        raise ValueError("created_at must be a datetime")
    return created_at


def _validate_private_message_ids(message_ids: object) -> list[int]:
    if not isinstance(message_ids, list):
        raise ValueError("message_ids must be a list")
    if any(not isinstance(message_id, int) or isinstance(message_id, bool) for message_id in message_ids):
        raise ValueError("message_ids list entries must be integers")
    return cast(list[int], message_ids)


def _validate_private_message_client(client: object) -> "Client":
    from .client import Client

    if not isinstance(client, Client):
        raise ValueError("client must be a Client")
    return client


def _validate_private_message_retry_batch_size(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"batch_size must be a positive integer, got {value}")
    return value


def _validate_private_message_retry_max_retries(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"max_retries must be a non-negative integer, got {value}")
    return value


def _require_private_message_send_action_status(recipient: "User", event: str, data: dict[str, Any]) -> Any:
    try:
        status = data["status"]
    except KeyError as exc:
        raise exceptions.NoElementException(
            f"Private message send action response is malformed for recipient: {recipient.name} "
            f"(id={recipient.id}, event={event}, field=status)"
        ) from exc

    if status != "ok":
        raise exceptions.WikidotStatusCodeException(
            f"Failed to send private message to recipient: {recipient.name}, event: {event}",
            status,
        )
    return status


def _validate_private_message_collection_messages(messages: object) -> list["PrivateMessage"]:
    if messages is None:
        return []
    if not isinstance(messages, list):
        raise ValueError("messages must be a list or None")
    if any(not isinstance(message, PrivateMessage) for message in messages):
        raise ValueError("messages list entries must be PrivateMessage")
    return cast(list["PrivateMessage"], messages)


def _odate_class_value(odate_element: Tag) -> str:
    class_attr = odate_element.get("class", [])
    if class_attr is None:
        return ""
    class_values = [class_attr] if isinstance(class_attr, str) else [str(value) for value in class_attr]
    return next((value for value in class_values if "time_" in value), " ".join(class_values))


def _user_onclick_value(user_element: Tag) -> str:
    link_element = user_element.find("a", recursive=False)
    if isinstance(link_element, Tag):
        onclick = link_element.get("onclick")
        if onclick is not None:
            return str(onclick)
    return user_element.get_text(" ", strip=True)


def _parse_message_user(client: "Client", user_element: Tag, parse_context: str, field: str) -> Any:
    try:
        return user_parser(client, user_element)
    except ValueError as exc:
        raise exceptions.NoElementException(
            f"Message {field} user is malformed {parse_context}, "
            f"field={field}, value={_user_onclick_value(user_element)}"
        ) from exc


class PrivateMessageCollection(list["PrivateMessage"]):
    """
    Base class representing a collection of private messages

    A list extension class for storing multiple private messages and performing batch operations.
    Inherited to represent specific message groups such as inbox or sent box.
    """

    def __init__(self, messages: list["PrivateMessage"] | None = None):
        """
        Initialization method

        Parameters
        ----------
        messages : list[PrivateMessage] | None, default None
            List of private messages to store
        """
        super().__init__(_validate_private_message_collection_messages(messages))

    def __str__(self) -> str:
        """
        String representation of the object

        Returns
        -------
        str
            String representation of the message collection
        """
        return f"{self.__class__.__name__}({len(self)} messages)"

    def __iter__(self) -> Iterator["PrivateMessage"]:
        """
        Iterator that returns messages in the collection sequentially

        Returns
        -------
        Iterator[PrivateMessage]
            Iterator of message objects
        """
        return super().__iter__()

    def find(self, id: int) -> Optional["PrivateMessage"]:
        """
        Retrieve a message with the specified ID

        Parameters
        ----------
        id : int
            The ID of the message to retrieve

        Returns
        -------
        PrivateMessage | None
            The retrieved message object, or None if not found
        """
        if not isinstance(id, int) or isinstance(id, bool):
            raise ValueError("id must be an integer")

        for message in self:
            if message.id == id:
                return message

        return None

    @staticmethod
    def _amc_request_with_retry(client: "Client", bodies: list[dict[str, Any]]) -> tuple[Any | None, ...]:
        config = getattr(client.amc_client, "config", None)
        batch_size = _validate_private_message_retry_batch_size(getattr(config, "retry_batch_size", 50))
        max_retries = _validate_private_message_retry_max_retries(getattr(config, "retry_max_retries", 3))

        def should_retry(response: Any) -> bool:
            if not isinstance(response, Exception):
                return False
            return not (
                isinstance(response, exceptions.ForbiddenException)
                or (
                    isinstance(response, exceptions.WikidotStatusCodeException) and response.status_code == "no_message"
                )
            )

        all_results: list[Any | None] = []

        for batch_start in range(0, len(bodies), batch_size):
            batch = bodies[batch_start : batch_start + batch_size]
            responses = client.amc_client.request(batch, return_exceptions=True)
            batch_results: list[Any | None] = []
            failed_indices: list[int] = []

            for index, response in enumerate(responses):
                batch_results.append(response)
                if should_retry(response):
                    failed_indices.append(index)

            for _attempt in range(max_retries):
                if not failed_indices:
                    break

                retry_responses = client.amc_client.request(
                    [batch[index] for index in failed_indices],
                    return_exceptions=True,
                )
                still_failed_indices: list[int] = []

                for retry_index, retry_response in enumerate(retry_responses):
                    result_index = failed_indices[retry_index]
                    batch_results[result_index] = retry_response
                    if should_retry(retry_response):
                        still_failed_indices.append(result_index)

                failed_indices = still_failed_indices

            for index in failed_indices:
                batch_results[index] = None

            all_results.extend(batch_results)

        return tuple(all_results)

    @staticmethod
    def _is_inside_message_row(element: Tag) -> bool:
        for ancestor in element.parents:
            if not isinstance(ancestor, Tag):
                continue
            if ancestor.name == "tr" and "message" in ancestor.get("class", []):
                return True
        return False

    @staticmethod
    def _message_list_parse_context(module_name: str, page: int, row_index: int) -> str:
        return f"for module: {module_name} (page={page}, row={row_index})"

    @staticmethod
    def _message_list_fetch_context(module_name: str, page: int) -> str:
        return f"for module: {module_name}, page: {page}"

    @staticmethod
    def _message_list_response_body(response: Any, module_name: str, page: int) -> str:
        response_body = response.json().get("body")
        if response_body is None:
            raise exceptions.NoElementException(
                "Message list response body is not found "
                f"{PrivateMessageCollection._message_list_fetch_context(module_name, page)}"
            )
        if not isinstance(response_body, str):
            raise exceptions.NoElementException(
                "Message list response body is malformed "
                f"{PrivateMessageCollection._message_list_fetch_context(module_name, page)} "
                f"(field=body, expected=str, actual={type(response_body).__name__})"
            )
        return response_body

    @staticmethod
    def _message_detail_fetch_context(module_name: str, message_id: int) -> str:
        return f"for module: {module_name}, message: {message_id}"

    @staticmethod
    def _pager_targets_from_html(html: BeautifulSoup) -> list[Tag]:
        for pager in html.select("div.pager"):
            if PrivateMessageCollection._is_inside_message_row(pager):
                continue
            return list(pager.select("span.target"))
        return []

    @staticmethod
    def from_ids(client: "Client", message_ids: list[int]) -> "PrivateMessageCollection":
        """
        Retrieve a collection of message objects from a list of message IDs

        Batch retrieves messages with the specified IDs and returns them as a collection.

        Parameters
        ----------
        client : Client
            Client instance
        message_ids : list[int]
            List of message IDs to retrieve

        Returns
        -------
        PrivateMessageCollection
            Collection of retrieved messages

        Raises
        ------
        LoginRequiredException
            If not logged in
        ForbiddenException
            If no permission to access the message
        """
        message_ids = _validate_private_message_ids(message_ids)
        if len(message_ids) == 0:
            return PrivateMessageCollection([])
        client = _validate_private_message_client(client)

        client.login_check()

        unique_message_ids: list[int] = []
        seen_message_ids: set[int] = set()
        for message_id in message_ids:
            if message_id in seen_message_ids:
                continue
            seen_message_ids.add(message_id)
            unique_message_ids.append(message_id)

        message_detail_module_name = "dashboard/messages/DMViewMessageModule"
        bodies = []

        for message_id in unique_message_ids:
            bodies.append(
                {
                    "item": message_id,
                    "moduleName": message_detail_module_name,
                }
            )

        responses = PrivateMessageCollection._amc_request_with_retry(client, bodies)

        responses_by_id: dict[int, Any] = {}

        for index, response in enumerate(responses):
            message_id = unique_message_ids[index]
            fetch_context = PrivateMessageCollection._message_detail_fetch_context(
                message_detail_module_name, message_id
            )

            if isinstance(response, exceptions.WikidotStatusCodeException):
                if response.status_code == "no_message":
                    raise exceptions.ForbiddenException(f"Failed to get private message {fetch_context}") from response

            if response is None:
                raise exceptions.UnexpectedException(f"Cannot retrieve private message {fetch_context}")

            if isinstance(response, Exception):
                raise response

            responses_by_id[message_id] = response

        parsed_messages_by_id: dict[int, tuple[Any, Any, str, str, datetime]] = {}
        for message_id in unique_message_ids:
            response = responses_by_id[message_id]
            parse_context = PrivateMessageCollection._message_detail_fetch_context(
                message_detail_module_name, message_id
            )
            response_body = response.json().get("body")
            if response_body is None:
                raise exceptions.NoElementException(f"Message response body is not found {parse_context}")
            if not isinstance(response_body, str):
                raise exceptions.NoElementException(
                    f"Message response body is malformed {parse_context} "
                    f"(field=body, expected=str, actual={type(response_body).__name__})"
                )
            html = BeautifulSoup(response_body, "lxml")

            message_element = html.select_one("div.pmessage")
            if message_element is None:
                raise exceptions.NoElementException(f"Message element is not found {parse_context}")
            header_element = message_element.select_one(":scope > div.header")
            if header_element is None:
                raise exceptions.NoElementException(f"Message header element is not found {parse_context}")

            user_elements = header_element.select(":scope > span.printuser")
            if len(user_elements) != 2:
                raise exceptions.NoElementException(f"Expected sender and recipient elements {parse_context}")
            sender, recipient = user_elements

            subject_element = header_element.select_one(":scope > span.subject")
            body_element = message_element.select_one(":scope > div.body")
            odate_element = header_element.select_one(":scope > span.odate")
            if subject_element is None:
                raise exceptions.NoElementException(
                    f"Message subject element is not found {parse_context}, field=subject"
                )
            if body_element is None:
                raise exceptions.NoElementException(f"Message body element is not found {parse_context}, field=body")
            if odate_element is None:
                raise exceptions.NoElementException(f"Message odate element is not found {parse_context}, field=odate")

            try:
                created_at = odate_parser(odate_element)
            except ValueError as exc:
                raise exceptions.NoElementException(
                    f"Message odate value is malformed {parse_context}, "
                    f"field=odate, value={_odate_class_value(odate_element)}"
                ) from exc

            parsed_messages_by_id[message_id] = (
                _parse_message_user(client, sender, parse_context, "sender"),
                _parse_message_user(client, recipient, parse_context, "recipient"),
                subject_element.get_text(" ", strip=True),
                body_element.get_text(" ", strip=True),
                created_at,
            )

        messages = []
        for message_id in message_ids:
            sender, recipient, subject, body, created_at = parsed_messages_by_id[message_id]
            messages.append(
                PrivateMessage(
                    client=client,
                    id=message_id,
                    sender=sender,
                    recipient=recipient,
                    subject=subject,
                    body=body,
                    created_at=created_at,
                )
            )

        return PrivateMessageCollection(messages)

    @staticmethod
    @login_required
    def _acquire(client: "Client", module_name: str) -> "PrivateMessageCollection":
        """
        Internal method to retrieve private messages from a specific module

        Common method for retrieving message lists such as inbox or sent box.
        If pagination exists, retrieves from all pages.

        Parameters
        ----------
        client : Client
            Client instance
        module_name : str
            Module name to retrieve messages from

        Returns
        -------
        PrivateMessageCollection
            Collection of retrieved messages

        Raises
        ------
        LoginRequiredException
            If not logged in
        """
        # pager取得
        first_response = PrivateMessageCollection._amc_request_with_retry(client, [{"moduleName": module_name}])[0]
        if first_response is None:
            raise exceptions.UnexpectedException(
                f"Cannot retrieve private messages {PrivateMessageCollection._message_list_fetch_context(module_name, 1)}"
            )
        if isinstance(first_response, Exception):
            raise first_response

        first_body = PrivateMessageCollection._message_list_response_body(first_response, module_name, 1)
        first_html = BeautifulSoup(first_body, "lxml")
        # pagerの最後から2番目の要素を取得
        # pageが存在しない場合は1ページのみ
        pager = PrivateMessageCollection._pager_targets_from_html(first_html)
        max_page = 1
        for pager_target in reversed(pager):
            page_text = pager_target.get_text(strip=True)
            if page_text.isdigit():
                max_page = int(page_text)
                break

        if max_page > 1:
            # メッセージ取得
            page_numbers = list(range(2, max_page + 1))
            additional_responses = PrivateMessageCollection._amc_request_with_retry(
                client,
                [{"page": page, "moduleName": module_name} for page in page_numbers],
            )
            responses = (first_response, *additional_responses)
            response_pages = (1, *page_numbers)
        else:
            responses = (first_response,)
            response_pages = (1,)

        message_ids = []
        seen_message_ids: set[int] = set()
        for page, response in zip(response_pages, responses, strict=True):
            if response is None:
                raise exceptions.UnexpectedException(
                    "Cannot retrieve private messages "
                    f"{PrivateMessageCollection._message_list_fetch_context(module_name, page)}"
                )
            if isinstance(response, Exception):
                raise response
            if page == 1:
                html = first_html
            else:
                body = PrivateMessageCollection._message_list_response_body(response, module_name, page)
                html = BeautifulSoup(body, "lxml")
            row_index = 0
            for message_row in html.select("tr.message"):
                if PrivateMessageCollection._is_inside_message_row(message_row):
                    continue

                row_index += 1
                parse_context = PrivateMessageCollection._message_list_parse_context(module_name, page, row_index)
                data_href = message_row.get("data-href")
                if data_href is None:
                    raise exceptions.NoElementException(f"Message data-href attribute is not found {parse_context}")

                message_id_match = re.search(r"(\d+)(?:[/?#].*)?$", str(data_href))
                if message_id_match is None:
                    raise exceptions.NoElementException(
                        f"Message ID is not found in data-href: {data_href} {parse_context}"
                    )

                message_id = int(message_id_match.group(1))
                if message_id in seen_message_ids:
                    continue
                seen_message_ids.add(message_id)
                message_ids.append(message_id)

        return PrivateMessageCollection.from_ids(client, message_ids)

    @classmethod
    def _factory_from_ids(cls, client: "Client", message_ids: list[int]) -> Self:
        """
        Generic factory method to retrieve message collection from a list of message IDs

        Parameters
        ----------
        client : Client
            Client instance
        message_ids : list[int]
            List of message IDs to retrieve

        Returns
        -------
        cls
            Instance of the calling class
        """
        return cls(PrivateMessageCollection.from_ids(client, message_ids))

    @classmethod
    def _factory_acquire(cls, client: "Client", module_name: str) -> Self:
        """
        Generic factory method to retrieve messages from a specified module

        Parameters
        ----------
        client : Client
            Client instance
        module_name : str
            Module name to use for retrieval

        Returns
        -------
        cls
            Instance of the calling class

        Raises
        ------
        LoginRequiredException
            If not logged in
        """
        client = _validate_private_message_client(client)
        return cls(PrivateMessageCollection._acquire(client, module_name))


class PrivateMessageInbox(PrivateMessageCollection):
    """
    Class representing a collection of received private messages

    A specialized class of PrivateMessageCollection for storing and operating
    on private messages in the inbox.
    """

    @classmethod
    def from_ids(cls, client: "Client", message_ids: list[int]) -> "PrivateMessageInbox":
        """
        Retrieve inbox message collection from a list of message IDs

        Parameters
        ----------
        client : Client
            Client instance
        message_ids : list[int]
            List of message IDs to retrieve

        Returns
        -------
        PrivateMessageInbox
            Collection of inbox messages
        """
        return cls._factory_from_ids(client, message_ids)

    @classmethod
    def acquire(cls, client: "Client") -> "PrivateMessageInbox":
        """
        Retrieve all inbox messages for the logged-in user

        Parameters
        ----------
        client : Client
            Client instance

        Returns
        -------
        PrivateMessageInbox
            Collection of inbox messages

        Raises
        ------
        LoginRequiredException
            If not logged in
        """
        return cls._factory_acquire(client, "dashboard/messages/DMInboxModule")


class PrivateMessageSentBox(PrivateMessageCollection):
    """
    Class representing a collection of sent private messages

    A specialized class of PrivateMessageCollection for storing and operating
    on private messages in the sent box.
    """

    @classmethod
    def from_ids(cls, client: "Client", message_ids: list[int]) -> "PrivateMessageSentBox":
        """
        Retrieve sent box message collection from a list of message IDs

        Parameters
        ----------
        client : Client
            Client instance
        message_ids : list[int]
            List of message IDs to retrieve

        Returns
        -------
        PrivateMessageSentBox
            Collection of sent box messages
        """
        return cls._factory_from_ids(client, message_ids)

    @classmethod
    def acquire(cls, client: "Client") -> "PrivateMessageSentBox":
        """
        Retrieve all sent box messages for the logged-in user

        Parameters
        ----------
        client : Client
            Client instance

        Returns
        -------
        PrivateMessageSentBox
            Collection of sent box messages

        Raises
        ------
        LoginRequiredException
            If not logged in
        """
        return cls._factory_acquire(client, "dashboard/messages/DMSentModule")


@dataclass
class PrivateMessage:
    """
    Class representing a Wikidot private message

    Holds information about private messages exchanged between users.
    Provides basic information such as sender, recipient, subject, and body.

    Attributes
    ----------
    client : Client
        Client instance
    id : int
        Message ID
    sender : AbstractUser
        Sender of the message
    recipient : AbstractUser
        Recipient of the message
    subject : str
        Subject of the message
    body : str
        Body of the message
    created_at : datetime
        Creation date and time of the message
    """

    client: "Client"
    id: int
    sender: "AbstractUser"
    recipient: "AbstractUser"
    subject: str
    body: str
    created_at: datetime

    def __post_init__(self) -> None:
        self.id = _validate_private_message_id(self.id)
        self.client = _validate_private_message_client(self.client)
        self.sender = _validate_private_message_user("sender", self.sender)
        self.recipient = _validate_private_message_user("recipient", self.recipient)
        _validate_private_message_user_client(self.client, "sender", self.sender)
        _validate_private_message_user_client(self.client, "recipient", self.recipient)
        self.subject = validate_text_field("subject", self.subject)
        self.body = validate_text_field("body", self.body)
        self.created_at = _validate_private_message_created_at(self.created_at)

    def __str__(self) -> str:
        """
        String representation of the object

        Returns
        -------
        str
            String representation of the message
        """
        return f"PrivateMessage(id={self.id}, sender={self.sender}, recipient={self.recipient}, subject={self.subject})"

    @staticmethod
    def from_id(client: "Client", message_id: int) -> "PrivateMessage":
        """
        Retrieve a message object from a message ID

        Parameters
        ----------
        client : Client
            Client instance
        message_id : int
            Message ID to retrieve

        Returns
        -------
        PrivateMessage
            Retrieved message object

        Raises
        ------
        LoginRequiredException
            If not logged in
        ForbiddenException
            If no permission to access the message
        IndexError
            If message not found
        """
        message_id = _validate_private_message_id(message_id)
        return PrivateMessageCollection.from_ids(client, [message_id])[0]

    @staticmethod
    def send(client: "Client", recipient: "User", subject: str, body: str) -> None:
        """
        Send a private message

        Parameters
        ----------
        client : Client
            Client instance
        recipient : User
            Recipient of the message
        subject : str
            Subject of the message
        body : str
            Body of the message

        Raises
        ------
        LoginRequiredException
            If not logged in
        """
        subject = validate_text_field("subject", subject)
        body = validate_text_field("body", body)
        recipient = _validate_private_message_recipient(recipient)
        client = _validate_private_message_client(client)
        client.login_check()

        response = client.amc_client.request(
            [
                {
                    "source": body,
                    "subject": subject,
                    "to_user_id": recipient.id,
                    "action": "DashboardMessageAction",
                    "event": "send",
                    "moduleName": "Empty",
                }
            ]
        )[0]
        _require_private_message_send_action_status(recipient, "send", response.json())
