# PR Draft: Validate Page Constructor Tags

## Summary

`Page.tags` stores the parsed page tag list used by browser-free page inventories, required-tag filtering, metadata/tag writes, source collection decisions, generated ledgers, local audit rows, and rehydrated `Page` fixtures. Query-side tag inputs already validate `SearchPagesQuery(tags=[...])` list entries, and iterator-side required-tag filters already validate `required_tags=[...]` list entries. Before this change, direct `Page(...)` construction still accepted malformed tag state such as `tags=None`, `tags="tag1 tag2"`, `tags=("tag1",)`, `tags=["tag1", 3]`, `tags=[True]`, or `tags=[None]`, storing values that could later fail as raw joins, inconsistent client-side filtering, or malformed local workflow records.

This change validates the direct constructor's `tags` field during `Page.__post_init__`. Non-list values now raise `ValueError("tags must be a list")`; list entries must be strings and otherwise raise `ValueError("tags list entries must be strings")`; valid `list[str]` values remain accepted. Valid page construction, parser-created pages, query tag serialization, required-tag filtering, metadata/tag workflows, page source/revision/file/vote workflows, and site workflows remain unchanged.

## Outcome

Callers cannot silently construct `Page` objects with malformed tag state, while valid page tag lists continue to behave as before.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page inventories, tag-based source collection, required-tag filters, metadata/tag writes, page publishing checks, generated audit rows, migration tooling, local fixtures, or rehydrated `Page` objects.

## Current Evidence

Local rollout-backed drafts already establish tag handling as operationally meaningful. [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md) and [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md) document broad ListPages discovery with local required-tag filtering, and [342-pr-validate-tag-list-inputs.md](342-pr-validate-tag-list-inputs.md) validates public query and iterator tag-list inputs. Recent direct-constructor hardening in [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md), [482-pr-validate-page-constructor-count-fields.md](482-pr-validate-page-constructor-count-fields.md), [483-pr-validate-page-constructor-rating-field.md](483-pr-validate-page-constructor-rating-field.md), and [484-pr-validate-page-constructor-parent-fullname.md](484-pr-validate-page-constructor-parent-fullname.md) validates adjacent page identity, count, rating, and parent metadata boundaries.

Those prior slices are not duplicates. Issue 342 validates `SearchPagesQuery(tags=[...]).as_dict()` before query serialization and `SitePagesAccessor._normalize_required_tags(...)` before iterator filtering. It does not validate stored `Page.tags` state created by direct `Page(tags=...)` construction. Issues 481 through 484 validate direct page identity, count, rating, and parent fields only. None validates direct `Page(tags=...)` construction before malformed tags become stored page state.

## Related Issue / Non-Duplicate Analysis

