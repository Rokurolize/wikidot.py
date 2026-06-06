"""
Module for handling Wikidot forum threads

This module provides classes and functionality related to Wikidot forum threads.
It enables operations such as retrieving thread information and viewing.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, cast

from bs4 import BeautifulSoup, NavigableString, Tag

from ..common.exceptions import NoElementException, UnexpectedException, WikidotStatusCodeException
from ..util.parser import odate as odate_parser
from ..util.parser import user as user_parser
from ._validation import validate_text_field

if TYPE_CHECKING:
    from .forum_category import ForumCategory
    from .forum_post import ForumPostCollection
    from .site import Site
    from .user import AbstractUser


def _site_name(site: "Site") -> str:
    site_unix_name = getattr(site, "unix_name", None)
    return site_unix_name if isinstance(site_unix_name, str) else str(site)


def _validate_thread_id(thread_id: object) -> int:
    if not isinstance(thread_id, int) or isinstance(thread_id, bool):
        raise ValueError("thread_id must be an integer")
    return thread_id


def _validate_thread_created_by(created_by: object) -> "AbstractUser":
    from .user import AbstractUser

    if not isinstance(created_by, AbstractUser):
        raise ValueError("created_by must be an AbstractUser")
    return created_by


def _validate_thread_created_at(created_at: object) -> datetime:
    if not isinstance(created_at, datetime):
        raise ValueError("created_at must be a datetime")
    return created_at


def _validate_thread_post_count(post_count: object) -> int:
    if not isinstance(post_count, int) or isinstance(post_count, bool):
        raise ValueError("post_count must be an integer")
    return post_count


def _validate_thread_ids(thread_ids: object) -> list[int]:
    if not isinstance(thread_ids, list):
        raise ValueError("thread_ids must be a list")
    if any(not isinstance(thread_id, int) or isinstance(thread_id, bool) for thread_id in thread_ids):
        raise ValueError("thread_ids list entries must be integers")
    return cast(list[int], thread_ids)


def _validate_forum_thread_collection_threads(threads: object) -> list["ForumThread"]:
    if threads is None:
        return []
    if not isinstance(threads, list):
        raise ValueError("threads must be a list or None")
    if any(not isinstance(thread, ForumThread) for thread in threads):
        raise ValueError("threads list entries must be ForumThread")
    return cast(list["ForumThread"], threads)


def _validate_optional_forum_category(category: object) -> Optional["ForumCategory"]:
    if category is None:
        return None
    from .forum_category import ForumCategory

    if not isinstance(category, ForumCategory):
        raise ValueError("category must be a ForumCategory or None")
    return category


def _validate_optional_post_id(field: str, post_id: object) -> int | None:
    if post_id is None:
        return None
    if not isinstance(post_id, int) or isinstance(post_id, bool):
        raise ValueError(f"{field} must be an integer or None")
    return post_id


def _thread_list_parse_context(
    site: "Site",
    category: Optional["ForumCategory"],
    row_index: int,
    page: int | None = None,
    **details: object,
) -> str:
    context = []
    if category is not None:
        context.append(f"category={category.id}")
    if page is not None:
        context.append(f"page={page}")
    context.append(f"row={row_index}")
    context.extend(f"{name}={value}" for name, value in details.items())
    return f"for site: {_site_name(site)} ({', '.join(context)})"


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


def _parse_thread_list_count(
    site: "Site", category: Optional["ForumCategory"], row_index: int, page: int | None, value: str
) -> int:
    try:
        return int(value)
    except ValueError as exc:
        parse_context = _thread_list_parse_context(site, category, row_index, page, field="posts", value=value)
        raise NoElementException(f"Posts count is malformed {parse_context}") from exc


def _parse_thread_list_user(
    site: "Site",
    category: Optional["ForumCategory"],
    row_index: int,
    page: int | None,
    user_elem: Tag,
) -> "AbstractUser":
    try:
        return user_parser(site.client, user_elem)
    except ValueError as exc:
        parse_context = _thread_list_parse_context(
            site,
            category,
            row_index,
            page,
            field="created_by",
            value=_user_onclick_value(user_elem),
        )
        raise NoElementException(f"Forum thread list user is malformed {parse_context}") from exc


def _parse_thread_list_created_at(
    site: "Site",
    category: Optional["ForumCategory"],
    row_index: int,
    page: int | None,
    odate_elem: Tag,
) -> datetime:
    try:
        return odate_parser(odate_elem)
    except ValueError as exc:
        parse_context = _thread_list_parse_context(
            site,
            category,
            row_index,
            page,
            field="created_at",
            value=_odate_class_value(odate_elem),
        )
        raise NoElementException(f"Forum thread list created_at is malformed {parse_context}") from exc


def _thread_detail_parse_context(
    site: "Site", thread_id: int | None = None, category: Optional["ForumCategory"] = None, **details: object
) -> str:
    context = []
    if thread_id is not None:
        context.append(f"thread={thread_id}")
    if category is not None:
        context.append(f"category={category.id}")
    context.extend(f"{name}={value}" for name, value in details.items())
    if context:
        return f"for site: {_site_name(site)} ({', '.join(context)})"
    return f"for site: {_site_name(site)}"


def _parse_thread_detail_post_count(
    site: "Site", thread_id: int | None, category: Optional["ForumCategory"], value: object
) -> int:
    value_text = str(value).strip()
    post_count_match = re.search(r"(\d+)", value_text)
    if post_count_match is None:
        parse_context = _thread_detail_parse_context(site, thread_id, category, field="posts", value=value_text)
        raise NoElementException(f"Post count is malformed {parse_context}")
    return int(post_count_match.group(1))


def _parse_thread_detail_thread_id(
    site: "Site", thread_id: int | None, category: Optional["ForumCategory"], value: object
) -> int:
    value_text = str(value).strip()
    if re.fullmatch(r"\d+", value_text) is None:
        parse_context = _thread_detail_parse_context(site, thread_id, category, field="thread_id", value=value_text)
        raise NoElementException(f"Forum thread detail ID is malformed {parse_context}")
    return int(value_text)


def _parse_thread_detail_user(
    site: "Site",
    thread_id: int | None,
    category: Optional["ForumCategory"],
    user_elem: Tag,
) -> "AbstractUser":
    try:
        return user_parser(site.client, user_elem)
    except ValueError as exc:
        parse_context = _thread_detail_parse_context(
            site,
            thread_id,
            category,
            field="created_by",
            value=_user_onclick_value(user_elem),
        )
        raise NoElementException(f"Forum thread detail user is malformed {parse_context}") from exc


def _parse_thread_detail_created_at(
    site: "Site",
    thread_id: int | None,
    category: Optional["ForumCategory"],
    odate_elem: Tag,
) -> datetime:
    try:
        return odate_parser(odate_elem)
    except ValueError as exc:
        parse_context = _thread_detail_parse_context(
            site,
            thread_id,
            category,
            field="created_at",
            value=_odate_class_value(odate_elem),
        )
        raise NoElementException(f"Forum thread detail created_at is malformed {parse_context}") from exc


def _require_forum_thread_action_status(thread: "ForumThread", event: str, data: dict[str, Any]) -> Any:
    try:
        status = data["status"]
    except KeyError as exc:
        raise NoElementException(
            f"Forum thread action response is malformed for site: {thread.site.unix_name}, thread: {thread.id} "
            f"(event={event}, field=status)"
        ) from exc

    if status != "ok":
        raise WikidotStatusCodeException(
            f"Failed to complete forum thread action for site: {thread.site.unix_name}, thread: {thread.id}, "
            f"event: {event}",
            status,
        )
    return status


class ForumThreadCollection(list["ForumThread"]):
    """
    Class representing a collection of forum threads

    A list extension class for storing multiple forum threads and performing batch operations.
    Provides functionality such as retrieving thread lists within specific categories。
    """

    site: "Site"

    def __init__(
        self,
        site: Optional["Site"] = None,
        threads: list["ForumThread"] | None = None,
    ):
        """
        Initialization method

        Parameters
        ----------
        site : Site | None, default None
            The site the threads belong to。If None, inferred from the first thread
        threads : list[ForumThread] | None, default None
            List of threads to store
        """
        super().__init__(_validate_forum_thread_collection_threads(threads))

        if site is not None:
            self.site = site
        else:
            self.site = self[0].site

    def __iter__(self) -> Iterator["ForumThread"]:
        """
        Iterator that returns threads in the collection sequentially

        Returns
        -------
        Iterator[ForumThread]
            Iterator of thread objects
        """
        return super().__iter__()

    def find(self, id: int) -> Optional["ForumThread"]:
        """
        Retrieve a thread with the specified ID

        Parameters
        ----------
        id : int
            Thread ID to retrieve

        Returns
        -------
        ForumThread | None
            Thread with the specified ID, or None if it does not exist
        """
        if not isinstance(id, int) or isinstance(id, bool):
            raise ValueError("id must be an integer")
        for thread in self:
            if thread.id == id:
                return thread
        return None

    @staticmethod
    def _pager_from_html(html: BeautifulSoup) -> Tag | None:
        for pager in html.select("div.pager"):
            if ForumThreadCollection._is_inside_thread_description(pager):
                continue
            return pager
        return None

    @staticmethod
    def _is_inside_thread_description(element: Tag) -> bool:
        for ancestor in element.parents:
            if not isinstance(ancestor, Tag):
                continue
            ancestor_classes = ancestor.get("class")
            if not (isinstance(ancestor_classes, list) and "description" in ancestor_classes):
                continue

            parent = ancestor.parent
            if not isinstance(parent, Tag):
                continue
            parent_classes = parent.get("class")
            if parent.name == "td" and isinstance(parent_classes, list) and "name" in parent_classes:
                return True
        return False

    @staticmethod
    def _description_text_from_block(description_block_elem: Tag, statistics_elem: Tag) -> str:
        chunks: list[str] = []

        for child in description_block_elem.children:
            if child is statistics_elem:
                continue

            if isinstance(child, NavigableString):
                text = child.strip()
            elif isinstance(child, Tag):
                text = child.get_text(" ", strip=True)
            else:
                continue

            if text:
                chunks.append(text)

        return " ".join(chunks)

    @staticmethod
    def _thread_title_from_breadcrumbs(bc_elem: Tag) -> str:
        for child in reversed(list(bc_elem.children)):
            if not isinstance(child, NavigableString):
                continue
            text = child.strip()
            if not text:
                continue
            title = text.removeprefix("»").strip()
            if title:
                return title
        return bc_elem.get_text(" ", strip=True).split("»")[-1].strip()

    @staticmethod
    def _parse_list_in_category(
        site: "Site", html: BeautifulSoup, category: Optional["ForumCategory"] = None, page: int | None = None
    ) -> "ForumThreadCollection":
        """
        Internal method to extract thread information from forum page HTML

        Extracts information such as thread title, description, author, creation date from HTML
        and generates a list of ForumThread objects。

        Parameters
        ----------
        site : Site
            The site the threads belong to
        html : BeautifulSoup
            HTML to parse
        category : ForumCategory | None, default None
            Category the thread belongs to (optional)

        Returns
        -------
        list[ForumThread]
            List of extracted thread objects

        Raises
        ------
        NoElementException
            If required HTML elements are not found
        """
        threads = []
        for table in html.select("div.forum-category-box > table.table"):
            rows = table.find_all("tr", recursive=False)
            row_index = 0
            for info in rows:
                row_class = info.get("class")
                if isinstance(row_class, list) and "head" in row_class:
                    continue

                cells = info.find_all("td", recursive=False)
                if len(cells) < 3:
                    continue

                row_index += 1
                parse_context = _thread_list_parse_context(site, category, row_index, page, cells=len(cells))
                name_elem = cells[0]
                started_elem = cells[1]
                posts_count_elem = cells[2]

                name_class = name_elem.get("class")
                started_class = started_elem.get("class")
                posts_count_class = posts_count_elem.get("class")
                if not (isinstance(name_class, list) and "name" in name_class):
                    raise NoElementException(f"Thread name element is not found {parse_context}")
                if not (isinstance(started_class, list) and "started" in started_class):
                    raise NoElementException(f"Thread started element is not found {parse_context}")
                if not (isinstance(posts_count_class, list) and "posts" in posts_count_class):
                    raise NoElementException(f"Posts count element is not found {parse_context}")

                title = name_elem.select_one(":scope > div.title > a")
                if title is None:
                    raise NoElementException(f"Title element is not found {parse_context}")

                title_href = title.get("href")
                if title_href is None:
                    raise NoElementException(f"Title href is not found {parse_context}")

                thread_id_match = re.search(r"t-(\d+)", str(title_href))
                if thread_id_match is None:
                    raise NoElementException(f"Thread ID is not found {parse_context}")

                thread_id = int(thread_id_match.group(1))

                description_elem = name_elem.select_one(":scope > div.description")
                user_elem = started_elem.select_one(":scope > span.printuser")
                odate_elem = started_elem.select_one(":scope > span.odate")

                if description_elem is None:
                    raise NoElementException(f"Description element is not found {parse_context}")
                if user_elem is None:
                    raise NoElementException(f"User element is not found {parse_context}")
                if odate_elem is None:
                    raise NoElementException(f"Odate element is not found {parse_context}")
                post_count = _parse_thread_list_count(
                    site,
                    category,
                    row_index,
                    page,
                    posts_count_elem.get_text("", strip=True),
                )

                thread = ForumThread(
                    site=site,
                    id=int(thread_id),
                    title=title.get_text(" ", strip=True),
                    description=description_elem.get_text(" ", strip=True),
                    created_by=_parse_thread_list_user(site, category, row_index, page, user_elem),
                    created_at=_parse_thread_list_created_at(site, category, row_index, page, odate_elem),
                    post_count=post_count,
                    category=category,
                )

                threads.append(thread)

        return ForumThreadCollection(site=site, threads=threads)

    @staticmethod
    def _parse_thread_page(
        site: "Site",
        html: BeautifulSoup,
        category: Optional["ForumCategory"] = None,
        thread_id: int | None = None,
    ) -> "ForumThread":
        """
        Internal method to extract thread information from thread page HTML

        Extracts information such as thread title, description, author, creation date from HTML,
        and generates a ForumThread object.

        Parameters
        ----------
        site : Site
            The site the threads belong to
        html : BeautifulSoup
            HTML to parse
        category : ForumCategory | None, default None
            Category the thread belongs to (optional)

        Returns
        -------
        ForumThread
            Extracted thread object

        Raises
        ------
        NoElementException
            If required HTML elements are not found
        """
        parse_context = _thread_detail_parse_context(site, thread_id, category)

        # title取得処理
        # forum-breadcrumbsの最後のNavigableStringを取得
        bc_elem = html.select_one("div.forum-breadcrumbs")
        if bc_elem is None:
            raise NoElementException(f"Breadcrumbs element is not found {parse_context}")
        title = ForumThreadCollection._thread_title_from_breadcrumbs(bc_elem)
        if not title:
            raise NoElementException(f"Thread title is not found {parse_context}")

        # description取得処理
        description_block_elem = html.select_one("div.description-block")
        if description_block_elem is None:
            raise NoElementException(f"Description block element is not found {parse_context}")
        statistics_elems = description_block_elem.find_all("div", class_="statistics", recursive=False)
        if not statistics_elems:
            raise NoElementException(f"Statistics element is not found {parse_context}")
        statistics_elem = statistics_elems[-1]
        description = ForumThreadCollection._description_text_from_block(description_block_elem, statistics_elem)

        # created_by取得処理
        user_elem = statistics_elem.find("span", class_="printuser", recursive=False)
        if user_elem is None:
            raise NoElementException(f"User element is not found {parse_context}")
        created_by = _parse_thread_detail_user(site, thread_id, category, user_elem)

        # created_at取得処理
        odate_elem = statistics_elem.find("span", class_="odate", recursive=False)
        if odate_elem is None:
            raise NoElementException(f"Odate element is not found {parse_context}")
        created_at = _parse_thread_detail_created_at(site, thread_id, category, odate_elem)

        # post_count取得処理
        # 3番目のbrの前のテキスト
        br_tags = statistics_elem.find_all("br", recursive=False)
        if len(br_tags) < 3:
            raise NoElementException(f"Br tags are not enough {parse_context}")
        post_count_elem = br_tags[2].previous_sibling
        if post_count_elem is None:
            raise NoElementException(f"Posts count element is not found {parse_context}")
        post_count_text = str(post_count_elem)
        post_count = _parse_thread_detail_post_count(site, thread_id, category, post_count_text)

        # id取得処理
        # WIKIDOT.forumThreadId = xxxxxx;を全体から検索
        thread_id_pattern = re.compile(r"WIKIDOT\.forumThreadId\s*=\s*([^;]*);")
        thread_id_match = None
        for script in html.find_all("script"):
            if script.string is None:
                continue
            thread_id_match = thread_id_pattern.search(str(script.string))
            if thread_id_match is not None:
                break
        if thread_id_match is None:
            raise NoElementException(f"Script element is not found {parse_context}")
        parsed_thread_id = _parse_thread_detail_thread_id(site, thread_id, category, thread_id_match.group(1))

        return ForumThread(
            site=site,
            id=parsed_thread_id,
            title=title,
            description=description,
            created_by=created_by,
            created_at=created_at,
            post_count=post_count,
            category=category,
        )

    @staticmethod
    def acquire_all_in_category(category: "ForumCategory") -> "ForumThreadCollection":
        """
        Retrieve all threads within a specific category

        Accesses each page of the category page and collects all thread information。
        Traverses all pages if pagination exists。

        Parameters
        ----------
        category : ForumCategory
            Category to retrieve threads from

        Returns
        -------
        ForumThreadCollection
            Collection containing all threads in the category

        Raises
        ------
        NoElementException
            If HTML element parsing fails
        """
        if category._threads is not None:
            return category._threads

        threads: list[ForumThread] = []

        def cache_threads() -> ForumThreadCollection:
            collection = ForumThreadCollection(site=category.site, threads=threads)
            category._threads = collection
            return collection

        first_response = category.site.amc_request_with_retry(
            [
                {
                    "p": 1,
                    "c": category.id,
                    "moduleName": "forum/ForumViewCategoryModule",
                }
            ]
        )[0]
        if first_response is None:
            raise UnexpectedException(
                f"Cannot retrieve forum threads for site: {category.site.unix_name}, category: {category.id}, page: 1"
            )

        first_body = ForumThreadCollection._thread_list_response_body(first_response, category, 1)
        first_html = BeautifulSoup(first_body, "lxml")

        threads.extend(ForumThreadCollection._parse_list_in_category(category.site, first_html, category, page=1))

        # pager検索
        pager = ForumThreadCollection._pager_from_html(first_html)
        if pager is None:
            return cache_threads()

        last_page = 1
        for link in reversed(pager.select("a")):
            page_text = link.get_text(strip=True)
            if page_text.isdigit():
                last_page = int(page_text)
                break
        if last_page == 1:
            return cache_threads()

        page_numbers = list(range(2, last_page + 1))
        responses = category.site.amc_request_with_retry(
            [
                {
                    "p": page,
                    "c": category.id,
                    "moduleName": "forum/ForumViewCategoryModule",
                }
                for page in page_numbers
            ]
        )

        for page, response in zip(page_numbers, responses, strict=True):
            if response is None:
                raise UnexpectedException(
                    f"Cannot retrieve forum threads for site: {category.site.unix_name}, category: {category.id}, page: {page}"
                )
            body = ForumThreadCollection._thread_list_response_body(response, category, page)
            html = BeautifulSoup(body, "lxml")
            threads.extend(ForumThreadCollection._parse_list_in_category(category.site, html, category, page=page))

        return cache_threads()

    @staticmethod
    def _thread_list_response_body(response: Any, category: "ForumCategory", page: int) -> str:
        body = response.json().get("body")
        if body is None:
            raise NoElementException(
                "Forum thread list response body is not found "
                f"for site: {category.site.unix_name}, category: {category.id}, page: {page}"
            )
        if not isinstance(body, str):
            raise NoElementException(
                "Forum thread list response body is malformed "
                f"for site: {category.site.unix_name}, category: {category.id}, page: {page} "
                f"(field=body, expected=str, actual={type(body).__name__})"
            )
        return body

    @staticmethod
    def acquire_from_thread_ids(
        site: "Site", thread_ids: list[int], category: Optional["ForumCategory"] = None
    ) -> "ForumThreadCollection":
        """
        Retrieve thread information for the specified thread IDs

        Retrieves thread information for the specified thread IDs and returns them as a collection.

        Parameters
        ----------
        site : Site
            The site the threads belong to
        thread_ids : list[int]
            List of thread IDs to retrieve
        category : ForumCategory | None, default None
            Category the thread belongs to (optional)

        Returns
        -------
        ForumThreadCollection
            Collection of retrieved thread information
        """
        thread_ids = _validate_thread_ids(thread_ids)
        if len(thread_ids) == 0:
            return ForumThreadCollection(site=site, threads=[])

        target_thread_ids = list(dict.fromkeys(thread_ids))
        responses = site.amc_request_with_retry(
            [
                {
                    "t": thread_id,
                    "moduleName": "forum/ForumViewThreadModule",
                }
                for thread_id in target_thread_ids
            ]
        )

        threads_by_id = {}

        for response, thread_id in zip(responses, target_thread_ids, strict=True):
            if response is None:
                raise UnexpectedException(
                    f"Cannot retrieve forum thread for site: {_site_name(site)}, thread: {thread_id}"
                )
            body = ForumThreadCollection._thread_detail_response_body(response, site, thread_id)
            html = BeautifulSoup(body, "lxml")

            thread = ForumThreadCollection._parse_thread_page(site, html, category, thread_id=thread_id)
            if thread_id != thread.id:
                raise NoElementException(
                    f"Thread ID is not matched for site: {_site_name(site)} "
                    f"(requested_thread={thread_id}, parsed_thread={thread.id})"
                )
            threads_by_id[thread_id] = thread

        threads = [threads_by_id[thread_id] for thread_id in thread_ids]

        return ForumThreadCollection(site=site, threads=threads)

    @staticmethod
    def _thread_detail_response_body(response: Any, site: "Site", thread_id: int) -> str:
        body = response.json().get("body")
        if body is None:
            raise NoElementException(
                f"Forum thread detail response body is not found for site: {_site_name(site)}, thread: {thread_id}"
            )
        if not isinstance(body, str):
            raise NoElementException(
                f"Forum thread detail response body is malformed for site: {_site_name(site)}, thread: {thread_id} "
                f"(field=body, expected=str, actual={type(body).__name__})"
            )
        return body


@dataclass
class ForumThread:
    """
    Class representing a Wikidot forum thread

    Holds basic forum thread information. Provides information such as thread title,
    description, author, creation date, and post count.

    Attributes
    ----------
    site : Site
        The site the thread belongs to
    id : int
        Thread ID
    title : str
        Thread title
    description : str
        Thread description or excerpt
    created_by : AbstractUser
        Thread creator
    created_at : datetime
        Thread creation date and time
    post_count : int
        Number of posts in the thread
    category : ForumCategory | None, default None
        Forum category the thread belongs to
    _posts : ForumPostCollection | None, default None
        Post collection in the thread (lazy loading)
    """

    site: "Site"
    id: int
    title: str
    description: str
    created_by: "AbstractUser"
    created_at: datetime
    post_count: int
    category: Optional["ForumCategory"] = None
    _posts: Optional["ForumPostCollection"] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self.id = _validate_thread_id(self.id)
        self.title = validate_text_field("title", self.title)
        self.description = validate_text_field("description", self.description)
        self.created_by = _validate_thread_created_by(self.created_by)
        self.created_at = _validate_thread_created_at(self.created_at)
        self.post_count = _validate_thread_post_count(self.post_count)
        self.category = _validate_optional_forum_category(self.category)

    def __str__(self) -> str:
        """
        String representation of the object

        Returns
        -------
        str
            String representation of the thread
        """
        return (
            f"ForumThread(id={self.id}, "
            f"title={self.title}, description={self.description}, "
            f"created_by={self.created_by}, created_at={self.created_at}, "
            f"post_count={self.post_count}), "
            f"category={self.category}"
        )

    @property
    def url(self) -> str:
        """
        Retrieve the thread URL

        Returns
        -------
        str
            Thread URL
        """
        return f"{self.site.url}/forum/t-{self.id}/"

    @property
    def posts(self) -> "ForumPostCollection":
        """
        Retrieve all posts in a thread

        Automatically retrieves if posts have not been fetched。

        Returns
        -------
        ForumPostCollection
            Collection containing all posts in the thread
        """
        if self._posts is None:
            from .forum_post import ForumPostCollection

            result = ForumPostCollection.acquire_all_in_threads([self])
            self._posts = result.get(self.id, ForumPostCollection(thread=self, posts=[]))
        return self._posts

    def reply(self, source: str, title: str = "", parent_post_id: int | None = None) -> "ForumThread":
        """
        Post a reply to the thread

        Adds a new post to the thread. If a parent post ID is specified,
        it is posted as a reply to that post。

        Parameters
        ----------
        source : str
            Post body (Wikidot syntax)
        title : str, default ""
            Post title
        parent_post_id : int | None, default None
            Post ID to reply to (None for direct replies to thread)

        Returns
        -------
        ForumThread
            Self (for method chaining)

        Raises
        ------
        LoginRequiredException
            If not logged in
        WikidotStatusCodeException
            If posting fails
        """
        source = validate_text_field("source", source)
        title = validate_text_field("title", title)
        parent_post_id = _validate_optional_post_id("parent_post_id", parent_post_id)
        self.site.client.login_check()
        response = self.site.amc_request(
            [
                {
                    "threadId": str(self.id),
                    "parentId": str(parent_post_id) if parent_post_id is not None else "",
                    "title": title,
                    "source": source,
                    "action": "ForumAction",
                    "event": "savePost",
                    "moduleName": "Empty",
                }
            ]
        )[0]
        _require_forum_thread_action_status(self, "savePost", response.json())
        # キャッシュをクリアして次回アクセス時に再取得
        self._posts = None
        self.post_count += 1
        if self.category is not None:
            self.category.posts_count += 1
            self.category._threads = None
        return self

    @staticmethod
    def get_from_id(site: "Site", thread_id: int, category: Optional["ForumCategory"] = None) -> "ForumThread":
        """
        Retrieve thread information from thread ID

        Parameters
        ----------
        site : Site
            The site the thread belongs to
        thread_id : int
            Thread ID to retrieve
        category : ForumCategory | None, default None
            Category the thread belongs to (optional)

        Returns
        -------
        ForumThread
            Retrieved thread information
        """
        thread_id = _validate_thread_id(thread_id)
        return ForumThreadCollection.acquire_from_thread_ids(site, [thread_id], category)[0]
