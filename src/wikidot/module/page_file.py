"""
Module for handling Wikidot page file attachments

This module provides classes and functions related to files attached
to Wikidot site pages. It enables operations such as retrieving file information.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, cast
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from ..common import exceptions

if TYPE_CHECKING:
    from .page import Page


_SIZE_PATTERN = re.compile(r"\s*([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]+)\s*")
_SIZE_MULTIPLIERS = {
    "b": 1,
    "byte": 1,
    "bytes": 1,
    "kb": 1000,
    "mb": 1000000,
    "gb": 1000000000,
}


def _validate_files(files: object) -> list["PageFile"]:
    if files is None:
        return []
    if not isinstance(files, list):
        raise ValueError("files must be a list or None")
    if any(not isinstance(file, PageFile) for file in files):
        raise ValueError("files list entries must be PageFile")
    return cast(list["PageFile"], files)


def _validate_file_page(value: object) -> "Page":
    from .page import Page

    if not isinstance(value, Page):
        raise ValueError("page must be a Page")
    return value


def _validate_file_id(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("id must be an integer")
    return value


def _validate_file_text(field: str, value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def _validate_file_size(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("size must be an integer")
    return value


class PageFileCollection(list["PageFile"]):
    """
    Class representing a collection of page files

    A list extension class for storing and operating on multiple files
    attached to a page in bulk.
    """

    page: "Page"

    def __init__(
        self,
        page: Optional["Page"] = None,
        files: list["PageFile"] | None = None,
    ):
        """
        Initialize the collection

        Parameters
        ----------
        page : Page | None, default None
            The page the files belong to. If None, inferred from the first file
        files : list[PageFile] | None, default None
            List of files to store
        """
        super().__init__(_validate_files(files))

        if page is not None:
            self.page = page
        elif len(self) > 0:
            self.page = self[0].page

    def __iter__(self) -> Iterator["PageFile"]:
        """
        Return an iterator over the files in the collection

        Returns
        -------
        Iterator[PageFile]
            Iterator of file objects
        """
        return super().__iter__()

    def find(self, id: int) -> Optional["PageFile"]:
        """
        Get the file with the specified ID

        Parameters
        ----------
        id : int
            The ID of the file to retrieve

        Returns
        -------
        PageFile | None
            The file with the specified ID, or None if not found
        """
        if not isinstance(id, int) or isinstance(id, bool):
            raise ValueError("id must be an integer")
        for file in self:
            if file.id == id:
                return file
        return None

    def find_by_name(self, name: str) -> Optional["PageFile"]:
        """
        Get the file with the specified name

        Parameters
        ----------
        name : str
            The name of the file to retrieve

        Returns
        -------
        PageFile | None
            The file with the specified name, or None if not found
        """
        if not isinstance(name, str):
            raise ValueError("name must be a string")
        for file in self:
            if file.name == name:
                return file
        return None

    @staticmethod
    def _parse_size(size_text: str) -> int:
        """
        Convert file size string to bytes

        Parameters
        ----------
        size_text : str
            Size string (e.g., "1.5 kB", "2 MB", "500 Bytes")

        Returns
        -------
        int
            Size in bytes
        """
        size = PageFileCollection._parse_size_value(size_text)
        return 0 if size is None else size

    @staticmethod
    def _parse_size_value(size_text: str) -> int | None:
        size_match = _SIZE_PATTERN.fullmatch(size_text)
        if size_match is None:
            return None

        value = float(size_match.group(1))
        unit = size_match.group(2).lower()
        multiplier = _SIZE_MULTIPLIERS.get(unit)
        if multiplier is None:
            return None
        return int(value * multiplier)

    @staticmethod
    def _parse_file_fields_from_html(
        site_url: str, html: BeautifulSoup, *, context: str = ""
    ) -> list[tuple[int, str, str, str, int]]:
        files_table = html.select_one("table.page-files")

        if not isinstance(files_table, Tag):
            return []
        files_tbody = files_table.find("tbody", recursive=False)
        if not isinstance(files_tbody, Tag):
            return []

        file_fields: list[tuple[int, str, str, str, int]] = []
        for row_index, row in enumerate(files_tbody.find_all("tr", recursive=False), start=1):
            row_id = row.get("id")
            if row_id is None:
                continue

            row_id_text = str(row_id)
            if not row_id_text.startswith("file-row-"):
                continue

            file_id_text = row_id_text.removeprefix("file-row-")
            if not file_id_text.isdigit():
                location = f"{context} " if context else ""
                raise exceptions.NoElementException(
                    f"Page file row ID is malformed {location}(row={row_index}, field=id, value={row_id_text})"
                )
            file_id = int(file_id_text)
            tds = [td for td in row.find_all("td", recursive=False) if isinstance(td, Tag)]
            if len(tds) < 3:
                continue

            link_elem = tds[0].find("a", recursive=False)
            if not isinstance(link_elem, Tag):
                continue

            name = link_elem.get_text(" ", strip=True)
            if name == "":
                location = f"{context} " if context else ""
                raise exceptions.NoElementException(f"Page file name is not found {location}(id={file_id}, field=name)")
            href = link_elem.get("href")
            if not isinstance(href, str) or href.strip() == "":
                location = f"{context}, file: {name}" if context else f"for file: {name}"
                raise exceptions.NoElementException(
                    f"Page file link href is not found {location} (id={file_id}, field=href)"
                )
            url = urljoin(f"{site_url}/", str(href))

            mime_elem = tds[1].find("span", recursive=False)
            mime_title = mime_elem.get("title") if isinstance(mime_elem, Tag) else None
            if mime_title is None:
                location = f"{context}, file: {name}" if context else f"for file: {name}"
                raise exceptions.NoElementException(
                    f"Page file MIME type title is not found {location} (id={file_id}, field=mime_type)"
                )
            mime_type = str(mime_title)

            size_text = tds[2].get_text().strip()
            if PageFileCollection._parse_size_value(size_text) is None:
                location = f"{context}, file: {name}" if context else f"for file: {name}"
                raise exceptions.NoElementException(
                    f"Page file size is malformed {location} (id={file_id}, field=size, value={size_text})"
                )
            size = PageFileCollection._parse_size(size_text)

            file_fields.append((file_id, name, url, mime_type, size))

        return file_fields

    @staticmethod
    def _build_page_files(page: "Page", file_fields: list[tuple[int, str, str, str, int]]) -> list["PageFile"]:
        return [
            PageFile(
                page=page,
                id=file_id,
                name=name,
                url=url,
                mime_type=mime_type,
                size=size,
            )
            for file_id, name, url, mime_type, size in file_fields
        ]

    @staticmethod
    def _parse_from_html(page: "Page", html: BeautifulSoup) -> list["PageFile"]:
        """
        Parse file information from HTML response

        Internal helper method used by acquire() and PageCollection._acquire_page_files().

        Parameters
        ----------
        page : Page
            The page the files belong to
        html : BeautifulSoup
            Parsed HTML response from files/PageFilesModule

        Returns
        -------
        list[PageFile]
            List of parsed PageFile objects
        """
        context = f"for site: {page.site.unix_name}, page: {page.fullname}"
        file_fields = PageFileCollection._parse_file_fields_from_html(page.site.url, html, context=context)
        return PageFileCollection._build_page_files(page, file_fields)

    @staticmethod
    def acquire(page: "Page") -> "PageFileCollection":
        """
        Get the list of files attached to a page

        Parameters
        ----------
        page : Page
            The page to retrieve files from

        Returns
        -------
        PageFileCollection
            Collection of files attached to the page
        """
        cached_files = getattr(page, "_files", None)
        if isinstance(cached_files, PageFileCollection):
            return cached_files

        response = page.site.amc_request_with_retry(
            [
                {
                    "moduleName": "files/PageFilesModule",
                    "page_id": page.id,
                }
            ]
        )[0]
        if response is None:
            raise exceptions.UnexpectedException(
                f"Cannot retrieve page files for site: {page.site.unix_name}, page: {page.fullname}"
            )

        body = response.json().get("body")
        if body is None:
            raise exceptions.NoElementException(
                f"Page file list response body is not found for site: {page.site.unix_name}, page: {page.fullname}"
            )
        if not isinstance(body, str):
            raise exceptions.NoElementException(
                "Page file list response body is malformed "
                f"for site: {page.site.unix_name}, page: {page.fullname} "
                f"(field=body, expected=str, actual={type(body).__name__})"
            )

        html = BeautifulSoup(body, "lxml")
        files = PageFileCollection._parse_from_html(page, html)
        collection = PageFileCollection(page=page, files=files)
        page._files = collection

        return collection


@dataclass
class PageFile:
    """
    Class representing a Wikidot page attachment file

    Holds information about an individual file attached to a page.

    Attributes
    ----------
    page : Page
        The page the file is attached to
    id : int
        File ID
    name : str
        File name
    url : str
        File download URL
    mime_type : str
        File MIME type
    size : int
        File size in bytes
    """

    page: "Page"
    id: int
    name: str
    url: str
    mime_type: str
    size: int

    def __post_init__(self) -> None:
        self.page = _validate_file_page(self.page)
        self.id = _validate_file_id(self.id)
        self.name = _validate_file_text("name", self.name)
        self.url = _validate_file_text("url", self.url)
        self.mime_type = _validate_file_text("mime_type", self.mime_type)
        self.size = _validate_file_size(self.size)

    def __str__(self) -> str:
        """
        String representation of the object

        Returns
        -------
        str
            String representation of the file
        """
        return f"PageFile(id={self.id}, name={self.name}, url={self.url}, mime_type={self.mime_type}, size={self.size})"
