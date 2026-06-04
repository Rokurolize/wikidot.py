import html as html_lib
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

import httpx
from bs4 import BeautifulSoup, Tag

if sys.version_info >= (3, 12):
    from typing import TypedDict, Unpack
else:
    from typing_extensions import TypedDict, Unpack

from ..common import exceptions
from ..util.parser import odate as odate_parser
from ..util.parser import user as user_parser
from ..util.requestutil import RequestUtil
from .page_revision import PageRevision, PageRevisionCollection
from .page_source import PageSource, extract_page_source_text
from .page_votes import PageVote, PageVoteCollection

if TYPE_CHECKING:
    from .forum_thread import ForumThread
    from .page_file import PageFileCollection
    from .site import Site
    from .user import User


class _UnsetParentType:
    pass


_UNSET_PARENT = _UnsetParentType()


def _normalize_parent_fullname(parent_fullname: str | None) -> str | None:
    return parent_fullname or None


class PageConstants:
    """
    A class for centrally managing constants used in the page module

    Attributes
    ----------
    DEFAULT_PER_PAGE : int
        Default number of items per page for ListPagesModule
    """

    DEFAULT_PER_PAGE: int = 250


DEFAULT_MODULE_BODY = [
    "fullname",  # ページのフルネーム(str)
    "category",  # カテゴリ(str)
    "name",  # ページ名(str)
    "title",  # タイトル(str)
    "created_at",  # 作成日時(odate element)
    "created_by_linked",  # 作成者(user element)
    "updated_at",  # 更新日時(odate element)
    "updated_by_linked",  # 更新者(user element)
    "commented_at",  # コメント日時(odate element)
    "commented_by_linked",  # コメントしたユーザ(user element)
    "parent_fullname",  # 親ページのフルネーム(str)
    "comments",  # コメント数(int)
    "size",  # サイズ(int)
    "children",  # 子ページ数(int)
    "rating_votes",  # 投票数(int)
    "rating",  # レーティング(int or float)
    "rating_percent",  # 5つ星レーティング(%)
    "revisions",  # リビジョン数(int)
    "tags",  # タグのリスト(list of str)
    "_tags",  # 隠しタグのリスト(list of str)
]


def _parse_revision_row_id(site: "Site", page: "Page", value: object) -> int:
    value_text = str(value)
    raw_id = value_text.removeprefix("revision-row-")
    if value_text == raw_id or not raw_id.isdigit():
        raise exceptions.NoElementException(
            f"Revision ID is malformed for site: {site.unix_name}, page: {page.fullname} "
            f"(id={page.id}, field=revision_row_id, value={value_text})"
        )
    return int(raw_id)


def _parse_revision_number(site: "Site", page: "Page", rev_id: int, value: object) -> int:
    value_text = str(value).strip()
    try:
        return int(value_text.removesuffix("."))
    except ValueError as exc:
        raise exceptions.NoElementException(
            f"Revision number is malformed for site: {site.unix_name}, page: {page.fullname}, "
            f"revision: {rev_id} (id={page.id}, field=revision_number, value={value_text})"
        ) from exc


def _parse_listpages_integer_field(site: "Site", page_name: str, key: str, value: object) -> int:
    value_text = str(value).strip()
    try:
        return int(value_text)
    except ValueError as exc:
        raise exceptions.NoElementException(
            f"ListPages integer field is malformed for site: {site.unix_name}, page: {page_name} "
            f"(field={key}, value={value_text})"
        ) from exc


def _parse_listpages_float_field(site: "Site", page_name: str, key: str, value: object) -> float:
    value_text = str(value).strip()
    try:
        return float(value_text)
    except ValueError as exc:
        raise exceptions.NoElementException(
            f"ListPages float field is malformed for site: {site.unix_name}, page: {page_name} "
            f"(field={key}, value={value_text})"
        ) from exc


def _parse_who_rated_vote_value(site: "Site", page: "Page", value: object) -> int:
    value_text = str(value).strip()
    if value_text == "+":
        return 1
    if value_text == "-":
        return -1
    try:
        return int(value_text)
    except ValueError as exc:
        raise exceptions.NoElementException(
            f"WhoRated vote value is malformed for site: {site.unix_name}, page: {page.fullname} "
            f"(id={page.id}, field=vote_value, value={value_text})"
        ) from exc


def _require_page_edit_lock_field(site: "Site", fullname: str, data: dict[str, Any], field: str) -> Any:
    try:
        return data[field]
    except KeyError as exc:
        raise exceptions.NoElementException(
            f"Page edit lock response is malformed for site: {site.unix_name}, page: {fullname} (field={field})"
        ) from exc


def _require_page_save_status(site: "Site", fullname: str, data: dict[str, Any]) -> Any:
    try:
        return data["status"]
    except KeyError as exc:
        raise exceptions.NoElementException(
            f"Page save response is malformed for site: {site.unix_name}, page: {fullname} (field=status)"
        ) from exc


def _require_page_action_status(site: "Site", page: "Page", event: str, data: dict[str, Any]) -> Any:
    try:
        status = data["status"]
    except KeyError as exc:
        raise exceptions.NoElementException(
            f"Page action response is malformed for site: {site.unix_name}, page: {page.fullname} "
            f"(id={page.id}, event={event}, field=status)"
        ) from exc

    if status != "ok":
        raise exceptions.WikidotStatusCodeException(
            f"Failed to complete page action for site: {site.unix_name}, page: {page.fullname}, event: {event}",
            status,
        )
    return status


def _parse_page_rating_points(site: "Site", page: "Page", event: str, data: dict[str, Any]) -> int:
    try:
        value = data["points"]
    except KeyError as exc:
        raise exceptions.NoElementException(
            f"Page rating response is malformed for site: {site.unix_name}, page: {page.fullname} "
            f"(id={page.id}, event={event}, field=points)"
        ) from exc

    value_text = str(value).strip()
    try:
        return int(value_text)
    except (TypeError, ValueError) as exc:
        raise exceptions.NoElementException(
            f"Page rating response is malformed for site: {site.unix_name}, page: {page.fullname} "
            f"(id={page.id}, event={event}, field=points, value={value_text})"
        ) from exc


def _require_page_metadata_action_status(site: "Site", page: "Page", event: str, data: dict[str, Any]) -> Any:
    try:
        status = data["status"]
    except KeyError as exc:
        raise exceptions.NoElementException(
            f"Page metadata action response is malformed for site: {site.unix_name}, page: {page.fullname} "
            f"(id={page.id}, event={event}, field=status)"
        ) from exc

    if status != "ok":
        raise exceptions.WikidotStatusCodeException(
            f"Failed to set page metadata for site: {site.unix_name}, page: {page.fullname}, event: {event}",
            status,
        )
    return status


class SearchPagesQueryParams(TypedDict, total=False):
    """
    A TypedDict defining page search query parameters

    Used for type definition of keyword arguments in SitePagesAccessor.search()
    and SearchPagesQuery.__init__(). Enables IDE autocomplete and type checking.

    Attributes
    ----------
    pagetype : str
        Page type (e.g., "normal", "admin", etc.). Default: "*"
    category : str
        Category name. Default: "*"
    tags : str | list[str]
        Tags to search for (string or list of strings)
    parent : str
        Parent page name
    link_to : str
        Linked page name
    created_at : str
        Creation date condition (e.g., "> -86400 86400")
    updated_at : str
        Update date condition
    created_by : User | str
        Filter by creator
    rating : str
        Filter by rating value
    votes : str
        Filter by vote count
    name : str
        Filter by page name
    fullname : str
        Filter by fullname (exact match)
    range : str
        Range specification
    order : str
        Sort order (e.g., "created_at desc", "title asc"). Default: "created_at desc"
    offset : int
        Starting position for retrieval. Default: 0
    limit : int
        Limit on number of items to retrieve
    perPage : int
        Number of items displayed per page. Default: 250
    separate : str
        Whether to display separately. Default: "no"
    wrapper : str
        Whether to display wrapper element. Default: "no"
    """

    pagetype: str
    category: str
    tags: "str | list[str]"
    parent: str
    link_to: str
    created_at: str
    updated_at: str
    created_by: "User | str"
    rating: str
    votes: str
    name: str
    fullname: str
    range: str
    order: str
    offset: int
    limit: int
    perPage: int
    separate: str
    wrapper: str


