# PR Draft: Validate Search Created-By Filters

## Summary

`SearchPagesQuery.created_by` is documented as `User | str | None` and serializes into the scalar `created_by` field passed to Wikidot's `ListPagesModule`. The existing serializer correctly converted a regular `User` with `unix_name="test-user"` into `"test-user"`, but it also accepted arbitrary duck-typed objects that happened to expose a `unix_name` or `name` attribute. It also fell back from a `User`'s missing `unix_name` to display `name`, which can serialize a non-unix display name such as `"Test User"` into a field that is expected to identify a Wikidot account by unix name.

This change validates the `created_by` search filter at serialization time. Strings remain accepted unchanged, regular `User` objects serialize only through a non-empty `unix_name`, non-string non-`User` values raise `ValueError("created_by must be a string or User")`, and `User` objects with missing or empty unix names raise `ValueError("created_by user must have a unix_name")`. Existing tag serialization, pagination validation, valid `User` conversion, `None` exclusion, ListPages search calls, and site page accessors remain unchanged.

## Outcome

Page search queries no longer silently turn display names, mocks, fixture doubles, parsed placeholder-like objects, or arbitrary ledger objects into a `created_by` filter. Callers either pass a deliberate raw string filter or a real Wikidot `User` with a usable unix name.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page search, page-source iterators, large ListPages inventories, translation audit tooling, author-filtered report generation, or local ledgers that construct search queries from previously parsed objects.

## Current Evidence

