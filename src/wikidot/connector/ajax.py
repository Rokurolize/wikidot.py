"""
Module responsible for communication with Wikidot's Ajax Module Connector

This module provides classes and utilities for communicating with
Wikidot site's ajax-module-connector.php. It features async communication,
error handling, and retry functionality.
"""

import asyncio
import json.decoder
import random
from dataclasses import dataclass
from typing import Any, Literal, overload

import httpx

from ..common import wd_logger
from ..common.exceptions import (
    AMCHttpStatusCodeException,
    ForbiddenException,
    NotFoundException,
    ResponseDataException,
    WikidotStatusCodeException,
)
from ..util.async_helper import run_coroutine
from ..util.http import sync_get_with_retry
from ..util.stringutil import StringUtil


def _validate_cookie_name(name: object) -> str:
    if not isinstance(name, str):
        raise TypeError("cookie name must be str")
    if not name or any(char.isspace() or char in "=;" for char in name):
        raise ValueError("cookie name must be a non-empty string without whitespace, '=' or ';'")
    return name


def _validate_cookie_value(value: object) -> object:
    serialized = str(value)
    if any(char.isspace() or char == ";" for char in serialized):
        raise ValueError("cookie value must serialize without whitespace or ';'")
    return value


def _validate_cookie_dict(cookie: object) -> dict[Any, Any]:
    if cookie is None:
        return {}
    if not isinstance(cookie, dict):
        raise ValueError("cookie must be a dictionary")
    return cookie


