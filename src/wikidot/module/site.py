import re
import sys
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, Optional, cast, overload

import httpx
from bs4 import BeautifulSoup, Tag

if sys.version_info >= (3, 12):
    from typing import Unpack
else:
    from typing_extensions import Unpack

from ..common import exceptions
from ..common.decorators import login_required
from ..common.logger import logger
from ..util.http import sync_get_with_retry
from ..util.parser import odate as odate_parser
from ..util.parser import user as user_parser
from ..util.quick_module import QMCUser, QuickModule
from ..util.stringutil import StringUtil
from .forum_category import ForumCategoryCollection
from .forum_thread import ForumThread, ForumThreadCollection
from .page import Page, PageCollection, PageConstants, SearchPagesQuery, SearchPagesQueryParams
from .page_source import PageSource
from .site_application import SiteApplication
from .site_member import SiteMember

if TYPE_CHECKING:
    from .client import Client
    from .user import AbstractUser, User


class _UnsetPublishParentType:
    pass


_UNSET_PUBLISH_PARENT = _UnsetPublishParentType()


def _printuser_onclick_value(user_elem: Tag) -> str:
    link_elem = user_elem.find("a", recursive=False)
    if isinstance(link_elem, Tag):
        onclick = link_elem.get("onclick")
        if onclick is not None:
            return str(onclick)
    return user_elem.get_text(" ", strip=True)


def _parse_recent_change_user(
    site: "Site",
    user_elem: Tag,
    *,
    page_no: int,
    change_index: int,
) -> "AbstractUser":
    try:
        return user_parser(site.client, user_elem)
    except ValueError as exc:
        raise exceptions.NoElementException(
            "Recent change user is malformed "
            f"for site: {site.unix_name} "
            f"(page={page_no}, change={change_index}, field=changed_by, value={_printuser_onclick_value(user_elem)})"
        ) from exc


def _require_site_invitation_action_status(site: "Site", user: "AbstractUser", event: str, data: dict[str, Any]) -> Any:
    try:
        status = data["status"]
    except KeyError as exc:
        raise exceptions.NoElementException(
            f"Site invitation action response is malformed for site: {site.unix_name}, user: {user.name} "
            f"(id={user.id}, event={event}, field=status)"
        ) from exc

    if status != "ok":
        raise exceptions.WikidotStatusCodeException(
            f"Failed to complete site invitation action for site: {site.unix_name}, user: {user.name}, event: {event}",
            status,
        )
    return status


@dataclass(frozen=True)
class PagePublishResult:
    """
    Result returned by Site.page.publish()

    Attributes
    ----------
    page : Page
        Created or edited page.
    page_id : int
        Public page ID resolved after saving.
    source_matches : bool | None
        True when source verification was requested and matched. None when verification was not requested.
    tags_updated : bool
        Whether the publish call requested a tags update.
    parent_updated : bool
        Whether the publish call requested a parent update.
    metas_updated : bool
        Whether the publish call requested a meta-tag update.
    created : bool
        True when publish created a new page. False when publish edited an existing page.
    operation : Literal["create", "edit"]
        Audit-friendly operation name derived from created.
    url : str
        Page URL derived from the returned page object.
    metadata_update_count : int
        Number of metadata update categories requested by the publish call.
    metadata_updated : bool
        True when any metadata update was requested by the publish call.
    source_verification_requested : bool
        True when source verification was requested by the publish call.
    source_verification_status : Literal["matched", "mismatched", "skipped"]
        Low-cardinality source verification status for audit records.
    source_verified : bool
        True when source verification was requested and matched.
    as_dict : dict[str, str | int | bool | None]
        Audit-friendly dictionary containing publish result status fields.
    """

    page: "Page"
    page_id: int
    source_matches: bool | None
    tags_updated: bool
    parent_updated: bool
    metas_updated: bool
    created: bool = False

    @property
    def metadata_update_count(self) -> int:
        """Number of metadata update categories requested by publish."""
        return sum((self.tags_updated, self.parent_updated, self.metas_updated))

    @property
    def metadata_updated(self) -> bool:
        """Whether publish requested any metadata update."""
        return self.tags_updated or self.parent_updated or self.metas_updated

    @property
    def source_verified(self) -> bool:
        """Whether publish source verification matched."""
        return self.source_matches is True

    @property
    def source_verification_requested(self) -> bool:
        """Whether publish requested source verification."""
        return self.source_matches is not None

    @property
    def source_verification_status(self) -> Literal["matched", "mismatched", "skipped"]:
        """Low-cardinality source verification status for audit records."""
        if self.source_matches is True:
            return "matched"
        if self.source_matches is False:
            return "mismatched"
        return "skipped"

    @property
    def operation(self) -> Literal["create", "edit"]:
        """Create/edit operation name for audit records."""
        return "create" if self.created else "edit"

    @property
    def url(self) -> str:
        """Page URL for audit records."""
        return self.page.get_url()

    def as_dict(self) -> dict[str, str | int | bool | None]:
        """Return a compact audit-friendly representation of this publish result."""
        return {
            "fullname": self.page.fullname,
            "url": self.url,
            "page_id": self.page_id,
            "created": self.created,
            "operation": self.operation,
            "source_matches": self.source_matches,
            "source_verification_requested": self.source_verification_requested,
            "source_verification_status": self.source_verification_status,
            "source_verified": self.source_verified,
            "tags_updated": self.tags_updated,
            "parent_updated": self.parent_updated,
            "metas_updated": self.metas_updated,
            "metadata_update_count": self.metadata_update_count,
            "metadata_updated": self.metadata_updated,
        }


