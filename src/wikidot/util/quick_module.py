from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar
from urllib.parse import urlencode

import httpx

from .http import sync_get_with_retry


def _validate_qmc_integer_field(field: str, value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    return value


def _validate_qmc_text_field(field: str, value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def _validate_qmc_user_name(name: object) -> str:
    name = _validate_qmc_text_field("name", name)
    if name.strip() == "":
        raise ValueError("name must not be empty")
    return name


def _validate_quickmodule_site_id(site_id: object) -> int:
    if not isinstance(site_id, int) or isinstance(site_id, bool):
        raise ValueError("site_id must be an integer")
    return site_id


def _validate_quickmodule_query(query: object) -> str:
    if not isinstance(query, str):
        raise ValueError("query must be a string")
    return query


def _validate_quickmodule_user_query(query: object) -> str:
    query = _validate_quickmodule_query(query)
    if query.strip() == "":
        raise ValueError("query must not be empty")
    return query


@dataclass
class QMCUser:
    """Class to store user information returned from QuickModule

    Attributes
    ----------
    id: int
        User ID
    name: str
        User name
    """

    id: int
    name: str

    def __post_init__(self) -> None:
        self.id = _validate_qmc_integer_field("id", self.id)
        self.name = _validate_qmc_user_name(self.name)


@dataclass
class QMCPage:
    """Class to store page information returned from QuickModule

    Attributes
    ----------
    title: str
        Page title
    unix_name: str
        UNIX name of the page
    """

    title: str
    unix_name: str

    def __post_init__(self) -> None:
        self.title = _validate_qmc_text_field("title", self.title)
        self.unix_name = _validate_qmc_text_field("unix_name", self.unix_name)


T = TypeVar("T", QMCUser, QMCPage)


class QuickModule:
    @staticmethod
    def _request(
        module_name: str,
        site_id: int,
        query: str,
    ) -> dict[str, Any]:
        """Send a request

        Parameters
        ----------
        module_name: str
            Module name
        site_id: int
            Site ID
        query: str
            Query
        """

        if module_name not in [
            "MemberLookupQModule",
            "UserLookupQModule",
            "PageLookupQModule",
        ]:
            raise ValueError("Invalid module name")

        site_id = _validate_quickmodule_site_id(site_id)
        query = _validate_quickmodule_query(query)

        params = urlencode({"module": module_name, "s": site_id, "q": query})
        url = f"https://www.wikidot.com/quickmodule.php?{params}"
        response = sync_get_with_retry(url, timeout=300, attempt_limit=3, raise_for_status=False)
        if response.status_code == httpx.codes.INTERNAL_SERVER_ERROR:
            raise ValueError("Site is not found")
        try:
            return response.json()
        except ValueError as exc:
            raise ValueError(
                f"QuickModule response JSON is malformed for module: {module_name}, site_id={site_id}"
            ) from exc

    @staticmethod
    def _response_items(module_name: str, site_id: int, query: str, response_key: str) -> list[Any]:
        response_data = QuickModule._request(module_name, site_id, query)
        if not isinstance(response_data, dict):
            raise ValueError(
                f"QuickModule response body is malformed for module: {module_name}, site_id={site_id} "
                f"(expected=dict, actual={type(response_data).__name__})"
            )
        if response_key not in response_data:
            raise ValueError(
                f"QuickModule response key is missing for module: {module_name}, site_id={site_id} "
                f"(field={response_key})"
            )

        items = response_data[response_key]
        if items is False:
            return []
        if not isinstance(items, list):
            raise ValueError(
                f"QuickModule response field is malformed for module: {module_name}, site_id={site_id} "
                f"(field={response_key}, expected=list, actual={type(items).__name__})"
            )
        return items

    @staticmethod
    def _generic_lookup(
        module_name: str,
        site_id: int,
        query: str,
        response_key: str,
        item_mapping: Callable[[str, int, int, dict[str, Any]], T],
    ) -> list[T]:
        """
        Generic lookup method

        Parameters
        ----------
        module_name: str
            Module name
        site_id: int
            Site ID
        query: str
            Query
        response_key: str
            Key to retrieve from response
        item_mapping: callable
            Conversion function from response items to class instances

        Returns
        -------
        list
            List of items
        """
        items = QuickModule._response_items(module_name, site_id, query, response_key)
        return [item_mapping(module_name, site_id, row_index, item) for row_index, item in enumerate(items, start=1)]

    @staticmethod
    def _row_field(module_name: str, site_id: int, row_index: int, item: Any, field: str) -> Any:
        if not isinstance(item, dict):
            raise ValueError(
                f"QuickModule row is malformed for module: {module_name}, site_id={site_id} "
                f"(row={row_index}, expected=dict, actual={type(item).__name__})"
            )
        if field not in item:
            raise ValueError(
                f"QuickModule row field is missing for module: {module_name}, site_id={site_id} "
                f"(row={row_index}, field={field})"
            )
        return item[field]

    @staticmethod
    def _row_text_field(module_name: str, site_id: int, row_index: int, item: Any, field: str) -> str:
        value = QuickModule._row_field(module_name, site_id, row_index, item, field)
        if not isinstance(value, str):
            raise ValueError(
                f"QuickModule row field is malformed for module: {module_name}, site_id={site_id} "
                f"(row={row_index}, field={field}, expected=str, actual={type(value).__name__})"
            )
        return value

    @staticmethod
    def _row_non_empty_text_field(module_name: str, site_id: int, row_index: int, item: Any, field: str) -> str:
        value = QuickModule._row_text_field(module_name, site_id, row_index, item, field)
        if value.strip() == "":
            raise ValueError(
                f"QuickModule row field is empty for module: {module_name}, site_id={site_id} "
                f"(row={row_index}, field={field})"
            )
        return value

    @staticmethod
    def _map_user_item(module_name: str, site_id: int, row_index: int, item: dict[str, Any]) -> QMCUser:
        user_id_value = QuickModule._row_field(module_name, site_id, row_index, item, "user_id")
        try:
            user_id = int(str(user_id_value))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"QuickModule user ID is malformed for module: {module_name}, site_id={site_id} "
                f"(row={row_index}, field=user_id, value={user_id_value})"
            ) from exc

        return QMCUser(
            id=user_id,
            name=QuickModule._row_non_empty_text_field(module_name, site_id, row_index, item, "name"),
        )

    @staticmethod
    def _map_page_item(module_name: str, site_id: int, row_index: int, item: dict[str, Any]) -> QMCPage:
        return QMCPage(
            title=QuickModule._row_text_field(module_name, site_id, row_index, item, "title"),
            unix_name=QuickModule._row_text_field(module_name, site_id, row_index, item, "unix_name"),
        )

    @staticmethod
    def _user_lookup(module_name: str, site_id: int, query: str) -> list[QMCUser]:
        query = _validate_quickmodule_user_query(query)
        items = QuickModule._response_items(module_name, site_id, query, "users")
        return [
            QuickModule._map_user_item(module_name, site_id, row_index, item)
            for row_index, item in enumerate(items, start=1)
        ]

    @staticmethod
    def member_lookup(site_id: int, query: str) -> list[QMCUser]:
        """Search for members

        Parameters
        ----------
        site_id: int
            Site ID
        query: str
            Query

        Returns
        -------
        list[QMCUser]
            List of users
        """
        return QuickModule._user_lookup("MemberLookupQModule", site_id, query)

    @staticmethod
    def user_lookup(site_id: int, query: str) -> list[QMCUser]:
        """Search for users

        Parameters
        ----------
        site_id: int
            Site ID
        query: str
            Query

        Returns
        -------
        list[QMCUser]
            List of users
        """
        return QuickModule._user_lookup("UserLookupQModule", site_id, query)

    @staticmethod
    def page_lookup(site_id: int, query: str) -> list[QMCPage]:
        """Search for pages

        Parameters
        ----------
        site_id: int
            Site ID
        query: str
            Query

        Returns
        -------
        list[QMCPage]
            List of pages
        """
        return QuickModule._generic_lookup(
            "PageLookupQModule",
            site_id,
            query,
            "pages",
            QuickModule._map_page_item,
        )
