"""ForumPostモジュールのユニットテスト"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

from wikidot.common import exceptions
from wikidot.module.forum_post import ForumPost, ForumPostCollection
from wikidot.module.forum_post_revision import ForumPostRevisionCollection
from wikidot.module.forum_thread import ForumThread

# ============================================================
# ForumPostCollectionテスト
# ============================================================


class TestForumPostCollectionInit:
    """ForumPostCollectionの初期化テスト"""

    def test_init_with_thread_and_empty_posts(self, mock_forum_thread_no_http: ForumThread) -> None:
        """スレッドと空の投稿リストで初期化できる"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [])
        assert collection.thread == mock_forum_thread_no_http
        assert len(collection) == 0

    def test_init_with_thread_and_posts(
        self, mock_forum_thread_no_http: ForumThread, mock_forum_post_no_http: ForumPost
    ) -> None:
        """スレッドと投稿リストで初期化できる"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])
        assert collection.thread == mock_forum_thread_no_http
        assert len(collection) == 1

    def test_find_existing(self, mock_forum_thread_no_http: ForumThread, mock_forum_post_no_http: ForumPost) -> None:
        """存在する投稿をIDで検索できる"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])
        found = collection.find(5001)
        assert found is not None
        assert found.id == 5001

    def test_find_nonexistent(self, mock_forum_thread_no_http: ForumThread) -> None:
        """存在しない投稿を検索するとNoneを返す"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [])
        found = collection.find(9999)
        assert found is None


class TestForumPostCollectionParse:
    """ForumPostCollection._parseのテスト"""

    def test_parse_success(self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]) -> None:
        """投稿一覧を正常にパースできる"""
        html = BeautifulSoup(forum_posts_in_thread["body"], "lxml")
        posts = ForumPostCollection._parse(mock_forum_thread_no_http, html)
        assert len(posts) == 2

    def test_parse_fields(self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]) -> None:
        """投稿の各フィールドが正しくパースされる"""
        html = BeautifulSoup(forum_posts_in_thread["body"], "lxml")
        posts = ForumPostCollection._parse(mock_forum_thread_no_http, html)

        # 1つ目の投稿を検証
        post = posts[0]
        assert post.id == 5001
        assert post.title == "Test Post Title"
        assert "<p>Test post content</p>" in post.text

        # 2つ目の投稿を検証
        post2 = posts[1]
        assert post2.id == 5002
        assert post2.title == "Second Post"

    def test_parse_ignores_pseudo_posts(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_with_pseudo_post: dict[str, Any]
    ) -> None:
        """コンテンツ内の疑似ポストを無視してトップレベルの投稿のみをパースする"""
        html = BeautifulSoup(forum_posts_with_pseudo_post["body"], "lxml")
        posts = ForumPostCollection._parse(mock_forum_thread_no_http, html)

        # 疑似ポストを除いてトップレベルの投稿のみ（2件）
        assert len(posts) == 2
        assert posts[0].id == 5001
        assert posts[1].id == 5002

    def test_parse_pseudo_post_user_not_mixed(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_with_pseudo_post: dict[str, Any]
    ) -> None:
        """疑似ポスト内のユーザー情報が本物の投稿に混入しない"""
        html = BeautifulSoup(forum_posts_with_pseudo_post["body"], "lxml")
        posts = ForumPostCollection._parse(mock_forum_thread_no_http, html)

        # 1つ目の投稿者はtest_user_1（疑似ポスト内のtest_user_3/4ではない）
        assert posts[0].created_by.name == "test_user_1"
        # 2つ目の投稿者はtest_user_2
        assert posts[1].created_by.name == "test_user_2"

    def test_parse_ignores_pseudo_posts_with_post_id(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_with_pseudo_post: dict[str, Any]
    ) -> None:
        """post ID風のidを持つコンテンツ内疑似ポストも無視する"""
        body = forum_posts_with_pseudo_post["body"].replace(
            '<div class="collapsible-block post">',
            '<div class="collapsible-block post" id="post-9999">',
            1,
        )
        html = BeautifulSoup(body, "lxml")

        posts = ForumPostCollection._parse(mock_forum_thread_no_http, html)

        assert [post.id for post in posts] == [5001, 5002]

    def test_parse_ignores_content_post_containers(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """本文内のpost-container風マークアップを投稿として扱わない"""
        body = forum_posts_in_thread["body"].replace(
            "<p>Test post content</p>",
            (
                "<p>Test post content</p>"
                '<div class="post-container" id="fpc-9999"><div class="post" id="post-9999">'
                '<div class="long"><div class="head"><div class="title" id="post-title-9999">'
                'Content Post</div><div class="info"><span class="printuser">'
                '<a href="http://www.wikidot.com/user:info/content-post-user" '
                'onclick="WIKIDOT.page.listeners.userInfo(54323); return false;">content_post_user</a>'
                '</span> <span class="odate time_1700000600">17 Dec 2025</span></div></div>'
                '<div class="content" id="post-content-9999"><p>Content pseudo post body</p></div>'
                "</div></div></div>"
            ),
            1,
        )
        html = BeautifulSoup(body, "lxml")

        posts = ForumPostCollection._parse(mock_forum_thread_no_http, html)

        assert [post.id for post in posts] == [5001, 5002]

    def test_parse_ignores_content_changes_metadata(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """本文内のchanges風マークアップを編集情報として扱わない"""
        body = forum_posts_in_thread["body"].replace(
            "<p>Test post content</p>",
            (
                "<p>Test post content</p>"
                '<div class="changes"><span class="printuser">'
                '<a href="http://www.wikidot.com/user:info/content-user" '
                'onclick="WIKIDOT.page.listeners.userInfo(54321); return false;">content_user</a>'
                '</span> <span class="odate time_1700000400">17 Dec 2025</span></div>'
            ),
            1,
        )
        html = BeautifulSoup(body, "lxml")

        posts = ForumPostCollection._parse(mock_forum_thread_no_http, html)

        assert posts[0].edited_by is None
        assert posts[0].edited_at is None

    def test_parse_preserves_top_level_changes_metadata(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """トップレベルの編集情報は引き続きパースする"""
        body = forum_posts_in_thread["body"].replace(
            '<div class="content" id="post-content-5001"><p>Test post content</p></div>',
            (
                '<div class="content" id="post-content-5001"><p>Test post content</p></div>'
                '<div class="changes"><span class="printuser">'
                '<a href="http://www.wikidot.com/user:info/edit-user" '
                'onclick="WIKIDOT.page.listeners.userInfo(54322); return false;">edit_user</a>'
                '</span> <span class="odate time_1700000500">17 Dec 2025</span></div>'
            ),
            1,
        )
        html = BeautifulSoup(body, "lxml")

        posts = ForumPostCollection._parse(mock_forum_thread_no_http, html)

        assert posts[0].edited_by is not None
        assert posts[0].edited_by.name == "edit_user"
        assert posts[0].edited_by.id == 54322
        assert posts[0].edited_at is not None

    def test_parse_scopes_post_info_metadata_to_direct_children(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """投稿情報内のネストしたユーザー/日時風マークアップを投稿メタデータとして扱わない"""
        body = forum_posts_in_thread["body"].replace(
            '<div class="info"><span class="printuser">',
            (
                '<div class="info"><span class="preview">'
                '<span class="printuser"><a href="http://www.wikidot.com/user:info/fake-user" '
                'onclick="WIKIDOT.page.listeners.userInfo(99999); return false;">fake_user</a></span>'
                '<span class="odate time_1700000999">17 Dec 2025</span></span><span class="printuser">'
            ),
            1,
        )
        html = BeautifulSoup(body, "lxml")

        posts = ForumPostCollection._parse(mock_forum_thread_no_http, html)

        assert posts[0].created_by.name == "test_user"
        assert posts[0].created_by.id == 12345
        assert posts[0].created_at == datetime.fromtimestamp(1700000000)

    def test_parse_scopes_post_edit_metadata_to_direct_children(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """編集情報内のネストしたユーザー/日時風マークアップを編集メタデータとして扱わない"""
        body = forum_posts_in_thread["body"].replace(
            '<div class="content" id="post-content-5001"><p>Test post content</p></div>',
            (
                '<div class="content" id="post-content-5001"><p>Test post content</p></div>'
                '<div class="changes"><span class="preview">'
                '<span class="printuser"><a href="http://www.wikidot.com/user:info/fake-editor" '
                'onclick="WIKIDOT.page.listeners.userInfo(99998); return false;">fake_editor</a></span>'
                '<span class="odate time_1700000998">17 Dec 2025</span></span>'
                '<span class="printuser"><a href="http://www.wikidot.com/user:info/edit-user" '
                'onclick="WIKIDOT.page.listeners.userInfo(54322); return false;">edit_user</a></span> '
                '<span class="odate time_1700000500">17 Dec 2025</span></div>'
            ),
            1,
        )
        html = BeautifulSoup(body, "lxml")

        posts = ForumPostCollection._parse(mock_forum_thread_no_http, html)

        assert posts[0].edited_by is not None
        assert posts[0].edited_by.name == "edit_user"
        assert posts[0].edited_by.id == 54322
        assert posts[0].edited_at == datetime.fromtimestamp(1700000500)


class TestForumPostCollectionAcquireAll:
    """ForumPostCollection.acquire_all_in_threadのテスト"""

    def test_acquire_all_in_threads_rejects_non_list_threads_before_fetch(self) -> None:
        """threadsがlistでない場合は取得前に拒否する"""
        with pytest.raises(ValueError, match="threads must be a list"):
            ForumPostCollection.acquire_all_in_threads("3001")

    @pytest.mark.parametrize("bad_thread", [None, True, "3001"])
    def test_acquire_all_in_threads_rejects_non_thread_entries_before_fetch(
        self, mock_forum_thread_no_http: ForumThread, bad_thread: object
    ) -> None:
        """threadsの要素がForumThreadでない場合は取得前に拒否する"""
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock()

        with pytest.raises(ValueError, match="threads list entries must be ForumThread"):
            ForumPostCollection.acquire_all_in_threads([mock_forum_thread_no_http, bad_thread])  # type: ignore[list-item]

        mock_forum_thread_no_http.site.amc_request.assert_not_called()
        mock_forum_thread_no_http.site.amc_request_with_retry.assert_not_called()

    @pytest.mark.parametrize("thread", [None, True, "3001"])
    def test_acquire_all_in_thread_rejects_non_thread_before_fetch(self, thread: object) -> None:
        """単一threadがForumThreadでない場合は取得前に拒否する"""
        with pytest.raises(ValueError, match="thread must be a ForumThread"):
            ForumPostCollection.acquire_all_in_thread(thread)

    def test_acquire_all_single_page(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """単一ページの投稿一覧を取得できる"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_posts_in_thread
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)
        assert len(collection) == 2
        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_populates_thread_posts_cache(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """直接取得したスレッド内投稿一覧はthread.postsのキャッシュとして保持する"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_posts_in_thread
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        assert mock_forum_thread_no_http._posts is collection
        assert mock_forum_thread_no_http.posts is collection
        mock_forum_thread_no_http.site.amc_request_with_retry.assert_called_once()

    def test_acquire_all_preserves_title_text_spacing(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """投稿タイトル内の隣接した表示テキスト間の空白を維持する"""
        body = forum_posts_in_thread["body"].replace(
            '<div class="title" id="post-title-5001">Test Post Title</div>',
            '<div class="title" id="post-title-5001"><p>First <span>part</span></p><p>Second part</p></div>',
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {**forum_posts_in_thread, "body": body}
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection = ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        assert collection[0].title == "First part Second part"
        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_missing_post_title_includes_thread_page_and_post_context(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """投稿一覧の構造欠損はサイト・スレッド・ページ・投稿位置を含めて失敗する"""
        body = forum_posts_in_thread["body"].replace(
            '<div class="title" id="post-title-5001">Test Post Title</div>',
            "",
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {**forum_posts_in_thread, "body": body}
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Post title element is not found for site: test-site "
                r"\(thread=3001, page=1, post=1, post_id=5001\)"
            ),
        ):
            ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_malformed_post_id_includes_thread_page_and_value_context(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """投稿一覧の投稿IDが壊れている場合はサイト・スレッド・ページ・投稿位置・値を含めて失敗する"""
        body = forum_posts_in_thread["body"].replace(
            '<div class="post" id="post-5001">',
            '<div class="post" id="post-not-a-number">',
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {**forum_posts_in_thread, "body": body}
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Post ID is malformed for site: test-site "
                r"\(thread=3001, page=1, post=1, field=post_id, value=post-not-a-number\)"
            ),
        ):
            ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_malformed_parent_post_id_includes_child_post_context(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_nested: dict[str, Any]
    ) -> None:
        """返信の親投稿IDが壊れている場合は子投稿の文脈と値を含めて失敗する"""
        body = forum_posts_nested["body"].replace(
            '<div class="post" id="post-5001">',
            '<div class="post" id="bad-parent">',
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {**forum_posts_nested, "body": body}
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Post ID is malformed for site: test-site "
                r"\(thread=3001, page=1, post=1, post_id=5002, field=parent_post_id, value=bad-parent\)"
            ),
        ):
            ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_malformed_user_includes_thread_page_post_and_value_context(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """投稿一覧の作成者IDが壊れている場合はsite/thread/page/post/field/value文脈付きで失敗する"""
        body = forum_posts_in_thread["body"].replace(
            "WIKIDOT.page.listeners.userInfo(12345); return false;",
            "WIKIDOT.page.listeners.userInfo(latest); return false;",
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {**forum_posts_in_thread, "body": body}
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum post user is malformed for site: test-site "
                r"\(thread=3001, page=1, post=1, post_id=5001, field=created_by, "
                r"value=WIKIDOT\.page\.listeners\.userInfo\(latest\); return false;\)"
            ),
        ):
            ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_malformed_odate_includes_thread_page_post_and_value_context(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """投稿一覧の作成日時が壊れている場合はsite/thread/page/post/field/value文脈付きで失敗する"""
        body = forum_posts_in_thread["body"].replace(
            "odate time_1700000000",
            "odate time_latest",
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {**forum_posts_in_thread, "body": body}
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum post created_at is malformed for site: test-site "
                r"\(thread=3001, page=1, post=1, post_id=5001, field=created_at, value=time_latest\)"
            ),
        ):
            ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_malformed_edit_user_includes_thread_page_post_and_value_context(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """投稿一覧の編集者IDが壊れている場合はsite/thread/page/post/field/value文脈付きで失敗する"""
        body = forum_posts_in_thread["body"].replace(
            '<div class="content" id="post-content-5001"><p>Test post content</p></div>',
            (
                '<div class="content" id="post-content-5001"><p>Test post content</p></div>'
                '<div class="changes"><span class="printuser">'
                '<a href="http://www.wikidot.com/user:info/edit-user" '
                'onclick="WIKIDOT.page.listeners.userInfo(latest); return false;">edit_user</a>'
                '</span> <span class="odate time_1700000500">17 Dec 2025</span></div>'
            ),
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {**forum_posts_in_thread, "body": body}
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum post user is malformed for site: test-site "
                r"\(thread=3001, page=1, post=1, post_id=5001, field=edited_by, "
                r"value=WIKIDOT\.page\.listeners\.userInfo\(latest\); return false;\)"
            ),
        ):
            ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_malformed_edit_odate_includes_thread_page_post_and_value_context(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """投稿一覧の編集日時が壊れている場合はsite/thread/page/post/field/value文脈付きで失敗する"""
        body = forum_posts_in_thread["body"].replace(
            '<div class="content" id="post-content-5001"><p>Test post content</p></div>',
            (
                '<div class="content" id="post-content-5001"><p>Test post content</p></div>'
                '<div class="changes"><span class="printuser">'
                '<a href="http://www.wikidot.com/user:info/edit-user" '
                'onclick="WIKIDOT.page.listeners.userInfo(54322); return false;">edit_user</a>'
                '</span> <span class="odate time_latest">17 Dec 2025</span></div>'
            ),
            1,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {**forum_posts_in_thread, "body": body}
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum post edited_at is malformed for site: test-site "
                r"\(thread=3001, page=1, post=1, post_id=5001, field=edited_at, value=time_latest\)"
            ),
        ):
            ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_missing_first_page_response_body_includes_thread_and_page_context(
        self, mock_forum_thread_no_http: ForumThread
    ) -> None:
        """初回投稿一覧応答のbody欠落はsite/thread/page付きで失敗する"""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match="Forum post list response body is not found for site: test-site, thread: 3001, page: 1",
        ):
            ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_malformed_first_page_response_body_type_includes_thread_and_page_context(
        self, mock_forum_thread_no_http: ForumThread
    ) -> None:
        """初回投稿一覧応答のbody型異常はsite/thread/page/type付きで失敗する"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"body": ["not-html"]}
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum post list response body is malformed for site: test-site, thread: 3001, page: 1 "
                r"\(field=body, expected=str, actual=list\)"
            ),
        ):
            ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_ignores_content_pager_markup(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """本文内のpager風マークアップをページネーションとして扱わない"""
        body_with_content_pager = forum_posts_in_thread["body"].replace(
            "<p>Test post content</p>",
            (
                "<p>Test post content</p>"
                '<div class="pager"><span class="target">1</span>'
                '<span class="target">2</span></div>'
            ),
            1,
        )
        first_response = MagicMock()
        first_response.json.return_value = {"status": "ok", "body": body_with_content_pager}
        second_response = MagicMock()
        second_response.json.return_value = forum_posts_in_thread
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(
            side_effect=[(first_response,), (second_response,)]
        )

        collection = ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        assert len(collection) == 2
        mock_forum_thread_no_http.site.amc_request.assert_not_called()
        mock_forum_thread_no_http.site.amc_request_with_retry.assert_called_once()

    def test_acquire_all_retries_transient_first_page_failures(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """一時的なAMC失敗後にスレッド内投稿一覧をリトライする"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_posts_in_thread
        amc_request = MagicMock(side_effect=[(RuntimeError("temporary failure"),), (mock_response,)])
        mock_forum_thread_no_http.site.client.amc_client.request = amc_request

        collection = ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        assert len(collection) == 2
        assert amc_request.call_count == 2

    def test_acquire_all_pagination(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """複数ページの投稿一覧を取得できる（ページャーあり）"""
        # ページャー付きのレスポンスを作成
        body_with_pager = (
            forum_posts_in_thread["body"]
            + '<div class="pager"><span class="target">1</span><span class="target">2</span><span class="target">next</span></div>'
        )
        first_response = MagicMock()
        first_response.json.return_value = {"status": "ok", "body": body_with_pager}

        second_response = MagicMock()
        second_response.json.return_value = forum_posts_in_thread

        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(
            side_effect=[(first_response,), (second_response,)]
        )

        collection = ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)
        # 最初のページで2件 + 2ページ目で2件 = 4件
        assert len(collection) == 4
        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_in_threads_deduplicates_duplicate_thread_ids(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """重複したthread IDの投稿一覧取得は1回にまとめる"""
        duplicate_thread = ForumThread(
            site=mock_forum_thread_no_http.site,
            id=mock_forum_thread_no_http.id,
            title="Duplicate Thread",
            description=mock_forum_thread_no_http.description,
            created_by=mock_forum_thread_no_http.created_by,
            created_at=mock_forum_thread_no_http.created_at,
            post_count=mock_forum_thread_no_http.post_count,
            category=mock_forum_thread_no_http.category,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = forum_posts_in_thread
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        result = ForumPostCollection.acquire_all_in_threads([mock_forum_thread_no_http, duplicate_thread])

        assert set(result) == {mock_forum_thread_no_http.id}
        assert len(result[mock_forum_thread_no_http.id]) == 2
        assert result[mock_forum_thread_no_http.id].thread == mock_forum_thread_no_http
        mock_forum_thread_no_http.site.amc_request.assert_not_called()
        mock_forum_thread_no_http.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "moduleName": "forum/ForumViewThreadPostsModule",
                    "pageNo": "1",
                    "t": str(mock_forum_thread_no_http.id),
                }
            ]
        )

    def test_acquire_all_in_threads_skips_cached_thread_posts(
        self,
        mock_forum_thread_no_http: ForumThread,
        mock_forum_post_no_http: ForumPost,
        forum_posts_in_thread: dict[str, Any],
    ) -> None:
        """取得済みthread.postsは再取得せず未取得threadだけを取得する"""
        cached_collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])
        mock_forum_thread_no_http._posts = cached_collection
        uncached_thread = ForumThread(
            site=mock_forum_thread_no_http.site,
            id=3002,
            title="Uncached Thread",
            description=mock_forum_thread_no_http.description,
            created_by=mock_forum_thread_no_http.created_by,
            created_at=mock_forum_thread_no_http.created_at,
            post_count=mock_forum_thread_no_http.post_count,
            category=mock_forum_thread_no_http.category,
        )
        mock_response = MagicMock()
        mock_response.json.return_value = forum_posts_in_thread

        def request_with_retry(requests):
            return tuple(mock_response for _ in requests)

        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(side_effect=request_with_retry)

        result = ForumPostCollection.acquire_all_in_threads([mock_forum_thread_no_http, uncached_thread])

        assert result[mock_forum_thread_no_http.id] is cached_collection
        assert len(result[uncached_thread.id]) == 2
        assert result[uncached_thread.id].thread == uncached_thread
        mock_forum_thread_no_http.site.amc_request.assert_not_called()
        mock_forum_thread_no_http.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "moduleName": "forum/ForumViewThreadPostsModule",
                    "pageNo": "1",
                    "t": str(uncached_thread.id),
                }
            ]
        )

    def test_acquire_all_in_threads_all_cached_skips_fetch(
        self, mock_forum_thread_no_http: ForumThread, mock_forum_post_no_http: ForumPost
    ) -> None:
        """全threadが取得済みならAMCを呼ばずにcached collectionを返す"""
        cached_collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])
        mock_forum_thread_no_http._posts = cached_collection
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock()

        result = ForumPostCollection.acquire_all_in_threads([mock_forum_thread_no_http])

        assert result[mock_forum_thread_no_http.id] is cached_collection
        mock_forum_thread_no_http.site.amc_request.assert_not_called()
        mock_forum_thread_no_http.site.amc_request_with_retry.assert_not_called()

    def test_acquire_all_in_threads_reuses_later_cached_duplicate_thread_posts(
        self, mock_forum_thread_no_http: ForumThread
    ) -> None:
        """後続の重複threadにcached postsがあればfirst-seen thread用に再利用する"""
        cached_duplicate_thread = ForumThread(
            site=mock_forum_thread_no_http.site,
            id=mock_forum_thread_no_http.id,
            title="Cached Duplicate Thread",
            description=mock_forum_thread_no_http.description,
            created_by=mock_forum_thread_no_http.created_by,
            created_at=mock_forum_thread_no_http.created_at,
            post_count=mock_forum_thread_no_http.post_count,
            category=mock_forum_thread_no_http.category,
        )
        cached_post = ForumPost(
            thread=cached_duplicate_thread,
            id=5001,
            title="Cached Post",
            text="<div>Cached post body</div>",
            element=MagicMock(),
            created_by=mock_forum_thread_no_http.created_by,
            created_at=mock_forum_thread_no_http.created_at,
            _source="cached source",
        )
        cached_post._revisions = MagicMock()
        cached_duplicate_thread._posts = ForumPostCollection(cached_duplicate_thread, [cached_post])
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock()

        result = ForumPostCollection.acquire_all_in_threads([mock_forum_thread_no_http, cached_duplicate_thread])

        assert set(result) == {mock_forum_thread_no_http.id}
        result_collection = result[mock_forum_thread_no_http.id]
        assert result_collection.thread == mock_forum_thread_no_http
        assert result_collection is not cached_duplicate_thread._posts
        assert len(result_collection) == 1
        assert result_collection[0] is not cached_post
        assert result_collection[0].thread == mock_forum_thread_no_http
        assert result_collection[0].id == cached_post.id
        assert result_collection[0].title == cached_post.title
        assert result_collection[0]._source == "cached source"
        assert result_collection[0]._revisions is None
        mock_forum_thread_no_http.site.amc_request.assert_not_called()
        mock_forum_thread_no_http.site.amc_request_with_retry.assert_not_called()

    def test_acquire_all_ignores_non_numeric_pager_targets(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """数値ページがないpagerでは単一ページとして扱う"""
        body_with_pager = forum_posts_in_thread["body"] + '<div class="pager"><span class="target">next</span></div>'
        first_response = MagicMock()
        first_response.json.return_value = {"status": "ok", "body": body_with_pager}
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(first_response,))

        collection = ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        assert len(collection) == 2
        mock_forum_thread_no_http.site.amc_request.assert_not_called()
        mock_forum_thread_no_http.site.amc_request_with_retry.assert_called_once()

    def test_acquire_all_raises_when_first_page_retry_is_exhausted(
        self, mock_forum_thread_no_http: ForumThread
    ) -> None:
        """初回ページのリトライが尽きた場合は明示的に例外を出す"""
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(None,))

        with pytest.raises(
            exceptions.UnexpectedException,
            match="Cannot retrieve forum posts for site: test-site, thread: 3001, page: 1",
        ):
            ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_raises_when_paginated_retry_is_exhausted(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """追加ページのリトライが尽きた場合は部分一覧を返さない"""
        body_with_pager = (
            forum_posts_in_thread["body"]
            + '<div class="pager"><span class="target">1</span><span class="target">2</span></div>'
        )
        first_response = MagicMock()
        first_response.json.return_value = {"status": "ok", "body": body_with_pager}

        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(side_effect=[(first_response,), (None,)])

        with pytest.raises(
            exceptions.UnexpectedException,
            match="Cannot retrieve forum posts for site: test-site, thread: 3001, page: 2",
        ):
            ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_acquire_all_missing_paginated_response_body_includes_thread_and_page_context(
        self, mock_forum_thread_no_http: ForumThread, forum_posts_in_thread: dict[str, Any]
    ) -> None:
        """追加投稿一覧応答のbody欠落はsite/thread/page付きで失敗する"""
        body_with_pager = (
            forum_posts_in_thread["body"]
            + '<div class="pager"><span class="target">1</span><span class="target">2</span></div>'
        )
        first_response = MagicMock()
        first_response.json.return_value = {"status": "ok", "body": body_with_pager}
        second_response = MagicMock()
        second_response.json.return_value = {}

        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(
            side_effect=[(first_response,), (second_response,)]
        )

        with pytest.raises(
            exceptions.NoElementException,
            match="Forum post list response body is not found for site: test-site, thread: 3001, page: 2",
        ):
            ForumPostCollection.acquire_all_in_thread(mock_forum_thread_no_http)

        mock_forum_thread_no_http.site.amc_request.assert_not_called()


class TestForumPostCollectionGetSources:
    """ForumPostCollection.get_post_sourcesのテスト"""

    def test_get_post_sources_success(
        self,
        mock_forum_thread_no_http: ForumThread,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
    ) -> None:
        """ソースを正常に取得できる"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])

        mock_response = MagicMock()
        mock_response.json.return_value = forum_editpost_form
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        result = collection.get_post_sources()
        assert result == collection
        assert mock_forum_post_no_http._source is not None
        assert mock_forum_post_no_http._source == "Test source content in wikidot syntax"
        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_get_post_sources_scopes_source_textarea_to_edit_form_direct_child(
        self,
        mock_forum_thread_no_http: ForumThread,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
    ) -> None:
        """編集フォーム直下のソースtextareaを使用する"""
        form_with_preview = {
            **forum_editpost_form,
            "body": forum_editpost_form["body"].replace(
                '<form id="edit-post-form">',
                '<form id="edit-post-form"><div class="preview">'
                '<textarea name="source">Preview source</textarea></div>',
                1,
            ),
        }
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])

        mock_response = MagicMock()
        mock_response.json.return_value = form_with_preview
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        collection.get_post_sources()

        assert mock_forum_post_no_http._source == "Test source content in wikidot syntax"
        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_get_post_sources_missing_direct_source_textarea_includes_context(
        self,
        mock_forum_thread_no_http: ForumThread,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
    ) -> None:
        """編集フォーム直下のsource textarea欠落はsite/post付きで失敗する"""
        malformed_form = {
            **forum_editpost_form,
            "body": forum_editpost_form["body"].replace(
                '<textarea id="np-text" name="source">Test source content in wikidot syntax</textarea>',
                '<div><textarea id="np-text" name="source">Nested source</textarea></div>',
                1,
            ),
        }
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])

        mock_response = MagicMock()
        mock_response.json.return_value = malformed_form
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match="Source textarea is not found for site: test-site, post: 5001",
        ):
            collection.get_post_sources()

        assert mock_forum_post_no_http._source is None
        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_get_post_sources_missing_response_body_includes_site_and_post_context(
        self, mock_forum_thread_no_http: ForumThread, mock_forum_post_no_http: ForumPost
    ) -> None:
        """投稿ソース応答のbody欠落はsite/post付きで失敗する"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])

        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match="Forum post source response body is not found for site: test-site, post: 5001",
        ):
            collection.get_post_sources()

        assert mock_forum_post_no_http._source is None
        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_get_post_sources_malformed_response_body_type_includes_site_post_and_type_context(
        self, mock_forum_thread_no_http: ForumThread, mock_forum_post_no_http: ForumPost
    ) -> None:
        """投稿ソース応答のbody型異常はsite/post/type付きで失敗する"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])

        mock_response = MagicMock()
        mock_response.json.return_value = {"body": ["not-html"]}
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum post source response body is malformed for site: test-site, post: 5001 "
                r"\(field=body, expected=str, actual=list\)"
            ),
        ):
            collection.get_post_sources()

        assert mock_forum_post_no_http._source is None
        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_get_post_sources_retries_transient_fetch_failures(
        self,
        mock_forum_thread_no_http: ForumThread,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
    ) -> None:
        """一時的なAMC失敗後に投稿ソース取得をリトライする"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])

        mock_response = MagicMock()
        mock_response.json.return_value = forum_editpost_form
        amc_request = MagicMock(side_effect=[(RuntimeError("temporary failure"),), (mock_response,)])
        mock_forum_thread_no_http.site.client.amc_client.request = amc_request

        result = collection.get_post_sources()

        assert result == collection
        assert mock_forum_post_no_http._source == "Test source content in wikidot syntax"
        assert amc_request.call_count == 2

    def test_get_post_sources_skips_already_acquired(
        self, mock_forum_thread_no_http: ForumThread, mock_forum_post_no_http: ForumPost
    ) -> None:
        """既に取得済みのソースはスキップ"""
        mock_forum_post_no_http._source = "cached source"
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock()
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])

        result = collection.get_post_sources()
        mock_forum_thread_no_http.site.amc_request.assert_not_called()
        mock_forum_thread_no_http.site.amc_request_with_retry.assert_not_called()
        assert result == collection
        assert mock_forum_post_no_http._source == "cached source"

    def test_get_post_sources_empty_collection(self, mock_forum_thread_no_http: ForumThread) -> None:
        """空のコレクションでも動作する"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [])
        result = collection.get_post_sources()
        assert result == collection
        assert len(collection) == 0

    def test_get_post_sources_multiple_posts(
        self,
        mock_forum_thread_no_http: ForumThread,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
    ) -> None:
        """複数の投稿のソースを一括取得できる"""
        # 2つ目の投稿を作成
        post2 = ForumPost(
            thread=mock_forum_thread_no_http,
            id=5002,
            title="Second Post",
            text="<p>Second post content</p>",
            element=mock_forum_post_no_http.element,
            created_by=mock_forum_post_no_http.created_by,
            created_at=mock_forum_post_no_http.created_at,
        )

        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http, post2])

        mock_response1 = MagicMock()
        mock_response1.json.return_value = forum_editpost_form
        mock_response2 = MagicMock()
        mock_response2.json.return_value = forum_editpost_form
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response1, mock_response2))

        result = collection.get_post_sources()
        assert result == collection
        assert mock_forum_post_no_http._source is not None
        assert post2._source is not None
        mock_forum_thread_no_http.site.amc_request.assert_not_called()

    def test_get_post_sources_deduplicates_duplicate_post_ids(
        self,
        mock_forum_thread_no_http: ForumThread,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
    ) -> None:
        """重複した投稿IDのソース取得は1回にまとめる"""
        duplicate_post = ForumPost(
            thread=mock_forum_thread_no_http,
            id=mock_forum_post_no_http.id,
            title="Duplicate Post",
            text="<p>Duplicate post content</p>",
            element=mock_forum_post_no_http.element,
            created_by=mock_forum_post_no_http.created_by,
            created_at=mock_forum_post_no_http.created_at,
        )
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http, duplicate_post])

        mock_response = MagicMock()
        mock_response.json.return_value = forum_editpost_form
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        result = collection.get_post_sources()

        assert result == collection
        assert mock_forum_post_no_http._source == "Test source content in wikidot syntax"
        assert duplicate_post._source == "Test source content in wikidot syntax"
        mock_forum_thread_no_http.site.amc_request.assert_not_called()
        mock_forum_thread_no_http.site.amc_request_with_retry.assert_called_once_with(
            [
                {
                    "moduleName": "forum/sub/ForumEditPostFormModule",
                    "threadId": mock_forum_thread_no_http.id,
                    "postId": mock_forum_post_no_http.id,
                }
            ]
        )

    def test_get_post_sources_reuses_cached_duplicate_post_source(
        self,
        mock_forum_thread_no_http: ForumThread,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
    ) -> None:
        """取得済みの重複投稿ソースを未取得の同一ID投稿へ再利用する"""
        mock_forum_post_no_http._source = "cached source"
        duplicate_post = ForumPost(
            thread=mock_forum_thread_no_http,
            id=mock_forum_post_no_http.id,
            title="Duplicate Post",
            text="<p>Duplicate post content</p>",
            element=mock_forum_post_no_http.element,
            created_by=mock_forum_post_no_http.created_by,
            created_at=mock_forum_post_no_http.created_at,
        )
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http, duplicate_post])

        mock_response = MagicMock()
        mock_response.json.return_value = forum_editpost_form
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        result = collection.get_post_sources()

        assert result == collection
        assert duplicate_post._source == "cached source"
        mock_forum_thread_no_http.site.amc_request.assert_not_called()
        mock_forum_thread_no_http.site.amc_request_with_retry.assert_not_called()

    def test_get_post_sources_skips_failed_retry_response(
        self, mock_forum_thread_no_http: ForumThread, mock_forum_post_no_http: ForumPost
    ) -> None:
        """リトライが尽きた投稿は未取得のまま残す"""
        collection = ForumPostCollection(mock_forum_thread_no_http, [mock_forum_post_no_http])
        mock_forum_thread_no_http.site.amc_request = MagicMock()
        mock_forum_thread_no_http.site.amc_request_with_retry = MagicMock(return_value=(None,))

        result = collection.get_post_sources()

        assert result == collection
        assert mock_forum_post_no_http._source is None
        mock_forum_thread_no_http.site.amc_request.assert_not_called()


