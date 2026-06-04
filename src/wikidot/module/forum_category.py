"""
Module for handling Wikidot forum categories

This module provides classes and functionality related to Wikidot forum categories.
It enables operations such as retrieving category information and thread lists.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from bs4 import BeautifulSoup

from ..common.exceptions import NoElementException, UnexpectedException
from .forum_thread import ForumThread, ForumThreadCollection

if TYPE_CHECKING:
    from .site import Site


def _site_name(site: "Site") -> str:
    site_unix_name = getattr(site, "unix_name", None)
    return site_unix_name if isinstance(site_unix_name, str) else str(site)


def _category_parse_context(site: "Site", row_index: int, **counts: int) -> str:
    context = [f"row={row_index}"]
    context.extend(f"{name}={value}" for name, value in counts.items())
    return f"for site: {_site_name(site)} ({', '.join(context)})"


class ForumCategoryCollection(list["ForumCategory"]):
    """
    Class representing a collection of forum categories

    A list extension class for storing multiple forum categories and performing batch operations.
    """

    site: "Site"

    def __init__(
        self,
        site: Optional["Site"] = None,
        categories: list["ForumCategory"] | None = None,
    ):
        """
        Initialization method

        Parameters
        ----------
        site : Site | None, default None
            The site the categories belong to。If None, inferred from the first category
        categories : list[ForumCategory] | None, default None
            List of categories to store
        """
        super().__init__(categories or [])

        if site is not None:
            self.site = site
        else:
            self.site = self[0].site

    def __iter__(self) -> Iterator["ForumCategory"]:
        """
        Iterator that returns categories in the collection sequentially

        Returns
        -------
        Iterator[ForumCategory]
            Iterator of category objects
        """
        return super().__iter__()

    def find(self, id: int) -> Optional["ForumCategory"]:
        """
        Search for a category by category ID

        Returns the category object if a category with the specified ID exists。

        Parameters
        ----------
        id : int
            Category ID to search for

        Returns
        -------
        ForumCategory | None
            Category object if found, None otherwise
        """
        for category in self:
            if category.id == id:
                return category
        return None

    @staticmethod
    def acquire_all(site: "Site") -> "ForumCategoryCollection":
        """
        Retrieve all forum categories of a site

        Accesses the forum page of the specified site and retrieves
        information about all available categories。

        Parameters
        ----------
        site : Site
            The site to retrieve categories from

        Returns
        -------
        ForumCategoryCollection
            Collection of retrieved forum categories

        Raises
        ------
        NoElementException
            If required HTML elements are not found
        """
        categories = []

        response = site.amc_request_with_retry([{"moduleName": "forum/ForumStartModule", "hidden": "true"}])[0]
        if response is None:
            raise UnexpectedException(f"Cannot retrieve forum categories for site: {site.unix_name}")

        body = response.json()["body"]
        html = BeautifulSoup(body, "lxml")

        for table in html.select("div.forum-group > div:not(.head) > table"):
            row_index = 0
            for row in table.find_all("tr", recursive=False):
                row_class = row.get("class")
                if isinstance(row_class, list) and "head" in row_class:
                    continue

                row_index += 1
                parse_context = _category_parse_context(site, row_index)
                cells = row.find_all("td", recursive=False)
                if len(cells) < 3:
                    parse_context = _category_parse_context(site, row_index, cells=len(cells))
                    raise NoElementException(f"Category row is malformed {parse_context}")

                name_elem = cells[0]
                if "name" not in name_elem.get("class", []):
                    raise NoElementException(f"Name element is not found {parse_context}")
                thread_count_elem = cells[1]
                if "threads" not in thread_count_elem.get("class", []):
                    raise NoElementException(f"Thread count element is not found {parse_context}")
                post_count_elem = cells[2]
                if "posts" not in post_count_elem.get("class", []):
                    raise NoElementException(f"Post count element is not found {parse_context}")

                title_container = name_elem.find("div", class_="title", recursive=False)
                if title_container is None:
                    raise NoElementException(f"Title element is not found {parse_context}")
                name_link_elem = title_container.find("a", recursive=False)
                if name_link_elem is None:
                    raise NoElementException(f"Name link element is not found {parse_context}")
                name_link_href = name_link_elem.get("href")
                if name_link_href is None:
                    raise NoElementException(f"Name link href is not found {parse_context}")
                category_id_match = re.search(r"c-(\d+)", str(name_link_href))
                if category_id_match is None:
                    raise NoElementException(f"Category ID is not found {parse_context}")
                category_id_str = category_id_match.group(1)
                description_elem = name_elem.find("div", class_="description", recursive=False)
                if description_elem is None:
                    raise NoElementException(f"Description element is not found {parse_context}")

                category = ForumCategory(
                    site=site,
                    id=int(category_id_str),
                    title=name_link_elem.get_text(" ", strip=True),
                    description=description_elem.get_text(" ", strip=True),
                    threads_count=int(thread_count_elem.text),
                    posts_count=int(post_count_elem.text),
                )

                categories.append(category)

        return ForumCategoryCollection(site=site, categories=categories)


@dataclass
class ForumCategory:
    """
    Class representing a Wikidot forum category

    Provides basic forum category information and access to thread lists。

    Attributes
    ----------
    site : Site
        The site the categories belong to
    id : int
        Category ID
    title : str
        Category title
    description : str
        Category description
    threads_count : int
        Number of threads in the category
    posts_count : int
        Number of posts in the category
    _threads : ForumThreadCollection | None
        Thread collection in the category (for internal caching)
    """

    site: "Site"
    id: int
    title: str
    description: str
    threads_count: int
    posts_count: int
    _threads: ForumThreadCollection | None = None

    def __str__(self) -> str:
        """
        String representation of the object

        Returns
        -------
        str
            String representation of the category
        """
        return (
            f"ForumCategory(id={self.id}, "
            f"title={self.title}, description={self.description}, "
            f"threads_count={self.threads_count}, posts_count={self.posts_count})"
        )

    @property
    def threads(self) -> ForumThreadCollection:
        """
        Retrieve the list of threads in the category

        Automatically retrieves if the thread list has not been fetched。

        Returns
        -------
        ForumThreadCollection
            Thread collection in the category
        """
        if self._threads is None:
            self._threads = ForumThreadCollection.acquire_all_in_category(self)
        return self._threads

    @threads.setter
    def threads(self, value: ForumThreadCollection) -> None:
        """
        Set the list of threads in the category

        Parameters
        ----------
        value : ForumThreadCollection
            Thread collection to set
        """
        self._threads = value

    def reload_threads(self) -> ForumThreadCollection:
        """
        Re-retrieve the list of threads in the category

        Retrieves the latest thread list ignoring the cache。

        Returns
        -------
        ForumThreadCollection
            Latest thread collection
        """
        self._threads = None
        self._threads = ForumThreadCollection.acquire_all_in_category(self)
        return self._threads

    def create_thread(self, title: str, description: str, source: str) -> ForumThread:
        """
        Create a new thread in the category

        Parameters
        ----------
        title : str
            Thread title
        description : str
            Thread description
        source : str
            Thread body (Wikidot syntax)

        Returns
        -------
        ForumThread
            Created thread object
        """
        self.site.client.login_check()

        # 作成リクエスト
        response = self.site.amc_request(
            [
                {
                    "moduleName": "Empty",
                    "action": "ForumAction",
                    "event": "newThread",
                    "category_id": self.id,
                    "title": title,
                    "description": description,
                    "source": source,
                }
            ]
        )[0].json()

        # responseからthreadIdを取得
        if not isinstance(response.get("threadId"), int):
            raise NoElementException(f"Thread ID is not found for site: {self.site.unix_name}, category: {self.id}")

        thread_id: int = response["threadId"]

        return ForumThread.get_from_id(self.site, thread_id, self)
