# PR Draft: Skip Cached Thread Post-List Fetches

## Summary

`ForumThread.posts` already caches a thread's `ForumPostCollection`, but the lower-level batch helper `ForumPostCollection.acquire_all_in_threads(...)` ignored that cache. A caller that batched a mix of already acquired threads and uncached threads still sent `forum/ForumViewThreadPostsModule` requests for every unique thread ID, then replaced the cached result with a newly parsed collection.

This fix seeds the batch result from threads whose `_posts` cache is already populated and only requests first pages for uncached unique threads. Public result keys, duplicate thread-ID dedupe, pagination, retry exhaustion, parser scoping, and direct `thread.posts` behavior remain unchanged.

## Related Issue

Builds on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), which made thread post-list reads retry-aware and failure-visible, [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), which deduplicated duplicate thread IDs in batched post-list reads, and [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md), which avoided empty direct thread batches. It also preserves parser and pager hardening from [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), and [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), and follows the cache-aware collection pattern from [008-pr-skip-cached-source-fetches.md](008-pr-skip-cached-source-fetches.md), [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md), and [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md).

No upstream issue was filed from this local workspace.

## Changes

- Reuse `thread._posts` in `ForumPostCollection.acquire_all_in_threads(...)` when a unique input thread already has acquired posts.
- Request `forum/ForumViewThreadPostsModule` first pages only for uncached unique threads.
- Return immediately when every unique input thread is already cached.
- Add a focused regression covering a mixed cached/uncached thread batch and proving only the uncached thread ID is requested.
- Preserve duplicate thread-ID dedupe, pagination requests, retry exhaustion errors, parser scoping, and existing `ForumThread.posts` lazy cache behavior.

## Type Of Change

- Performance improvement
- Cache-aware batch behavior
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Already acquired thread post collections must satisfy `acquire_all_in_threads(...)` without being fetched again. | `TestForumPostCollectionAcquireAll.test_acquire_all_in_threads_skips_cached_thread_posts` asserts the cached collection object is returned for the cached thread. | The RED test failed before the fix because the cached entry was overwritten by a newly fetched and parsed collection. |
| Mixed cached/uncached batches must still fetch uncached threads. | The same focused test asserts the uncached thread returns two parsed posts and that `amc_request_with_retry(...)` receives only that uncached thread ID. | A regression that omits the uncached thread or requests the cached thread rejects this local completion claim. |
| Existing thread post-list behavior remains stable. | `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll -q` passed 11 tests. | Pagination, duplicate-thread-ID dedupe, pager filtering, first-page retry exhaustion, or additional-page retry exhaustion regressions reject this local completion claim. |
| Forum-adjacent behavior remains stable. | `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py -q` passed 134 tests. | Forum thread/category/revision regressions reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `3068746 perf(forum_post): skip cached thread post lists`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_skips_cached_thread_posts -q` failed before the fix because the cached `ForumPostCollection` was overwritten by a newly fetched collection.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_skips_cached_thread_posts -q`
- `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_skips_cached_thread_posts tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_all_cached_skips_fetch -q` passed 2 cached-thread tests.
- `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll -q` passed 11 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 45 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py -q` passed 134 tests.
- `uv run pytest tests/unit -q` passed 690 tests.
- `uv run ruff check src/wikidot/module/forum_post.py tests/unit/test_forum_post.py`
- `uv run ruff format --check src/wikidot/module/forum_post.py tests/unit/test_forum_post.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- `ForumPostCollection.acquire_all_in_threads(...)` returns an existing cached `ForumPostCollection` for each first-seen unique thread whose `_posts` is already populated.
- Cached thread IDs are not included in the first-page `forum/ForumViewThreadPostsModule` batch.
- Uncached unique threads are still fetched and parsed.
- If every unique thread is cached, no AMC request is sent.
- Duplicate thread IDs continue to collapse to the first-seen unique thread.
- Thread post-list pagination still requests pages 2 and later for uncached threads with real pagers.
- Pager-like markup inside authored post content remains ignored.
- Exhausted first-page and additional-page retries still raise `UnexpectedException`.
- `ForumThread.posts` lazy cache behavior remains unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Callers can naturally mix `ForumThread` objects whose posts were already loaded through `thread.posts` with uncached threads from search, category scans, or retry queues. Refetching an already loaded post list adds avoidable AMC work and can discard the cached collection object even though no caller-visible freshness request was made. Skipping cached threads makes the batch helper consistent with existing lazy-cache behavior while keeping explicit reloads available through caller code that clears or replaces the cache.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed forum drafts repeatedly identified thread post-list acquisition as a practical read-heavy surface, including retry hardening, duplicate thread-ID batching, empty direct batches, parser scoping, pager filtering, and title text fidelity.
- Prior cache-aware local drafts established that collection helpers should avoid repeat reads when the same object already carries the requested data.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved forum contents out of upstream discussion.

## Additional Notes

This slice does not add a public refresh method, change `ForumThread.reply(...)`, alter parser output, change pagination semantics, or change the shape of the result dictionary. It only lets already acquired thread post lists satisfy the batch helper before new AMC requests are built.
