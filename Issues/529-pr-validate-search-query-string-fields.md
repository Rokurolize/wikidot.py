# PR Draft: Validate SearchPagesQuery String Fields

## Summary

`SearchPagesQuery` already validates invalid parameter names, pagination integers, boolean pagination values, tag-list entries during serialization, and `created_by` user-name conversion. The remaining scalar ListPages filters still accepted booleans, lists, dictionaries, integers, and arbitrary objects during query construction. Those malformed values could then enter `as_dict()` and `PageCollection.search_pages(...)` request payloads as non-string ListPages controls.

This change validates the scalar string-style query fields at `SearchPagesQuery` construction. `pagetype`, `category`, `parent`, `link_to`, `created_at`, `updated_at`, `rating`, `votes`, `name`, `fullname`, `range`, `order`, `separate`, and `wrapper` now accept only `str` or `None`, with stable `ValueError("<field> must be a string or None")` diagnostics. Existing defaults, explicit `None` exclusion, tag serialization, `created_by` conversion, pagination validation, ListPages request construction, bounded iterators, required-tag filtering, page/source collection, and full static gates remain unchanged.

## Outcome

Generated page-search callers now fail before ListPages request construction when scalar query filters are malformed, instead of serializing non-string objects into AMC payloads.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `SearchPagesQuery`, `Site.pages.search(...)`, `Site.pages.iter_search(...)`, `Site.pages.iter_sources(...)`, browser-free corpus collection, source ledgers, publish verification, generated query dictionaries, JSON/YAML adapters, and local fixtures.

## Current Evidence