# ============================================================
# ForumPostテスト
# ============================================================


class TestForumPostBasic:
    """ForumPostの基本テスト"""

    def test_str(self, mock_forum_post_no_http: ForumPost) -> None:
        """__str__が正しい文字列を返す"""
        result = str(mock_forum_post_no_http)
        assert "ForumPost" in result
        assert "id=5001" in result
        assert "Test Post Title" in result

    def test_parent_id_property(self, mock_forum_post_no_http: ForumPost) -> None:
        """parent_idプロパティが正しい値を返す"""
        assert mock_forum_post_no_http.parent_id is None

        mock_forum_post_no_http._parent_id = 4999
        assert mock_forum_post_no_http.parent_id == 4999


class TestForumPostSource:
    """ForumPost.sourceプロパティのテスト"""

    def test_source_property_calls_api(
        self, mock_forum_post_no_http: ForumPost, forum_editpost_form: dict[str, Any]
    ) -> None:
        """sourceプロパティがAPIを呼び出す"""
        mock_response = MagicMock()
        mock_response.json.return_value = forum_editpost_form
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(mock_response,))

        source = mock_forum_post_no_http.source
        assert source == "Test source content in wikidot syntax"
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()

    def test_source_property_cached(self, mock_forum_post_no_http: ForumPost) -> None:
        """sourceプロパティがキャッシュされる"""
        mock_forum_post_no_http._source = "cached source"
        assert mock_forum_post_no_http.source == "cached source"

    def test_source_property_raises_when_retry_is_exhausted(self, mock_forum_post_no_http: ForumPost) -> None:
        """sourceプロパティはリトライ枯渇時にsite/post付きの未取得例外を返す"""
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(None,))

        with pytest.raises(
            exceptions.NoElementException,
            match="Source textarea is not found for site: test-site, post: 5001",
        ):
            _ = mock_forum_post_no_http.source

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()


