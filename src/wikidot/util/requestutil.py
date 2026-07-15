import asyncio
import math
from contextlib import AsyncExitStack
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx

from ..common.exceptions import WikidotTransportSecurityException
from ..connector.ajax import (
    AjaxModuleConnectorConfig,
    AjaxRequestHeader,
    _normalize_local_base_url,
    _validate_optional_insecure_transport_site,
)
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
    numeric_value = float(value)
    if not math.isfinite(numeric_value) or numeric_value <= 0:
        raise ValueError(f"{field_name} must be a positive number")
    return numeric_value


def _validate_request_config_object(config: object) -> AjaxModuleConnectorConfig:
    if not isinstance(config, AjaxModuleConnectorConfig):
        raise ValueError("config must be AjaxModuleConnectorConfig")
    return config


def _validate_request_header_object(header: object) -> AjaxRequestHeader:
    if not isinstance(header, AjaxRequestHeader):
        raise ValueError("header must be AjaxRequestHeader")
    return header


def _validate_request_config(
    config: AjaxModuleConnectorConfig,
) -> tuple[float, int, float, float, float, int, str | None]:
    return (
        _validate_positive_number_option("request_timeout", getattr(config, "request_timeout", None)),
        _validate_positive_int_option("attempt_limit", getattr(config, "attempt_limit", None)),
        _validate_non_negative_number_option("retry_interval", getattr(config, "retry_interval", None)),
        _validate_non_negative_number_option("backoff_factor", getattr(config, "backoff_factor", None)),
        _validate_non_negative_number_option("max_backoff", getattr(config, "max_backoff", None)),
        _validate_positive_int_option("semaphore_limit", getattr(config, "semaphore_limit", None)),
        _validate_optional_insecure_transport_site(getattr(config, "allow_insecure_session_transport_for", None)),
    )


def _is_configured_local_url(config: AjaxModuleConnectorConfig, url: str) -> bool:
    local_base_url = _normalize_local_base_url(config.local_base_url)
    if local_base_url is None:
        return False

    parsed_url = urlparse(url)
    parsed_base = urlparse(local_base_url)
    if parsed_url.scheme != parsed_base.scheme or parsed_url.netloc != parsed_base.netloc:
        return False
    base_path = parsed_base.path.rstrip("/")
    return base_path == "" or parsed_url.path == base_path or parsed_url.path.startswith(f"{base_path}/")


def _is_authorized_insecure_wikidot_url(url: str, allowed_site: str | None) -> bool:
    if allowed_site is None:
        return False
    parsed = urlparse(url)
    try:
        port = parsed.port
    except ValueError:
        return False
    hostname = str(parsed.hostname).lower().rstrip(".")
    return parsed.scheme.lower() == "http" and port in {None, 80} and hostname == f"{allowed_site}.wikidot.com"


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
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in {"http", "https"} or parsed.hostname is None:
            raise ValueError("urls must be absolute HTTP(S) URLs")
    return urls


def _validate_request_client(client: object) -> "Client":
    from wikidot.module.client import Client

    if not isinstance(client, Client):
        raise ValueError("client must be a Client")
    return client


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

        client = _validate_request_client(client)
        config = client.amc_client.config
        (
            request_timeout,
            attempt_limit,
            retry_interval,
            backoff_factor,
            max_backoff,
            semaphore_limit,
            allow_insecure_session_transport_for,
        ) = _validate_request_config(_validate_request_config_object(config))
        semaphore = asyncio.Semaphore(semaphore_limit)

        def _get_headers() -> dict[str, str]:
            header = _validate_request_header_object(client.amc_client.header)
            headers = header.get_header()
            return {str(k): str(v) for k, v in headers.items()}

        request_headers = _get_headers()

        def _uses_direct_connection(url: str) -> bool:
            return _is_configured_local_url(config, url) or _is_authorized_insecure_wikidot_url(
                url, allow_insecure_session_transport_for
            )

        def _get_headers_for_url(url: str) -> dict[str, str] | None:
            parsed = urlparse(url)
            hostname = str(parsed.hostname).lower().rstrip(".")
            if parsed.scheme.lower() == "https" and (hostname == "wikidot.com" or hostname.endswith(".wikidot.com")):
                return request_headers
            if _is_authorized_insecure_wikidot_url(url, allow_insecure_session_transport_for):
                return request_headers
            if _is_configured_local_url(config, url):
                return request_headers

            return None

        async def _get(http_client: httpx.AsyncClient, url: str) -> httpx.Response:
            async with semaphore:
                attempt = 0
                while True:
                    try:
                        headers = _get_headers_for_url(url)
                        response = await http_client.get(url, headers=headers)
                        if headers is not None and 300 <= response.status_code < 400:
                            raise WikidotTransportSecurityException(
                                f"Redirect refused for credential-bearing direct request: {url}"
                            )
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
                        attempt += 1
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
                        attempt += 1

        async def _post(http_client: httpx.AsyncClient, url: str) -> httpx.Response:
            async with semaphore:
                attempt = 0
                while True:
                    try:
                        headers = _get_headers_for_url(url)
                        response = await http_client.post(url, headers=headers)
                        if headers is not None and 300 <= response.status_code < 400:
                            raise WikidotTransportSecurityException(
                                f"Redirect refused for credential-bearing direct request: {url}"
                            )
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
                        attempt += 1
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
                        attempt += 1

        async def _execute() -> list[httpx.Response | BaseException]:
            async with AsyncExitStack() as stack:
                normal_http_client: httpx.AsyncClient | None = None
                direct_http_client: httpx.AsyncClient | None = None

                if any(not _uses_direct_connection(url) for url in urls):
                    normal_http_client = await stack.enter_async_context(
                        httpx.AsyncClient(
                            timeout=request_timeout,
                            follow_redirects=False,
                            trust_env=True,
                        )
                    )
                if any(_uses_direct_connection(url) for url in urls):
                    direct_http_client = await stack.enter_async_context(
                        httpx.AsyncClient(
                            timeout=request_timeout,
                            follow_redirects=False,
                            trust_env=False,
                        )
                    )

                def _client_for_url(url: str) -> httpx.AsyncClient:
                    if _uses_direct_connection(url):
                        assert direct_http_client is not None
                        return direct_http_client
                    assert normal_http_client is not None
                    return normal_http_client

                if method == "GET":
                    return await asyncio.gather(
                        *[_get(_client_for_url(url), url) for url in urls],
                        return_exceptions=return_exceptions,
                    )
                return await asyncio.gather(
                    *[_post(_client_for_url(url), url) for url in urls],
                    return_exceptions=return_exceptions,
                )

        results: list[httpx.Response | BaseException] = run_coroutine(_execute())
        return [
            r if isinstance(r, httpx.Response) else r if isinstance(r, Exception) else Exception(str(r))
            for r in results
        ]
