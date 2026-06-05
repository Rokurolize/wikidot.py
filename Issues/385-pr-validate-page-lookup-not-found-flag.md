# PR Draft: Validate Page Lookup Not-Found Flags

## Summary

`Site.page.get(fullname, raise_when_not_found=...)` documents `raise_when_not_found` as a boolean, but malformed caller-provided values were accepted at the public page lookup boundary. Truthy strings such as `"false"` could turn a lookup that should return `None` into a raising lookup, while integers such as `0` and `1` could silently act as booleans.

This change validates `raise_when_not_found` before ListPages search, direct page-ID fallback probing, or not-found branching. Malformed values now raise `ValueError("raise_when_not_found must be a boolean")`. Existing valid `False` return-`None` behavior and valid `True` not-found raising behavior remain unchanged.

## Outcome

Browser-free page lookup callers now get deterministic Python-side preflight validation for malformed not-found controls instead of surprising not-found behavior, accidental ListPages/direct page-ID work, or configuration strings being treated as truthy booleans.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `Site.page.get(...)` for page existence checks, stale-ListPages reconciliation, browser-free publishing, source collection, migration tooling, archival indexing, moderation workflows, audit ledgers, or generated page inventories.

## Current Evidence

Local rollout-backed drafts repeatedly identify page lookup as a practical browser-free surface. Existing drafts [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [190-pr-site-page-get-direct-id-error-surface.md](190-pr-site-page-get-direct-id-error-surface.md), and [203-pr-site-page-get-miss-site-context.md](203-pr-site-page-get-miss-site-context.md) cover ListPages lookup, stale-ListPages direct page-ID fallback, direct-probe error classification, and site-aware page miss diagnostics. Page discovery and search drafts such as [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [183-pr-listpages-fetch-failure-context.md](183-pr-listpages-fetch-failure-context.md), [220-pr-listpages-response-body-context.md](220-pr-listpages-response-body-context.md), [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md), and [382-pr-validate-page-collection-find-fullname.md](382-pr-validate-page-collection-find-fullname.md) establish ListPages-backed page lookup and loaded page search as operationally important read paths.

Those prior slices are not duplicates. They covered lookup fallback behavior, direct page-ID diagnostics, ListPages response diagnostics, page collection search-key validation, and page write/publish preflight. They did not validate the boolean `raise_when_not_found` control before ListPages search, direct page-ID fallback, or final not-found branching. This slice follows the boolean-control preflight pattern from [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md) and the lookup-control pattern from [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md), but applies it to page lookup rather than page writes or user profile lookup.

## Related Issue

Builds directly on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [190-pr-site-page-get-direct-id-error-surface.md](190-pr-site-page-get-direct-id-error-surface.md), [203-pr-site-page-get-miss-site-context.md](203-pr-site-page-get-miss-site-context.md), [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), [382-pr-validate-page-collection-find-fullname.md](382-pr-validate-page-collection-find-fullname.md), and [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `raise_when_not_found` in `Site.page.get(...)` before ListPages search.
- Reject malformed not-found controls before direct page-ID fallback probing.
- Preserve valid `raise_when_not_found=False` behavior for ordinary missing pages.
- Preserve valid default/`True` behavior for not-found exceptions.
- Preserve successful ListPages hits, stale-ListPages direct page-ID recovery, direct `404` handling, structural direct-probe error propagation, page creation/publish callers, and adjacent page workflows.

## Type Of Change

- Input validation
- Public API behavior hardening
- Page lookup control preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.page.get(..., raise_when_not_found=...)` must reject `None`, strings, integers, and other non-bool values with `ValueError("raise_when_not_found must be a boolean")` before ListPages search or direct page-ID fallback probing. |
| R2 | Valid `raise_when_not_found=False` behavior must remain unchanged: ordinary missing page lookup returns `None`. |
| R3 | Valid default/`raise_when_not_found=True` behavior must remain unchanged: ordinary missing page lookup raises `NotFoundException` with site and page context. |
| R4 | Successful ListPages hits, stale-ListPages direct page-ID recovery, direct `404` miss handling, and structural direct-probe error propagation must remain unchanged. |
| R5 | Adjacent page create, publish, source, revision, file, vote, and page collection behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, SitePageAccessor tests, adjacent site/page tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed page lookup not-found controls fail before ListPages search or direct fallback probing. | `TestSitePageAccessor.test_get_rejects_non_bool_raise_when_not_found_before_lookup` failed RED for `None`, `"false"`, `0`, and `1` because malformed controls reached page lookup/not-found behavior, then passed GREEN after validation was added. | Treating `"false"` as truthy, accepting `0`/`1` as booleans, calling `PageCollection.search_pages(...)`, calling `_get_by_direct_page_id(...)`, returning `None`, or raising not-found based on malformed controls rejects this local completion claim. | Page lookup preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Valid false controls still return `None` for ordinary misses. | Existing `test_get_returns_none_when_direct_page_id_probe_is_404` passed after validation was added. | Raising for valid `False`, fabricating a page, or changing direct `404` miss handling rejects this local completion claim. | Page lookup not-found behavior | `tests/unit/test_site.py` |
| R3 | Valid true/default controls still raise contextual not-found exceptions for ordinary misses. | Existing `test_get_not_found_raises_with_site_context` passed after validation was added. | Returning `None`, changing exception type, or losing site/page context rejects this local completion claim. | Page lookup not-found behavior | `tests/unit/test_site.py` |
| R4 | Existing direct fallback behavior stays intact. | Existing `test_get_success`, `test_get_falls_back_to_direct_page_id_when_listpages_is_stale`, and `test_get_surfaces_unexpected_direct_page_id_probe_errors` passed in the SitePageAccessor suite. | Regressing ListPages hits, stale-ListPages direct page-ID recovery, direct `404` classification, or structural direct-probe error propagation rejects this local completion claim. | Page lookup fallback | `tests/unit/test_site.py` |
| R5 | Adjacent site/page behavior remains green. | `tests/unit/test_site.py::TestSitePageAccessor` passed 36 tests, `tests/unit/test_site.py tests/unit/test_page.py` passed 325 tests, and full unit tests passed 1118 tests. | Regressing publish, create/edit, source iteration, ListPages parsing, page files, page revisions, page votes, or page collection behavior rejects this local completion claim. | Site/page workflow | affected site and page tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic local values and mocks. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text from real sites, private page content, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, SitePageAccessor tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `98e1808 fix(site): validate page lookup not-found flag`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_site.py -k 'raise_when_not_found and non_bool'` failed 4 selected tests before the fix because malformed controls reached page lookup/not-found behavior.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_site.py -k 'raise_when_not_found and non_bool'` passed 4 tests after adding boolean preflight.
- `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSitePageAccessor` passed 36 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_site.py tests/unit/test_page.py` passed 325 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1118 tests.
- `.venv/bin/ruff format src/wikidot/module/site.py tests/unit/test_site.py` left 2 files unchanged.
- `.venv/bin/ruff check src/wikidot/module/site.py tests/unit/test_site.py` passed.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `site.page.get("missing", raise_when_not_found=None)`, `raise_when_not_found="false"`, `raise_when_not_found=0`, and `raise_when_not_found=1` raise `ValueError("raise_when_not_found must be a boolean")` before ListPages search or direct page-ID fallback probing.
- `site.page.get("missing", raise_when_not_found=False)` still returns `None` for ordinary missing pages.
- `site.page.get("missing")` and `site.page.get("missing", raise_when_not_found=True)` still raise `NotFoundException` naming the site and requested page.
- `site.page.get("new-page")` still recovers pages that are missing from ListPages but visible through direct page-ID fallback.
- Structural direct page-ID probe errors still propagate instead of being hidden as ordinary page absence.
- Existing page lookup, page create/publish, ListPages, source, file, revision, vote, and page collection behavior remains unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private page data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `0` or `1` tightens behavior for callers that previously used integers as booleans. Mitigation: the documented API type is `bool`; accepting integer controls can hide config parsing mistakes and accidentally change not-found behavior.
- Risk: Rejecting string values can expose CLI, environment, JSON, YAML, or spreadsheet parsing bugs. Mitigation: text configuration should parse `"true"`/`"false"` into real booleans before calling wikidot.py.
- Risk: The change could be confused with page fullname validation. Mitigation: page fullname/search validation remains unchanged; this slice only validates the not-found control flag.
- Risk: The change could be confused with page write boolean validation. Mitigation: page create/edit/publish bool controls were already covered separately; this slice only applies to read-only `Site.page.get(...)`.

## Dependencies

- Existing `PageCollection.get_by_fullname(...)` remains the source of truth for ListPages-backed page lookup.
- Existing direct page-ID fallback probing remains the source of truth for stale-ListPages recovery.
- Existing `NotFoundException` and `UnexpectedException` behavior for valid controls remains unchanged.
- Existing page write boolean validation helper supplies the same strict `bool` contract and message shape.
- The validation is local to `src/wikidot/module/site.py` and does not affect user lookup, QuickModule lookup, page collection search, page writes, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered page lookup not-found flag validation path.

## Upstream-Safe Motivation

Page lookup helpers are often called from migration ledgers, archival crawlers, browser-free publishing scripts, generated page inventories, and moderation workflows. Since `raise_when_not_found` controls whether a missing page is a returned `None` or a raised exception, malformed truthy strings and integer stand-ins should fail deterministically before request work rather than changing not-found behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established page lookup as a practical workflow through stale-ListPages direct fallback, page-ID diagnostics, site-aware miss diagnostics, browser-free publishing, source collection, ListPages parsing, and page collection search validation.
- Existing page lookup and ListPages drafts covered fallback behavior, response diagnostics, parser diagnostics, source/page ledgers, collection lookup keys, and write/publish preflight; they did not validate the caller-provided `raise_when_not_found` control.
- This slice only validates `raise_when_not_found` inputs for `Site.page.get(...)`. It does not change fullname normalization, ListPages query construction, direct page URL construction, missing-page classification for valid controls, page-ID parsing, page collection search, page writes, publish behavior, source iteration, page file/revision/vote behavior, user lookup, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private page content, private site data, and page source text from real sites out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed not-found controls instead of coercing them. Callers that load this flag from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should resolve it into a real boolean before calling `Site.page.get(...)`.
