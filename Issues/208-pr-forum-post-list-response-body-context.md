# PR Draft: Validate Forum Post List Response Bodies

## Summary

`ForumPostCollection.acquire_all_in_thread(...)` and `ForumPostCollection.acquire_all_in_threads(...)`, exposed through `ForumThread.posts`, retrieve first and paginated forum post-list pages through `forum/ForumViewThreadPostsModule`. Earlier local slices made that path retry-aware, added site/thread/page exhausted-retry context, deduplicated duplicate thread IDs, reused cached thread post lists, filtered content pager markup, scoped post-list parser metadata, and added site/thread/page/post context to malformed post rows. The remaining malformed response-body path still read `response.json()["body"]` for first and paginated post-list pages, so an AMC response without a `body` field leaked a raw `KeyError`.

This follow-up keeps cached post-list reuse, duplicate thread-ID handling, request payloads, retry counts, pagination, content-pager filtering, post-row parser context, source fetching, edit behavior, replies, and `ForumThread.posts` behavior unchanged. It only treats a missing post-list response `body` as a malformed list response and raises `NoElementException` with site/thread/page context before pager parsing, row parsing, or partial result extension.

## Related Issue

Builds on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [099-pr-ignore-forum-post-content-pager-markup.md](099-pr-ignore-forum-post-content-pager-markup.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [143-pr-reuse-cached-duplicate-thread-posts.md](143-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), and [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md). Those drafts established forum post-list acquisition as a retry-aware, parser-scoped, cache-sensitive, page-aware, and diagnosable local workflow.

No upstream issue was filed from this local workspace.

## Changes

- Add a small forum post-list response-body helper that reads `response.json().get("body")`.
- Convert missing first-page post-list response `body` into site/thread/page-specific `NoElementException`.
- Convert missing paginated post-list response `body` into site/thread/page-specific `NoElementException`.
- Add focused regressions for first-page and paginated forum post-list response body handling.
- Preserve existing successful post-list parsing, pager behavior, cached/duplicate thread behavior, source fetching, edit behavior, and replies.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post-list response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A first-page forum post-list response without JSON `body` still fails before pager or row parsing. | `TestForumPostCollectionAcquireAll.test_acquire_all_missing_first_page_response_body_includes_thread_and_page_context` returns `{}` from the first AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, fabricates an empty post collection, or parses rows rejects this local completion claim. |
| A paginated forum post-list response without JSON `body` still fails before returning or extending a partial post list. | `TestForumPostCollectionAcquireAll.test_acquire_all_missing_paginated_response_body_includes_thread_and_page_context` returns page 1 with a real pager and page 2 as `{}` and expects `NoElementException`. | A change that raises raw `KeyError`, silently skips page 2, or returns only page 1 posts rejects this local completion claim. |
| Malformed list response errors identify the affected site, thread, and page. | The focused regressions assert `Forum post list response body is not found for site: test-site, thread: 3001, page: 1` and page `2`. | A generic parser exception without site/thread/page context rejects this local completion claim. |
| Existing forum post-list behavior remains green. | `uv run pytest tests/unit/test_forum_post.py -q` passed 53 tests. | Regressions in retry behavior, pagination, parser context, content-pager filtering, cached/duplicate thread behavior, source fetching, edit behavior, or replies reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py tests/unit/test_forum_category.py -q` passed 153 tests. | Regressions in category/thread/post/revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `7933768 fix(forum_post): validate list response bodies`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_missing_first_page_response_body_includes_thread_and_page_context -q` failed before the first fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_missing_first_page_response_body_includes_thread_and_page_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_single_page -q`.
- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_missing_paginated_response_body_includes_thread_and_page_context -q` failed before the second fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_missing_first_page_response_body_includes_thread_and_page_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_missing_paginated_response_body_includes_thread_and_page_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_pagination tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_raises_when_paginated_retry_is_exhausted -q`.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 53 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py tests/unit/test_forum_category.py -q` passed 153 tests.
- `uv run pytest tests/unit -q` passed 743 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- First-page forum post-list requests still use `forum/ForumViewThreadPostsModule`, page `1`, and the same thread ID body.
- Paginated forum post-list requests still use `forum/ForumViewThreadPostsModule`, the discovered page number, and the same thread ID body.
- Missing first-page list response JSON `body` raises `NoElementException` naming the site, thread, and page 1.
- Missing paginated list response JSON `body` raises `NoElementException` naming the site, thread, and affected page.
- Missing response-body handling does not fabricate empty collections, skip failed pages, or return partial post-list output.
- Successful post-list parsing, pager handling, non-numeric pager behavior, content-pager filtering, parser row context, cached post-list reuse, duplicate thread-ID deduplication, source fetching, edit behavior, replies, and `ForumThread.posts` behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post-list acquisition depends on Wikidot returning a JSON `body` field before HTML parsing can start. If that field is missing on the first page or a later page, wikidot.py should report a structured malformed-response failure with the site, thread, and page number, so caller logs can route failures without preserving raw response JSON, raw forum post-list HTML, post bodies, credentials, local rollout paths, or account details.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum post-list acquisition as retry-aware, page-aware, duplicate/cached-thread-aware, protected from authored content pager markup, and backed by site/thread/page/post parser context.
- The immediately prior private-message list response slice showed the same raw `KeyError` failure mode at an adjacent list response boundary.
- Recent context slices showed that compact site/thread/page identifiers improve resumable ledgers without changing successful behavior or storing raw post HTML.
- The refreshed complexity memo continues to list parser/source collection helpers as follow-up leads, but this slice only claims forum post-list response-body validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, raw forum post-list HTML, post bodies, and private deployment details out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, cached post-list reuse, duplicate thread-ID handling, pagination calculation, parser-context failures, returned `ForumPostCollection`, source fetching, edit behavior, replies, or live Wikidot behavior. It only converts missing forum post-list response `body` fields into site/thread/page-context `NoElementException` failures before parser work.
