# PR Draft: Include Context In Forum Thread List Fetch Failures

## Summary

`ForumThreadCollection.acquire_all_in_category(...)` retrieves a category's thread-list pages through retry-aware AMC requests. When the first page or a later paginated page exhausted retries, the method raised `UnexpectedException("Cannot retrieve forum threads page: ...")`, which did not identify the affected site or forum category.

This follow-up preserves cached category thread reuse, retry-aware first-page and paginated fetching, pagination discovery, parser-context errors, nested thread-table filtering, description-pager filtering, title/description spacing, direct thread lookup, post access, and replies, but includes site unix name, category ID, and page number in exhausted thread-list fetch failures.

## Related Issue

Builds on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), which introduced retry-aware category thread-list fetching and explicit exhausted-retry failures. It also follows [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [167-pr-forum-thread-create-result-context.md](167-pr-forum-thread-create-result-context.md), and [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), because those drafts make forum category/thread diagnostics identify the affected site/category path without changing successful behavior.

No upstream issue was filed from this local workspace.

## Changes

- Include site unix name, category ID, and page number when the first category thread-list page exhausts retries.
- Include the same site/category/page context when a later paginated category thread-list page exhausts retries.
- Strengthen the existing paginated exhausted-retry unit test to assert the contextual message.
- Preserve non-retry `amc_request(...)` avoidance, cached category-thread reuse, pagination, parser behavior, and successful category thread-list output.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum thread-list fetch failure context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Paginated exhausted-retry thread-list fetches still fail. | `TestForumThreadCollectionAcquireAll.test_acquire_all_raises_when_paginated_retry_is_exhausted` raises `UnexpectedException` when page 2 retry returns `None`. | A change that silently drops a failed page and returns a partial thread list rejects this local completion claim. |
| Exhausted-retry failures identify the failed path. | The focused test asserts `Cannot retrieve forum threads for site: test-site, category: 1001, page: 2`. | The RED test failed before the fix because the message only said `Cannot retrieve forum threads page: 2`. |
| The retry-aware path is preserved. | The focused test asserts non-retry `amc_request(...)` is not called. | A change that falls back to the non-retry path rejects this local completion claim. |
| Forum thread-list behavior remains green. | `uv run pytest tests/unit/test_forum_thread.py -q` passed 42 tests. | Regressions in cached category reuse, reloads, pagination, nested-table filtering, parser-context errors, title/description spacing, direct thread lookup, post access, or replies reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 148 tests. | Regressions in category/thread/post/revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `765a00a fix(forum_thread): include context in thread list fetch failures`.

- Initial command correction: the first focused command used the wrong test class nodeid and collected no tests; the correct nodeid below was then used.
- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_raises_when_paginated_retry_is_exhausted -q` failed before the fix because the exhausted-retry message lacked site/category/page context.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_raises_when_paginated_retry_is_exhausted -q`
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 42 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 148 tests.
- `uv run pytest tests/unit -q` passed 722 tests.
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- First-page and paginated exhausted retry-aware category thread-list fetches still raise `UnexpectedException`.
- Those exceptions include the site unix name, category ID, and page number.
- Successful category thread-list parsing, cached reuse, reloads, pagination, parser-context failures, nested-table filtering, title/description spacing, direct thread lookup, post access, and replies remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Category thread-list acquisition is a read-heavy workflow and pagination can fail after page 1. The failure should identify the site, category, and page so logs can distinguish a targeted exhausted retry from a generic thread-list failure without storing raw response bodies or local rollout details.

## Local Evidence, Not For Upstream Paste

- Earlier rollout-backed forum drafts established category thread-list fetching and parsing as practical local Codex surfaces.
- The retry-aware thread-list draft intentionally exposed exhausted retries; this slice narrows that failure message for multi-site and multi-category ledgers.
- The refreshed complexity memo continues to keep action/read boundaries and remaining direct property/parser failure messages as follow-up leads, but this slice only claims category thread-list exhausted-retry diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw AMC responses, and raw response bodies out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, retry counts, cache semantics, response parsing, pagination calculation, parser-context failures, returned `ForumThreadCollection`, or live Wikidot behavior. It only adds site/category/page context to existing exhausted retry-aware category thread-list failures.
