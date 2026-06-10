# PR Draft: Validate ListPages Site Client

## Summary

`PageCollection.search_pages(...)` now validates the retained `site.client` before the first-page ListPages helper reads retry configuration from `site.client.amc_client.config`. A valid `Site` whose public `client` field was replaced after construction now fails with `ValueError("client must be a Client")` before retry-config access, first-page AMC request work, response parsing, or result construction.

The change is intentionally narrow: valid ListPages request construction, retry-count validation, first-page retry behavior, additional-page retry behavior, private-site status mapping, response-body diagnostics, parser output, site page accessors, RequestUtil behavior, and raw AMC behavior remain unchanged.

## Problem Statement

`PageCollection.search_pages(site, query)` validates that `site` is a `Site`, but `PageCollection._request_listpages_page(...)` immediately read `site.client.amc_client.config` before validating that the retained client was still a `Client`. If a caller, fixture, or rehydrated record replaced `site.client` after construction, the ListPages read path could leak a raw attribute error or inspect a malformed object before the established wikidot.py client diagnostic was raised.

This mattered because the first ListPages page is the gateway into browser-free page search, source collection, stale page fallback, publish verification, and generated page ledgers.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify ListPages and page/source collection as practical surfaces: [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [005-pr-bound-listpages-pagination-by-limit.md](005-pr-bound-listpages-pagination-by-limit.md), [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [183-pr-listpages-fetch-failure-context.md](183-pr-listpages-fetch-failure-context.md), [220-pr-listpages-response-body-context.md](220-pr-listpages-response-body-context.md), [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md), [396-pr-validate-listpages-retry-control.md](396-pr-validate-listpages-retry-control.md), [534-pr-validate-search-pages-arguments.md](534-pr-validate-search-pages-arguments.md), and [712-pr-validate-site-amc-request-state.md](712-pr-validate-site-amc-request-state.md).

This slice is not a duplicate of [396-pr-validate-listpages-retry-control.md](396-pr-validate-listpages-retry-control.md). Issue 396 validates malformed `retry_max_retries` values after the config object is reachable; this draft validates the retained client before reaching that config object.

This slice is not a duplicate of [534-pr-validate-search-pages-arguments.md](534-pr-validate-search-pages-arguments.md). Issue 534 validates that the public `site` argument is a `Site` and `query` is a `SearchPagesQuery` or `None`; this draft covers post-construction mutation of a valid `Site.client`.

This slice is not a duplicate of [712-pr-validate-site-amc-request-state.md](712-pr-validate-site-amc-request-state.md). Issue 712 validates retained `Site` request state inside `Site.amc_request(...)` and `Site.amc_request_with_retry(...)`; the first-page ListPages helper read `site.client.amc_client.config` before it could reach those wrappers.

This slice is not a duplicate of Issues 800, 801, 802, or 803. Those drafts validate retained clients in page save/action, forum action, and site-administration write paths. This draft covers the read-side first-page ListPages request helper.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Direct page search through `PageCollection.search_pages(...)`.
- `Site.pages.search(...)`, `Site.pages.iter_search(...)`, and `Site.pages.iter_sources(...)`.
- Stale page lookup fallback through ListPages before direct URL ID lookup.
- Browser-free publish source verification and generated page/source ledgers.
- Local tests, migration tools, and serialized fixtures that may rehydrate valid `Site` objects and later mutate public retained fields.

## Proposed Fix

- In `PageCollection._request_listpages_page(...)`, call `_validate_page_site_client(site)` before reading `amc_client.config`.
- Read `retry_max_retries` through the validated `Client`.
- Leave the existing `Site.amc_request(...)` call in place so Issue 712 continues to own retained routing state validation for non-empty AMC requests.
- Preserve the existing default retry count when the config object lacks `retry_max_retries`.
- Preserve existing retry-count, response-body, pagination, parser, and accessor behavior.

## Implementation Notes

Implemented locally in commit `4bd4cb8 fix(page): validate listpages site client`.

The code change is a single local preflight in `src/wikidot/module/page.py`:

```python
client = _validate_page_site_client(site)
config = client.amc_client.config
```

The regression uses a non-`Client` object whose `amc_client` property raises if read. Before the fix, `PageCollection.search_pages(...)` reached that property and failed with the sentinel assertion. After the fix, it raises `ValueError("client must be a Client")` and does not call the mocked `site.amc_request(...)`.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| `PageCollection.search_pages(...)` rejects a valid `Site` whose retained `client` was replaced by a non-`Client` before retry-config access. | `TestPageCollectionSearchPages.test_search_pages_rejects_mutated_site_client_before_config_read` failed RED by reading the malformed client's `amc_client`, then passed GREEN. | Reading `amc_client`, reaching `retry_max_retries` validation, calling `site.amc_request(...)`, or leaking raw attribute errors rejects this claim. |
| Existing ListPages search and retry behavior remains stable. | `TestPageCollectionSearchPages` passed 35 tests. | Regressing basic search, retry-aware first fetch, exhausted retry diagnostics, private-site mapping, pager filtering, offset preservation, limit behavior, or response-body diagnostics rejects this claim. |
| Adjacent page, search, site-accessor, RequestUtil, and raw AMC behavior remains stable. | Adjacent suites passed 1092 tests. | Regressing site page accessors, query validation, request utilities, raw AMC behavior, or adjacent page workflows rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3893 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `4bd4cb8 fix(page): validate listpages site client`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_rejects_mutated_site_client_before_config_read -q --tb=short` failed before the fix because `_request_listpages_page(...)` read `site.client.amc_client.config` and triggered `AssertionError("malformed site.client should not read amc_client")`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_rejects_mutated_site_client_before_config_read -q --tb=short` passed 1 test.
- Affected ListPages class: `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages -q --tb=short` passed 35 tests.
- Adjacent page/search/site/request suites: `uv run pytest tests/unit/test_page.py tests/unit/test_search_pages_query.py tests/unit/test_site.py::TestSitePagesAccessor tests/unit/test_site.py::TestSitePageAccessor tests/unit/test_requestutil.py tests/unit/test_amc_client.py -q --tb=short` passed 1092 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3893 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `PageCollection.search_pages(valid_site, SearchPagesQuery())` with `valid_site.client` replaced by a non-`Client` raises `ValueError("client must be a Client")`.
- The rejection happens before `site.client.amc_client`, `retry_max_retries`, first-page `site.amc_request(...)`, response-body parsing, pager parsing, or page result construction.
- Existing malformed `site` and `query` public argument diagnostics from Issue 534 remain unchanged.
- Existing malformed `retry_max_retries` diagnostics from Issue 396 remain unchanged for valid clients.
- Existing retained `Site.amc_request(...)` state validation from Issue 712 remains the owner of non-empty AMC routing state after first-page retry setup.
- Valid ListPages search, retry, pagination, private-site mapping, response-body diagnostics, parser output, and site page accessors remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: Earlier client validation could change precedence for calls that combine a valid `Site` object with a mutated retained client and malformed retry config. Mitigation: malformed retained clients are a more fundamental parent-state error; valid clients still reach the existing retry-count validator unchanged.
- Risk: This could be confused with public `search_pages(site=...)` argument validation. Mitigation: Issue 534 protects the public method boundary; this draft protects the retained client inside an otherwise valid `Site`.
- Risk: This could be confused with Site AMC retained-state validation. Mitigation: Issue 712 still owns non-empty AMC request routing state; this change only protects the config read that happens before `site.amc_request(...)`.
- Risk: The helper now validates the client twice for valid calls: once before config read and again inside `Site.amc_request(...)`. Mitigation: the duplicated identity check is cheap and keeps ownership boundaries explicit.

## Dependencies

- Existing `Client` class identity remains the parent-client contract.
- Existing `SearchPagesQuery` validation remains the query-shape contract.
- Existing `_validate_listpages_retry_max_retries(...)` remains the retry-count contract.
- Existing `Site.amc_request(...)` retained-state validation remains the AMC routing-state contract after retry setup.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, result ergonomics, cache ownership checks, cross-owner batch checks, or complexity candidates outside this now-covered first-page ListPages retained-client boundary.

## Rationale for Upstream Suitability

ListPages search is a central browser-free read path. The first-page helper should fail locally and deterministically when its retained parent client is corrupted, using the same client diagnostic already enforced at constructor, Site AMC, page action, forum action, and site-administration boundaries. The patch is small, preserves existing valid behavior, and prevents confusing attribute errors or malformed config reads before request work.

## Local Evidence

- Local browser-free maintenance drafts repeatedly use ListPages search, source iteration, stale lookup fallback, publish verification, and generated ledgers.
- Existing local drafts covered ListPages retry setup, query argument validation, response diagnostics, parser behavior, and Site AMC retained-state validation. They did not cover post-construction retained `Site.client` mutation before first-page ListPages retry-config access.
- This slice only validates retained client state before first-page ListPages config access. It does not change live Wikidot behavior, request payload shapes, retry policy, parser behavior, response diagnostics, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw page content, raw response bodies, private site data, and private source text out of upstream discussion.

