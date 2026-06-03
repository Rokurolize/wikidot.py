# PR Draft: Deduplicate Thread Detail Fetch IDs

## Summary

`ForumThreadCollection.acquire_from_thread_ids(...)`, exposed through `Site.get_threads(...)`, builds one `forum/ForumViewThreadModule` request for each requested thread ID. When callers pass the same thread ID more than once, the read path used to send duplicate thread detail requests even though the same parsed thread detail can satisfy every duplicate entry.

The fix keeps `Site.get_threads(...)` and `ForumThreadCollection.acquire_from_thread_ids(...)` result ordering stable while deduplicating direct thread detail fetches by first-seen thread ID. Retry handling, exhausted retry errors, requested-ID validation, parsing, optional category association, thread post lazy loading, and reply mutation behavior stay unchanged.

## Related Issue

Builds on the retry-aware direct thread detail work in [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md). Also follows the ordered deduplication pattern from [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), and [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md). No upstream issue filed yet.

## Changes

- Deduplicate `ForumThreadCollection.acquire_from_thread_ids(...)` input IDs before constructing `ForumViewThreadModule` AMC requests.
- Preserve first-seen thread ID order for the direct detail request batch.
- Preserve `Site.get_threads([...])` and `ForumThreadCollection.acquire_from_thread_ids(...)` output order and duplicate positions by rebuilding the collection in the original requested ID order.
- Preserve retry-aware AMC, exhausted thread-specific errors, requested thread ID mismatch detection, thread page parsing, optional category assignment, lazy `ForumThread.posts`, and `ForumThread.reply(...)` mutation behavior.
- Add a focused regression test covering duplicate direct thread IDs.

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
| R1: Duplicate direct thread IDs do not trigger duplicate detail fetches | `acquire_from_thread_ids(...)` calls `amc_request_with_retry(...)` with one `ForumViewThreadModule` request per first-seen thread ID | `test_acquire_from_ids_deduplicates_duplicate_thread_ids` | Reverting the dedupe makes the focused test fail with `ValueError: zip() argument 2 is longer than argument 1` |
| R2: Existing collection ordering is preserved | Duplicate input positions still produce duplicate output positions in the original order | Same focused test | Returning only unique threads would break callers that align results with requested IDs |
| R3: Existing direct thread behavior is preserved | Retry, exhausted errors, ID mismatch checks, parsing, category association, lazy posts, and reply paths remain green | Commands listed below | Existing forum thread/category/post tests fail if retry, parse, or mutation boundaries change |

## Testing

Local implementation commit: `a4b3fed perf(forum_thread): deduplicate thread detail fetch ids`

- [x] `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_deduplicates_duplicate_thread_ids -q` failed before the fix with `ValueError: zip() argument 2 is longer than argument 1`, then passed after the fix with one direct thread detail request for duplicate thread IDs.
- [x] `uv run --extra test pytest tests/unit/test_forum_thread.py -q` passed with 29 tests.
- [x] `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py -q` passed with 76 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 614 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`

## Acceptance Criteria

- Duplicate thread IDs in `ForumThreadCollection.acquire_from_thread_ids(...)` input are fetched once.
- First-seen request order is preserved.
- Returned collection entries remain aligned with the original requested ID order, including duplicate positions.
- Existing exhausted retry errors keep their thread-specific `UnexpectedException` message.
- Requested thread ID mismatch detection still raises `NoElementException`.
- Successful thread parsing, optional category association, `Site.get_thread(...)`, `Site.get_threads(...)`, `ForumThread.get_from_id(...)`, lazy `ForumThread.posts`, and `ForumThread.reply(...)` behavior remain unchanged.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Direct forum thread lookup is a read-heavy workflow for moderation, archival indexing, and discussion inspection. Deduplicating identical thread IDs avoids redundant AMC detail work while keeping the public collection order stable for callers that pass an ID list and expect results to align with that list.

## Local Evidence, Not For Upstream Paste

- Local forum read hardening in [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), and [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md) established forum thread inspection as an active read-heavy surface.
- The refreshed complexity scan continues to flag `src/wikidot/module/forum_thread.py` as a forum inspection hotspot.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice does not change category thread-list retrieval, thread parsing rules, post-list retrieval, post source fetching, lazy post acquisition, or forum mutation methods. It only removes duplicate direct thread detail requests for repeated thread IDs while preserving the original requested-ID order in the returned collection. The later follow-up [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md) skips the same direct thread detail request path when the requested ID list is empty.
