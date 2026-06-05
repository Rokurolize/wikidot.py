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


def _validate_forum_post_revisions(revisions: list["ForumPostRevision"]) -> list["ForumPostRevision"]:
    if any(not isinstance(revision, ForumPostRevision) for revision in revisions):
        raise ValueError("revisions list entries must be ForumPostRevision")
    return revisions


def _revision_list_response_body(response: Any, post: "ForumPost") -> str:
    body = response.json().get("body")
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


def _revision_html_content(revision: "ForumPostRevision", data: dict[str, object]) -> str:
    content = data.get("content")
    if content is None:
        raise exceptions.NoElementException(
            f"Forum post revision HTML response content is not found {_revision_html_context(revision)}, field=content"
        )
    return str(content)


class ForumPostRevisionCollection(list["ForumPostRevision"]):
    """
    Class representing a collection of forum post revisions

    A list extension class for storing and operating on multiple versions of a post's
    edit history (revisions) in bulk. Provides convenient functions such as
    batch retrieval of HTML content.
    """

    post: "ForumPost"

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
        super().__init__(revisions or [])
        if post is not None:
            self.post = post
        elif len(self) > 0:
            self.post = self[0].post

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
            if revision.id == id:
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
            if revision.rev_no == rev_no:
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
                continue

            # Get user element
            user_elem = cells[0].find("span", class_="printuser", recursive=False)
            if user_elem is None:
                continue

            # Get odate element
            odate_elem = cells[1].find("span", class_="odate", recursive=False)
            if odate_elem is None:
                continue

            # Get revision ID from onclick attribute
            revision_link = cells[2].find(
                "a",
                onclick=lambda onclick: isinstance(onclick, str) and "showRevision" in onclick,
                recursive=False,
            )
            if revision_link is None:
                continue

            onclick = revision_link.get("onclick", "")
            match = re.search(r"showRevision\s*\(\s*event\s*,\s*(\d+)\s*\)", str(onclick))
            if match is None:
                parse_context = _revision_list_parse_context(
                    post,
                    row_index,
                    field="revision_id",
                    value=str(onclick),
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
        if post._revisions is not None:
            return post._revisions

        response = post.thread.site.amc_request_with_retry(
            [
                {
                    "moduleName": "forum/sub/ForumPostRevisionsModule",
                    "postId": post.id,
                }
            ]
        )[0]
        if response is None:
            raise exceptions.UnexpectedException(
                f"Cannot retrieve forum post revisions for site: {post.thread.site.unix_name}, post: {post.id}"
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

        result: dict[int, ForumPostRevisionCollection] = {}
        site = posts[0].thread.site
        target_posts: list[ForumPost] = []
        cached_revisions_by_id: dict[int, ForumPostRevisionCollection] = {}
        for post in posts:
            if post._revisions is not None and post.id not in cached_revisions_by_id:
                cached_revisions_by_id[post.id] = post._revisions

        seen_post_ids: set[int] = set()
        for post in posts:
            if post.id in seen_post_ids:
                continue
            seen_post_ids.add(post.id)
            cached_revisions = cached_revisions_by_id.get(post.id)
            if cached_revisions is not None:
                if cached_revisions.post is post:
                    result[post.id] = cached_revisions
                else:
                    result[post.id] = ForumPostRevisionCollection._copy_for_post(post, cached_revisions)
                continue
            target_posts.append(post)

        # Step 1: Get and parse missing revision lists
        if len(target_posts) > 0:
            responses = site.amc_request_with_retry(
                [
                    {
                        "moduleName": "forum/sub/ForumPostRevisionsModule",
                        "postId": post.id,
                    }
                    for post in target_posts
                ]
            )

            for post, response in zip(target_posts, responses, strict=True):
                if response is None:
                    raise exceptions.UnexpectedException(
                        f"Cannot retrieve forum post revisions for site: {site.unix_name}, post: {post.id}"
                    )
                html = BeautifulSoup(_revision_list_response_body(response, post), "lxml")
                revisions = ForumPostRevisionCollection._parse(post, html)
                result[post.id] = ForumPostRevisionCollection(post=post, revisions=revisions)

        # Step 2: Optionally get HTML content for all revisions
        if with_html:
            all_revisions: list[ForumPostRevision] = []
            all_revisions_by_id: dict[int, list[ForumPostRevision]] = {}
            for collection in result.values():
                for revision in collection:
                    if revision.is_html_acquired():
                        continue
                    if revision.id not in all_revisions_by_id:
                        all_revisions.append(revision)
                        all_revisions_by_id[revision.id] = []
                    all_revisions_by_id[revision.id].append(revision)

            if len(all_revisions) > 0:
                html_responses = site.amc_request_with_retry(
                    [
                        {
                            "moduleName": "forum/sub/ForumPostRevisionModule",
                            "revisionId": revision.id,
                        }
                        for revision in all_revisions
                    ]
                )

                for revision, response in zip(all_revisions, html_responses, strict=True):
                    if response is None:
                        continue
                    data = response.json()
                    revision_html = _revision_html_content(revision, data)
                    for target_revision in all_revisions_by_id[revision.id]:
                        target_revision._html = revision_html

        for post in target_posts:
            post._revisions = result[post.id]

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

        acquired_html_by_id = {revision.id: revision._html for revision in self if revision._html is not None}
        target_revisions: list[ForumPostRevision] = []
        target_revisions_by_id: dict[int, list[ForumPostRevision]] = {}
        for revision in self:
            if revision.is_html_acquired():
                continue
            acquired_html = acquired_html_by_id.get(revision.id)
            if acquired_html is not None:
                revision._html = acquired_html
                continue
            if revision.id not in target_revisions_by_id:
                target_revisions.append(revision)
                target_revisions_by_id[revision.id] = []
            target_revisions_by_id[revision.id].append(revision)

        if len(target_revisions) == 0:
            return self

        responses = self.post.thread.site.amc_request_with_retry(
            [{"moduleName": "forum/sub/ForumPostRevisionModule", "revisionId": r.id} for r in target_revisions]
        )

        for revision, response in zip(target_revisions, responses, strict=True):
            if response is None:
                continue
            data = response.json()
            html = _revision_html_content(revision, data)
            for target_revision in target_revisions_by_id[revision.id]:
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
        self._html = value
