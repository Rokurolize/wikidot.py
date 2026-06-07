"""
Module for handling Wikidot forum posts

This module provides classes and functionality related to Wikidot forum posts (individual messages within threads).
It enables operations such as retrieving post information and display.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, cast

from bs4 import BeautifulSoup, Tag

from ..common.exceptions import NoElementException, UnexpectedException, WikidotStatusCodeException
from ..util.parser import odate as odate_parser
from ..util.parser import user as user_parser
from ._validation import validate_text_field

if TYPE_CHECKING:
    from .forum_post_revision import ForumPostRevisionCollection
    from .forum_thread import ForumThread
    from .site import Site
    from .user import AbstractUser


def _site_name(site: object) -> str:
    site_unix_name = getattr(site, "unix_name", None)
    return site_unix_name if isinstance(site_unix_name, str) else str(site)


def _validate_forum_thread(thread: object) -> "ForumThread":
    from .forum_thread import ForumThread

    if not isinstance(thread, ForumThread):
        raise ValueError("thread must be a ForumThread")
    return thread


def _validate_forum_thread_site(site: object) -> "Site":
    from .site import Site

    if not isinstance(site, Site):
        raise ValueError("site must be a Site")
    return site


def _validate_post_id(post_id: object) -> int:
    if not isinstance(post_id, int) or isinstance(post_id, bool):
        raise ValueError("id must be an integer")
    return post_id


def _validate_optional_post_parent_id(parent_id: object) -> int | None:
    if parent_id is None:
        return None
    if not isinstance(parent_id, int) or isinstance(parent_id, bool):
        raise ValueError("parent_id must be an integer or None")
    return parent_id


def _validate_optional_post_source(source: object) -> str | None:
    if source is None:
        return None
    if not isinstance(source, str):
        raise ValueError("post.source must be a string or None")
    return source


def _validate_optional_post_revisions(revisions: object) -> Optional["ForumPostRevisionCollection"]:
    if revisions is None:
        return None

    from .forum_post_revision import ForumPostRevision, ForumPostRevisionCollection

    if not isinstance(revisions, ForumPostRevisionCollection):
        raise ValueError("post.revisions must be ForumPostRevisionCollection or None")
    if any(not isinstance(revision, ForumPostRevision) for revision in revisions):
        raise ValueError("post.revisions list entries must be ForumPostRevision")
    return revisions


def _validate_post_created_by(created_by: object) -> "AbstractUser":
    from .user import AbstractUser

    if not isinstance(created_by, AbstractUser):
        raise ValueError("created_by must be an AbstractUser")
    return created_by


def _validate_post_created_at(created_at: object) -> datetime:
    if not isinstance(created_at, datetime):
        raise ValueError("created_at must be a datetime")
    return created_at


def _validate_optional_post_edited_by(edited_by: object) -> Optional["AbstractUser"]:
    if edited_by is None:
        return None

    from .user import AbstractUser

    if not isinstance(edited_by, AbstractUser):
        raise ValueError("edited_by must be an AbstractUser or None")
    return edited_by


def _validate_optional_post_edited_at(edited_at: object) -> datetime | None:
    if edited_at is None:
        return None
    if not isinstance(edited_at, datetime):
        raise ValueError("edited_at must be a datetime or None")
    return edited_at


def _validate_forum_threads(threads: object) -> list["ForumThread"]:
    from .forum_thread import ForumThread

    if not isinstance(threads, list):
        raise ValueError("threads must be a list")
    if any(not isinstance(thread, ForumThread) for thread in threads):
        raise ValueError("threads list entries must be ForumThread")
    return cast(list["ForumThread"], threads)


def _validate_forum_posts(posts: object) -> list["ForumPost"]:
    if not isinstance(posts, list):
        raise ValueError("posts must be a list")
    if any(not isinstance(post, ForumPost) for post in posts):
        raise ValueError("posts list entries must be ForumPost")
    return cast(list["ForumPost"], posts)


def _validate_forum_post_collection_posts(posts: object) -> list["ForumPost"]:
    if posts is None:
        return []
    if not isinstance(posts, list):
        raise ValueError("posts must be a list or None")
    return _validate_forum_posts(posts)


def _post_list_parse_context(
    thread: "ForumThread",
    page: int | None,
    post_index: int,
    post_id: int | None = None,
    **details: object,
) -> str:
    context = [f"thread={thread.id}"]
    if page is not None:
        context.append(f"page={page}")
    context.append(f"post={post_index}")
    if post_id is not None:
        context.append(f"post_id={post_id}")
    context.extend(f"{name}={value}" for name, value in details.items())
    return f"for site: {_site_name(thread.site)} ({', '.join(context)})"


def _parse_post_id_value(
    thread: "ForumThread",
    page: int | None,
    post_index: int,
    value: object,
    *,
    field: str,
    post_id: int | None = None,
) -> int:
    value_text = str(value)
    raw_id = value_text.removeprefix("post-")
    if value_text == raw_id or not raw_id.isdigit():
        parse_context = _post_list_parse_context(thread, page, post_index, post_id, field=field, value=value_text)
        raise NoElementException(f"Post ID is malformed {parse_context}")
    return int(raw_id)


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


def _parse_post_list_user(
    thread: "ForumThread",
    page: int | None,
    post_index: int,
    post_id: int,
    user_elem: Tag,
    *,
    field: str = "created_by",
) -> "AbstractUser":
    try:
        return user_parser(thread.site.client, user_elem)
    except ValueError as exc:
        parse_context = _post_list_parse_context(
            thread,
            page,
            post_index,
            post_id,
            field=field,
            value=_user_onclick_value(user_elem),
        )
        raise NoElementException(f"Forum post user is malformed {parse_context}") from exc


def _parse_post_list_created_at(
    thread: "ForumThread",
    page: int | None,
    post_index: int,
    post_id: int,
    odate_elem: Tag,
    *,
    field: str = "created_at",
) -> datetime:
    try:
        return odate_parser(odate_elem)
    except ValueError as exc:
        parse_context = _post_list_parse_context(
            thread,
            page,
            post_index,
            post_id,
            field=field,
            value=_odate_class_value(odate_elem),
        )
        raise NoElementException(f"Forum post {field} is malformed {parse_context}") from exc


def _require_forum_post_action_status(post: "ForumPost", event: str, data: dict[str, Any]) -> Any:
    try:
        status = data["status"]
    except KeyError as exc:
        raise NoElementException(
            f"Forum post action response is malformed for site: {post.thread.site.unix_name}, post: {post.id} "
            f"(event={event}, field=status)"
        ) from exc

    if status != "ok":
        raise WikidotStatusCodeException(
            f"Failed to complete forum post action for site: {post.thread.site.unix_name}, post: {post.id}, "
            f"event: {event}",
            status,
        )
    return status


class ForumPostCollection(list["ForumPost"]):
    """
    Class representing a collection of forum posts

    A list extension class for storing multiple posts within a forum thread and performing batch operations。
    """

    thread: "ForumThread | None"

    def __init__(
        self,
        thread: Optional["ForumThread"] = None,
        posts: list["ForumPost"] | None = None,
    ):
        """
        Initialization method

        Parameters
        ----------
        thread : ForumThread | None, default None
            The thread the posts belong to。If None, inferred from the first post
        posts : list[ForumPost] | None, default None
            List of posts to store
        """
        super().__init__(_validate_forum_post_collection_posts(posts))

        if thread is not None:
            self.thread = _validate_forum_thread(thread)
        elif len(self) > 0:
            self.thread = self[0].thread
        else:
            self.thread = None

    def __iter__(self) -> Iterator["ForumPost"]:
        """
        Iterator that returns posts in the collection sequentially

        Returns
        -------
        Iterator[ForumPost]
            Iterator of post objects
        """
        return super().__iter__()

    def find(self, id: int) -> Optional["ForumPost"]:
        """
        Retrieve a post with the specified ID

        Parameters
        ----------
        id : int
            Post ID to retrieve

        Returns
        -------
        ForumPost | None
            Post with the specified ID, or None if it does not exist
        """
        if not isinstance(id, int) or isinstance(id, bool):
            raise ValueError("id must be an integer")
        for post in self:
            if post.id == id:
                return post
        return None

    @staticmethod
    def _copy_for_thread(thread: "ForumThread", posts: "ForumPostCollection") -> "ForumPostCollection":
        return ForumPostCollection(
            thread=thread,
            posts=[
                ForumPost(
                    thread=thread,
                    id=post.id,
                    title=post.title,
                    text=post.text,
                    element=post.element,
                    created_by=post.created_by,
                    created_at=post.created_at,
                    edited_by=post.edited_by,
                    edited_at=post.edited_at,
                    _parent_id=post._parent_id,
                    _source=post._source,
                )
                for post in posts
            ],
        )

    @staticmethod
    def _last_page_from_pager(pager: Tag) -> int:
        last_page = 1
        for pager_target in reversed(pager.select("span.target")):
            page_text = pager_target.get_text(strip=True)
            if page_text.isdigit():
                last_page = int(page_text)
                break
        return last_page

    @staticmethod
    def _pager_from_html(html: BeautifulSoup) -> Tag | None:
        for pager in html.select("div.pager"):
            if ForumPostCollection._is_inside_post_content(pager):
                continue
            return pager
        return None

    @staticmethod
    def _post_list_response_body(response: Any, thread: "ForumThread", page: int) -> str:
        body = response.json().get("body")
        if body is None:
            raise NoElementException(
                "Forum post list response body is not found "
                f"for site: {thread.site.unix_name}, thread: {thread.id}, page: {page}"
            )
        if not isinstance(body, str):
            raise NoElementException(
                "Forum post list response body is malformed "
                f"for site: {thread.site.unix_name}, thread: {thread.id}, page: {page} "
                f"(field=body, expected=str, actual={type(body).__name__})"
            )
        return body

    @staticmethod
    def _source_response_body(response: Any, post: "ForumPost") -> str:
        body = response.json().get("body")
        if body is None:
            raise NoElementException(
                f"Forum post source response body is not found for site: {post.thread.site.unix_name}, post: {post.id}"
            )
        if not isinstance(body, str):
            raise NoElementException(
                f"Forum post source response body is malformed for site: {post.thread.site.unix_name}, post: {post.id} "
                f"(field=body, expected=str, actual={type(body).__name__})"
            )
        return body

    @staticmethod
    def _is_inside_post_content(post_elem: Tag) -> bool:
        for ancestor in post_elem.parents:
            if not isinstance(ancestor, Tag):
                continue
            ancestor_classes = ancestor.get("class")
            ancestor_id = ancestor.get("id")
            if (
                isinstance(ancestor_classes, list)
                and "content" in ancestor_classes
                and isinstance(ancestor_id, str)
                and ancestor_id.startswith("post-content-")
            ):
                return True
        return False

    @staticmethod
    def _parse(thread: "ForumThread", html: BeautifulSoup, page: int | None = None) -> list["ForumPost"]:
        """
        Parse post list from HTML

        Parameters
        ----------
        thread : ForumThread
            The thread the posts belong to
        html : BeautifulSoup
            HTML to parse
        page : int | None, default None
            Post-list page number when available

        Returns
        -------
        list[ForumPost]
            List of parsed posts

        Raises
        ------
        NoElementException
            If required elements are not found
        """
        posts: list[ForumPost] = []
        # Wikidot forum posts are direct children of post containers; content can contain post-like markup.
        post_elements = html.select("div.post-container > div.post[id^='post-']")

        post_index = 0
        for post_elem in post_elements:
            if ForumPostCollection._is_inside_post_content(post_elem):
                continue

            post_index += 1
            parse_context = _post_list_parse_context(thread, page, post_index)
            post_id_attr = post_elem.get("id")
            if post_id_attr is None:
                raise NoElementException(f"Post ID attribute is not found {parse_context}")
            post_id = _parse_post_id_value(thread, page, post_index, post_id_attr, field="post_id")
            parse_context = _post_list_parse_context(thread, page, post_index, post_id)

            # 親Post IDの取得
            parent_id: int | None = None
            parent_container = post_elem.parent
            if parent_container is not None:
                grandparent = parent_container.parent
                if grandparent is not None and grandparent.name != "body":
                    grandparent_class = grandparent.get("class")
                    if isinstance(grandparent_class, list) and "post-container" in grandparent_class:
                        parent_post = grandparent.find("div", class_="post", recursive=False)
                        if isinstance(parent_post, Tag):
                            parent_id_attr = parent_post.get("id")
                            if parent_id_attr is not None:
                                parent_id = _parse_post_id_value(
                                    thread,
                                    page,
                                    post_index,
                                    parent_id_attr,
                                    field="parent_post_id",
                                    post_id=post_id,
                                )

            # タイトルと本文の取得
            # Use :scope > to get direct children only (avoid matching nested pseudo-posts)
            wrapper = post_elem.select_one(":scope > div.long")
            if wrapper is None:
                raise NoElementException(f"Post wrapper element is not found {parse_context}")

            head = wrapper.select_one(":scope > div.head")
            if head is None:
                raise NoElementException(f"Post head element is not found {parse_context}")

            title_elem = head.select_one(":scope > div.title")
            if title_elem is None:
                raise NoElementException(f"Post title element is not found {parse_context}")
            title = title_elem.get_text(" ", strip=True)

            content_elem = wrapper.select_one(":scope > div.content")
            if content_elem is None:
                raise NoElementException(f"Post content element is not found {parse_context}")
            text = str(content_elem)

            # 投稿者と日時
            info_elem = head.select_one(":scope > div.info")
            if info_elem is None:
                raise NoElementException(f"Post info element is not found {parse_context}")

            user_elem = info_elem.select_one(":scope > span.printuser")
            if user_elem is None:
                raise NoElementException(f"Post user element is not found {parse_context}")
            created_by = _parse_post_list_user(thread, page, post_index, post_id, user_elem)

            odate_elem = info_elem.select_one(":scope > span.odate")
            if odate_elem is None:
                raise NoElementException(f"Post odate element is not found {parse_context}")
            created_at = _parse_post_list_created_at(thread, page, post_index, post_id, odate_elem)

            # 編集情報（存在する場合）
            edited_by = None
            edited_at = None
            changes_elem = wrapper.select_one(":scope > div.changes")
            if changes_elem is not None:
                edit_user_elem = changes_elem.select_one(":scope > span.printuser")
                edit_odate_elem = changes_elem.select_one(":scope > span.odate")
                if edit_user_elem is not None and edit_odate_elem is not None:
                    edited_by = _parse_post_list_user(
                        thread,
                        page,
                        post_index,
                        post_id,
                        edit_user_elem,
                        field="edited_by",
                    )
                    edited_at = _parse_post_list_created_at(
                        thread,
                        page,
                        post_index,
                        post_id,
                        edit_odate_elem,
                        field="edited_at",
                    )

            post = ForumPost(
                thread=thread,
                id=post_id,
                title=title,
                text=text,
                element=post_elem,
                created_by=created_by,
                created_at=created_at,
                edited_by=edited_by,
                edited_at=edited_at,
                _parent_id=parent_id,
            )
            posts.append(post)

        return posts

    @staticmethod
    def acquire_all_in_thread(thread: "ForumThread") -> "ForumPostCollection":
        """
        Retrieve all posts in a thread

        Retrieves all posts in the specified thread。
        Traverses all pages if pagination exists。

        Parameters
        ----------
        thread : ForumThread
            Thread to retrieve posts from

        Returns
        -------
        ForumPostCollection
            Collection containing all posts in the thread

        Raises
        ------
        NoElementException
            If HTML element parsing fails
        """
        thread = _validate_forum_thread(thread)
        return ForumPostCollection.acquire_all_in_threads([thread])[thread.id]

    @staticmethod
    def acquire_all_in_threads(
        threads: list["ForumThread"],
    ) -> dict[int, "ForumPostCollection"]:
        """
        Retrieve all posts from multiple threads

        Batch retrieves all posts from the specified threads.
        Handles pagination for each thread.

        Parameters
        ----------
        threads : list[ForumThread]
            List of threads to retrieve posts from

        Returns
        -------
        dict[int, ForumPostCollection]
            Dictionary mapping thread ID to ForumPostCollection

        Raises
        ------
        NoElementException
            If HTML element parsing fails
        """
        threads = _validate_forum_threads(threads)
        if len(threads) == 0:
            return {}

        result: dict[int, ForumPostCollection] = {}
        cached_posts_by_id: dict[int, ForumPostCollection] = {}
        for thread in threads:
            if thread._posts is not None and thread.id not in cached_posts_by_id:
                cached_posts_by_id[thread.id] = thread._posts

        target_threads: list[ForumThread] = []
        seen_thread_ids: set[int] = set()
        for thread in threads:
            if thread.id in seen_thread_ids:
                continue
            seen_thread_ids.add(thread.id)
            if thread._posts is not None:
                result[thread.id] = thread._posts
                continue
            cached_posts = cached_posts_by_id.get(thread.id)
            if cached_posts is not None:
                result[thread.id] = ForumPostCollection._copy_for_thread(thread, cached_posts)
                continue
            target_threads.append(thread)

        if len(target_threads) == 0:
            return result

        target_sites = [_validate_forum_thread_site(thread.site) for thread in target_threads]
        site = target_sites[0]

        # Step 1: Get the first page of all threads
        first_page_responses = site.amc_request_with_retry(
            [
                {
                    "moduleName": "forum/ForumViewThreadPostsModule",
                    "pageNo": "1",
                    "t": str(thread.id),
                }
                for thread in target_threads
            ]
        )

        # Step 2: Parse first pages and determine pagination
        additional_requests: list[tuple[ForumThread, int]] = []

        for thread, response in zip(target_threads, first_page_responses, strict=True):
            if response is None:
                raise UnexpectedException(
                    f"Cannot retrieve forum posts for site: {thread.site.unix_name}, thread: {thread.id}, page: 1"
                )
            body = ForumPostCollection._post_list_response_body(response, thread, 1)
            html = BeautifulSoup(body, "lxml")

            posts = ForumPostCollection._parse(thread, html, page=1)
            result[thread.id] = ForumPostCollection(thread=thread, posts=posts)

            # Check pagination
            pager = ForumPostCollection._pager_from_html(html)
            if pager is None:
                continue

            last_page = ForumPostCollection._last_page_from_pager(pager)
            if last_page <= 1:
                continue

            # Queue additional page requests
            for page in range(2, last_page + 1):
                additional_requests.append((thread, page))

        # Step 3: Fetch additional pages
        if len(additional_requests) > 0:
            additional_responses = site.amc_request_with_retry(
                [
                    {
                        "moduleName": "forum/ForumViewThreadPostsModule",
                        "pageNo": str(page),
                        "t": str(thread.id),
                    }
                    for thread, page in additional_requests
                ]
            )

            for (thread, page), response in zip(additional_requests, additional_responses, strict=True):
                if response is None:
                    raise UnexpectedException(
                        f"Cannot retrieve forum posts for site: {thread.site.unix_name}, thread: {thread.id}, page: {page}"
                    )
                body = ForumPostCollection._post_list_response_body(response, thread, page)
                html = BeautifulSoup(body, "lxml")
                posts = ForumPostCollection._parse(thread, html, page=page)
                result[thread.id].extend(posts)

        for thread in target_threads:
            thread._posts = result[thread.id]

        return result

    @staticmethod
    def _acquire_post_sources(thread: "ForumThread", posts: list["ForumPost"]) -> list["ForumPost"]:
        """
        Internal method to retrieve post sources

        Batch retrieves source code (Wikidot syntax) for specified posts.

        Parameters
        ----------
        thread : ForumThread
            Thread to which posts belong
        posts : list[ForumPost]
            List of target posts

        Returns
        -------
        list[ForumPost]
            List of posts with updated source information

        Raises
        ------
        NoElementException
            When source elements are not found
        """
        thread = _validate_forum_thread(thread)
        posts = _validate_forum_posts(posts)
        if len(posts) == 0:
            return posts

        sources_by_id: dict[int, str] = {}
        for post in posts:
            if post._source is not None:
                sources_by_id[post.id] = post._source

        target_posts: list[ForumPost] = []
        target_posts_by_id: dict[int, list[ForumPost]] = {}
        for post in posts:
            if post._source is not None:
                continue
            if post.id in sources_by_id:
                post._source = sources_by_id[post.id]
                continue
            if post.id not in target_posts_by_id:
                target_posts.append(post)
                target_posts_by_id[post.id] = []
            target_posts_by_id[post.id].append(post)

        if len(target_posts) == 0:
            return posts

        responses = thread.site.amc_request_with_retry(
            [
                {
                    "moduleName": "forum/sub/ForumEditPostFormModule",
                    "threadId": thread.id,
                    "postId": post.id,
                }
                for post in target_posts
            ]
        )

        for post, response in zip(target_posts, responses, strict=True):
            if response is None:
                continue
            html = BeautifulSoup(ForumPostCollection._source_response_body(response, post), "lxml")
            edit_form = html.select_one("form#edit-post-form")
            source_elem = (
                edit_form.select_one(":scope > textarea[name='source']") if isinstance(edit_form, Tag) else None
            )
            if source_elem is None:
                raise NoElementException(
                    f"Source textarea is not found for site: {thread.site.unix_name}, post: {post.id}"
                )
            source = source_elem.get_text()
            for target_post in target_posts_by_id[post.id]:
                target_post._source = source

        return posts

    def get_post_sources(self) -> "ForumPostCollection":
        """
        Get source code for all posts in the collection

        Batch retrieves source code (Wikidot syntax) for posts and sets the source property for each post.

        Returns
        -------
        ForumPostCollection
            Self (for method chaining)
        """
        if self.thread is None:
            return self

        ForumPostCollection._acquire_post_sources(self.thread, self)
        return self


@dataclass
class ForumPost:
    """
    Class representing a Wikidot forum post

    Holds information about individual posts (messages) within a forum thread.
    Provides information such as post title, body, author, and creation date.

    Attributes
    ----------
    thread : ForumThread
        The thread the post belongs to
    id : int
        Post ID
    title : str
        Post title
    text : str
        Post body (HTML text)
    element : Tag
        HTML element of the post (for parsing)
    created_by : AbstractUser
        Post creator
    created_at : datetime
        Post creation date and time
    edited_by : AbstractUser | None, default None
        Post editor (None if not edited)
    edited_at : datetime | None, default None
        Post edit date and time (None if not edited)
    _parent_id : int | None, default None
        Parent post ID (ID of the post being replied to)
    _source : str | None, default None
        Post source (Wikidot syntax)
    """

    thread: "ForumThread"
    id: int
    title: str
    text: str
    element: Tag
    created_by: "AbstractUser"
    created_at: datetime
    edited_by: Optional["AbstractUser"] = None
    edited_at: datetime | None = None
    _parent_id: int | None = None
    _source: str | None = None
    _revisions: Optional["ForumPostRevisionCollection"] = None

    def __post_init__(self) -> None:
        self.thread = _validate_forum_thread(self.thread)
        self.id = _validate_post_id(self.id)
        self._parent_id = _validate_optional_post_parent_id(self._parent_id)
        self._source = _validate_optional_post_source(self._source)
        self._revisions = _validate_optional_post_revisions(self._revisions)
        self.title = validate_text_field("title", self.title)
        self.text = validate_text_field("text", self.text)
        self.created_by = _validate_post_created_by(self.created_by)
        self.created_at = _validate_post_created_at(self.created_at)
        self.edited_by = _validate_optional_post_edited_by(self.edited_by)
        self.edited_at = _validate_optional_post_edited_at(self.edited_at)

    def __str__(self) -> str:
        """
        String representation of the object

        Returns
        -------
        str
            String representation of the post
        """
        return (
            f"ForumPost(thread={self.thread}, id={self.id}, title={self.title}, "
            f"text={self.text}, created_by={self.created_by}, created_at={self.created_at}, "
            f"edited_by={self.edited_by}, edited_at={self.edited_at})"
        )

    @property
    def parent_id(self) -> int | None:
        """
        Retrieve the parent post ID

        Returns
        -------
        int | None
            Parent post ID, or None if no parent
        """
        return self._parent_id

    @property
    def has_revisions(self) -> bool:
        """
        Check if the post has been edited (has revisions)

        Returns
        -------
        bool
            True if the post has been edited, False otherwise
        """
        return self.edited_by is not None

    @property
    def revisions(self) -> "ForumPostRevisionCollection":
        """
        Retrieve all revisions for this post

        Automatically retrieves if revisions have not been fetched.

        Returns
        -------
        ForumPostRevisionCollection
            Collection of all revisions for this post
        """
        if self._revisions is None:
            from .forum_post_revision import ForumPostRevisionCollection

            result = ForumPostRevisionCollection.acquire_all_for_posts([self])
            self._revisions = result.get(self.id, ForumPostRevisionCollection(post=self, revisions=[]))
        return self._revisions

    @property
    def source(self) -> str:
        """
        Retrieve the post source (Wikidot syntax)

        Automatically retrieves if source has not been fetched.

        Returns
        -------
        str
            Post source (Wikidot syntax)

        Raises
        ------
        NoElementException
            If source element is not found
        """
        if self._source is None:
            ForumPostCollection(self.thread, [self]).get_post_sources()

        if self._source is None:
            raise NoElementException(
                f"Source textarea is not found for site: {self.thread.site.unix_name}, post: {self.id}"
            )

        return self._source

    @staticmethod
    def _edit_form_response_body(response: Any, post: "ForumPost") -> str:
        body = response.json().get("body")
        if body is None:
            raise NoElementException(
                f"Forum post edit form response body is not found for site: {post.thread.site.unix_name}, post: {post.id}"
            )
        if not isinstance(body, str):
            raise NoElementException(
                "Forum post edit form response body is malformed "
                f"for site: {post.thread.site.unix_name}, post: {post.id} "
                f"(field=body, expected=str, actual={type(body).__name__})"
            )
        return body

    def edit(self, source: str, title: str | None = None) -> "ForumPost":
        """
        Edit the post

        Updates the post content. Maintains the current title if not specified。

        Parameters
        ----------
        source : str
            New source (Wikidot syntax)
        title : str | None, default None
            New title (maintains current title if None)

        Returns
        -------
        ForumPost
            Self (for method chaining)

        Raises
        ------
        LoginRequiredException
            If not logged in
        WikidotStatusCodeException
            If editing fails
        NoElementException
            If revision ID element is not found
        UnexpectedException
            If the edit form cannot be retrieved
        """
        source = validate_text_field("source", source)
        if title is not None:
            title = validate_text_field("title", title)
        self.thread.site.client.login_check()

        # 現在のリビジョンIDを取得
        form_response = self.thread.site.amc_request_with_retry(
            [
                {
                    "moduleName": "forum/sub/ForumEditPostFormModule",
                    "threadId": self.thread.id,
                    "postId": self.id,
                }
            ]
        )[0]
        if form_response is None:
            raise UnexpectedException(
                f"Cannot retrieve forum post edit form for site: {self.thread.site.unix_name}, post: {self.id}"
            )

        html = BeautifulSoup(ForumPost._edit_form_response_body(form_response, self), "lxml")
        edit_form = html.select_one("form#edit-post-form")
        revision_elem = (
            edit_form.select_one(":scope > input[name='currentRevisionId']") if isinstance(edit_form, Tag) else None
        )
        if revision_elem is None:
            raise NoElementException(
                f"Current revision ID input is not found for site: {self.thread.site.unix_name}, post: {self.id}"
            )
        revision_value = revision_elem.get("value")
        if revision_value is None:
            raise NoElementException(
                f"Current revision ID value is not found for site: {self.thread.site.unix_name}, post: {self.id}"
            )
        try:
            current_revision_id = int(str(revision_value))
        except ValueError as exc:
            raise NoElementException(
                f"Current revision ID value is malformed for site: {self.thread.site.unix_name}, post: {self.id}"
            ) from exc

        # 編集を保存
        save_response = self.thread.site.amc_request(
            [
                {
                    "action": "ForumAction",
                    "event": "saveEditPost",
                    "moduleName": "Empty",
                    "postId": self.id,
                    "currentRevisionId": current_revision_id,
                    "title": title if title is not None else self.title,
                    "source": source,
                }
            ]
        )[0]
        _require_forum_post_action_status(self, "saveEditPost", save_response.json())

        # ローカル状態を更新
        if title is not None:
            self.title = title
        self._source = source
        self._revisions = None
        self.thread._posts = None

        return self