def _validate_header_value(field_name: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be str")
    if "\r" in value or "\n" in value:
        raise ValueError(f"{field_name} must not contain line breaks")
    return value


class AjaxRequestHeader:
    """
    Class for managing request headers used in Ajax Module Connector communication

    Manages Content-Type, User-Agent, Referer, Cookie, etc.,
    and provides functionality to generate appropriate HTTP headers.
    """

    def __init__(
        self,
        content_type: str | None = None,
        user_agent: str | None = None,
        referer: str | None = None,
        cookie: dict | None = None,
    ):
        """
        Initialize AjaxRequestHeader

        Parameters
        ----------
        content_type : str | None, default None
            Content-Type to set. Default value is used if None
        user_agent : str | None, default None
            User-Agent to set. Default value is used if None
        referer : str | None, default None
            Referer to set. Default value is used if None
        cookie : dict | None, default None
            Cookie to set. Empty dict is used if None
        """
        self.content_type: str = (
            "application/x-www-form-urlencoded; charset=UTF-8"
            if content_type is None
            else _validate_header_value("content_type", content_type)
        )
        self.user_agent: str = "WikidotPy" if user_agent is None else _validate_header_value("user_agent", user_agent)
        self.referer: str = (
            "https://www.wikidot.com/" if referer is None else _validate_header_value("referer", referer)
        )
        self.cookie: dict[str, Any] = {"wikidot_token7": 123456}
        self.cookie.update(
            {
                _validate_cookie_name(name): _validate_cookie_value(value)
                for name, value in _validate_cookie_dict(cookie).items()
            }
        )
        return

    def set_cookie(self, name: str, value: Any) -> None:
        """
        Set a cookie

        Parameters
        ----------
        name : str
            Name of the cookie to set
        value : str
            Value of the cookie to set
        """
        self.cookie[_validate_cookie_name(name)] = _validate_cookie_value(value)
        return

    def delete_cookie(self, name: str) -> None:
        """
        Delete a cookie

        Parameters
        ----------
        name : str
            Name of the cookie to delete
        """
        self.cookie.pop(_validate_cookie_name(name), None)
        return

    def get_header(self) -> dict:
        """
        Get the constructed HTTP headers

        Returns
        -------
        dict
            Header dictionary for HTTP requests
        """
        if not isinstance(self.cookie, dict):
            raise ValueError("cookie must be a dictionary")
        return {
            "Content-Type": _validate_header_value("content_type", self.content_type),
            "User-Agent": _validate_header_value("user_agent", self.user_agent),
            "Referer": _validate_header_value("referer", self.referer),
            "Cookie": "".join(
                [
                    f"{_validate_cookie_name(name)}={_validate_cookie_value(value)};"
                    for name, value in self.cookie.items()
                ]
            ),
        }


@dataclass
class AjaxModuleConnectorConfig:
    """
    Data class holding Ajax Module Connector communication settings

    Manages settings such as request timeout, retry count, and concurrent connections.

    Attributes
    ----------
    request_timeout : int, default 20
        Request timeout in seconds
    attempt_limit : int, default 3
        Maximum number of retries on error
    retry_interval : float, default 1.0
        Base retry interval in seconds. Used as the basis for exponential backoff
    max_backoff : float, default 60.0
        Maximum retry interval in seconds
    backoff_factor : float, default 2.0
        Exponential backoff factor (interval is multiplied by this factor for each retry)
    semaphore_limit : int, default 10
        Maximum number of concurrent async requests
    retry_batch_size : int, default 50
        Default batch size for amc_request_with_retry
    retry_max_retries : int, default 3
        Default maximum retry attempts for amc_request_with_retry
    """

    request_timeout: int = 20
    attempt_limit: int = 5
    retry_interval: float = 1.0
    max_backoff: float = 60.0
    backoff_factor: float = 2.0
    semaphore_limit: int = 10
    retry_batch_size: int = 50
    retry_max_retries: int = 3

    def __post_init__(self) -> None:
        _validate_positive_number_option("request_timeout", self.request_timeout)
        _validate_positive_int_option("attempt_limit", self.attempt_limit)
        _validate_non_negative_number_option("retry_interval", self.retry_interval)
        _validate_non_negative_number_option("max_backoff", self.max_backoff)
        _validate_non_negative_number_option("backoff_factor", self.backoff_factor)
        _validate_positive_int_option("semaphore_limit", self.semaphore_limit)
        _validate_positive_int_option("retry_batch_size", self.retry_batch_size)
        _validate_non_negative_int_option("retry_max_retries", self.retry_max_retries)


def _validate_amc_config(config: object) -> AjaxModuleConnectorConfig:
    if config is None:
        return AjaxModuleConnectorConfig()
    if not isinstance(config, AjaxModuleConnectorConfig):
        raise ValueError("config must be AjaxModuleConnectorConfig")
    return config


def _validate_positive_int_option(field_name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a positive integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _validate_non_negative_int_option(field_name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a non-negative integer")
    if value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _validate_positive_number_option(field_name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be a positive number")
    if value <= 0:
        raise ValueError(f"{field_name} must be a positive number")
    return float(value)


def _validate_non_negative_number_option(field_name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be a non-negative number")
    if value < 0:
        raise ValueError(f"{field_name} must be a non-negative number")
    return float(value)


def _validate_amc_request_config(
    config: AjaxModuleConnectorConfig,
) -> tuple[float, int, float, float, float, int]:
    return (
        _validate_positive_number_option("request_timeout", config.request_timeout),
        _validate_positive_int_option("attempt_limit", config.attempt_limit),
        _validate_non_negative_number_option("retry_interval", config.retry_interval),
        _validate_non_negative_number_option("backoff_factor", config.backoff_factor),
        _validate_non_negative_number_option("max_backoff", config.max_backoff),
        _validate_positive_int_option("semaphore_limit", config.semaphore_limit),
    )


def _validate_amc_request_bodies(bodies: object) -> list[dict[str, Any]]:
    if not isinstance(bodies, list):
        raise ValueError("bodies must be a list of dictionaries")
    for index, body in enumerate(bodies):
        if not isinstance(body, dict):
            raise ValueError(f"bodies[{index}] must be a dictionary")
    return bodies


def _mask_sensitive_data(body: dict[str, Any]) -> dict[str, Any]:
    """
    Mask sensitive information for log output

    Parameters
    ----------
    body : dict[str, Any]
        Request body to mask

    Returns
    -------
    dict[str, Any]
        Dictionary with sensitive information masked
    """
    redacted_keys = {
        "password",
        "login",
        "WIKIDOT_SESSION_ID",
        "wikidot_token7",
        "lock_secret",
        "source",
        "body",
        "text",
        "subject",
        "title",
        "comment",
        "comments",
        "description",
    }

    def mask_value(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: "***MASKED***" if key in redacted_keys else mask_value(nested_value)
                for key, nested_value in value.items()
            }
        if isinstance(value, list):
            return [mask_value(item) for item in value]
        return value

    return mask_value(body)


def _calculate_backoff(
    retry_count: int,
    base_interval: float,
    backoff_factor: float,
    max_backoff: float,
) -> float:
    """
    Calculate exponential backoff interval (with jitter)

    Parameters
    ----------
    retry_count : int
        Current retry count (starting from 1)
    base_interval : float
        Base interval in seconds
    backoff_factor : float
        Backoff factor (interval is multiplied by this factor for each retry)
    max_backoff : float
        Maximum backoff interval in seconds

    Returns
    -------
    float
        Calculated backoff interval in seconds
    """
    retry_count = _validate_positive_int_option("retry_count", retry_count)
    base_interval = _validate_non_negative_number_option("base_interval", base_interval)
    backoff_factor = _validate_non_negative_number_option("backoff_factor", backoff_factor)
    max_backoff = _validate_non_negative_number_option("max_backoff", max_backoff)

    # backoff_factor^(retry_count-1) * base_interval
    backoff = (backoff_factor ** (retry_count - 1)) * base_interval
    # Add 10% jitter
    jitter = random.uniform(0, backoff * 0.1)
    return min(backoff + jitter, max_backoff)


class AjaxModuleConnectorClient:
    """
    Client class for communicating with Wikidot's Ajax Module Connector

    Performs HTTP requests to ajax-module-connector.php and processes responses.
    Features async communication, retry processing, and error handling.
    """

    def __init__(
        self,
        site_name: str | None = None,
        config: AjaxModuleConnectorConfig | None = None,
    ):
        """
        Initialize AjaxModuleConnectorClient

        Parameters
        ----------
        site_name : str | None, default None
            Wikidot site name to connect to. "www" is used if None
        config : AjaxModuleConnectorConfig | None, default None
            Communication settings. Default values are used if None
        """
        self.site_name: str = site_name if site_name is not None else "www"
        StringUtil.validate_site_unix_name(self.site_name)
        self.config: AjaxModuleConnectorConfig = _validate_amc_config(config)

        # Check SSL support
        self.ssl_supported: bool = self._check_existence_and_ssl()

        # Initialize headers
        self.header: AjaxRequestHeader = AjaxRequestHeader()

    def _check_existence_and_ssl(self) -> bool:
        """
        Check site existence and SSL support status

        Sends an actual HTTP request to verify site existence and
        determines SSL support status by checking if redirected to HTTPS.

        Returns
        -------
        bool
            True if the site supports SSL, False otherwise

        Raises
        ------
        NotFoundException
            If the specified site does not exist
        """
        # www always supports SSL
        if self.site_name == "www":
            return True

        # For other sites, determine by checking if redirected to https
        response = sync_get_with_retry(
            f"http://{self.site_name}.wikidot.com",
            timeout=self.config.request_timeout,
            attempt_limit=self.config.attempt_limit,
            retry_interval=self.config.retry_interval,
            max_backoff=self.config.max_backoff,
            backoff_factor=self.config.backoff_factor,
            follow_redirects=False,
            raise_for_status=False,
        )

        # Raise exception if not found
        if response.status_code == httpx.codes.NOT_FOUND:
            raise NotFoundException(f"Site is not found: {self.site_name}.wikidot.com")

        # Determine by checking if redirected to https
        return (
            response.status_code == httpx.codes.MOVED_PERMANENTLY
            and "Location" in response.headers
            and response.headers["Location"].startswith("https")
        )

    @overload
    def request(
        self,
        bodies: list[dict[str, Any]],
        return_exceptions: Literal[False] = False,
        site_name: str | None = None,
        site_ssl_supported: bool | None = None,
    ) -> tuple[httpx.Response, ...]: ...

    @overload
    def request(
        self,
        bodies: list[dict[str, Any]],
        return_exceptions: Literal[True],
        site_name: str | None = None,
        site_ssl_supported: bool | None = None,
    ) -> tuple[httpx.Response | Exception, ...]: ...

    def request(
        self,
        bodies: list[dict[str, Any]],
        return_exceptions: bool = False,
        site_name: str | None = None,
        site_ssl_supported: bool | None = None,
    ) -> tuple[httpx.Response, ...] | tuple[httpx.Response | Exception, ...]:
        """
        Send request to Ajax Module Connector and get response

        Processes multiple requests asynchronously in parallel and automatically retries on error.

        Parameters
        ----------
        bodies : list[dict[str, Any]]
            List of request bodies to send
        return_exceptions : bool, default False
            Whether to return or raise exceptions (True: return, False: raise)
        site_name : str | None, default None
            Target site name. Uses the site name specified at initialization if None
        site_ssl_supported : bool | None, default None
            Site's SSL support status. Uses the result confirmed at initialization if None

        Returns
        -------
        tuple[httpx.Response, ...] | tuple[httpx.Response | Exception, ...]
            Tuple of responses or exceptions (in same order as requests)

        Raises
        ------
        AMCHttpStatusCodeException
            If HTTP status code is not 200 (when return_exceptions is False)
        WikidotStatusCodeException
            If response status is not "ok" (when return_exceptions is False)
        ResponseDataException
            If response is invalid JSON format or empty (when return_exceptions is False)
        """
        if not isinstance(return_exceptions, bool):
            raise ValueError("return_exceptions must be a boolean")
        bodies = _validate_amc_request_bodies(bodies)

        (
            request_timeout,
            attempt_limit,
            retry_interval,
            backoff_factor,
            max_backoff,
            semaphore_limit,
        ) = _validate_amc_request_config(self.config)
        semaphore_instance = asyncio.Semaphore(semaphore_limit)

        site_name = site_name if site_name is not None else self.site_name
        site_ssl_supported = site_ssl_supported if site_ssl_supported is not None else self.ssl_supported
        StringUtil.validate_site_unix_name(site_name)

        async def _request(_body: dict[str, Any], client: httpx.AsyncClient) -> httpx.Response:
            retry_count = 0
            response: httpx.Response | None = None
            request_body = {"wikidot_token7": self.header.cookie.get("wikidot_token7", 123456), **_body}

            while True:
                # Execute request
                try:
                    # Control concurrent execution with Semaphore
                    async with semaphore_instance:
                        url = (
                            f"http{'s' if site_ssl_supported else ''}://{site_name}.wikidot.com/"
                            f"ajax-module-connector.php"
                        )
                        wd_logger.debug(f"Ajax Request: {url} -> {_mask_sensitive_data(request_body)}")
                        response = await client.post(
                            url,
                            headers=self.header.get_header(),
                            data=request_body,
                            timeout=request_timeout,
                        )
                        response.raise_for_status()
                except (httpx.HTTPStatusError, httpx.RequestError) as e:
                    # Retry on all request errors (HTTP errors, timeouts, network errors, etc.)
                    # Wikidot server has a relatively high error rate, so retry is essential
                    retry_count += 1

                    # Raise exception if retry limit reached
                    if retry_count >= attempt_limit:
                        error_detail = str(response.status_code) if response is not None else str(e)
                        wd_logger.error(f"AMC request failed: {error_detail} -> {_mask_sensitive_data(request_body)}")
                        raise AMCHttpStatusCodeException(
                            f"AMC request failed: {error_detail}",
                            response.status_code if response is not None else 999,
                        ) from e

                    # Retry with exponential backoff interval
                    backoff = _calculate_backoff(
                        retry_count,
                        retry_interval,
                        backoff_factor,
                        max_backoff,
                    )
                    error_info = str(response.status_code) if response is not None else str(e)
                    wd_logger.info(
                        f"AMC request error: {error_info} "
                        f"(retry: {retry_count}, backoff: {backoff:.2f}s) -> {_mask_sensitive_data(request_body)}"
                    )
                    await asyncio.sleep(backoff)
                    continue

                # Parse body as JSON data
                try:
                    _response_body = response.json()
                except json.decoder.JSONDecodeError:
                    # Retry on JSON parse error (e.g., empty response)
                    retry_count += 1
                    if retry_count >= attempt_limit:
                        wd_logger.error(f"AMC responded with non-JSON data -> {_mask_sensitive_data(request_body)}")
                        raise ResponseDataException("AMC responded with non-JSON data") from None

                    backoff = _calculate_backoff(
                        retry_count,
                        retry_interval,
                        backoff_factor,
                        max_backoff,
                    )
                    wd_logger.info(f"AMC responded with non-JSON data (retry: {retry_count}, backoff: {backoff:.2f}s)")
                    await asyncio.sleep(backoff)
                    continue

                if not isinstance(_response_body, dict):
                    retry_count += 1
                    if retry_count >= attempt_limit:
                        response_type = type(_response_body).__name__
                        wd_logger.error(
                            f"AMC responded with invalid JSON data type: {response_type} -> "
                            f"{_mask_sensitive_data(request_body)}"
                        )
                        raise ResponseDataException(f"AMC responded with invalid JSON data type: {response_type}")

                    backoff = _calculate_backoff(
                        retry_count,
                        retry_interval,
                        backoff_factor,
                        max_backoff,
                    )
                    wd_logger.info(
                        f"AMC responded with invalid JSON data (retry: {retry_count}, backoff: {backoff:.2f}s)"
                    )
                    await asyncio.sleep(backoff)
                    continue

                # Retry if response is empty
                if _response_body is None or len(_response_body) == 0:
                    retry_count += 1
                    if retry_count >= attempt_limit:
                        wd_logger.error(f"AMC is respond empty data -> {_mask_sensitive_data(request_body)}")
                        raise ResponseDataException("AMC is respond empty data")

                    backoff = _calculate_backoff(
                        retry_count,
                        retry_interval,
                        backoff_factor,
                        max_backoff,
                    )
                    wd_logger.info(f"AMC responded with empty data (retry: {retry_count}, backoff: {backoff:.2f}s)")
                    await asyncio.sleep(backoff)
                    continue

                if "status" not in _response_body:
                    retry_count += 1
                    if retry_count >= attempt_limit:
                        wd_logger.error(f"AMC response is missing status field -> {_mask_sensitive_data(request_body)}")
                        raise ResponseDataException("AMC response is missing status field")

                    backoff = _calculate_backoff(
                        retry_count,
                        retry_interval,
                        backoff_factor,
                        max_backoff,
                    )
                    wd_logger.info(
                        f"AMC response is missing status field (retry: {retry_count}, backoff: {backoff:.2f}s)"
                    )
                    await asyncio.sleep(backoff)
                    continue

                if not isinstance(_response_body["status"], str):
                    retry_count += 1
                    if retry_count >= attempt_limit:
                        wd_logger.error(f"AMC response status must be a string -> {_mask_sensitive_data(request_body)}")
                        raise ResponseDataException("AMC response status must be a string")

                    backoff = _calculate_backoff(
                        retry_count,
                        retry_interval,
                        backoff_factor,
                        max_backoff,
                    )
                    wd_logger.info(
                        f"AMC response status must be a string (retry: {retry_count}, backoff: {backoff:.2f}s)"
                    )
                    await asyncio.sleep(backoff)
                    continue

                # Treat as error if status is not ok
                status = _response_body["status"]
                if status == "try_again":
                    retry_count += 1
                    if retry_count >= attempt_limit:
                        wd_logger.error(f'AMC is respond status: "try_again" -> {_mask_sensitive_data(request_body)}')
                        raise WikidotStatusCodeException('AMC is respond status: "try_again"', "try_again")

                    # Retry with exponential backoff interval
                    backoff = _calculate_backoff(
                        retry_count,
                        retry_interval,
                        backoff_factor,
                        max_backoff,
                    )
                    wd_logger.info(
                        f'AMC is respond status: "try_again" (retry: {retry_count}, backoff: {backoff:.2f}s)'
                    )
                    await asyncio.sleep(backoff)
                    continue

                elif status == "no_permission":
                    target_str = "unknown"
                    if "moduleName" in request_body:
                        target_str = f"moduleName: {request_body['moduleName']}"
                    elif "action" in request_body:
                        target_str = (
                            f"action: {request_body['action']}/"
                            f"{request_body['event'] if 'event' in request_body else ''}"
                        )
                    raise ForbiddenException(f"Your account has no permission to perform this action: {target_str}")

                # Treat as error if status is not ok for other cases
                elif status != "ok":
                    wd_logger.error(f'AMC is respond error status: "{status}" -> {_mask_sensitive_data(request_body)}')
                    raise WikidotStatusCodeException(
                        f'AMC is respond error status: "{status}"',
                        status,
                    )

                # Return response
                return response

        async def _execute_requests() -> list[httpx.Response | BaseException]:
            async with httpx.AsyncClient() as client:
                return await asyncio.gather(
                    *[_request(body, client) for body in bodies],
                    return_exceptions=return_exceptions,
                )

        # Execute processing (works safely even in existing loop environments)
        results: list[httpx.Response | BaseException] = run_coroutine(_execute_requests())
        return tuple(
            r if isinstance(r, httpx.Response) else r if isinstance(r, Exception) else Exception(str(r))
            for r in results
        )
