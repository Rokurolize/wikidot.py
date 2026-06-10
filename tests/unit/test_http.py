"""HTTPユーティリティのユニットテスト

リトライ機構を持つHTTPリクエスト関数のテストを行う。
"""

import math
from typing import Any

import httpx
import pytest

from wikidot.util.http import (
    _is_retryable_status,
    calculate_backoff,
    sync_get_with_retry,
    sync_post_with_retry,
)


class TestIsRetryableStatus:
    """_is_retryable_status関数のテスト"""

    def test_5xx_is_retryable(self):
        """5xxエラーはリトライ可能"""
        assert _is_retryable_status(500) is True
        assert _is_retryable_status(502) is True
        assert _is_retryable_status(503) is True
        assert _is_retryable_status(599) is True

    def test_4xx_is_not_retryable(self):
        """4xxエラーはリトライ不可"""
        assert _is_retryable_status(400) is False
        assert _is_retryable_status(401) is False
        assert _is_retryable_status(403) is False
        assert _is_retryable_status(404) is False
        assert _is_retryable_status(499) is False

    def test_2xx_is_not_retryable(self):
        """2xxはリトライ不可"""
        assert _is_retryable_status(200) is False
        assert _is_retryable_status(201) is False
        assert _is_retryable_status(204) is False

    def test_3xx_is_not_retryable(self):
        """3xxはリトライ不可"""
        assert _is_retryable_status(301) is False
        assert _is_retryable_status(302) is False
        assert _is_retryable_status(304) is False


class TestCalculateBackoff:
    """calculate_backoff関数のテスト"""

    @pytest.mark.parametrize("retry_count", [None, True, "1", 0, -1, 1.5])
    def test_rejects_invalid_retry_count(self, retry_count: Any):
        """retry_countは1以上の整数として検証する"""
        with pytest.raises(ValueError, match="retry_count must be a positive integer"):
            calculate_backoff(retry_count, 1.0, 2.0, 60.0)

    @pytest.mark.parametrize("field", ["base_interval", "backoff_factor", "max_backoff"])
    @pytest.mark.parametrize("value", [None, True, "1", -0.1, float("nan"), float("inf"), -float("inf")])
    def test_rejects_invalid_numeric_backoff_options(self, field: str, value: Any):
        """backoffの数値オプションは非負数として検証する"""
        options = {
            "base_interval": 1.0,
            "backoff_factor": 2.0,
            "max_backoff": 60.0,
        }
        options[field] = value

        with pytest.raises(ValueError, match=f"{field} must be a non-negative number"):
            calculate_backoff(1, options["base_interval"], options["backoff_factor"], options["max_backoff"])

    def test_first_retry(self):
        """最初のリトライ（retry_count=1）"""
        result = calculate_backoff(1, 1.0, 2.0, 60.0)
        assert 1.0 <= result <= 1.1

    def test_second_retry(self):
        """2回目のリトライ（retry_count=2）"""
        result = calculate_backoff(2, 1.0, 2.0, 60.0)
        assert 2.0 <= result <= 2.2

    def test_third_retry(self):
        """3回目のリトライ（retry_count=3）"""
        result = calculate_backoff(3, 1.0, 2.0, 60.0)
        assert 4.0 <= result <= 4.4

    def test_respects_max_backoff(self):
        """max_backoffを超えない"""
        result = calculate_backoff(10, 1.0, 2.0, 60.0)
        assert result == 60.0

    def test_caps_large_exponential_backoff_before_overflow(self):
        """max_backoffを超える巨大な指数バックオフも上限で丸める"""
        result = calculate_backoff(1025, 1.0, 2.0, 60.0)
        assert result == 60.0

    def test_large_exponential_backoff_preserves_tiny_base_below_cap(self):
        """指数部だけが巨大な場合も上限未満なら有限のバックオフを返す"""
        expected_backoff = math.exp(math.log(1e-308) + 1024 * math.log(2.0))

        result = calculate_backoff(1025, 1e-308, 2.0, 60.0)

        assert expected_backoff <= result <= expected_backoff * 1.1


