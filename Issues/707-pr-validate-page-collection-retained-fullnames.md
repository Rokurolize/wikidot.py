# PR Draft: Validate Page Collection Retained Fullnames

## Summary

`PageCollection.find(fullname)` already validates the caller-provided search key before scanning loaded pages, but the scan still compared each stored `page.fullname` directly. After local fixtures, generated page ledgers, serialized records, or rehydrated `Page` objects mutate a retained page fullname to `None`, booleans, numbers, lists, or other non-string state, lookup treated the corrupted stored page as an ordinary miss instead of surfacing the same deterministic page fullname diagnostic used by direct construction and URL generation.

This change validates each stored page fullname immediately before comparison inside `PageCollection.find(...)`. Malformed retained fullnames now raise `ValueError("fullname must be a string")`, while valid matches and valid string misses remain unchanged.

## Outcome

Loaded page collection lookup can no longer hide corrupted retained page identity as a not-found result. This keeps browser-free page inventories, source collection ledgers, publication checks, migration fixtures, and duplicate-cache workflows honest without changing ListPages parsing, network behavior, or fullname syntax.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `PageCollection.find(...)`, `PageCollection.get_by_fullname(...)`, page search results, page/source collection, generated page inventories, serialized page records, migration checks, or local fixtures that may reconstruct `Page` objects before lookup.

## Current Evidence

Local rollout-backed drafts repeatedly identify page discovery, ListPages parsing, loaded page lookup, source collection, publish verification, duplicate cache reuse, and generated page ledgers as practical read surfaces. Existing drafts [382-pr-validate-page-collection-find-fullname.md](382-pr-validate-page-collection-find-fullname.md), [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md), [533-pr-validate-page-fullname-inputs.md](533-pr-validate-page-fullname-inputs.md), [570-pr-validate-page-url-fullname.md](570-pr-validate-page-url-fullname.md), [664-pr-validate-page-collection-retained-page-id-state.md](664-pr-validate-page-collection-retained-page-id-state.md), and [705-pr-validate-page-collection-site-ownership.md](705-pr-validate-page-collection-site-ownership.md) establish page collection lookup, direct page identity validation, direct lookup/write fullname validation, URL-time retained fullname validation, retained page-ID validation, and collection site ownership as active operational boundaries.

This slice is not a duplicate of those drafts. Issue 382 validates the caller-provided `PageCollection.find(fullname=...)` search key before scanning pages, not each stored row's retained `page.fullname`. Issue 481 validates direct `Page(...)` construction but cannot cover a valid page whose fullname is corrupted after construction. Issue 533 validates direct lookup/write fullname inputs, not stored rows inside an already loaded collection. Issue 570 validates mutated `page.fullname` only when `Page.get_url()` is called. Issue 664 validates retained page IDs in collection page-ID acquisition, and Issue 705 validates page-site ownership in collection construction; neither validates retained page fullnames during local lookup.

No upstream issue was filed from this local workspace.

## Changes

- Validate stored `page.fullname` values inside `PageCollection.find(...)` before comparing them with the caller's validated search key.
- Reject malformed retained fullnames such as `None`, `True`, `123`, `1.0`, and `[]` with `ValueError("fullname must be a string")`.
- Preserve valid `collection.find("test-page")` matches and valid absent string behavior.
- Preserve caller search-key validation order, `PageCollection.get_by_fullname(...)` fallback behavior, ListPages parsing, page ID/source/revision/vote/file acquisition, page writes, and live Wikidot behavior.

## Type Of Change

