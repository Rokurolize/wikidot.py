# PR Draft: Deduplicate Thread Post Fetch IDs

## Summary

`ForumPostCollection.acquire_all_in_threads(...)` fetches the first post-list page for each input `ForumThread` with `forum/ForumViewThreadPostsModule` and returns a dictionary keyed by thread ID. If the input list contains the same thread ID more than once, the public result already collapses to one dictionary entry, but the read path still sent duplicate first-page post-list requests for the duplicate thread ID.

The fix keeps the thread-ID keyed result contract, retry handling, exhausted retry errors, post parsing, pagination, ordering, and source/edit/reply paths stable while deduplicating first-page thread post-list fetch requests by first-seen thread ID.

## Related Issue

Builds on the retry-aware forum thread post-list work in [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md). Also follows the ordered deduplication pattern from [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), and [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md). No upstream issue filed yet.

## Changes

- Deduplicate `ForumPostCollection.acquire_all_in_threads(...)` input threads by `thread.id` before constructing first-page `ForumViewThreadPostsModule` AMC requests.
- Preserve first-seen thread ID order for the first-page request batch.
- Preserve the existing dictionary keyed by thread ID.
- Preserve the first-seen thread object as the returned `ForumPostCollection.thread` for that thread ID.
- Preserve retry-aware AMC, exhausted first/additional-page errors, post parsing, pager handling, source fetching, edit/reply mutation paths, and `ForumThread.posts` behavior.
- Add a focused regression test covering duplicate thread IDs in multi-thread post-list acquisition.

## Type Of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Performance/reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Requirements Traceability

| Requirement | Acceptance | Verification | Negative Control |
| --- | --- | --- | --- |
| R1: Duplicate forum thread IDs do not trigger duplicate first-page post-list fetches | `acquire_all_in_threads(...)` calls `amc_request_with_retry(...)` with one `ForumViewThreadPostsModule` page-1 request per first-seen thread ID | `test_acquire_all_in_threads_deduplicates_duplicate_thread_ids` | Reverting the dedupe makes the focused test fail with `ValueError: zip() argument 2 is shorter than argument 1` |
| R2: Existing result shape is preserved | The returned mapping remains keyed by thread ID and uses the first-seen thread object for the collection | Same focused test | A change that returns duplicate entries would break the existing `dict[int, ForumPostCollection]` contract |
| R3: Existing forum post-list behavior is preserved | Retry, exhausted first/additional-page errors, post parsing, pagination, source fetching, edit/reply paths, and broader forum tests remain green | Commands listed below | Existing post/thread tests fail if retry, parse, pagination, or mutation boundaries change |

## Testing

Local implementation commit: `051ee91 perf(forum_post): deduplicate thread post fetch ids`

- [x] `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_deduplicates_duplicate_thread_ids -q` failed before the fix with `ValueError: zip() argument 2 is shorter than argument 1`, then passed after the fix with one first-page post-list request.
- [x] `uv run --extra test pytest tests/unit/test_forum_post.py -q` passed with 32 tests.
- [x] `uv run --extra test pytest tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed with 91 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 613 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`

## Acceptance Criteria

- Duplicate thread IDs in `ForumPostCollection.acquire_all_in_threads(...)` input are fetched once for the first post-list page.
- First-seen request order is preserved.
- The returned mapping remains keyed by thread ID.
- The first-seen thread object remains the `ForumPostCollection.thread` for that thread ID.
- Existing exhausted first-page and additional-page retry errors keep their thread/page-specific `UnexpectedException` messages.
- Successful post parsing, pagination, non-numeric pager handling, `ForumThread.posts`, forum post source fetching, edit/reply mutation paths, and request retry policy remain unchanged.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Forum thread post-list inspection is a read-heavy workflow for moderation, archiving, discussion analysis, and audit tooling. Deduplicating identical thread IDs avoids redundant AMC work while preserving the existing thread-ID keyed result shape and retry-aware behavior.

## Local Evidence, Not For Upstream Paste

- Local forum read hardening in [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), and [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md) established forum post inspection as an active read-heavy surface.
- The refreshed complexity scan flags `src/wikidot/module/forum_post.py` as a remaining forum inspection hotspot, including the multi-thread post-list acquisition path.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice does not change forum post parsing, pagination semantics, thread detail fetching, category thread-list fetching, forum post source fetching, edit/reply mutation methods, or the retry policy. It only removes duplicate first-page post-list requests for repeated thread IDs in the existing multi-thread read path.
