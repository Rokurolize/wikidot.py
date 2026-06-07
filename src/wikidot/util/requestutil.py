import asyncio
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx

from ..connector.ajax import AjaxModuleConnectorConfig
from .async_helper import run_coroutine
from .http import (
    _is_retryable_status,
    _validate_non_negative_number_option,
    _validate_positive_int_option,
    calculate_backoff,
)

if TYPE_CHECKING:
    from wikidot.module.client import Client


def _validate_positive_number_option(field_name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be a positive number")
    if value <= 0:
        raise ValueError(f"{field_name} must be a positive number")
    return float(value)


def _validate_request_config_object(config: object) -> AjaxModuleConnectorConfig:
    if not isinstance(config, AjaxModuleConnectorConfig):
        raise ValueError("config must be AjaxModuleConnectorConfig")
    return config


def _validate_request_config(config: AjaxModuleConnectorConfig) -> tuple[float, int, float, float, float, int]:
    return (
        _validate_positive_number_option("request_timeout", getattr(config, "request_timeout", None)),
        _validate_positive_int_option("attempt_limit", getattr(config, "attempt_limit", None)),
        _validate_non_negative_number_option("retry_interval", getattr(config, "retry_interval", None)),
        _validate_non_negative_number_option("backoff_factor", getattr(config, "backoff_factor", None)),
        _validate_non_negative_number_option("max_backoff", getattr(config, "max_backoff", None)),
        _validate_positive_int_option("semaphore_limit", getattr(config, "semaphore_limit", None)),
    )


def _validate_request_method(method: object) -> str:
    if not isinstance(method, str):
        raise ValueError("method must be a string")
    method = method.upper()
    if method not in {"GET", "POST"}:
        raise ValueError("Invalid method")
    return method


def _validate_request_urls(urls: object) -> list[str]:
    if not isinstance(urls, list):
        raise ValueError("urls must be a list of strings")
    if any(not isinstance(url, str) for url in urls):
        raise ValueError("urls must be a list of strings")
    return urls


class RequestUtil:
    @staticmethod
    def request(
        client: "Client", method: str, urls: list[str], return_exceptions: bool = False
    ) -> list[httpx.Response | Exception]:
        """Send GET/POST request with retry mechanism.

        Parameters
        ----------
        client: Client
            Client instance
        method: str
            Request method
        urls: list[str]
            List of URLs
        return_exceptions: bool
            Whether to return exceptions (True: return, False: raise)
            Default is to raise exceptions

        Returns
        -------
        list[httpx.Response | Exception]
            List of responses
        """
        method = _validate_request_method(method)
        if not isinstance(return_exceptions, bool):
            raise ValueError("return_exceptions must be a boolean")
        urls = _validate_request_urls(urls)
        if len(urls) == 0:
            return []

        config = client.amc_client.config
        (
            request_timeout,
            attempt_limit,
            retry_interval,
            backoff_factor,
            max_backoff,
            semaphore_limit,
        ) = _validate_request_config(_validate_request_config_object(config))
        semaphore = asyncio.Semaphore(semaphore_limit)

        def _get_headers() -> dict[str, str] | None:
            header = getattr(client.amc_client, "header", None)
            get_header = getattr(header, "get_header", None)
            if not callable(get_header):
                return None

            headers = get_header()
            if not isinstance(headers, dict):
                return None

            return {str(k): str(v) for k, v in headers.items()}

        request_headers = _get_headers()

        def _get_headers_for_url(url: str) -> dict[str, str] | None:
            if request_headers is None:
                return None

            hostname = urlparse(url).hostname
            if hostname is None:
                return None

            hostname = hostname.lower().rstrip(".")
            if hostname == "wikidot.com" or hostname.endswith(".wikidot.com"):
                return request_headers

            return None

        async def _get(http_client: httpx.AsyncClient, url: str) -> httpx.Response:
            async with semaphore:
                for attempt in range(attempt_limit):
                    try:
                        response = await http_client.get(url, headers=_get_headers_for_url(url))
                        response.raise_for_status()
                        return response
                    except httpx.HTTPStatusError as e:
                        # Don't retry 4xx errors - they are client errors that won't change on retry
                        if not _is_retryable_status(e.response.status_code):
                            raise
                        if attempt >= attempt_limit - 1:
                            raise
                        backoff = calculate_backoff(
                            attempt + 1,
                            retry_interval,
                            backoff_factor,
                            max_backoff,
                        )
                        await asyncio.sleep(backoff)
                    except (httpx.TimeoutException, httpx.NetworkError):
                        if attempt >= attempt_limit - 1:
                            raise
                        backoff = calculate_backoff(
                            attempt + 1,
                            retry_interval,
                            backoff_factor,
                            max_backoff,
                        )
                        await asyncio.sleep(backoff)
                raise RuntimeError("Unreachable")

        async def _post(http_client: httpx.AsyncClient, url: str) -> httpx.Response:
            async with semaphore:
                for attempt in range(attempt_limit):
                    try:
                        response = await http_client.post(url, headers=_get_headers_for_url(url))
                        response.raise_for_status()
                        return response
                    except httpx.HTTPStatusError as e:
                        # Don't retry 4xx errors - they are client errors that won't change on retry
                        if not _is_retryable_status(e.response.status_code):
                            raise
                        if attempt >= attempt_limit - 1:
                            raise
                        backoff = calculate_backoff(
                            attempt + 1,
                            retry_interval,
                            backoff_factor,
                            max_backoff,
                        )
                        await asyncio.sleep(backoff)
                    except (httpx.TimeoutException, httpx.NetworkError):
                        if attempt >= attempt_limit - 1:
                            raise
                        backoff = calculate_backoff(
                            attempt + 1,
                            retry_interval,
                            backoff_factor,
                            max_backoff,
                        )
                        await asyncio.sleep(backoff)
                raise RuntimeError("Unreachable")

        async def _execute() -> list[httpx.Response | BaseException]:
            async with httpx.AsyncClient(timeout=request_timeout) as http_client:
                if method == "GET":
                    return await asyncio.gather(
                        *[_get(http_client, url) for url in urls],
                        return_exceptions=return_exceptions,
                    )
                elif method == "POST":
                    return await asyncio.gather(
                        *[_post(http_client, url) for url in urls],
                        return_exceptions=return_exceptions,
                    )
                else:
                    raise ValueError("Invalid method")

        results: list[httpx.Response | BaseException] = run_coroutine(_execute())
        return [
            r if isinstance(r, httpx.Response) else r if isinstance(r, Exception) else Exception(str(r))
            for r in results
        ]
