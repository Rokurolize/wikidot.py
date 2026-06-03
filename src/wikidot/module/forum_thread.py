"""
Module for handling Wikidot forum threads

This module provides classes and functionality related to Wikidot forum threads.
It enables operations such as retrieving thread information and viewing.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from bs4 import BeautifulSoup, NavigableString, Tag

from ..common.exceptions import NoElementException, UnexpectedException
from ..util.parser import odate as odate_parser
from ..util.parser import user as user_parser

if TYPE_CHECKING:
    from .forum_category import ForumCategory
    from .forum_post import ForumPostCollection
    from .site import Site
    from .user import AbstractUser


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
        super().__init__(threads or [])

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
        site: "Site", html: BeautifulSoup, category: Optional["ForumCategory"] = None
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
            for info in rows:
                row_class = info.get("class")
                if isinstance(row_class, list) and "head" in row_class:
                    continue

                cells = info.find_all("td", recursive=False)
                if len(cells) < 3:
                    continue

                name_elem = cells[0]
                started_elem = cells[1]
                posts_count_elem = cells[2]

                name_class = name_elem.get("class")
                started_class = started_elem.get("class")
                posts_count_class = posts_count_elem.get("class")
                if not (isinstance(name_class, list) and "name" in name_class):
                    raise NoElementException("Thread name element is not found.")
                if not (isinstance(started_class, list) and "started" in started_class):
                    raise NoElementException("Thread started element is not found.")
                if not (isinstance(posts_count_class, list) and "posts" in posts_count_class):
                    raise NoElementException("Posts count element is not found.")

                title = name_elem.select_one(":scope > div.title > a")
                if title is None:
                    raise NoElementException("Title element is not found.")

                title_href = title.get("href")
                if title_href is None:
                    raise NoElementException("Title href is not found.")

                thread_id_match = re.search(r"t-(\d+)", str(title_href))
                if thread_id_match is None:
                    raise NoElementException("Thread ID is not found.")

                thread_id = int(thread_id_match.group(1))

                description_elem = name_elem.select_one(":scope > div.description")
                user_elem = started_elem.select_one(":scope > span.printuser")
                odate_elem = started_elem.select_one(":scope > span.odate")

                if description_elem is None:
                    raise NoElementException("Description element is not found.")
                if user_elem is None:
                    raise NoElementException("User element is not found.")
                if odate_elem is None:
                    raise NoElementException("Odate element is not found.")

                thread = ForumThread(
                    site=site,
                    id=int(thread_id),
                    title=title.get_text(" ", strip=True),
                    description=description_elem.get_text(" ", strip=True),
                    created_by=user_parser(site.client, user_elem),
                    created_at=odate_parser(odate_elem),
                    post_count=int(posts_count_elem.text),
                    category=category,
                )

                threads.append(thread)

        return ForumThreadCollection(site=site, threads=threads)

    @staticmethod
    def _parse_thread_page(
        site: "Site", html: BeautifulSoup, category: Optional["ForumCategory"] = None
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
        # title取得処理
        # forum-breadcrumbsの最後のNavigableStringを取得
        bc_elem = html.select_one("div.forum-breadcrumbs")
        if bc_elem is None:
            raise NoElementException("Breadcrumbs element is not found.")
        title = ForumThreadCollection._thread_title_from_breadcrumbs(bc_elem)
        if not title:
            raise NoElementException("Thread title is not found.")

        # description取得処理
        description_block_elem = html.select_one("div.description-block")
        if description_block_elem is None:
            raise NoElementException("Description block element is not found.")
        statistics_elems = description_block_elem.find_all("div", class_="statistics", recursive=False)
        if not statistics_elems:
            raise NoElementException("Statistics element is not found.")
        statistics_elem = statistics_elems[-1]
        description = ForumThreadCollection._description_text_from_block(description_block_elem, statistics_elem)

        # created_by取得処理
        user_elem = statistics_elem.find("span", class_="printuser", recursive=False)
        if user_elem is None:
            raise NoElementException("User element is not found.")
        created_by = user_parser(site.client, user_elem)

        # created_at取得処理
        odate_elem = statistics_elem.find("span", class_="odate", recursive=False)
        if odate_elem is None:
            raise NoElementException("Odate element is not found.")
        created_at = odate_parser(odate_elem)

        # post_count取得処理
        # 3番目のbrの前のテキスト
        br_tags = statistics_elem.find_all("br", recursive=False)
        if len(br_tags) < 3:
            raise NoElementException("Br tags are not enough.")
        post_count_elem = br_tags[2].previous_sibling
        if post_count_elem is None:
            raise NoElementException("Posts count element is not found.")
        post_count_text = str(post_count_elem)
        post_count_match = re.search(r"(\d+)", post_count_text)
        if post_count_match is None:
            raise NoElementException("Post count is not found.")
        post_count = int(post_count_match.group(1))

        # id取得処理
        # WIKIDOT.forumThreadId = xxxxxx;を全体から検索
        thread_id_pattern = re.compile(r"WIKIDOT.forumThreadId = \d+;")
        script_elem = None
        for script in html.find_all("script"):
            if script.string and thread_id_pattern.search(script.string):
                script_elem = script
                break
        if script_elem is None or script_elem.string is None:
            raise NoElementException("Script element is not found.")
        thread_id_match = re.search(r"(\d+)", script_elem.string)
        if thread_id_match is None:
            raise NoElementException("Thread ID is not found in script.")
        thread_id = int(thread_id_match.group(1))

        return ForumThread(
            site=site,
            id=thread_id,
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
            raise UnexpectedException("Cannot retrieve forum threads page: 1")

        first_body = first_response.json()["body"]
        first_html = BeautifulSoup(first_body, "lxml")

        threads.extend(ForumThreadCollection._parse_list_in_category(category.site, first_html, category))

        # pager検索
        pager = ForumThreadCollection._pager_from_html(first_html)
        if pager is None:
            return ForumThreadCollection(site=category.site, threads=threads)

        last_page = 1
        for link in reversed(pager.select("a")):
            page_text = link.get_text(strip=True)
            if page_text.isdigit():
                last_page = int(page_text)
                break
        if last_page == 1:
            return ForumThreadCollection(site=category.site, threads=threads)

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
                raise UnexpectedException(f"Cannot retrieve forum threads page: {page}")
            body = response.json()["body"]
            html = BeautifulSoup(body, "lxml")
            threads.extend(ForumThreadCollection._parse_list_in_category(category.site, html, category))

        return ForumThreadCollection(site=category.site, threads=threads)

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
                raise UnexpectedException(f"Cannot retrieve forum thread: {thread_id}")
            body = response.json()["body"]
            html = BeautifulSoup(body, "lxml")

            thread = ForumThreadCollection._parse_thread_page(site, html, category)
            if thread_id != thread.id:
                raise NoElementException("Thread ID is not matched.")
            threads_by_id[thread_id] = thread

        threads = [threads_by_id[thread_id] for thread_id in thread_ids]

        return ForumThreadCollection(site=site, threads=threads)


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
        self.site.client.login_check()
        self.site.amc_request(
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
        )
        # キャッシュをクリアして次回アクセス時に再取得
        self._posts = None
        self.post_count += 1
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
        return ForumThreadCollection.acquire_from_thread_ids(site, [thread_id], category)[0]
