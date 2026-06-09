# PR Draft: Validate Page File Collection Retained Names

## Summary

`PageFileCollection.find_by_name(name)` already validates the caller-provided lookup name before scanning loaded files, but the scan compared each retained `file.name` directly. If a local fixture, generated attachment ledger, serialized record, cache handoff, or rehydrated `PageFile` object mutates a retained file name to `None`, booleans, numbers, lists, empty strings, or whitespace-only strings after construction, lookup treated the corrupted stored row as an ordinary miss instead of surfacing the deterministic file-name diagnostics used by direct `PageFile` construction.

This change validates each stored `file.name` immediately before comparison inside `PageFileCollection.find_by_name(...)`. Malformed retained names now raise `ValueError("name must be a string")`, blank retained names raise `ValueError("name must not be empty")`, and valid matches or valid string misses remain unchanged.

## Outcome

Loaded page-file lookup can no longer hide corrupted retained attachment identity as a not-found result. This keeps browser-free attachment inventories, page file acquisition caches, generated file ledgers, migration fixtures, publication checks, and duplicate-cache workflows honest without changing file-list parsing, network behavior, or file-name syntax.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `PageFileCollection.find_by_name(...)`, `Page.files`, page attachment inventories, generated file ledgers, migration checks, serialized `PageFile` records, local fixtures, or duplicate-cache workflows that may reconstruct `PageFile` objects before lookup.

## Current Evidence

Local rollout-backed drafts repeatedly identify page attachment inventories, page file parsing, direct page-file acquisition, lazy `Page.files` loading, generated migration/publication ledgers, and duplicate-cache reuse as practical read surfaces. Existing drafts [383-pr-validate-page-file-find-by-name.md](383-pr-validate-page-file-find-by-name.md), [630-pr-validate-blank-page-file-names.md](630-pr-validate-blank-page-file-names.md), [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md), [671-pr-validate-page-file-collection-retained-id-state.md](671-pr-validate-page-file-collection-retained-id-state.md), [589-pr-validate-page-file-collection-page-ownership.md](589-pr-validate-page-file-collection-page-ownership.md), [536-pr-preserve-empty-page-file-parent.md](536-pr-preserve-empty-page-file-parent.md), and [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md) establish caller lookup-key validation, direct blank-name validation, direct scalar-field validation, retained file-ID validation, page-file ownership, empty collection parent preservation, and collection initialization as active operational boundaries.

This slice is not a duplicate of those drafts. Issue 383 validates the caller-provided `find_by_name(name=...)` key before scanning stored files, not each retained row's `file.name`. Issue 630 validates blank direct `PageFile.name` and blank search names, not a valid file whose retained name is corrupted after construction. Issue 468 validates direct constructor scalar fields but cannot cover post-construction mutation. Issue 671 validates retained file IDs during `PageFileCollection.find(id)`, not retained names during `find_by_name(...)`. Issues 589, 536, and 420 cover collection ownership/parent/initialization boundaries, not retained name comparison.

No upstream issue was filed from this local workspace.

## Changes

- Validate stored `file.name` values inside `PageFileCollection.find_by_name(...)` before comparing them with the caller's validated search key.
- Reject malformed retained names such as `None`, `True`, `123`, `1.0`, and `[]` with `ValueError("name must be a string")`.
- Reject blank retained names such as `""` and `"   "` with `ValueError("name must not be empty")`.
- Preserve valid `collection.find_by_name("document.pdf")` matches and valid absent string behavior.
- Preserve caller search-key validation order, `PageFileCollection.find(id)`, file-list parsing, page/file ownership checks, lazy `Page.files` acquisition, and live Wikidot behavior.

## Type Of Change