@dataclass(frozen=True)
class PageSourceResult:
    """
    Result returned by Site.pages.iter_sources()

    Attributes
    ----------
    page : Page
        Page associated with the source attempt.
    fullname : str
        Page fullname associated with the source attempt.
    page_id : int | None
        Page ID already associated with the source attempt. None when the page ID is not loaded.
    source : PageSource | None
        Page source when retrieval succeeded.
    wiki_text : str | None
        Page source text when retrieval succeeded. None when retrieval failed.
    error : Exception | None
        Error describing why source retrieval did not produce a source for this page.
    error_type : str | None
        Exception class name when source retrieval failed. None when retrieval succeeded.
    error_message : str | None
        String representation of the error when source retrieval failed. None when retrieval succeeded.
    as_dict : dict[str, str | int | bool | None]
        Ledger-friendly dictionary containing fullname, page_id, ok, wiki_text, error_type, and error_message.
    """

    page: "Page"
    source: PageSource | None
    error: Exception | None = None

    @property
    def ok(self) -> bool:
        """Whether source retrieval succeeded for this page."""
        return self.source is not None and self.error is None

    @property
    def fullname(self) -> str:
        """Page fullname associated with this source result."""
        return self.page.fullname

    @property
    def page_id(self) -> int | None:
        """Page ID associated with this source result when already loaded."""
        return self.page._id

    @property
    def wiki_text(self) -> str | None:
        """Source wiki text when retrieval succeeded."""
        if self.source is None:
            return None
        return self.source.wiki_text

    @property
    def error_message(self) -> str | None:
        """String error message when source retrieval failed."""
        if self.error is None:
            return None
        return str(self.error)

    @property
    def error_type(self) -> str | None:
        """Exception class name when source retrieval failed."""
        if self.error is None:
            return None
        return self.error.__class__.__name__

    def as_dict(self) -> dict[str, str | int | bool | None]:
        """Return a compact ledger-friendly representation of this source result."""
        return {
            "fullname": self.fullname,
            "page_id": self.page_id,
            "ok": self.ok,
            "wiki_text": self.wiki_text,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }


class SitePagesAccessor:
    """
    A class that provides operations on page collections within a site

    Provides operations on multiple pages such as page search functionality.
    Access through the Site.pages property.
    """

    def __init__(self, site: "Site"):
        """
        Initialize method

        Parameters
        ----------
        site : Site
            Parent site instance
        """
        self.site = site

    def search(self, **kwargs: Unpack[SearchPagesQueryParams]) -> "PageCollection":
        """
        Search for pages within a site

        Receives keyword arguments, converts them to a SearchPagesQuery object, and executes the search.

        Parameters
        ----------
        **kwargs : Unpack[SearchPagesQueryParams]
            Search condition keyword arguments. See SearchPagesQueryParams for details.

        Returns
        -------
        PageCollection
            Page collection of search results
        """
        query = SearchPagesQuery(**kwargs)
        return PageCollection.search_pages(self.site, query)

    @staticmethod
    def _normalize_required_tags(required_tags: str | list[str] | None) -> set[str]:
        if required_tags is None:
            return set()
        if isinstance(required_tags, str):
            return set(required_tags.split())
        return set(required_tags)

    def iter_search(
        self,
        required_tags: str | list[str] | None = None,
        **kwargs: Unpack[SearchPagesQueryParams],
    ) -> Iterator["Page"]:
        """
        Iterate through page search results in bounded ListPages chunks

        Receives keyword arguments, converts them to a SearchPagesQuery object, and yields pages while advancing the
        query offset by perPage. Unlike search(), this avoids loading an unbounded result set into memory by default.

        Parameters
        ----------
        required_tags : str | list[str] | None, default None
            Tags that every yielded page must contain after the ListPages result is parsed.
        **kwargs : Unpack[SearchPagesQueryParams]
            Search condition keyword arguments. See SearchPagesQueryParams for details.

        Yields
        ------
        Page
            Matching pages yielded in ListPages order.
        """
        query = SearchPagesQuery(**kwargs)
        offset = query.offset or 0
        per_page = query.perPage or PageConstants.DEFAULT_PER_PAGE
        remaining = query.limit

        if remaining is not None and remaining <= 0:
            return

        required_tag_set = self._normalize_required_tags(required_tags)
        while True:
            batch_limit = per_page if remaining is None or required_tag_set else min(per_page, remaining)
            if batch_limit <= 0:
                return

            batch_kwargs = query.as_dict()
            batch_kwargs["offset"] = offset
            batch_kwargs["perPage"] = per_page
            batch_kwargs["limit"] = batch_limit
            pages = PageCollection.search_pages(self.site, SearchPagesQuery(**batch_kwargs))
            if not pages:
                return

            batch_pages = pages[:batch_limit]
            if required_tag_set:
                batch_pages = [page for page in batch_pages if required_tag_set.issubset(set(page.tags))]

            yield from batch_pages

            yielded_count = len(batch_pages) if required_tag_set else min(len(pages), batch_limit)
            if remaining is not None:
                remaining -= yielded_count
                if remaining <= 0:
                    return
            if len(pages) < batch_limit:
                return
            offset += per_page

    def iter_sources(
        self,
        source_batch_size: int = 25,
        fallback_batch_size: int = 1,
        required_tags: str | list[str] | None = None,
        **kwargs: Unpack[SearchPagesQueryParams],
    ) -> Iterator[PageSourceResult]:
        """
        Iterate through page source results in bounded source batches

        Receives page search keyword arguments, discovers pages with iter_search(), and retrieves source code in
        source_batch_size chunks while yielding one structured result per page.

        Parameters
        ----------
        source_batch_size : int, default 25
            Number of pages to fetch source for in each primary batch.
        fallback_batch_size : int, default 1
            Number of pages to fetch per fallback batch when a primary batch leaves pages without source.
        required_tags : str | list[str] | None, default None
            Tags that every yielded source result page must contain after the ListPages result is parsed.
        **kwargs : Unpack[SearchPagesQueryParams]
            Search condition keyword arguments. See SearchPagesQueryParams for details.

        Yields
        ------
        PageSourceResult
            Structured source success or failure for each matching page.
        """
        if source_batch_size <= 0:
            raise ValueError("source_batch_size must be greater than 0")
        if fallback_batch_size <= 0:
            raise ValueError("fallback_batch_size must be greater than 0")

        batch: list[Page] = []
        for page in self.iter_search(required_tags=required_tags, **kwargs):
            batch.append(page)
            if len(batch) >= source_batch_size:
                yield from self._source_results(batch, fallback_batch_size)
                batch = []

        if batch:
            yield from self._source_results(batch, fallback_batch_size)

    def _get_page_sources_error(self, pages: list[Page]) -> Exception | None:
        try:
            PageCollection(self.site, pages).get_page_sources()
        except Exception as exc:
            return exc
        return None

    def _source_results(self, pages: list[Page], fallback_batch_size: int) -> Iterator[PageSourceResult]:
        source_errors: dict[int, Exception] = {}
        source_error = self._get_page_sources_error(pages)
        if source_error is not None:
            for page in pages:
                if page._source is None:
                    source_errors[id(page)] = source_error

        missing_pages = [page for page in pages if page._source is None]
        if missing_pages:
            for index in range(0, len(missing_pages), fallback_batch_size):
                fallback_pages = missing_pages[index : index + fallback_batch_size]
                for page in fallback_pages:
                    source_errors.pop(id(page), None)
                fallback_error = self._get_page_sources_error(fallback_pages)
                if fallback_error is not None:
                    if len(fallback_pages) == 1:
                        source_errors[id(fallback_pages[0])] = fallback_error
                    else:
                        for page in fallback_pages:
                            if page._source is None:
                                source_errors.pop(id(page), None)
                                page_error = self._get_page_sources_error([page])
                                if page_error is not None:
                                    source_errors[id(page)] = page_error

        for page in pages:
            if page._source is None:
                yield PageSourceResult(
                    page=page,
                    source=None,
                    error=source_errors.get(
                        id(page),
                        exceptions.NotFoundException(
                            f"Cannot find page source for site: {page.site.unix_name}, page: {page.fullname}"
                        ),
                    ),
                )
            else:
                yield PageSourceResult(page=page, source=page._source)


