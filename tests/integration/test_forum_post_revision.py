"""フォーラムポストリビジョンの統合テスト"""

from __future__ import annotations

import pytest

from wikidot.module.forum_post_revision import ForumPostRevisionCollection


def _all_forum_posts(site):
    categories = site.forum.categories
    if len(categories) == 0:
        pytest.skip("No forum categories found")

    posts = []
    for category in categories:
        for thread in category.threads:
            posts.extend(thread.posts)
    if len(posts) == 0:
        pytest.skip("No posts found in forum")
    return posts


class TestForumPostRevision:
    """フォーラムポストリビジョン操作テスト"""

    def test_1_get_revisions_from_edited_post(self, site) -> None:
        """1. 編集済みポストからリビジョン取得"""
        edited_posts = [post for post in _all_forum_posts(site) if post.has_revisions]
        if len(edited_posts) == 0:
            pytest.skip("No edited posts found in forum")

        revisions = edited_posts[0].revisions
        assert isinstance(revisions, ForumPostRevisionCollection)
        assert len(revisions) > 1
        assert revisions[0].rev_no == 0
        assert revisions[-1].rev_no == len(revisions) - 1

        for revision in revisions:
            assert revision.id is not None
            assert revision.rev_no >= 0
            assert revision.created_by is not None
            assert revision.created_at is not None

    def test_2_get_revisions_from_unedited_post(self, site) -> None:
        """2. 未編集ポストからリビジョン取得"""
        unedited_posts = [post for post in _all_forum_posts(site) if not post.has_revisions]
        if len(unedited_posts) == 0:
            pytest.skip("No unedited posts found in forum")

        revisions = unedited_posts[0].revisions
        assert isinstance(revisions, ForumPostRevisionCollection)
        assert len(revisions) == 1
        assert revisions[0].rev_no == 0

    def test_3_get_revision_html(self, site) -> None:
        """3. リビジョンHTML取得"""
        revision_sets = [post.revisions for post in _all_forum_posts(site) if len(post.revisions) > 0]
        if len(revision_sets) == 0:
            pytest.skip("No forum post revisions found")

        html = revision_sets[0][0].html
        assert html is not None
        assert isinstance(html, str)
        assert len(html) > 0

    def test_4_verify_collection_methods(self, site) -> None:
        """4. コレクションメソッドの検証"""
        revision_sets = [
            post.revisions for post in _all_forum_posts(site) if post.has_revisions and len(post.revisions) >= 2
        ]
        if len(revision_sets) == 0:
            pytest.skip("No edited posts with multiple revisions found in forum")

        revisions = revision_sets[0]
        first_revision = revisions[0]
        found = revisions.find(first_revision.id)
        assert found is not None
        assert found.id == first_revision.id

        found_by_rev_no = revisions.find_by_rev_no(0)
        assert found_by_rev_no is not None
        assert found_by_rev_no.rev_no == 0
