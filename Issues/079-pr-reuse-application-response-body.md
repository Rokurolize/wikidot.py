# PR Draft: Reuse Site Application Response Body

## Summary

`SiteApplication.acquire_all(...)`, exposed through `site.applications`, already stores the pending-application module response body so it can detect forbidden access before parsing. The implementation then called `response.json()` a second time to pass the same body into BeautifulSoup.

This fix reuses the already extracted response body for HTML parsing. Login checks, retry-aware AMC fetching, forbidden detection, empty-list handling, application text parsing, user parsing, accept/decline behavior, and error semantics remain unchanged.

## Related Issue

Builds directly on [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), which moved pending-application list reads onto retry-aware AMC handling. It is also adjacent to [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), which covered the same site-application workflow from the mutation side.

No upstream issue was filed from this local workspace.

## Changes

- Parse the successful `managesite/ManageSiteMembersApplicationsModule` response JSON once in `SiteApplication.acquire_all(...)`.
- Reuse the extracted `body` string for the forbidden-page check and the BeautifulSoup parse.
- Strengthen the successful application-list test to assert one response JSON decode.
- Preserve login enforcement, retry exhaustion handling, forbidden detection, empty application lists, unrelated table handling, missing text-cell errors, application length mismatch checks, and application processing methods.

## Type Of Change

- Performance improvement
- Refactoring
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A successful pending-application list response should be decoded once. | `TestSiteApplicationAcquireAll.test_acquire_all_success` asserts `response.json.call_count == 1`. | The RED test failed before the fix with `assert 2 == 1`. |
| The public application list result stays unchanged. | The focused test still asserts one `SiteApplication` with the parsed mock user and application text. | Returning no applications, skipping user parsing, or losing the application text would fail the existing assertions. |
| Adjacent site application behavior stays green. | `uv run pytest tests/unit/test_site_application.py` passed 17 tests. | Regressions in retry, forbidden, empty, malformed, accept, or decline behavior reject the local completion claim. |
| Adjacent site/member workflows stay green. | `uv run pytest tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_site_member.py` passed 97 tests. | Site accessor, recent-changes, member-list, or application workflow regressions reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `ab87c97 perf(site_application): reuse application response body`.

- RED: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_success` failed before the fix with `assert 2 == 1`.
- GREEN: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_success`
- `uv run pytest tests/unit/test_site_application.py` passed 17 tests.
- `uv run pytest tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_site_member.py` passed 97 tests.
- `uv run pytest tests/unit` passed 630 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- `SiteApplication.acquire_all(...)` still uses retry-aware AMC to fetch pending applications.
- A successful response's JSON body is decoded once.
- The forbidden-page marker is still detected before parsing applications.
- Empty application lists still return an empty list.
- Valid application entries still produce `SiteApplication` objects with parsed users and stripped text.
- Unrelated tables are still ignored.
- Missing application text tables/cells and duplicate text-table mismatches still raise the existing exceptions.
- Exhausted retry results still raise `UnexpectedException("Cannot retrieve site applications")`.
- Login-required behavior for listing and processing applications remains unchanged.
- Accept and decline request bodies remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Pending site application review is a read-heavy management workflow. Once the application-list response body is available, decoding the same response JSON twice does not add information. Reusing the body removes avoidable response work while preserving the public `site.applications` behavior and existing permission checks.

## Local Evidence, Not For Upstream Paste

- [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md) established retry-aware fetching for pending applications.
- The focused RED test demonstrated the remaining avoidable work: a successful pending-application list response was decoded twice.
- Keep local rollout paths, account names, and corpus-specific identifiers out of any upstream discussion.

## Additional Notes

This slice does not change site application request construction, login checks, permission rules, application parsing structure, membership accept/decline mutation behavior, or retry policy. It only reuses the successful response body string already read inside `SiteApplication.acquire_all(...)`.
