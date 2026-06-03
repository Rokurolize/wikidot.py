# PR Draft: Retry Application List Fetches

## Summary

`SiteApplication.acquire_all(...)`, exposed through `site.applications`, retrieves pending site join applications with `managesite/ManageSiteMembersApplicationsModule`, but it used the plain `site.amc_request(...)` path. A transient AMC failure could abort pending-application inspection even though the `Site` object already provides retry-aware AMC handling for read-heavy collection paths.

The fix routes the pending-application list fetch through `site.amc_request_with_retry(...)`. Existing login checks, permission detection, parsing, and accept/decline behavior are preserved. If retries are exhausted, the method raises `UnexpectedException("Cannot retrieve site applications")` instead of trying to parse a missing response.

## Related Issue

Drafted from the same retry and read-heavy inspection area as [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), and the large-corpus/source collection work in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md). No upstream issue filed yet.

## Changes

- Use `site.amc_request_with_retry(...)` for the pending site-application list request.
- Preserve the public `site.applications` property and `SiteApplication.acquire_all(...)` return type.
- Preserve existing forbidden-page detection and application parsing behavior.
- Preserve existing accept/decline mutation requests on the plain action path.
- Raise `UnexpectedException("Cannot retrieve site applications")` when retries are exhausted.
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

Local implementation commit: `babb553 fix(site_application): retry application list fetches`

- [x] `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_site_applications_retries_transient_fetch_failures -q` failed before the fix because the plain AMC path tried to parse a transient exception object as a response and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site_application.py -q` passed with 17 tests.
- [x] `uv run --extra test pytest tests/unit/test_site_application.py tests/unit/test_site.py::TestSiteMemberLookup -q` passed with 21 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 561 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed the current complexity leads.

## Acceptance Criteria

- A transient AMC failure while fetching pending applications is retried through `site.amc_request_with_retry(...)`.
- Successful retry responses are parsed into the same `SiteApplication` records as before.
- Existing forbidden-page detection still raises `ForbiddenException`.
- Existing malformed application table handling still raises the same parsing exceptions.
- Exhausted retries raise `UnexpectedException` instead of becoming an attribute/parsing failure.
- Existing `accept()` and `decline()` application mutation behavior is unchanged.

## Upstream-Safe Motivation

Pending join-application inspection is an administrative read path, similar to member, moderator, admin, and recent-changes inspection. It should have the same transient-failure tolerance as other retry-aware Wikidot read paths while keeping the public API unchanged.

## Local Evidence, Not For Upstream Paste

- Local work on source collection, member inspection, recent-changes retrieval, and browser-free publishing repeatedly hardened read-heavy AMC paths with retry-aware calls.
- The complexity scan continues to flag `src/wikidot/module/site_application.py` as an inspection path where AMC failure interrupts list collection.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, or command transcripts into an upstream PR.

## Additional Notes

This slice does not change application parsing rules, login checks, permission checks, `SiteApplication.accept()`, or `SiteApplication.decline()`. It only moves the pending-application list read to the established retry-aware AMC helper and makes exhausted retries explicit. Follow-up [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md) fixes the decline notification text without changing the mutation action path.