- Input validation
- Retained page identity hardening
- Loaded collection lookup safety
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageCollection.find("test-page")` must reject malformed retained stored `page.fullname` values such as `None`, `True`, `123`, `1.0`, and `[]` with `ValueError("fullname must be a string")` before treating the row as a miss. |
| R2 | Caller-provided malformed search keys must still raise `ValueError("fullname must be a string")` before stored rows are inspected. |
| R3 | Valid lookup for matching string fullnames must still return the stored `Page` object. |
| R4 | Valid not-found lookup for absent string fullnames must still return `None`. |
| R5 | Existing page collection, page lookup, ListPages parsing, source/revision/file/vote acquisition, page write, and adjacent site workflows must remain compatible. |
| R6 | Focused RED/GREEN, page collection tests, page module tests, adjacent page/site/source/revision/file/vote/search tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Corrupted retained fullnames fail at the loaded collection lookup boundary. | `test_find_rejects_malformed_retained_page_fullnames` failed RED for five malformed retained values with `DID NOT RAISE`, then passed GREEN after stored row validation was added. | Returning `None`, coercing stored values with `str(...)`, comparing malformed state, or hiding corrupted retained identity as a not-found miss rejects this local completion claim. | `PageCollection.find(...)` stored row scan | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Caller key validation order stays intact. | Focused GREEN included `test_find_rejects_non_string_fullnames`, which still passed for `None`, `True`, `123`, and `1.0`. | Inspecting stored rows before rejecting a malformed caller key or changing the diagnostic rejects this local completion claim. | `PageCollection.find(...)` caller preflight | `tests/unit/test_page.py` |
| R3 | Existing valid matches keep object identity. | Focused GREEN included `test_find_existing_page`, which still returns the stored page with fullname `test-page`. | Returning a copy, changing the selected object, rejecting valid strings, or matching a different field rejects this local completion claim. | Page collection lookup | `tests/unit/test_page.py` |
| R4 | Existing valid misses stay misses. | Focused GREEN included `test_find_nonexistent_page`, which still returns `None` for absent string fullnames. | Raising for absent valid strings or changing not-found behavior rejects this local completion claim. | Page collection lookup | `tests/unit/test_page.py` |
| R5 | Existing page and adjacent workflows remain green. | `TestPageCollectionInit` passed 30 tests, `tests/unit/test_page.py` passed 382 tests, adjacent page/site/source/revision/file/vote/search coverage passed 1350 tests, and full unit coverage passed 3549 tests. | Regressing `get_by_fullname(...)`, ListPages parsing, search pagination, source iteration, page ID/source/revision/file/vote acquisition, page writes, page constructors, or site accessors rejects this local completion claim. | Page and adjacent workflows | `tests/unit` |
| R6 | Repository quality gates pass in the local dependency environment. | Full ruff check passed, full ruff format check passed, full mypy passed with no issues in 87 source files, pyright passed with 0 errors, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic local fixture mutation and unit-level mocks only, and this draft avoids raw rollout paths and private payloads. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private page source, private site data, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `e3ded45 fix(page): validate collection retained fullnames`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionInit::test_find_rejects_malformed_retained_page_fullnames -q` failed 5 parameterized cases before the fix because malformed retained fullnames did not raise.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageCollectionInit::test_find_rejects_malformed_retained_page_fullnames tests/unit/test_page.py::TestPageCollectionInit::test_find_rejects_non_string_fullnames tests/unit/test_page.py::TestPageCollectionInit::test_find_existing_page tests/unit/test_page.py::TestPageCollectionInit::test_find_nonexistent_page -q` passed 11 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionInit -q` passed 30 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 382 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_constructor.py tests/unit/test_search_pages_query.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py -q` passed 1350 tests.
- `uv run mypy src/wikidot/module/page.py tests/unit/test_page.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_page.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 3549 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageCollection(mock_site, [page_with_mutated_fullname]).find("test-page")` raises `ValueError("fullname must be a string")` when the stored page fullname is `None`, `True`, `123`, `1.0`, or `[]`.
- `collection.find(None)`, `collection.find(True)`, `collection.find(123)`, and `collection.find(1.0)` still raise `ValueError("fullname must be a string")` before scanning stored pages.
- Valid string lookup still returns the stored matching `Page`.
- Valid absent string lookup still returns `None`.
- Existing ListPages parsing, direct page lookup fallback, search pagination, source iteration, page ID/source/revision/file/vote acquisition, duplicate cache reuse, page write behavior, and adjacent site workflows remain green.
- The new tests use unit-level synthetic mutation only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A corrupted stored row that used to be ignored as a miss now raises. Mitigation: `PageCollection` stores `Page` objects whose `fullname` is already required to be a string at construction and URL generation; treating later corruption as local state damage is consistent with retained-ID and retained-owner validation slices.
- Risk: The diagnostic could be confused with caller search-key validation. Mitigation: the caller key is still validated first, and the same stable `ValueError("fullname must be a string")` diagnostic matches existing page identity validation.
- Risk: Extra validation adds per-row work during lookup. Mitigation: the operation is already a linear local scan over loaded pages, and the added type check is constant-time with no network or parser behavior changes.

## Out Of Scope

Changing fullname syntax, rejecting blank fullnames, normalizing or coercing stored page names, changing `Page(...)` construction, changing `Page.get_url()`, changing ListPages parsing, changing `PageCollection.get_by_fullname(...)` request strategy, changing live Wikidot behavior, pushing changes, opening upstream Issues, and opening upstream PRs are outside this slice.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used `PageCollection`, ListPages search, direct page lookup, page source collection, publish checks, and generated page/source ledgers.
- Existing local drafts covered caller lookup keys, direct page identity construction, direct lookup/write fullname inputs, URL-time retained fullname validation, retained page IDs, and collection site ownership, but did not validate retained stored fullnames during `PageCollection.find(...)`.
- The focused RED failure showed a loaded collection with a corrupted retained page fullname returned normally instead of producing a deterministic page identity diagnostic.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private page content, private site data, and source text from real sites out of upstream discussion.
