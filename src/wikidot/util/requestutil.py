import asyncio
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx

from .async_helper import run_coroutine
from .http import _is_retryable_status, calculate_backoff

if TYPE_CHECKING:
    from wikidot.module.client import Client


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
        config = client.amc_client.config
        semaphore = asyncio.Semaphore(config.semaphore_limit)
        method = method.upper()

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

        async def _get(url: str) -> httpx.Response:
            async with semaphore:
                for attempt in range(config.attempt_limit):
                    try:
                        async with httpx.AsyncClient(timeout=config.request_timeout) as _client:
                            response = await _client.get(url, headers=_get_headers_for_url(url))
                            response.raise_for_status()
                            return response
                    except httpx.HTTPStatusError as e:
                        # Don't retry 4xx errors - they are client errors that won't change on retry
                        if not _is_retryable_status(e.response.status_code):
                            raise
                        if attempt >= config.attempt_limit - 1:
                            raise
                        backoff = calculate_backoff(
                            attempt + 1,
                            config.retry_interval,
                            config.backoff_factor,
                            config.max_backoff,
                        )
                        await asyncio.sleep(backoff)
                    except (httpx.TimeoutException, httpx.NetworkError):
                        if attempt >= config.attempt_limit - 1:
                            raise
                        backoff = calculate_backoff(
                            attempt + 1,
                            config.retry_interval,
                            config.backoff_factor,
                            config.max_backoff,
                        )
                        await asyncio.sleep(backoff)
                raise RuntimeError("Unreachable")

        async def _post(url: str) -> httpx.Response:
            async with semaphore:
                for attempt in range(config.attempt_limit):
                    try:
                        async with httpx.AsyncClient(timeout=config.request_timeout) as _client:
                            response = await _client.post(url, headers=_get_headers_for_url(url))
                            response.raise_for_status()
                            return response
                    except httpx.HTTPStatusError as e:
                        # Don't retry 4xx errors - they are client errors that won't change on retry
                        if not _is_retryable_status(e.response.status_code):
                            raise
                        if attempt >= config.attempt_limit - 1:
                            raise
                        backoff = calculate_backoff(
                            attempt + 1,
                            config.retry_interval,
                            config.backoff_factor,
                            config.max_backoff,
                        )
                        await asyncio.sleep(backoff)
                    except (httpx.TimeoutException, httpx.NetworkError):
                        if attempt >= config.attempt_limit - 1:
                            raise
                        backoff = calculate_backoff(
                            attempt + 1,
                            config.retry_interval,
                            config.backoff_factor,
                            config.max_backoff,
                        )
                        await asyncio.sleep(backoff)
                raise RuntimeError("Unreachable")

        async def _execute() -> list[httpx.Response | BaseException]:
            if method == "GET":
                return await asyncio.gather(*[_get(url) for url in urls], return_exceptions=return_exceptions)
            elif method == "POST":
                return await asyncio.gather(*[_post(url) for url in urls], return_exceptions=return_exceptions)
            else:
                raise ValueError("Invalid method")

        results: list[httpx.Response | BaseException] = run_coroutine(_execute())
        return [
            r if isinstance(r, httpx.Response) else r if isinstance(r, Exception) else Exception(str(r))
            for r in results
        ]
