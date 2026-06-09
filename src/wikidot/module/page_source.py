"""
Module for handling Wikidot page source code

This module provides classes and functions related to Wikidot page source code (Wikidot markup).
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .page import Page


def _validate_page_source_page(value: object) -> "Page":
    from .page import Page

    if not isinstance(value, Page):
        raise ValueError("page must be a Page")
    return value


@dataclass
class PageSource:
    """
    Class representing a page's source code (Wikidot markup)

    Holds the source code (Wikidot markup) of a Wikidot page and provides basic operations.
    Represents the source code of a page's current or specific revision.

    Attributes
    ----------
    page : Page
        The page this source code belongs to
    wiki_text : str
        The page's source code (Wikidot markup)
    """

    page: "Page"
    wiki_text: str

    def __post_init__(self) -> None:
        self.page = _validate_page_source_page(self.page)
        if not isinstance(self.wiki_text, str):
            raise ValueError("wiki_text must be a string")


def extract_page_source_text(source_element: Any) -> str:
    """
    Extract Wikidot markup from a page-source element.

    Wikidot wraps each displayed source line with one leading tab. Remove that
    wrapper tab per line while preserving the source text's own blank lines.
    """
    text = source_element.get_text().removeprefix("\n").removesuffix("\n")
    return "\n".join(line.removeprefix("\t") for line in text.split("\n"))
