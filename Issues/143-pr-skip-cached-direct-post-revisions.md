# PR Draft: Skip Cached Direct Post Revision Fetches

## Summary

`ForumPostRevisionCollection.acquire_all_for_posts(...)` already skips cached post revision lists in the batch path, including first-seen cached posts and later cached duplicate posts. Before this fix, the single-post helper `ForumPostRevisionCollection.acquire_all(post)` did not share that cache-aware behavior: even when `post._revisions` was already populated, it still built a `forum/sub/ForumPostRevisionsModule` request and could fail or perform a redundant AMC round trip.

This fix adds a fast path at the start of `ForumPostRevisionCollection.acquire_all(post)`. When the target post already owns a `ForumPostRevisionCollection`, the direct helper returns that collection immediately. Uncached posts still use the existing retry-aware request, parser, and exhausted-retry error behavior.

## Related Issue

Builds on [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), which made cached post revision lists skip batch fetches, and [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), which reused later cached duplicate post revision lists in the batch helper. It also keeps the direct acquisition path aligned with the retry-aware revision fetch behavior in [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md).

No upstream issue was filed from this local workspace.

## Changes

- Return `post._revisions` immediately from `ForumPostRevisionCollection.acquire_all(post)` when the direct target is already cached.
- Leave uncached direct acquisition on the existing `amc_request_with_retry(...)` and parser path.
- Add a focused regression that seeds `post._revisions`, makes AMC helpers fail if called, and asserts the cached collection is returned unchanged.

## Type Of Change

- Performance improvement
- Cache-aware direct helper
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Direct post revision acquisition must not refetch an already cached `post._revisions` collection. | `TestForumPostRevisionCollectionAcquireAll.test_acquire_all_skips_cached_post_revisions` asserts both plain and retry-aware AMC helpers are not called. | The RED test failed before the fix because the helper ignored the cache and raised `UnexpectedException` from the forced `None` response. |
| Cached direct acquisition should preserve object identity. | The focused test asserts the returned collection is the exact cached `ForumPostRevisionCollection` object. | Copying or reparsing the revisions would change identity and make direct cache behavior less predictable. |
| Uncached direct acquisition remains retry-aware and parser-backed. | The existing `TestForumPostRevisionCollectionAcquireAll` tests still passed 4 tests, including ordinary acquisition and exhausted retry behavior. | Regressions in parser output, request module name, or retry-exhaustion error handling reject this local completion claim. |
| Batch post revision behavior remains stable. | `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 38 tests, including the batch cached and duplicate reuse cases. | Regressions in batch duplicate dedupe, cached duplicate reuse, `with_html=True`, or cached HTML propagation reject this local completion claim. |
| Forum-adjacent behavior remains stable. | `uv run pytest tests/unit/test_forum_*.py -q` passed 142 tests. | Forum category/thread/post/revision regressions reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check HEAD~1..HEAD`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `1dbd300 perf(forum_post_revision): skip cached direct post revisions`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_skips_cached_post_revisions -q` failed before the fix because the direct helper ignored `post._revisions`, called the retry-aware AMC helper, and raised `UnexpectedException: Cannot retrieve forum post revisions for post: 5001`.
- GREEN: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_skips_cached_post_revisions -q`
- `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll -q` passed 4 tests.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 38 tests.
- `uv run pytest tests/unit/test_forum_*.py -q` passed 142 tests.
- `uv run pytest tests/unit -q` passed 707 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check HEAD~1..HEAD`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- `ForumPostRevisionCollection.acquire_all(post)` returns `post._revisions` without making an AMC request when the post revision collection is already cached.
- The returned direct cached collection is the same object stored on the post.
- Uncached direct acquisition still uses `forum/sub/ForumPostRevisionsModule` through `amc_request_with_retry(...)`.
- Existing direct retry exhaustion handling remains unchanged.
- Existing batch cached skip, cached duplicate reuse, duplicate post-ID dedupe, `with_html=True`, revision HTML dedupe, and parser scoping remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Callers can reach a post revision list through both `post.revisions` and collection helper paths. When the post object already carries its revision collection, the direct helper should not issue another network request for the same immutable revision list. This avoids a redundant AMC round trip and keeps the direct helper consistent with the cache-aware batch helper.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed forum drafts repeatedly identified post revision acquisition as a practical read-heavy surface, including retry hardening, duplicate post-ID batching, cached first-seen skips, cached duplicate reuse, parser scoping, and `with_html=True` behavior.
- This slice came from comparing the newly cache-aware batch helper with the still-uncached direct helper and then proving the direct helper's redundant fetch with a RED no-fetch mock.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved forum contents out of upstream discussion.

## Additional Notes

This slice does not add a public refresh method, mutate cached collections, change revision parser output, alter batch result keys, change retry policy, or alter lazy `ForumPostRevision.html`. It only makes the direct post revision-list helper honor an already populated cache before building a new revision-list AMC request.
