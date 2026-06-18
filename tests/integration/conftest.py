"""統合テスト用フィクスチャ"""

from __future__ import annotations

import os
import random
import string
import time
from collections.abc import Callable, Generator
from typing import TypeVar

import pytest

T = TypeVar("T")

# 統合テストは環境変数が設定されている場合のみ実行
WIKIDOT_USERNAME = os.environ.get("WIKIDOT_USERNAME")
WIKIDOT_PASSWORD = os.environ.get("WIKIDOT_PASSWORD")
TEST_SITE_UNIX_NAME = os.environ.get("WIKIDOT_TEST_SITE_UNIX_NAME")
TEST_EXISTING_PAGE_FULLNAME = os.environ.get("WIKIDOT_TEST_EXISTING_PAGE_FULLNAME", "integration-start")

# 認証情報が未設定の場合はスキップ
pytestmark = pytest.mark.skipif(
    not WIKIDOT_USERNAME or not WIKIDOT_PASSWORD or not TEST_SITE_UNIX_NAME,
    reason=("WIKIDOT_USERNAME, WIKIDOT_PASSWORD, and WIKIDOT_TEST_SITE_UNIX_NAME environment variables are required"),
)


def pytest_collection_modifyitems(config, items):
    skip_marker = pytest.mark.skip(
        reason=(
            "WIKIDOT_USERNAME, WIKIDOT_PASSWORD, and WIKIDOT_TEST_SITE_UNIX_NAME environment variables are required"
        )
    )
    for item in items:
        item_path = str(item.path).replace("\\", "/")
        if "/tests/integration/" in item_path:
            item.add_marker(pytest.mark.integration)
            if not (WIKIDOT_USERNAME and WIKIDOT_PASSWORD and TEST_SITE_UNIX_NAME):
                item.add_marker(skip_marker)


def generate_page_name(prefix: str = "test") -> str:
    """テスト用ランダムページ名を生成

    フォーマット: {prefix}-{timestamp}-{random6chars}
    例: test-1703404800-abc123
    """
    timestamp = int(time.time())
    random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}-{timestamp}-{random_suffix}"


@pytest.fixture(scope="session")
def credentials() -> dict[str, str]:
    """テスト用認証情報"""
    assert WIKIDOT_USERNAME is not None
    assert WIKIDOT_PASSWORD is not None
    return {
        "username": WIKIDOT_USERNAME,
        "password": WIKIDOT_PASSWORD,
    }


@pytest.fixture(scope="session")
def client(credentials: dict[str, str]):
    """認証済みクライアント（セッション全体で共有）"""
    from wikidot import Client

    _client = Client(
        username=credentials["username"],
        password=credentials["password"],
    )
    yield _client
    # セッション終了時にクリーンアップ


@pytest.fixture(scope="session")
def site(client):
    """テストサイト（セッション全体で共有）"""
    assert TEST_SITE_UNIX_NAME is not None
    _site = client.site.get(TEST_SITE_UNIX_NAME)
    if _site.page.get(TEST_EXISTING_PAGE_FULLNAME, raise_when_not_found=False) is None:
        try:
            _site.page.create(
                fullname=TEST_EXISTING_PAGE_FULLNAME,
                title="Integration Start",
                source="Existing page for wikidot.py integration tests.",
                comment="Create integration test existing page",
            )
        except Exception as exc:
            if exc.__class__.__name__ != "NotFoundException":
                raise
        wait_for_condition(
            lambda: _site.page.get(TEST_EXISTING_PAGE_FULLNAME, raise_when_not_found=False),
            lambda page: page is not None,
            max_retries=10,
            interval=2.0,
        )
    return _site


@pytest.fixture
def page_name_generator() -> Callable[[str], str]:
    """ページ名生成ヘルパー"""
    return generate_page_name


@pytest.fixture
def cleanup_pages(site) -> Generator[list[str], None, None]:
    """テスト終了時にページをクリーンアップ

    使用方法:
        def test_something(site, cleanup_pages):
            page_name = "test-page"
            cleanup_pages.append(page_name)
            # ... ページ作成
    """
    pages_to_cleanup: list[str] = []
    yield pages_to_cleanup

    cleanup_errors: list[str] = []
    for fullname in pages_to_cleanup:
        try:
            page = site.page.get(fullname, raise_when_not_found=False)
            if page is not None:
                page.destroy()
        except Exception as e:
            cleanup_errors.append(f"{fullname}: {e}")
    if cleanup_errors:
        pytest.fail("Failed to cleanup integration test pages: " + "; ".join(cleanup_errors))


def wait_for_condition(
    fn: Callable[[], T],
    predicate: Callable[[T], bool],
    max_retries: int = 5,
    interval: float = 1.0,
) -> T:
    """条件が満たされるまでリトライする

    Wikidot APIのeventual consistencyを考慮し、
    期待する条件が満たされるまでリトライを行う。

    Parameters
    ----------
    fn : Callable[[], T]
        値を取得する関数
    predicate : Callable[[T], bool]
        条件を判定する関数
    max_retries : int, default 5
        最大リトライ回数
    interval : float, default 1.0
        リトライ間隔（秒）

    Returns
    -------
    T
        条件を満たした値

    Raises
    ------
    AssertionError
        条件を満たさないままリトライ上限に達した場合
    """
    for _ in range(max_retries):
        time.sleep(interval)
        value = fn()
        if predicate(value):
            return value
    raise AssertionError(f"Condition not met after {max_retries} retries")
