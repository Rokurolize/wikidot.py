# PR Draft: Validate Tag Container Inputs

## Summary

`SearchPagesQuery.as_dict()` already validated non-string entries inside a `tags` list, and `SitePagesAccessor._normalize_required_tags()` already validated non-string entries inside a `required_tags` list. Both public surfaces still accepted malformed container shapes outside the documented `str | list[str] | None` contract. `SearchPagesQuery(tags=123).as_dict()`, `tags=True`, `tags=("scp",)`, `tags={"tag": "scp"}`, and arbitrary objects were serialized into the query dictionary unchanged. `Site.pages.iter_search(required_tags=123)` and similar scalar/object values raised raw `TypeError`, while tuple and dictionary containers were accepted or normalized before any stable validation error.

This change validates tag container shape at the existing public boundaries. `SearchPagesQuery.as_dict()` now accepts only tag strings or tag lists after `None` exclusion, and raises `ValueError("tags must be a string, list, or None")` for other containers. `SitePagesAccessor._normalize_required_tags()` now accepts only `None`, whitespace-delimited strings, or lists, and raises `ValueError("required_tags must be a string, list, or None")` before any ListPages request for other containers. Existing tag string serialization, valid `list[str]` joining, non-string list-entry errors, required-tag filtering, chunk sizing, page/source iteration, and static gates remain unchanged.

## Outcome

Generated ListPages callers now get stable tag-container diagnostics before malformed values can be serialized into query payloads or silently alter required-tag filtering.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `SearchPagesQuery`, `Site.pages.search(...)`, `Site.pages.iter_search(...)`, `Site.pages.iter_sources(...)`, broad tag-based corpus collection, client-side required-tag filtering, generated query dictionaries, JSON/YAML adapters, and local fixtures.

## Current Evidence