class SitePageAccessor:
    """
    A class that provides operations on individual pages within a site

    Provides individual page operations such as retrieving and creating pages.
    Access through the Site.page property.
    """

    def __init__(self, site: "Site"):
        """
        Initialize method

        Parameters
        ----------
        site : Site
            Parent site instance
        """
        self.site = site

    def get(self, fullname: str, raise_when_not_found: bool = True) -> Optional["Page"]:
        """
        Get a page from its fullname

        Parameters
        ----------
        fullname : str
            Fullname of the page (e.g., "component:scp-173")
        raise_when_not_found : bool, default True
            Whether to raise an exception if the page is not found
            If False, returns None when the page is not found

        Returns
        -------
        Page | None
            Page object, or None if not found

        Raises
        ------
        NotFoundException
            When raise_when_not_found is True and the page is not found
        """
        page = PageCollection.get_by_fullname(self.site, fullname)
        if page is None:
            page = self._get_by_direct_page_id(fullname)
        if page is None:
            if raise_when_not_found:
                raise exceptions.NotFoundException(
                    f"Page is not found for site: {self.site.unix_name}, page: {fullname}"
                )
            return None
        return page

    def _get_by_direct_page_id(self, fullname: str) -> Optional["Page"]:
        if ":" in fullname:
            category, name = fullname.split(":", 1)
        else:
            category, name = "_default", fullname

        now = datetime.now()
        page = Page(
            site=self.site,
            fullname=fullname,
            name=name,
            category=category,
            title="",
            children_count=0,
            comments_count=0,
            size=0,
            rating=0,
            votes_count=0,
            rating_percent=0.0,
            revisions_count=0,
            parent_fullname=None,
            tags=[],
            created_by=PageCollection._current_user_or_placeholder(self.site),
            created_at=now,
            updated_by=PageCollection._current_user_or_placeholder(self.site),
            updated_at=now,
            commented_by=None,
            commented_at=None,
        )
        try:
            _ = page.id
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise
        except exceptions.NotFoundException:
            return None
        return page

    def create(
        self,
        fullname: str,
        title: str = "",
        source: str = "",
        comment: str = "",
        force_edit: bool = False,
    ) -> "Page":
        """
        Create a new page

        Parameters
        ----------
        fullname : str
            Fullname of the page (e.g., "scp-173")
        title : str, default ""
            Title of the page
        source : str, default ""
            Source code of the page (Wikidot markup)
        comment : str, default ""
            Edit comment
        force_edit : bool, default False
            Whether to overwrite if the page already exists

        Returns
        -------
        Page
            Created page object

        Raises
        ------
        TargetErrorException
            When the page already exists and force_edit is False
        """
        self.site.client.login_check()

        if force_edit:
            existing_page = self.get(fullname, raise_when_not_found=False)
            if existing_page is not None:
                return existing_page.edit(title=title, source=source, comment=comment, force_edit=True)

        return Page.create_or_edit(
            site=self.site,
            fullname=fullname,
            title=title,
            source=source,
            comment=comment,
            force_edit=force_edit,
            raise_on_exists=True,
        )

    @staticmethod
    def _resolve_post_save_page_id(page: "Page", attempts: int, interval: float) -> int:
        for attempt in range(attempts):
            try:
                return page.id
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code != 404:
                    raise
                if attempt == attempts - 1:
                    raise exceptions.NotFoundException(
                        "Cannot resolve published page id for "
                        f"site: {page.site.unix_name}, page: {page.fullname} after {attempts} attempts"
                    ) from exc
            except (exceptions.NotFoundException, exceptions.UnexpectedException):
                if attempt == attempts - 1:
                    raise
            if interval > 0:
                time.sleep(interval)

        raise exceptions.NotFoundException("Cannot find page id")

    def publish(
        self,
        fullname: str,
        title: str = "",
        source: str = "",
        comment: str = "",
        tags: list[str] | None = None,
        parent_fullname: str | None | _UnsetPublishParentType = _UNSET_PUBLISH_PARENT,
        metas: dict[str, str] | None = None,
        force_edit: bool = False,
        verify_source: bool = False,
        source_normalizer: Callable[[str], str] | None = None,
        post_save_visibility_attempts: int = 1,
        post_save_visibility_interval: float = 2.0,
    ) -> PagePublishResult:
        """
        Create or edit a page, then optionally update metadata and verify saved source

        Parameters
        ----------
        fullname : str
            Fullname of the page to publish.
        title : str, default ""
            Title to save.
        source : str, default ""
            Wikidot source to save.
        comment : str, default ""
            Edit comment.
        tags : list[str] | None, default None
            Tags to save after the page source. None leaves tags unchanged.
        parent_fullname : str | None, optional
            Parent fullname to set. Passing None clears the parent. Omitting this argument leaves the parent unchanged.
        metas : dict[str, str] | None, default None
            Meta tags to save after the page source. None leaves meta tags unchanged.
        force_edit : bool, default False
            Whether to forcibly release locks by other users.
        verify_source : bool, default False
            Whether to force a fresh ViewSourceModule fetch and compare it with the submitted source.
        source_normalizer : Callable[[str], str] | None, default None
            Optional function applied to both fetched and submitted source before verification.
        post_save_visibility_attempts : int, default 1
            Total attempts to resolve the saved page ID before metadata updates, source verification, and result return.
        post_save_visibility_interval : float, default 2.0
            Seconds to wait between post-save page ID resolution attempts.

        Returns
        -------
        PagePublishResult
            Created or edited page plus publish status fields.

        Raises
        ------
        LoginRequiredException
            When not logged in.
        TargetErrorException
            When the page is locked.
        UnexpectedException
            When source verification is requested and the fetched source does not match.
        WikidotStatusCodeException
            When saving the page or metadata fails.
        """
        if post_save_visibility_attempts < 1:
            raise ValueError("post_save_visibility_attempts must be at least 1")
        if post_save_visibility_interval < 0:
            raise ValueError("post_save_visibility_interval must be non-negative")

        self.site.client.login_check()

        existing_page = self.get(fullname, raise_when_not_found=False)
        if existing_page is None:
            created = True
            page = Page.create_or_edit(
                site=self.site,
                fullname=fullname,
                title=title,
                source=source,
                comment=comment,
                force_edit=force_edit,
                raise_on_exists=True,
            )
        else:
            created = False
            page = existing_page.edit(title=title, source=source, comment=comment, force_edit=force_edit)

        page_id = self._resolve_post_save_page_id(
            page,
            attempts=post_save_visibility_attempts,
            interval=post_save_visibility_interval,
        )

        tags_updated = tags is not None
        parent_updated = parent_fullname is not _UNSET_PUBLISH_PARENT
        metas_updated = metas is not None

        source_matches: bool | None = None
        if verify_source:
            fetched_source = page.refresh_source().wiki_text
            expected_source = source
            if source_normalizer is not None:
                fetched_source = source_normalizer(fetched_source)
                expected_source = source_normalizer(expected_source)
            source_matches = fetched_source == expected_source
            if not source_matches:
                raise exceptions.UnexpectedException(
                    f"Saved source verification failed for site: {self.site.unix_name}, page: {fullname}"
                )

        if tags_updated or parent_updated or metas_updated:
            if parent_updated:
                page.set_metadata(
                    tags=tags,
                    parent_fullname=cast(str | None, parent_fullname),
                    metas=metas,
                )
            else:
                page.set_metadata(tags=tags, metas=metas)

        return PagePublishResult(
            page=page,
            page_id=page_id,
            source_matches=source_matches,
            tags_updated=tags_updated,
            parent_updated=parent_updated,
            metas_updated=metas_updated,
            created=created,
        )


