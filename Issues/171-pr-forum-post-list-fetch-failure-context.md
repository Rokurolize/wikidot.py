# PR Draft: Include Site Context In Forum Post List Fetch Failures

## Summary

`ForumPostCollection.acquire_all_in_thread(...)` and `ForumPostCollection.acquire_all_in_threads(...)`, exposed through `ForumThread.posts`, retrieve thread post-list pages through retry-aware AMC requests. When the first page or a later paginated page exhausted retries, the method raised `UnexpectedException("Cannot retrieve forum posts for thread ... page: ...")`, which identified the thread and page but not the Wikidot site.

This follow-up preserves retry-aware first-page and paginated post-list fetching, cached thread post reuse, duplicate thread-ID handling, post parsing, parser-context errors, pagination, source fetching, edit/reply behavior, and the `ForumThread.posts` property surface, but includes site unix name in exhausted post-list fetch failures.

## Related Issue

Builds on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), which introduced retry-aware thread post-list fetching and explicit exhausted-retry failures. It also follows [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), and [170-pr-forum-thread-detail-fetch-failure-context.md](170-pr-forum-thread-detail-fetch-failure-context.md), because those drafts established post-list acquisition, duplicate/cached behavior, parser context, and adjacent thread detail fetch context as practical rollout-backed surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Include site unix name, thread ID, and page number when first-page thread post-list fetching exhausts retries.
- Include the same site/thread/page context when a paginated thread post-list page exhausts retries.
- Strengthen the existing first-page and paginated exhausted-retry tests, plus the `ForumThread.posts` property regression, to assert the contextual messages.
- Preserve non-retry `amc_request(...)` avoidance, cached thread post reuse, duplicate thread-ID handling, pagination, parser-context failures, source fetching, edit behavior, and replies.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post-list fetch failure context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| First-page exhausted retry post-list fetches still fail. | `TestForumPostCollectionAcquireAll.test_acquire_all_raises_when_first_page_retry_is_exhausted` raises `UnexpectedException` when page 1 retry returns `None`. | A change that returns an empty post collection for a failed first page rejects this local completion claim. |
| Paginated exhausted retry post-list fetches still fail. | `TestForumPostCollectionAcquireAll.test_acquire_all_raises_when_paginated_retry_is_exhausted` raises `UnexpectedException` when page 2 retry returns `None`. | A change that silently drops a failed page and returns a partial post list rejects this local completion claim. |
| The `ForumThread.posts` property keeps surfacing the same failure. | `TestForumThreadPosts.test_posts_property_raises_when_retry_is_exhausted` asserts the contextual message and non-caching behavior through the property path. | A change that caches an empty collection after failed retry rejects this local completion claim. |
| Exhausted-retry failures identify the failed site, thread, and page. | Focused tests assert `Cannot retrieve forum posts for site: test-site, thread: 3001, page: ...`. | The RED tests failed before the fix because messages only named thread/page. |
| Forum post-list behavior remains green. | `uv run pytest tests/unit/test_forum_post.py -q` passed 48 tests. | Regressions in post parsing, pagination, parser-context failures, source fetching, edit behavior, or replies reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 148 tests. | Regressions in category/thread/post/revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `bf83cd9 fix(forum_post): include site in post list fetch failures`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_raises_when_first_page_retry_is_exhausted tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_raises_when_paginated_retry_is_exhausted -q` failed before the fix because the exhausted-retry messages lacked site context.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_raises_when_first_page_retry_is_exhausted tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_raises_when_paginated_retry_is_exhausted -q`
- `uv run pytest tests/unit/test_forum_post.py -q` passed 48 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` initially exposed one adjacent `ForumThread.posts` expectation that still matched the old message, then passed 148 tests after updating that public-path expectation.
- `uv run pytest tests/unit -q` passed 722 tests.
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- First-page and paginated exhausted retry-aware thread post-list fetches still raise `UnexpectedException`.
- Those exceptions include the site unix name, thread ID, and page number.
- Successful post-list parsing, cached thread post reuse, duplicate thread-ID handling, pagination, parser-context failures, source fetching, edit behavior, replies, and `ForumThread.posts` behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post-list acquisition can run across sites and many threads. The exhausted-retry failure should identify site, thread, and page so logs can route failures without storing raw AMC responses, post content, or local rollout context.

## Local Evidence, Not For Upstream Paste

- Earlier rollout-backed forum drafts established thread post-list acquisition, duplicate/cached behavior, parser scoping, source fetching, and edit/reply boundaries as practical local Codex surfaces.
- Recent context slices showed that site-specific exhausted-retry messages improve multi-site ledgers without changing successful behavior.
- The refreshed complexity memo continues to keep action/read boundaries and remaining direct property/parser failure messages as follow-up leads, but this slice only claims thread post-list exhausted-retry diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw AMC responses, raw post content, and raw response bodies out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, retry counts, cached post reuse, duplicate ID handling, pagination calculation, parser-context failures, returned `ForumPostCollection`, source fetching, edit behavior, replies, or live Wikidot behavior. It only adds site context to existing exhausted retry-aware thread post-list failures.
