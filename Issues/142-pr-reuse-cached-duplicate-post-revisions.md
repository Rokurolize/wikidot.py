# PR Draft: Reuse Cached Duplicate Post Revision Lists

## Summary

`ForumPostRevisionCollection.acquire_all_for_posts(...)` already skips a first-seen post whose `_revisions` cache is populated, and it already deduplicates duplicate post IDs before building `forum/sub/ForumPostRevisionsModule` requests. Before this fix, the helper still missed the mirror case: when the first occurrence of a post ID was uncached but a later duplicate `ForumPost` object already carried an acquired `ForumPostRevisionCollection`, the helper ignored the later cache and fetched the revision list again.

This fix indexes cached revision lists by post ID before first-seen duplicate filtering. If a first-seen post is uncached but another duplicate input object already has revisions, the helper copies that cached revision list into a new `ForumPostRevisionCollection` owned by the first-seen post and skips the AMC request. Public result keys, first-seen ownership, duplicate post-ID dedupe, retry exhaustion, optional `with_html=True` HTML acquisition, cached HTML preservation, and direct `post.revisions` behavior remain unchanged.

## Related Issue

Builds on [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), which made first-seen cached posts skip revision-list fetches, and [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), which established duplicate post IDs as a practical batch performance lead. It also follows the cached duplicate reuse pattern from [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), and [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md).

No upstream issue was filed from this local workspace.

## Changes

- Build a `post.id -> cached ForumPostRevisionCollection` map before first-seen duplicate filtering.
- When the first-seen post is uncached but a later duplicate is cached, copy the cached revisions into a collection owned by the first-seen post.
- Preserve cached revision HTML on copied revisions.
- Skip `forum/sub/ForumPostRevisionsModule` when every uncached first-seen post can be satisfied from cached duplicates.
- Add a focused regression covering an uncached first-seen post followed by a cached duplicate post with the same ID.

## Type Of Change

- Performance improvement
- Cache-aware duplicate reuse
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A later cached duplicate post must satisfy an uncached first-seen same-ID post without an AMC request. | `TestForumPostRevisionCollectionAcquireAllForPosts.test_acquire_all_for_posts_reuses_later_cached_duplicate_post_revisions` asserts neither plain nor retry-aware AMC helper is called. | The RED test failed before the fix because the first-seen uncached post was added to the revision-list fetch batch. |
| Cached duplicate reuse must preserve first-seen post ownership. | The same focused test asserts the returned collection is owned by the first-seen post, is not the later duplicate's cached collection, and contains a distinct `ForumPostRevision` whose `post` is the first-seen post. | Returning the later duplicate's cached collection directly would point revisions at the wrong `ForumPost` object. |
| Reused cached revisions should preserve cheap cached HTML. | The focused test asserts the copied revision returns `<p>Cached revision HTML</p>` without calling the HTML fetch path. | Dropping cached HTML would make a later `revision.html` access perform avoidable work. |
| Existing post revision-list behavior remains stable. | `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts -q` passed 9 tests, and `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 37 tests. | Regressions in ordinary duplicate dedupe, first-seen cached skip, all-cached skip, `with_html=True`, retry exhaustion, duplicate revision HTML propagation, parser scoping, or direct acquisition reject this local completion claim. |
| Forum-adjacent behavior remains stable. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 141 tests. | Forum category/thread/post/revision regressions reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check HEAD~1..HEAD`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `69b53a0 perf(forum_post_revision): reuse cached duplicate post revisions`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_reuses_later_cached_duplicate_post_revisions -q` failed before the fix because the helper ignored the later cached duplicate and attempted to fetch the first-seen post, ending in `ValueError: zip() argument 2 is shorter than argument 1` under the no-fetch mock.
- GREEN: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_reuses_later_cached_duplicate_post_revisions -q`
- `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts -q` passed 9 tests.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 37 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 141 tests.
- `uv run pytest tests/unit -q` passed 706 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check HEAD~1..HEAD`

Not run: `uv run pyright` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- `ForumPostRevisionCollection.acquire_all_for_posts([uncached_post, cached_duplicate_post])` returns a result for the shared post ID without calling AMC when `cached_duplicate_post._revisions` is populated.
- The returned collection for that post ID is owned by `uncached_post`, not by the later duplicate object.
- Returned copied revisions point at `uncached_post`.
- Cached revision HTML is preserved on copied revisions.
- Existing first-seen cached skip and all-cached skip behavior remains unchanged.
- Existing first-seen duplicate ownership for uncached duplicate batches remains unchanged.
- Optional `with_html=True` still fetches missing revision HTML from the existing HTML path and skips already acquired HTML.
- Retry exhaustion handling, duplicate revision HTML dedupe, parser scoping, and direct `post.revisions` lazy caching remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Post revision batches can be assembled from thread scans, direct `post.revisions` accesses, retry queues, and caller-side merges. When those sources contain duplicate `ForumPost` objects for the same ID, a later object may already carry the revision list even if the first object does not. Reusing that cached data avoids a redundant AMC round trip and another failure point while preserving the first-seen result ownership expected by existing duplicate-ID behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed forum drafts repeatedly identified post revision acquisition as a practical read-heavy surface, including retry hardening, duplicate post-ID batching, duplicate revision HTML dedupe, cached first-seen skips, cached duplicate HTML reuse, parser scoping, and `with_html=True` behavior.
- Prior cached duplicate reuse drafts established that collection helpers should reuse same-ID cached data before constructing request batches, while preserving object ownership.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved forum contents out of upstream discussion.

## Additional Notes

This slice does not add a public refresh method, change revision parser output, alter duplicate post-ID result keys, change retry policy, change lazy `ForumPostRevision.html`, or alter forum post source/edit/reply behavior. It only lets cached duplicate revision lists satisfy uncached first-seen same-ID posts before new revision-list AMC requests are built.