Local rollout-backed drafts establish ListPages search and source iteration as practical read-heavy surfaces. [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [005-pr-bound-listpages-pagination-by-limit.md](005-pr-bound-listpages-pagination-by-limit.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [023-pr-search-pagination-validation.md](023-pr-search-pagination-validation.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md), [342-pr-validate-tag-list-inputs.md](342-pr-validate-tag-list-inputs.md), [344-pr-validate-search-pagination-types.md](344-pr-validate-search-pagination-types.md), [409-pr-reject-boolean-search-pagination-values.md](409-pr-reject-boolean-search-pagination-values.md), and [496-pr-clean-pyright-test-typing.md](496-pr-clean-pyright-test-typing.md) cover broad ListPages use, bounded pagination, iterator filtering, response diagnostics, tag-list validation, pagination type validation, boolean pagination rejection, and query typing cleanup.

Those prior slices are not duplicates. Issue 342 validates tag-list entries and required-tag entries, not scalar ListPages filter fields. Issues 023, 344, and 409 validate pagination controls, not string filters. Issue 496 corrects query typing for `tags=None` and `limit=None`, but intentionally leaves other `SearchPagesQueryParams` typing questions as future work. This slice validates the separate scalar query filter fields before malformed non-string values can become request payload values. No upstream issue was filed from this local workspace.

## Changes

- Add a `SearchPagesQuery` optional-string validator.
- Validate `pagetype`, `category`, `parent`, `link_to`, `created_at`, `updated_at`, `rating`, `votes`, `name`, `fullname`, `range`, `order`, `separate`, and `wrapper` during query construction.
- Preserve existing `None` semantics by excluding `None` values from `as_dict()`.
- Leave `tags` and `created_by` on their existing specialized serialization paths.
- Add focused parametrized tests covering malformed values across all scalar string-style query fields.

## Type Of Change

- Input validation
- ListPages request preflight hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SearchPagesQuery(...)` must reject malformed non-string scalar query filter values for `pagetype`, `category`, `parent`, `link_to`, `created_at`, `updated_at`, `rating`, `votes`, `name`, `fullname`, `range`, `order`, `separate`, and `wrapper`. |
| R2 | Each rejection must use `ValueError("<field> must be a string or None")` so callers can identify the malformed field before ListPages request construction. |
| R3 | Valid strings, defaults, and existing explicit `None` exclusion must remain compatible. |
| R4 | Existing tag-list serialization, `created_by` conversion, invalid-parameter checks, pagination type/range checks, boolean pagination rejection, ListPages request construction, page searches, bounded iterators, source iterators, and required-tag filtering must remain unchanged. |
| R5 | This slice must not validate tag syntax, date grammar, rating expression grammar, sort-order grammar, wrapper/separate enum values, creator object shape, live Wikidot behavior, or upstream Issue/PR creation. |
| R6 | Focused RED/GREEN, query tests, adjacent page/site ListPages tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed scalar query filters raise during `SearchPagesQuery(...)` construction. | `test_string_query_fields_must_be_strings_or_none` failed RED for 14 malformed scalar fields with `DID NOT RAISE`, then passed GREEN after validation was added. | Accepting a boolean, list, dictionary, integer, or arbitrary object into query state rejects this local completion claim. | SearchPagesQuery constructor | `src/wikidot/module/page.py`, `tests/unit/test_search_pages_query.py` |
| R2 | Each malformed field reports the affected field name. | The focused GREEN tests assert field-specific messages such as `category must be a string or None` and `order must be a string or None`. | Generic invalid-parameter messages, pagination messages, raw type errors, or request-time failures reject this local completion claim. | Query diagnostics | `tests/unit/test_search_pages_query.py` |
| R3 | Defaults, valid strings, and existing `None` omission remain stable. | Existing default, custom, valid-all-fields, `None` exclusion, and practical query tests passed inside the 40-test SearchPagesQuery suite. | Removing default `pagetype`, `category`, `order`, `separate`, or `wrapper`; serializing `None`; or rejecting valid strings rejects this local completion claim. | Query serialization | `tests/unit/test_search_pages_query.py`, `tests/unit/test_page.py` |
| R4 | Existing ListPages and iterator behavior remains green. | SearchPagesQuery passed 40 tests, adjacent page/search/site accessor tests passed 65 tests, and full unit passed 2502 tests. | Regressing tags, creator conversion, pagination, request payloads, ListPages response handling, iterators, required-tag filtering, or source collection rejects this local completion claim. | Page search and source workflows | `tests/unit` |
| R5 | Broader semantics stay out of scope. | The implementation only checks type/`None` shape and does not parse filter grammar or enum values. | Adding syntax rules, coercing values, trimming values, changing tag handling, changing `created_by`, or changing live request behavior rejects this local completion claim. | SearchPagesQuery scope | `src/wikidot/module/page.py` |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No private material or live action is needed to prove the behavior. | All regressions use synthetic query values and local unit tests; the draft contains no raw credentials, cookies, auth JSON, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `04029a0 fix(page): validate search query string fields`.

- RED scalar-field tests: `uv run pytest tests/unit/test_search_pages_query.py::TestSearchPagesQueryValidation::test_string_query_fields_must_be_strings_or_none -q` failed 14 cases before the fix with `DID NOT RAISE`, proving malformed scalar filter values were accepted during query construction.
- GREEN focused tests: the same focused command passed 14 tests after scalar field validation was added.
- `uv run pytest tests/unit/test_search_pages_query.py -q` passed 40 tests.
- `uv run pytest tests/unit/test_page.py::TestSearchPagesQuery tests/unit/test_page.py::TestPageCollectionSearchPages tests/unit/test_site.py::TestSitePagesAccessor -q` passed 65 tests.
- `uv run pytest tests/unit -q` passed 2502 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `SearchPagesQuery(category=["scp"])`, `SearchPagesQuery(parent=123)`, `SearchPagesQuery(order=["rating desc"])`, and analogous malformed scalar filter values raise `ValueError("<field> must be a string or None")` before ListPages request construction.
- Valid scalar strings still serialize through `as_dict()` unchanged.
- Existing defaults for `pagetype`, `category`, `order`, `separate`, and `wrapper` remain present.
- Existing `None` values remain excluded from `as_dict()`.
- Existing `tags` string/list serialization and `created_by` user conversion remain unchanged.
- Existing pagination validation, page searches, bounded iterators, source iterators, required-tag filtering, and ListPages response diagnostics remain green.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with tag-list validation. Mitigation: Issue 342 covers `tags` and required-tag entries; this slice leaves tags unchanged and validates only scalar fields.
- Risk: This could be confused with pagination validation. Mitigation: Issues 023, 344, and 409 cover pagination controls; this slice validates non-pagination scalar filters.
- Risk: Rejecting non-string objects could affect callers that passed generated dictionaries or booleans intentionally. Mitigation: the public query contract describes these fields as string-style ListPages controls; callers should normalize generated structures into strings before constructing the query.
- Risk: Adding grammar validation could overreach. Mitigation: this slice validates type only and deliberately does not parse dates, rating expressions, order grammar, or layout-control values.

## Out Of Scope

Changing tag syntax, validating `tags` container type beyond the existing list-entry path, changing `created_by` object conversion, parsing date expressions, validating rating/vote grammar, validating order grammar, validating `separate`/`wrapper` enum values, changing pagination semantics, changing ListPages request modules, changing response parsing, changing source iteration, changing live Wikidot behavior, and upstream Issue/PR creation are outside this slice.

## Why This Matters

ListPages queries drive browser-free page inventories, source collection, required-tag filtering, publish verification, and generated local ledgers. Scalar query filters are request controls, so malformed generated values should fail at construction with field-specific diagnostics instead of being serialized as arbitrary objects in AMC payloads.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used broad ListPages search, bounded page/source iterators, required-tag filters, publish verification, and generated source ledgers.
- Existing drafts covered search pagination, tag-list entries, required-tag filters, response-body diagnostics, and full pyright cleanup, but did not validate scalar query filter values.
- The focused RED failures showed every scalar field accepting malformed objects during query construction. The GREEN regression covers all affected fields before request payload construction can run.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