class SiteForumAccessor:
    """
    A class that provides operations on forum functionality within a site

    Provides forum-related functionality such as retrieving forum categories.
    Access through the Site.forum property.
    """

    def __init__(self, site: "Site"):
        """
        Initialize method

        Parameters
        ----------
        site : Site
            Parent site instance
        """
        self.site = site

    @property
    def categories(self) -> "ForumCategoryCollection":
        """
        Get a list of forum categories within the site

        Returns
        -------
        ForumCategoryCollection
            Collection of forum categories
        """
        return ForumCategoryCollection.acquire_all(self.site)


@dataclass
class SiteChange:
    """
    A class representing a single change history entry for a site

    Holds information about changes to pages within a site (creation, editing, deletion, etc.).

    Attributes
    ----------
    site : Site
        Site where the change occurred
    page_fullname : str
        Fullname of the changed page
    page_title : str
        Title of the changed page
    revision_no : int
        Revision number
    changed_by : AbstractUser
        User who made the change
    changed_at : datetime
        Date and time of change
    flags : list[str]
        Change flags ("N"=new, "S"=source change, "T"=title change, "R"=rename, "M"=move, "F"=file, "A"=delete)
    comment : str | None
        Change comment
    """

    site: "Site"
    page_fullname: str
    page_title: str
    revision_no: int
    changed_by: "AbstractUser"
    changed_at: datetime
    flags: list[str]
    comment: str | None

    def __str__(self) -> str:
        """
        String representation of the object

        Returns
        -------
        str
            String representation of the change history
        """
        return (
            f"SiteChange(page_fullname={self.page_fullname}, "
            f"revision_no={self.revision_no}, changed_by={self.changed_by}, "
            f"changed_at={self.changed_at}, flags={self.flags})"
        )


