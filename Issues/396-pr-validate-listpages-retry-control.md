# PR Draft: Validate ListPages Retry Control

## Summary

`PageCollection._request_listpages_page(...)` fetches the first ListPages page directly through `site.amc_request(...)` and reads `client.amc_client.config.retry_max_retries` to decide how many transient `AMCHttpStatusCodeException` failures to retry. That first-page helper did not validate malformed config values before request work. Values such as `retry_max_retries=None`, `True`, `False`, `"1"`, or `1.5` could reach the AMC request/response path and produce later parser diagnostics instead of a stable wikidot.py-side validation error at the retry-control boundary.

This change validates `retry_max_retries` as a non-bool non-negative integer before the direct first-page ListPages AMC request is issued. Existing missing-attribute default behavior, valid zero retry counts, first-page transient retry behavior, exhausted retry diagnostics, private-site `not_ok` handling, ListPages pagination, page search iterators, page source iterators, Site AMC retry helper behavior, RequestUtil behavior, and raw AMC behavior remain unchanged.

## Outcome

First-page ListPages callers now get deterministic retry-control validation before direct AMC request execution instead of accidental bool coercion, parser work on mock or malformed responses, or diagnostics from a later layer.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page search, large ListPages collection, source collection, migration tools, generated audits, archival workflows, moderation tooling, or mocked test clients that may load retry settings from JSON, YAML, CLI flags, spreadsheets, generated structures, environment variables, or test fixtures.

## Current Evidence

