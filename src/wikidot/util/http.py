"""HTTP utilities with retry mechanism."""

import asyncio
import math
import random
import time

import httpx


def _is_retryable_status(status_code: int) -> bool:
    """Check if HTTP status code is retryable (5xx server errors)."""
    return 500 <= status_code < 600


def _validate_bool_option(field: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


def _validate_positive_int_option(field: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be a positive integer")
    if value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _validate_non_negative_number_option(field: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field} must be a non-negative number")
    numeric_value = float(value)
    if not math.isfinite(numeric_value) or numeric_value < 0:
        raise ValueError(f"{field} must be a non-negative number")
    return numeric_value


def _validate_positive_number_option(field: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field} must be a positive number")
    numeric_value = float(value)
    if not math.isfinite(numeric_value) or numeric_value <= 0:
        raise ValueError(f"{field} must be a positive number")
    return numeric_value


def _validate_retry_options(
    *,
    attempt_limit: object,
    retry_interval: object,
    max_backoff: object,
    backoff_factor: object,
) -> tuple[int, float, float, float]:
    return (
        _validate_positive_int_option("attempt_limit", attempt_limit),
        _validate_non_negative_number_option("retry_interval", retry_interval),
        _validate_non_negative_number_option("max_backoff", max_backoff),
        _validate_non_negative_number_option("backoff_factor", backoff_factor),
    )


def _calculate_exponential_backoff(
    retry_count: int,
    base_interval: float,
    backoff_factor: float,
    max_backoff: float,
) -> float:
    exponent = retry_count - 1

    try:
        return (backoff_factor**exponent) * base_interval
    except OverflowError:
        pass

    if base_interval == 0:
        return 0.0

    try:
        backoff_log = math.log(base_interval) + exponent * math.log(backoff_factor)
    except (OverflowError, ValueError):
        return max_backoff

    if max_backoff == 0 or backoff_log >= math.log(max_backoff):
        return max_backoff

    try:
        return math.exp(backoff_log)
    except OverflowError:
        return max_backoff


def calculate_backoff(
    retry_count: int,
    base_interval: float,
    backoff_factor: float,
    max_backoff: float,
) -> float:
    """Calculate backoff time with exponential backoff and jitter.

    Parameters
    ----------
    retry_count
        Current retry count (1-based)
    base_interval
        Base interval in seconds
    backoff_factor
        Exponential backoff factor
    max_backoff
        Maximum backoff time in seconds

    Returns
    -------
    float
        Backoff time in seconds
    """
    retry_count = _validate_positive_int_option("retry_count", retry_count)
    base_interval = _validate_non_negative_number_option("base_interval", base_interval)
    backoff_factor = _validate_non_negative_number_option("backoff_factor", backoff_factor)
    max_backoff = _validate_non_negative_number_option("max_backoff", max_backoff)

    backoff = _calculate_exponential_backoff(retry_count, base_interval, backoff_factor, max_backoff)
    if not math.isfinite(backoff) or backoff >= max_backoff:
        return max_backoff
    jitter = random.uniform(0, backoff * 0.1)
    return min(backoff + jitter, max_backoff)


async def async_get_with_retry(
    url: str,
    *,
    timeout: float = 20.0,
    attempt_limit: int = 5,
    retry_interval: float = 1.0,
    max_backoff: float = 60.0,
    backoff_factor: float = 2.0,
    headers: dict[str, str] | None = None,
    follow_redirects: bool = True,
) -> httpx.Response:
    """Async GET request with retry on timeout/network errors.

    Parameters
    ----------
    url
        URL to fetch
    timeout
        Request timeout in seconds
    attempt_limit
        Maximum number of attempts
    retry_interval
        Base retry interval in seconds
    max_backoff
        Maximum backoff time in seconds
    backoff_factor
        Exponential backoff factor
    headers
        Optional HTTP headers
    follow_redirects
        Whether to follow redirects

    Returns
    -------
    httpx.Response
        HTTP response

    Raises
    ------
    httpx.TimeoutException
        If all retries exhausted due to timeout
    httpx.NetworkError
        If all retries exhausted due to network error
    httpx.HTTPStatusError
        If all retries exhausted due to HTTP error
    """
    follow_redirects = _validate_bool_option("follow_redirects", follow_redirects)
    timeout = _validate_positive_number_option("timeout", timeout)
    attempt_limit, retry_interval, max_backoff, backoff_factor = _validate_retry_options(
        attempt_limit=attempt_limit,
        retry_interval=retry_interval,
        max_backoff=max_backoff,
        backoff_factor=backoff_factor,
    )

    for attempt in range(attempt_limit):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers, follow_redirects=follow_redirects)
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


def sync_get_with_retry(
    url: str,
    *,
    timeout: float = 20.0,
    attempt_limit: int = 5,
    retry_interval: float = 1.0,
    max_backoff: float = 60.0,
    backoff_factor: float = 2.0,
    headers: dict[str, str] | None = None,
    follow_redirects: bool = True,
    raise_for_status: bool = True,
) -> httpx.Response:
    """Sync GET request with retry on timeout/network errors.

    Parameters
    ----------
    url
        URL to fetch
    timeout
        Request timeout in seconds
    attempt_limit
        Maximum number of attempts
    retry_interval
        Base retry interval in seconds
    max_backoff
        Maximum backoff time in seconds
    backoff_factor
        Exponential backoff factor
    headers
        Optional HTTP headers
    follow_redirects
        Whether to follow redirects
    raise_for_status
        Whether to raise HTTPStatusError for 4xx/5xx responses

    Returns
    -------
    httpx.Response
        HTTP response

    Raises
    ------
    httpx.TimeoutException
        If all retries exhausted due to timeout
    httpx.NetworkError
        If all retries exhausted due to network error
    httpx.HTTPStatusError
        If all retries exhausted due to HTTP error (when raise_for_status=True)
    """
    follow_redirects = _validate_bool_option("follow_redirects", follow_redirects)
    raise_for_status = _validate_bool_option("raise_for_status", raise_for_status)
    timeout = _validate_positive_number_option("timeout", timeout)
    attempt_limit, retry_interval, max_backoff, backoff_factor = _validate_retry_options(
        attempt_limit=attempt_limit,
        retry_interval=retry_interval,
        max_backoff=max_backoff,
        backoff_factor=backoff_factor,
    )

    for attempt in range(attempt_limit):
        try:
            response = httpx.get(
                url,
                headers=headers,
                timeout=timeout,
                follow_redirects=follow_redirects,
            )
            if raise_for_status:
                response.raise_for_status()
            elif _is_retryable_status(response.status_code) and attempt < attempt_limit - 1:
                backoff = calculate_backoff(
                    attempt + 1,
                    retry_interval,
                    backoff_factor,
                    max_backoff,
                )
                time.sleep(backoff)
                continue
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
            time.sleep(backoff)
        except (httpx.TimeoutException, httpx.NetworkError):
            if attempt >= attempt_limit - 1:
                raise
            backoff = calculate_backoff(
                attempt + 1,
                retry_interval,
                backoff_factor,
                max_backoff,
            )
            time.sleep(backoff)
    raise RuntimeError("Unreachable")


def sync_post_with_retry(
    url: str,
    *,
    data: dict | None = None,
    timeout: float = 20.0,
    attempt_limit: int = 5,
    retry_interval: float = 1.0,
    max_backoff: float = 60.0,
    backoff_factor: float = 2.0,
    headers: dict[str, str] | None = None,
    raise_for_status: bool = True,
) -> httpx.Response:
    """Sync POST request with retry on timeout/network errors.

    Parameters
    ----------
    url
        URL to post to
    data
        Form data to send
    timeout
        Request timeout in seconds
    attempt_limit
        Maximum number of attempts
    retry_interval
        Base retry interval in seconds
    max_backoff
        Maximum backoff time in seconds
    backoff_factor
        Exponential backoff factor
    headers
        Optional HTTP headers
    raise_for_status
        Whether to raise HTTPStatusError for 4xx/5xx responses

    Returns
    -------
    httpx.Response
        HTTP response

    Raises
    ------
    httpx.TimeoutException
        If all retries exhausted due to timeout
    httpx.NetworkError
        If all retries exhausted due to network error
    httpx.HTTPStatusError
        If all retries exhausted due to HTTP error (when raise_for_status=True)
    """
    raise_for_status = _validate_bool_option("raise_for_status", raise_for_status)
    timeout = _validate_positive_number_option("timeout", timeout)
    attempt_limit, retry_interval, max_backoff, backoff_factor = _validate_retry_options(
        attempt_limit=attempt_limit,
        retry_interval=retry_interval,
        max_backoff=max_backoff,
        backoff_factor=backoff_factor,
    )

    for attempt in range(attempt_limit):
        try:
            response = httpx.post(
                url,
                data=data,
                headers=headers,
                timeout=timeout,
            )
            if raise_for_status:
                response.raise_for_status()
            elif _is_retryable_status(response.status_code) and attempt < attempt_limit - 1:
                backoff = calculate_backoff(
                    attempt + 1,
                    retry_interval,
                    backoff_factor,
                    max_backoff,
                )
                time.sleep(backoff)
                continue
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
            time.sleep(backoff)
        except (httpx.TimeoutException, httpx.NetworkError):
            if attempt >= attempt_limit - 1:
                raise
            backoff = calculate_backoff(
                attempt + 1,
                retry_interval,
                backoff_factor,
                max_backoff,
            )
            time.sleep(backoff)
    raise RuntimeError("Unreachable")