@dataclass
class Site:
    """
    A class representing a Wikidot site

    Provides basic site information and various operational functions for the site.
    Serves as the entry point for accessing features such as pages, forums, and member management.

    Attributes
    ----------
    client : Client
        Client instance
    id : int
        Site ID
    title : str
        Title of the site
    unix_name : str
        UNIX name of the site (used as part of the URL)
    domain : str
        Domain of the site (fully qualified domain name)
    ssl_supported : bool
        Whether the site supports SSL/HTTPS
    """

    client: "Client"

    id: int
    title: str
    unix_name: str
    domain: str
    ssl_supported: bool

    # Accessor属性
    pages: "SitePagesAccessor" = field(init=False, repr=False)
    page: "SitePageAccessor" = field(init=False, repr=False)
    forum: "SiteForumAccessor" = field(init=False, repr=False)

    # キャッシュ属性
    _members: list["SiteMember"] | None = field(init=False, default=None, repr=False)
    _moderators: list["SiteMember"] | None = field(init=False, default=None, repr=False)
    _admins: list["SiteMember"] | None = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        """
        Post-initialization processing

        Initializes instances of each subclass that provides site-related functionality.
        """
        self.pages = SitePagesAccessor(self)
        self.page = SitePageAccessor(self)
        self.forum = SiteForumAccessor(self)

    def __str__(self) -> str:
        """
        String representation of the object

        Returns
        -------
        str
            String representation of the site object
        """
        return f"Site(id={self.id}, title={self.title}, unix_name={self.unix_name})"

    @staticmethod
    def from_unix_name(client: "Client", unix_name: str) -> "Site":
        """
        Get a site object from a UNIX name

        Accesses the site with the specified UNIX name, parses site information, and generates a Site object.

        Parameters
        ----------
        client : Client
            Client instance
        unix_name : str
            UNIX name of the site (e.g., "fondation")

        Returns
        -------
        Site
            Site object

        Raises
        ------
        NotFoundException
            When a site with the specified UNIX name does not exist
        UnexpectedException
            When an error occurs during site information parsing
        """
        StringUtil.validate_site_unix_name(unix_name)

        # サイト情報を取得
        # リダイレクトには従う、リトライ付き
        config = client.amc_client.config
        response = sync_get_with_retry(
            f"http://{unix_name}.wikidot.com",
            timeout=config.request_timeout,
            attempt_limit=config.attempt_limit,
            retry_interval=config.retry_interval,
            max_backoff=config.max_backoff,
            backoff_factor=config.backoff_factor,
            follow_redirects=True,
            raise_for_status=False,
        )

        # サイトが存在しない場合
        if response.status_code == httpx.codes.NOT_FOUND:
            raise exceptions.NotFoundException(f"Site is not found: {unix_name}.wikidot.com")

        # サイトが存在する場合
        source = response.text

        # id : WIKIREQUEST.info.siteId = xxxx;
        id_match = re.search(r"WIKIREQUEST\.info\.siteId\s*=\s*([^;]*);", source)
        if id_match is None:
            raise exceptions.UnexpectedException(f"Cannot find site id: {unix_name}.wikidot.com")
        site_id_text = id_match.group(1).strip()
        try:
            site_id = int(site_id_text)
        except ValueError as exc:
            raise exceptions.NoElementException(
                f"Site ID is malformed for site: {unix_name}.wikidot.com (field=site_id, value={site_id_text})"
            ) from exc

        # title : titleタグ
        title_match = re.search(r"<title>(.*?)</title>", source)
        if title_match is None:
            raise exceptions.UnexpectedException(f"Cannot find site title: {unix_name}.wikidot.com")
        title = title_match.group(1)

        # unix_name : WIKIREQUEST.info.siteUnixName = "xxxx";
        unix_name_match = re.search(r'WIKIREQUEST\.info\.siteUnixName = "(.*?)";', source)
        if unix_name_match is None:
            raise exceptions.UnexpectedException(f"Cannot find site unix_name: {unix_name}.wikidot.com")
        unix_name = unix_name_match.group(1)

        # domain :WIKIREQUEST.info.domain = "xxxx";
        domain_match = re.search(r'WIKIREQUEST\.info\.domain = "(.*?)";', source)
        if domain_match is None:
            raise exceptions.UnexpectedException(f"Cannot find site domain: {unix_name}.wikidot.com")
        domain = domain_match.group(1)

        # SSL対応チェック
        ssl_supported = str(response.url).startswith("https")

        return Site(
            client=client,
            id=site_id,
            title=title,
            unix_name=unix_name,
            domain=domain,
            ssl_supported=ssl_supported,
        )

    @overload
    def amc_request(
        self, bodies: list[dict[str, Any]], return_exceptions: Literal[False] = False
    ) -> tuple[httpx.Response, ...]: ...

    @overload
    def amc_request(
        self, bodies: list[dict[str, Any]], return_exceptions: Literal[True] = ...
    ) -> tuple[httpx.Response | Exception, ...]: ...

    def amc_request(
        self, bodies: list[dict[str, Any]], return_exceptions: bool = False
    ) -> tuple[httpx.Response, ...] | tuple[httpx.Response | Exception, ...]:
        """
        Execute an Ajax Module Connector request for this site

        Parameters
        ----------
        bodies : list[dict]
            List of request bodies
        return_exceptions : bool, default False
            Whether to return or raise exceptions (True: return, False: raise)

        Returns
        -------
        list | Exception
            List of responses, or exceptions if return_exceptions is True
        """
        if len(bodies) == 0:
            return ()

        if return_exceptions:
            return self.client.amc_client.request(bodies, True, self.unix_name, self.ssl_supported)
        else:
            return self.client.amc_client.request(bodies, False, self.unix_name, self.ssl_supported)

    def amc_request_with_retry(
        self,
        bodies: list[dict[str, Any]],
        *,
        batch_size: int | None = None,
        max_retries: int | None = None,
    ) -> tuple[httpx.Response | None, ...]:
        """Execute amc_request with batch splitting and partial failure tolerance.

        Requests are split into batches and failed requests are retried
        up to max_retries times. Still-failed requests return None.

        Parameters
        ----------
        bodies : list[dict]
            List of request bodies
        batch_size : int | None, optional
            Number of requests per batch.
            Defaults to config.retry_batch_size if not specified.
        max_retries : int | None, optional
            Maximum number of retry attempts for failed requests.
            Defaults to config.retry_max_retries if not specified.

        Returns
        -------
        tuple[httpx.Response | None, ...]
            Responses for each body. None for permanently failed requests.
        """
        if batch_size is not None and batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {batch_size}")
        if max_retries is not None and max_retries < 0:
            raise ValueError(f"max_retries must be non-negative, got {max_retries}")
        if len(bodies) == 0:
            return ()

        config = self.client.amc_client.config
        batch_size = batch_size if batch_size is not None else config.retry_batch_size
        max_retries = max_retries if max_retries is not None else config.retry_max_retries

        if batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {batch_size}")
        if max_retries < 0:
            raise ValueError(f"max_retries must be non-negative, got {max_retries}")

        all_results: list[httpx.Response | None] = []

        for batch_start in range(0, len(bodies), batch_size):
            batch = bodies[batch_start : batch_start + batch_size]

            responses = self.amc_request(batch, return_exceptions=True)
            batch_results: list[httpx.Response | None] = []
            failed_indices: list[int] = []

            for i, resp_or_exc in enumerate(responses):
                if isinstance(resp_or_exc, Exception):
                    batch_results.append(None)
                    failed_indices.append(i)
                else:
                    batch_results.append(resp_or_exc)

            for attempt in range(max_retries):
                if not failed_indices:
                    break
                retry_bodies = [batch[i] for i in failed_indices]
                logger.warning(
                    "amc_request_with_retry: %d/%d requests failed, retrying (attempt %d/%d)",
                    len(failed_indices),
                    len(batch),
                    attempt + 1,
                    max_retries,
                )
                retry_responses = self.amc_request(retry_bodies, return_exceptions=True)

                still_failed_indices: list[int] = []
                for j, retry_resp in enumerate(retry_responses):
                    if isinstance(retry_resp, Exception):
                        still_failed_indices.append(failed_indices[j])
                    else:
                        batch_results[failed_indices[j]] = retry_resp
                failed_indices = still_failed_indices

            all_results.extend(batch_results)

        failed_count = sum(1 for r in all_results if r is None)
        if failed_count > 0:
            logger.warning(
                "amc_request_with_retry: %d/%d succeeded (%d failed)",
                len(all_results) - failed_count,
                len(all_results),
                failed_count,
            )

        return tuple(all_results)

    @property
    def applications(self) -> list[SiteApplication]:
        """
        Get pending membership applications to the site

        Returns
        -------
        list[SiteApplication]
            List of membership applications
        """
        return SiteApplication.acquire_all(self)

    @login_required
    def invite_user(self, user: "User", text: str) -> None:
        """
        Invite a user to the site

        Parameters
        ----------
        user : User
            User to invite
        text : str
            Invitation message

        Raises
        ------
        TargetErrorException
            When the user is already invited or already a member
        WikidotStatusCodeException
            When other Wikidot API errors occur
        LoginRequiredException
            When not logged in (by @login_required decorator)
        """
        try:
            response = self.amc_request(
                [
                    {
                        "action": "ManageSiteMembershipAction",
                        "event": "inviteMember",
                        "user_id": user.id,
                        "text": text,
                        "moduleName": "Empty",
                    }
                ]
            )[0]
            _require_site_invitation_action_status(self, user, "inviteMember", response.json())
        except exceptions.WikidotStatusCodeException as e:
            if e.status_code == "already_invited":
                raise exceptions.TargetErrorException(
                    f"User is already invited to {self.unix_name}: {user.name}"
                ) from e
            elif e.status_code == "already_member":
                raise exceptions.TargetErrorException(
                    f"User is already a member of {self.unix_name}: {user.name}"
                ) from e
            else:
                raise e

    @property
    def url(self) -> str:
        """
        Get the URL of the site

        Returns
        -------
        str
            Full URL of the site
        """
        return f"http{'s' if self.ssl_supported else ''}://{self.domain}"

    @property
    def members(self) -> list[SiteMember]:
        """
        Get a list of site members

        Returns
        -------
        list[SiteMember]
            List of site members
        """
        if self._members is None:
            self._members = SiteMember.get(self)
        return self._members

    @property
    def moderators(self) -> list[SiteMember]:
        """
        Get a list of site moderators

        Returns
        -------
        list[SiteMember]
            List of site moderators
        """
        if self._moderators is None:
            self._moderators = SiteMember.get(self, "moderators")
        return self._moderators

    @property
    def admins(self) -> list[SiteMember]:
        """
        Get a list of site administrators

        Returns
        -------
        list[SiteMember]
            List of site administrators
        """
        if self._admins is None:
            self._admins = SiteMember.get(self, "admins")
        return self._admins

    def member_lookup(self, user_name: str, user_id: int | None = None) -> bool:
        """
        Check whether a specified user is a member of the site

        Parameters
        ----------
        user_name : str
            Username to check
        user_id : int | None, default None
            User ID to check (if specified, the ID must also match)

        Returns
        -------
        bool
            True if the user is a site member, False otherwise
        """
        users: list[QMCUser] = QuickModule.member_lookup(self.id, user_name)

        if len(users) == 0:
            return False

        for user in users:
            if user.name.strip() == user_name and (user_id is None or user.id == user_id):
                return True

        return False

    def get_thread(self, thread_id: int) -> ForumThread:
        """
        Get a thread

        Parameters
        ----------
        thread_id : int
            Thread ID

        Returns
        -------
        ForumThread
            Thread object
        """
        return ForumThread.get_from_id(self, thread_id)

    def get_threads(self, thread_ids: list[int]) -> ForumThreadCollection:
        """
        Get multiple threads

        Parameters
        ----------
        thread_ids : list[int]
            List of thread IDs

        Returns
        -------
        list[ForumThread]
            List of thread objects
        """
        return ForumThreadCollection.acquire_from_thread_ids(self, thread_ids)

    def get_recent_changes(self, limit: int | None = None) -> list["SiteChange"]:
        """
        Get recent change history of the site

        Retrieves recent changes to pages within the site (creation, editing, deletion, etc.).

        Parameters
        ----------
        limit : int | None, default None
            Maximum number of entries to retrieve. If None, retrieves only the first page (default count)

        Returns
        -------
        list[SiteChange]
            List of change history (in descending order by date)

        Raises
        ------
        NoElementException
            When HTML element parsing fails
        """
        from ..common.exceptions import NoElementException

        if limit is not None and limit <= 0:
            return []

        changes: list[SiteChange] = []
        per_page = min(limit, 1000) if limit is not None else 1000

        def iter_changes(html: BeautifulSoup, page_no: int) -> Iterator[SiteChange]:
            change_index = 0
            for item in html.select("div.changes-list-item"):
                if item.find_parent("table") is not None:
                    continue

                change_index += 1
                parse_context = f"for site: {self.unix_name} (page={page_no}, change={change_index})"
                table_elem = item.find("table", recursive=False)
                if not isinstance(table_elem, Tag):
                    raise NoElementException(f"Change table element is not found {parse_context}")

                rows = table_elem.find_all("tr", recursive=False)
                if not rows:
                    raise NoElementException(f"Change row element is not found {parse_context}")

                metadata_row = rows[0]

                comment_elem = rows[1].find("td", class_="comments", recursive=False) if len(rows) > 1 else None
                comment = comment_elem.get_text(" ", strip=True) if comment_elem else None
                if comment == "":
                    comment = None

                title_cell = metadata_row.find("td", class_="title", recursive=False)
                title_elem = title_cell.find("a", recursive=False) if isinstance(title_cell, Tag) else None
                if not isinstance(title_elem, Tag):
                    raise NoElementException(f"Title element is not found {parse_context}")

                page_title = title_elem.get_text(" ", strip=True)
                if page_title == "":
                    raise NoElementException(f"Page title is not found {parse_context}")
                href = title_elem.get("href")
                if not isinstance(href, str) or href.strip() == "":
                    raise NoElementException(f"Title href is not found {parse_context}")
                page_fullname = href.strip().strip("/")
                if page_fullname == "":
                    raise NoElementException(f"Page fullname is not found {parse_context}")

                date_cell = metadata_row.find("td", class_="mod-date", recursive=False)
                odate_elem = (
                    date_cell.find("span", class_="odate", recursive=False) if isinstance(date_cell, Tag) else None
                )
                if not isinstance(odate_elem, Tag):
                    raise NoElementException(f"Odate element is not found {parse_context}")
                try:
                    changed_at = odate_parser(odate_elem)
                except ValueError as exc:
                    class_attr = odate_elem.get("class", [])
                    class_values = [class_attr] if isinstance(class_attr, str) else [str(value) for value in class_attr]
                    odate_value = next((value for value in class_values if "time_" in value), " ".join(class_values))
                    raise NoElementException(
                        "Odate value is malformed "
                        f"for site: {self.unix_name} "
                        f"(page={page_no}, change={change_index}, field=changed_at, value={odate_value})"
                    ) from exc

                rev_elem = metadata_row.find("td", class_="revision-no", recursive=False)
                if rev_elem is None:
                    raise NoElementException(f"Revision number element is not found {parse_context}")
                rev_text = rev_elem.get_text()
                rev_match = re.search(r"(\d+)", rev_text)
                if rev_match is None:
                    rev_value = rev_elem.get_text(" ", strip=True)
                    raise NoElementException(
                        "Revision number is not found "
                        f"for site: {self.unix_name} "
                        f"(page={page_no}, change={change_index}, field=revision_no, value={rev_value})"
                    )
                revision_no = int(rev_match.group(1))

                user_cell = metadata_row.find("td", class_="mod-by", recursive=False)
                user_elem = (
                    user_cell.find("span", class_="printuser", recursive=False) if isinstance(user_cell, Tag) else None
                )
                if not isinstance(user_elem, Tag):
                    raise NoElementException(f"User element is not found {parse_context}")
                changed_by = _parse_recent_change_user(
                    self,
                    user_elem,
                    page_no=page_no,
                    change_index=change_index,
                )

                flags_cell = metadata_row.find("td", class_="flags", recursive=False)
                flags_elem = flags_cell.find_all("span", recursive=False) if isinstance(flags_cell, Tag) else []
                flags = [span.get_text().strip() for span in flags_elem]

                yield (
                    SiteChange(
                        site=self,
                        page_fullname=page_fullname,
                        page_title=page_title,
                        revision_no=revision_no,
                        changed_by=changed_by,
                        changed_at=changed_at,
                        flags=flags,
                        comment=comment,
                    )
                )

        def is_in_comment_cell(element: Tag) -> bool:
            for ancestor in element.parents:
                if not isinstance(ancestor, Tag):
                    continue
                if ancestor.name == "td" and "comments" in ancestor.get("class", []):
                    return True
            return False

        def find_structural_pager(html: BeautifulSoup) -> Tag | None:
            for pager in html.select("div.pager"):
                if is_in_comment_cell(pager):
                    continue
                return pager
            return None

        def get_last_page(html: BeautifulSoup) -> int:
            pager = find_structural_pager(html)
            if pager is None:
                return 1

            for pager_link in reversed(pager.select("a")):
                page_text = pager_link.get_text(strip=True)
                if page_text.isdigit():
                    return int(page_text)
            return 1

        def request_body(page_no: int) -> dict[str, Any]:
            return {
                "moduleName": "changes/SiteChangesListModule",
                "perpage": str(per_page),
                "page": page_no,
                "options": "{'all':true}",
            }

        response = self.amc_request_with_retry([request_body(1)])[0]
        if response is None:
            raise exceptions.UnexpectedException(f"Cannot retrieve recent changes for site: {self.unix_name}, page: 1")

        body = response.json().get("body")
        if body is None:
            raise NoElementException(f"Recent changes response body is not found for site: {self.unix_name}, page: 1")
        html = BeautifulSoup(body, "lxml")
        page_changes = list(iter_changes(html, 1))
        if not page_changes:
            return changes

        for change in page_changes:
            changes.append(change)
            if limit is not None and len(changes) >= limit:
                return changes

        last_page = get_last_page(html)
        if last_page <= 1:
            return changes

        page_numbers = list(range(2, last_page + 1))
        if limit is not None:
            remaining = limit - len(changes)
            if remaining <= 0:
                return changes
            page_numbers = page_numbers[: (remaining + per_page - 1) // per_page]

        responses = self.amc_request_with_retry([request_body(page_no) for page_no in page_numbers])
        for page_no, response in zip(page_numbers, responses, strict=True):
            if response is None:
                raise exceptions.UnexpectedException(
                    f"Cannot retrieve recent changes for site: {self.unix_name}, page: {page_no}"
                )

            body = response.json().get("body")
            if body is None:
                raise NoElementException(
                    f"Recent changes response body is not found for site: {self.unix_name}, page: {page_no}"
                )
            html = BeautifulSoup(body, "lxml")
            page_changes = list(iter_changes(html, page_no))
            if not page_changes:
                break

            for change in page_changes:
                changes.append(change)
                if limit is not None and len(changes) >= limit:
                    return changes

        return changes
