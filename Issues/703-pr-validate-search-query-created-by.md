# PR Draft: Validate SearchPagesQuery Created-By

## Summary

`SearchPagesQuery` already validates invalid parameter names, pagination shape/range, boolean pagination values, scalar string fields, tag-list entries during serialization, and valid `created_by` user-name conversion. One creator filter gap remained: `created_by` accepted arbitrary non-string objects during query construction, and `as_dict()` then duck-typed any object with a string `unix_name` or `name` into the ListPages request payload.

This change validates `created_by` at the `SearchPagesQuery(...)` constructor boundary. Creator filters now accept only `str`, real `AbstractUser` objects, or `None`, with `ValueError("created_by must be an AbstractUser, string, or None")` for malformed values. Existing string filters, default query values, tag serialization, regular `User` conversion, pagination validation, page searches, and source iterator workflows remain unchanged.

## Outcome

Generated page-search callers fail before ListPages request construction when `created_by` is a malformed object, instead of serializing a fake duck-typed name or deferring failure to request serialization.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `SearchPagesQuery`, `Site.pages.search(...)`, `Site.pages.iter_search(...)`, `Site.pages.iter_sources(...)`, browser-free corpus collection, source ledgers, publish verification, generated query dictionaries, JSON/YAML adapters, and local fixtures that may hydrate creator filters from untyped data.

## Current Evidence