Local rollout-backed drafts repeatedly identify ListPages and page/source collection as practical surfaces. [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [005-pr-bound-listpages-pagination-by-limit.md](005-pr-bound-listpages-pagination-by-limit.md), [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md), [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md), [183-pr-listpages-fetch-failure-context.md](183-pr-listpages-fetch-failure-context.md), [220-pr-listpages-response-body-context.md](220-pr-listpages-response-body-context.md), [239-pr-listpages-field-type-context.md](239-pr-listpages-field-type-context.md), [240-pr-listpages-response-body-type-context.md](240-pr-listpages-response-body-type-context.md), [305-pr-page-source-fetch-error-context.md](305-pr-page-source-fetch-error-context.md), [306-pr-page-source-result-context.md](306-pr-page-source-result-context.md), [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md), [344-pr-validate-search-pagination-types.md](344-pr-validate-search-pagination-types.md), [345-pr-validate-source-iterator-batch-sizes.md](345-pr-validate-source-iterator-batch-sizes.md), [382-pr-validate-page-collection-search-fullnames.md](382-pr-validate-page-collection-search-fullnames.md), and [385-pr-validate-page-lookup-not-found-flag.md](385-pr-validate-page-lookup-not-found-flag.md) show why page-search setup should fail deterministically before remote work when caller configuration is malformed.

Those prior slices are not duplicates. Issue 038 made the first ListPages fetch retry-aware, but did not validate malformed `retry_max_retries`. Issue 344 validates `SearchPagesQuery` pagination fields, not retry config read from `client.amc_client.config`. Issue 394 validates explicit and config retry controls in `Site.amc_request_with_retry(...)`; this slice covers the separate direct first-page ListPages helper, which calls `site.amc_request(...)` itself before pagination continues through the site-level retry helper.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [344-pr-validate-search-pagination-types.md](344-pr-validate-search-pagination-types.md), [345-pr-validate-source-iterator-batch-sizes.md](345-pr-validate-source-iterator-batch-sizes.md), [382-pr-validate-page-collection-search-fullnames.md](382-pr-validate-page-collection-search-fullnames.md), [394-pr-validate-site-amc-retry-controls.md](394-pr-validate-site-amc-retry-controls.md), and the broader ListPages/source collection drafts listed above.

## Changes

- Validate `retry_max_retries` in `PageCollection._request_listpages_page(...)` as a non-bool non-negative integer before the direct first-page AMC request.
- Preserve the existing default of `3` when the config object has no `retry_max_retries` attribute.
- Preserve valid zero retry counts and valid positive retry counts.
- Preserve first-page transient retry behavior and exhausted retry diagnostics.
- Preserve private-site `not_ok` handling, ListPages response parsing, search pagination, page source iterators, Site AMC retry helper behavior, RequestUtil behavior, and raw AMC behavior.

## Type Of Change

- Input validation
- ListPages request preflight hardening
- Retry-control boundary clarification
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageCollection.search_pages(...)` must reject malformed first-page ListPages `retry_max_retries` values with `ValueError("retry_max_retries must be a non-negative integer")` before issuing a direct AMC request. |
| R2 | Missing `retry_max_retries`, `retry_max_retries=0`, and positive integer retry counts must remain accepted. |
| R3 | Existing first-page transient retry behavior, exhausted retry diagnostics, private-site `not_ok` mapping, ListPages pagination, source/search iterators, Site AMC retry helper behavior, RequestUtil behavior, and raw AMC behavior must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, affected page tests, adjacent tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `retry_max_retries=None`, `True`, `False`, `"1"`, `-1`, and `1.5` fail before direct ListPages AMC request work. | `TestPageCollectionSearchPages.test_search_pages_rejects_invalid_retry_max_retries_before_request` passed GREEN for all six values and asserts `mock_site_no_http.amc_request.assert_not_called()`. | Issuing the direct AMC request, accepting booleans or strings, accepting negative counts, accepting floats, or raising an unrelated parser error rejects this local completion claim. | First-page ListPages request helper | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Valid default and valid integer retry controls remain stable. | Existing first-page ListPages tests passed in `tests/unit/test_page.py`, including retry-aware first fetch, exhausted retry, and adjacent private-site cases. | Regressing missing-attribute default behavior, valid zero retry behavior, valid positive retry behavior, or existing first-page retry behavior rejects this local completion claim. | ListPages retry setup | `tests/unit/test_page.py` |
| R3 | Valid adjacent behavior remains stable. | `tests/unit/test_page.py` passed 210 tests; adjacent Site pages accessor, RequestUtil, and AMC tests passed 170 tests; full unit passed 1379 tests. | Regressing private-site handling, ListPages pagination, search/source iterators, Site AMC retry controls, direct URL RequestUtil, or raw AMC behavior rejects this local completion claim. | Page and request workflows | affected unit suites |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic config values, mocks, and local assertions. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, affected tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `47ddfa3 fix(page): validate listpages retry control`.

- RED tracer: `timeout 8s .venv/bin/python -m pytest -q tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_rejects_invalid_retry_max_retries_before_request` failed 5 tests before the fix for `None`, `True`, `False`, `"1"`, and `1.5`; each reached ListPages response processing and raised `NoElementException` from the `MagicMock` response body instead of preflight `ValueError`, proving malformed retry config reached request/response work.
- GREEN tracer: `.venv/bin/python -m pytest -q tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_rejects_invalid_retry_max_retries_before_request` passed 6 tests after adding preflight, including the added `-1` regression case.
- `.venv/bin/python -m pytest -q tests/unit/test_page.py::TestPageCollectionSearchPages` passed 25 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_page.py` passed 210 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSitePagesAccessor tests/unit/test_requestutil.py tests/unit/test_amc_client.py` passed 170 tests.
- `.venv/bin/python -m ruff check src/wikidot/module/page.py tests/unit/test_page.py` passed.
- `.venv/bin/python -m ruff format --check src/wikidot/module/page.py tests/unit/test_page.py` passed with 2 files already formatted.
- `.venv/bin/python -m mypy src/wikidot/module/page.py tests/unit/test_page.py` passed with no issues in 2 source files.
- `.venv/bin/python -m pytest -q tests/unit` passed 1379 tests.
- `.venv/bin/python -m ruff check .` passed.
- `.venv/bin/python -m ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/python -m mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed before the code commit.

Not run successfully: `pyright src tests` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `PageCollection.search_pages(site, SearchPagesQuery())` rejects `client.amc_client.config.retry_max_retries=None`, `True`, `False`, `"1"`, `-1`, and `1.5` with `ValueError("retry_max_retries must be a non-negative integer")` before issuing the first direct ListPages AMC request.
- A missing `retry_max_retries` attribute still uses the existing default retry count.
- Valid `retry_max_retries=0` and positive integer retry counts remain accepted.
- Existing first-page transient retry behavior, exhausted retry diagnostics, private-site `not_ok` mapping, ListPages pagination, source/search iterators, Site AMC retry helper behavior, RequestUtil behavior, and raw AMC behavior remains green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting booleans tightens behavior for callers that accidentally relied on Python's `bool` subclassing `int`. Mitigation: `True` and `False` are configuration mistakes for a retry count and should not become one retry or zero retries.
- Risk: Rejecting strings can expose CLI, environment, JSON, YAML, spreadsheet, or generated-structure parsing bugs. Mitigation: textual configuration should parse retry controls into real non-negative integers before calling page search.
- Risk: Rejecting floats tightens behavior for callers that accidentally used decimal config values. Mitigation: retry counts are discrete attempts; fractional retries cannot be executed meaningfully.
- Risk: This change could be confused with Issue 038. Mitigation: Issue 038 made the first ListPages fetch retry-aware; this slice validates the retry count that controls that helper.
- Risk: This change could be confused with Issue 344. Mitigation: Issue 344 validated search pagination parameters on `SearchPagesQuery`; this slice validates retry config on the client config object.
- Risk: This change could be confused with Issue 394. Mitigation: Issue 394 validates `Site.amc_request_with_retry(...)`; the first ListPages page uses the separate direct helper `PageCollection._request_listpages_page(...)`.

## Dependencies

- Existing `PageCollection._request_listpages_page(...)` remains the source of truth for first-page ListPages request and retry behavior.
- Existing `Site.amc_request_with_retry(...)` remains the source of truth for site-level AMC batch retry behavior after the first page and for other site helper callers.
- Existing `SearchPagesQuery` validation remains the source of truth for search pagination fields.
- The validation is local to `src/wikidot/module/page.py` and does not affect URL construction, response parsing, raw AMC request execution, direct URL RequestUtil execution, site-level AMC retry helper behavior, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-body field-type checks, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered first-page ListPages retry-control path.

## Upstream-Safe Motivation

The first ListPages page is a practical gateway into browser-free page search and source collection. Since retry settings determine whether request work starts, repeats, or fails, malformed `None`, strings, booleans, negative counts, and floats should fail deterministically before direct AMC request setup.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established ListPages and page/source collection as practical surfaces through large corpus collection, bounded ListPages pagination, retry-aware first and subsequent page fetching, page search iterators, source iterators, required-tag filtering, parser diagnostics, response-body diagnostics, and adjacent input validation.
- Existing drafts covered first-page retry awareness, search pagination validation, source iterator batch-size validation, page collection fullname validation, and site-level AMC retry-control validation; they did not validate first-page ListPages `retry_max_retries` before direct AMC request work.
- This slice only validates first-page ListPages retry count config. It does not change retry policy, status classification, response parsing, source collection, RequestUtil behavior, raw AMC request behavior, site-level AMC retry behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or user names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed retry controls instead of coercing them. Callers that load retry values from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should resolve them into real non-negative integers before calling page search.
