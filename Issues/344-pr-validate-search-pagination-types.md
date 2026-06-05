# PR Draft: Validate Search Pagination Types

## Summary

`SearchPagesQuery` already rejected negative `offset` values and non-positive `perPage` values, and `PageCollection.search_pages(...)` intentionally preserves `limit <= 0` as a no-request empty-result path. A remaining boundary gap was type validation: `offset="0"` raised a raw Python comparison `TypeError`, `limit="50"` was accepted until later search/iterator comparison code, and `perPage=50.5` was accepted even though downstream pagination uses integer offsets, chunk limits, and request fields.

This change validates `offset`, `limit`, and `perPage` as integers or `None` during `SearchPagesQuery` construction. Invalid values now raise stable `ValueError` messages before ListPages request construction, iterator chunking, or pager offset arithmetic begins.

## Outcome

Bounded ListPages searches and source-collection iterators now fail early for malformed pagination types instead of leaking raw comparison errors or allowing non-integer pagination values into request construction.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `SearchPagesQuery`, `Site.pages.search(...)`, `Site.pages.iter_search(...)`, or `Site.pages.iter_sources(...)` for bounded page/source collection.

## Current Evidence

Local rollout evidence repeatedly uses broad ListPages and source iterator workflows with explicit `limit`, `perPage`, and `offset` values to keep corpus collection bounded. Existing drafts [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [005-pr-bound-listpages-pagination-by-limit.md](005-pr-bound-listpages-pagination-by-limit.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [023-pr-search-pagination-validation.md](023-pr-search-pagination-validation.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md), and [342-pr-validate-tag-list-inputs.md](342-pr-validate-tag-list-inputs.md) establish this as a practical request and iterator boundary. Those slices covered bounded pagination, retry behavior, response-body diagnostics, required-tag filtering, tag-list element validation, and pagination value ranges; they did not cover non-integer pagination types.

## Related Issue

Builds directly on [023-pr-search-pagination-validation.md](023-pr-search-pagination-validation.md), which rejected `offset < 0` and `perPage <= 0`. This slice preserves those range checks and adds type checks for `offset`, `limit`, and `perPage`.

No upstream issue was filed from this local workspace.

## Changes

- Add a small shared `SearchPagesQuery` helper for optional integer pagination fields.
- Reject non-integer `offset` values with `ValueError("offset must be an integer or None")`.
- Reject non-integer `limit` values with `ValueError("limit must be an integer or None")`.
- Reject non-integer `perPage` values with `ValueError("perPage must be an integer or None")`.
- Preserve existing valid integer and `None` behavior.
- Preserve existing `offset >= 0`, `perPage > 0`, and `limit <= 0` no-request semantics.

## Type Of Change

- Input validation
- Public API behavior hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SearchPagesQuery(offset=...)` must reject non-integer, non-`None` offset values with `ValueError("offset must be an integer or None")` before range comparison or request construction. |
| R2 | `SearchPagesQuery(limit=...)` must reject non-integer, non-`None` limit values with `ValueError("limit must be an integer or None")` during query construction. |
| R3 | `SearchPagesQuery(perPage=...)` must reject non-integer, non-`None` per-page values with `ValueError("perPage must be an integer or None")` before range comparison or iterator arithmetic. |
| R4 | Existing valid pagination behavior must remain unchanged for default values, positive integer `perPage`, non-negative integer `offset`, integer `limit`, and `None` values where supported. |
| R5 | Existing `limit <= 0` no-request behavior, `offset < 0` rejection, and `perPage <= 0` rejection must remain unchanged. |
| R6 | Existing `Site.pages.search(...)`, `iter_search(...)`, `iter_sources(...)`, ListPages parsing, required-tag filtering, and source batching behavior must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, adjacent search/iterator tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | String offsets fail with a stable `ValueError` instead of raw comparison `TypeError`. | New `TestSearchPagesQueryValidation.test_offset_must_be_integer` failed RED before the fix with `TypeError` and passed GREEN after it. | Leaking `TypeError`, accepting `"0"`, coercing strings, or reaching request construction rejects this local completion claim. | Search query pagination boundary | `src/wikidot/module/page.py`, `tests/unit/test_search_pages_query.py` |
| R2 | String limits fail during query construction. | New `TestSearchPagesQueryValidation.test_limit_must_be_integer` failed RED before the fix because no `ValueError` was raised and passed GREEN after it. | Accepting `"50"`, coercing strings, or deferring the failure to `search_pages(...)` / `iter_search(...)` rejects this local completion claim. | Search query pagination boundary | `src/wikidot/module/page.py`, `tests/unit/test_search_pages_query.py` |
| R3 | Float per-page values fail during query construction. | New `TestSearchPagesQueryValidation.test_per_page_must_be_integer` failed RED before the fix because no `ValueError` was raised and passed GREEN after it. | Accepting `50.5`, truncating floats, or using a non-integer per-page value in offset arithmetic rejects this local completion claim. | Search query pagination boundary | `src/wikidot/module/page.py`, `tests/unit/test_search_pages_query.py` |
| R4 | Valid query construction and serialization remain compatible. | `tests/unit/test_search_pages_query.py` passed 25 tests. | Changing defaults, valid tag serialization, `created_by` conversion, valid integer pagination fields, or valid `None` exclusion rejects this local completion claim. | Search query public API | `tests/unit/test_search_pages_query.py` |
| R5 | Existing range and no-request contracts remain compatible. | The adjacent page/search/site run passed 40 tests, including zero-limit no-request, limit-capped pagination, `offset < 0`, and `perPage <= 0` coverage. | Regressing `limit=0`, negative offset rejection, non-positive per-page rejection, pager offset calculation, or limit capping rejects this local completion claim. | ListPages pagination contract | `tests/unit/test_page.py`, `tests/unit/test_site.py` |
| R6 | Existing page search and iterator behavior remains green. | Full unit passed 924 tests. | Regressing `Site.pages.search(...)`, `iter_search(...)`, `iter_sources(...)`, required-tag filtering, source fallback, source result fields, ListPages response diagnostics, or publish-adjacent page behavior rejects this local completion claim. | Page/source collection workflows | `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, `test_search_pages_query.py` passed 25 tests, adjacent page/search/site tests passed 40 tests, full unit passed 924 tests, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `706765c fix(page): validate search pagination types`.

- RED: `uv run --extra test pytest tests/unit/test_search_pages_query.py::TestSearchPagesQueryValidation::test_offset_must_be_integer tests/unit/test_search_pages_query.py::TestSearchPagesQueryValidation::test_limit_must_be_integer tests/unit/test_search_pages_query.py::TestSearchPagesQueryValidation::test_per_page_must_be_integer -q` failed before the fix. `offset="0"` leaked a raw comparison `TypeError`; `limit="50"` and `perPage=50.5` did not raise the expected validation error.
- GREEN: `uv run --extra test pytest tests/unit/test_search_pages_query.py::TestSearchPagesQueryValidation::test_offset_must_be_integer tests/unit/test_search_pages_query.py::TestSearchPagesQueryValidation::test_limit_must_be_integer tests/unit/test_search_pages_query.py::TestSearchPagesQueryValidation::test_per_page_must_be_integer -q` passed 3 tests.
- `uv run --extra test pytest tests/unit/test_search_pages_query.py -q` passed 25 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestSearchPagesQuery tests/unit/test_page.py::TestPageCollectionSearchPages tests/unit/test_site.py::TestSitePagesAccessor -q` passed 40 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run --extra test pytest tests/unit -q` passed 924 tests.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `SearchPagesQuery(offset="0")` raises `ValueError("offset must be an integer or None")`.
- `SearchPagesQuery(limit="50")` raises `ValueError("limit must be an integer or None")`.
- `SearchPagesQuery(perPage=50.5)` raises `ValueError("perPage must be an integer or None")`.
- Existing valid integer/default pagination query behavior is unchanged.
- Existing `SearchPagesQuery(offset=-1)` and `SearchPagesQuery(perPage=0)` validation remains unchanged.
- Existing `PageCollection.search_pages(..., SearchPagesQuery(limit=0))` no-request empty-result behavior remains unchanged.
- Existing ListPages search, iterator, required-tag, and source-iterator tests remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

ListPages pagination is a core path for browser-free page inventory, source collection, and publish verification workflows. The pagination fields are numeric controls, so invalid types should fail at query construction with stable caller-facing validation rather than leaking Python comparison errors or reaching request payloads.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used bounded ListPages and source iterator workflows with explicit `limit`, `perPage`, and `offset` values.
- Existing local drafts covered large-corpus pagination, source fallback, retry behavior, required-tag filtering, and value-range checks, but did not cover non-integer pagination types.
- The focused RED failures showed `offset="0"` leaking raw `TypeError`, while `limit="50"` and `perPage=50.5` were accepted at query construction.
- This slice only validates pagination field types; it does not change valid pagination values, `limit <= 0` no-request behavior, offset arithmetic, pager parsing, retry policy, tag filtering, source batching, live site behavior, or result parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed pagination types instead of coercing them. Callers that load pagination settings from CLI arguments, environment variables, or config files should parse those values into integers before constructing `SearchPagesQuery`.