Local rollout-backed drafts establish tag-based ListPages search and source iteration as practical high-use surfaces. [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [342-pr-validate-tag-list-inputs.md](342-pr-validate-tag-list-inputs.md), [344-pr-validate-search-pagination-types.md](344-pr-validate-search-pagination-types.md), [409-pr-reject-boolean-search-pagination-values.md](409-pr-reject-boolean-search-pagination-values.md), [496-pr-clean-pyright-test-typing.md](496-pr-clean-pyright-test-typing.md), and [529-pr-validate-search-query-string-fields.md](529-pr-validate-search-query-string-fields.md) cover broad ListPages use, bounded search/source iteration, required-tag filtering, remote chunk preservation, tag-list entry validation, pagination validation, boolean pagination rejection, pyright cleanup, and scalar query string-field validation.

Those prior slices are not duplicates. Issue 342 validates entries inside `tags=[...]` and `required_tags=[...]`, but does not reject non-list containers such as tuples, dictionaries, booleans, integers, or arbitrary objects. Issue 529 validates scalar ListPages filter fields and explicitly leaves tag container validation out of scope. This slice closes the separate tag-container boundary while preserving existing entry validation and serialization semantics. No upstream issue was filed from this local workspace.

## Changes

- Validate `SearchPagesQuery.as_dict()` tag container shape before returning the query dictionary.
- Preserve `tags="scp euclid"` string passthrough and `tags=["scp", "euclid"]` list joining.
- Preserve `ValueError("tags list entries must be strings")` for invalid list entries.
- Validate `SitePagesAccessor._normalize_required_tags()` container shape before iterating values.
- Preserve `required_tags=None`, whitespace-delimited required-tag strings, valid `list[str]` required tags, and existing `ValueError("required_tags list entries must be strings")` for invalid list entries.
- Add focused parametrized tests covering integer, boolean, tuple, dictionary, and arbitrary-object containers for both public surfaces.

## Type Of Change

- Input validation
- ListPages request preflight hardening
- Required-tag filtering hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SearchPagesQuery(tags=...).as_dict()` must reject non-string and non-list tag containers with `ValueError("tags must be a string, list, or None")`. |
| R2 | `Site.pages.iter_search(required_tags=...)` must reject non-string and non-list required-tag containers with `ValueError("required_tags must be a string, list, or None")` before any ListPages search. |
| R3 | Existing valid tag strings, valid tag lists, `None` exclusion, and non-string list-entry diagnostics must remain compatible. |
| R4 | Existing required-tag strings, valid required-tag lists, `None`, non-string list-entry diagnostics, broad remote search, local filtering, source iteration, and remote chunk-size behavior must remain compatible. |
| R5 | This slice must not validate tag syntax, coerce containers, accept tuple/dict/set aliases, parse scalar query fields, change pagination semantics, change `created_by`, change live Wikidot behavior, or create upstream Issues/PRs. |
| R6 | Focused RED/GREEN, query tests, adjacent page/site ListPages tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed `tags` containers raise during query serialization. | `test_as_dict_tags_must_be_string_list_or_none` failed RED for 5 malformed containers with `DID NOT RAISE`, then passed GREEN after validation was added. | Returning booleans, integers, tuples, dictionaries, or arbitrary objects from `as_dict()` rejects this local completion claim. | SearchPagesQuery serialization | `src/wikidot/module/page.py`, `tests/unit/test_search_pages_query.py` |
| R2 | Malformed `required_tags` containers raise before search. | `test_iter_search_required_tags_must_be_string_list_or_none` failed RED for 5 malformed containers: scalar/object values raised raw `TypeError`, and tuple/dictionary values produced `DID NOT RAISE`; the test passed GREEN after validation was added. | Calling `PageCollection.search_pages`, raising raw `TypeError`, or silently accepting tuple/dict containers rejects this local completion claim. | Site page iterator filtering | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Existing tag serialization remains stable. | `uv run pytest tests/unit/test_search_pages_query.py -q` passed 45 tests, including valid tag string/list cases and list-entry validation. | Rejecting valid strings/lists, serializing `None`, changing list joining, or changing list-entry diagnostics rejects this local completion claim. | Query serialization | `tests/unit/test_search_pages_query.py`, `tests/unit/test_page.py` |
| R4 | Existing ListPages and required-tag iterator behavior remains green. | `TestSitePagesAccessor` passed 38 tests and page search tests passed 32 tests. | Regressing broad remote chunks, required-tag filtering, source fetch skipping, pagination, page searches, or ListPages request payloads rejects this local completion claim. | Site page accessors and PageCollection search | `tests/unit/test_site.py`, `tests/unit/test_page.py` |
| R5 | Broader semantics stay out of scope. | The implementation only checks container shape and keeps syntax, coercion, pagination, scalar field grammar, and live request behavior unchanged. | Accepting tuple/dict/set aliases, stringifying containers, parsing tag grammar, or changing live request behavior rejects this local completion claim. | Scope control | `src/wikidot/module/page.py`, `src/wikidot/module/site.py` |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No private material or live action is needed to prove the behavior. | All regressions use synthetic values and local unit tests; the draft contains no raw credentials, cookies, auth JSON, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `307c836 fix(page): validate tag container inputs`.

- RED tag-container query tests: `uv run pytest tests/unit/test_search_pages_query.py::TestSearchPagesQueryAsDict::test_as_dict_tags_must_be_string_list_or_none -q` failed 5 cases before the fix with `DID NOT RAISE`, proving malformed `tags` containers were returned by `as_dict()` unchanged.
- RED required-tag-container tests: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_search_required_tags_must_be_string_list_or_none -q` failed 5 cases before the fix; integer, boolean, and arbitrary-object containers raised raw `TypeError`, while tuple and dictionary containers produced `DID NOT RAISE`.
- GREEN focused query tests: `uv run pytest tests/unit/test_search_pages_query.py::TestSearchPagesQueryAsDict::test_as_dict_tags_must_be_string_list_or_none -q` passed 5 tests.
- GREEN focused required-tag tests: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_search_required_tags_must_be_string_list_or_none -q` passed 5 tests.
- `uv run pytest tests/unit/test_search_pages_query.py -q` passed 45 tests.
- `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed 38 tests.
- `uv run pytest tests/unit/test_page.py::TestSearchPagesQuery tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed 32 tests.
- `uv run pytest tests/unit -q` passed 2512 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `SearchPagesQuery(tags=123).as_dict()`, `SearchPagesQuery(tags=True).as_dict()`, `SearchPagesQuery(tags=("scp",)).as_dict()`, `SearchPagesQuery(tags={"tag": "scp"}).as_dict()`, and arbitrary object containers raise `ValueError("tags must be a string, list, or None")`.
- `SearchPagesQuery(tags="scp euclid").as_dict()` still returns `{"tags": "scp euclid"}` plus other non-`None` defaults.
- `SearchPagesQuery(tags=["scp", "euclid"]).as_dict()` still returns a space-delimited tag string.
- `SearchPagesQuery(tags=["scp", 3]).as_dict()` still raises `ValueError("tags list entries must be strings")`.
- `Site.pages.iter_search(required_tags=123, limit=1)` and analogous malformed containers raise `ValueError("required_tags must be a string, list, or None")` before `PageCollection.search_pages` is called.
- Valid `required_tags` strings and valid `list[str]` values keep broad remote search, client-side filtering, source-fetch skip behavior, and remote chunk-size behavior.
- Existing pagination validation, scalar string-field validation, page searches, source iterators, ListPages response diagnostics, and static gates remain green.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 342. Mitigation: Issue 342 covers non-string entries inside list containers; this slice validates the separate container shape before entry validation runs.
- Risk: Rejecting tuple or dictionary containers could affect callers that used iterable aliases. Mitigation: the public type contract is `str | list[str] | None`, and accepting dictionaries can silently turn keys into required tags.
- Risk: `SearchPagesQuery` construction still accepts malformed `tags` containers until `as_dict()`. Mitigation: existing tag list-entry validation already occurs at serialization, so this preserves the local timing of the tag-specific path.
- Risk: Adding tag syntax validation could overreach. Mitigation: this slice validates container shape only and deliberately does not parse tag names, hidden-tag syntax, whitespace, or remote ListPages semantics.

## Out Of Scope

Changing tag syntax, parsing or normalizing tag strings, accepting tuple/dict/set aliases, changing tag list-entry validation, changing `created_by` object conversion, changing scalar ListPages field validation, changing pagination semantics, changing ListPages request modules, changing response parsing, changing source iteration, changing live Wikidot behavior, and upstream Issue/PR creation are outside this slice.

## Why This Matters

Tag-based ListPages queries drive browser-free page inventories, source collection, required-tag filtering, publish verification, and generated ledgers. Tag containers are request controls, so malformed generated values should fail with stable diagnostics instead of becoming arbitrary payload values, raw Python iteration errors, or accidental filter sets.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used broad ListPages search, bounded page/source iterators, required-tag filters, publish verification, and generated source ledgers.
- Existing drafts covered search pagination, tag-list entries, required-tag filters, response-body diagnostics, scalar search string fields, and full pyright cleanup, but did not validate tag container shape.
- The focused RED failures showed `tags` containers passing through query serialization unchanged and `required_tags` containers either raising raw `TypeError` or being accepted silently. The GREEN regressions cover both public boundaries before request payload construction or required-tag filtering can run.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
