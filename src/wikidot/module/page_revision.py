"""
Module for handling Wikidot page edit history (revisions)

This module provides classes and functions related to Wikidot page edit history (revisions).
It enables operations such as retrieving revisions, getting source code, and displaying HTML.
"""

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional, cast

import httpx
from bs4 import BeautifulSoup

from ..common.exceptions import NoElementException, UnexpectedException
from .page_source import PageSource, extract_page_source_text

if TYPE_CHECKING:
    from .page import Page
    from .user import AbstractUser


def _validate_revisions(revisions: object) -> list["PageRevision"]:
    if revisions is None:
        return []
    if not isinstance(revisions, list):
        raise ValueError("revisions must be a list or None")
    if any(not isinstance(revision, PageRevision) for revision in revisions):
        raise ValueError("revisions list entries must be PageRevision")
    return cast(list["PageRevision"], revisions)


def _validate_revision_page(value: object) -> "Page":
    from .page import Page

    if not isinstance(value, Page):
        raise ValueError("page must be a Page")
    return value


def _validate_revisions_belong_to_page(page: "Page", revisions: list["PageRevision"]) -> None:
    if any(revision.page is not page for revision in revisions):
        raise ValueError("revisions must belong to the collection page")


def _validate_revision_id(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("id must be an integer")
    if value < 0:
        raise ValueError("id must be non-negative")
    return value


def _validate_revision_number(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("rev_no must be an integer")
    if value < 0:
        raise ValueError("rev_no must be non-negative")
    return value


def _validate_revision_created_by(value: object) -> "AbstractUser":
    from .user import AbstractUser

    if not isinstance(value, AbstractUser):
        raise ValueError("created_by must be an AbstractUser")
    return value


def _validate_revision_created_by_site(page: "Page", created_by: "AbstractUser") -> None:
    if created_by.client is not page.site.client:
        raise ValueError("created_by must belong to the site")


def _validate_revision_created_at(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("created_at must be a datetime")
    return value


def _validate_revision_comment(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("comment must be a string")
    return value


def _validate_revision_source(value: object) -> PageSource:
    if not isinstance(value, PageSource):
        raise ValueError("revision.source must be PageSource")
    return value


def _validate_revision_source_belongs_to_page(page: "Page", source: PageSource) -> None:
    from .page import Page, _validate_optional_page_constructor_id

    message = "revision.source must belong to the revision page"
    source_page = source.page
    if not isinstance(source_page, Page):
        raise ValueError(message)
    if source_page.site is not page.site:
        raise ValueError(message)
    page_id = _validate_optional_page_constructor_id(page._id)
    source_page_id = _validate_optional_page_constructor_id(source_page._id)
    if page_id is not None and source_page_id is not None:
        if source_page_id != page_id:
            raise ValueError(message)
        return
    if source_page.fullname != page.fullname:
        raise ValueError(message)


def _validate_optional_revision_source(value: object) -> PageSource | None:
    if value is None:
        return None
    return _validate_revision_source(value)


def _validate_revision_html(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("revision.html must be a string")
    return value


def _validate_optional_revision_html(value: object) -> str | None:
    if value is None:
        return None
    return _validate_revision_html(value)


class PageRevisionCollection(list["PageRevision"]):
    """
    Class representing a collection of page revisions

    A list extension class for storing and operating on multiple versions of a page's
    edit history (revisions) in bulk. Provides convenient functions such as
    batch retrieval of source code and HTML.
    """

    page: "Page | None"

    def __init__(
        self,
        page: Optional["Page"] = None,
        revisions: list["PageRevision"] | None = None,
    ):
        """
        Initialize the collection

        Parameters
        ----------
        page : Page | None, default None
            The page the revisions belong to. If None, inferred from the first revision
        revisions : list[PageRevision] | None, default None
            List of revisions to store
        """
        super().__init__(_validate_revisions(revisions))
        if page is not None:
            self.page = _validate_revision_page(page)
        elif len(self) > 0:
            self.page = self[0].page
        else:
            self.page = None

    def __iter__(self) -> Iterator["PageRevision"]:
        """
        Return an iterator over the revisions in the collection

        Returns
        -------
        Iterator[PageRevision]
            Iterator of revision objects
        """
        return super().__iter__()

    def find(self, id: int) -> Optional["PageRevision"]:
        """
        Get the revision with the specified ID

        Parameters
        ----------
        id : int
            The ID of the revision to retrieve

        Returns
        -------
        PageRevision | None
            The revision with the specified ID, or None if not found
        """
        if not isinstance(id, int) or isinstance(id, bool):
            raise ValueError("id must be an integer")
        for revision in self:
            if revision.id == id:
                return revision
        return None

    @staticmethod
    def _generic_acquire(
        page: "Page",
        revisions: list["PageRevision"],
        check_acquired_func: Callable[["PageRevision"], bool],
        module_name: str,
        process_response_func: Callable[[httpx.Response, "Page", int], Callable[["PageRevision"], None]],
        copy_acquired_func: Callable[["PageRevision", "PageRevision"], None] | None = None,
    ) -> list["PageRevision"]:
        """
        Generic method for batch retrieval of revision data

        Parameters
        ----------
        page : Page
            The page the revisions belong to
        revisions : list[PageRevision]
            List of revisions to retrieve data for
        check_acquired_func : callable
            Function to check if data is already acquired
        module_name : str
            Module name to use in AMC request
        process_response_func : callable
            Function to process the response once and return an applicator for each revision
        copy_acquired_func : callable | None, default None
            Function to copy already acquired same-ID revision data before requesting

        Returns
        -------
        list[PageRevision]
            List of revisions with updated data
        """
        if any(not isinstance(revision, PageRevision) for revision in revisions):
            raise ValueError("revisions list entries must be PageRevision")
        _validate_revisions_belong_to_page(page, revisions)

        acquired_revisions_by_id: dict[int, PageRevision] = {}
        if copy_acquired_func is not None:
            for revision in revisions:
                if check_acquired_func(revision):
                    acquired_revisions_by_id[revision.id] = revision

        target_revisions_by_id: dict[int, list[PageRevision]] = {}
        for revision in revisions:
            if check_acquired_func(revision):
                continue
            acquired_revision = acquired_revisions_by_id.get(revision.id)
            if acquired_revision is not None and copy_acquired_func is not None:
                copy_acquired_func(acquired_revision, revision)
                continue
            target_revisions_by_id.setdefault(revision.id, []).append(revision)

        if len(target_revisions_by_id) == 0:
            return revisions

        responses = page.site.amc_request_with_retry(
            [{"moduleName": module_name, "revision_id": revision_id} for revision_id in target_revisions_by_id]
        )

        for revision_id, response in zip(target_revisions_by_id, responses, strict=True):
            if response is None:
                continue
            apply_response = process_response_func(response, page, revision_id)
            for revision in target_revisions_by_id[revision_id]:
                apply_response(revision)

        return revisions

    @staticmethod
    def _acquire_sources(page: "Page", revisions: list["PageRevision"]) -> list["PageRevision"]:
        """
        Internal method to batch retrieve source code for multiple revisions

        Requests and retrieves source code for revisions that haven't been fetched yet.

        Parameters
        ----------
        page : Page
            The page the revisions belong to
        revisions : list[PageRevision]
            List of revisions to retrieve source code for

        Returns
        -------
        list[PageRevision]
            List of revisions with updated source code information

        Raises
        ------
        NoElementException
            If source element is not found
        """

        def process_source_response(
            response: httpx.Response, page: "Page", revision_id: int
        ) -> Callable[["PageRevision"], None]:
            body = response.json().get("body")
            if body is None:
                raise NoElementException(
                    f"Page revision source response body is not found for site: {page.site.unix_name}, "
                    f"page: {page.fullname}, revision: {revision_id}"
                )
            if not isinstance(body, str):
                raise NoElementException(
                    f"Page revision source response body is malformed for site: {page.site.unix_name}, "
                    f"page: {page.fullname}, revision: {revision_id} "
                    f"(field=body, expected=str, actual={type(body).__name__})"
                )
            # Replace nbsp with space
            body = body.replace("&nbsp;", " ")
            body_html = BeautifulSoup(body, "lxml")
            wiki_text_elem = body_html.select_one("div.page-source")
            if wiki_text_elem is None:
                raise NoElementException(
                    f"Wiki text element not found for site: {page.site.unix_name}, "
                    f"page: {page.fullname}, revision: {revision_id}"
                )
            wiki_text = extract_page_source_text(wiki_text_elem)

            def apply_source(revision: "PageRevision") -> None:
                revision.source = PageSource(page=page, wiki_text=wiki_text)

            return apply_source

        def copy_acquired_source(acquired: "PageRevision", revision: "PageRevision") -> None:
            revision._source = acquired._source

        return PageRevisionCollection._generic_acquire(
            page,
            revisions,
            lambda r: r.is_source_acquired(),
            "history/PageSourceModule",
            process_source_response,
            copy_acquired_source,
        )

    def get_sources(self) -> "PageRevisionCollection":
        """
        Get source code for all revisions in the collection

        Returns
        -------
        PageRevisionCollection
            Self (for method chaining)
        """
        if self.page is None:
            raise ValueError("Page is not set for this collection")
        self._acquire_sources(self.page, self)
        return self

    @staticmethod
    def _acquire_htmls(page: "Page", revisions: list["PageRevision"]) -> list["PageRevision"]:
        """
        Internal method to batch retrieve HTML display for multiple revisions

        Requests and retrieves HTML for revisions that haven't been fetched yet.

        Parameters
        ----------
        page : Page
            The page the revisions belong to
        revisions : list[PageRevision]
            List of revisions to retrieve HTML for

        Returns
        -------
        list[PageRevision]
            List of revisions with updated HTML information
        """

        def process_html_response(
            response: httpx.Response, page: "Page", revision_id: int
        ) -> Callable[["PageRevision"], None]:
            body = response.json().get("body")
            if body is None:
                raise NoElementException(
                    f"Page revision HTML response body is not found for site: {page.site.unix_name}, "
                    f"page: {page.fullname}, revision: {revision_id}"
                )
            if not isinstance(body, str):
                raise NoElementException(
                    f"Page revision HTML response body is malformed for site: {page.site.unix_name}, "
                    f"page: {page.fullname}, revision: {revision_id} "
                    f"(field=body, expected=str, actual={type(body).__name__})"
                )
            marker = "onclick=\"document.getElementById('page-version-info').style.display='none'\">"
            _, separator, source = body.partition(marker)
            if separator:
                _, close_separator, source = source.partition("</a>")
                if close_separator:
                    source = re.sub(r"^\s*</div>\s*", "", source, count=1)
                else:
                    source = body
            else:
                source = body

            def apply_html(revision: "PageRevision") -> None:
                revision._html = source

            return apply_html

        def copy_acquired_html(acquired: "PageRevision", revision: "PageRevision") -> None:
            revision._html = acquired._html

        return PageRevisionCollection._generic_acquire(
            page,
            revisions,
            lambda r: r.is_html_acquired(),
            "history/PageVersionModule",
            process_html_response,
            copy_acquired_html,
        )

    def get_htmls(self) -> "PageRevisionCollection":
        """
        Get HTML display for all revisions in the collection

        Returns
        -------
        PageRevisionCollection
            Self (for method chaining)
        """
        if self.page is None:
            raise ValueError("Page is not set for this collection")
        self._acquire_htmls(self.page, self)
        return self


@dataclass
class PageRevision:
    """
    Class representing a page revision (version in edit history)

    Holds information about a specific version of a page. Provides basic information
    such as revision number, creator, creation date, and edit comment, along with
    access to source code and HTML display.

    Attributes
    ----------
    page : Page
        The page this revision belongs to
    id : int
        Revision ID
    rev_no : int
        Revision number
    created_by : AbstractUser
        The creator of the revision
    created_at : datetime
        The creation date and time of the revision
    comment : str
        Edit comment
    _source : PageSource | None, default None
        The revision's source code (internal cache)
    _html : str | None, default None
        The revision's HTML display (internal cache)
    """

    page: "Page"
    id: int
    rev_no: int
    created_by: "AbstractUser"
    created_at: datetime
    comment: str
    _source: Optional["PageSource"] = None
    _html: str | None = None

    def __post_init__(self) -> None:
        self.page = _validate_revision_page(self.page)
        self.id = _validate_revision_id(self.id)
        self.rev_no = _validate_revision_number(self.rev_no)
        self.created_by = _validate_revision_created_by(self.created_by)
        _validate_revision_created_by_site(self.page, self.created_by)
        self.created_at = _validate_revision_created_at(self.created_at)
        self.comment = _validate_revision_comment(self.comment)
        self._source = _validate_optional_revision_source(self._source)
        if self._source is not None:
            _validate_revision_source_belongs_to_page(self.page, self._source)
        self._html = _validate_optional_revision_html(self._html)

    def is_source_acquired(self) -> bool:
        """
        Check if source code has already been acquired

        Returns
        -------
        bool
            True if source code is acquired, False otherwise
        """
        return self._source is not None

    def is_html_acquired(self) -> bool:
        """
        Check if HTML display has already been acquired

        Returns
        -------
        bool
            True if HTML display is acquired, False otherwise
        """
        return self._html is not None

    @property
    def source(self) -> "PageSource":
        """
        Get the revision's source code

        Automatically fetches the source code if not yet acquired.

        Returns
        -------
        PageSource
            The revision's source code
        """
        if not self.is_source_acquired():
            PageRevisionCollection(self.page, [self]).get_sources()
        if self._source is None:
            raise UnexpectedException(
                f"Cannot retrieve page revision source for site: {self.page.site.unix_name}, "
                f"page: {self.page.fullname}, revision: {self.id}"
            )
        return self._source

    @source.setter
    def source(self, value: "PageSource") -> None:
        """
        Set the revision's source code

        Parameters
        ----------
        value : PageSource
            The source code to set
        """
        source = _validate_revision_source(value)
        _validate_revision_source_belongs_to_page(self.page, source)
        self._source = source

    @property
    def html(self) -> str:
        """
        Get the revision's HTML display

        Automatically fetches the HTML display if not yet acquired.

        Returns
        -------
        str
            The revision's HTML display
        """
        if not self.is_html_acquired():
            PageRevisionCollection(self.page, [self]).get_htmls()
        if self._html is None:
            raise UnexpectedException(
                f"Cannot retrieve page revision HTML for site: {self.page.site.unix_name}, "
                f"page: {self.page.fullname}, revision: {self.id}"
            )
        return self._html

    @html.setter
    def html(self, value: str) -> None:
        """
        Set the revision's HTML display

        Parameters
        ----------
        value : str
            The HTML display to set
        """
        self._html = _validate_revision_html(value)
