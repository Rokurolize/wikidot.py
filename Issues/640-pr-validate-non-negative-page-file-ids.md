# PR Draft: Validate Non-Negative Page File IDs

## Summary

`PageFile.id` identifies a concrete page attachment row used by direct file acquisition, batched page-file acquisition, lazy `Page.files`, duplicate cached file reuse, attachment inventories, migration ledgers, publication checks, and collection lookup helpers. Existing local drafts validate `PageFile.id` as a non-boolean integer and generated row IDs as digit-only parser values, but direct constructors still accepted negative integers such as `-1`. That allowed manually constructed fixtures, generated ledgers, or rehydrated records to carry impossible attachment identity state.

This change validates direct `PageFile.id` values as non-negative integers at the constructor boundary. It deliberately preserves `id=0` because prior identity-field drafts avoid stronger positive-ID requirements unless parser or live evidence proves one.

## Outcome

Directly constructed page-file records can no longer store negative attachment IDs, while zero-ID compatibility, malformed direct ID type diagnostics, non-negative size validation, parser-created file row IDs, direct and batched file acquisition, lazy `Page.files`, duplicate cached file reuse, collection lookup, and adjacent page workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free attachment inventories, page asset audits, generated migration ledgers, file ownership checks, publication verification, duplicate page-file cache reuse, direct `PageFileCollection.acquire(page)`, lazy `Page.files`, or local tests that construct `PageFile` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page-file data as a practical workflow surface. [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md) validates malformed generated page-file row IDs and reports them with context. [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md) validates caller-provided loaded-collection lookup ID types. [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md) validates direct `PageFile.id` type, but explicitly limits that slice to scalar/text type integrity. [632-pr-validate-non-negative-page-file-sizes.md](632-pr-validate-non-negative-page-file-sizes.md) validates direct `PageFile.size` as a non-negative byte count.

This slice is not a duplicate of Issues 286, 375, 468, or 632. Issue 286 handles parser-created row IDs, and generated row IDs already remain non-negative through `str.isdigit()`. Issue 375 validates search-key shape, not stored file identity state. Issue 468 rejects booleans, strings, floats, and other malformed direct IDs, but still accepts negative integers. Issue 632 validates byte-size range semantics, not attachment ID range semantics.

## Related Issue / Non-Duplicate Analysis

