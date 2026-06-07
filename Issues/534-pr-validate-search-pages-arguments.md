# PR Draft: Validate PageCollection.search_pages Arguments

## Summary

`PageCollection.search_pages(site, query)` is the public ListPages entry point behind direct page search, site page lookup, source iteration, browser-free publish verification, and many generated page ledgers. Existing local slices validated `SearchPagesQuery` fields, `PageCollection` constructor state, page collection parent sites, and ListPages response boundaries, but the public `search_pages(...)` method still trusted its own `site` and `query` arguments. Malformed `site` values reached `site.client` lookup, and malformed `query` values reached `query.limit` before any stable wikidot.py diagnostic.

This change validates `site` with the existing page collection site validator and rejects non-`SearchPagesQuery` query objects with `ValueError("query must be a SearchPagesQuery or None")`. Valid `query=None`, valid `SearchPagesQuery`, no-request `limit <= 0`, ListPages request construction, retry behavior, pagination, response diagnostics, parser output, site accessors, and source iterators remain unchanged.

## Outcome

Callers now get deterministic preflight errors at the `PageCollection.search_pages(...)` boundary instead of raw attribute errors from malformed site or query objects.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use direct page searches, `Site.pages.search(...)`, `Site.pages.iter_search(...)`, `Site.pages.iter_sources(...)`, stale page lookup fallback, source collection, browser-free publish verification, generated page inventories, or local fixtures that may pass deserialized or mocked objects into ListPages search.

## Current Evidence

