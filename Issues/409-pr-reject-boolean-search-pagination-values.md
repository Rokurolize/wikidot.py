# PR Draft: Reject Boolean Search Pagination Values

## Summary

`SearchPagesQuery` validates `offset`, `limit`, and `perPage` as optional integers, but the shared helper used plain `isinstance(value, int)`. Because Python treats `bool` as an `int` subclass, boolean pagination values could enter ListPages query state: `offset=True` became offset `1`, `limit=True` became limit `1`, and `perPage=True` became a one-row page size, while some `False` values were classified as range failures rather than type failures.

This change treats boolean pagination values as malformed integer controls during `SearchPagesQuery` construction. Valid integer and `None` pagination values, existing string/float validation, range validation, `limit <= 0` no-request behavior, ListPages request construction, iterators, required-tag filtering, and source batching remain unchanged.

## Outcome

Bounded ListPages searches and source-collection iterators now fail early for boolean pagination controls instead of accidentally accepting booleans as integer offsets, limits, or page sizes.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `SearchPagesQuery`, `Site.pages.search(...)`, `Site.pages.iter_search(...)`, or `Site.pages.iter_sources(...)` for bounded page/source collection.

## Current Evidence

Local rollout evidence repeatedly uses broad ListPages and source iterator workflows with explicit `limit`, `perPage`, and `offset` values to keep corpus collection bounded. Existing drafts [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [005-pr-bound-listpages-pagination-by-limit.md](005-pr-bound-listpages-pagination-by-limit.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [023-pr-search-pagination-validation.md](023-pr-search-pagination-validation.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md), [342-pr-validate-tag-list-inputs.md](342-pr-validate-tag-list-inputs.md), [344-pr-validate-search-pagination-types.md](344-pr-validate-search-pagination-types.md), [345-pr-validate-source-iterator-batch-sizes.md](345-pr-validate-source-iterator-batch-sizes.md), and [408-pr-reject-boolean-publish-visibility-controls.md](408-pr-reject-boolean-publish-visibility-controls.md) establish this as a practical request and iterator boundary. Those slices covered bounded pagination, retry behavior, response-body diagnostics, required-tag filtering, tag-list element validation, source batch-size validation, string/float pagination types, and the same Python bool-as-int issue on a publish write path; they did not cover booleans in `SearchPagesQuery` pagination fields.

## Related Issue

Builds directly on [344-pr-validate-search-pagination-types.md](344-pr-validate-search-pagination-types.md), which rejected string and float pagination values. This slice preserves those diagnostics and adds the missing boolean exclusion for the same optional integer fields.

No upstream issue was filed from this local workspace.

## Changes

- Reject `SearchPagesQuery(offset=True or False)` with `ValueError("offset must be an integer or None")`.
- Reject `SearchPagesQuery(limit=True or False)` with `ValueError("limit must be an integer or None")`.
- Reject `SearchPagesQuery(perPage=True or False)` with `ValueError("perPage must be an integer or None")`.
- Preserve existing valid integer and `None` behavior.
- Preserve existing `offset >= 0`, `perPage > 0`, and `limit <= 0` no-request semantics.

## Type Of Change

- Input validation
- Public API behavior hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SearchPagesQuery(offset=True or False)` must reject the value with `ValueError("offset must be an integer or None")` during query construction before range comparison, serialization, ListPages request construction, or iterator work. |
| R2 | `SearchPagesQuery(limit=True or False)` must reject the value with `ValueError("limit must be an integer or None")` during query construction before serialization, ListPages request construction, no-request branching, or iterator work. |
| R3 | `SearchPagesQuery(perPage=True or False)` must reject the value with `ValueError("perPage must be an integer or None")` during query construction before range comparison, serialization, ListPages request construction, pager offset arithmetic, or iterator work. |
| R4 | Existing non-boolean pagination validation must remain unchanged for valid integers, `None`, malformed strings/floats, negative offsets, non-positive per-page values, and `limit <= 0` no-request behavior. |
| R5 | Existing `Site.pages.search(...)`, `iter_search(...)`, `iter_sources(...)`, ListPages parsing, required-tag filtering, and source batching behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent search/iterator tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Boolean offsets fail with the same integer-type diagnostic used for malformed non-integer offsets. | New `TestSearchPagesQueryValidation.test_pagination_values_reject_booleans` failed RED because `offset=True` did not raise, then passed GREEN after `bool` exclusion was added. | Treating `True` as offset `1`, classifying `False` as a range failure, serializing booleans, or reaching ListPages request code rejects this local completion claim. | Search query pagination boundary | `src/wikidot/module/page.py`, `tests/unit/test_search_pages_query.py` |
| R2 | Boolean limits fail during query construction. | The same focused regression covers `limit=True` and `limit=False` and passed GREEN after the helper change. | Treating booleans as bounded limits, converting them into request fields, or using `False` as `limit=0` no-request behavior rejects this local completion claim. | Search query pagination boundary | `src/wikidot/module/page.py`, `tests/unit/test_search_pages_query.py` |
| R3 | Boolean per-page values fail during query construction. | The same focused regression covers `perPage=True` and `perPage=False` and passed GREEN after the helper change. | Treating `True` as a one-row page size, classifying `False` as a range failure, or using booleans in pager arithmetic rejects this local completion claim. | Search query pagination boundary | `src/wikidot/module/page.py`, `tests/unit/test_search_pages_query.py` |
| R4 | Existing query construction, serialization, and range contracts remain compatible. | `tests/unit/test_search_pages_query.py` passed 26 tests after the boolean rejection was added. | Changing defaults, valid tag serialization, `created_by` conversion, valid integer pagination fields, valid `None` exclusion, string/float diagnostics, negative offset rejection, non-positive per-page rejection, or `limit=0` semantics rejects this local completion claim. | Search query public API | `tests/unit/test_search_pages_query.py` |
| R5 | Existing page search and iterator behavior remains green. | Adjacent page/search/site tests passed 48 tests; full unit tests passed 1446 tests. | Regressing `Site.pages.search(...)`, `iter_search(...)`, `iter_sources(...)`, required-tag filtering, source fallback, source result fields, ListPages response diagnostics, or page collection behavior rejects this local completion claim. | Page/source collection workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, query file passed, adjacent page/search/site tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4cd3af8 fix(page): reject boolean search pagination values`.

- RED: `uv run --extra test pytest tests/unit/test_search_pages_query.py::TestSearchPagesQueryValidation::test_pagination_values_reject_booleans -q` failed before the fix because `offset=True` did not raise.
- GREEN: `uv run --extra test pytest tests/unit/test_search_pages_query.py::TestSearchPagesQueryValidation::test_pagination_values_reject_booleans -q` passed 1 test covering boolean `offset`, `limit`, and `perPage` values.
- `uv run --extra test pytest tests/unit/test_search_pages_query.py -q` passed 26 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestSearchPagesQuery tests/unit/test_page.py::TestPageCollectionSearchPages tests/unit/test_site.py::TestSitePagesAccessor -q` passed 48 tests.
- `uv run ruff format src tests` left 81 files unchanged.
- `uv run --extra test pytest tests/unit -q` passed 1446 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `SearchPagesQuery(offset=True)` and `SearchPagesQuery(offset=False)` raise `ValueError("offset must be an integer or None")`.
- `SearchPagesQuery(limit=True)` and `SearchPagesQuery(limit=False)` raise `ValueError("limit must be an integer or None")`.
- `SearchPagesQuery(perPage=True)` and `SearchPagesQuery(perPage=False)` raise `ValueError("perPage must be an integer or None")`.
- Existing valid integer/default pagination query behavior is unchanged.
- Existing `SearchPagesQuery(offset="0")`, `SearchPagesQuery(limit="50")`, and `SearchPagesQuery(perPage=50.5)` validation remains unchanged.
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

ListPages pagination is a core path for browser-free page inventory, source collection, and publish verification workflows. The pagination fields are numeric controls, so boolean values from JSON, YAML, generated structures, or flag parsing should fail at query construction instead of silently becoming integer offsets, limits, or page sizes.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used bounded ListPages and source iterator workflows with explicit `limit`, `perPage`, and `offset` values.
- Existing local drafts covered large-corpus pagination, source fallback, retry behavior, required-tag filtering, value-range checks, and string/float pagination type checks, but did not cover Python booleans passing through optional integer pagination validation.
- The focused RED failure showed `offset=True` accepted at query construction. The GREEN regression covers `True` and `False` for `offset`, `limit`, and `perPage`.
- This slice only rejects boolean pagination values; it does not change valid pagination values, `limit <= 0` no-request behavior, offset arithmetic, pager parsing, retry policy, tag filtering, source batching, live site behavior, or result parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed pagination types instead of coercing them. Callers that load pagination settings from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should resolve those values into real integers before constructing `SearchPagesQuery`.
