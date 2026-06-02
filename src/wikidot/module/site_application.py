"""
Module for handling site join applications on Wikidot

This module provides classes and functionality related to site join applications on Wikidot.
It enables operations such as retrieving, accepting, and declining applications.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup, Tag

from ..common import exceptions
from ..common.decorators import login_required
from ..util.parser import user as user_parser

if TYPE_CHECKING:
    from ..module.site import Site
    from ..module.user import AbstractUser


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
    @login_required
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
        response = site.amc_request([{"moduleName": "managesite/ManageSiteMembersApplicationsModule"}])[0]

        body = response.json()["body"]

        if "WIKIDOT.page.listeners.loginClick(event)" in body:
            raise exceptions.ForbiddenException("You are not allowed to access this page")

        html = BeautifulSoup(response.json()["body"], "lxml")

        applications = []

        application_headers = [header for header in html.select("h3") if header.select_one("span.printuser")]
        used_text_tables: set[int] = set()

        for header in application_headers:
            user_element = header.select_one("span.printuser")
            if user_element is None:
                continue

            text_wrapper_element = header.find_next_sibling("table")
            if not isinstance(text_wrapper_element, Tag):
                raise exceptions.NoElementException("Application text table is not found")
            if id(text_wrapper_element) in used_text_tables:
                raise exceptions.UnexpectedException("Length of application users and text tables are different")
            used_text_tables.add(id(text_wrapper_element))

            text_cells = text_wrapper_element.select("td")
            if len(text_cells) < 2:
                raise exceptions.NoElementException("Application text cell is not found")

            user = user_parser(site.client, user_element)
            text = text_cells[1].text.strip()

            applications.append(SiteApplication(site, user, text))

        return applications

    @login_required
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
            If an invalid action is specified
        NotFoundException
            If the specified application is not found
        WikidotStatusCodeException
            If other errors occur
        """
        if action not in ["accept", "decline"]:
            raise ValueError(f"Invalid action: {action}")

        try:
            self.site.amc_request(
                [
                    {
                        "action": "ManageSiteMembershipAction",
                        "event": "acceptApplication",
                        "user_id": self.user.id,
                        "text": f"your application has been {action}ed",
                        "type": action,
                        "moduleName": "Empty",
                    }
                ]
            )
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
