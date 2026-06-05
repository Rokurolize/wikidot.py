# PR Draft: Validate Tag List Inputs

## Summary

`SearchPagesQuery.as_dict()` accepted `tags` as either a string or a list of strings, but a mixed list such as `["scp", 3]` failed later with Python's raw `"sequence item ... expected str instance"` `TypeError` during string joining. `SitePagesAccessor.iter_search()` and `iter_sources()` accepted `required_tags` as either a whitespace-delimited string or a list of strings, but a mixed list could be normalized into a set containing non-string values and silently filter out otherwise valid ListPages results.

This change validates both list inputs at the public boundary. Non-string `tags` list entries now raise `ValueError("tags list entries must be strings")`; non-string `required_tags` list entries now raise `ValueError("required_tags list entries must be strings")` before any ListPages request is made.

## Outcome

Large ListPages and source-collection workflows fail early with clear caller-facing validation errors instead of raw serialization failures or silent client-side filtering misses.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `SearchPagesQuery`, `Site.pages.iter_search()`, or `Site.pages.iter_sources()` to collect broad page/source corpora by tag.

## Current Evidence

Local rollout evidence repeatedly exercises broad ListPages and source iterator workflows with `tags` and `required_tags`, especially around large corpus collection and client-side required-tag filtering. Existing drafts [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), and [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md) document those workflows and their pagination/filtering constraints, but they did not cover invalid non-string tag-list entries.

## Related Issue