class SearchPagesQuery:
    """
    A class representing a page search query

    Defines various search conditions used for Wikidot page searches.
    Encapsulates query parameters to pass to ListPagesModule.

    Attributes
    ----------
    pagetype : str, default "*"
        Page type (e.g., "normal", "admin", etc.)
    category : str, default "*"
        Category name
    tags : str | list[str] | None, default None
        Tags to search for (string or list of strings)
    parent : str | None, default None
        Parent page name
    link_to : str | None, default None
        Linked page name
    created_at : str | None, default None
        Creation date condition
    updated_at : str | None, default None
        Update date condition
    created_by : User | str | None, default None
        Filter by creator
    rating : str | None, default None
        Filter by rating value
    votes : str | None, default None
        Filter by vote count
    name : str | None, default None
        Filter by page name
    fullname : str | None, default None
        Filter by fullname (exact match)
    range : str | None, default None
        Range specification
    order : str, default "created_at desc"
        Sort order (e.g., "created_at desc", "title asc", etc.)
    offset : int, default 0
        Starting position for retrieval
    limit : int | None, default None
        Limit on number of items to retrieve
    perPage : int, default 250
        Number of items displayed per page
    separate : str, default "no"
        Whether to display separately
    wrapper : str, default "no"
        Whether to display wrapper element

    Raises
    ------
    ValueError
        When invalid keyword arguments are passed
    """

    # 有効なフィールド名のセット
    _VALID_FIELDS = {
        "pagetype",
        "category",
        "tags",
        "parent",
        "link_to",
        "created_at",
        "updated_at",
        "created_by",
        "rating",
        "votes",
        "name",
        "fullname",
        "range",
        "order",
        "offset",
        "limit",
        "perPage",
        "separate",
        "wrapper",
    }

    def __init__(self, **kwargs: Unpack[SearchPagesQueryParams]) -> None:
        """
        Initialize SearchPagesQuery

        Parameters
        ----------
        **kwargs : Unpack[SearchPagesQueryParams]
            Search condition keyword arguments. See SearchPagesQueryParams for details.

        Raises
        ------
        ValueError
            When invalid keyword arguments are included
        """
        # 無効なキーのチェック
        invalid_keys = set(kwargs.keys()) - self._VALID_FIELDS
        if invalid_keys:
            raise ValueError(
                f"Invalid query parameters: {', '.join(sorted(invalid_keys))}. "
                f"Valid parameters are: {', '.join(sorted(self._VALID_FIELDS))}"
            )

        # デフォルト値の設定
        # selecting pages
        self.pagetype: str | None = kwargs.get("pagetype", "*")
        self.category: str | None = kwargs.get("category", "*")
        self.tags: str | list[str] | None = kwargs.get("tags")
        self.parent: str | None = kwargs.get("parent")
        self.link_to: str | None = kwargs.get("link_to")
        self.created_at: str | None = kwargs.get("created_at")
        self.updated_at: str | None = kwargs.get("updated_at")
        self.created_by: User | str | None = kwargs.get("created_by")
        self.rating: str | None = kwargs.get("rating")
        self.votes: str | None = kwargs.get("votes")
        self.name: str | None = kwargs.get("name")
        self.fullname: str | None = kwargs.get("fullname")
        self.range: str | None = kwargs.get("range")

        # ordering
        self.order: str = kwargs.get("order", "created_at desc")

        # pagination
        self.offset: int | None = kwargs.get("offset", 0)
        self.limit: int | None = kwargs.get("limit")
        self.perPage: int | None = kwargs.get("perPage", PageConstants.DEFAULT_PER_PAGE)
        if self.offset is not None and self.offset < 0:
            raise ValueError("offset must be non-negative")
        if self.perPage is not None and self.perPage <= 0:
            raise ValueError("perPage must be positive")
        # layout
        self.separate: str | None = kwargs.get("separate", "no")
        self.wrapper: str | None = kwargs.get("wrapper", "no")

    def as_dict(self) -> dict[str, Any]:
        """
        Convert query parameters to dictionary format

        If tags are in list format, converts them to a space-separated string.
        If created_by is a User object, converts it to the user's Wikidot
        unix name because ListPagesModule expects a scalar form field.

        Returns
        -------
        dict[str, Any]
            Dictionary format parameters for API requests
        """
        res = {k: v for k, v in self.__dict__.items() if v is not None and k in self._VALID_FIELDS}

        if "tags" in res and isinstance(res["tags"], list):
            res["tags"] = " ".join(res["tags"])
        if "created_by" in res and not isinstance(res["created_by"], str):
            user_name = getattr(res["created_by"], "unix_name", None) or getattr(res["created_by"], "name", None)
            if not isinstance(user_name, str) or user_name == "":
                raise ValueError("created_by user must have a name or unix_name")
            res["created_by"] = user_name
        return res


