# PR Draft: Retry Category Thread List Fetches

## Summary

`ForumThreadCollection.acquire_all_in_category(...)`, exposed through `ForumCategory.threads`, retrieves the first page of a category thread list with `forum/ForumViewCategoryModule`, but the first page used the plain `site.amc_request(...)` path. Later paginated pages already used `site.amc_request_with_retry(...)`, but exhausted retries were silently skipped, which could return a partial thread list.

The fix routes the first category thread-list page through `site.amc_request_with_retry(...)` and raises page-numbered `UnexpectedException` errors when any required page cannot be retrieved. Existing parsing, category association, no-pager behavior, and successful pagination behavior are preserved.

## Related Issue

Drafted from the same forum inspection and retry area as [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), and [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md). No upstream issue filed yet.

## Changes

- Use `site.amc_request_with_retry(...)` for the first `forum/ForumViewCategoryModule` category thread-list page.
- Preserve the public `ForumCategory.threads` property and `ForumThreadCollection.acquire_all_in_category(...)` return type.
- Preserve successful pagination behavior for additional pages.
- Raise `UnexpectedException("Cannot retrieve forum threads page: ...")` when the first page or a later page exhausts retries.
- Preserve existing thread parsing and category association behavior.
- Add focused tests for transient first-page retry and exhausted paginated-page retry handling.

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

Local implementation commit: `51ac867 fix(forum_thread): retry category thread list fetches`

- [x] `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_category_threads_retries_transient_first_page_failures -q` failed before the fix because the plain AMC path tried to parse a transient exception object as a response and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_forum_thread.py -q` passed with 25 tests.
- [x] `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py -q` passed with 40 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 565 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed the current complexity leads.

## Acceptance Criteria

- A transient AMC failure while fetching the first category thread-list page is retried through `site.amc_request_with_retry(...)`.
- Additional category thread-list pages keep using retry-aware AMC.
- Successful retry responses are parsed into the same `ForumThread` records as before.
- Thread records keep the source `ForumCategory` association.
- Exhausted retries for any required page raise page-numbered `UnexpectedException` instead of returning a partial list.
- Existing direct thread retrieval and thread mutation behavior is unchanged.

## Upstream-Safe Motivation

Forum thread-list inspection is a read-heavy Wikidot workflow and naturally follows category inspection. It should have the same transient-failure tolerance as other retry-aware collection paths, and exhausted paginated reads should not silently lose threads.

## Local Evidence, Not For Upstream Paste

- Local work on source collection, member/application inspection, recent-changes retrieval, and forum category retrieval repeatedly hardened read-heavy AMC paths with retry-aware calls.
- The complexity scan continues to flag `src/wikidot/module/forum_thread.py` as a forum inspection path where AMC failure interrupts list collection.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, or command transcripts into an upstream PR.

## Additional Notes

This slice does not change thread detail lookup, thread parsing rules, category parsing, or forum mutation methods. It only moves category thread-list reads to the established retry-aware AMC helper and makes exhausted retries explicit.

Follow-up [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md) keeps this retry-aware acquisition path and narrows the category thread-list parser so description-rendered user/date markup cannot be mistaken for the row's structural creator/date metadata.