- Input validation
- Retained page-file identity hardening
- Loaded attachment lookup safety
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageFileCollection.find_by_name("document.pdf")` must reject malformed retained stored `file.name` values such as `None`, `True`, `123`, `1.0`, and `[]` with `ValueError("name must be a string")` before treating the row as a miss. |
| R2 | `PageFileCollection.find_by_name("document.pdf")` must reject blank retained stored `file.name` values such as `""` and `"   "` with `ValueError("name must not be empty")` before treating the row as a miss. |
| R3 | Caller-provided malformed or blank search keys must still raise the existing diagnostics before stored rows are inspected. |
| R4 | Valid lookup for matching string names must still return the stored `PageFile` object. |
| R5 | Valid not-found lookup for absent string names must still return `None`. |
| R6 | Existing page-file collection, page-file parsing/acquisition, page, page-source, page-revision, page-vote, and adjacent site workflows must remain compatible. |
| R7 | Focused RED/GREEN, page-file tests, adjacent page/site/source/revision/vote coverage, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming local implementation complete. |
| R8 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Corrupted retained non-string file names fail at the loaded collection lookup boundary. | `test_find_by_name_rejects_malformed_retained_file_names` failed RED for five malformed retained values with `DID NOT RAISE`, then passed GREEN after stored row validation was added. | Returning `None`, coercing stored values with `str(...)`, comparing malformed state, or hiding corrupted retained identity as a not-found miss rejects this local completion claim. | `PageFileCollection.find_by_name(...)` stored row scan | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | Corrupted retained blank file names fail at the loaded collection lookup boundary. | `test_find_by_name_rejects_blank_retained_file_names` failed RED for two blank retained values with `DID NOT RAISE`, then passed GREEN after stored row validation was added. | Returning `None`, trimming and accepting empty state, or hiding blank retained identity as a not-found miss rejects this local completion claim. | `PageFileCollection.find_by_name(...)` stored row scan | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R3 | Caller key validation order stays intact. | Focused GREEN included `test_find_by_name_rejects_non_string_names` and `test_find_by_name_rejects_blank_names`. | Inspecting stored rows before rejecting a malformed caller key or changing the diagnostics rejects this local completion claim. | `PageFileCollection.find_by_name(...)` caller preflight | `tests/unit/test_page_file.py` |
| R4 | Existing valid matches keep object identity. | Focused GREEN included `test_find_by_name_existing`, which still returns the stored `PageFile` named `test.txt`. | Returning a copy, changing the selected object, rejecting valid strings, or matching a different field rejects this local completion claim. | Page-file collection lookup | `tests/unit/test_page_file.py` |
| R5 | Existing valid misses stay misses. | Focused GREEN included `test_find_by_name_nonexistent`, which still returns `None` for absent string names. | Raising for absent valid strings or changing not-found behavior rejects this local completion claim. | Page-file collection lookup | `tests/unit/test_page_file.py` |
| R6 | Existing page-file and adjacent workflows remain green. | `tests/unit/test_page_file.py` passed 116 tests, adjacent page/site/source/revision/vote coverage passed 1307 tests, and full unit coverage passed 3556 tests. | Regressing file parsing, direct file acquisition, lazy `Page.files`, page/source/revision/vote workflows, page constructors, or site accessors rejects this local completion claim. | Page-file and adjacent workflows | `tests/unit` |
| R7 | Repository quality gates pass in the local dependency environment. | Full ruff check passed, full ruff format check passed, full mypy passed with no issues in 87 source files, pyright passed with 0 errors, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R8 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic local fixture mutation and unit-level mocks only, and this draft avoids raw rollout paths and private payloads. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private page source, private site data, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `e83d094 fix(page_file): validate retained file names`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollection::test_find_by_name_rejects_malformed_retained_file_names tests/unit/test_page_file.py::TestPageFileCollection::test_find_by_name_rejects_blank_retained_file_names -q` failed 7 parameterized cases before the fix because malformed and blank retained file names did not raise.
- GREEN focused: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollection::test_find_by_name_rejects_malformed_retained_file_names tests/unit/test_page_file.py::TestPageFileCollection::test_find_by_name_rejects_blank_retained_file_names tests/unit/test_page_file.py::TestPageFileCollection::test_find_by_name_rejects_non_string_names tests/unit/test_page_file.py::TestPageFileCollection::test_find_by_name_rejects_blank_names tests/unit/test_page_file.py::TestPageFileCollection::test_find_by_name_existing tests/unit/test_page_file.py::TestPageFileCollection::test_find_by_name_nonexistent -q` passed 15 tests.
- `uv run pytest tests/unit/test_page_file.py -q` passed 116 tests.
- `uv run pytest tests/unit/test_page_file.py tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1307 tests.
- `uv run ruff format src/wikidot/module/page_file.py tests/unit/test_page_file.py --check` passed with 2 files already formatted.
- `uv run ruff check src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed.
- `uv run mypy src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 3556 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageFileCollection(page, [file_with_mutated_name]).find_by_name("document.pdf")` raises `ValueError("name must be a string")` when the retained file name is `None`, `True`, `123`, `1.0`, or `[]`.
- `PageFileCollection(page, [file_with_mutated_name]).find_by_name("document.pdf")` raises `ValueError("name must not be empty")` when the retained file name is `""` or `"   "`.
- `collection.find_by_name(None)`, `collection.find_by_name(True)`, `collection.find_by_name(123)`, and `collection.find_by_name(1.0)` still raise `ValueError("name must be a string")` before scanning stored files.
- `collection.find_by_name("")` and `collection.find_by_name("   ")` still raise `ValueError("name must not be empty")` before scanning stored files.
- Valid string lookup still returns the stored matching `PageFile`.
- Valid absent string lookup still returns `None`.
- Existing file-list parsing, direct page-file acquisition, lazy `Page.files`, page/source/revision/vote workflows, page constructors, and adjacent site workflows remain green.
- The new tests use unit-level synthetic mutation only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A corrupted stored row that used to be ignored as a miss now raises. Mitigation: `PageFileCollection` stores `PageFile` objects whose `name` is already required to be a non-empty string at construction and lookup; treating later corruption as local state damage is consistent with retained-ID and retained-owner validation slices.
- Risk: The diagnostic could be confused with caller search-key validation. Mitigation: the caller key is still validated first, and the same stable diagnostics match existing page-file identity validation.
- Risk: Extra validation adds per-row work during lookup. Mitigation: the operation is already a linear local scan over loaded files, and the added string/blank check is constant-time with no network or parser behavior changes.

## Out Of Scope

Changing file-name syntax, normalizing or coercing stored names, changing `PageFile(...)` construction, changing page-file parsing, changing lazy `Page.files` acquisition, changing `PageFileCollection.find(id)`, changing direct file acquisition, changing live Wikidot behavior, pushing changes, opening upstream Issues, and opening upstream PRs are outside this slice.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used page attachment inventories, direct page-file acquisition, lazy `Page.files`, generated file ledgers, publication checks, migration fixtures, and duplicate-cache reuse.
- Existing local drafts covered caller lookup keys, direct blank-name validation, direct scalar-field validation, retained file IDs, collection ownership, empty parent preservation, and collection initialization, but did not validate retained stored names during `PageFileCollection.find_by_name(...)`.
- The focused RED failure showed a loaded collection with corrupted retained file names returned normally instead of producing deterministic page-file identity diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private page content, private site data, and source text from real sites out of upstream discussion.
