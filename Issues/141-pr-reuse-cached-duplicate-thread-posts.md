# PR Draft: Reuse Cached Duplicate Thread Post Lists

## Summary

`ForumPostCollection.acquire_all_in_threads(...)` already skips a first-seen thread whose `_posts` cache is populated, and it already deduplicates duplicate thread IDs before building `forum/ForumViewThreadPostsModule` requests. Before this fix, the helper still missed one common mixed-collection case: when the first occurrence of a thread ID was uncached but a later duplicate `ForumThread` object carried an existing `_posts` collection, the helper ignored the later cache and fetched the post list again.

This fix indexes cached post lists by thread ID before first-seen deduplication. If a first-seen thread is uncached but another duplicate input object already has posts, the helper copies that cached post list into a new `ForumPostCollection` owned by the first-seen thread and skips the AMC request. Public result keys, first-seen ownership, duplicate thread-ID dedupe, pagination, retry exhaustion, parser scoping, cached-source preservation, and direct `thread.posts` behavior remain unchanged.

## Related Issue

Builds on [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), which made first-seen cached threads skip post-list fetches, and [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), which established duplicate thread IDs as a practical batch performance lead. It also follows the cached duplicate reuse pattern from [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), and [132-pr-reuse-cached-duplicate-page-ids.md](132-pr-reuse-cached-duplicate-page-ids.md).

No upstream issue was filed from this local workspace.

## Changes

- Build a `thread.id -> cached ForumPostCollection` map before first-seen duplicate filtering.
- When the first-seen thread is uncached but a later duplicate is cached, copy the cached posts into a collection owned by the first-seen thread.
- Preserve cached post source text while avoiding revision collection sharing across different post owners.
- Skip `forum/ForumViewThreadPostsModule` when every uncached first-seen thread can be satisfied from cached duplicates.
- Add a focused regression covering an uncached first-seen thread followed by a cached duplicate thread with the same ID.

## Type Of Change

- Performance improvement
- Cache-aware duplicate reuse
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A later cached duplicate thread must satisfy an uncached first-seen same-ID thread without an AMC request. | `TestForumPostCollectionAcquireAll.test_acquire_all_in_threads_reuses_later_cached_duplicate_thread_posts` asserts neither plain nor retry-aware AMC helper is called. | The RED test failed before the fix because the first-seen uncached thread was added to the fetch batch. |
| Cached duplicate reuse must preserve first-seen thread ownership. | The same focused test asserts the returned collection is owned by the first-seen thread, is not the later duplicate's cached collection, and contains a distinct `ForumPost` whose `thread` is the first-seen thread. | Returning the later duplicate's cached collection directly would point posts at the wrong `ForumThread` object. |
| Reused cached posts should preserve cheap cached source text without sharing owner-bound revision collections. | The focused test asserts `_source == "cached source"` on the copied post and `_revisions is None` when the cached duplicate post had a revision cache. | Dropping source text would make a later `post.source` access perform avoidable work; sharing `_revisions` would point revision data at the wrong post owner. |
| Existing thread post-list behavior remains stable. | `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll -q` passed 12 tests, and `uv run pytest tests/unit/test_forum_post.py -q` passed 46 tests. | Regressions in ordinary duplicate dedupe, first-seen cached skip, all-cached skip, pagination, pager filtering, first-page retry exhaustion, additional-page retry exhaustion, or direct acquisition reject this local completion claim. |
| Forum-adjacent behavior remains stable. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 140 tests. | Forum category/thread/post revision regressions reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check HEAD~1..HEAD`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `04ada52 perf(forum_post): reuse cached duplicate thread posts`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_reuses_later_cached_duplicate_thread_posts -q` failed before the fix because the helper ignored the later cached duplicate and attempted to fetch the first-seen thread.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_reuses_later_cached_duplicate_thread_posts -q`
- `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll -q` passed 12 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 46 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 140 tests.
- `uv run pytest tests/unit -q` passed 705 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check HEAD~1..HEAD`

Not run: `uv run pyright` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- `ForumPostCollection.acquire_all_in_threads([uncached_thread, cached_duplicate_thread])` returns a result for the shared thread ID without calling AMC when `cached_duplicate_thread._posts` is populated.
- The returned collection for that thread ID is owned by `uncached_thread`, not by the later duplicate object.
- Returned copied posts point at `uncached_thread`.
- Cached post source text is preserved on copied posts.
- Cached revision collections are not shared across different copied post owners.
- Existing first-seen cached skip and all-cached skip behavior remains unchanged.
- Existing first-seen duplicate ownership for uncached duplicate batches remains unchanged.
- Pagination, retry exhaustion handling, authored-content pager filtering, and parser scoping remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Thread batches can be assembled from category scans, cached `thread.posts` accesses, retry queues, and caller-side merges. When those sources contain duplicate `ForumThread` objects for the same ID, a later object may already carry the post list even if the first object does not. Reusing that cached data avoids a redundant AMC round trip and another failure point while preserving the first-seen result ownership expected by existing duplicate-ID behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed forum drafts repeatedly identified thread post-list acquisition as a practical read-heavy surface, including retry hardening, duplicate thread-ID batching, empty direct batches, cached first-seen skips, parser scoping, pager filtering, and title text fidelity.
- Prior cached duplicate reuse drafts established that collection helpers should reuse same-ID cached data before constructing request batches, while preserving object ownership.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved forum contents out of upstream discussion.

## Additional Notes

This slice does not add a public refresh method, change `ForumThread.reply(...)`, alter parser output, change pagination semantics, or change the shape of the result dictionary. It only lets cached duplicate post lists satisfy uncached first-seen same-ID threads before new AMC requests are built.
