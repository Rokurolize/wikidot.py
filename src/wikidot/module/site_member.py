"""
Module for handling Wikidot site members

This module provides classes and functionality related to Wikidot site members.
It enables operations such as retrieving member information and changing permissions.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup, Tag

from ..common.exceptions import (
    TargetErrorException,
    UnexpectedException,
    WikidotStatusCodeException,
)
from ..util.parser import odate as odate_parser
from ..util.parser import user as user_parser

if TYPE_CHECKING:
    from .site import Site
    from .user import AbstractUser


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

    @staticmethod
    def _parse(site: "Site", html: BeautifulSoup) -> list["SiteMember"]:
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

            for row in row_container.find_all("tr", recursive=False):
                if not isinstance(row, Tag):
                    continue

                tds = [td for td in row.find_all("td", recursive=False) if isinstance(td, Tag)]
                if not tds:
                    continue

                user_elem = tds[0].find("span", class_="printuser", recursive=False)

                if not isinstance(user_elem, Tag):
                    continue

                user = user_parser(site.client, user_elem)

                # tdsが2つあったら加入日時がある
                if len(tds) == 2:
                    joined_at_elem = tds[1].find("span", class_="odate", recursive=False)
                    if not isinstance(joined_at_elem, Tag):
                        joined_at = None
                    else:
                        joined_at = odate_parser(joined_at_elem)
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

        first_body = first_response.json()["body"]
        first_html = BeautifulSoup(first_body, "lxml")

        members.extend(SiteMember._parse(site, first_html))

        pager = SiteMember._pager_from_html(first_html)
        if pager is None:
            return members

        last_page = 1
        for link in reversed(pager.select("a")):
            page_text = link.get_text(strip=True)
            if page_text.isdigit():
                last_page = int(page_text)
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
            body = response.json()["body"]
            html = BeautifulSoup(body, "lxml")
            members.extend(SiteMember._parse(site, html))

        return members

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

        self.site.client.login_check()

        try:
            self.site.amc_request(
                [
                    {
                        "action": "ManageSiteMembershipAction",
                        "event": event,
                        "user_id": self.user.id,
                        "moduleName": "",
                    }
                ]
            )
        except WikidotStatusCodeException as e:
            if e.status_code == "not_already":
                raise TargetErrorException(f"User is not moderator/admin: {self.user.name}") from e

            if e.status_code in ("already_admin", "already_moderator"):
                raise TargetErrorException(
                    f"User is already {e.status_code.removeprefix('already_')}: {self.user.name}"
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