class TestForumPostEdit:
    """ForumPost.editのテスト"""

    def test_edit_not_logged_in(self, mock_forum_post_no_http: ForumPost) -> None:
        """ログインしていない場合に例外"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = False
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock(
            side_effect=exceptions.LoginRequiredException("Login required")
        )

        with pytest.raises(exceptions.LoginRequiredException):
            mock_forum_post_no_http.edit(source="Updated source")

    def test_edit_success(
        self,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
        amc_ok_response: dict[str, Any],
    ) -> None:
        """編集が成功する"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()

        form_response = MagicMock()
        form_response.json.return_value = forum_editpost_form
        save_response = MagicMock()
        save_response.json.return_value = amc_ok_response

        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(form_response,))
        mock_forum_post_no_http.thread.site.amc_request = MagicMock(return_value=[save_response])

        result = mock_forum_post_no_http.edit(source="Updated source")

        assert result == mock_forum_post_no_http
        assert mock_forum_post_no_http._source == "Updated source"
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once()
        mock_forum_post_no_http.thread.site.amc_request.assert_called_once()

    def test_edit_success_invalidates_cached_revisions(
        self,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
        amc_ok_response: dict[str, Any],
    ) -> None:
        """編集成功後は古いrevision一覧キャッシュを使い回さない"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()
        mock_forum_post_no_http._revisions = ForumPostRevisionCollection(mock_forum_post_no_http, [])

        form_response = MagicMock()
        form_response.json.return_value = forum_editpost_form
        save_response = MagicMock()
        save_response.json.return_value = amc_ok_response

        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(form_response,))
        mock_forum_post_no_http.thread.site.amc_request = MagicMock(return_value=[save_response])

        result = mock_forum_post_no_http.edit(source="Updated source")

        assert result == mock_forum_post_no_http
        assert mock_forum_post_no_http._source == "Updated source"
        assert mock_forum_post_no_http._revisions is None

    def test_edit_success_invalidates_thread_posts_cache(
        self,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
        amc_ok_response: dict[str, Any],
    ) -> None:
        """編集成功後はスレッド側の投稿一覧キャッシュも再取得させる"""
        cached_post = ForumPost(
            thread=mock_forum_post_no_http.thread,
            id=mock_forum_post_no_http.id,
            title="Cached title",
            text="Cached text",
            element=mock_forum_post_no_http.element,
            created_by=mock_forum_post_no_http.created_by,
            created_at=mock_forum_post_no_http.created_at,
            edited_by=mock_forum_post_no_http.edited_by,
            edited_at=mock_forum_post_no_http.edited_at,
            _parent_id=mock_forum_post_no_http._parent_id,
            _source="cached source",
        )
        mock_forum_post_no_http.thread._posts = ForumPostCollection(mock_forum_post_no_http.thread, [cached_post])
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()

        form_response = MagicMock()
        form_response.json.return_value = forum_editpost_form
        save_response = MagicMock()
        save_response.json.return_value = amc_ok_response

        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(form_response,))
        mock_forum_post_no_http.thread.site.amc_request = MagicMock(return_value=[save_response])

        result = mock_forum_post_no_http.edit(source="Updated source", title="Updated title")

        assert result == mock_forum_post_no_http
        assert mock_forum_post_no_http.thread._posts is None

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"source": 3}, "source must be a string"),
            ({"title": 3}, "title must be a string"),
        ],
    )
    def test_edit_rejects_non_string_text_inputs_before_login_or_form_fetch(
        self,
        mock_forum_post_no_http: ForumPost,
        kwargs: dict[str, object],
        message: str,
    ) -> None:
        """投稿編集の文字列入力不正はログイン確認や編集フォーム取得前に拒否する"""
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()

        inputs: dict[str, Any] = {"source": "Updated source", **kwargs}
        with pytest.raises(ValueError, match=message):
            mock_forum_post_no_http.edit(**inputs)

        mock_forum_post_no_http.thread.site.client.login_check.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_not_called()
        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()

    def test_edit_scopes_current_revision_id_to_edit_form_direct_child(
        self,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
        amc_ok_response: dict[str, Any],
    ) -> None:
        """編集フォーム直下のcurrentRevisionIdを使用する"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()
        form_with_preview = {
            **forum_editpost_form,
            "body": forum_editpost_form["body"].replace(
                '<form id="edit-post-form">',
                '<form id="edit-post-form"><div class="preview">'
                '<input type="hidden" name="currentRevisionId" value="9999"/></div>',
                1,
            ),
        }

        form_response = MagicMock()
        form_response.json.return_value = form_with_preview
        save_response = MagicMock()
        save_response.json.return_value = amc_ok_response

        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(form_response,))
        mock_forum_post_no_http.thread.site.amc_request = MagicMock(return_value=[save_response])

        mock_forum_post_no_http.edit(source="Updated source")

        save_request = mock_forum_post_no_http.thread.site.amc_request.call_args.args[0][0]
        assert save_request["currentRevisionId"] == 9001

    def test_edit_missing_current_revision_id_includes_site_and_post_context(
        self,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
    ) -> None:
        """currentRevisionId欠落時はsite/postつきの例外を返す"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()
        form_without_revision_id = {
            **forum_editpost_form,
            "body": forum_editpost_form["body"].replace(
                '<input type="hidden" name="currentRevisionId" value="9001"/>',
                "",
                1,
            ),
        }

        form_response = MagicMock()
        form_response.json.return_value = form_without_revision_id
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(form_response,))
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()

        with pytest.raises(
            exceptions.NoElementException,
            match="Current revision ID input is not found for site: test-site, post: 5001",
        ):
            mock_forum_post_no_http.edit(source="Updated source")

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        assert mock_forum_post_no_http._source is None

    def test_edit_missing_current_revision_id_value_includes_site_and_post_context(
        self,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
    ) -> None:
        """currentRevisionId value欠落時はsite/postつきで保存せず失敗する"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()
        form_without_revision_value = {
            **forum_editpost_form,
            "body": forum_editpost_form["body"].replace(
                '<input type="hidden" name="currentRevisionId" value="9001"/>',
                '<input type="hidden" name="currentRevisionId"/>',
                1,
            ),
        }

        form_response = MagicMock()
        form_response.json.return_value = form_without_revision_value
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(form_response,))
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()

        with pytest.raises(
            exceptions.NoElementException,
            match="Current revision ID value is not found for site: test-site, post: 5001",
        ):
            mock_forum_post_no_http.edit(source="Updated source")

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        assert mock_forum_post_no_http._source is None

    def test_edit_malformed_current_revision_id_value_includes_site_and_post_context(
        self,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
    ) -> None:
        """currentRevisionId valueが数値でない場合はsite/postつきで保存せず失敗する"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()
        form_with_malformed_revision_value = {
            **forum_editpost_form,
            "body": forum_editpost_form["body"].replace(
                '<input type="hidden" name="currentRevisionId" value="9001"/>',
                '<input type="hidden" name="currentRevisionId" value="not-a-number"/>',
                1,
            ),
        }

        form_response = MagicMock()
        form_response.json.return_value = form_with_malformed_revision_value
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(form_response,))
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()

        with pytest.raises(
            exceptions.NoElementException,
            match="Current revision ID value is malformed for site: test-site, post: 5001",
        ):
            mock_forum_post_no_http.edit(source="Updated source")

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        assert mock_forum_post_no_http._source is None

    def test_edit_retries_transient_form_fetch_failures(
        self,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
        amc_ok_response: dict[str, Any],
    ) -> None:
        """一時的なAMC失敗後に編集フォーム取得をリトライする"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()

        form_response = MagicMock()
        form_response.json.return_value = forum_editpost_form
        save_response = MagicMock()
        save_response.json.return_value = amc_ok_response
        amc_request = MagicMock(side_effect=[(RuntimeError("temporary failure"),), (form_response,), (save_response,)])
        mock_forum_post_no_http.thread.site.client.amc_client.request = amc_request

        result = mock_forum_post_no_http.edit(source="Updated source")

        assert result == mock_forum_post_no_http
        assert mock_forum_post_no_http._source == "Updated source"
        assert amc_request.call_count == 3

    def test_edit_raises_when_form_fetch_retry_is_exhausted(self, mock_forum_post_no_http: ForumPost) -> None:
        """編集フォーム取得のリトライが尽きた場合はsite/post付きで保存せず失敗する"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(None,))
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()

        with pytest.raises(
            exceptions.UnexpectedException,
            match="Cannot retrieve forum post edit form for site: test-site, post: 5001",
        ):
            mock_forum_post_no_http.edit(source="Updated source")

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        assert mock_forum_post_no_http._source is None

    def test_edit_missing_form_response_body_includes_site_and_post_context(
        self, mock_forum_post_no_http: ForumPost
    ) -> None:
        """編集フォーム応答のbody欠落時はsite/post付きで保存せず失敗する"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()

        form_response = MagicMock()
        form_response.json.return_value = {}
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(form_response,))
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()

        with pytest.raises(
            exceptions.NoElementException,
            match="Forum post edit form response body is not found for site: test-site, post: 5001",
        ):
            mock_forum_post_no_http.edit(source="Updated source")

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        assert mock_forum_post_no_http._source is None

    def test_edit_malformed_form_response_body_type_includes_site_post_and_type_context(
        self, mock_forum_post_no_http: ForumPost
    ) -> None:
        """編集フォーム応答のbody型異常時はsite/post/type付きで保存せず失敗する"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()

        form_response = MagicMock()
        form_response.json.return_value = {"body": ["not-html"]}
        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(form_response,))
        mock_forum_post_no_http.thread.site.amc_request = MagicMock()

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum post edit form response body is malformed for site: test-site, post: 5001 "
                r"\(field=body, expected=str, actual=list\)"
            ),
        ):
            mock_forum_post_no_http.edit(source="Updated source")

        mock_forum_post_no_http.thread.site.amc_request.assert_not_called()
        assert mock_forum_post_no_http._source is None

    def test_edit_missing_save_action_status_does_not_update_local_state(
        self,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
    ) -> None:
        """編集保存応答のstatus欠落は文脈付きで失敗しローカル状態を更新しない"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()
        mock_forum_post_no_http.title = "Original Title"
        mock_forum_post_no_http._source = "Original source"
        cached_posts = ForumPostCollection(mock_forum_post_no_http.thread, [mock_forum_post_no_http])
        mock_forum_post_no_http.thread._posts = cached_posts

        form_response = MagicMock()
        form_response.json.return_value = forum_editpost_form
        malformed_save_response = MagicMock()
        malformed_save_response.json.return_value = {"body": ""}

        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(form_response,))
        mock_forum_post_no_http.thread.site.amc_request = MagicMock(return_value=[malformed_save_response])

        with pytest.raises(
            exceptions.NoElementException,
            match=(
                r"Forum post action response is malformed for site: test-site, post: 5001 "
                r"\(event=saveEditPost, field=status\)"
            ),
        ):
            mock_forum_post_no_http.edit(source="Updated source", title="New Title")

        assert mock_forum_post_no_http.title == "Original Title"
        assert mock_forum_post_no_http._source == "Original source"
        assert mock_forum_post_no_http.thread._posts is cached_posts

    def test_edit_with_new_title(
        self,
        mock_forum_post_no_http: ForumPost,
        forum_editpost_form: dict[str, Any],
        amc_ok_response: dict[str, Any],
    ) -> None:
        """タイトル付きで編集できる"""
        mock_forum_post_no_http.thread.site.client.is_logged_in = True
        mock_forum_post_no_http.thread.site.client.login_check = MagicMock()

        form_response = MagicMock()
        form_response.json.return_value = forum_editpost_form
        save_response = MagicMock()
        save_response.json.return_value = amc_ok_response

        mock_forum_post_no_http.thread.site.amc_request_with_retry = MagicMock(return_value=(form_response,))
        mock_forum_post_no_http.thread.site.amc_request = MagicMock(return_value=[save_response])

        mock_forum_post_no_http.edit(source="Updated source", title="New Title")

        assert mock_forum_post_no_http.title == "New Title"
        assert mock_forum_post_no_http._source == "Updated source"
        mock_forum_post_no_http.thread.site.amc_request_with_retry.assert_called_once()
        mock_forum_post_no_http.thread.site.amc_request.assert_called_once()
