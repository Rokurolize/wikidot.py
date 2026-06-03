# PR Draft: Skip Cached Category Thread-List Fetches

## Summary

`ForumCategory.threads` already caches a category's `ForumThreadCollection`, but the lower-level helper `ForumThreadCollection.acquire_all_in_category(category)` ignored that cache. A caller that had already loaded `category.threads` and then delegated through the helper still sent a `forum/ForumViewCategoryModule` request for page 1, then replaced the cached result with a newly parsed collection.

This fix returns the existing `category._threads` collection from direct helper acquisition when it is already populated. `ForumCategory.reload_threads()` now clears `_threads` before delegating, so explicit reload still bypasses the cache and fetches fresh category-thread pages. Parser scoping, pagination, retry exhaustion, direct `category.threads` lazy cache behavior, and thread/category ownership remain unchanged.

## Related Issue

Builds on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), which made category thread-list reads retry-aware and failure-visible. It preserves parser and pager hardening from [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), and [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md). It follows the cache-aware helper pattern from [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md) and [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md).

No upstream issue was filed from this local workspace.

## Changes

- Return `category._threads` from `ForumThreadCollection.acquire_all_in_category(...)` when a category already has an acquired thread collection.
- Keep `ForumCategory.reload_threads()` as an explicit cache-bypass path by clearing `_threads` before invoking the helper.
- Add focused regressions for direct cached helper reuse and reload cache bypass.
- Preserve retry-aware first-page and paginated category thread-list fetching for uncached categories.
- Preserve nested thread-table filtering, description-pager filtering, direct-cell metadata parsing, title/description spacing, category ownership, and the `ForumCategory.threads` lazy property.

## Type Of Change

- Performance improvement
- Cache-aware helper behavior
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Already acquired category thread collections must satisfy `acquire_all_in_category(...)` without being fetched again. | `TestForumThreadCollectionAcquireAll.test_acquire_all_skips_cached_category_threads` asserts the cached collection object is returned and neither AMC request helper is called. | The RED test failed before the fix because the helper called `ForumViewCategoryModule` and raised `UnexpectedException("Cannot retrieve forum threads page: 1")` when the mocked retry result was `None`. |
| Explicit reload must still bypass the cache. | `TestForumThreadCollectionAcquireAll.test_reload_threads_bypasses_cached_category_threads` asserts `reload_threads()` returns a new collection, updates `_threads`, and sends the normal page-1 request. | The RED test failed after the first cache check because `reload_threads()` returned the old cached collection. |
| Existing category thread-list behavior remains stable. | `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll -q` passed 11 tests, and `uv run pytest tests/unit/test_forum_thread.py -q` passed 40 tests. | Pagination, retry exhaustion, nested-thread filtering, description-pager filtering, metadata scoping, title/description spacing, direct thread lookup, or post access regressions reject this local completion claim. |
| Forum-adjacent behavior remains stable. | `uv run pytest tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 139 tests. | Forum category, thread, post, or revision regressions reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `1857df0 perf(forum_thread): skip cached category thread lists`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_skips_cached_category_threads -q` failed before the fix because cached category threads were ignored and the helper attempted a new category-thread request.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_skips_cached_category_threads -q`
- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_reload_threads_bypasses_cached_category_threads -q` failed after the first cache check because `reload_threads()` returned the existing cached collection instead of refreshing it.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_reload_threads_bypasses_cached_category_threads -q`
- `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_skips_cached_category_threads tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_reload_threads_bypasses_cached_category_threads -q` passed 2 cached category-thread tests.
- `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll -q` passed 11 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 40 tests.
- `uv run pytest tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 139 tests.
- `uv run pytest tests/unit -q` passed 695 tests.
- `uv run ruff check src/wikidot/module/forum_thread.py src/wikidot/module/forum_category.py tests/unit/test_forum_thread.py`
- `uv run ruff format --check src/wikidot/module/forum_thread.py src/wikidot/module/forum_category.py tests/unit/test_forum_thread.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- `ForumThreadCollection.acquire_all_in_category(...)` returns an existing cached `ForumThreadCollection` when `category._threads` is already populated.
- Cached category thread-list acquisition sends no AMC request.
- Uncached category acquisition still fetches page 1 and additional real pager pages through `amc_request_with_retry(...)`.
- Exhausted first-page and additional-page retries still raise `UnexpectedException`.
- `ForumCategory.reload_threads()` still forces a fresh fetch and replaces `_threads`.
- `ForumCategory.threads` lazy cache behavior remains unchanged.
- Parser scoping, nested-thread filtering, description-pager filtering, title/description spacing, category ownership, direct thread lookup, thread posts, and reply behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Callers can naturally pass a `ForumCategory` object through helper code after `category.threads` has already loaded its thread list. Refetching the same category thread list adds avoidable AMC work and can discard the cached collection object even though no caller-visible freshness request was made. Returning the cached collection makes direct helper acquisition consistent with the lazy property while preserving explicit freshness through `reload_threads()`.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed forum drafts repeatedly identified category thread-list acquisition as a practical read-heavy surface, including retry hardening, pagination, parser scoping, description-pager filtering, and title/description text fidelity.
- Issues 134 and 135 showed the same cache-aware helper gap in adjacent forum post-list and forum post revision-list helpers.
- Prior cache-aware local drafts established that collection helpers should avoid repeat reads when the same object already carries the requested data, while explicit reload methods should remain available for freshness.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved forum contents out of upstream discussion.

## Additional Notes

This slice does not add a public refresh method, change category-thread parser output, alter pagination semantics, change retry policy, change direct thread lookup, change post acquisition, or modify thread/category mutation methods. It only lets already acquired category thread lists satisfy direct helper acquisition before new category-thread AMC requests are built, and keeps `reload_threads()` as the cache-bypass path.