Builds on [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [023-pr-search-pagination-validation.md](023-pr-search-pagination-validation.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), and [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md). Those drafts covered bounded iteration, source iteration, pagination validation, required-tag filtering, and remote chunk-size preservation; this slice covers tag-list element type validation.

No upstream issue was filed from this local workspace.

## Changes

- Validate `SearchPagesQuery(tags=[...]).as_dict()` list elements before joining them.
- Validate `SitePagesAccessor._normalize_required_tags()` list elements before converting them to a required-tag set.
- Preserve valid string and list tag behavior.
- Preserve the existing non-positive `limit` no-request contract and existing pagination validation.
- Add focused regression tests for both invalid list-input surfaces.

## Type Of Change

- Input validation
- Public API behavior hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SearchPagesQuery(tags=[...]).as_dict()` must raise `ValueError("tags list entries must be strings")` when any list entry is not a string. |
| R2 | Valid `tags` strings and valid `list[str]` inputs must keep their existing serialization behavior. |
| R3 | `Site.pages.iter_search(required_tags=[...])` and `iter_sources(required_tags=[...])` must raise `ValueError("required_tags list entries must be strings")` when any list entry is not a string. |
| R4 | Invalid `required_tags` list input must be rejected before `PageCollection.search_pages()` is called. |
| R5 | Valid `required_tags` strings and valid `list[str]` inputs must keep their existing broad remote search, local filtering, and remote chunk-size behavior. |
| R6 | Existing search pagination behavior, including non-positive `limit` no-request behavior and `perPage`/`offset` validation, must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, adjacent tag iterator tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Mixed `tags` lists fail with a stable `ValueError` message instead of a raw join `TypeError`. | New `TestSearchPagesQueryAsDict.test_as_dict_tags_list_requires_strings` failed RED before the fix and passed GREEN after it. | Allowing raw `TypeError`, silently stringifying non-strings, or accepting non-string entries rejects this local completion claim. | Search query serialization | `src/wikidot/module/page.py`, `tests/unit/test_search_pages_query.py` |
| R2 | Existing valid tag list and tag string tests remain green. | Existing tag serialization tests passed. | Changing valid list serialization, changing string passthrough, or adding quoting/escaping behavior outside this slice rejects this local completion claim. | Search query serialization | `tests/unit/test_search_pages_query.py` |
| R3 | Mixed `required_tags` lists fail with a stable `ValueError` message. | New `TestSitePagesAccessor.test_iter_search_required_tags_list_requires_strings` failed RED before the fix and passed GREEN after it. | Silently building a set containing non-string tags, dropping invalid entries, or coercing them to strings rejects this local completion claim. | Site page iterator filtering | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R4 | Invalid `required_tags` list input is rejected before a ListPages search is attempted. | The new regression asserts `PageCollection.search_pages` is not called. | Performing a remote ListPages request before validation rejects this local completion claim. | Site page iterator request boundary | `tests/unit/test_site.py` |
| R5 | Existing required-tag filtering and remote chunk-size behavior remain green. | Existing required-tag filter, chunk-size, and source-fetch skip tests passed. | Shrinking remote chunks because of local filtering, fetching sources for nonmatching pages, or changing valid required-tag string/list behavior rejects this local completion claim. | Iterative page/source collection | `tests/unit/test_site.py` |
| R6 | Existing pagination validation behavior is unchanged. | Full unit tests passed 918 tests, including the existing pagination validation suite. | Changing non-positive limit no-request behavior or existing `perPage`/`offset` validation rejects this local completion claim. | Search pagination contract | `tests/unit/test_search_pages_query.py`, `tests/unit/test_site.py` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use local unit tests and mocks only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed 918 tests, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `48a9932 fix(page): validate tag list inputs`.

- RED: `uv run --extra test pytest tests/unit/test_search_pages_query.py::TestSearchPagesQueryAsDict::test_as_dict_tags_list_requires_strings -q` failed before the fix because `as_dict()` raised a raw join `TypeError`.
- GREEN: `uv run --extra test pytest tests/unit/test_search_pages_query.py::TestSearchPagesQueryAsDict::test_as_dict_tags_list_requires_strings tests/unit/test_site.py::TestSitePagesAccessor::test_iter_search_required_tags_list_requires_strings -q` passed 2 tests.
- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_search_required_tags_list_requires_strings -q` failed before the `required_tags` fix because no `ValueError` was raised.
- `uv run --extra test pytest tests/unit/test_search_pages_query.py::TestSearchPagesQueryAsDict::test_as_dict_tags_list_conversion tests/unit/test_search_pages_query.py::TestSearchPagesQueryAsDict::test_as_dict_tags_string_unchanged tests/unit/test_site.py::TestSitePagesAccessor::test_iter_search_required_tags_filters_client_side tests/unit/test_site.py::TestSitePagesAccessor::test_iter_search_required_tags_keeps_remote_chunk_size_after_skips tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_required_tags_skips_source_fetch_for_nonmatching_pages -q` passed 5 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor tests/unit/test_search_pages_query.py -q` passed 36 tests.
- `uv run --extra test pytest tests/unit -q` passed 918 tests.
- `uv run ruff format src tests` left 80 files unchanged after the final edit.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- Mixed `tags` lists raise `ValueError("tags list entries must be strings")`.
- Valid `tags` strings and valid tag lists continue to serialize exactly as before.
- Mixed `required_tags` lists raise `ValueError("required_tags list entries must be strings")`.
- Invalid `required_tags` lists are rejected before `PageCollection.search_pages()` is called.
- Valid `required_tags` strings and valid required-tag lists keep broad remote search, client-side filtering, source-fetch skip, and chunk-size behavior.
- Existing search pagination validation and non-positive limit behavior remain unchanged.
- The new tests use unit-level mocks only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Tag-based page and source iteration is a common way to inspect large Wikidot corpora. Rejecting malformed tag lists at the API boundary gives callers an actionable error, preserves existing valid behavior, and avoids a harder-to-debug path where broad remote results are fetched and then silently filtered by an impossible required-tag set.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used broad ListPages and source iterator workflows with `tags` and `required_tags` as central inputs.
- The focused RED failures showed `tags=["scp", 3]` currently raising raw join `TypeError` and `required_tags=["scp", 3]` currently proceeding without the expected validation error.
- This slice only validates tag-list element types; it does not change valid tag syntax, tag normalization semantics, pagination limits, source batching, live site behavior, request retries, or result parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, and private site data out of upstream discussion.

## Additional Notes

The validation intentionally rejects non-string list entries rather than coercing them. Callers that dynamically assemble tag lists should normalize their inputs before constructing `SearchPagesQuery` or calling `iter_search()` / `iter_sources()`.
