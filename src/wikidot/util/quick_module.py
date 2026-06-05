from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar
from urllib.parse import urlencode

import httpx

from .http import sync_get_with_retry


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

        params = urlencode({"module": module_name, "s": site_id, "q": query})
        url = f"https://www.wikidot.com/quickmodule.php?{params}"
        response = sync_get_with_retry(url, timeout=300, attempt_limit=3, raise_for_status=False)
        if response.status_code == httpx.codes.INTERNAL_SERVER_ERROR:
            raise ValueError("Site is not found")
        return response.json()

    @staticmethod
    def _generic_lookup(
        module_name: str,
        site_id: int,
        query: str,
        response_key: str,
        item_class: type[T],
        item_mapping: Callable[[type[T], dict[str, Any]], T],
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
        item_class: type
            Class of items to return
        item_mapping: callable
            Conversion function from response items to class instances

        Returns
        -------
        list
            List of items
        """
        items = QuickModule._request(module_name, site_id, query)[response_key]
        # member_lookupの特殊ケースを処理
        if items is False:
            return []
        return [item_mapping(item_class, item) for item in items]

    @staticmethod
    def _map_user_item(module_name: str, site_id: int, row_index: int, item: dict[str, Any]) -> QMCUser:
        user_id_value = item["user_id"]
        try:
            user_id = int(str(user_id_value))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"QuickModule user ID is malformed for module: {module_name}, site_id={site_id} "
                f"(row={row_index}, field=user_id, value={user_id_value})"
            ) from exc

        return QMCUser(id=user_id, name=item["name"])

    @staticmethod
    def _user_lookup(module_name: str, site_id: int, query: str) -> list[QMCUser]:
        items = QuickModule._request(module_name, site_id, query)["users"]
        # member_lookupの特殊ケースを処理
        if items is False:
            return []
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
            QMCPage,
            lambda cls, item: cls(title=item["title"], unix_name=item["unix_name"]),
        )