class TestSyncGetWithRetry:
    """sync_get_with_retry関数のテスト"""

    @pytest.mark.parametrize("timeout", [None, True, "1", 0, -0.1, float("nan"), float("inf"), -float("inf")])
    def test_rejects_invalid_timeout_before_request(self, httpx_mock, timeout: Any):
        """timeoutはHTTPリクエスト前に正の数値として検証する"""
        with pytest.raises(ValueError, match="timeout must be a positive number"):
            sync_get_with_retry("https://example.com/test", timeout=timeout)

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("attempt_limit", [None, True, "3", 0, -1, 1.5])
    def test_rejects_invalid_attempt_limit_before_request(self, httpx_mock, attempt_limit: Any):
        """attempt_limitはHTTPリクエスト前に1以上の整数として検証する"""
        with pytest.raises(ValueError, match="attempt_limit must be a positive integer"):
            sync_get_with_retry("https://example.com/test", attempt_limit=attempt_limit)

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("field", ["retry_interval", "max_backoff", "backoff_factor"])
    @pytest.mark.parametrize("value", [None, True, "1", -0.1, float("nan"), float("inf"), -float("inf")])
    def test_rejects_invalid_numeric_retry_options_before_request(self, httpx_mock, field: str, value: Any):
        """retry系の数値オプションはHTTPリクエスト前に非負数として検証する"""
        kwargs: dict[str, Any] = {field: value}

        with pytest.raises(ValueError, match=f"{field} must be a non-negative number"):
            sync_get_with_retry("https://example.com/test", **kwargs)

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("follow_redirects", [None, "false", 0, 1])
    def test_rejects_non_bool_follow_redirects_before_request(self, httpx_mock, follow_redirects: Any):
        """follow_redirectsはHTTPリクエスト前に真偽値として検証する"""
        with pytest.raises(ValueError, match="follow_redirects must be a boolean"):
            sync_get_with_retry("https://example.com/test", follow_redirects=follow_redirects)

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("raise_for_status", [None, "false", 0, 1])
    def test_rejects_non_bool_raise_for_status_before_request(self, httpx_mock, raise_for_status: Any):
        """raise_for_statusはHTTPリクエスト前に真偽値として検証する"""
        with pytest.raises(ValueError, match="raise_for_status must be a boolean"):
            sync_get_with_retry("https://example.com/test", raise_for_status=raise_for_status)

        assert httpx_mock.get_requests() == []

    def test_success_on_first_attempt(self, httpx_mock):
        """最初の試行で成功"""
        httpx_mock.add_response(url="https://example.com/test", status_code=200)

        response = sync_get_with_retry(
            "https://example.com/test",
            attempt_limit=3,
            retry_interval=0.01,
        )

        assert response.status_code == 200

    def test_retry_on_5xx_then_success(self, httpx_mock):
        """5xxエラー後にリトライして成功"""
        httpx_mock.add_response(url="https://example.com/test", status_code=500)
        httpx_mock.add_response(url="https://example.com/test", status_code=200)

        response = sync_get_with_retry(
            "https://example.com/test",
            attempt_limit=3,
            retry_interval=0.01,
        )

        assert response.status_code == 200

    def test_no_retry_on_4xx(self, httpx_mock):
        """4xxエラーはリトライしない"""
        httpx_mock.add_response(url="https://example.com/test", status_code=404)

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            sync_get_with_retry(
                "https://example.com/test",
                attempt_limit=3,
                retry_interval=0.01,
            )

        assert exc_info.value.response.status_code == 404

    def test_max_retries_exceeded_on_5xx(self, httpx_mock):
        """5xxでリトライ上限に達した場合"""
        httpx_mock.add_response(url="https://example.com/test", status_code=500)
        httpx_mock.add_response(url="https://example.com/test", status_code=500)
        httpx_mock.add_response(url="https://example.com/test", status_code=500)

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            sync_get_with_retry(
                "https://example.com/test",
                attempt_limit=3,
                retry_interval=0.01,
            )

        assert exc_info.value.response.status_code == 500

    def test_retry_on_timeout(self, httpx_mock):
        """タイムアウト後にリトライして成功"""
        httpx_mock.add_exception(httpx.TimeoutException("Timeout"))
        httpx_mock.add_response(url="https://example.com/test", status_code=200)

        response = sync_get_with_retry(
            "https://example.com/test",
            attempt_limit=3,
            retry_interval=0.01,
        )

        assert response.status_code == 200

    def test_max_retries_exceeded_on_timeout(self, httpx_mock):
        """タイムアウトでリトライ上限に達した場合"""
        httpx_mock.add_exception(httpx.TimeoutException("Timeout"))
        httpx_mock.add_exception(httpx.TimeoutException("Timeout"))
        httpx_mock.add_exception(httpx.TimeoutException("Timeout"))

        with pytest.raises(httpx.TimeoutException):
            sync_get_with_retry(
                "https://example.com/test",
                attempt_limit=3,
                retry_interval=0.01,
            )

    def test_retry_on_network_error(self, httpx_mock):
        """ネットワークエラー後にリトライして成功"""
        httpx_mock.add_exception(httpx.NetworkError("Connection failed"))
        httpx_mock.add_response(url="https://example.com/test", status_code=200)

        response = sync_get_with_retry(
            "https://example.com/test",
            attempt_limit=3,
            retry_interval=0.01,
        )

        assert response.status_code == 200

    def test_raise_for_status_false(self, httpx_mock):
        """raise_for_status=Falseの場合はエラーでも返す"""
        httpx_mock.add_response(url="https://example.com/test", status_code=404)

        response = sync_get_with_retry(
            "https://example.com/test",
            attempt_limit=3,
            retry_interval=0.01,
            raise_for_status=False,
        )

        assert response.status_code == 404

    def test_raise_for_status_false_retries_5xx(self, httpx_mock):
        """raise_for_status=Falseでも5xxはリトライする"""
        httpx_mock.add_response(url="https://example.com/test", status_code=500)
        httpx_mock.add_response(url="https://example.com/test", status_code=200)

        response = sync_get_with_retry(
            "https://example.com/test",
            attempt_limit=3,
            retry_interval=0.01,
            raise_for_status=False,
        )

        assert response.status_code == 200
        assert len(httpx_mock.get_requests()) == 2


