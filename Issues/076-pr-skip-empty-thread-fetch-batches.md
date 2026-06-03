# PR Draft: Skip Empty Direct Thread Fetch Batches

## Summary

`Site.get_threads([])` routes through `ForumThreadCollection.acquire_from_thread_ids(...)`. Before this fix, an empty requested thread ID list still called `site.amc_request_with_retry([])` and then iterated the empty response shape, even though no `forum/ForumViewThreadModule` read could be useful.

This fix returns an empty `ForumThreadCollection` immediately when the requested thread ID list is empty. The public result type, site ownership, duplicate-ID fetch deduplication, retry behavior, thread ID mismatch checks, and non-empty direct thread lookup behavior remain unchanged.

## Related Issue

Builds on [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), which made direct thread detail reads retry-aware, and [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), which removed duplicate direct thread detail requests while preserving requested-ID output order.

No upstream issue was filed from this local workspace.

## Changes

- Return `ForumThreadCollection(site=site, threads=[])` immediately from `ForumThreadCollection.acquire_from_thread_ids(...)` when `thread_ids` is empty.
- Preserve `Site.get_threads([])` as the public wrapper behavior for empty direct thread lookup.
- Preserve non-empty request construction, first-seen duplicate-ID request deduplication, retry-aware AMC, exhausted retry errors, requested-ID validation, thread page parsing, optional category assignment, `Site.get_thread(...)`, `Site.get_threads(...)`, `ForumThread.get_from_id(...)`, lazy `ForumThread.posts`, and reply mutation behavior.
- Add a focused public-wrapper regression test proving `Site.get_threads([])` does not call either plain or retry-aware AMC.

## Type Of Change

- Performance improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Empty direct thread lookup should not issue an empty AMC batch. | `TestForumThreadCollectionAcquireFromIds.test_site_get_threads_empty_input_skips_fetch` asserts `amc_request` and `amc_request_with_retry` are not called for `Site.get_threads([])`. | The RED test failed before the fix because `amc_request_with_retry([])` was called once. |
| Empty direct thread lookup should still return the expected collection type and site ownership. | The focused test asserts the result is a `ForumThreadCollection`, has the original `site`, and has length `0`. | Returning a plain list or a collection detached from the site would fail the focused test. |
| Existing thread read behavior stays green. | `uv run --extra test pytest tests/unit/test_forum_thread.py -q` passed 30 tests; `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py -q` passed 77 tests. | Regressions in category thread lists, direct thread detail lookup, post-list lookup, lazy posts, or retry behavior reject the local completion claim. |
| Existing unit behavior stays green. | `uv run --extra test pytest tests/unit -q` passed 629 tests. | Any broad unit regression rejects the local completion claim. |
| Static quality gates remain green. | `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Formatting, lint, type, or whitespace failures reject the local completion claim. |
| Complexity evidence is interpreted conservatively. | The refreshed scanner artifact is still required for the thread report; the claimed improvement is empty-batch elimination on direct thread lookup, not removal of all forum complexity warnings. | Overclaiming that forum scanner warnings disappeared would reject the draft. |

## Testing

Implemented locally in commit `ce7dde4 perf(forum_thread): skip empty thread fetch batches`.

- RED: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_site_get_threads_empty_input_skips_fetch -q` failed before the fix because `amc_request_with_retry([])` was called once.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_site_get_threads_empty_input_skips_fetch -q`
- `uv run --extra test pytest tests/unit/test_forum_thread.py -q` passed 30 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py -q` passed 77 tests.
- `uv run --extra test pytest tests/unit -q` passed 629 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not spawn the `pyright` executable.

## Acceptance Criteria

- `Site.get_threads([])` returns an empty `ForumThreadCollection`.
- The empty result collection keeps the original `Site`.
- Empty input does not call `site.amc_request(...)`.
- Empty input does not call `site.amc_request_with_retry(...)`.
- Non-empty direct thread lookup request construction is unchanged.
- Duplicate non-empty thread IDs are still fetched once and returned in requested-ID order.
- Exhausted retry errors still include the affected thread ID.
- Requested thread ID mismatch detection still raises `NoElementException`.
- Existing category thread-list acquisition, direct thread parsing, `Site.get_thread(...)`, `Site.get_threads(...)`, `ForumThread.get_from_id(...)`, lazy `ForumThread.posts`, and `ForumThread.reply(...)` behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Direct forum thread lookup is a read-heavy workflow for moderation, archival indexing, and discussion inspection. Empty lookup inputs can naturally arise after filtering, deduplication, permission pruning, or optional user-supplied thread ID lists. Returning an empty typed collection without an empty AMC batch removes avoidable work and keeps the helper behavior predictable.

## Local Evidence, Not For Upstream Paste

- Local forum read hardening in [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), and [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md) established forum thread inspection as an active read-heavy surface.
- The focused RED test demonstrated the previous empty-batch behavior through the public `Site.get_threads([])` wrapper.
- The refreshed complexity scan continues to flag forum read helpers as leads; this slice addresses one concrete empty-request path only.
- Keep local rollout paths, account names, and corpus-specific identifiers out of any upstream discussion.

## Additional Notes

This slice does not change category thread-list retrieval, thread parsing rules, non-empty direct thread detail lookup, duplicate thread ID request deduplication, post-list retrieval, post source fetching, lazy post acquisition, or forum mutation methods. It only skips the direct thread detail request path when there are no requested thread IDs.
