"""
Module for handling site join applications on Wikidot

This module provides classes and functionality related to site join applications on Wikidot.
It enables operations such as retrieving, accepting, and declining applications.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup, Tag

from ..common import exceptions
from ..module.user import AbstractUser
from ..util.parser import user as user_parser

if TYPE_CHECKING:
    from ..module.site import Site


def _site_name(site: "Site") -> str:
    site_unix_name = getattr(site, "unix_name", None)
    return site_unix_name if isinstance(site_unix_name, str) else str(site)


def _user_onclick_value(user_elem: Tag) -> str:
    link_elem = user_elem.find("a", recursive=False)
    if isinstance(link_elem, Tag):
        onclick = link_elem.get("onclick")
        if onclick is not None:
            return str(onclick)
    return user_elem.get_text(" ", strip=True)


def _application_parse_context(
    site: "Site",
    application_index: int,
    applications_count: int,
    **details: object,
) -> str:
    context = [
        f"application={application_index}",
        f"applications={applications_count}",
    ]
    context.extend(f"{name}={value}" for name, value in details.items())
    return f"for site: {_site_name(site)} ({', '.join(context)})"


def _parse_application_user(
    site: "Site",
    application_index: int,
    applications_count: int,
    user_element: Tag,
) -> "AbstractUser":
    try:
        return user_parser(site.client, user_element)
    except ValueError as exc:
        parse_context = _application_parse_context(
            site,
            application_index,
            applications_count,
            field="user",
            value=_user_onclick_value(user_element),
        )
        raise exceptions.NoElementException(f"Site application user is malformed {parse_context}") from exc


def _validate_site_application_user_object(user: object) -> AbstractUser:
    if not isinstance(user, AbstractUser):
        raise ValueError("application.user must be an AbstractUser")
    if isinstance(user.id, int) and not isinstance(user.id, bool) and user.id < 0:
        raise ValueError("application.user.id must be non-negative")
    return user


def _validate_site_application_user(user: object) -> AbstractUser:
    user = _validate_site_application_user_object(user)
    if not isinstance(user.id, int) or isinstance(user.id, bool):
        raise ValueError("application.user.id must be an integer")
    if user.id < 0:
        raise ValueError("application.user.id must be non-negative")
    if not isinstance(user.name, str):
        raise ValueError("application.user.name must be a string")
    return user


def _validate_site_application_user_site(site: "Site", user: AbstractUser) -> None:
    if user.client is not site.client:
        raise ValueError("application.user must belong to the site")


def _validate_site_application_text(text: object) -> str:
    if not isinstance(text, str):
        raise ValueError("application.text must be a string")
    return text


def _validate_site_application_site(site: object) -> "Site":
    from .site import Site

    if not isinstance(site, Site):
        raise ValueError("site must be a Site")
    return site


def _require_site_application_action_status(
    application: "SiteApplication",
    event: str,
    action: str,
    data: dict[str, Any],
) -> Any:
    try:
        status = data["status"]
    except KeyError as exc:
        raise exceptions.NoElementException(
            f"Site application action response is malformed for site: {_site_name(application.site)}, "
            f"user: {application.user.name} "
            f"(id={application.user.id}, event={event}, type={action}, field=status)"
        ) from exc

    if status != "ok":
        raise exceptions.WikidotStatusCodeException(
            "Failed to complete site application action for "
            f"site: {_site_name(application.site)}, user: {application.user.name}, "
            f"event: {event}, type: {action}",
            status,
        )
    return status


@dataclass
class SiteApplication:
    """
    Class representing a site join application on Wikidot

    Holds site join application information from users and provides
    functionality for processing such as accepting or declining applications.

    Attributes
    ----------
    site : Site
        The site being applied to
    user : AbstractUser
        The applicant
    text : str
        Application message
    """

    site: "Site"
    user: "AbstractUser"
    text: str

    def __post_init__(self) -> None:
        self.site = _validate_site_application_site(self.site)
        self.user = _validate_site_application_user_object(self.user)
        self.text = _validate_site_application_text(self.text)
        _validate_site_application_user_site(self.site, self.user)

    def __str__(self) -> str:
        """
        String representation of the object

        Returns
        -------
        str
            String representation of the application
        """
        return f"SiteApplication(user={self.user}, site={self.site}, text={self.text})"

    @staticmethod
    def acquire_all(site: "Site") -> list["SiteApplication"]:
        """
        Retrieve all pending site join applications

        Parameters
        ----------
        site : Site
            The site to retrieve applications from

        Returns
        -------
        list[SiteApplication]
            List of site applications

        Raises
        ------
        LoginRequiredException
            If not logged in
        ForbiddenException
            If no permission to manage site applications
        UnexpectedException
            If response parsing fails
        """
        site = _validate_site_application_site(site)
        site.client.login_check()

        response = site.amc_request_with_retry([{"moduleName": "managesite/ManageSiteMembersApplicationsModule"}])[0]
        if response is None:
            raise exceptions.UnexpectedException(f"Cannot retrieve site applications for site: {_site_name(site)}")

        body = SiteApplication._application_list_response_body(response, site)

        if "WIKIDOT.page.listeners.loginClick(event)" in body:
            raise exceptions.ForbiddenException("You are not allowed to access this page")

        html = BeautifulSoup(body, "lxml")

        applications = []

        application_headers = [
            header
            for header in html.select("h3")
            if header.find_parent("table") is None and header.find("span", class_="printuser", recursive=False)
        ]
        used_text_tables: set[int] = set()

        for application_index, header in enumerate(application_headers, start=1):
            user_element = header.find("span", class_="printuser", recursive=False)
            if not isinstance(user_element, Tag):
                continue

            parse_context = _application_parse_context(site, application_index, len(application_headers))
            text_wrapper_element = header.find_next_sibling("table")
            if not isinstance(text_wrapper_element, Tag):
                raise exceptions.NoElementException(f"Application text table is not found {parse_context}")
            if id(text_wrapper_element) in used_text_tables:
                raise exceptions.UnexpectedException(
                    "Length of application users and text tables are different for site: "
                    f"{_site_name(site)} (users={len(application_headers)}, text_tables={len(used_text_tables)})"
                )
            used_text_tables.add(id(text_wrapper_element))

            text_row = text_wrapper_element.find("tr", recursive=False)
            if not isinstance(text_row, Tag):
                raise exceptions.NoElementException(f"Application text row is not found {parse_context}")

            text_cells = text_row.find_all("td", recursive=False)
            if len(text_cells) < 2:
                parse_context = _application_parse_context(
                    site,
                    application_index,
                    len(application_headers),
                    cells=len(text_cells),
                )
                raise exceptions.NoElementException(f"Application text cell is not found {parse_context}")

            user = _parse_application_user(site, application_index, len(application_headers), user_element)
            text = text_cells[1].get_text(" ", strip=True)

            applications.append(SiteApplication(site, user, text))

        return applications

    @staticmethod
    def _application_list_response_body(response: Any, site: "Site") -> str:
        body = response.json().get("body")
        if body is None:
            raise exceptions.NoElementException(
                f"Site application list response body is not found for site: {_site_name(site)}"
            )
        if not isinstance(body, str):
            raise exceptions.NoElementException(
                "Site application list response body is malformed "
                f"for site: {_site_name(site)} (field=body, expected=str, actual={type(body).__name__})"
            )
        return body

    def _process(self, action: str) -> None:
        """
        Internal method to process a site join application

        Common method for processing acceptance or decline.

        Parameters
        ----------
        action : str
            Type of action ("accept" or "decline")

        Raises
        ------
        LoginRequiredException
            If not logged in
        ValueError
            If an invalid action or applicant user is specified
        NotFoundException
            If the specified application is not found
        WikidotStatusCodeException
            If other errors occur
        """
        if action not in ["accept", "decline"]:
            raise ValueError(f"Invalid action: {action}")

        site = _validate_site_application_site(self.site)
        user = _validate_site_application_user(self.user)
        _validate_site_application_user_site(site, user)
        site.client.login_check()

        status_text = {"accept": "accepted", "decline": "declined"}[action]
        event = "acceptApplication"

        try:
            response = site.amc_request(
                [
                    {
                        "action": "ManageSiteMembershipAction",
                        "event": event,
                        "user_id": user.id,
                        "text": f"your application has been {status_text}",
                        "type": action,
                        "moduleName": "Empty",
                    }
                ]
            )[0]
            _require_site_application_action_status(self, event, action, response.json())
            if action == "accept":
                site._members = None
        except exceptions.WikidotStatusCodeException as e:
            if e.status_code == "no_application":
                raise exceptions.NotFoundException(f"Application not found: {self.user}") from e
            else:
                raise e

    def accept(self) -> None:
        """
        Accept the site join application

        Adds the applicant as a member of the site.

        Raises
        ------
        LoginRequiredException
            If not logged in
        NotFoundException
            If the specified application is not found
        WikidotStatusCodeException
            If other errors occur
        """
        self._process("accept")

    def decline(self) -> None:
        """
        Decline the site join application

        Rejects the applicant's join request and deletes the application.

        Raises
        ------
        LoginRequiredException
            If not logged in
        NotFoundException
            If the specified application is not found
        WikidotStatusCodeException
            If other errors occur
        """
        self._process("decline")