class TestSyncPostWithRetry:
    """sync_post_with_retry関数のテスト"""

    @pytest.mark.parametrize("timeout", [None, True, "1", 0, -0.1, float("nan"), float("inf"), -float("inf")])
    def test_rejects_invalid_timeout_before_request(self, httpx_mock, timeout: Any):
        """timeoutはHTTPリクエスト前に正の数値として検証する"""
        with pytest.raises(ValueError, match="timeout must be a positive number"):
            sync_post_with_retry("https://example.com/test", timeout=timeout)

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("attempt_limit", [None, True, "3", 0, -1, 1.5])
    def test_rejects_invalid_attempt_limit_before_request(self, httpx_mock, attempt_limit: Any):
        """attempt_limitはHTTPリクエスト前に1以上の整数として検証する"""
        with pytest.raises(ValueError, match="attempt_limit must be a positive integer"):
            sync_post_with_retry("https://example.com/test", attempt_limit=attempt_limit)

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("field", ["retry_interval", "max_backoff", "backoff_factor"])
    @pytest.mark.parametrize("value", [None, True, "1", -0.1, float("nan"), float("inf"), -float("inf")])
    def test_rejects_invalid_numeric_retry_options_before_request(self, httpx_mock, field: str, value: Any):
        """retry系の数値オプションはHTTPリクエスト前に非負数として検証する"""
        kwargs: dict[str, Any] = {field: value}

        with pytest.raises(ValueError, match=f"{field} must be a non-negative number"):
            sync_post_with_retry("https://example.com/test", **kwargs)

        assert httpx_mock.get_requests() == []

    @pytest.mark.parametrize("raise_for_status", [None, "false", 0, 1])
    def test_rejects_non_bool_raise_for_status_before_request(self, httpx_mock, raise_for_status: Any):
        """raise_for_statusはHTTPリクエスト前に真偽値として検証する"""
        with pytest.raises(ValueError, match="raise_for_status must be a boolean"):
            sync_post_with_retry("https://example.com/test", raise_for_status=raise_for_status)

        assert httpx_mock.get_requests() == []

    def test_success_on_first_attempt(self, httpx_mock):
        """最初の試行で成功"""
        httpx_mock.add_response(url="https://example.com/test", status_code=200, method="POST")

        response = sync_post_with_retry(
            "https://example.com/test",
            data={"key": "value"},
            attempt_limit=3,
            retry_interval=0.01,
        )

        assert response.status_code == 200

    def test_retry_on_5xx_then_success(self, httpx_mock):
        """5xxエラー後にリトライして成功"""
        httpx_mock.add_response(url="https://example.com/test", status_code=500, method="POST")
        httpx_mock.add_response(url="https://example.com/test", status_code=200, method="POST")

        response = sync_post_with_retry(
            "https://example.com/test",
            data={"key": "value"},
            attempt_limit=3,
            retry_interval=0.01,
        )

        assert response.status_code == 200

    def test_no_retry_on_4xx(self, httpx_mock):
        """4xxエラーはリトライしない"""
        httpx_mock.add_response(url="https://example.com/test", status_code=400, method="POST")

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            sync_post_with_retry(
                "https://example.com/test",
                data={"key": "value"},
                attempt_limit=3,
                retry_interval=0.01,
            )

        assert exc_info.value.response.status_code == 400

    def test_retry_on_timeout(self, httpx_mock):
        """タイムアウト後にリトライして成功"""
        httpx_mock.add_exception(httpx.TimeoutException("Timeout"), method="POST")
        httpx_mock.add_response(url="https://example.com/test", status_code=200, method="POST")

        response = sync_post_with_retry(
            "https://example.com/test",
            data={"key": "value"},
            attempt_limit=3,
            retry_interval=0.01,
        )

        assert response.status_code == 200

    def test_raise_for_status_false(self, httpx_mock):
        """raise_for_status=Falseの場合はエラーでも返す"""
        httpx_mock.add_response(url="https://example.com/test", status_code=400, method="POST")

        response = sync_post_with_retry(
            "https://example.com/test",
            data={"key": "value"},
            attempt_limit=3,
            retry_interval=0.01,
            raise_for_status=False,
        )

        assert response.status_code == 400

    def test_raise_for_status_false_retries_5xx(self, httpx_mock):
        """raise_for_status=Falseでも5xxはリトライする"""
        httpx_mock.add_response(url="https://example.com/test", status_code=500, method="POST")
        httpx_mock.add_response(url="https://example.com/test", status_code=200, method="POST")

        response = sync_post_with_retry(
            "https://example.com/test",
            data={"key": "value"},
            attempt_limit=3,
            retry_interval=0.01,
            raise_for_status=False,
        )

        assert response.status_code == 200
        assert len(httpx_mock.get_requests()) == 2


