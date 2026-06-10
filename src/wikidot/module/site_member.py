"""
Module for handling Wikidot site members

This module provides classes and functionality related to Wikidot site members.
It enables operations such as retrieving member information and changing permissions.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup, Tag

from ..common.exceptions import (
    NoElementException,
    TargetErrorException,
    UnexpectedException,
    WikidotStatusCodeException,
)
from ..util.parser import odate as odate_parser
from ..util.parser import user as user_parser
from .user import AbstractUser

if TYPE_CHECKING:
    from .client import Client
    from .site import Site


def _user_onclick_value(user_elem: Tag) -> str:
    link_elem = user_elem.find("a", recursive=False)
    if isinstance(link_elem, Tag):
        onclick = link_elem.get("onclick")
        if onclick is not None:
            return str(onclick)
    return user_elem.get_text(" ", strip=True)


def _odate_class_value(odate_elem: Tag) -> str:
    class_attr = odate_elem.get("class", [])
    if class_attr is None:
        return ""

    class_values = [class_attr] if isinstance(class_attr, str) else [str(value) for value in class_attr]
    return next((value for value in class_values if "time_" in value), " ".join(class_values))


def _member_parse_context(
    site: "Site",
    group_label: str | None,
    page: int | None,
    row_index: int,
    **details: object,
) -> str:
    context = f"for site: {site.unix_name}"
    if group_label is not None:
        context = f"{context}, group: {group_label}"
    if page is not None:
        context = f"{context}, page: {page}"

    detail_text = ", ".join([f"row: {row_index}", *(f"{key}={value}" for key, value in details.items())])
    return f"{context}, {detail_text}"


def _parse_member_pager_page(site: "Site", group_label: str, page_text: str) -> int | None:
    if re.fullmatch(r"[0-9]+", page_text) is not None:
        return int(page_text)

    if page_text.isdigit():
        raise NoElementException(
            "Site member pager page is malformed "
            f"for site: {site.unix_name}, group: {group_label}, page: 1 (field=page, value={page_text})"
        )

    return None


def _parse_member_user(
    site: "Site",
    user_elem: Tag,
    group_label: str | None,
    page: int | None,
    row_index: int,
) -> "AbstractUser":
    try:
        return user_parser(site.client, user_elem)
    except ValueError as exc:
        parse_context = _member_parse_context(
            site,
            group_label,
            page,
            row_index,
            field="user",
            value=_user_onclick_value(user_elem),
        )
        raise NoElementException(f"Site member user is malformed {parse_context}") from exc


def _parse_member_joined_at(
    site: "Site",
    joined_at_elem: Tag,
    group_label: str | None,
    page: int | None,
    row_index: int,
) -> datetime:
    try:
        return odate_parser(joined_at_elem)
    except ValueError as exc:
        parse_context = _member_parse_context(
            site,
            group_label,
            page,
            row_index,
            field="joined_at",
            value=_odate_class_value(joined_at_elem),
        )
        raise NoElementException(f"Site member joined_at is malformed {parse_context}") from exc


def _require_site_member_action_status(member: "SiteMember", event: str, data: dict[str, Any]) -> Any:
    try:
        status = data["status"]
    except KeyError as exc:
        raise NoElementException(
            f"Site member action response is malformed for site: {member.site.unix_name}, "
            f"user: {member.user.name} (id={member.user.id}, event={event}, field=status)"
        ) from exc

    if not isinstance(status, str):
        raise NoElementException(
            f"Site member action response is malformed for site: {member.site.unix_name}, "
            f"user: {member.user.name} "
            f"(id={member.user.id}, event={event}, field=status, expected=str, actual={type(status).__name__})"
        )

    if status != "ok":
        raise WikidotStatusCodeException(
            f"Failed to complete site member action for site: {member.site.unix_name}, "
            f"user: {member.user.name}, event: {event}",
            status,
        )
    return status


def _validate_site_member_user(user: object) -> AbstractUser:
    if not isinstance(user, AbstractUser):
        raise ValueError("member.user must be an AbstractUser")
    _validate_site_member_user_id(user.id)
    return user


def _validate_site_member_user_id(user_id: object) -> int | None:
    if user_id is None:
        return None
    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValueError("member.user.id must be an integer or None")
    if user_id < 0:
        raise ValueError("member.user.id must be non-negative")
    return user_id


def _validate_site_member_site(site: object) -> "Site":
    from .site import Site

    if not isinstance(site, Site):
        raise ValueError("site must be a Site")
    return site


def _validate_site_member_site_client(site: "Site") -> "Client":
    from .client import Client

    if not isinstance(site.client, Client):
        raise ValueError("client must be a Client")
    return site.client


def _validate_site_member_user_site(site: "Site", user: AbstractUser) -> None:
    if user.client is not site.client:
        raise ValueError("member.user must belong to the site")


def _validate_site_member_joined_at(joined_at: object) -> datetime | None:
    if joined_at is None:
        return None
    if not isinstance(joined_at, datetime):
        raise ValueError("joined_at must be a datetime or None")
    return joined_at


def _validate_site_member_action_user(user: object) -> AbstractUser:
    user = _validate_site_member_user(user)
    if not isinstance(user.id, int) or isinstance(user.id, bool):
        raise ValueError("member.user.id must be an integer")
    if user.id < 0:
        raise ValueError("member.user.id must be non-negative")
    if not isinstance(user.name, str):
        raise ValueError("member.user.name must be a string")
    return user


@dataclass
class SiteMember:
    """
    Class representing a member of a Wikidot site

    Holds site member information and provides functionality for operations such as permission changes.

    Attributes
    ----------
    site : Site
        The site the member belongs to
    user : AbstractUser
        The member user
    joined_at : datetime | None
        Date and time the member joined the site (None if unavailable)
    """

    site: "Site"
    user: "AbstractUser"
    joined_at: datetime | None

    def __post_init__(self) -> None:
        self.site = _validate_site_member_site(self.site)
        self.user = _validate_site_member_user(self.user)
        _validate_site_member_user_site(self.site, self.user)
        self.joined_at = _validate_site_member_joined_at(self.joined_at)

    @staticmethod
    def _parse(
        site: "Site",
        html: BeautifulSoup,
        group_label: str | None = None,
        page: int | None = None,
    ) -> list["SiteMember"]:
        """
        Internal method to extract member information from member list page HTML

        Parameters
        ----------
        site : Site
            The site the members belong to
        html : BeautifulSoup
            HTML to parse

        Returns
        -------
        list[SiteMember]
            List of extracted members
        """
        members: list[SiteMember] = []

        for table in html.find_all("table"):
            if not isinstance(table, Tag) or table.find_parent("table") is not None:
                continue

            tbody = table.find("tbody", recursive=False)
            row_container = tbody if isinstance(tbody, Tag) else table

            for row_index, row in enumerate(row_container.find_all("tr", recursive=False), start=1):
                if not isinstance(row, Tag):
                    continue

                tds = [td for td in row.find_all("td", recursive=False) if isinstance(td, Tag)]
                if not tds:
                    continue

                user_elem = tds[0].find("span", class_="printuser", recursive=False)

                if not isinstance(user_elem, Tag):
                    continue

                user = _parse_member_user(site, user_elem, group_label, page, row_index)

                # tdsが2つあったら加入日時がある
                if len(tds) == 2:
                    joined_at_elem = tds[1].find("span", class_="odate", recursive=False)
                    if not isinstance(joined_at_elem, Tag):
                        joined_at = None
                    else:
                        joined_at = _parse_member_joined_at(site, joined_at_elem, group_label, page, row_index)
                else:
                    joined_at = None

                members.append(SiteMember(site, user, joined_at))

        return members

    @staticmethod
    def _is_inside_member_row(element: Tag) -> bool:
        for ancestor in element.parents:
            if not isinstance(ancestor, Tag) or ancestor.name != "tr":
                continue

            tds = [td for td in ancestor.find_all("td", recursive=False) if isinstance(td, Tag)]
            if not tds:
                continue

            if isinstance(tds[0].find("span", class_="printuser", recursive=False), Tag):
                return True

        return False

    @staticmethod
    def _pager_from_html(html: BeautifulSoup) -> Tag | None:
        for pager in html.select("div.pager"):
            if not isinstance(pager, Tag) or SiteMember._is_inside_member_row(pager):
                continue

            return pager

        return None

    @staticmethod
    def get(site: "Site", group: str | None = None) -> list["SiteMember"]:
        """
        Retrieve the member list of a site

        Retrieves a list of members of the specified group (admins, moderators, etc.).

        Parameters
        ----------
        site : Site
            The site to retrieve members from
        group : str | None, default None
            Group of members to retrieve ("admins", "moderators", or "" for all members)

        Returns
        -------
        list[SiteMember]
            List of members

        Raises
        ------
        ValueError
            If an invalid group is specified
        """
        if group is None:
            group = ""

        if group not in ["admins", "moderators", ""]:
            raise ValueError("Invalid group")

        site = _validate_site_member_site(site)
        group_label = group or "members"
        members: list[SiteMember] = []

        first_response = site.amc_request_with_retry(
            [
                {
                    "moduleName": "membership/MembersListModule",
                    "page": 1,
                    "group": group,
                }
            ]
        )[0]
        if first_response is None:
            raise UnexpectedException(
                f"Cannot retrieve site members for site: {site.unix_name}, group: {group_label}, page: 1"
            )

        first_body = SiteMember._member_list_response_body(first_response, site, group_label, 1)
        first_html = BeautifulSoup(first_body, "lxml")

        members.extend(SiteMember._parse(site, first_html, group_label, 1))

        pager = SiteMember._pager_from_html(first_html)
        if pager is None:
            return members

        last_page = 1
        for link in reversed(pager.select("a")):
            page_text = link.get_text(strip=True)
            parsed_page = _parse_member_pager_page(site, group_label, page_text)
            if parsed_page is not None:
                last_page = parsed_page
                break
        if last_page == 1:
            return members

        page_numbers = list(range(2, last_page + 1))
        responses = site.amc_request_with_retry(
            [
                {
                    "moduleName": "membership/MembersListModule",
                    "page": page,
                    "group": group,
                }
                for page in page_numbers
            ]
        )

        for page, response in zip(page_numbers, responses, strict=True):
            if response is None:
                raise UnexpectedException(
                    f"Cannot retrieve site members for site: {site.unix_name}, group: {group_label}, page: {page}"
                )
            body = SiteMember._member_list_response_body(response, site, group_label, page)
            html = BeautifulSoup(body, "lxml")
            members.extend(SiteMember._parse(site, html, group_label, page))

        return members

    @staticmethod
    def _member_list_response_body(response: Any, site: "Site", group_label: str, page: int) -> str:
        body = response.json().get("body")
        if body is None:
            raise NoElementException(
                "Site member list response body is not found "
                f"for site: {site.unix_name}, group: {group_label}, page: {page}"
            )
        if not isinstance(body, str):
            raise NoElementException(
                "Site member list response body is malformed "
                f"for site: {site.unix_name}, group: {group_label}, page: {page} "
                f"(field=body, expected=str, actual={type(body).__name__})"
            )
        return body

    def _change_group(self, event: str) -> None:
        """
        Internal method to change a member's group (permissions)

        Common method for promoting to or demoting from moderator or admin.

        Parameters
        ----------
        event : str
            Change event ("toModerators", "removeModerator", "toAdmins", "removeAdmin")

        Raises
        ------
        ValueError
            If an invalid event is specified
        ForbiddenException
            If insufficient permissions
        TargetErrorException
            If the user already has or doesn't have the specified permission
        WikidotStatusCodeException
            If other errors occur
        """
        if event not in [
            "toModerators",
            "removeModerator",
            "toAdmins",
            "removeAdmin",
        ]:
            raise ValueError("Invalid event")

        site = _validate_site_member_site(self.site)
        user = _validate_site_member_action_user(self.user)
        _validate_site_member_user_site(site, user)
        client = _validate_site_member_site_client(site)
        client.login_check()

        try:
            response = site.amc_request(
                [
                    {
                        "action": "ManageSiteMembershipAction",
                        "event": event,
                        "user_id": user.id,
                        "moduleName": "",
                    }
                ]
            )[0]
            _require_site_member_action_status(self, event, response.json())
            if event in ("toModerators", "removeModerator"):
                site._moderators = None
            else:
                site._admins = None
        except WikidotStatusCodeException as e:
            if e.status_code == "not_already":
                raise TargetErrorException(f"User is not moderator/admin: {user.name}") from e

            if e.status_code in ("already_admin", "already_moderator"):
                raise TargetErrorException(
                    f"User is already {e.status_code.removeprefix('already_')}: {user.name}"
                ) from e

            raise e

    def to_moderator(self) -> None:
        """
        Promote a member to moderator

        Raises
        ------
        ForbiddenException
            If insufficient permissions
        TargetErrorException
            If the user is already a moderator
        WikidotStatusCodeException
            If other errors occur
        """
        self._change_group("toModerators")

    def remove_moderator(self) -> None:
        """
        Remove moderator permissions from a member

        Raises
        ------
        ForbiddenException
            If insufficient permissions
        TargetErrorException
            If the user is not a moderator
        WikidotStatusCodeException
            If other errors occur
        """
        self._change_group("removeModerator")

    def to_admin(self) -> None:
        """
        Promote a member to admin

        Raises
        ------
        ForbiddenException
            If insufficient permissions
        TargetErrorException
            If the user is already an admin
        WikidotStatusCodeException
            If other errors occur
        """
        self._change_group("toAdmins")

    def remove_admin(self) -> None:
        """
        Remove admin permissions from a member

        Raises
        ------
        ForbiddenException
            If insufficient permissions
        TargetErrorException
            If the user is not an admin
        WikidotStatusCodeException
            If other errors occur
        """
        self._change_group("removeAdmin")
