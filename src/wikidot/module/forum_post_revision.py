"""
Module for handling Wikidot forum post revisions (edit history)

This module provides classes and functions related to Wikidot forum post revisions.
It enables operations such as retrieving revision history and accessing historical content.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass, replace
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, cast

from bs4 import BeautifulSoup, Tag

from ..common import exceptions
from ..util.parser import odate as odate_parser
from ..util.parser import user as user_parser

if TYPE_CHECKING:
    from .forum_post import ForumPost
    from .forum_thread import ForumThread
    from .site import Site
    from .user import AbstractUser


def _revision_list_parse_context(post: "ForumPost", row_index: int, **details: object) -> str:
    detail_values = {"row": row_index, **details}
    detail_text = ", ".join(f"{key}={value}" for key, value in detail_values.items())
    return f"for site: {post.thread.site.unix_name}, post: {post.id} ({detail_text})"


def _odate_class_value(odate_elem: Tag) -> str:
    class_attr = odate_elem.get("class", [])
    if class_attr is None:
        return ""
    class_values = [class_attr] if isinstance(class_attr, str) else [str(value) for value in class_attr]
    return next((value for value in class_values if "time_" in value), " ".join(class_values))


def _user_onclick_value(user_elem: Tag) -> str:
    link_elem = user_elem.find("a", recursive=False)
    if isinstance(link_elem, Tag):
        onclick = link_elem.get("onclick")
        if onclick is not None:
            return str(onclick)
    return user_elem.get_text(" ", strip=True)


def _revision_html_context(revision: "ForumPostRevision") -> str:
    return f"for site: {revision.post.thread.site.unix_name}, post: {revision.post.id}, revision: {revision.id}"


def _validate_forum_post(post: object) -> "ForumPost":
    from .forum_post import ForumPost

    if not isinstance(post, ForumPost):
        raise ValueError("post must be a ForumPost")
    return post


def _validate_forum_post_thread(thread: object) -> "ForumThread":
    from .forum_thread import ForumThread

    if not isinstance(thread, ForumThread):
        raise ValueError("thread must be a ForumThread")
    return thread


def _validate_forum_post_id(post_id: object) -> int:
    from .forum_post import _validate_post_id

    return _validate_post_id(post_id)


def _validate_forum_thread_id(thread_id: object) -> int:
    from .forum_thread import _validate_thread_id

    return _validate_thread_id(thread_id)


def _validate_forum_thread_site(site: object) -> "Site":
    from .site import Site

    if not isinstance(site, Site):
        raise ValueError("site must be a Site")
    return site


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


def _validate_revision_created_by(created_by: object) -> "AbstractUser":
    from .user import AbstractUser

    if not isinstance(created_by, AbstractUser):
        raise ValueError("created_by must be an AbstractUser")
    _validate_revision_created_by_id(created_by.id)
    return created_by


def _validate_revision_created_by_id(value: object) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("created_by.id must be an integer or None")
    if value < 0:
        raise ValueError("created_by.id must be non-negative or None")
    return value


def _validate_revision_created_by_site(site: "Site", created_by: "AbstractUser") -> None:
    if created_by.client is not site.client:
        raise ValueError("created_by must belong to the site")


def _validate_revision_created_at(created_at: object) -> datetime:
    if not isinstance(created_at, datetime):
        raise ValueError("created_at must be a datetime")
    return created_at


def _validate_forum_posts(posts: object) -> list["ForumPost"]:
    from .forum_post import ForumPost

    if not isinstance(posts, list):
        raise ValueError("posts must be a list")
    if any(not isinstance(post, ForumPost) for post in posts):
        raise ValueError("posts list entries must be ForumPost")
    return cast(list["ForumPost"], posts)


def _validate_with_html(value: object) -> bool:
    if not isinstance(value, bool):
        raise ValueError("with_html must be a boolean")
    return value


def _validate_revision_html(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("revision.html must be a string")
    return value


def _validate_optional_revision_html(value: object) -> str | None:
    if value is None:
        return None
    return _validate_revision_html(value)


def _validate_forum_post_revisions(revisions: object) -> list["ForumPostRevision"]:
    if revisions is None:
        return []
    if not isinstance(revisions, list):
        raise ValueError("revisions must be a list or None")
    if any(not isinstance(revision, ForumPostRevision) for revision in revisions):
        raise ValueError("revisions list entries must be ForumPostRevision")
    return cast(list["ForumPostRevision"], revisions)


def _revision_list_response_body(response: Any, post: "ForumPost") -> str:
    data = response.json()
    if not isinstance(data, dict):
        raise exceptions.NoElementException(
            "Forum post revision list response payload is malformed "
            f"for site: {post.thread.site.unix_name}, post: {post.id} "
            f"(expected=dict, actual={type(data).__name__})"
        )

    body = data.get("body")
    if body is None:
        raise exceptions.NoElementException(
            "Forum post revision list response body is not found "
            f"for site: {post.thread.site.unix_name}, post: {post.id}"
        )
    if not isinstance(body, str):
        raise exceptions.NoElementException(
            "Forum post revision list response body is malformed "
            f"for site: {post.thread.site.unix_name}, post: {post.id} "
            f"(field=body, expected=str, actual={type(body).__name__})"
        )
    return body


def _revision_html_content(revision: "ForumPostRevision", data: object) -> str:
    if not isinstance(data, dict):
        raise exceptions.NoElementException(
            "Forum post revision HTML response payload is malformed "
            f"{_revision_html_context(revision)} "
            f"(expected=dict, actual={type(data).__name__})"
        )
    content = data.get("content")
    if content is None:
        raise exceptions.NoElementException(
            f"Forum post revision HTML response content is not found {_revision_html_context(revision)}, field=content"
        )
    if not isinstance(content, str):
        raise exceptions.NoElementException(
            "Forum post revision HTML response content is malformed "
            f"{_revision_html_context(revision)} "
            f"(field=content, expected=str, actual={type(content).__name__})"
        )
    return content


def _validate_revision_html_targets(revisions: list["ForumPostRevision"]) -> None:
    for revision in revisions:
        revision_post = _validate_forum_post(revision.post)
        revision_thread = _validate_forum_post_thread(revision_post.thread)
        _validate_forum_thread_site(revision_thread.site)


def _validate_revisions_belong_to_post(post: "ForumPost", revisions: list["ForumPostRevision"]) -> None:
    if len(revisions) == 0:
        return

    post_thread = _validate_forum_post_thread(post.thread)
    post_site = _validate_forum_thread_site(post_thread.site)
    post_id = _validate_forum_post_id(post.id)
    post_thread_id = _validate_forum_thread_id(post_thread.id)
    for revision in revisions:
        revision_post = _validate_forum_post(revision.post)
        revision_thread = _validate_forum_post_thread(revision_post.thread)
        revision_site = _validate_forum_thread_site(revision_thread.site)
        revision_post_id = _validate_forum_post_id(revision_post.id)
        revision_thread_id = _validate_forum_thread_id(revision_thread.id)
        if revision_post_id != post_id or revision_thread_id != post_thread_id or revision_site is not post_site:
            raise ValueError("revisions must belong to the collection post")


def _validate_single_site(sites: list["Site"]) -> "Site":
    site = sites[0]
    if any(candidate is not site for candidate in sites[1:]):
        raise ValueError("posts must belong to the same Site")
    return site


def _validate_duplicate_post_ids_share_site(posts: list["ForumPost"], post_ids: list[int]) -> None:
    posts_by_id: dict[int, ForumPost] = {}
    sites_by_post_id: dict[int, Site] = {}
    for post, post_id in zip(posts, post_ids, strict=True):
        existing_post = posts_by_id.get(post_id)
        if existing_post is None:
            posts_by_id[post_id] = post
            continue

        existing_site = sites_by_post_id.get(post_id)
        if existing_site is None:
            existing_thread = _validate_forum_post_thread(existing_post.thread)
            existing_site = _validate_forum_thread_site(existing_thread.site)
            sites_by_post_id[post_id] = existing_site
        post_thread = _validate_forum_post_thread(post.thread)
        site = _validate_forum_thread_site(post_thread.site)
        if site is not existing_site:
            raise ValueError("posts must belong to the same Site")


class ForumPostRevisionCollection(list["ForumPostRevision"]):
    """
    Class representing a collection of forum post revisions

    A list extension class for storing and operating on multiple versions of a post's
    edit history (revisions) in bulk. Provides convenient functions such as
    batch retrieval of HTML content.
    """

    post: "ForumPost | None"

    def __init__(
        self,
        post: Optional["ForumPost"] = None,
        revisions: list["ForumPostRevision"] | None = None,
    ):
        """
        Initialize the collection

        Parameters
        ----------
        post : ForumPost | None, default None
            The post the revisions belong to. If None, inferred from the first revision
        revisions : list[ForumPostRevision] | None, default None
            List of revisions to store
        """
        validated_revisions = _validate_forum_post_revisions(revisions)
        if post is not None:
            self.post = _validate_forum_post(post)
            _validate_revisions_belong_to_post(self.post, validated_revisions)
        elif len(validated_revisions) > 0:
            self.post = _validate_forum_post(validated_revisions[0].post)
            _validate_revisions_belong_to_post(self.post, validated_revisions)
        else:
            self.post = None
        super().__init__(validated_revisions)

    def __iter__(self) -> Iterator["ForumPostRevision"]:
        """
        Return an iterator over the revisions in the collection

        Returns
        -------
        Iterator[ForumPostRevision]
            Iterator of revision objects
        """
        return super().__iter__()

    def find(self, id: int) -> Optional["ForumPostRevision"]:
        """
        Get the revision with the specified ID

        Parameters
        ----------
        id : int
            The ID of the revision to retrieve

        Returns
        -------
        ForumPostRevision | None
            The revision with the specified ID, or None if not found
        """
        if not isinstance(id, int) or isinstance(id, bool):
            raise ValueError("id must be an integer")
        for revision in self:
            if _validate_revision_id(revision.id) == id:
                return revision
        return None

    def find_by_rev_no(self, rev_no: int) -> Optional["ForumPostRevision"]:
        """
        Get the revision with the specified revision number

        Parameters
        ----------
        rev_no : int
            The revision number to retrieve (0 = initial version)

        Returns
        -------
        ForumPostRevision | None
            The revision with the specified revision number, or None if not found
        """
        if not isinstance(rev_no, int) or isinstance(rev_no, bool):
            raise ValueError("rev_no must be an integer")
        for revision in self:
            if _validate_revision_number(revision.rev_no) == rev_no:
                return revision
        return None

    @staticmethod
    def _parse(post: "ForumPost", html: BeautifulSoup) -> list["ForumPostRevision"]:
        """
        Parse revision list from HTML

        Parameters
        ----------
        post : ForumPost
            The post the revisions belong to
        html : BeautifulSoup
            HTML to parse

        Returns
        -------
        list[ForumPostRevision]
            List of parsed revisions (oldest first, with rev_no set)
        """
        revisions: list[ForumPostRevision] = []

        revision_table = html.select_one("table.table")
        if revision_table is None:
            return revisions

        rows = revision_table.find_all("tr", recursive=False)
        for row_index, row in enumerate(rows, start=1):
            # Skip header row
            row_class = row.get("class")
            if isinstance(row_class, list) and "head" in row_class:
                continue

            cells = row.find_all("td", recursive=False)
            if len(cells) < 3:
                parse_context = _revision_list_parse_context(post, row_index, field="cells", value=str(len(cells)))
                raise exceptions.NoElementException(f"Forum post revision row is malformed {parse_context}")

            # Get user element
            user_elem = cells[0].find("span", class_="printuser", recursive=False)
            if user_elem is None:
                parse_context = _revision_list_parse_context(post, row_index, field="created_by", value="")
                raise exceptions.NoElementException(f"Forum post revision user is not found {parse_context}")

            # Get odate element
            odate_elem = cells[1].find("span", class_="odate", recursive=False)
            if odate_elem is None:
                parse_context = _revision_list_parse_context(post, row_index, field="created_at", value="")
                raise exceptions.NoElementException(f"Forum post revision timestamp is not found {parse_context}")

            # Get revision ID from onclick attribute
            revision_link = cells[2].find(
                "a",
                onclick=lambda onclick: isinstance(onclick, str) and "showRevision" in onclick,
                recursive=False,
            )
            if revision_link is None:
                parse_context = _revision_list_parse_context(post, row_index, field="revision_id", value="")
                raise exceptions.NoElementException(f"Forum post revision link is not found {parse_context}")

            onclick = str(revision_link.get("onclick", ""))
            match = re.fullmatch(
                r"(?:WIKIDOT\.modules\.ForumViewThreadModule\.listeners\.)?"
                r"showRevision\s*\(\s*event\s*,\s*([0-9]+)\s*\)",
                onclick,
            )
            if match is None:
                parse_context = _revision_list_parse_context(
                    post,
                    row_index,
                    field="revision_id",
                    value=onclick,
                )
                raise exceptions.NoElementException(f"Forum post revision ID is malformed {parse_context}")

            revision_id = int(match.group(1))
            try:
                created_by = user_parser(post.thread.site.client, user_elem)
            except ValueError as exc:
                parse_context = _revision_list_parse_context(
                    post,
                    row_index,
                    field="created_by",
                    value=_user_onclick_value(user_elem),
                )
                raise exceptions.NoElementException(f"Forum post revision user is malformed {parse_context}") from exc
            try:
                created_at = odate_parser(odate_elem)
            except ValueError as exc:
                parse_context = _revision_list_parse_context(
                    post,
                    row_index,
                    field="created_at",
                    value=_odate_class_value(odate_elem),
                )
                raise exceptions.NoElementException(
                    f"Forum post revision timestamp is malformed {parse_context}"
                ) from exc

            revisions.append(
                ForumPostRevision(
                    post=post,
                    id=revision_id,
                    rev_no=0,  # Will be set after parsing all revisions
                    created_by=created_by,
                    created_at=created_at,
                )
            )

        # API returns newest first, reverse to get oldest first and set rev_no
        revisions.reverse()
        for i, revision in enumerate(revisions):
            # Use object.__setattr__ to set dataclass field
            object.__setattr__(revision, "rev_no", i)

        return revisions

    @staticmethod
    def acquire_all(post: "ForumPost") -> "ForumPostRevisionCollection":
        """
        Get all revisions for a post

        Parameters
        ----------
        post : ForumPost
            Forum post to get revisions for

        Returns
        -------
        ForumPostRevisionCollection
            Collection containing all revisions for the post
        """
        post = _validate_forum_post(post)
        post_id = _validate_forum_post_id(post.id)
        if post._revisions is not None:
            return post._revisions

        thread = _validate_forum_post_thread(post.thread)
        site = _validate_forum_thread_site(thread.site)
        response = site.amc_request_with_retry(
            [
                {
                    "moduleName": "forum/sub/ForumPostRevisionsModule",
                    "postId": post_id,
                }
            ]
        )[0]
        if response is None:
            raise exceptions.UnexpectedException(
                f"Cannot retrieve forum post revisions for site: {site.unix_name}, post: {post_id}"
            )

        html = BeautifulSoup(_revision_list_response_body(response, post), "lxml")

        revisions = ForumPostRevisionCollection._parse(post, html)
        collection = ForumPostRevisionCollection(post=post, revisions=revisions)
        post._revisions = collection
        return collection

    @staticmethod
    def _copy_for_post(post: "ForumPost", revisions: "ForumPostRevisionCollection") -> "ForumPostRevisionCollection":
        return ForumPostRevisionCollection(
            post=post,
            revisions=[replace(revision, post=post) for revision in revisions],
        )

    @staticmethod
    def acquire_all_for_posts(
        posts: list["ForumPost"],
        with_html: bool = False,
    ) -> dict[int, "ForumPostRevisionCollection"]:
        """
        Get all revisions for multiple posts

        Batch retrieves revision history for the specified posts.
        Optionally retrieves HTML content for all revisions.

        Parameters
        ----------
        posts : list[ForumPost]
            List of posts to get revisions for
        with_html : bool, default False
            If True, also retrieves HTML content for all revisions

        Returns
        -------
        dict[int, ForumPostRevisionCollection]
            Dictionary mapping post ID to ForumPostRevisionCollection
        """
        posts = _validate_forum_posts(posts)
        with_html = _validate_with_html(with_html)
        if len(posts) == 0:
            return {}
        post_ids = [_validate_forum_post_id(post.id) for post in posts]
        _validate_duplicate_post_ids_share_site(posts, post_ids)

        result: dict[int, ForumPostRevisionCollection] = {}
        target_posts: list[ForumPost] = []
        target_post_ids: list[int] = []
        site: Site | None = None
        cached_revisions_by_id: dict[int, ForumPostRevisionCollection] = {}
        for post, post_id in zip(posts, post_ids, strict=True):
            if post._revisions is not None and post_id not in cached_revisions_by_id:
                cached_revisions_by_id[post_id] = post._revisions

        seen_post_ids: set[int] = set()
        for post, post_id in zip(posts, post_ids, strict=True):
            if post_id in seen_post_ids:
                continue
            seen_post_ids.add(post_id)
            cached_revisions = cached_revisions_by_id.get(post_id)
            if cached_revisions is not None:
                if cached_revisions.post is post:
                    result[post_id] = cached_revisions
                else:
                    result[post_id] = ForumPostRevisionCollection._copy_for_post(post, cached_revisions)
                continue
            target_posts.append(post)
            target_post_ids.append(post_id)

        # Step 1: Get and parse missing revision lists
        if len(target_posts) > 0:
            target_sites = [
                _validate_forum_thread_site(_validate_forum_post_thread(post.thread).site) for post in target_posts
            ]
            site = _validate_single_site(target_sites)
            responses = site.amc_request_with_retry(
                [
                    {
                        "moduleName": "forum/sub/ForumPostRevisionsModule",
                        "postId": post_id,
                    }
                    for post_id in target_post_ids
                ]
            )

            for post, post_id, response in zip(target_posts, target_post_ids, responses, strict=True):
                if response is None:
                    raise exceptions.UnexpectedException(
                        f"Cannot retrieve forum post revisions for site: {site.unix_name}, post: {post_id}"
                    )
                html = BeautifulSoup(_revision_list_response_body(response, post), "lxml")
                revisions = ForumPostRevisionCollection._parse(post, html)
                result[post_id] = ForumPostRevisionCollection(post=post, revisions=revisions)

        # Step 2: Optionally get HTML content for all revisions
        if with_html:
            all_revisions: list[ForumPostRevision] = []
            all_revision_ids: list[int] = []
            all_revisions_by_id: dict[int, list[ForumPostRevision]] = {}
            for collection in result.values():
                for revision in collection:
                    revision_id = _validate_revision_id(revision.id)
                    if revision.is_html_acquired():
                        continue
                    if revision_id not in all_revisions_by_id:
                        all_revisions.append(revision)
                        all_revision_ids.append(revision_id)
                        all_revisions_by_id[revision_id] = []
                    all_revisions_by_id[revision_id].append(revision)

            if len(all_revisions) > 0:
                _validate_revision_html_targets(all_revisions)
                if site is None:
                    revision_post = _validate_forum_post(all_revisions[0].post)
                    site = _validate_forum_thread_site(_validate_forum_post_thread(revision_post.thread).site)
                revision_sites = [
                    _validate_forum_thread_site(_validate_forum_post_thread(revision.post.thread).site)
                    for revision in all_revisions
                ]
                _validate_single_site([site, *revision_sites])
                html_responses = site.amc_request_with_retry(
                    [
                        {
                            "moduleName": "forum/sub/ForumPostRevisionModule",
                            "revisionId": revision_id,
                        }
                        for revision_id in all_revision_ids
                    ]
                )

                for revision, revision_id, response in zip(
                    all_revisions, all_revision_ids, html_responses, strict=True
                ):
                    if response is None:
                        revision_post = _validate_forum_post(revision.post)
                        revision_site = _validate_forum_thread_site(
                            _validate_forum_post_thread(revision_post.thread).site
                        )
                        raise exceptions.UnexpectedException(
                            "Cannot retrieve forum post revision HTML "
                            f"for site: {revision_site.unix_name}, post: {revision_post.id}, revision: {revision_id}"
                        )
                    data = response.json()
                    revision_html = _revision_html_content(revision, data)
                    for target_revision in all_revisions_by_id[revision_id]:
                        target_revision._html = revision_html

        for post, post_id in zip(target_posts, target_post_ids, strict=True):
            post._revisions = result[post_id]

        return result

    def get_htmls(self) -> "ForumPostRevisionCollection":
        """
        Get HTML content for all revisions in the collection

        Returns
        -------
        ForumPostRevisionCollection
            Self (for method chaining)
        """
        _validate_forum_post_revisions(self)

        revision_ids = [_validate_revision_id(revision.id) for revision in self]
        acquired_html_by_id = {
            revision_id: revision._html
            for revision, revision_id in zip(self, revision_ids, strict=True)
            if revision._html is not None
        }
        target_revisions: list[ForumPostRevision] = []
        target_revision_ids: list[int] = []
        target_revisions_by_id: dict[int, list[ForumPostRevision]] = {}
        for revision, revision_id in zip(self, revision_ids, strict=True):
            if revision.is_html_acquired():
                continue
            acquired_html = acquired_html_by_id.get(revision_id)
            if acquired_html is not None:
                revision._html = acquired_html
                continue
            if revision_id not in target_revisions_by_id:
                target_revisions.append(revision)
                target_revision_ids.append(revision_id)
                target_revisions_by_id[revision_id] = []
            target_revisions_by_id[revision_id].append(revision)

        if len(target_revisions) == 0:
            return self

        post = _validate_forum_post(self.post)
        thread = _validate_forum_post_thread(post.thread)
        site = _validate_forum_thread_site(thread.site)
        _validate_revision_html_targets(target_revisions)
        responses = site.amc_request_with_retry(
            [
                {
                    "moduleName": "forum/sub/ForumPostRevisionModule",
                    "revisionId": revision_id,
                }
                for revision_id in target_revision_ids
            ]
        )

        for revision, revision_id, response in zip(target_revisions, target_revision_ids, responses, strict=True):
            if response is None:
                continue
            data = response.json()
            html = _revision_html_content(revision, data)
            for target_revision in target_revisions_by_id[revision_id]:
                target_revision._html = html

        return self


@dataclass
class ForumPostRevision:
    """
    Class representing a forum post revision (version in edit history)

    Holds information about a specific version of a post. Provides basic information
    such as revision number, creator, and creation date, along with access to HTML content.

    Attributes
    ----------
    post : ForumPost
        The post this revision belongs to
    id : int
        Revision ID
    rev_no : int
        Revision number (0 = initial version)
    created_by : AbstractUser
        The creator of the revision
    created_at : datetime
        The creation date and time of the revision
    _html : str | None, default None
        The revision's HTML content (internal cache)
    """

    post: "ForumPost"
    id: int
    rev_no: int
    created_by: "AbstractUser"
    created_at: datetime
    _html: str | None = None

    def __post_init__(self) -> None:
        self.post = _validate_forum_post(self.post)
        self.id = _validate_revision_id(self.id)
        self.rev_no = _validate_revision_number(self.rev_no)
        self.created_by = _validate_revision_created_by(self.created_by)
        post_thread = _validate_forum_post_thread(self.post.thread)
        post_site = _validate_forum_thread_site(post_thread.site)
        _validate_revision_created_by_site(post_site, self.created_by)
        self.created_at = _validate_revision_created_at(self.created_at)
        self._html = _validate_optional_revision_html(self._html)

    def __str__(self) -> str:
        """
        String representation of the object

        Returns
        -------
        str
            String representation of the revision
        """
        return f"ForumPostRevision(id={self.id}, rev_no={self.rev_no})"

    def is_html_acquired(self) -> bool:
        """
        Check if HTML content has already been acquired

        Returns
        -------
        bool
            True if HTML content is acquired, False otherwise
        """
        return self._html is not None

    @property
    def html(self) -> str:
        """
        Get the revision's HTML content

        Automatically fetches the HTML content if not yet acquired.

        Returns
        -------
        str
            The revision's HTML content
        """
        if not self.is_html_acquired():
            ForumPostRevisionCollection(self.post, [self]).get_htmls()
        if self._html is None:
            raise exceptions.UnexpectedException(
                "Cannot retrieve forum post revision HTML "
                f"for site: {self.post.thread.site.unix_name}, post: {self.post.id}, revision: {self.id}"
            )
        return self._html

    @html.setter
    def html(self, value: str) -> None:
        """
        Set the revision's HTML content

        Parameters
        ----------
        value : str
            The HTML content to set
        """
        self._html = _validate_revision_html(value)
