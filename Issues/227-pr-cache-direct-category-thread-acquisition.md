# PR Draft: Cache Direct Category Thread Acquisition

## Summary

`ForumCategory.threads` caches the `ForumThreadCollection` it lazily reads from `ForumThreadCollection.acquire_all_in_category(...)`, and the lower-level helper already checks `category._threads` before making an AMC request. Before this fix, a caller that used the public helper directly received the fetched collection but left `category._threads` unset. A later `category.threads` access or repeated direct helper call could therefore fetch the same category thread list again even though the helper advertised cache-aware behavior at entry.

This change stores the returned `ForumThreadCollection` in `category._threads` only after a successful direct acquisition completes. Fetch and parse failures still leave the cache empty, `ForumCategory.reload_threads()` still clears the cache before fetching, pagination behavior is unchanged, and already-cached categories still skip AMC requests.

## Related Issue

Builds on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), which made category thread-list reads retry-aware, [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), which established that `ForumThreadCollection.acquire_all_in_category(...)` should honor an existing `category._threads` cache, [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), and [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), which hardened category thread-list parser, fetch, and response-body diagnostics. It also follows the cache-aware collection pattern from [008-pr-skip-cached-source-fetches.md](008-pr-skip-cached-source-fetches.md), [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), and [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md).

No upstream issue was filed from this local workspace.

## Changes

- Populate `category._threads` with the returned `ForumThreadCollection` when `ForumThreadCollection.acquire_all_in_category(category)` completes successfully.
- Share the successful-return path for no-pager, single-page pager, and multi-page acquisitions so all complete reads cache consistently.
- Preserve `category._threads is not None` fast-path behavior.
- Preserve `ForumCategory.reload_threads()` semantics by keeping its explicit cache clear before acquisition.
- Add a focused regression proving direct acquisition populates the category cache and that a later `category.threads` access does not refetch.

## Type Of Change

- Performance improvement
- Cache consistency hardening
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Successful direct category thread-list acquisition must populate `category._threads` with the returned collection. | `TestForumThreadCollectionAcquireAll.test_acquire_all_populates_category_threads_cache` asserts `mock_forum_category_no_http._threads is collection` immediately after direct acquisition. | The RED test failed before the fix because `_threads` stayed `None` after the helper returned. |
| A later `category.threads` access after direct acquisition must reuse the same collection without another AMC request. | The focused test asserts `mock_forum_category_no_http.threads is collection` and `amc_request_with_retry.assert_called_once()`. | A second fetch, a distinct collection object, or a property cache miss rejects this local completion claim. |
| Existing cached-category fast-path behavior remains unchanged. | `TestForumThreadCollectionAcquireAll.test_acquire_all_skips_cached_category_threads` still passes and asserts no AMC helper is called. | Fetching when `_threads` is already set rejects this local completion claim. |
| `ForumCategory.reload_threads()` still bypasses stale cached data before storing the fresh collection. | `TestForumThreadCollectionAcquireAll.test_reload_threads_bypasses_cached_category_threads` still passes and asserts the returned collection replaces the prior cache. | Reusing stale cached threads during reload, failing to store the reloaded collection, or changing request payloads rejects this local completion claim. |
| Failed acquisitions must not seed the cache. | Existing missing-body and exhausted-pagination failure tests still pass; the new cache write is only reached by successful return paths. | Caching a partial first page, caching after a missing JSON body, or caching after exhausted additional-page retry rejects this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `31b833c perf(forum_thread): cache direct category thread acquisition`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_populates_category_threads_cache -q` failed before the fix because `_threads` remained `None` after a successful direct fetch.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_populates_category_threads_cache -q`.
- `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll -q` passed 15 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py -q` passed 121 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run pytest tests/unit -q` passed 771 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `ForumThreadCollection.acquire_all_in_category(category)` returns the same collection it stores in `category._threads` after a successful direct read.
- A following `category.threads` access returns that stored collection without another AMC request.
- Existing `category._threads` values still satisfy direct acquisition without fetching.
- `ForumCategory.reload_threads()` still clears stale cached data and stores the fresh acquisition result.
- Successful no-pager, single-page pager, and multi-page acquisitions all use the same cache behavior.
- Failed first-page response, missing response body, malformed parser input, exhausted additional-page retry, and missing additional-page response body do not seed `category._threads`.
- Category thread-list parsing, pager filtering, response-body validation, retry behavior, and request payloads remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, non-goals, verification, and false-positive rejection checks.
- `Issues/README.md` records the local draft and implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Callers can naturally use `ForumThreadCollection.acquire_all_in_category(category)` directly when batching forum scans, composing retry queues, or avoiding property syntax in helper code. Because the helper already checks `category._threads`, a successful direct read should become the cache source for the same category object. Populating the cache after a complete acquisition avoids redundant AMC work and keeps direct helper usage consistent with `ForumCategory.threads` without adding a refresh API or changing parser output.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed forum drafts repeatedly identified category thread-list acquisition as a practical read-heavy surface, including retry hardening, cached skip behavior, parser scoping, response-body validation, pager filtering, and thread title/description fidelity.
- Prior cache-aware local drafts established that collection helpers should avoid repeat reads when the target object already carries the requested data.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved forum contents out of upstream discussion.

## Additional Notes

This slice does not add a public refresh method, change `ForumCategory.reload_threads()`, alter thread parser output, change pagination semantics, or change the collection type. It only stores the successful direct acquisition result in the cache that the helper already respects.
