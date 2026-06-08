# PR Draft: Validate Non-Negative Page File Sizes

## Summary

`PageFile.size` represents attachment size in bytes for browser-free page-file inventories, generated asset ledgers, publication checks, migration audits, lazy `Page.files`, direct file acquisition, batch file acquisition, and collection lookup helpers. Parser-created page files already come from unsigned size text such as `500 Bytes`, `1.5 kB`, or `2 MB`, and malformed size text fails at the row parser boundary. The direct `PageFile(...)` constructor, however, still accepted negative integer sizes such as `-1`, allowing manually constructed fixtures, generated ledgers, or rehydrated records to carry an impossible byte count.

This change keeps the existing non-boolean integer validation for `PageFile.size`, then rejects negative integers with `ValueError("size must be non-negative")`. Valid zero-byte attachments remain accepted, and existing parser behavior, URL normalization, MIME parsing, file-name validation, direct and batched acquisition, duplicate cached file reuse, lazy `Page.files`, and adjacent page workflows remain unchanged.

## Outcome

Directly constructed `PageFile` records can no longer store negative attachment sizes, while legitimate zero-byte files and all valid positive sizes remain supported.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free attachment inventories, generated file ledgers, migration audits, publication checks, duplicate page-file cache reuse, direct `PageFileCollection.acquire(page)`, lazy `Page.files`, or local tests that construct `PageFile` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page-file data as a practical workflow surface. Existing drafts [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [224-pr-page-file-batch-response-body-context.md](224-pr-page-file-batch-response-body-context.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [383-pr-validate-page-file-find-by-name.md](383-pr-validate-page-file-find-by-name.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md), [471-pr-validate-page-file-collection-page-field.md](471-pr-validate-page-file-collection-page-field.md), [493-pr-validate-page-constructor-files-cache.md](493-pr-validate-page-constructor-files-cache.md), [536-pr-preserve-empty-page-file-parent.md](536-pr-preserve-empty-page-file-parent.md), [589-pr-validate-page-file-collection-page-ownership.md](589-pr-validate-page-file-collection-page-ownership.md), [599-pr-validate-page-files-cache-ownership.md](599-pr-validate-page-files-cache-ownership.md), and [630-pr-validate-blank-page-file-names.md](630-pr-validate-blank-page-file-names.md) establish page attachments, parser diagnostics, response diagnostics, cache reuse, lookup validation, direct constructor integrity, and ownership hardening as active operational boundaries.

This slice is not a duplicate of Issue 275. Issue 275 validates malformed size text on parser-created attachment rows and preserves `_parse_size("unknown") == 0` for direct utility callers; it does not cover direct `PageFile(size=-1)` construction after an integer value is already present. This slice is also not a duplicate of Issue 468. Issue 468 validates `PageFile.size` type and explicitly does not require positive sizes; this follow-up still does not require positive sizes because `size=0` remains valid, but it rejects negative byte counts as impossible attachment state.

## Related Issue / Non-Duplicate Analysis

Builds directly on [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md), and [630-pr-validate-blank-page-file-names.md](630-pr-validate-blank-page-file-names.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a non-negative check to `PageFile.size` validation after the existing non-boolean integer check.
- Reject `PageFile(size=-1)` and `PageFile(size=-1024)` with `ValueError("size must be non-negative")`.
- Preserve `PageFile(size=0)` for legitimate zero-byte attachments.
- Preserve the existing `ValueError("size must be an integer")` diagnostic for missing, boolean, string, float, and other non-integer sizes.
- Preserve existing parser-created file behavior, direct file acquisition, batch file acquisition, lazy `Page.files`, duplicate cached file reuse, collection lookup, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page-file state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageFile(size=-1)` and `PageFile(size=-1024)` must raise `ValueError("size must be non-negative")` when every other file field is valid. |
| R2 | `PageFile(size=0)` must remain valid and store `0`. |
| R3 | Existing malformed size-type diagnostics must remain `ValueError("size must be an integer")` for `None`, booleans, strings, floats, and other non-integers. |
| R4 | Parser-created page files, direct file acquisition, batched page-file acquisition, file lookup, lazy `Page.files`, duplicate cached file reuse, and adjacent page workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, page-file tests, adjacent page workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative direct sizes fail at the public dataclass boundary. | `TestPageFile.test_init_rejects_negative_sizes` failed RED for `-1` and `-1024` with `DID NOT RAISE`, then passed GREEN after `_validate_file_size(...)` rejected negative integers. | Accepting negative byte counts, coercing them to zero, or deferring failure to a parser/acquisition path rejects this local completion claim. | PageFile constructor | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | Zero-byte files remain valid. | `TestPageFile.test_init_allows_zero_size` passed in both RED and GREEN focused runs and asserts `file.size == 0`. | Rejecting `size=0`, treating zero as missing, or requiring positive sizes rejects this local completion claim. | PageFile constructor compatibility | `tests/unit/test_page_file.py` |
| R3 | Existing malformed-size type diagnostics remain stable. | `TestPageFile.test_init_rejects_malformed_sizes` passed in the focused RED and GREEN commands with the existing `size must be an integer` diagnostic. | Changing non-integer diagnostics, accepting booleans as integers, or coercing string/float sizes rejects this local completion claim. | PageFile constructor | `tests/unit/test_page_file.py` |
| R4 | Existing page-file and adjacent page workflows remain green. | `tests/unit/test_page_file.py` passed 98 tests, adjacent page/page-file/page-revision/page-votes/site coverage passed 857 tests, and the full unit suite passed 2848 tests. | Regressing parser diagnostics, file URL normalization, MIME parsing, size parsing, direct acquisition, batch acquisition, cached duplicate reuse, collection lookup, lazy `Page.files`, page revision behavior, page vote behavior, or site/page workflows rejects this local completion claim. | Page-file and adjacent workflows | `tests/unit/test_page.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic `Page` and `PageFile` objects only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, file URLs from private sites, attachment names from private pages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `10f0f73 fix(page_file): validate non-negative file sizes`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFile::test_init_rejects_negative_sizes tests/unit/test_page_file.py::TestPageFile::test_init_allows_zero_size tests/unit/test_page_file.py::TestPageFile::test_init_rejects_malformed_sizes -q` failed 2 negative-size cases before the fix with `DID NOT RAISE`; the zero-size and malformed-size type checks stayed green.
- GREEN: the same focused command passed 7 tests after `_validate_file_size(...)` rejected negative integers.
- `uv run pytest tests/unit/test_page_file.py -q` passed 98 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 857 tests.
- `uv run ruff format src/wikidot/module/page_file.py tests/unit/test_page_file.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed.
- `uv run pytest tests/unit -q` passed 2848 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageFile(size=-1)` and `PageFile(size=-1024)` raise `ValueError("size must be non-negative")`.
- `PageFile(size=0)` remains valid and stores `0`.
- `PageFile(size=None)`, `True`, `"1024"`, and `1024.0` continue to raise `ValueError("size must be an integer")`.
- Valid positive integer sizes remain valid.
- Existing parser-side row/name/href/MIME/size diagnostics, direct acquisition, batch acquisition, duplicate cached file reuse, collection lookup, and lazy `Page.files` behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Attachment byte sizes cannot be negative. Parser-created `PageFile` records already come from unsigned size text, and parser-side malformed text is already surfaced with context. Constructor validation keeps impossible negative byte counts out of direct fixtures, rehydrated records, generated ledgers, and downstream audit tooling without requiring positive sizes or changing valid zero-byte attachment behavior.

## Local Evidence

- Local rollout evidence used browser-free page-file reads, duplicate file-list reuse, attachment inventory checks, direct page-file acquisition, lazy `Page.files`, and generated file ledgers that construct or consume `PageFile` records directly.
- Existing local drafts covered page-file acquisition, retry behavior, duplicate request deduplication, parse reuse, cached duplicate reuse, parser field diagnostics, response-body diagnostics, collection initialization validation, ID/name lookup validation, direct parent-page validation, scalar type validation, and blank name validation, but did not cover direct negative integer sizes.
- The focused RED failures showed negative constructor sizes were accepted as dataclass state. The GREEN regressions cover negative values, zero compatibility, and pre-existing malformed type validation.
- This slice only validates non-negative direct page-file sizes. It does not change direct file acquisition, collection-level file acquisition, parser selectors, file URL normalization, MIME parsing, size text parsing, cached duplicate behavior, `find(...)`, `find_by_name(...)`, page source/revision/vote behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, file URLs from private sites, attachment names from private pages, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates semantic impossibility, not display or transport metadata. It does not require positive sizes, validate URL syntax, validate MIME syntax, coerce strings to integers, infer file contents, compare file metadata against parent page metadata, or change live client authentication; those are separate parser, normalization, and workflow concerns.
