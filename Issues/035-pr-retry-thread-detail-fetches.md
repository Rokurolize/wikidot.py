# PR Draft: Retry Thread Detail Fetches

## Summary

`ForumThreadCollection.acquire_from_thread_ids(...)`, exposed through `Site.get_thread(...)`, `Site.get_threads(...)`, and `ForumThread.get_from_id(...)`, retrieves thread detail pages with `forum/ForumViewThreadModule`, but it used the plain `site.amc_request(...)` path. A transient AMC failure could make direct thread inspection fail even though the neighboring forum category and category thread-list reads now use retry-aware AMC.

The fix routes thread detail fetches through `site.amc_request_with_retry(...)` and raises `UnexpectedException("Cannot retrieve forum thread: ...")` when retries are exhausted. Existing thread parsing, ID mismatch detection, optional category association, and reply behavior are preserved.

## Related Issue

Drafted from the same forum inspection and retry area as [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), and [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md). No upstream issue filed yet.

## Changes

- Use `site.amc_request_with_retry(...)` for `forum/ForumViewThreadModule` thread detail requests.
- Preserve the public `Site.get_thread(...)`, `Site.get_threads(...)`, `ForumThread.get_from_id(...)`, and `ForumThreadCollection.acquire_from_thread_ids(...)` return types.
- Raise `UnexpectedException("Cannot retrieve forum thread: ...")` when a required thread detail request exhausts retries.
- Preserve existing thread page parsing and requested-ID validation.
- Preserve forum thread mutation paths such as `ForumThread.reply(...)` on the existing plain action request path.
- Add focused tests for transient detail-fetch retry and exhausted retry handling.

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

Local implementation commit: `763f48c fix(forum_thread): retry thread detail fetches`

- [x] `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_site_get_threads_retries_transient_fetch_failures -q` failed before the fix because the plain AMC path tried to parse a transient exception object as a response and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_forum_thread.py -q` passed with 27 tests.
- [x] `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py -q` passed with 64 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 567 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed the current complexity leads.

## Acceptance Criteria

- A transient AMC failure while fetching a thread detail page is retried through `site.amc_request_with_retry(...)`.
- Successful retry responses are parsed into the same `ForumThread` records as before.
- `Site.get_thread(...)`, `Site.get_threads(...)`, and `ForumThread.get_from_id(...)` continue to expose the same public API.
- Requested thread ID mismatch detection still raises `NoElementException`.
- Exhausted retries for a required thread detail page raise `UnexpectedException` with the affected thread ID instead of producing an attribute error or silently omitting the thread.
- Existing forum category list, category thread-list, post-list, and reply behavior is unchanged.

## Upstream-Safe Motivation

Direct thread lookup is a read-heavy Wikidot forum inspection workflow and naturally follows category and thread-list inspection. It should have the same transient-failure tolerance as other retry-aware collection paths, while exhausted direct reads should be explicit because callers requested specific thread IDs.

## Local Evidence, Not For Upstream Paste

- Local work on source collection, member/application inspection, recent-changes retrieval, forum category retrieval, and category thread-list retrieval repeatedly hardened read-heavy AMC paths with retry-aware calls.
- The complexity scan continues to flag `src/wikidot/module/forum_thread.py` as a forum inspection path where AMC failure interrupts collection work.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, or command transcripts into an upstream PR.

## Additional Notes

This slice does not change category thread-list retrieval, thread parsing rules, post retrieval, or forum mutation methods. It only moves direct thread detail reads to the established retry-aware AMC helper and makes exhausted retries explicit.
