"""
Module for handling Wikidot private messages

This module provides classes and functionality related to Wikidot private messages (PM).
It enables operations such as sending messages, retrieving inbox/sent box, and viewing messages.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from bs4 import BeautifulSoup, Tag
from typing_extensions import Self

from ..common import exceptions
from ..common.decorators import login_required
from ..util.parser import odate as odate_parser
from ..util.parser import user as user_parser

if TYPE_CHECKING:
    from .client import Client
    from .user import AbstractUser, User


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


class PrivateMessageCollection(list["PrivateMessage"]):
    """
    Base class representing a collection of private messages

    A list extension class for storing multiple private messages and performing batch operations.
    Inherited to represent specific message groups such as inbox or sent box.
    """

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
        for message in self:
            if message.id == id:
                return message

        return None

    @staticmethod
    def _amc_request_with_retry(client: "Client", bodies: list[dict[str, Any]]) -> tuple[Any | None, ...]:
        config = getattr(client.amc_client, "config", None)
        batch_size = getattr(config, "retry_batch_size", 50)
        max_retries = getattr(config, "retry_max_retries", 3)

        if not isinstance(batch_size, int):
            batch_size = 50
        if not isinstance(max_retries, int):
            max_retries = 3
        if batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {batch_size}")
        if max_retries < 0:
            raise ValueError(f"max_retries must be non-negative, got {max_retries}")

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
        if len(message_ids) == 0:
            return PrivateMessageCollection([])

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
            if odate_element is None:
                raise exceptions.NoElementException(f"Message odate element is not found {parse_context}, field=odate")

            parsed_messages_by_id[message_id] = (
                user_parser(client, sender),
                user_parser(client, recipient),
                subject_element.get_text(" ", strip=True) if subject_element else "",
                body_element.get_text(" ", strip=True) if body_element else "",
                odate_parser(odate_element),
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
        return PrivateMessageCollection.from_ids(client, [message_id])[0]

    @staticmethod
    @login_required
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