class TestAsyncGetWithRetry:
    """async_get_with_retry関数のテスト"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("timeout", [None, True, "1", 0, -0.1, float("nan"), float("inf"), -float("inf")])
    async def test_rejects_invalid_timeout_before_request(self, httpx_mock, timeout: Any):
        """timeoutはHTTPリクエスト前に正の数値として検証する"""
        from wikidot.util.http import async_get_with_retry

        with pytest.raises(ValueError, match="timeout must be a positive number"):
            await async_get_with_retry("https://example.com/test", timeout=timeout)

        assert httpx_mock.get_requests() == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize("attempt_limit", [None, True, "3", 0, -1, 1.5])
    async def test_rejects_invalid_attempt_limit_before_request(self, httpx_mock, attempt_limit: Any):
        """attempt_limitはHTTPリクエスト前に1以上の整数として検証する"""
        from wikidot.util.http import async_get_with_retry

        with pytest.raises(ValueError, match="attempt_limit must be a positive integer"):
            await async_get_with_retry("https://example.com/test", attempt_limit=attempt_limit)

        assert httpx_mock.get_requests() == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize("field", ["retry_interval", "max_backoff", "backoff_factor"])
    @pytest.mark.parametrize("value", [None, True, "1", -0.1, float("nan"), float("inf"), -float("inf")])
    async def test_rejects_invalid_numeric_retry_options_before_request(self, httpx_mock, field: str, value: Any):
        """retry系の数値オプションはHTTPリクエスト前に非負数として検証する"""
        from wikidot.util.http import async_get_with_retry

        kwargs: dict[str, Any] = {field: value}

        with pytest.raises(ValueError, match=f"{field} must be a non-negative number"):
            await async_get_with_retry("https://example.com/test", **kwargs)

        assert httpx_mock.get_requests() == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize("follow_redirects", [None, "false", 0, 1])
    async def test_rejects_non_bool_follow_redirects_before_request(self, httpx_mock, follow_redirects: Any):
        """follow_redirectsはHTTPリクエスト前に真偽値として検証する"""
        from wikidot.util.http import async_get_with_retry

        with pytest.raises(ValueError, match="follow_redirects must be a boolean"):
            await async_get_with_retry("https://example.com/test", follow_redirects=follow_redirects)

        assert httpx_mock.get_requests() == []

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self, httpx_mock):
        """最初の試行で成功"""
        from wikidot.util.http import async_get_with_retry

        httpx_mock.add_response(url="https://example.com/test", status_code=200)

        response = await async_get_with_retry(
            "https://example.com/test",
            attempt_limit=3,
            retry_interval=0.01,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_retry_on_5xx_then_success(self, httpx_mock):
        """5xxエラー後にリトライして成功"""
        from wikidot.util.http import async_get_with_retry

        httpx_mock.add_response(url="https://example.com/test", status_code=500)
        httpx_mock.add_response(url="https://example.com/test", status_code=200)

        response = await async_get_with_retry(
            "https://example.com/test",
            attempt_limit=3,
            retry_interval=0.01,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_no_retry_on_4xx(self, httpx_mock):
        """4xxエラーはリトライしない"""
        from wikidot.util.http import async_get_with_retry

        httpx_mock.add_response(url="https://example.com/test", status_code=404)

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await async_get_with_retry(
                "https://example.com/test",
                attempt_limit=3,
                retry_interval=0.01,
            )

        assert exc_info.value.response.status_code == 404

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, httpx_mock):
        """タイムアウト後にリトライして成功"""
        from wikidot.util.http import async_get_with_retry

        httpx_mock.add_exception(httpx.TimeoutException("Timeout"))
        httpx_mock.add_response(url="https://example.com/test", status_code=200)

        response = await async_get_with_retry(
            "https://example.com/test",
            attempt_limit=3,
            retry_interval=0.01,
        )

        assert response.status_code == 200
