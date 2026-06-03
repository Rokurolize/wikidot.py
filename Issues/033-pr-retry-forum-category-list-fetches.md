# PR Draft: Retry Forum Category List Fetches

## Summary

`ForumCategoryCollection.acquire_all(...)`, exposed through `site.forum.categories`, retrieves the forum index with `forum/ForumStartModule`, but it used the plain `site.amc_request(...)` path. A transient AMC failure could abort forum category inspection even though the `Site` object already provides retry-aware AMC handling for read-heavy collection paths.

The fix routes the forum category list fetch through `site.amc_request_with_retry(...)`. Existing forum category parsing, empty-list behavior, category field values, and thread creation behavior are preserved. If retries are exhausted, the method raises `UnexpectedException("Cannot retrieve forum categories")` instead of trying to parse a missing response.

## Related Issue

Drafted from the same retry and read-heavy inspection area as [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), and [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md). No upstream issue filed yet.

## Changes

- Use `site.amc_request_with_retry(...)` for the `forum/ForumStartModule` category list request.
- Preserve the public `site.forum.categories` property and `ForumCategoryCollection.acquire_all(...)` return type.
- Preserve existing category parsing and empty forum index behavior.
- Preserve existing `ForumCategory.create_thread(...)` mutation behavior.
- Raise `UnexpectedException("Cannot retrieve forum categories")` when retries are exhausted.
- Add focused tests for transient fetch retry and exhausted retry handling.

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

Local implementation commit: `d6a582b fix(forum_category): retry category list fetches`

- [x] `uv run --extra test pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_site_forum_categories_retries_transient_fetch_failures -q` failed before the fix because the plain AMC path tried to parse a transient exception object as a response and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_forum_category.py -q` passed with 15 tests.
- [x] `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py -q` passed with 38 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 563 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed the current complexity leads.

## Acceptance Criteria

- A transient AMC failure while fetching forum categories is retried through `site.amc_request_with_retry(...)`.
- Successful retry responses are parsed into the same `ForumCategory` records as before.
- Empty forum indexes still return an empty `ForumCategoryCollection`.
- Existing missing-element parse failures still raise `NoElementException`.
- Exhausted retries raise `UnexpectedException` instead of becoming an attribute/parsing failure.
- Existing thread creation behavior is unchanged.

## Upstream-Safe Motivation

Forum category inspection is a read-heavy Wikidot workflow and a prerequisite for thread inspection. It should have the same transient-failure tolerance as other retry-aware Wikidot collection paths while keeping the public API unchanged.

## Local Evidence, Not For Upstream Paste

- Local work on source collection, member/application inspection, recent-changes retrieval, and browser-free publishing repeatedly hardened read-heavy AMC paths with retry-aware calls.
- The complexity scan continues to flag `src/wikidot/module/forum_category.py` as a forum inspection path where AMC failure interrupts list collection.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, or command transcripts into an upstream PR.

## Additional Notes

This slice does not change category parsing rules, thread caching, `ForumCategory.create_thread(...)`, or thread retrieval. It only moves the forum category list read to the established retry-aware AMC helper and makes exhausted retries explicit.
