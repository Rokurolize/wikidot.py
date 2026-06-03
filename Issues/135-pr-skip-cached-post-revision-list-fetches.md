# PR Draft: Skip Cached Post Revision-List Fetches

## Summary

`ForumPost.revisions` already caches a post's `ForumPostRevisionCollection`, but the lower-level batch helper `ForumPostRevisionCollection.acquire_all_for_posts(...)` ignored that cache. A caller that batched a mix of already acquired posts and uncached posts still sent `forum/sub/ForumPostRevisionsModule` requests for every unique post ID, then replaced the cached result with a newly parsed collection.

This fix seeds the batch result from posts whose `_revisions` cache is already populated and only requests revision lists for uncached unique posts. Public result keys, duplicate post-ID dedupe, retry exhaustion, parser scoping, direct `post.revisions` lazy cache behavior, and optional `with_html=True` HTML acquisition remain unchanged.

## Related Issue

Builds on [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), which made forum post revision-list reads retry-aware and failure-visible, [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), which deduplicated duplicate post IDs in batched revision-list reads, and [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), which kept optional `with_html=True` revision HTML fetching deduplicated. It also preserves cached revision HTML reuse from [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), parser scoping from [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), and follows the cache-aware batch pattern from [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [008-pr-skip-cached-source-fetches.md](008-pr-skip-cached-source-fetches.md), and [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md).

No upstream issue was filed from this local workspace.

## Changes

- Reuse `post._revisions` in `ForumPostRevisionCollection.acquire_all_for_posts(...)` when a unique input post already has acquired revisions.
- Request `forum/sub/ForumPostRevisionsModule` only for uncached unique posts.
- Avoid any revision-list AMC request when every unique input post is already cached.
- Keep `with_html=True` behavior active for cached revision lists, so cached lists can still fetch missing revision HTML without refetching the list.
- Add focused regressions covering mixed cached/uncached batches, all-cached batches, and cached-list `with_html=True` HTML fill behavior.
- Preserve duplicate post-ID dedupe, retry exhaustion errors, revision-list parser scoping, duplicate revision HTML handling, and existing `ForumPost.revisions` lazy cache behavior.

## Type Of Change

- Performance improvement
- Cache-aware batch behavior
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Already acquired forum post revision collections must satisfy `acquire_all_for_posts(...)` without being fetched again. | `TestForumPostRevisionCollectionAcquireAllForPosts.test_acquire_all_for_posts_skips_cached_post_revisions` asserts the cached collection object is returned for the cached post. | The RED test failed before the fix because the cached entry was overwritten by a newly fetched and parsed collection. |
| Mixed cached/uncached batches must still fetch uncached posts. | The same focused test asserts the uncached post returns three parsed revisions and that `amc_request_with_retry(...)` receives only that uncached post ID. | A regression that omits the uncached post or requests the cached post rejects this local completion claim. |
| All-cached batches must not send revision-list requests. | `TestForumPostRevisionCollectionAcquireAllForPosts.test_acquire_all_for_posts_all_cached_skips_fetch` asserts both AMC request helpers are not called. | A regression that builds an empty list-fetch request or refetches cached revisions fails the not-called assertions. |
| Cached revision lists must still participate in optional HTML acquisition. | `TestForumPostRevisionCollectionAcquireAllForPosts.test_acquire_all_for_posts_with_html_reuses_cached_revision_list` asserts `with_html=True` reuses the cached list and sends only the missing `ForumPostRevisionModule` HTML request. | A regression that skips HTML acquisition for cached lists, refetches the list first, or requests the wrong module rejects this local completion claim. |
| Existing forum post revision behavior remains stable. | `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts -q` passed 8 tests, and `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 36 tests. | Retry, exhausted retry, duplicate post-ID dedupe, duplicate revision HTML propagation, lazy HTML, or parser regressions reject this local completion claim. |
| Forum-adjacent behavior remains stable. | `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py -q` passed 137 tests. | Forum post, thread, category, or revision regressions reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `4e6841e perf(forum_post_revision): skip cached post revision lists`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_skips_cached_post_revisions -q` failed before the fix because the cached `ForumPostRevisionCollection` was overwritten by a newly fetched collection.
- GREEN: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_skips_cached_post_revisions -q`
- `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_skips_cached_post_revisions tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_all_cached_skips_fetch tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_with_html_reuses_cached_revision_list -q` passed 3 cached revision-list tests.
- `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts -q` passed 8 tests.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 36 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py -q` passed 137 tests.
- `uv run pytest tests/unit -q` passed 693 tests.
- `uv run ruff check src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py`
- `uv run ruff format --check src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- `ForumPostRevisionCollection.acquire_all_for_posts(...)` returns an existing cached `ForumPostRevisionCollection` for each first-seen unique post whose `_revisions` is already populated.
- Cached post IDs are not included in the `forum/sub/ForumPostRevisionsModule` batch.
- Uncached unique posts are still fetched and parsed.
- If every unique post is cached and `with_html=False`, no AMC request is sent.
- If every unique post is cached and `with_html=True`, no revision-list request is sent, but missing revision HTML is still fetched through the existing revision HTML path.
- Duplicate post IDs continue to collapse to the first-seen unique post.
- Exhausted revision-list retries still raise `UnexpectedException` for uncached posts.
- Duplicate revision HTML dedupe and cached duplicate HTML propagation remain unchanged.
- `ForumPost.revisions` lazy cache behavior remains unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Callers can naturally mix `ForumPost` objects whose revisions were already loaded through `post.revisions` with uncached posts from thread scans, moderation queues, archival tooling, or retry batches. Refetching an already loaded revision list adds avoidable AMC work and can discard the cached collection object even though no caller-visible freshness request was made. Skipping cached posts makes the batch helper consistent with existing lazy-cache behavior while keeping explicit reloads available through caller code that clears or replaces the cache.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed forum drafts repeatedly identified forum post revision acquisition as a practical read-heavy surface, including retry hardening, duplicate post-ID batching, optional HTML dedupe, cached duplicate HTML reuse, and parser scoping.
- Issue 134 showed the same cache-aware batch gap for thread post lists, making `ForumPostRevisionCollection.acquire_all_for_posts(...)` a direct adjacent candidate.
- Prior cache-aware local drafts established that collection helpers should avoid repeat reads when the same object already carries the requested data.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved forum contents out of upstream discussion.

## Additional Notes

This slice does not add a public refresh method, change revision parser output, change revision HTML request construction, alter duplicate post-ID result keys, change retry policy, change lazy `ForumPostRevision.html`, or alter forum post source/edit/reply behavior. It only lets already acquired post revision lists satisfy the batch helper before new revision-list AMC requests are built.