Local rollout-backed drafts establish ListPages search as a high-use read path: broad page/source collection, bounded search iteration, required-tag filtering, stale page lookup fallback, publish source verification, retry-aware first and additional ListPages requests, response-body diagnostics, pagination validation, tag/query validation, and page collection state validation all build on `PageCollection.search_pages(...)`. Relevant prior drafts include [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [183-pr-listpages-fetch-failure-context.md](183-pr-listpages-fetch-failure-context.md), [220-pr-listpages-response-body-context.md](220-pr-listpages-response-body-context.md), [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md), [344-pr-validate-search-pagination-types.md](344-pr-validate-search-pagination-types.md), [409-pr-reject-boolean-search-pagination-values.md](409-pr-reject-boolean-search-pagination-values.md), [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md), [529-pr-validate-search-query-string-fields.md](529-pr-validate-search-query-string-fields.md), [530-pr-validate-tag-container-inputs.md](530-pr-validate-tag-container-inputs.md), and [533-pr-validate-page-fullname-inputs.md](533-pr-validate-page-fullname-inputs.md).

Those prior slices are not duplicates. Issues 344, 409, 529, and 530 validate fields inside a real `SearchPagesQuery`, not whether the public `search_pages(query=...)` argument is a query object. Issue 477 validates `PageCollection(site=...)` constructor state after search parsing or manual collection construction, not the `site` argument before `search_pages(...)` request work. Issues 018, 019, 049, and 068 use `search_pages(...)` through higher-level site accessors but do not harden the direct static method boundary. No upstream issue was filed from this local workspace.

## Changes

- Validate `PageCollection.search_pages(site=...)` before query serialization, retry configuration lookup, AMC requests, response parsing, or result construction.
- Preserve `query=None` as the default `SearchPagesQuery()` path.
- Reject non-`SearchPagesQuery` query objects with `ValueError("query must be a SearchPagesQuery or None")` before `query.limit`, `query.as_dict()`, or request work.
- Preserve existing valid ListPages search, pagination, retry, response diagnostics, and page parsing behavior.

## Type Of Change

- Input validation
- Public ListPages search preflight hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageCollection.search_pages(site=...)` must reject non-`Site` values with `ValueError("site must be a Site")` before ListPages request work. |
| R2 | `PageCollection.search_pages(query=...)` must accept `None` and `SearchPagesQuery`, but reject other values with `ValueError("query must be a SearchPagesQuery or None")` before request work. |
| R3 | Valid page search behavior, `query=None`, no-request `limit=0`, pagination, first-page retry, additional-page retry, private-site mapping, response-body diagnostics, and parser output must remain unchanged. |
| R4 | Higher-level `Site.pages` and `Site.page` accessors that delegate into `PageCollection.search_pages(...)` must remain green. |
| R5 | This slice must not change `SearchPagesQuery` field semantics, tag serialization, pagination contracts, site constructor validation, page collection constructor semantics, ListPages request body shape, parser behavior, live Wikidot behavior, or upstream Issue/PR state. |
| R6 | Focused RED/GREEN, adjacent page/search/site tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed `site` arguments fail before `site.client` or AMC request access. | `test_search_pages_rejects_malformed_site_before_request` failed RED for `None`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` with raw `AttributeError`, then passed GREEN with `ValueError("site must be a Site")`. | Reaching `site.client`, issuing AMC requests, accepting mocks/dicts/strings as sites, or returning an empty collection rejects this local completion claim. | Direct ListPages search boundary | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Malformed `query` arguments fail before `query.limit` or request construction. | `test_search_pages_rejects_malformed_query_before_request` failed RED for `True`, `{"limit": 1}`, and `object()` with raw `AttributeError`, then passed GREEN and asserted `amc_request` was not called. | Reaching `query.limit`, calling `as_dict`, issuing AMC requests, duck-typing dictionaries, coercing values, or accepting booleans rejects this local completion claim. | Direct ListPages query boundary | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Existing direct ListPages behavior remains stable. | `TestPageCollectionSearchPages` plus `TestPageCollectionInit` passed 55 tests; `tests/unit/test_page.py tests/unit/test_search_pages_query.py tests/unit/test_site.py` passed 601 tests. | Regressing basic search, field spacing, retry, private-site mapping, pager filtering, offset preservation, additional-page handling, missing/malformed body diagnostics, limit capping, or zero-limit behavior rejects this local completion claim. | Page search workflows | `tests/unit/test_page.py`, `tests/unit/test_search_pages_query.py`, `tests/unit/test_site.py` |
| R4 | Higher-level page accessors remain compatible. | `TestSearchPagesQuery`, `test_search_pages_query.py`, `TestSitePagesAccessor`, and `TestSitePageAccessor` passed 177 tests. | Regressing site page search, bounded iterators, required-tag filtering, source iterators, direct page lookup fallback, create/publish preflight, or publish result behavior rejects this local completion claim. | Site page accessors | `tests/unit/test_site.py`, `tests/unit/test_search_pages_query.py` |
| R5 | The implementation stays scoped to argument object preflight. | The code adds one existing site validator call and one query `isinstance` guard at the start of `search_pages(...)`; no query-field, request-body, parser, or live behavior changes were made. | Changing query syntax, accepting dict aliases, altering tag handling, changing pagination, changing response parsing, or changing live Wikidot behavior rejects this local completion claim. | Code scope | `src/wikidot/module/page.py` |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, focused 55 passed, adjacent 177 passed, page/search/site 601 passed, full unit 2552 passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No private material or live action is needed to prove the behavior. | All regressions use synthetic malformed values and local mocks; the draft contains no raw credentials, cookies, auth JSON, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `a1794ab fix(page): validate search pages arguments`.

- RED focused argument tests: `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_rejects_malformed_site_before_request tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_rejects_malformed_query_before_request -q` failed 8 cases before the fix. Malformed sites reached `site.client`, and malformed queries reached `query.limit`.
- GREEN focused argument tests: the same command passed 8 tests after adding preflight validation.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages tests/unit/test_page.py::TestPageCollectionInit -q` passed 55 tests.
- `uv run pytest tests/unit/test_page.py::TestSearchPagesQuery tests/unit/test_search_pages_query.py tests/unit/test_site.py::TestSitePagesAccessor tests/unit/test_site.py::TestSitePageAccessor -q` passed 177 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_search_pages_query.py tests/unit/test_site.py -q` passed 601 tests.
- `uv run pytest tests/unit -q` passed 2552 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageCollection.search_pages(None, SearchPagesQuery())`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` raise `ValueError("site must be a Site")` before request work.
- `PageCollection.search_pages(valid_site, True)`, `{"limit": 1}`, and `object()` raise `ValueError("query must be a SearchPagesQuery or None")` before `amc_request`.
- `PageCollection.search_pages(valid_site, None)` still uses default search parameters.
- `PageCollection.search_pages(valid_site, SearchPagesQuery(limit=0))` still returns an empty `PageCollection` without request work.
- Existing ListPages request construction, first-page retry, additional-page retry, private-site mapping, response-body diagnostics, pager filtering, offset preservation, limit capping, parsing, source iteration, and site page accessor behavior remain green.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with `SearchPagesQuery` validation. Mitigation: this slice validates the public `query` object itself; existing query slices validate fields inside a real query.
- Risk: This could be confused with `PageCollection(site=...)` constructor validation. Mitigation: that validation protects stored result collection state; this slice protects the search method before request planning.
- Risk: Accepting dictionary query aliases might appear convenient. Mitigation: `Site.pages.search(**kwargs)` is already the keyword/dict expansion path; direct `PageCollection.search_pages(...)` documents a `SearchPagesQuery | None`.

## Out Of Scope

Changing `SearchPagesQuery` fields, accepting dictionary query aliases, changing tag syntax, changing pagination semantics, changing ListPages request payload shape, changing response parsing, changing `PageCollection` constructor behavior, changing site constructor behavior, changing live Wikidot behavior, and upstream Issue/PR creation are outside this slice.

## Why This Matters

`PageCollection.search_pages(...)` is both a direct public API and the lower-level ListPages workhorse used by site page helpers. Stable method-level preflight keeps generated configs, mocks, JSON/YAML payloads, and local ledgers from leaking raw Python attribute errors or entering network-oriented request planning with malformed boundary objects.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used ListPages search, source iteration, stale page lookup fallback, publish source verification, and generated page/source ledgers as practical workflows.
- Existing local drafts covered search pagination, tag containers, scalar query fields, page collection constructor state, page collection parent sites, and ListPages response diagnostics, but did not validate the direct `search_pages(site=..., query=...)` objects.
- The focused RED failures showed malformed arguments crossing into implementation internals (`site.client` and `query.limit`). The GREEN regression now proves the method fails before those effects and before AMC request work.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