class PageCollection(list["Page"]):
    """
    A class representing a collection of page objects

    Stores multiple page objects and provides functionality for batch operations.
    Consolidates features such as page search, batch retrieval, and batch operations.
    """

    site: "Site"

    @staticmethod
    def _is_inside_listpages_result(element: Tag) -> bool:
        for ancestor in element.parents:
            if not isinstance(ancestor, Tag):
                continue
            if ancestor.name == "div" and "page" in ancestor.get("class", []):
                return True
        return False

    @staticmethod
    def _pager_from_listpages_html(html_body: BeautifulSoup) -> Tag | None:
        for pager in html_body.select("div.pager"):
            if PageCollection._is_inside_listpages_result(pager):
                continue
            return pager
        return None

    def __init__(self, site: Optional["Site"] = None, pages: list["Page"] | None = None):
        """
        Initialize method

        Parameters
        ----------
        site : Site | None, default None
            Site to which pages belong. If None, inferred from the first page
        pages : list[Page] | None, default None
            List of pages to store
        """
        super().__init__(pages or [])

        if site is not None:
            self.site = site
        else:
            self.site = self[0].site

    def __iter__(self) -> Iterator["Page"]:
        """
        An iterator that returns pages in the collection sequentially

        Returns
        -------
        Iterator[Page]
            Iterator of page objects
        """
        return super().__iter__()

    def find(self, fullname: str) -> Optional["Page"]:
        """
        Get a page with the specified fullname

        Parameters
        ----------
        fullname : str
            Fullname of the page to retrieve

        Returns
        -------
        Page | None
            Page with the specified fullname. None if it does not exist
        """
        for page in self:
            if page.fullname == fullname:
                return page
        return None

    @staticmethod
    def _split_fullname(fullname: str) -> tuple[str, str]:
        if ":" in fullname:
            category, name = fullname.split(":", 1)
            return category, name
        return "_default", fullname

    @staticmethod
    def get_by_fullname(site: "Site", fullname: str) -> Optional["Page"]:
        """
        Get a page by fullname.

        Some Wikidot sites do not return default-category pages when
        ListPagesModule is queried with ``fullname``. Prefer the equivalent
        category/name query while keeping the public API based on fullnames.
        """
        category, name = PageCollection._split_fullname(fullname)
        pages = PageCollection.search_pages(site, SearchPagesQuery(category=category, name=name))
        if len(pages) > 0:
            return pages.find(fullname) or pages[0]

        pages = PageCollection.search_pages(site, SearchPagesQuery(fullname=fullname))
        if len(pages) > 0:
            return pages.find(fullname) or pages[0]

        return None

    @staticmethod
    def _current_user_or_placeholder(site: "Site") -> "User":
        from .user import User

        current_user = getattr(site.client, "me", None)
        if isinstance(current_user, User):
            return current_user

        username = getattr(site.client, "username", None)
        return User(
            client=site.client,
            name=username if isinstance(username, str) else None,
            unix_name=None,
            avatar_url=None,
        )

    @staticmethod
    def _parse(site: "Site", html_body: BeautifulSoup) -> "PageCollection":
        """
        Parse ListPagesModule responses and generate a list of page objects

        Parameters
        ----------
        site : Site
            Site to which pages belong
        html_body : BeautifulSoup
            HTML to parse

        Returns
        -------
        PageCollection
            Page collection from parsing results

        Raises
        ------
        NoElementException
            When required elements are not found
        """
        pages = []

        page_container = html_body.body if html_body.body is not None else html_body
        for page_element in page_container.find_all("div", class_="page", recursive=False):
            page_params: dict[str, Any] = {}
            set_container = page_element.find("p", recursive=False)
            if not isinstance(set_container, Tag):
                set_container = page_element
            set_elements = [
                set_element
                for set_element in set_container.find_all("span", class_="set", recursive=False)
                if isinstance(set_element, Tag)
            ]

            # レーティング方式を判定
            is_5star_rating = any(
                "rating" in set_element.get("class", [])
                and set_element.find("span", class_="page-rate-list-pages-start", recursive=False) is not None
                for set_element in set_elements
            )

            # 各値を取得
            for field_index, set_element in enumerate(set_elements, start=1):
                key_element = set_element.find("span", class_="name", recursive=False)
                if key_element is None:
                    page_name = page_params.get("fullname", "unknown")
                    raise exceptions.NoElementException(
                        "Cannot find key element in set "
                        f"for site: {site.unix_name}, page: {page_name}, field: {field_index}"
                    )
                key = key_element.text.strip()
                value_element = set_element.find("span", class_="value", recursive=False)

                if value_element is None:
                    value: Any = None

                elif key in ["created_at", "updated_at", "commented_at"]:
                    odate_element = (
                        value_element.find("span", class_="odate", recursive=False)
                        if isinstance(value_element, Tag)
                        else None
                    )
                    if not isinstance(odate_element, Tag):
                        value = None
                    else:
                        value = odate_parser(odate_element)

                elif key in [
                    "created_by_linked",
                    "updated_by_linked",
                    "commented_by_linked",
                ]:
                    printuser_element = (
                        value_element.find("span", class_="printuser", recursive=False)
                        if isinstance(value_element, Tag)
                        else None
                    )
                    if not isinstance(printuser_element, Tag):
                        value = None
                    else:
                        value = user_parser(site.client, printuser_element)

                elif key in ["tags", "_tags"]:
                    value = value_element.text.split()

                elif key in ["rating_votes", "comments", "size", "children", "revisions"]:
                    page_name = str(page_params.get("fullname", "unknown"))
                    value = _parse_listpages_integer_field(site, page_name, key, value_element.text)

                elif key in ["rating"]:
                    page_name = str(page_params.get("fullname", "unknown"))
                    if is_5star_rating:
                        value = _parse_listpages_float_field(site, page_name, key, value_element.text)
                    else:
                        value = _parse_listpages_integer_field(site, page_name, key, value_element.text)

                elif key in ["rating_percent"]:
                    if is_5star_rating:
                        page_name = str(page_params.get("fullname", "unknown"))
                        percent_text = value_element.text.strip().removesuffix("%")
                        value = _parse_listpages_float_field(site, page_name, key, percent_text) / 100
                    else:
                        value = None

                else:
                    value = value_element.get_text(" ", strip=True)

                # keyを変換
                if "_linked" in key:
                    key = key.replace("_linked", "")
                elif key in ["comments", "children", "revisions"]:
                    key = f"{key}_count"
                elif key in ["rating_votes"]:
                    key = "votes_count"

                page_params[key] = value

            # タグのリストを統合
            for key in ["tags", "_tags"]:
                if key not in page_params or page_params[key] is None:
                    page_params[key] = []

            page_params["tags"] = page_params["tags"] + page_params["_tags"]
            del page_params["_tags"]

            # ページオブジェクトを作成
            pages.append(Page(site, **page_params))

        return PageCollection(site, pages)

    @staticmethod
    def _request_listpages_page(site: "Site", query_dict: dict[str, Any], offset: int | None) -> httpx.Response:
        config = site.client.amc_client.config
        max_retries = getattr(config, "retry_max_retries", 3)
        if not isinstance(max_retries, int):
            max_retries = 3
        if max_retries < 0:
            raise ValueError(f"max_retries must be non-negative, got {max_retries}")

        last_exception: Exception | None = None
        for _ in range(max_retries + 1):
            try:
                response_or_exception = site.amc_request([query_dict], return_exceptions=True)[0]
            except Exception as exc:
                response_or_exception = exc

            if not isinstance(response_or_exception, Exception):
                return response_or_exception

            if isinstance(response_or_exception, exceptions.ForbiddenException):
                raise response_or_exception

            if isinstance(response_or_exception, exceptions.WikidotStatusCodeException):
                if response_or_exception.status_code == "not_ok":
                    raise exceptions.ForbiddenException("Failed to get pages, target site may be private") from (
                        response_or_exception
                    )
                if response_or_exception.status_code != "try_again":
                    raise response_or_exception

            last_exception = response_or_exception

        raise exceptions.UnexpectedException(
            f"Failed to get ListPages page for site: {site.unix_name}, offset: {offset}"
        ) from last_exception

    @staticmethod
    def _listpages_response_body(site: "Site", response: httpx.Response, offset: int | None) -> str:
        body = response.json().get("body")
        if body is None:
            raise exceptions.NoElementException(
                f"ListPages response body is not found for site: {site.unix_name}, offset: {offset}"
            )
        return body

    @staticmethod
    def search_pages(site: "Site", query: SearchPagesQuery | None = None) -> "PageCollection":
        """
        Search for pages within a site

        Searches for pages within a site based on the specified query and returns the results.
        Executes the search using Wikidot's "ListPagesModule".

        Parameters
        ----------
        site : Site
            Site to search
        query : SearchPagesQuery | None, default None
            Search conditions. If None, default search conditions are used.

        Returns
        -------
        PageCollection
            Page collection of search results

        Raises
        ------
        ForbiddenException
            When access is denied on a private site
        WikidotStatusCodeException
            When other API errors occur
        NoElementException
            When page information cannot be extracted from the response
        """
        if query is None:
            query = SearchPagesQuery()
        if query.limit is not None and query.limit <= 0:
            return PageCollection(site, [])

        # 初回実行
        query_dict = query.as_dict()
        query_dict["moduleName"] = "list/ListPagesModule"
        query_dict["module_body"] = (
            '[[div class="page"]]\n'
            + "".join(
                [
                    f'[[span class="set {key}"]]'
                    f'[[span class="name"]] {key} [[/span]]'
                    f'[[span class="value"]] %%{key}%% [[/span]]'
                    f"[[/span]]"
                    for key in DEFAULT_MODULE_BODY
                ]
            )
            + "\n[[/div]]"
        )

        response = PageCollection._request_listpages_page(site, query_dict, query.offset)

        body = PageCollection._listpages_response_body(site, response, query.offset)

        first_page_html_body = BeautifulSoup(body, "lxml")

        total = 1
        html_bodies = [first_page_html_body]
        pager = PageCollection._pager_from_listpages_html(first_page_html_body)
        if pager is not None:
            for pager_target in reversed(pager.select("span.target")):
                pager_link = pager_target.select_one("a")
                page_text = (pager_link or pager_target).get_text(strip=True)
                if page_text.isdigit():
                    total = int(page_text)
                    break

        if total > 1:
            request_bodies = []
            base_offset = query.offset or 0
            per_page = query.perPage or PageConstants.DEFAULT_PER_PAGE
            page_count = total
            if query.limit is not None:
                remaining_limit = query.limit - per_page
                page_count = 1
                if remaining_limit > 0:
                    page_count += (remaining_limit + per_page - 1) // per_page
                page_count = min(total, page_count)

            for i in range(1, page_count):
                _query_dict = query_dict.copy()
                _query_dict["offset"] = base_offset + i * per_page
                request_bodies.append(_query_dict)

            if request_bodies:
                responses = site.amc_request_with_retry(request_bodies)
                for index, additional_response in enumerate(responses):
                    offset = request_bodies[index].get("offset")
                    if additional_response is None:
                        raise exceptions.UnexpectedException(
                            f"Failed to get ListPages page for site: {site.unix_name}, offset: {offset}"
                        )
                    body = PageCollection._listpages_response_body(site, additional_response, offset)
                    html_bodies.append(BeautifulSoup(body, "lxml"))

        pages: list[Page] = []
        for html_body in html_bodies:
            pages.extend(PageCollection._parse(site, html_body))

        if query.limit is not None:
            pages = pages[: query.limit]

        return PageCollection(site, pages)

    @staticmethod
    def _acquire_page_ids(site: "Site", pages: list["Page"]) -> list["Page"]:
        """
        Internal method to retrieve page IDs

        Batch retrieves unacquired page IDs. Accesses pages with norender/noredirect options
        and extracts IDs from page source.

        Parameters
        ----------
        site : Site
            Site to which pages belong
        pages : list[Page]
            List of target pages

        Returns
        -------
        list[Page]
            List of pages with updated ID information

        Raises
        ------
        NotFoundException
            When page ID is not found
        UnexpectedException
            When response type is unexpected
        """
        acquired_ids_by_url: dict[str, int] = {}
        for page in pages:
            if page._id is not None:
                request_url = f"{page.get_url()}/norender/true/noredirect/true"
                acquired_ids_by_url.setdefault(request_url, page._id)

        target_pages: list[Page] = []
        for page in pages:
            if page.is_id_acquired():
                continue
            request_url = f"{page.get_url()}/norender/true/noredirect/true"
            acquired_id = acquired_ids_by_url.get(request_url)
            if acquired_id is not None:
                page.id = acquired_id
                continue
            target_pages.append(page)

        # なければ終了
        if len(target_pages) == 0:
            return pages

        target_pages_by_url: dict[str, list[Page]] = {}
        for page in target_pages:
            request_url = f"{page.get_url()}/norender/true/noredirect/true"
            target_pages_by_url.setdefault(request_url, []).append(page)

        # norender, noredirectでアクセス
        request_urls = list(target_pages_by_url)
        responses = RequestUtil.request(site.client, "GET", request_urls)

        # "WIKIREQUEST.info.pageId = xxx;"の値をidに設定
        for index, response in enumerate(responses):
            target_pages_for_url = target_pages_by_url[request_urls[index]]
            if not isinstance(response, httpx.Response):
                raise exceptions.UnexpectedException(
                    f"Unexpected response type for site: {site.unix_name}, "
                    f"page: {target_pages_for_url[0].fullname}, type: {type(response)}"
                )
            source = response.text

            id_match = re.search(r"WIKIREQUEST\.info\.pageId = (\d+);", source)
            if id_match is None:
                raise exceptions.NotFoundException(
                    f"Cannot find page id for site: {site.unix_name}, page: {target_pages_for_url[0].fullname}"
                )
            page_id = int(id_match.group(1))
            for page in target_pages_for_url:
                page.id = page_id

        return pages

    def get_page_ids(self) -> "PageCollection":
        """
        Get IDs for all pages in the collection

        Batch retrieves IDs for pages that do not have IDs set.

        Returns
        -------
        PageCollection
            Self (for method chaining)
        """
        PageCollection._acquire_page_ids(self.site, self)
        return self

    @staticmethod
    def _acquire_page_sources(site: "Site", pages: list["Page"]) -> list["Page"]:
        """
        Internal method to retrieve page sources

        Batch retrieves source code (Wikidot markup) for specified pages.

        Parameters
        ----------
        site : Site
            Site to which pages belong
        pages : list[Page]
            List of target pages

        Returns
        -------
        list[Page]
            List of pages with updated source information

        Raises
        ------
        NoElementException
            When source elements are not found
        """
        target_pages = [page for page in pages if page._source is None]
        if len(target_pages) == 0:
            return pages

        PageCollection._acquire_page_ids(site, target_pages)
        acquired_source_text_by_id = {
            page.id: page._source.wiki_text for page in pages if page._source is not None and page._id is not None
        }
        target_pages_by_id: dict[int, list[Page]] = {}
        for page in target_pages:
            acquired_source_text = acquired_source_text_by_id.get(page.id)
            if acquired_source_text is not None:
                page.source = PageSource(page, acquired_source_text)
                continue
            target_pages_by_id.setdefault(page.id, []).append(page)

        if len(target_pages_by_id) == 0:
            return pages

        responses = site.amc_request_with_retry(
            [{"moduleName": "viewsource/ViewSourceModule", "page_id": page_id} for page_id in target_pages_by_id]
        )

        source_error: exceptions.NoElementException | None = None
        for page_id, response in zip(target_pages_by_id, responses, strict=True):
            if response is None:
                continue
            target_pages_for_id = target_pages_by_id[page_id]
            body = response.json().get("body")
            if body is None:
                if source_error is None:
                    first_page = target_pages_for_id[0]
                    source_error = exceptions.NoElementException(
                        f"Page source response body is not found for site: {site.unix_name}, "
                        f"page: {first_page.fullname} (id={first_page.id})"
                    )
                continue
            # nbspをスペースに置換
            body = body.replace("&nbsp;", " ")
            html = BeautifulSoup(body, "lxml")
            source_element = html.select_one("div.page-source")
            if source_element is None:
                if source_error is None:
                    first_page = target_pages_for_id[0]
                    source_error = exceptions.NoElementException(
                        f"Cannot find source element for site: {site.unix_name}, page: {first_page.fullname} "
                        f"(id={first_page.id})"
                    )
                continue
            source = extract_page_source_text(source_element)
            for page in target_pages_for_id:
                page.source = PageSource(page, source)
        if source_error is not None:
            raise source_error
        return pages

    def get_page_sources(self) -> "PageCollection":
        """
        Get source code for all pages in the collection

        Batch retrieves source code (Wikidot markup) for pages and sets the source property for each page.

        Returns
        -------
        PageCollection
            Self (for method chaining)
        """
        PageCollection._acquire_page_sources(self.site, self)
        return self

    @staticmethod
    def _acquire_page_revisions(site: "Site", pages: list["Page"]) -> list["Page"]:
        """
        Internal method to retrieve page revision history

        Batch retrieves revisions (edit history) for specified pages.

        Parameters
        ----------
        site : Site
            Site to which pages belong
        pages : list[Page]
            List of target pages

        Returns
        -------
        list[Page]
            List of pages with updated revision information

        Raises
        ------
        NoElementException
            When required elements are not found
        """
        target_pages = [page for page in pages if page._revisions is None]
        if len(target_pages) == 0:
            return pages

        PageCollection._acquire_page_ids(site, target_pages)

        def clone_revisions(page: Page, revisions: PageRevisionCollection) -> PageRevisionCollection:
            cloned_revisions = []
            for revision in revisions:
                cloned_revision = PageRevision(
                    page=page,
                    id=revision.id,
                    rev_no=revision.rev_no,
                    created_by=revision.created_by,
                    created_at=revision.created_at,
                    comment=revision.comment,
                )
                if revision._source is not None:
                    cloned_revision._source = PageSource(page, revision._source.wiki_text)
                cloned_revision._html = revision._html
                cloned_revisions.append(cloned_revision)
            return PageRevisionCollection(page, cloned_revisions)

        acquired_revisions_by_id: dict[int, PageRevisionCollection] = {}
        for page in pages:
            if page._id is not None and page._revisions is not None:
                acquired_revisions_by_id[page.id] = page._revisions

        target_pages_by_id: dict[int, list[Page]] = {}
        for page in target_pages:
            acquired_revisions = acquired_revisions_by_id.get(page.id)
            if acquired_revisions is not None:
                page.revisions = clone_revisions(page, acquired_revisions)
                continue
            target_pages_by_id.setdefault(page.id, []).append(page)

        if len(target_pages_by_id) == 0:
            return pages

        responses = site.amc_request_with_retry(
            [
                {
                    "moduleName": "history/PageRevisionListModule",
                    "page_id": page_id,
                    "options": {"all": True},
                    "perpage": 100000000,  # pagerを使わずに全て取得
                }
                for page_id in target_pages_by_id
            ]
        )

        for page_id, response in zip(target_pages_by_id, responses, strict=True):
            if response is None:
                continue
            target_pages_for_id = target_pages_by_id[page_id]
            first_page = target_pages_for_id[0]
            body = response.json().get("body")
            if body is None:
                raise exceptions.NoElementException(
                    f"Page revision list response body is not found for site: {site.unix_name}, "
                    f"page: {first_page.fullname} (id={first_page.id})"
                )
            body_html = BeautifulSoup(body, "lxml")
            parsed_revisions: list[tuple[int, int, Any, datetime, str]] = []
            for rev_element in body_html.select("table.page-history > tr[id^=revision-row-]"):
                rev_id = _parse_revision_row_id(site, first_page, rev_element["id"])

                tds = [
                    td_element
                    for td_element in rev_element.find_all("td", recursive=False)
                    if isinstance(td_element, Tag)
                ]
                if len(tds) < 7:
                    raise exceptions.NoElementException(
                        f"Cannot find revision cells for site: {site.unix_name}, "
                        f"page: {first_page.fullname}, revision: {rev_id}"
                    )
                rev_no = _parse_revision_number(site, first_page, rev_id, tds[0].text)
                created_by_elem = tds[4].find("span", class_="printuser", recursive=False)
                if not isinstance(created_by_elem, Tag):
                    raise exceptions.NoElementException(
                        f"Cannot find created by element for site: {site.unix_name}, "
                        f"page: {first_page.fullname}, revision: {rev_id}"
                    )
                created_by = user_parser(site.client, created_by_elem)

                created_at_elem = tds[5].find("span", class_="odate", recursive=False)
                if not isinstance(created_at_elem, Tag):
                    raise exceptions.NoElementException(
                        f"Cannot find created at element for site: {site.unix_name}, "
                        f"page: {first_page.fullname}, revision: {rev_id}"
                    )
                created_at = odate_parser(created_at_elem)

                comment = tds[6].get_text(" ", strip=True)
                parsed_revisions.append((rev_id, rev_no, created_by, created_at, comment))

            for page in target_pages_for_id:
                page.revisions = PageRevisionCollection(
                    page,
                    [
                        PageRevision(
                            page=page,
                            id=rev_id,
                            rev_no=rev_no,
                            created_by=created_by,
                            created_at=created_at,
                            comment=comment,
                        )
                        for rev_id, rev_no, created_by, created_at, comment in parsed_revisions
                    ],
                )

        return pages

    def get_page_revisions(self) -> "PageCollection":
        """
        Get revision history for all pages in the collection

        Batch retrieves revisions (edit history) for pages and sets the revisions property for each page.

        Returns
        -------
        PageCollection
            Self (for method chaining)
        """
        PageCollection._acquire_page_revisions(self.site, self)
        return self

    @staticmethod
    def _acquire_page_votes(site: "Site", pages: list["Page"]) -> list["Page"]:
        """
        Internal method to retrieve vote information for pages

        Batch retrieves vote (rating) information for specified pages.

        Parameters
        ----------
        site : Site
            Site to which pages belong
        pages : list[Page]
            List of target pages

        Returns
        -------
        list[Page]
            List of pages with updated vote information

        Raises
        ------
        UnexpectedException
            When the number of user elements and vote value elements do not match
        """
        target_pages = [page for page in pages if page._votes is None]
        if len(target_pages) == 0:
            return pages

        PageCollection._acquire_page_ids(site, target_pages)

        def clone_votes(page: Page, votes: PageVoteCollection) -> PageVoteCollection:
            return PageVoteCollection(page, [PageVote(page, vote.user, vote.value) for vote in votes])

        acquired_votes_by_id: dict[int, PageVoteCollection] = {}
        for page in pages:
            if page._id is not None and page._votes is not None:
                acquired_votes_by_id[page.id] = page._votes

        target_pages_by_id: dict[int, list[Page]] = {}
        for page in target_pages:
            acquired_votes = acquired_votes_by_id.get(page.id)
            if acquired_votes is not None:
                page._votes = clone_votes(page, acquired_votes)
                continue
            target_pages_by_id.setdefault(page.id, []).append(page)

        if len(target_pages_by_id) == 0:
            return pages

        responses = site.amc_request_with_retry(
            [{"moduleName": "pagerate/WhoRatedPageModule", "pageId": page_id} for page_id in target_pages_by_id]
        )

        for page_id, response in zip(target_pages_by_id, responses, strict=True):
            if response is None:
                continue
            body = response.json().get("body")
            if body is None:
                first_page = target_pages_by_id[page_id][0]
                raise exceptions.NoElementException(
                    f"Page vote response body is not found for site: {site.unix_name}, "
                    f"page: {first_page.fullname} (id={first_page.id})"
                )
            html = BeautifulSoup(body, "lxml")
            vote_container: Tag | None = None
            for element in html.find_all("div"):
                if not isinstance(element, Tag):
                    continue
                style = element.get("style")
                if isinstance(style, str) and "column-count" in style:
                    vote_container = element
                    break
            user_elems: list[Tag] = []
            value_elems: list[Tag] = []
            if vote_container is not None:
                for span in vote_container.find_all("span", recursive=False):
                    if not isinstance(span, Tag):
                        continue
                    classes = span.get("class", [])
                    if isinstance(classes, str):
                        class_names = [classes]
                    elif isinstance(classes, list):
                        class_names = classes
                    else:
                        class_names = []
                    if "printuser" in class_names:
                        user_elems.append(span)
                        continue
                    style = span.get("style")
                    if isinstance(style, str) and style.lstrip().startswith("color"):
                        value_elems.append(span)

            if len(user_elems) != len(value_elems):
                first_page = target_pages_by_id[page_id][0]
                raise exceptions.UnexpectedException(
                    "User and value count mismatch for site: "
                    f"{site.unix_name}, page: {first_page.fullname} "
                    f"(users={len(user_elems)}, values={len(value_elems)})"
                )

            users = [user_parser(site.client, user_elem) for user_elem in user_elems]
            first_page = target_pages_by_id[page_id][0]
            values = [_parse_who_rated_vote_value(site, first_page, value.text) for value in value_elems]

            for page in target_pages_by_id[page_id]:
                votes = [PageVote(page, user, vote) for user, vote in zip(users, values, strict=True)]
                page._votes = PageVoteCollection(page, votes)

        return pages

    def get_page_votes(self) -> "PageCollection":
        """
        Get vote information for all pages in the collection

        Batch retrieves vote (rating) information for pages and sets the votes property for each page.

        Returns
        -------
        PageCollection
            Self (for method chaining)
        """
        PageCollection._acquire_page_votes(self.site, self)
        return self

    @staticmethod
    def _acquire_page_files(site: "Site", pages: list["Page"]) -> list["Page"]:
        """
        Internal method to retrieve file attachments for pages

        Batch retrieves file attachments for specified pages.

        Parameters
        ----------
        site : Site
            Site to which pages belong
        pages : list[Page]
            List of target pages

        Returns
        -------
        list[Page]
            List of pages with updated file information
        """
        target_pages = [page for page in pages if page._files is None]
        if len(target_pages) == 0:
            return pages

        PageCollection._acquire_page_ids(site, target_pages)

        from .page_file import PageFileCollection

        def clone_files(page: Page, files: PageFileCollection) -> PageFileCollection:
            file_fields = [(file.id, file.name, file.url, file.mime_type, file.size) for file in files]
            return PageFileCollection(page=page, files=PageFileCollection._build_page_files(page, file_fields))

        acquired_files_by_id: dict[int, PageFileCollection] = {}
        for page in pages:
            if page._id is not None and page._files is not None:
                acquired_files_by_id[page.id] = page._files

        target_pages_by_id: dict[int, list[Page]] = {}
        for page in target_pages:
            acquired_files = acquired_files_by_id.get(page.id)
            if acquired_files is not None:
                page._files = clone_files(page, acquired_files)
                continue
            target_pages_by_id.setdefault(page.id, []).append(page)

        if len(target_pages_by_id) == 0:
            return pages

        responses = site.amc_request_with_retry(
            [{"moduleName": "files/PageFilesModule", "page_id": page_id} for page_id in target_pages_by_id]
        )

        for page_id, response in zip(target_pages_by_id, responses, strict=True):
            first_page = target_pages_by_id[page_id][0]
            if response is None:
                continue
            body = response.json().get("body")
            if body is None:
                raise exceptions.NoElementException(
                    f"Page file response body is not found for site: {site.unix_name}, "
                    f"page: {first_page.fullname} (id={first_page.id})"
                )
            html = BeautifulSoup(body, "lxml")
            context = f"for site: {site.unix_name}, page: {first_page.fullname}"
            file_fields = PageFileCollection._parse_file_fields_from_html(site.url, html, context=context)
            for page in target_pages_by_id[page_id]:
                files = PageFileCollection._build_page_files(page, file_fields)
                page._files = PageFileCollection(page=page, files=files)

        return pages

    def get_page_files(self) -> "PageCollection":
        """
        Get file attachments for all pages in the collection

        Batch retrieves file attachments for pages and sets the files property for each page.

        Returns
        -------
        PageCollection
            Self (for method chaining)
        """
        PageCollection._acquire_page_files(self.site, self)
        return self