Local rollout-backed drafts repeatedly identify ListPages and page-search workflows as practical operational surfaces. Existing drafts [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [023-pr-search-pagination-validation.md](023-pr-search-pagination-validation.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [306-pr-listpages-user-context.md](306-pr-listpages-user-context.md), [344-pr-validate-search-pagination-types.md](344-pr-validate-search-pagination-types.md), [409-pr-reject-boolean-search-pagination-values.md](409-pr-reject-boolean-search-pagination-values.md), and [411-pr-reject-boolean-source-iterator-batch-sizes.md](411-pr-reject-boolean-source-iterator-batch-sizes.md) establish bounded search, source iteration, pagination validation, required-tag filtering, ListPages user parsing diagnostics, and batch-size validation as active downstream needs.

Those prior slices are not duplicates. Issues018, 019, 049, 068, and 411 improved page/source iterator ergonomics. Issues023, 344, and 409 validate pagination controls. Issue306 improves parsed linked-user diagnostics in generated ListPages output. None of them validates `SearchPagesQuery.created_by` input serialization before sending the `created_by` filter to ListPages. A local duplicate search over `Issues`, `tests/unit`, and `src/wikidot` found existing valid `User` conversion and several ListPages parser `created_by` diagnostics, but no draft or regression for `SearchPagesQuery.created_by` rejecting non-`User` objects or `User` objects without unix names.

## Related Issue

Builds directly on [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [023-pr-search-pagination-validation.md](023-pr-search-pagination-validation.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [306-pr-listpages-user-context.md](306-pr-listpages-user-context.md), [344-pr-validate-search-pagination-types.md](344-pr-validate-search-pagination-types.md), [409-pr-reject-boolean-search-pagination-values.md](409-pr-reject-boolean-search-pagination-values.md), and [411-pr-reject-boolean-source-iterator-batch-sizes.md](411-pr-reject-boolean-source-iterator-batch-sizes.md).

No upstream issue was filed from this local workspace.

## Changes

- Import `User` at runtime in `src/wikidot/module/page.py` so `SearchPagesQuery.as_dict()` can enforce the documented `created_by` object type.
- Preserve raw string `created_by` filters unchanged.
- Convert regular `User` objects only through non-empty `User.unix_name`.
- Reject non-string non-`User` `created_by` values with `ValueError("created_by must be a string or User")`.
- Reject `User` values with `unix_name is None` or `unix_name == ""` with `ValueError("created_by user must have a unix_name")`.
- Add focused unit regressions for duck-typed user-like objects and missing or empty unix names.

## Type Of Change

- Input validation
- Search query serialization hardening
- ListPages author-filter correctness
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SearchPagesQuery(created_by=<non-string non-User>).as_dict()` must raise `ValueError("created_by must be a string or User")` before serializing an arbitrary object into a ListPages field. |
| R2 | `SearchPagesQuery(created_by=user).as_dict()` must raise `ValueError("created_by user must have a unix_name")` when `user.unix_name` is `None` or an empty string. |
| R3 | `SearchPagesQuery(created_by="test-user").as_dict()` must keep the string unchanged. |
| R4 | `SearchPagesQuery(created_by=User(..., unix_name="test-user")).as_dict()` must serialize to `"test-user"`. |
| R5 | Existing tags, pagination, valid `None` exclusion, page search, and site page accessor behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A duck-typed object with `unix_name = "not-a-user"` is rejected, even though the previous serializer accepted it. | `TestSearchPagesQueryAsDict.test_as_dict_created_by_rejects_non_string_non_user` failed RED because no `ValueError` was raised, then passed GREEN after the type check was added. | Accepting fixture doubles, mocks, dictionaries, parsed placeholder-like objects, or arbitrary ledger rows as users rejects this local completion claim. | Search query serialization | `src/wikidot/module/page.py`, `tests/unit/test_search_pages_query.py` |
| R2 | Regular `User` objects with `unix_name is None` or `unix_name == ""` are rejected instead of falling back to display name. | `TestSearchPagesQueryAsDict.test_as_dict_created_by_requires_user_unix_name` covers both missing and empty unix names. | Serializing `User.name`, display names with spaces, empty strings, or placeholder values as the author filter rejects this local completion claim. | Search query serialization | `src/wikidot/module/page.py`, `tests/unit/test_search_pages_query.py` |
| R3 | Raw string filters remain a caller-controlled escape hatch. | Existing search query tests still pass with `created_by="test-user"`. | Coercing, normalizing, lowercasing, or rejecting valid strings rejects this local completion claim. | Search query public API | `tests/unit/test_search_pages_query.py` |
| R4 | Valid regular `User` conversion remains unchanged. | Existing `test_as_dict_created_by_user_conversion` still asserts `"test-user"`. | Rejecting valid `User` objects or serializing display `name` instead of `unix_name` rejects this local completion claim. | Search query public API | `tests/unit/test_search_pages_query.py` |
| R5 | Adjacent query and page-search behavior remains green. | Search query tests passed 29 tests, adjacent page/site search tests passed 89 tests, and full unit tests passed 1644 tests. | Regressing tag list serialization, `None` exclusion, pagination validation, ListPages calls, page search pagination, or site page accessors rejects this local completion claim. | Search query, page collection search, site pages accessor | `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests and local drafts only. | Using credentials, cookies, auth JSON, raw rollout paths, live Wikidot actions, sandbox account details, private site data, or upstream issue/PR creation rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `d7e7661 fix(page): validate search created_by filters`.

- RED: `uv run --extra test python -m pytest tests/unit/test_search_pages_query.py::TestSearchPagesQueryAsDict::test_as_dict_created_by_rejects_non_string_non_user tests/unit/test_search_pages_query.py::TestSearchPagesQueryAsDict::test_as_dict_created_by_requires_user_unix_name -q` failed before the fix because both invalid `created_by` values reported `DID NOT RAISE`.
- GREEN: the focused command passed after adding the `User` type check and unix-name validation.
- Boundary extension: `test_as_dict_created_by_requires_user_unix_name` now covers both `unix_name is None` and `unix_name == ""`.
- `uv run --extra test python -m pytest tests/unit/test_search_pages_query.py -q` passed 29 tests.
- `uv run --extra test python -m pytest tests/unit/test_search_pages_query.py tests/unit/test_page.py::TestSearchPagesQuery tests/unit/test_page.py::TestPageCollectionSearchPages tests/unit/test_site.py::TestSitePagesAccessor -q` passed 89 tests.
- `uv run --extra test python -m pytest tests/unit -q` passed 1644 tests.
- `uv run --extra lint ruff check .` passed.
- `uv run --extra lint ruff format --check .` passed with 82 files already formatted.
- `uv run --extra lint mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not green in the current local environment: `pyright` is now installed, but `pyright` still fails on pre-existing project-wide and negative-test typing issues. A targeted `pyright tests/unit/test_search_pages_query.py` run reports 26 existing errors in that file's older negative tests; after casting the new duck-object fixture to `Any`, it no longer reports a new error for the added `UserLike` case.

Integration tests were not run because this change is a unit-level query serialization boundary and integration tests may require live Wikidot credentials or site state.

## Acceptance Criteria

- Non-string non-`User` `created_by` values raise `ValueError("created_by must be a string or User")`.
- `User` values with missing or empty unix names raise `ValueError("created_by user must have a unix_name")`.
- String `created_by` filters remain unchanged.
- Valid regular `User` values continue to serialize to their unix name.
- Existing tags, pagination, `None` exclusion, page search, and site page accessor tests remain green.
- The implementation and draft do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and HTML implementation notes are refreshed after the docs commit.

## Upstream-Safe Motivation

Page search, bounded ListPages iteration, author-filtered inventories, and source collection workflows need predictable query serialization. A typed filter object with no unix account name should not silently degrade into a display-name string, and arbitrary objects should not become author filters just because they expose a similarly named attribute. Keeping raw strings allowed preserves explicit advanced caller control while regular `User` objects now follow the documented unix-name path.

## Local Evidence, Not For Upstream Paste

- The local rollout ledger used for this campaign covered 2427 candidate threads and repeatedly led to ListPages, page search, source iteration, pagination, required-tag filtering, parser diagnostics, and query validation slices.
- Existing local drafts covered search bounds, source fallback, pagination validation, required-tag filtering, ListPages linked-user parser diagnostics, boolean pagination rejection, and source iterator batch-size validation, but did not cover `SearchPagesQuery.created_by` serialization.
- Duplicate checks over local Issues, tests, and source found only valid `created_by` conversion and parsed ListPages user diagnostics, not input validation for this search filter.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, source text from real sites, forum content, page content, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally does not normalize strings. A caller that wants to pass an advanced or already-normalized ListPages author string can still do so explicitly. Object inputs, however, must be regular `User` instances with a real unix name.
