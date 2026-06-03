# PR Draft: Retry Recent Changes Fetches

## Summary

`Site.get_recent_changes(...)` retrieves `changes/SiteChangesListModule` pages one at a time, but it used the plain `site.amc_request(...)` path. A transient AMC failure could therefore abort a read-only site inspection even though the `Site` object already exposes retry-aware AMC handling through `site.amc_request_with_retry(...)`.

The fix routes each recent-changes page request through `amc_request_with_retry(...)`, preserving existing parsing, pagination, limit handling, and return values. If retries are exhausted, the method raises `UnexpectedException` with the recent-changes page number instead of silently returning partial data.

## Related Issue

Drafted from the same retry and read-heavy inspection area as [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md), [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), and the large-corpus/source collection work in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md). No upstream issue filed yet.

## Changes

- Use `Site.amc_request_with_retry(...)` for `changes/SiteChangesListModule` requests in `Site.get_recent_changes(...)`.
- Preserve the existing one-page-at-a-time pagination loop.
- Preserve `limit <= 0` empty-result behavior.
- Preserve existing HTML parsing and `SiteChange` construction behavior.
- Raise `UnexpectedException("Cannot retrieve recent changes page: ...")` when retries are exhausted.
- Add a regression test proving a transient AMC failure is retried and the change entry is still parsed.

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

Local implementation commit: `dbdf8dd fix(site): retry recent changes fetches`

- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_retries_transient_amc_failures -q` failed before the fix because the plain AMC path tried to parse a transient exception object as a response and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges tests/unit/test_site.py::TestSiteAmcRequest -q` passed with 7 tests.
- [x] `uv run --extra test pytest tests/unit/test_site.py -q` passed with 47 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 557 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed the current complexity leads.

## Acceptance Criteria

- A transient AMC failure while fetching recent changes is retried through the existing `amc_request_with_retry(...)` path.
- Successful retry responses are parsed into the same `SiteChange` records as before.
- Pagination, `limit`, empty-response, and non-numeric pager behavior remain unchanged.
- Exhausted retries do not silently produce a partial recent-changes list.
- Existing `Site.amc_request(...)` delegation behavior remains unchanged.

## Upstream-Safe Motivation

Recent-changes retrieval is a read-only inspection workflow, so it should benefit from the same retry-aware AMC behavior as other read-heavy wikidot.py paths. This small change reduces brittle transient failures without changing the public API or result model.

## Local Evidence, Not For Upstream Paste

- Local work on large page/source collection and browser-free publishing repeatedly hardened read-heavy AMC paths with retry-aware calls before higher-level ergonomics.
- The complexity scan continues to flag `Site.get_recent_changes(...)` as an AMC-in-pagination-loop path, which makes transient failure handling important even though the method still deliberately fetches pages sequentially.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, or command transcripts into an upstream PR.

## Additional Notes

This slice does not batch recent-changes pages or change the semantics of `limit=None`. It only moves the existing page fetch to the established retry-aware AMC helper and makes exhausted retries explicit.
