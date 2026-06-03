# PR Draft: Retry Thread Post Fetches

## Summary

`ForumPostCollection.acquire_all_in_thread(...)`, `ForumPostCollection.acquire_all_in_threads(...)`, and `ForumThread.posts` retrieve thread post-list pages with `forum/ForumViewThreadPostsModule`. The direct single-thread method used the plain `site.amc_request(...)` path, and the batched method silently skipped exhausted retry results. That could turn a transient first-page failure into an attribute error, cache an empty `ForumThread.posts` collection, or return a partial post list after a later page failed.

The fix routes direct single-thread reads through the retry-aware batched path and raises thread/page-specific `UnexpectedException` errors when required post-list pages exhaust retries. Existing post parsing, successful pagination, non-numeric pager handling, `ForumThread.posts` caching on success, and reply/edit/source-fetch action paths are preserved.

## Related Issue

Drafted from the same forum inspection and retry area as [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), and [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md). No upstream issue filed yet.

Follow-up performance draft: [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md) removes duplicate first-page post-list requests for repeated thread IDs while preserving this retry-aware read path and thread-ID keyed result shape.

## Changes

- Make `ForumPostCollection.acquire_all_in_thread(...)` delegate to `ForumPostCollection.acquire_all_in_threads(...)` so direct post-list reads use the established retry-aware AMC helper.
- Preserve the public `ForumPostCollection.acquire_all_in_thread(...)`, `ForumPostCollection.acquire_all_in_threads(...)`, and `ForumThread.posts` surfaces.
- Raise `UnexpectedException("Cannot retrieve forum posts for thread ... page: ...")` when the first page or an additional page exhausts retries.
- Preserve successful pagination, post parsing, and non-numeric pager fallback behavior.
- Preserve `ForumThread.posts` caching only for successful retrievals.
- Preserve forum post mutation and source-fetch action paths on their existing request helpers.
- Add focused tests for transient first-page retry and exhausted first/additional page retries.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [ ] Security/privacy hardening
- [x] Test addition/modification
- [ ] CI/CD or build related

## Testing

Local implementation commit: `55fcbae fix(forum_post): retry thread post fetches`

- [x] `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_retries_transient_first_page_failures -q` failed before the fix because the plain AMC path tried to parse a transient exception object as a response and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_forum_post.py -q` passed with 25 tests.
- [x] `uv run --extra test pytest tests/unit/test_forum_thread.py tests/unit/test_forum_post.py -q` passed with 53 tests.
- [x] `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py -q` passed with 68 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 571 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed the current complexity leads.

## Acceptance Criteria

- A transient AMC failure while fetching the first thread post-list page is retried through `site.amc_request_with_retry(...)`.
- Successful retry responses are parsed into the same `ForumPost` records as before.
- Direct `ForumPostCollection.acquire_all_in_thread(...)`, batched `ForumPostCollection.acquire_all_in_threads(...)`, and `ForumThread.posts` continue to expose the same public API.
- Exhausted retries for the first page raise `UnexpectedException` with the affected thread ID and page number.
- Exhausted retries for an additional page raise `UnexpectedException` with the affected thread ID and page number instead of returning a partial list.
- `ForumThread.posts` does not cache an empty collection when the first required page cannot be retrieved.
- Existing forum category list, category thread-list, thread detail, reply/edit, and source-fetch behavior is unchanged.

## Upstream-Safe Motivation

Thread post-list inspection is a read-heavy Wikidot forum workflow and naturally follows category and thread-detail inspection. It should have the same transient-failure tolerance as other retry-aware collection paths, and exhausted paginated reads should fail explicitly because silently returning empty or partial post lists can hide missing discussion content.

## Local Evidence, Not For Upstream Paste

- Local work on source collection, member/application inspection, recent-changes retrieval, forum category retrieval, category thread-list retrieval, and thread detail retrieval repeatedly hardened read-heavy AMC paths with retry-aware calls.
- The complexity scan continues to flag `src/wikidot/module/forum_post.py` as a forum inspection path where AMC failure interrupts list collection.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, or command transcripts into an upstream PR.

## Additional Notes

This slice does not change category retrieval, thread detail retrieval, post parsing rules, forum post source retrieval, or forum mutation methods. It only centralizes direct thread post-list retrieval on the retry-aware batched path and makes exhausted retries explicit.
