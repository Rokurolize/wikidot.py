"""
Module for handling Wikidot forum categories

This module provides classes and functionality related to Wikidot forum categories.
It enables operations such as retrieving category information and thread lists.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, cast
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from ..common.exceptions import NoElementException, UnexpectedException, WikidotStatusCodeException
from ..util.parser.html import class_values
from ._validation import validate_text_field
from .forum_thread import ForumThread, ForumThreadCollection

if TYPE_CHECKING:
    from .client import Client
    from .site import Site


def _site_name(site: "Site") -> str:
    site_unix_name = getattr(site, "unix_name", None)
    return site_unix_name if isinstance(site_unix_name, str) else str(site)


def _category_parse_context(site: "Site", row_index: int, **details: object) -> str:
    context = [f"row={row_index}"]
    context.extend(f"{name}={value}" for name, value in details.items())
    return f"for site: {_site_name(site)} ({', '.join(context)})"


def _parse_category_count(site: "Site", row_index: int, field: str, label: str, value: str) -> int:
    if re.fullmatch(r"-?[0-9]+", value) is None:
        parse_context = _category_parse_context(site, row_index, field=field, value=value)
        raise NoElementException(f"{label} is malformed {parse_context}")
    count = int(value)
    if count < 0:
        parse_context = _category_parse_context(site, row_index, field=field, value=value)
        raise NoElementException(f"{label} must be non-negative {parse_context}")
    return count


def _parse_category_id(site: "Site", row_index: int, href: object) -> int:
    href_text = str(href)
    category_id_candidate = re.search(r"(?:^|/)c-\d+", href_text)
    href_parts = urlsplit(href_text)
    href_host = href_parts.hostname.lower() if href_parts.hostname is not None else None
    site_domain = getattr(site, "domain", None)
    site_host = site_domain.lower() if isinstance(site_domain, str) else None
    if category_id_candidate is not None and (
        href_parts.scheme not in ("", "http", "https")
        or (href_parts.scheme in ("http", "https") and href_parts.netloc == "")
        or (href_parts.netloc != "" and href_host != site_host)
    ):
        parse_context = _category_parse_context(site, row_index, field="id", value=href_text)
        raise NoElementException(f"Category ID is malformed {parse_context}")

    category_id_match = re.search(r"(?:^|/)c-([0-9]+)(?=[/?#]|$)", href_parts.path)
    if category_id_match is not None:
        return int(category_id_match.group(1))

    if category_id_candidate is not None:
        parse_context = _category_parse_context(site, row_index, field="id", value=href_text)
        raise NoElementException(f"Category ID is malformed {parse_context}")

    parse_context = _category_parse_context(site, row_index)
    raise NoElementException(f"Category ID is not found {parse_context}")


def _require_forum_category_action_status(category: "ForumCategory", event: str, data: dict[str, Any]) -> Any:
    try:
        status = data["status"]
    except KeyError as exc:
        raise NoElementException(
            f"Forum category action response is malformed for site: {category.site.unix_name}, "
            f"category: {category.id} (event={event}, field=status)"
        ) from exc
    if not isinstance(status, str):
        raise NoElementException(
            f"Forum category action response is malformed for site: {category.site.unix_name}, "
            f"category: {category.id} (event={event}, field=status, expected=str, "
            f"actual={type(status).__name__})"
        )

    if status != "ok":
        raise WikidotStatusCodeException(
            f"Failed to complete forum category action for site: {category.site.unix_name}, "
            f"category: {category.id}, event: {event}",
            status,
        )
    return status


def _require_forum_category_action_response_count(
    category: "ForumCategory",
    event: str,
    responses: tuple[object, ...],
    expected_count: int,
) -> None:
    actual_count = len(responses)
    if actual_count != expected_count:
        raise UnexpectedException(
            f"Forum category action response count mismatch for site: {category.site.unix_name}, "
            f"category: {category.id}, event: {event}, expected: {expected_count}, actual: {actual_count}"
        )


def _validate_forum_category_collection_categories(categories: object) -> list["ForumCategory"]:
    if categories is None:
        return []
    if not isinstance(categories, list):
        raise ValueError("categories must be a list or None")
    if any(not isinstance(category, ForumCategory) for category in categories):
        raise ValueError("categories list entries must be ForumCategory")
    return cast(list["ForumCategory"], categories)


def _validate_categories_belong_to_site(site: "Site", categories: list["ForumCategory"]) -> None:
    if any(category.site is not site for category in categories):
        raise ValueError("categories must belong to the collection site")


def _validate_forum_category(category: object) -> "ForumCategory":
    if not isinstance(category, ForumCategory):
        raise ValueError("category must be a ForumCategory")
    return category


def _validate_forum_category_site(site: object) -> "Site":
    from .site import Site

    if not isinstance(site, Site):
        raise ValueError("site must be a Site")
    return site


def _validate_forum_category_site_client(site: "Site") -> "Client":
    from .client import Client

    if not isinstance(site.client, Client):
        raise ValueError("client must be a Client")
    return site.client


def _validate_forum_category_threads(value: object) -> ForumThreadCollection:
    if not isinstance(value, ForumThreadCollection):
        raise ValueError("category.threads must be ForumThreadCollection")
    if any(not isinstance(thread, ForumThread) for thread in value):
        raise ValueError("category.threads list entries must be ForumThread")
    return value


def _validate_optional_forum_category_threads(value: object) -> ForumThreadCollection | None:
    if value is None:
        return None
    if not isinstance(value, ForumThreadCollection):
        raise ValueError("category.threads must be ForumThreadCollection or None")
    if any(not isinstance(thread, ForumThread) for thread in value):
        raise ValueError("category.threads list entries must be ForumThread")
    return value


def _validate_threads_cache_site_matches(category_site: "Site", candidate_site: object) -> None:
    threads_site = _validate_forum_category_site(candidate_site)
    if threads_site is not category_site:
        raise ValueError("category.threads must belong to the category")


def _validate_threads_cache_category_matches(
    category: "ForumCategory",
    category_site: "Site",
    candidate_category: object,
) -> None:
    thread_category = _validate_forum_category(candidate_category)
    category_id = _validate_forum_category_id(category.id)
    thread_category_site = _validate_forum_category_site(thread_category.site)
    thread_category_id = _validate_forum_category_id(thread_category.id)
    if thread_category_id != category_id or thread_category_site is not category_site:
        raise ValueError("category.threads must belong to the category")


def _validate_threads_cache_belongs_to_category(
    category: "ForumCategory",
    threads: ForumThreadCollection,
) -> None:
    category_site = _validate_forum_category_site(category.site)
    if threads.site is not None:
        _validate_threads_cache_site_matches(category_site, threads.site)
    for thread in threads:
        _validate_threads_cache_site_matches(category_site, thread.site)
        if thread.category is not None:
            _validate_threads_cache_category_matches(category, category_site, thread.category)


def _validate_forum_category_id(category_id: object) -> int:
    if not isinstance(category_id, int) or isinstance(category_id, bool):
        raise ValueError("id must be an integer")
    if category_id < 0:
        raise ValueError("id must be non-negative")
    return category_id


def _validate_forum_category_count(field_name: str, count: object) -> int:
    if not isinstance(count, int) or isinstance(count, bool):
        raise ValueError(f"{field_name} must be an integer")
    if count < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return count


class ForumCategoryCollection(list["ForumCategory"]):
    """
    Class representing a collection of forum categories

    A list extension class for storing multiple forum categories and performing batch operations.
    """

    site: "Site | None"

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
        categories = _validate_forum_category_collection_categories(categories)

        if site is not None:
            site = _validate_forum_category_site(site)
            _validate_categories_belong_to_site(site, categories)
            self.site = site
        elif len(categories) > 0:
            site = categories[0].site
            _validate_categories_belong_to_site(site, categories)
            self.site = site
        else:
            self.site = None

        super().__init__(categories)

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
        id = _validate_forum_category_id(id)

        for category in self:
            if _validate_forum_category_id(category.id) == id:
                return category
        return None

    @staticmethod
    def _category_list_response_body(response: Any, site: "Site") -> str:
        data = response.json()
        if not isinstance(data, dict):
            raise NoElementException(
                "Forum category list response payload is malformed "
                f"for site: {_site_name(site)} (expected=dict, actual={type(data).__name__})"
            )

        body = data.get("body")
        if body is None:
            raise NoElementException(f"Forum category list response body is not found for site: {_site_name(site)}")
        if not isinstance(body, str):
            raise NoElementException(
                "Forum category list response body is malformed "
                f"for site: {_site_name(site)} (field=body, expected=str, actual={type(body).__name__})"
            )
        return body

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
        site = _validate_forum_category_site(site)
        categories = []

        response = site.amc_request_with_retry([{"moduleName": "forum/ForumStartModule", "hidden": "true"}])[0]
        if response is None:
            raise UnexpectedException(f"Cannot retrieve forum categories for site: {site.unix_name}")

        body = ForumCategoryCollection._category_list_response_body(response, site)
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
                if "name" not in class_values(name_elem):
                    raise NoElementException(f"Name element is not found {parse_context}")
                thread_count_elem = cells[1]
                if "threads" not in class_values(thread_count_elem):
                    raise NoElementException(f"Thread count element is not found {parse_context}")
                post_count_elem = cells[2]
                if "posts" not in class_values(post_count_elem):
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
                category_id = _parse_category_id(site, row_index, name_link_href)
                description_elem = name_elem.find("div", class_="description", recursive=False)
                if description_elem is None:
                    raise NoElementException(f"Description element is not found {parse_context}")
                threads_count = _parse_category_count(
                    site,
                    row_index,
                    "threads",
                    "Thread count",
                    thread_count_elem.get_text("", strip=True),
                )
                posts_count = _parse_category_count(
                    site,
                    row_index,
                    "posts",
                    "Post count",
                    post_count_elem.get_text("", strip=True),
                )

                category = ForumCategory(
                    site=site,
                    id=category_id,
                    title=name_link_elem.get_text(" ", strip=True),
                    description=description_elem.get_text(" ", strip=True),
                    threads_count=threads_count,
                    posts_count=posts_count,
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

    def __post_init__(self) -> None:
        self.site = _validate_forum_category_site(self.site)
        self.id = _validate_forum_category_id(self.id)
        self.title = validate_text_field("title", self.title)
        self.description = validate_text_field("description", self.description)
        self.threads_count = _validate_forum_category_count("threads_count", self.threads_count)
        self.posts_count = _validate_forum_category_count("posts_count", self.posts_count)
        self._threads = _validate_optional_forum_category_threads(self._threads)
        if self._threads is not None:
            _validate_threads_cache_belongs_to_category(self, self._threads)

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
        threads = _validate_forum_category_threads(value)
        _validate_threads_cache_belongs_to_category(self, threads)
        self._threads = threads

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
        title = validate_text_field("title", title)
        description = validate_text_field("description", description)
        source = validate_text_field("source", source)
        site = _validate_forum_category_site(self.site)
        category_id = _validate_forum_category_id(self.id)
        client = _validate_forum_category_site_client(site)
        client.login_check()

        # 作成リクエスト
        responses = site.amc_request(
            [
                {
                    "moduleName": "Empty",
                    "action": "ForumAction",
                    "event": "newThread",
                    "category_id": category_id,
                    "title": title,
                    "description": description,
                    "source": source,
                }
            ]
        )
        _require_forum_category_action_response_count(self, "newThread", responses, 1)
        response = responses[0].json()

        if not isinstance(response, dict):
            raise NoElementException(
                f"Forum category action response is malformed for site: {site.unix_name}, "
                f"category: {category_id} (event=newThread, expected=dict, actual={type(response).__name__})"
            )

        _require_forum_category_action_status(self, "newThread", response)

        # responseからthreadIdを取得
        thread_id = response.get("threadId")
        if not isinstance(thread_id, int) or isinstance(thread_id, bool):
            raise NoElementException(f"Thread ID is not found for site: {site.unix_name}, category: {category_id}")
        if thread_id < 0:
            raise NoElementException(
                f"Thread ID must be non-negative for site: {site.unix_name}, category: {category_id}"
            )

        self._threads = None

        return ForumThread.get_from_id(site, thread_id, self)