Local rollout-backed drafts establish ListPages search and source iteration as practical read-heavy surfaces. [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [023-pr-search-pagination-validation.md](023-pr-search-pagination-validation.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md), [342-pr-validate-tag-list-inputs.md](342-pr-validate-tag-list-inputs.md), [344-pr-validate-search-pagination-types.md](344-pr-validate-search-pagination-types.md), [409-pr-reject-boolean-search-pagination-values.md](409-pr-reject-boolean-search-pagination-values.md), [496-pr-clean-pyright-test-typing.md](496-pr-clean-pyright-test-typing.md), [529-pr-validate-search-query-string-fields.md](529-pr-validate-search-query-string-fields.md), and [534-pr-validate-search-pages-arguments.md](534-pr-validate-search-pages-arguments.md) cover broad ListPages use, bounded pagination, iterator filtering, response diagnostics, tag-list validation, pagination type validation, boolean pagination rejection, query typing cleanup, string-field validation, and direct search argument validation.

This slice is not a duplicate of those drafts. Issue 529 validates scalar string-style fields and explicitly leaves `created_by` unchanged. Issues 023, 344, and 409 validate pagination controls, not creator filters. Issue 342 validates tags and required-tag entries, not creator object shape. Issue 534 validates that `PageCollection.search_pages(...)` receives a `SearchPagesQuery` or `None`, not the internal `created_by` value inside a valid query object. No upstream issue was filed from this local workspace.

## Changes

- Add a `SearchPagesQuery` `created_by` validator.
- Accept `None`, `str`, and real `AbstractUser` instances only.
- Reject booleans, integers, dictionaries, arbitrary objects, and name-bearing non-user objects during query construction.
- Keep regular `User` conversion to the Wikidot unix-name scalar in `as_dict()`.
- Update the public query type documentation from `User | str` to `AbstractUser | str`, matching the existing user model and preserving valid user-object compatibility.

## Type Of Change

- Input validation
- ListPages request preflight hardening
- Creator-filter integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SearchPagesQuery(created_by=...)` must reject malformed non-user creator filters `True`, `12345`, `{"name": "test-user"}`, `object()`, and a non-user object with `name = "not-a-wikidot-user"`. |
| R2 | Each rejection must use `ValueError("created_by must be an AbstractUser, string, or None")` before `as_dict()` or ListPages request construction runs. |
| R3 | Existing string creator filters and regular `User` object conversion must remain compatible. |
| R4 | Existing invalid-key, pagination, tag, string-field, page search, site accessor, and ListPages response behavior must remain compatible. |
| R5 | This slice must not validate creator-name grammar, coerce creator values, change tag handling, change pagination behavior, change live Wikidot behavior, create upstream Issues, or create upstream PRs. |
| R6 | Focused RED/GREEN, query tests, adjacent page/site ListPages tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed creator filters raise during `SearchPagesQuery(...)` construction. | `test_created_by_must_be_user_string_or_none` failed RED for five malformed creator values with `DID NOT RAISE`, then passed GREEN after constructor validation was added. | Accepting a boolean, integer, dictionary, arbitrary object, or name-bearing non-user object into query state rejects this local completion claim. | SearchPagesQuery constructor | `src/wikidot/module/page.py`, `tests/unit/test_search_pages_query.py` |
| R2 | The malformed field reports the `created_by` contract directly. | The focused GREEN tests assert `created_by must be an AbstractUser, string, or None`. | Generic invalid-parameter messages, raw attribute errors, request-time failures, or late duck-typed conversion of fake objects reject this local completion claim. | Query diagnostics | `tests/unit/test_search_pages_query.py` |
| R3 | Strings and real users remain valid creator filters. | Existing `test_as_dict_created_by_user_conversion` and `test_all_valid_parameters_work` passed inside the 50-test SearchPagesQuery suite. | Rejecting creator strings, rejecting regular `User` objects, or changing `User` serialization rejects this local completion claim. | Query serialization | `tests/unit/test_search_pages_query.py` |
| R4 | Existing ListPages and iterator behavior remains green. | SearchPagesQuery passed 50 tests, adjacent page/search/site accessor tests passed 100 tests, and full unit coverage passed 3539 tests. | Regressing tags, pagination, string fields, request payload construction, ListPages response handling, page searches, site accessors, iterators, required-tag filtering, or source collection rejects this local completion claim. | Page search and source workflows | `tests/unit` |
| R5 | Broader semantics stay out of scope. | The implementation only checks object type and `None` shape, and leaves creator-name grammar plus existing name/unix-name conversion semantics unchanged. | Adding grammar rules, coercing values, trimming values, changing tag handling, changing pagination, changing live request behavior, pushing, or opening upstream Issues/PRs rejects this local completion claim. | SearchPagesQuery scope | `src/wikidot/module/page.py` |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No private material or live action is needed to prove the behavior. | All regressions use synthetic query values and local unit tests; the draft contains no raw credentials, cookies, auth JSON, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `ef5fa95 fix(page): validate search query creator`.

- RED: `uv run pytest tests/unit/test_search_pages_query.py::TestSearchPagesQueryValidation::test_created_by_must_be_user_string_or_none -q` failed 5 cases before the fix with `DID NOT RAISE`, proving malformed creator filters were accepted during query construction.
- GREEN: the same focused command passed 5 tests after creator validation was added.
- `uv run pytest tests/unit/test_search_pages_query.py -q` passed 50 tests.
- `uv run pytest tests/unit/test_page.py::TestSearchPagesQuery tests/unit/test_page.py::TestPageCollectionSearchPages tests/unit/test_site.py::TestSitePagesAccessor -q` passed 100 tests.
- `uv run pytest tests/unit -q` passed 3539 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `SearchPagesQuery(created_by=True)`, `SearchPagesQuery(created_by=12345)`, `SearchPagesQuery(created_by={"name": "test-user"})`, `SearchPagesQuery(created_by=object())`, and `SearchPagesQuery(created_by=<non-user object with name>)` raise `ValueError("created_by must be an AbstractUser, string, or None")`.
- `SearchPagesQuery(created_by="test-user").as_dict()` still emits the creator string unchanged.
- `SearchPagesQuery(created_by=<User with unix_name>).as_dict()` still emits the user's Wikidot unix name.
- Existing defaults, `None` omission, tag string/list serialization, scalar string-field validation, pagination validation, page searches, site accessors, ListPages response diagnostics, bounded iterators, required-tag filtering, and source iterators remain green.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with scalar string-field validation. Mitigation: Issue 529 explicitly left `created_by` unchanged; this slice targets only the creator filter.
- Risk: Restricting to `User` only could reject other existing wikidot.py user record types that already carry `name` or `unix_name`. Mitigation: the validator accepts `AbstractUser`, matching the broader user model used by parser-created page, forum, message, member, application, vote, and change records.
- Risk: Duck-typed objects with `name` were previously accepted. Mitigation: creator filters represent a user identity contract, so generated dictionaries or name-only carrier objects should be normalized into a string before constructing the query.
- Risk: Adding grammar validation could overreach. Mitigation: this slice validates object type only and deliberately does not parse creator-name grammar.

## Out Of Scope

Changing tag syntax, changing tag container validation, changing pagination semantics, changing scalar string-field validation, parsing creator-name grammar, coercing generated dictionaries to strings, validating live Wikidot query behavior, changing ListPages request modules, changing response parsing, changing source iteration, pushing changes, opening upstream Issues, and opening upstream PRs are outside this slice.

## Why This Matters

ListPages queries drive browser-free page inventories, source collection, required-tag filtering, publish verification, and generated local ledgers. Creator filters are request controls, so malformed generated values should fail at query construction with a field-specific diagnostic instead of being serialized from arbitrary duck-typed objects.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used broad ListPages search, bounded page/source iterators, required-tag filters, publish verification, and generated source ledgers.
- Existing drafts covered search pagination, tag-list entries, required-tag filters, response-body diagnostics, direct search argument shape, and scalar string fields, but did not validate the `created_by` object itself.
- The focused RED failures showed malformed direct creator filters could be stored in query state. The GREEN regression covers malformed creator rejection, valid string and user conversion compatibility, adjacent page/search/site behavior, full unit compatibility, lint, format, type, pyright, and whitespace gates.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
