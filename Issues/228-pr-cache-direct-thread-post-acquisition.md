# PR Draft: Cache Direct Thread Post Acquisition

## Summary

`ForumThread.posts` caches the `ForumPostCollection` it lazily reads from `ForumPostCollection.acquire_all_in_threads(...)`, and the lower-level batch helper already checks `thread._posts` before making AMC requests. Before this fix, a caller that used `ForumPostCollection.acquire_all_in_thread(thread)` or `acquire_all_in_threads([thread])` directly received the fetched post collection but left `thread._posts` unset. A later `thread.posts` access or repeated direct helper call could therefore refetch the same post list even though the helper already behaved as cache-aware at entry.

This change stores each newly fetched thread's returned `ForumPostCollection` in `thread._posts` only after the whole requested post-list acquisition completes successfully. First-page, parser, response-body, and additional-page failures still leave the cache empty, existing cached threads still skip AMC requests, duplicate thread-ID behavior remains first-seen, and pagination behavior is unchanged.

## Related Issue

Builds on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), which made thread post-list reads retry-aware, [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), which deduplicated duplicate thread IDs in post-list batches, [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), which established that `ForumPostCollection.acquire_all_in_threads(...)` should honor existing `thread._posts` caches, and [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), which reused later cached duplicate thread post lists. It also follows the direct helper cache consistency pattern from [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md).

No upstream issue was filed from this local workspace.

## Changes

- Populate `thread._posts` for each newly fetched target thread after `ForumPostCollection.acquire_all_in_threads(...)` completes successfully.
- Make `ForumPostCollection.acquire_all_in_thread(thread)` return the same collection that is stored in `thread._posts`.
- Preserve existing cached-thread fast paths and later cached duplicate reuse.
- Delay cache writes until after additional-page fetching succeeds so partial first-page results are not stored on failure.
- Add a focused regression proving direct acquisition populates the thread cache and a later `thread.posts` access does not refetch.

## Type Of Change

- Performance improvement
- Cache consistency hardening
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Successful direct thread post-list acquisition must populate `thread._posts` with the returned collection. | `TestForumPostCollectionAcquireAll.test_acquire_all_populates_thread_posts_cache` asserts `mock_forum_thread_no_http._posts is collection` immediately after direct acquisition. | The RED test failed before the fix because `_posts` stayed `None` after the helper returned. |
| A later `thread.posts` access after direct acquisition must reuse the same collection without another AMC request. | The focused test asserts `mock_forum_thread_no_http.posts is collection` and `amc_request_with_retry.assert_called_once()`. | A second fetch, a distinct collection object, or a property cache miss rejects this local completion claim. |
| Existing cached-thread fast-path behavior remains unchanged. | `TestForumPostCollectionAcquireAll.test_acquire_all_in_threads_skips_cached_thread_posts` and `test_acquire_all_in_threads_all_cached_skips_fetch` still pass. | Fetching when `_posts` is already set, or returning a different collection for a cached first-seen thread, rejects this local completion claim. |
| Cached duplicate reuse remains unchanged. | `TestForumPostCollectionAcquireAll.test_acquire_all_in_threads_reuses_later_cached_duplicate_thread_posts` still passes and preserves first-seen ownership. | Returning the later duplicate's collection directly, losing cached source text, sharing revision collections, or making an AMC request rejects this local completion claim. |
| Failed acquisitions must not seed the cache. | Existing first-page exhausted retry, missing first-page body, parser failure, additional-page exhausted retry, and missing additional-page body tests still pass; the new cache write is reached only after the complete batch succeeds. | Caching a partial first page, caching after a missing JSON body, or caching after an additional-page failure rejects this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `a9d6a68 perf(forum_post): cache direct thread post acquisition`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_populates_thread_posts_cache -q` failed before the fix because `_posts` remained `None` after a successful direct fetch.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_populates_thread_posts_cache -q`.
- `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll -q` passed 16 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 163 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run pytest tests/unit -q` passed 772 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `ForumPostCollection.acquire_all_in_thread(thread)` returns the same collection it stores in `thread._posts` after a successful direct read.
- `ForumPostCollection.acquire_all_in_threads([thread])` also stores the successful result for each newly fetched first-seen thread.
- A following `thread.posts` access returns that stored collection without another AMC request.
- Existing `thread._posts` values still satisfy direct and batched acquisition without fetching.
- Later cached duplicate thread post lists can still satisfy an uncached first-seen duplicate without fetching and without sharing owner-bound revision collections.
- Successful no-pager, non-numeric-pager, and multi-page acquisitions all use the same final cache behavior.
- Failed first-page response, missing response body, malformed parser input, exhausted additional-page retry, and missing additional-page response body do not seed `thread._posts`.
- Thread post-list parsing, content-pager filtering, response-body validation, retry behavior, duplicate ordering, cached source preservation, and request payloads remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, non-goals, verification, and false-positive rejection checks.
- `Issues/README.md` records the local draft and implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Callers can naturally use `ForumPostCollection.acquire_all_in_thread(thread)` directly when collecting forum data, composing retry queues, or writing batch helpers around thread objects. Because the batch helper already checks `thread._posts`, a successful direct read should become the cache source for the same thread object. Populating the cache only after a complete acquisition avoids redundant AMC work while preserving failure behavior and leaving explicit refresh under caller control through cache clearing or replacement.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed forum drafts repeatedly identified thread post-list acquisition as a practical read-heavy surface, including retry hardening, duplicate thread-ID batching, empty direct batches, cached first-seen skips, cached duplicate reuse, parser scoping, response-body validation, pager filtering, and title text fidelity.
- Prior cache-aware local drafts established that collection helpers should avoid repeat reads when the target object already carries the requested data.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved forum contents out of upstream discussion.

## Additional Notes

This slice does not add a public refresh method, change `ForumThread.posts`, alter post parser output, change pagination semantics, or change the result dictionary shape. It only stores complete successful direct post-list acquisitions in the cache that the helper already respects.
