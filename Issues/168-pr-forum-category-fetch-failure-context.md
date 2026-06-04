# PR Draft: Include Site Context In Forum Category Fetch Failures

## Summary

`ForumCategoryCollection.acquire_all(site)` already uses retry-aware AMC fetching for `forum/ForumStartModule`. When all retries are exhausted, the method raises `UnexpectedException`, but the message only said `Cannot retrieve forum categories`, which does not identify which Wikidot site failed.

This follow-up preserves the retry-aware request, empty category-list behavior, category parsing, nested-table filtering, contextual parser errors, and thread creation behavior, but includes the site unix name in the exhausted-retry failure.

## Related Issue

Builds on [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), which introduced retry-aware category-list fetching and the exhausted-retry failure path. It also follows [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), and [167-pr-forum-thread-create-result-context.md](167-pr-forum-thread-create-result-context.md), because those drafts made forum category/thread diagnostics identify the affected object without changing successful behavior.

No upstream issue was filed from this local workspace.

## Changes

- Include the site unix name when `ForumCategoryCollection.acquire_all(site)` exhausts retry-aware category-list fetching.
- Strengthen the existing exhausted-retry unit test to assert `Cannot retrieve forum categories for site: test-site`.
- Preserve `site.amc_request_with_retry(...)`, avoidance of the non-retry `amc_request(...)` path, empty category-list parsing, category row parsing, and thread creation behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum category list fetch failure context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Exhausted retry category-list fetches still fail. | `TestForumCategoryCollectionAcquireAll.test_acquire_all_raises_when_retry_is_exhausted` raises `UnexpectedException` when retry returns `None`. | A change that silently returns an empty collection for a failed fetch rejects this local completion claim. |
| The exhausted-retry failure identifies the failed site. | The focused test asserts `Cannot retrieve forum categories for site: test-site`. | The RED test failed before the fix because the message only said `Cannot retrieve forum categories`. |
| The retry-aware path is preserved. | The same focused test asserts non-retry `amc_request(...)` is not called. | A change that falls back to the non-retry path rejects this local completion claim. |
| Forum category behavior remains green. | `uv run pytest tests/unit/test_forum_category.py -q` passed 19 tests. | Regressions in empty lists, category parsing, parser-context errors, string output, thread property access, or thread creation reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 148 tests. | Regressions in category/thread/post/revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `8369597 fix(forum_category): include site in fetch failures`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_raises_when_retry_is_exhausted -q` failed before the fix because the exhausted-retry message lacked site context.
- GREEN: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_raises_when_retry_is_exhausted -q`
- `uv run pytest tests/unit/test_forum_category.py -q` passed 19 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 148 tests.
- `uv run pytest tests/unit -q` passed 722 tests.
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Exhausted retry-aware forum category list fetching still raises `UnexpectedException`.
- The exception includes the site unix name.
- Successful category-list parsing, empty-list parsing, parser-context failures, retry usage, and thread creation behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum category lists are site-scoped. When a retry-aware fetch fails, logs should show which site failed without requiring raw AMC response bodies or local rollout context. Site unix name is enough to route the failure while keeping the exception compact.

## Local Evidence, Not For Upstream Paste

- Earlier rollout-backed forum drafts established category-list fetching and parsing as practical local Codex surfaces.
- The previous retry-aware category draft intentionally exposed exhausted retries; this slice narrows that failure message so it is useful in multi-site ledgers.
- The refreshed complexity memo continues to keep action/read boundaries and remaining direct property/parser failure messages as follow-up leads, but this slice only claims category-list exhausted-retry diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw AMC responses, and raw response bodies out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, retry counts, response parsing, empty-forum handling, category row parser context, returned `ForumCategoryCollection`, or live Wikidot behavior. It only adds site context to the existing exhausted-retry category-list failure.