@dataclass
class Page:
    """
    A class representing a Wikidot page

    Provides information and operation functions for a single page within a Wikidot site.
    Manages page basic information, metadata, history, ratings, etc.

    Attributes
    ----------
    site : Site
        Site where the page exists
    fullname : str
        Fullname of the page (e.g., "component:scp-173")
    name : str
        Page name (e.g., "scp-173")
    category : str
        Category (e.g., "component")
    title : str
        Title of the page
    children_count : int
        Number of child pages
    comments_count : int
        Number of comments
    size : int
        Size of the page (in bytes)
    rating : int | float
        Rating (int for +/- rating, float for 5-star rating)
    votes_count : int
        Number of votes
    rating_percent : float
        Percentage value in 5-star rating system (0.0 to 1.0)
    revisions_count : int
        Number of revisions (edit history)
    parent_fullname : str | None
        Fullname of parent page (None if no parent)
    tags : list[str]
        List of tags attached
    created_by : User
        Creator of the page
    created_at : datetime
        Date and time the page was created
    updated_by : User
        Last updater
    updated_at : datetime
        Last update date and time
    commented_by : User | None
        User who last commented (None if no comments)
    commented_at : datetime | None
        Date and time of last comment (None if no comments)
    _id : int | None
        Page ID (internal identifier)
    _source : PageSource | None
        Source code of the page (retrieved on request)
    _revisions : PageRevisionCollection | None
        Revision history of the page (retrieved on request)
    _votes : PageVoteCollection | None
        Vote information for the page (retrieved on request)
    _metas : dict[str, str] | None
        Meta tag information for the page (retrieved on request)
    """

    site: "Site"
    fullname: str
    name: str
    category: str
    title: str
    children_count: int
    comments_count: int
    size: int
    rating: int | float
    votes_count: int
    rating_percent: float
    revisions_count: int
    parent_fullname: str | None
    tags: list[str]
    created_by: "User"
    created_at: datetime
    updated_by: "User"
    updated_at: datetime
    commented_by: Optional["User"]
    commented_at: datetime | None
    _id: int | None = None
    _source: PageSource | None = None
    _revisions: PageRevisionCollection | None = None
    _votes: PageVoteCollection | None = None
    _metas: dict[str, str] | None = None
    _discussion: Optional["ForumThread"] = None
    _discussion_checked: bool = False
    _files: Optional["PageFileCollection"] = None

    def get_url(self) -> str:
        """
        Get the full URL of the page

        Generates the full page URL from the site URL and page name.

        Returns
        -------
        str
            Full URL of the page
        """
        return f"{self.site.url}/{self.fullname}"

    @property
    def id(self) -> int:
        """
        Get the page ID

        Automatically performs retrieval processing if the ID has not been acquired.

        Returns
        -------
        int
            Page ID

        Raises
        ------
        NotFoundException
            When the page ID is not found
        """
        if not self.is_id_acquired():
            PageCollection(self.site, [self]).get_page_ids()

        if self._id is None:
            raise exceptions.NotFoundException(
                f"Cannot find page id for site: {self.site.unix_name}, page: {self.fullname}"
            )

        return self._id

    @id.setter
    def id(self, value: int) -> None:
        """
        Set the page ID

        Parameters
        ----------
        value : int
            Page ID to set
        """
        self._id = value

    def is_id_acquired(self) -> bool:
        """
        Check whether the page ID has already been acquired

        Returns
        -------
        bool
            True if the ID has been acquired, False if not acquired
        """
        return self._id is not None

    def _source_not_found_exception(self) -> exceptions.NotFoundException:
        return exceptions.NotFoundException(
            f"Cannot find page source for site: {self.site.unix_name}, page: {self.fullname}"
        )

    @property
    def source(self) -> PageSource:
        """
        Get the source code of the page

        Automatically performs retrieval processing if the source code has not been acquired.

        Returns
        -------
        PageSource
            Source code object of the page

        Raises
        ------
        NotFoundException
            When the page source is not found
        """
        if self._source is None:
            PageCollection(self.site, [self]).get_page_sources()

        if self._source is None:
            raise self._source_not_found_exception()

        return self._source

    @source.setter
    def source(self, value: PageSource) -> None:
        """
        Set the source code of the page

        Parameters
        ----------
        value : PageSource
            Source code object to set
        """
        self._source = value

    def refresh_source(self) -> PageSource:
        """
        Force retrieval of the current remote source code

        Returns
        -------
        PageSource
            Freshly retrieved source code object of the page

        Raises
        ------
        NotFoundException
            When the page source is not found
        """
        self._source = None
        PageCollection(self.site, [self]).get_page_sources()

        if self._source is None:
            raise self._source_not_found_exception()

        return self._source

    @property
    def revisions(self) -> PageRevisionCollection:
        """
        Get the revision history of the page

        Automatically performs retrieval processing if the revision history has not been acquired.

        Returns
        -------
        PageRevisionCollection
            Revision history collection of the page

        Raises
        ------
        NotFoundException
            When the revision history is not found
        """
        if self._revisions is None:
            PageCollection(self.site, [self]).get_page_revisions()

        if self._revisions is None:
            raise exceptions.NotFoundException(
                f"Cannot find page revisions for site: {self.site.unix_name}, page: {self.fullname}"
            )

        return self._revisions

    @revisions.setter
    def revisions(self, value: list["PageRevision"] | PageRevisionCollection) -> None:
        """
        Set the revision history of the page

        Parameters
        ----------
        value : list[PageRevision] | PageRevisionCollection
            List or collection of revisions to set
        """
        if isinstance(value, list):
            self._revisions = PageRevisionCollection(self, value)
        else:
            self._revisions = value

    @property
    def latest_revision(self) -> PageRevision:
        """
        Get the latest revision of the page

        Returns the revision where revision_count and rev_no match as the latest.

        Returns
        -------
        PageRevision
            Latest revision object

        Raises
        ------
        NotFoundException
            When the latest revision is not found
        """
        # revision_countとrev_noが一致するものを取得
        for revision in self.revisions:
            if revision.rev_no == self.revisions_count:
                return revision

        raise exceptions.NotFoundException(
            f"Cannot find latest revision for site: {self.site.unix_name}, page: {self.fullname} "
            f"(rev_no={self.revisions_count})"
        )

    @property
    def votes(self) -> PageVoteCollection:
        """
        Get vote information for the page

        Automatically performs retrieval processing if the vote information has not been acquired.

        Returns
        -------
        PageVoteCollection
            Vote information collection for the page

        Raises
        ------
        NotFoundException
            When the vote information is not found
        """
        if self._votes is None:
            PageCollection(self.site, [self]).get_page_votes()

        if self._votes is None:
            raise exceptions.NotFoundException(
                f"Cannot find page votes for site: {self.site.unix_name}, page: {self.fullname}"
            )

        return self._votes

    @votes.setter
    def votes(self, value: PageVoteCollection) -> None:
        """
        Set vote information for the page

        Parameters
        ----------
        value : PageVoteCollection
            Vote information collection to set
        """
        self._votes = value

    @property
    def discussion(self) -> Optional["ForumThread"]:
        """
        Get the discussion thread for the page

        Retrieves the forum thread (comments section) associated with the page.
        Returns None if the discussion does not exist.

        Returns
        -------
        ForumThread | None
            Discussion thread. None if it does not exist

        Raises
        ------
        UnexpectedException
            When the discussion module cannot be retrieved after retries
        """
        if not self._discussion_checked:
            response = self.site.amc_request_with_retry(
                [
                    {
                        "moduleName": "forum/ForumCommentsListModule",
                        "pageId": self.id,
                    }
                ]
            )[0]
            if response is None:
                raise exceptions.UnexpectedException(
                    f"Cannot retrieve page discussion for site: {self.site.unix_name}, page: {self.fullname}"
                )

            body = response.json().get("body")
            if body is None:
                raise exceptions.NoElementException(
                    f"Page discussion response body is not found for site: {self.site.unix_name}, page: {self.fullname}"
                )
            match = re.search(r"WIKIDOT\.forumThreadId = (\d+);", body)
            if match is not None:
                from .forum_thread import ForumThread

                thread_id = int(match.group(1))
                self._discussion = ForumThread.get_from_id(self.site, thread_id)
            self._discussion_checked = True

        return self._discussion

    @property
    def files(self) -> "PageFileCollection":
        """
        Get a list of files attached to the page

        Automatically performs retrieval processing if the file list has not been acquired.

        Returns
        -------
        PageFileCollection
            Collection of files attached to the page

        Raises
        ------
        NotFoundException
            When the file list is not found
        """
        if self._files is None:
            PageCollection(self.site, [self]).get_page_files()

        if self._files is None:
            raise exceptions.NotFoundException(
                f"Cannot find page files for site: {self.site.unix_name}, page: {self.fullname}"
            )

        return self._files

    def destroy(self) -> None:
        """
        Delete the page

        Can only be executed while logged in. Performs complete deletion of the page.

        Raises
        ------
        LoginRequiredException
            When not logged in
        WikidotStatusCodeException
            When deletion fails
        """
        self.site.client.login_check()
        response = self.site.amc_request(
            [
                {
                    "action": "WikiPageAction",
                    "event": "deletePage",
                    "page_id": self.id,
                    "moduleName": "Empty",
                }
            ]
        )[0]
        _require_page_action_status(self.site, self, "deletePage", response.json())
        self._source = None
        self._revisions = None
        self._votes = None
        self._metas = None
        self._discussion = None
        self._discussion_checked = False
        self._files = None

    @property
    def metas(self) -> dict[str, str]:
        """
        Get meta tag information for the page

        Automatically performs retrieval processing if the meta tag information has not been acquired.

        Returns
        -------
        dict[str, str]
            Dictionary of meta tag names and their contents

        Raises
        ------
        UnexpectedException
            When meta tag information cannot be retrieved after retries
        """
        if self._metas is None:
            response = self.site.amc_request_with_retry(
                [
                    {
                        "pageId": self.id,
                        "moduleName": "edit/EditMetaModule",
                    }
                ]
            )[0]
            if response is None:
                raise exceptions.UnexpectedException(
                    f"Cannot retrieve page metas for site: {self.site.unix_name}, page: {self.fullname}"
                )

            # レスポンス解析
            body = response.json().get("body")
            if body is None:
                raise exceptions.NoElementException(
                    f"Page metas response body is not found for site: {self.site.unix_name}, page: {self.fullname}"
                )

            # タグ境界だけを戻してからHTMLとして解析し、属性値は取得後に復号する
            body = body.replace("&lt;", "<").replace("&gt;", ">").replace("&LT;", "<").replace("&GT;", ">")
            metas = {}
            for meta in BeautifulSoup(body, "lxml").select("meta[name][content]"):
                metas[html_lib.unescape(str(meta["name"]))] = html_lib.unescape(str(meta["content"]))

            self._metas = metas

        return self._metas

    @metas.setter
    def metas(self, value: dict[str, str]) -> None:
        """
        Set meta tag information for the page

        Compares with current meta tags, deletes removed ones, and saves added/updated ones.

        Parameters
        ----------
        value : dict[str, str]
            Dictionary of meta tag names and their contents to set

        Raises
        ------
        LoginRequiredException
            When not logged in
        WikidotStatusCodeException
            When setting meta tags fails
        """
        self.site.client.login_check()
        request_bodies = self._meta_update_request_bodies(value)

        if request_bodies:
            responses = self.site.amc_request(request_bodies)
            for request_body, response in zip(request_bodies, responses, strict=True):
                _require_page_metadata_action_status(
                    self.site,
                    self,
                    str(request_body.get("event", "unknown")),
                    response.json(),
                )

        self._metas = dict(value)

    def _meta_update_request_bodies(self, value: dict[str, str]) -> list[dict[str, Any]]:
        current_metas = self.metas
        deleted_metas = {k: v for k, v in current_metas.items() if k not in value}
        added_metas = {k: v for k, v in value.items() if k not in current_metas}
        updated_metas = {k: v for k, v in value.items() if k in current_metas and current_metas[k] != v}

        request_bodies: list[dict[str, Any]] = []
        for name, _content in deleted_metas.items():
            request_bodies.append(
                {
                    "metaName": name,
                    "action": "WikiPageAction",
                    "event": "deleteMetaTag",
                    "pageId": self.id,
                    "moduleName": "edit/EditMetaModule",
                }
            )

        for name, content in added_metas.items():
            request_bodies.append(
                {
                    "metaName": name,
                    "metaContent": content,
                    "action": "WikiPageAction",
                    "event": "saveMetaTag",
                    "pageId": self.id,
                    "moduleName": "edit/EditMetaModule",
                }
            )

        for name, content in updated_metas.items():
            request_bodies.append(
                {
                    "metaName": name,
                    "metaContent": content,
                    "action": "WikiPageAction",
                    "event": "saveMetaTag",
                    "pageId": self.id,
                    "moduleName": "edit/EditMetaModule",
                }
            )

        return request_bodies

    def set_metadata(
        self,
        *,
        tags: list[str] | None = None,
        parent_fullname: str | None | _UnsetParentType = _UNSET_PARENT,
        metas: dict[str, str] | None = None,
    ) -> "Page":
        """
        Set page tags, parent page, and meta tags in one AMC batch when possible

        Parameters
        ----------
        tags : list[str] | None, default None
            Tags to save. None leaves tags unchanged; an empty list clears tags.
        parent_fullname : str | None, optional
            Parent fullname to set. Passing None clears the parent. Omitting this argument leaves the parent unchanged.
        metas : dict[str, str] | None, default None
            Meta tags to save. None leaves meta tags unchanged; an empty dict deletes existing meta tags.

        Returns
        -------
        Page
            Self (for method chaining)

        Raises
        ------
        LoginRequiredException
            When not logged in
        WikidotStatusCodeException
            When setting metadata fails
        """
        self.site.client.login_check()

        request_bodies: list[dict[str, Any]] = []
        if tags is not None:
            request_bodies.append(
                {
                    "tags": " ".join(tags),
                    "action": "WikiPageAction",
                    "event": "saveTags",
                    "pageId": self.id,
                    "moduleName": "Empty",
                }
            )

        parent_value: str | None = None
        if parent_fullname is not _UNSET_PARENT:
            parent_value = _normalize_parent_fullname(parent_fullname if isinstance(parent_fullname, str) else None)
            request_bodies.append(
                {
                    "action": "WikiPageAction",
                    "event": "setParentPage",
                    "moduleName": "Empty",
                    "pageId": str(self.id),
                    "parentName": parent_value or "",
                }
            )

        if metas is not None:
            request_bodies.extend(self._meta_update_request_bodies(metas))

        if request_bodies:
            responses = self.site.amc_request(request_bodies)
            for request_body, response in zip(request_bodies, responses, strict=True):
                _require_page_metadata_action_status(
                    self.site,
                    self,
                    str(request_body.get("event", "unknown")),
                    response.json(),
                )

        if tags is not None:
            self.tags = list(tags)
        if parent_fullname is not _UNSET_PARENT:
            self.parent_fullname = parent_value
        if metas is not None:
            self._metas = dict(metas)

        return self

    @staticmethod
    def create_or_edit(
        site: "Site",
        fullname: str,
        page_id: int | None = None,
        title: str = "",
        source: str = "",
        comment: str = "",
        force_edit: bool = False,
        raise_on_exists: bool = False,
    ) -> "Page":
        """
        Create or edit a page

        Creates a new page or edits an existing page.
        For editing, acquires page lock and performs page save processing.

        Parameters
        ----------
        site : Site
            Site to which the page belongs
        fullname : str
            Fullname of the page
        page_id : int | None, default None
            Page ID when editing (None when creating new)
        title : str, default ""
            Title of the page
        source : str, default ""
            Source code of the page (Wikidot markup)
        comment : str, default ""
            Edit comment
        force_edit : bool, default False
            Whether to forcibly release locks by other users
        raise_on_exists : bool, default False
            Whether to raise an exception if the page already exists

        Returns
        -------
        Page
            Created or edited page object

        Raises
        ------
        LoginRequiredException
            When not logged in
        TargetErrorException
            When the page is locked
        TargetExistsException
            When the page already exists and raise_on_exists is True
        ValueError
            When page_id is not specified when editing an existing page
        WikidotStatusCodeException
            When saving the page fails
        NotFoundException
            When the page cannot be found after creation
        """
        site.client.login_check()

        # ページロックを取得しにいく
        page_lock_request_body = {
            "mode": "page",
            "wiki_page": fullname,
            "moduleName": "edit/PageEditModule",
        }
        if force_edit:
            page_lock_request_body["force_lock"] = "yes"

        page_lock_response = site.amc_request([page_lock_request_body])[0]
        page_lock_response_data = page_lock_response.json()

        if page_lock_response_data.get("locked") or page_lock_response_data.get("other_locks"):
            raise exceptions.TargetErrorException(
                f"Page {fullname} is locked or other locks exist",
            )

        # ページが存在するか（page_revision_idがあるか）確認
        is_exist = "page_revision_id" in page_lock_response_data

        if raise_on_exists and is_exist:
            raise exceptions.TargetExistsException(f"Page {fullname} already exists")

        if is_exist and page_id is None:
            raise ValueError("page_id must be specified when editing existing page")

        # lock_idとlock_secret、page_revision_id（あれば）を取得
        lock_id = _require_page_edit_lock_field(site, fullname, page_lock_response_data, "lock_id")
        lock_secret = _require_page_edit_lock_field(site, fullname, page_lock_response_data, "lock_secret")
        page_revision_id = page_lock_response_data.get("page_revision_id")

        # ページの作成または編集
        edit_request_body = {
            "action": "WikiPageAction",
            "event": "savePage",
            "moduleName": "Empty",
            "mode": "page",
            "lock_id": lock_id,
            "lock_secret": lock_secret,
            "revision_id": page_revision_id if page_revision_id is not None else "",
            "wiki_page": fullname,
            "page_id": page_id if page_id is not None else "",
            "title": title,
            "source": source,
            "comments": comment,
        }
        response = site.amc_request([edit_request_body])[0]
        response_data = response.json()
        save_status = _require_page_save_status(site, fullname, response_data)

        if save_status != "ok":
            raise exceptions.WikidotStatusCodeException(f"Failed to create or edit page: {fullname}", save_status)

        page = PageCollection.get_by_fullname(site, fullname)
        if page is None:
            category, name = PageCollection._split_fullname(fullname)
            now = datetime.now()
            page = Page(
                site=site,
                fullname=fullname,
                name=name,
                category=category,
                title=title,
                children_count=0,
                comments_count=0,
                size=len(source.encode("utf-8")),
                rating=0,
                votes_count=0,
                rating_percent=0.0,
                revisions_count=1,
                parent_fullname=None,
                tags=[],
                created_by=PageCollection._current_user_or_placeholder(site),
                created_at=now,
                updated_by=PageCollection._current_user_or_placeholder(site),
                updated_at=now,
                commented_by=None,
                commented_at=None,
                _id=page_id,
            )

        if page_id is not None or title:
            page.title = title
        page.source = PageSource(page, source)
        return page

    def edit(
        self,
        title: str | None = None,
        source: str | None = None,
        comment: str | None = None,
        force_edit: bool = False,
    ) -> "Page":
        """
        Edit this page

        Updates the contents of an existing page. Parameters not specified maintain their current values.

        Parameters
        ----------
        title : str | None, default None
            New title (maintains current title if None)
        source : str | None, default None
            New source code (maintains current source if None)
        comment : str | None, default None
            Edit comment
        force_edit : bool, default False
            Whether to forcibly release locks by other users

        Returns
        -------
        Page
            Edited page object

        Raises
        ------
        Same as above (same as create_or_edit method)
        """
        self.site.client.login_check()

        # Noneならそのままにする
        if title is None:
            title = self.title
        if source is None:
            source = self.source.wiki_text
        if comment is None:
            comment = ""

        page = Page.create_or_edit(
            self.site,
            self.fullname,
            self.id,
            title,
            source,
            comment,
            force_edit,
        )
        self.title = page.title
        if page.revisions_count > self.revisions_count:
            self.revisions_count = page.revisions_count
        self._revisions = None
        self.source = PageSource(self, source)
        return page

    def commit_tags(self) -> "Page":
        """
        Save tag information for the page

        Saves the contents of the current tags property to Wikidot.

        Returns
        -------
        Page
            Self (for method chaining)

        Raises
        ------
        LoginRequiredException
            When not logged in
        WikidotStatusCodeException
            When saving tags fails
        """
        self.site.client.login_check()
        response = self.site.amc_request(
            [
                {
                    "tags": " ".join(self.tags),
                    "action": "WikiPageAction",
                    "event": "saveTags",
                    "pageId": self.id,
                    "moduleName": "Empty",
                }
            ]
        )[0]
        _require_page_metadata_action_status(self.site, self, "saveTags", response.json())
        return self

    def set_parent(self, parent_fullname: str | None) -> "Page":
        """
        Set the parent page

        Sets the specified parent page as the parent of this page.
        Specifying None or an empty string removes the parent page setting.

        Parameters
        ----------
        parent_fullname : str | None
            Fullname of the parent page. None or empty string removes the parent

        Returns
        -------
        Page
            Self (for method chaining)

        Raises
        ------
        LoginRequiredException
            When not logged in
        WikidotStatusCodeException
            When setting the parent page fails
        """
        self.site.client.login_check()
        parent_value = _normalize_parent_fullname(parent_fullname)
        response = self.site.amc_request(
            [
                {
                    "action": "WikiPageAction",
                    "event": "setParentPage",
                    "moduleName": "Empty",
                    "pageId": str(self.id),
                    "parentName": parent_value or "",
                }
            ]
        )[0]
        _require_page_metadata_action_status(self.site, self, "setParentPage", response.json())
        self.parent_fullname = parent_value
        return self

    def rename(self, new_fullname: str) -> "Page":
        """
        Rename the page

        Changes the page's fullname to a new name.
        Must specify the complete fullname including category.

        Parameters
        ----------
        new_fullname : str
            New fullname (e.g., "component:new-name")

        Returns
        -------
        Page
            Self (for method chaining)

        Raises
        ------
        LoginRequiredException
            When not logged in
        WikidotStatusCodeException
            When renaming the page fails (e.g., when a page with the same name exists)
        """
        self.site.client.login_check()
        response = self.site.amc_request(
            [
                {
                    "action": "WikiPageAction",
                    "event": "renamePage",
                    "moduleName": "Empty",
                    "page_id": self.id,
                    "new_name": new_fullname,
                }
            ]
        )[0]
        _require_page_action_status(self.site, self, "renamePage", response.json())
        self.fullname = new_fullname
        if ":" in new_fullname:
            self.category, self.name = new_fullname.split(":", 1)
        else:
            self.category = "_default"
            self.name = new_fullname
        self._files = None
        return self

    def vote(self, value: int) -> int:
        """
        Vote on the page

        Casts a +1 or -1 vote on the page.
        Overwrites if already voted.

        Parameters
        ----------
        value : int
            Vote value (1 or -1)

        Returns
        -------
        int
            New rating value after voting

        Raises
        ------
        LoginRequiredException
            When not logged in
        ValueError
            When value is not 1 or -1
        WikidotStatusCodeException
            When voting fails
        """
        if value not in (1, -1):
            raise ValueError("Vote value must be 1 or -1")

        self.site.client.login_check()
        response = self.site.amc_request(
            [
                {
                    "action": "RateAction",
                    "event": "ratePage",
                    "moduleName": "Empty",
                    "pageId": self.id,
                    "points": value,
                    "force": "yes",
                }
            ]
        )[0]
        new_rating = _parse_page_rating_points(self.site, self, "ratePage", response.json())
        self.rating = new_rating
        self._votes = None
        return new_rating

    def cancel_vote(self) -> int:
        """
        Cancel the vote

        Cancels your vote on this page.

        Returns
        -------
        int
            New rating value after cancellation

        Raises
        ------
        LoginRequiredException
            When not logged in
        WikidotStatusCodeException
            When vote cancellation fails
        """
        self.site.client.login_check()
        response = self.site.amc_request(
            [
                {
                    "action": "RateAction",
                    "event": "cancelVote",
                    "moduleName": "Empty",
                    "pageId": self.id,
                }
            ]
        )[0]
        new_rating = _parse_page_rating_points(self.site, self, "cancelVote", response.json())
        self.rating = new_rating
        self._votes = None
        return new_rating