Builds directly on [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md), and [632-pr-validate-non-negative-page-file-sizes.md](632-pr-validate-non-negative-page-file-sizes.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject direct `PageFile(id=-1)` and `PageFile(id=-100)` with `ValueError("id must be non-negative")`.
- Preserve direct `PageFile(id=0)` as a non-negative identity value.
- Preserve existing malformed-ID diagnostics for non-integers and booleans.
- Preserve existing non-negative `PageFile.size` validation and zero-size compatibility.
- Leave generated page-file row-ID parsing and collection `find(...)` lookup semantics unchanged.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page-file identity state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `PageFile(id=-1)` and `PageFile(id=-100)` must raise `ValueError("id must be non-negative")` when every other file field is valid. |
| R2 | Direct `PageFile(id=0)` must remain valid and store `0`. |
| R3 | Existing malformed direct ID diagnostics must remain stable. |
| R4 | Existing non-negative `PageFile.size` validation and zero-size compatibility must remain stable. |
| R5 | Generated page-file row-ID parsing, direct file acquisition, batched file acquisition, lazy `Page.files`, duplicate cached file reuse, collection lookup, and adjacent page workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private file data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, page-file tests, adjacent page workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct page-file records cannot store negative IDs. | `TestPageFile.test_init_rejects_negative_ids` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after `_validate_file_id(...)` rejected values below zero. | Accepting negative file IDs, coercing them to zero, or deferring failure to parser or lookup code rejects this local completion claim. | PageFile constructor | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | Zero remains valid for direct file IDs. | `TestPageFile.test_init_accepts_zero_id` passed in RED and GREEN runs. | Requiring positive-only file IDs without separate evidence rejects this local completion claim. | Constructor compatibility | `tests/unit/test_page_file.py` |
| R3 | Existing malformed direct ID diagnostics remain stable. | `TestPageFile.test_init_rejects_malformed_ids` passed in the same focused RED and GREEN commands. | Changing `ValueError("id must be an integer")` or accepting booleans, strings, floats, or missing IDs rejects this local completion claim. | PageFile ID type validation | `tests/unit/test_page_file.py` |
| R4 | Existing size range behavior remains stable. | `TestPageFile.test_init_rejects_negative_sizes` and `test_init_allows_zero_size` passed in the same focused RED and GREEN commands. | Regressing `PageFile.size` negative rejection or zero-size compatibility rejects this local completion claim. | PageFile size validation | `tests/unit/test_page_file.py` |
| R5 | Existing page-file and adjacent page workflows remain green. | Page-file coverage passed 101 tests, adjacent page/page-file/page-revision/page-vote/site coverage passed 873 tests, and the full unit suite passed 2891 tests. | Regressing parser diagnostics, file URL normalization, MIME parsing, size parsing, direct acquisition, batch acquisition, cached duplicate reuse, collection lookup, lazy `Page.files`, page revision behavior, page vote behavior, or site/page workflows rejects this local completion claim. | Page-file and adjacent workflows | `tests/unit/test_page_file.py`, `tests/unit/test_page.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw file URLs, attachment names from private pages, response bodies, private page content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, page-file tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `38dcf8b fix(page_file): validate non-negative file ids`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFile::test_init_rejects_malformed_ids tests/unit/test_page_file.py::TestPageFile::test_init_rejects_negative_ids tests/unit/test_page_file.py::TestPageFile::test_init_accepts_zero_id tests/unit/test_page_file.py::TestPageFile::test_init_rejects_negative_sizes tests/unit/test_page_file.py::TestPageFile::test_init_allows_zero_size -q` failed 2 negative file-ID cases before the fix with `DID NOT RAISE`; 8 malformed-ID, zero-ID, negative-size, and zero-size guards stayed green.
- GREEN: the same focused command passed 10 tests after file-ID range validation was added.
- `uv run ruff format src/wikidot/module/page_file.py tests/unit/test_page_file.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_page_file.py -q` passed 101 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 873 tests.
- `uv run pytest tests/unit -q` passed 2891 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageFile(id=-1)` and `PageFile(id=-100)` raise `ValueError("id must be non-negative")`.
- `PageFile(id=0)` remains accepted and stores `0`.
- `PageFile(id=None)`, `True`, `"123"`, and `123.0` continue to raise `ValueError("id must be an integer")`.
- Existing `PageFile(size=-1)` / `size=-1024` rejection and `size=0` compatibility remain unchanged.
- Generated page-file row-ID parsing, parser-side row/name/href/MIME/size diagnostics, direct acquisition, batch acquisition, duplicate cached file reuse, collection lookup, and lazy `Page.files` behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private file data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Attachment IDs are identity metadata for browser-free page-file inventories, duplicate cached file reuse, generated migration ledgers, publication checks, and attachment lookup. Negative IDs can look like valid integer state in direct fixtures or rehydrated records but are not useful attachment identifiers in the current public API surface. Non-negative validation catches that impossible state early while avoiding a stronger positive-only rule.

## Local Evidence

- Local rollout evidence used page-file reads, duplicate file-list reuse, direct page-file acquisition, lazy `Page.files`, attachment inventories, and generated file ledgers that construct or consume `PageFile` records directly.
- Existing local drafts covered generated malformed file row IDs, direct file scalar field types, collection lookup IDs, and non-negative file sizes, but did not cover negative direct file IDs.
- The focused RED failures showed negative direct file IDs were accepted as stored state. The GREEN regressions cover invalid values, zero compatibility, existing malformed type validation, and existing non-negative size validation.
- This slice only validates non-negative direct file-ID semantics. It does not change generated row-ID parsing, file lookup semantics, URL normalization, MIME parsing, size parsing, direct or batched acquisition, cached duplicate behavior, page source/revision/vote behavior, live site behavior, or upstream actions.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, file URLs from private sites, attachment names from private pages, and private site data out of upstream discussion.

## Additional Notes

This change intentionally validates non-negative direct file IDs only. It does not require positive IDs, and it does not change `PageFileCollection.find(...)` lookup semantics because prior local search-key drafts preserved absent integer lookup behavior while generated parser IDs already reject non-digit row IDs.
