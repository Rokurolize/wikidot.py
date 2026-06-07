# PR Draft: Validate Page Refresh Source Site

## Summary

`Page.refresh_source()` explicitly invalidates the cached source and forces a remote source fetch. Existing source-refresh and source-context work already covers normal refresh behavior, exhausted retry diagnostics, source assignment validation, and page construction-time site validation. One adjacent action-time state boundary still trusted `page.site` after construction: if a caller, fixture, or rehydrated page object replaced `page.site` with a mock, dictionary-like object, or other non-`Site` value, `refresh_source()` cleared `_source` before the downstream `PageCollection` site validation rejected the malformed parent.

This change revalidates `self.site` at the start of `Page.refresh_source()` before clearing `_source` and before constructing the fetch collection. Malformed action-time page sites now raise `ValueError("site must be a Site")` without destroying a usable cached source or reaching AMC request work. Valid forced refreshes, source lazy-acquisition behavior, exhausted retry context, and source assignment validation remain unchanged.

## Outcome

The direct page source refresh path now has an explicit action-time parent-site preflight consistent with the page constructor and adjacent page write/read action guards, while preserving cached source state when the parent site has been mutated into an invalid object.

## Current Evidence

Existing drafts [013-pr-refresh-cached-page-source.md](013-pr-refresh-cached-page-source.md), [149-pr-page-source-failure-context.md](149-pr-page-source-failure-context.md), [194-pr-page-source-site-context.md](194-pr-page-source-site-context.md), [414-pr-validate-page-source-assignments.md](414-pr-validate-page-source-assignments.md), [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), and [564-pr-validate-page-edit-site.md](564-pr-validate-page-edit-site.md) establish explicit source refresh behavior, direct source failure context, source-site context, source assignment validation, constructor site validation, and adjacent page action-time site validation. This slice covers mutated `Page.site` at `Page.refresh_source()` time, not normal source fetching, source parsing, source assignment, or page construction.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.site` at the start of `Page.refresh_source()`.
- Use the validated site when constructing `PageCollection` for the forced remote source fetch.
- Add a regression for a mutated non-`Site` `page.site` that asserts no AMC request work and no cached `_source` destruction.
- Preserve valid forced refresh behavior, lazy source acquisition, exhausted retry context, and source assignment validation.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.refresh_source()` must reject a mutated non-`Site` `page.site` with `ValueError("site must be a Site")` before clearing `_source`, constructing request work, or performing AMC requests. |
| R2 | A malformed action-time site must not destroy an existing cached `PageSource`. |
| R3 | Valid forced source refreshes, lazy `Page.source` acquisition, source retry context, and source assignment validation must remain stable. |
| R4 | Focused source tests, full page module tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A mutated non-`Site` parent fails before refresh request surfaces. | `TestPageProperties.test_refresh_source_rejects_malformed_site_before_clearing_cache` failed RED by raising `ValueError("site must be a Site")` only after cached `_source` had already been cleared, then passed GREEN with validation before cache invalidation. | Clearing `_source`, calling `amc_request(...)`, calling `amc_request_with_retry(...)`, accepting dictionaries/mocks as sites, or letting collection-level validation be the first guard rejects this local completion claim. | `Page.refresh_source()` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | A malformed parent site preserves a previously cached source. | The new regression stores a cached `PageSource`, mutates `page.site`, calls `refresh_source()`, and asserts `_source` still references the original cached object. | Replacing, clearing, or re-fetching cached `_source` before parent-site validation rejects this local completion claim. | Page source cache state | `tests/unit/test_page.py` |
| R3 | Existing source read and refresh behavior remains stable. | Focused GREEN included forced refresh, lazy source acquisition, retry-context, and source assignment tests; the full page module run and full unit suite stayed green. | Changing source fetch request shape, lazy acquisition, exhausted retry diagnostics, or source assignment validation rejects this local completion claim. | Page source behavior | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Existing repository quality gates remain green. | Focused source tests passed 10 tests, full page module tests passed 290 tests, full unit passed 2661 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live auth material or private state is needed to prove the behavior. | The regression uses a synthetic mutated site and mocked unit-level page state; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, or live account details. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `02d7867 fix(page): validate refresh source site`.

- RED action-time site validation: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_refresh_source_rejects_malformed_site_before_clearing_cache -q` failed before the fix because mutated `page.site` was rejected only after `_source` had already been cleared.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_refresh_source_rejects_malformed_site_before_clearing_cache tests/unit/test_page.py::TestPageProperties::test_refresh_source_forces_remote_source_fetch tests/unit/test_page.py::TestPageProperties::test_refresh_source_includes_site_page_context_when_retry_is_exhausted tests/unit/test_page.py::TestPageProperties::test_source_property_auto_acquire tests/unit/test_page.py::TestPageProperties::test_source_property_includes_site_page_context_when_retry_is_exhausted tests/unit/test_page.py::TestPageProperties::test_source_setter_rejects_invalid_sources -q` passed 10 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 290 tests.
- `uv run pytest tests/unit -q` passed 2661 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.refresh_source()` rejects a mutated malformed `page.site` with `ValueError("site must be a Site")` before clearing `_source`, constructing source-fetch work, or performing AMC requests.
- A cached `PageSource` survives malformed parent-site validation.
- Valid forced source refreshes, lazy source reads, exhausted retry context, and source assignment validation remain intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed invalid mutated parent state being rejected too late: cached `_source` had already been cleared before malformed-site validation surfaced.
- This slice only validates mutated `Page.site` before `Page.refresh_source()`. It does not change page construction, source parsing, source assignment, edit behavior, direct metadata/tag/parent APIs, response validation, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private-message content, and live Wikidot account details out of upstream discussion.
