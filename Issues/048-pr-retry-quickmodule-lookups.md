# PR Draft: Retry QuickModule Lookups

## Summary

`QuickModule._request(...)` wraps Wikidot's read-only `quickmodule.php` helper endpoint for `MemberLookupQModule`, `UserLookupQModule`, and `PageLookupQModule`. These helpers back high-level lookup APIs such as `Site.member_lookup(...)`.

The request already used `sync_get_with_retry(...)`, but passed `attempt_limit=1`. As a result, a single transient `500 Internal Server Error` from `https://www.wikidot.com/quickmodule.php` was not retried. Because QuickModule uses a `500` response to report a missing site, the transient response was immediately converted into `ValueError("Site is not found")`.

The fix keeps the existing final-error behavior, but allows transient 5xx responses to retry before the site-not-found mapping is applied.

## Related Issue

Complements the retry-aware read-path drafts [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), and [045-pr-retry-page-discussion-fetch.md](045-pr-retry-page-discussion-fetch.md). It specifically covers the separate QuickModule helper endpoint rather than AMC module reads. No upstream issue filed yet.

## Changes

- Increase `QuickModule._request(...)`'s `sync_get_with_retry(...)` attempt limit from 1 to 3.
- Preserve `raise_for_status=False` so QuickModule can still map a final `500` response to `ValueError("Site is not found")`.
- Add regression coverage showing a transient `500` followed by `200` returns the successful QuickModule JSON.
- Patch retry sleep in the permanent site-not-found test so the test suite stays fast.
- Leave QuickModule query encoding, response JSON parsing, and public lookup method signatures unchanged.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [ ] Security/privacy hardening
- [x] Reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Requirements Traceability

| Requirement | Acceptance | Verification | Negative Control |
| --- | --- | --- | --- |
| R1: QuickModule transient 5xx responses retry | A first `500` followed by a `200` returns the successful JSON payload | `test_request_retries_transient_5xx` | The test failed before the fix with `ValueError("Site is not found")` after one request |
| R2: Permanent site-not-found behavior is preserved | A final `500` response still raises `ValueError("Site is not found")` | `test_request_site_not_found`; `tests/unit/test_quick_module.py` | `raise_for_status=False` remains unchanged so the QuickModule-specific mapping still owns this case |
| R3: Public lookup helpers remain stable | Member lookup, user lookup, page lookup, and `Site.member_lookup(...)` tests continue to pass | `tests/unit/test_quick_module.py tests/unit/test_site.py::TestSiteMemberLookup`; `tests/unit` | Broad unit coverage still passes after the attempt-limit change |
| R4: The change is read-path only | No AMC mutation or browser workflow is retried by this slice | Code review of `src/wikidot/util/quick_module.py` diff | Only the QuickModule GET helper attempt limit changed |

## Testing

Local implementation commit: `3e48d2c fix(quick_module): retry transient lookup failures`

- [x] `uv run --extra test pytest tests/unit/test_quick_module.py::TestQuickModuleRequest::test_request_retries_transient_5xx -q` failed before the fix with `ValueError("Site is not found")` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_quick_module.py -q` passed with 14 tests.
- [x] `uv run --extra test pytest tests/unit/test_quick_module.py tests/unit/test_site.py::TestSiteMemberLookup -q` passed with 18 tests.
- [x] `uv run --extra test pytest tests/unit/test_quick_module.py tests/unit/test_site.py::TestSiteMemberLookup tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed with 24 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 601 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] Complexity scan refreshed at `/home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/artifacts/complexity_analysis_wikidot.md`

## Acceptance Criteria

- `QuickModule._request(...)` retries transient 5xx responses from `quickmodule.php`.
- A transient `500` followed by a successful response returns the successful JSON payload.
- A final `500` response still raises `ValueError("Site is not found")`.
- Existing `member_lookup`, `user_lookup`, `page_lookup`, and `Site.member_lookup(...)` behavior remains unchanged on successful responses.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

QuickModule lookups are read-only helper requests but can still hit transient Wikidot server errors. Retrying a temporary 5xx before applying the endpoint's site-not-found mapping avoids reporting a reachable site as missing because of one failed response. The change is narrow: it only increases the retry budget on the existing QuickModule GET path and keeps the final `500` handling intact.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence repeatedly used `wikidot.py` for member, page, and user lookup support around browser-free Wikidot workflows.
- Prior local drafts established the same practical need for retry-aware read paths across recent changes, member lists, ListPages, page discussion, and other non-mutating fetch helpers.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice intentionally does not retry write or mutation actions. It only changes the read-only QuickModule GET helper, where retrying a transient server response does not duplicate a user-visible mutation.