Builds directly on the tag workflow and page constructor surfaces documented by [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [342-pr-validate-tag-list-inputs.md](342-pr-validate-tag-list-inputs.md), [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md), [482-pr-validate-page-constructor-count-fields.md](482-pr-validate-page-constructor-count-fields.md), [483-pr-validate-page-constructor-rating-field.md](483-pr-validate-page-constructor-rating-field.md), and [484-pr-validate-page-constructor-parent-fullname.md](484-pr-validate-page-constructor-parent-fullname.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a direct page tags validator that requires a `list`.
- Validate every direct `Page.tags` list entry as `str`.
- Validate `Page.tags` during `Page.__post_init__`.
- Reject non-list constructor tags with stable `ValueError("tags must be a list")`.
- Reject non-string constructor tag entries with stable `ValueError("tags list entries must be strings")`.
- Preserve valid empty and non-empty tag lists, parser-created pages, query tag serialization, required-tag filtering, and adjacent page/site workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page tag-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(tags=...)` must reject non-list values with `ValueError("tags must be a list")`. |
| R2 | `Page(tags=[...])` must reject non-string entries with `ValueError("tags list entries must be strings")`. |
| R3 | `Page(tags=[])` and `Page(tags=["tag1", "_hidden"])` must remain valid and store the list values unchanged. |
| R4 | Valid `Page` construction, parser-created pages, query tag serialization, required-tag filtering, metadata/tag workflows, page source/revision/file/vote workflows, and site workflows must remain unchanged. |
| R5 | This slice must not change tag syntax rules, tag normalization, tag ordering, search query semantics, required-tag filtering semantics, parent site, users, timestamps, `rating_percent`, cached source/revisions/votes/files, or other parser-derived nullable metadata. |
| R6 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, constructor tests, adjacent page/site/page-file/page-vote/search tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list direct `Page.tags` values fail at the constructor boundary. | `TestPageInit.test_init_rejects_non_list_tags` failed RED for 3 non-list values because constructors did not raise, then passed GREEN after validation was added. | Accepting `None`, strings, tuples, arbitrary non-list objects, or coercing them into a tag list rejects this local completion claim. | `Page` constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Mixed or malformed direct tag lists fail with the same stable entry diagnostic used by query tag validation. | `TestPageInit.test_init_rejects_non_string_tag_entries` failed RED for 3 malformed lists because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, numbers, `None`, arbitrary non-string entries, silently dropping entries, or stringifying entries rejects this local completion claim. | `Page` constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Valid empty and non-empty tag lists remain accepted. | `TestPageInit.test_init_accepts_valid_tags` passed for `[]` and `["tag1", "_hidden"]` before and after the fix. | Rejecting valid lists, changing tag order, changing hidden-tag strings, or normalizing valid strings rejects this local completion claim. | `Page` constructor tag state | `tests/unit/test_page_constructor.py` |
| R4 | Existing valid page, query, and site workflows remain green. | `tests/unit/test_page_constructor.py` passed 57 tests; adjacent page/site/page-file/page-vote/search tests passed 710 tests; full unit tests passed 2039 tests. | Regressing valid fixture construction, parser-created pages, query tag serialization, required-tag filtering, metadata/tag behavior, page lookup, page source/revision/file/vote workflows, or site workflows rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_search_pages_query.py`, `tests/unit` |
| R5 | Broader tag semantics and parser metadata remain outside scope. | Existing tag-query tests, required-tag filtering tests, and nullable parser metadata fixture patterns remain unchanged and adjacent tests stay green. | Changing valid tag syntax, tag normalization, tag ordering, query serialization, required-tag filtering semantics, parent site, users, timestamps, `rating_percent`, cached state, or other parser-derived metadata rejects this local completion claim. | Page constructor scope | `src/wikidot/module/page.py`, adjacent tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `8e3d776 fix(page): validate constructor tags`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_tags tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_non_list_tags tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_non_string_tag_entries -q` failed 6 tests before the fix; malformed non-list and malformed list-entry cases all reported `DID NOT RAISE`, while the 2 valid tag-list cases passed.
- GREEN: the same focused command passed 8 tests after constructor tag validation was added.
- `uv run pytest tests/unit/test_page_constructor.py -q` passed 57 tests.
- `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_search_pages_query.py -q` passed 710 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed.
- `uv run ruff format --check src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- `uv run pytest tests/unit -q` passed 2039 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client/mock typing, invalid test cookie arguments, and existing site test mock typing issues. The changed source file and constructor test module pass pyright together.

## Acceptance Criteria

- `Page(tags=None)`, `Page(tags="tag1 tag2")`, and `Page(tags=("tag1",))` raise `ValueError("tags must be a list")` when every other constructor field is valid.
- `Page(tags=["tag1", 3])`, `Page(tags=[True])`, and `Page(tags=[None])` raise `ValueError("tags list entries must be strings")` when every other constructor field is valid.
- `Page(tags=[])` and `Page(tags=["tag1", "_hidden"])` are accepted and store the list values unchanged.
- Existing parser-created pages, direct page fixtures, query tag serialization, required-tag filtering, metadata/tag workflows, page lookup behavior, page source/revision/file/vote workflows, and site workflows remain green.
- The new tests use unit-level code only and do not validate tag syntax beyond `str`, change query tag semantics, change required-tag filtering, require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Page tag lists affect browser-free discovery, required-tag filtering, metadata writes, and generated workflow records. Query-side and iterator-side tag-list boundaries already reject malformed list entries, so this change is intentionally conservative: it applies the same list-entry integrity contract to direct `Page(...)` construction while also requiring the stored page tag container to be a list.

## Local Evidence

- Local rollout evidence used tags in broad ListPages discovery, required-tag filtering, source collection, metadata/tag workflows, generated ledgers, and local audit rows.
- Existing local drafts covered query tag-list validation and iterator required-tag validation, but did not cover direct `Page(tags=...)` construction.
- Existing unit fixtures use valid tag lists, including empty lists and hidden-tag strings, and adjacent tests prove query and iterator tag behavior remains unchanged.
- This slice does not change parser extraction, page write behavior, query serialization, required-tag filtering semantics, page ID/source/revision/file/vote acquisition, cached state, live Wikidot behavior, tag syntax/range semantics, user/timestamp metadata, `rating_percent`, parent fullname, or parent site validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change rejects malformed tag values rather than coercing them. Empty lists remain valid because pages may have no tags, and hidden-tag strings remain regular string entries at this constructor boundary.
