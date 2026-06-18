"""ページ投票の統合テスト"""

from __future__ import annotations

import pytest

from .conftest import TEST_EXISTING_PAGE_FULLNAME


class TestPageVotes:
    """ページ投票操作テスト"""

    def test_1_get_votes_from_existing_page(self, site):
        """1. 既存ページの投票情報取得"""
        page = site.page.get(TEST_EXISTING_PAGE_FULLNAME)
        assert page is not None

        votes = page.votes
        assert votes is not None
        if len(votes) == 0:
            pytest.skip("No votes found on existing integration page")
        assert votes[0].page is page

    def test_2_votes_properties(self, site):
        """2. 投票プロパティ確認"""
        page = site.page.get(TEST_EXISTING_PAGE_FULLNAME)
        assert page is not None

        votes = page.votes
        # 投票がある場合はプロパティを確認
        if len(votes) == 0:
            pytest.skip("No votes found on existing integration page")
        vote = votes[0]
        assert vote.page is not None
        assert vote.user is not None
        assert vote.value is not None
