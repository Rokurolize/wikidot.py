# PR Draft: Retry Member List Fetches

## Summary

`SiteMember.get(...)` retrieves `membership/MembersListModule` pages for all members, moderators, or admins, but it used the plain `site.amc_request(...)` path. A transient AMC failure on the first page or a later paginated page could abort member-list inspection even though the `Site` object already provides retry-aware AMC handling.

The fix routes both the first member-list request and any additional paginated member-list requests through `site.amc_request_with_retry(...)`. Existing parsing, group selection, pagination detection, and return values are preserved. If retries are exhausted for any page, the method raises `UnexpectedException` with the affected member-list page number instead of silently returning a partial list.

## Related Issue

Drafted from the same retry and read-heavy inspection area as [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), and the large-corpus/source collection work in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md). No upstream issue filed yet.

## Changes

- Use `site.amc_request_with_retry(...)` for the first `membership/MembersListModule` request in `SiteMember.get(...)`.
- Use `site.amc_request_with_retry(...)` for additional paginated member-list requests.
- Preserve the existing group values: all members, `admins`, and `moderators`.
- Preserve existing member parsing behavior.
- Raise `UnexpectedException("Cannot retrieve site members page: ...")` when retries are exhausted.
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

Local implementation commit: `51b4e1a fix(site_member): retry member list fetches`

- [x] `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_retries_transient_first_page_failures -q` failed before the fix because the plain AMC path tried to parse a transient exception object as a response and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberGet -q` passed with 9 tests.
- [x] `uv run --extra test pytest tests/unit/test_site_member.py -q` passed with 25 tests.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSiteMemberLookup tests/unit/test_site_member.py::TestSiteMemberGet -q` passed with 13 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 559 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed the current complexity leads.

## Acceptance Criteria

- A transient AMC failure while fetching the first member-list page is retried through `site.amc_request_with_retry(...)`.
- Additional paginated member-list pages also use `site.amc_request_with_retry(...)`.
- Successful retry responses are parsed into the same `SiteMember` records as before.
- `admins`, `moderators`, and default all-member group requests preserve their request body semantics.
- A permanently failed paginated page does not silently produce a partial member list.
- Existing permission-changing methods continue to use their existing action request behavior.

## Upstream-Safe Motivation

Membership inspection is a read-heavy Wikidot workflow and should have the same transient-failure tolerance as other library-tested read paths. This change keeps the public API unchanged while making member, moderator, and admin list retrieval less brittle.

## Local Evidence, Not For Upstream Paste

- Local work on source collection, recent-changes retrieval, and browser-free publishing repeatedly hardened read-heavy AMC paths with retry-aware calls.
- The complexity scan continues to flag `src/wikidot/module/site_member.py` member parsing and pagination as read-heavy paths where AMC failures can interrupt list collection.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, or command transcripts into an upstream PR.

## Additional Notes

This slice does not change group names, parsing rules, permission mutation methods, or member caching on `Site.members`, `Site.admins`, and `Site.moderators`. It only moves member-list reads to the established retry-aware AMC helper and makes exhausted retries explicit.
