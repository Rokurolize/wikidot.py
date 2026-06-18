"""ページライフサイクル（作成→取得→編集→削除）の統合テスト"""

from __future__ import annotations

import httpx
import pytest
from bs4 import BeautifulSoup

from .conftest import generate_page_name, wait_for_condition


def fetch_page_document_title(url: str) -> str:
    response = httpx.get(url, follow_redirects=True, timeout=20.0)
    response.raise_for_status()
    title_element = BeautifulSoup(response.text, "lxml").title
    assert title_element is not None
    return title_element.get_text(strip=True)


def _has_source_text(page, expected: str) -> bool:
    try:
        return page is not None and page.source is not None and page.source.wiki_text == expected
    except Exception:
        return False


class TestPageLifecycle:
    """ページライフサイクルテスト

    テストは順番に実行され、前のテストで作成したページを使用する。
    """

    @pytest.fixture(autouse=True)
    def setup(self, site):
        """テストセットアップ"""
        self.site = site
        self.page_name = generate_page_name("lifecycle")
        self.page = None
        yield
        # クリーンアップ
        cleanup_errors = []
        if self.page is not None:
            try:
                self.page.destroy()
            except Exception as exc:
                cleanup_errors.append(f"{self.page_name}: {exc}")
        else:
            # ページオブジェクトがない場合は名前で削除を試行
            try:
                page = self.site.page.get(self.page_name, raise_when_not_found=False)
                if page is not None:
                    page.destroy()
            except Exception as exc:
                cleanup_errors.append(f"{self.page_name}: {exc}")
        if cleanup_errors:
            pytest.fail("Failed to cleanup integration test pages: " + "; ".join(cleanup_errors))

    def test_1_page_create(self):
        """1. ページ作成"""
        self.site.page.create(
            fullname=self.page_name,
            title="Test Page",
            source="This is test content.",
            comment="Initial creation",
        )
        # 作成確認
        self.page = wait_for_condition(
            lambda: self.site.page.get(self.page_name, raise_when_not_found=False),
            lambda page: page is not None,
            max_retries=10,
            interval=2.0,
        )
        assert self.page is not None
        assert self.page.fullname == self.page_name

    def test_2_page_get(self):
        """2. 作成ページ取得"""
        # まずページを作成
        self.site.page.create(
            fullname=self.page_name,
            title="Test Page",
            source="This is test content.",
        )
        self.page = wait_for_condition(
            lambda: self.site.page.get(self.page_name, raise_when_not_found=False),
            lambda page: page is not None and page.title == "Test Page",
            max_retries=10,
            interval=2.0,
        )

        assert self.page is not None
        assert self.page.fullname == self.page_name
        assert self.page.title == "Test Page"

    def test_3_page_source(self):
        """3. ページソース取得"""
        # まずページを作成
        self.site.page.create(
            fullname=self.page_name,
            title="Test Page",
            source="This is test content.",
        )
        self.page = wait_for_condition(
            lambda: self.site.page.get(self.page_name, raise_when_not_found=False),
            lambda page: _has_source_text(page, "This is test content."),
            max_retries=10,
            interval=2.0,
        )

        assert self.page is not None
        source = self.page.source
        assert source is not None
        assert source.wiki_text == "This is test content."

    def test_4_page_edit(self):
        """4. ページ編集"""
        # まずページを作成
        self.site.page.create(
            fullname=self.page_name,
            title="Test Page",
            source="Original content.",
        )
        self.page = wait_for_condition(
            lambda: self.site.page.get(self.page_name, raise_when_not_found=False),
            lambda page: _has_source_text(page, "Original content."),
            max_retries=10,
            interval=2.0,
        )
        assert self.page is not None

        # 編集
        self.page.edit(
            title="Updated Test Page",
            source="Updated content.",
            comment="Test edit",
        )

        # ListPagesModule can keep stale title metadata briefly; source and
        # rendered HTML reflect the saved edit more reliably.
        updated_page = wait_for_condition(
            lambda: self.site.page.get(self.page_name, raise_when_not_found=False),
            lambda page: _has_source_text(page, "Updated content."),
            max_retries=10,
            interval=2.0,
        )
        assert updated_page is not None
        assert updated_page.source.wiki_text == "Updated content."
        document_title = wait_for_condition(
            lambda: fetch_page_document_title(updated_page.get_url()),
            lambda title: title.startswith("Updated Test Page"),
            max_retries=10,
            interval=2.0,
        )
        assert document_title.startswith("Updated Test Page")

    def test_5_page_delete(self):
        """5. ページ削除"""
        # まずページを作成
        self.site.page.create(
            fullname=self.page_name,
            title="Test Page",
            source="Content to be deleted.",
        )
        self.page = wait_for_condition(
            lambda: self.site.page.get(self.page_name, raise_when_not_found=False),
            lambda page: page is not None,
            max_retries=10,
            interval=2.0,
        )
        assert self.page is not None

        # 削除
        self.page.destroy()
        self.page = None  # クリーンアップ不要

        deleted_page = wait_for_condition(
            lambda: self.site.page.get(self.page_name, raise_when_not_found=False),
            lambda page: page is None,
            max_retries=10,
            interval=2.0,
        )
        assert deleted_page is None
