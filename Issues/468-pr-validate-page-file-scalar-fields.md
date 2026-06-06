# PR Draft: Validate Page File Scalar Fields

## Summary

`PageFile` records carry attachment identity, filename, download URL, MIME type, and byte size for browser-free page-file inventories, generated attachment ledgers, duplicate file-list cache reuse, direct file acquisition, lazy `Page.files`, migration audits, publication checks, and file lookup helpers. Earlier local slices validated page-file parser diagnostics, direct file acquisition responses, batch response shape, collection entries, collection initialization, lookup keys, duplicate cache reuse, and the direct parent `page` field, but the public `PageFile(...)` constructor still accepted malformed direct `id`, `name`, `url`, `mime_type`, and `size` values such as `None`, booleans, strings where integers are required, integers where strings are required, floats, and lists.

This change validates direct `PageFile.id`, `PageFile.name`, `PageFile.url`, `PageFile.mime_type`, and `PageFile.size` values at initialization. `id` and `size` now accept only non-boolean integers. `name`, `url`, and `mime_type` now accept only strings. Malformed values raise stable diagnostics: `ValueError("id must be an integer")`, `ValueError("name must be a string")`, `ValueError("url must be a string")`, `ValueError("mime_type must be a string")`, and `ValueError("size must be an integer")`. Existing page-file parsing, parser-side malformed row/name/href/MIME/size diagnostics, direct and batch acquisition, lazy `Page.files`, duplicate cached file reuse, collection lookup, and adjacent page workflows remain unchanged.

## Outcome

Callers cannot silently construct attachment records with malformed scalar or text fields, while parser-created, fixture-created, and manually created valid page files continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free attachment inventories, page asset audits, generated migration ledgers, file ownership checks, publication verification, duplicate page-file cache reuse, direct `PageFileCollection.acquire(page)`, lazy `Page.files`, or local tests that construct `PageFile` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page-file data as a practical workflow surface. Existing drafts [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [224-pr-page-file-batch-response-body-context.md](224-pr-page-file-batch-response-body-context.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [383-pr-validate-page-file-find-by-name.md](383-pr-validate-page-file-find-by-name.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), and [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md) establish file fetches, parser diagnostics, response diagnostics, duplicate cache reuse, lookup validation, collection constructor integrity, and direct parent-page constructor integrity as active operational boundaries.

Those prior slices are not duplicates. Issues 274, 275, 276, 277, and 286 validate parser-side malformed MIME, size, href, name, and row-ID data before parser-created files are built. Issues 375 and 383 validate collection lookup keys. Issue 420 validates collection initialization. Issue 443 validates only the parent `page` field. None validates direct `PageFile(id=..., name=..., url=..., mime_type=..., size=...)` construction before malformed scalar/text state becomes stored dataclass state in manually constructed files, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [383-pr-validate-page-file-find-by-name.md](383-pr-validate-page-file-find-by-name.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), and [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PageFile.id` validation at dataclass initialization.
- Add `PageFile.name`, `PageFile.url`, and `PageFile.mime_type` validation at dataclass initialization.
- Add `PageFile.size` validation at dataclass initialization.
- Reject boolean values for integer fields even though `bool` subclasses `int`.
- Preserve existing parser-created page files, direct file acquisition, batch file acquisition, lazy `Page.files`, duplicate cached file reuse, collection lookup, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page-file scalar/text state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageFile(id=None)`, `True`, `"123"`, and `123.0` must raise `ValueError("id must be an integer")` when every other file field is valid. |
| R2 | `PageFile(name=...)`, `PageFile(url=...)`, and `PageFile(mime_type=...)` must reject `None`, booleans, integers, and lists with the matching `"<field> must be a string"` diagnostic when every other file field is valid. |
| R3 | `PageFile(size=None)`, `True`, `"1024"`, and `1024.0` must raise `ValueError("size must be an integer")` when every other file field is valid. |
| R4 | Valid non-boolean integer IDs/sizes and string text fields must remain valid and preserve existing file fields. |
| R5 | Existing parser-side row/name/href/MIME/size diagnostics, direct file acquisition, batch file acquisition, lazy `Page.files`, duplicate cached file reuse, collection lookup, and adjacent page workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, page-file tests, adjacent page workflow tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor IDs fail at the public dataclass boundary. | `TestPageFile.test_init_rejects_malformed_ids` failed RED for 4 malformed values because the constructor did not raise, then passed GREEN after ID validation was added. | Accepting missing values, booleans, numeric strings, floats, arbitrary objects, or emitting attachment records with non-integer ID state rejects this local completion claim. | PageFile constructor | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | Malformed constructor text fields fail at the public dataclass boundary. | `TestPageFile.test_init_rejects_malformed_text_fields` failed RED for 12 malformed field/value combinations because the constructor did not raise, then passed GREEN after text-field validation was added. | Accepting missing values, booleans, integers, lists, arbitrary objects, or emitting attachment records with non-string `name`, `url`, or `mime_type` state rejects this local completion claim. | PageFile constructor | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R3 | Malformed constructor sizes fail at the public dataclass boundary. | `TestPageFile.test_init_rejects_malformed_sizes` failed RED for 4 malformed values because the constructor did not raise, then passed GREEN after size validation was added. | Accepting missing values, booleans, numeric strings, floats, arbitrary objects, or emitting attachment records with non-integer size state rejects this local completion claim. | PageFile constructor | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R4 | Valid file field semantics stay green. | Existing page-file unit tests passed after the new helper constructed valid `PageFile` rows with the same field values used by prior tests. | Rejecting valid integer IDs/sizes, rejecting empty strings used by existing valid fixtures, coercing text, coercing size, or changing stored file fields rejects this local completion claim. | Parser-created and manually created files | `tests/unit/test_page_file.py` |
| R5 | Existing adjacent page-file workflows remain green. | `tests/unit/test_page_file.py` passed 78 tests, adjacent page workflow tests passed 696 tests, and full unit tests passed 1880 tests. | Regressing parser diagnostics, file URL normalization, MIME parsing, size parsing, direct acquisition, batch acquisition, cached duplicate reuse, collection lookup, lazy `Page.files`, page revision behavior, page vote behavior, or site/page workflows rejects this local completion claim. | Page-file and adjacent page workflows | `tests/unit/test_page.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, file URLs from private sites, attachment names from private pages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `a5d7784 fix(page_file): validate file scalar fields`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFile::test_init_rejects_malformed_ids tests/unit/test_page_file.py::TestPageFile::test_init_rejects_malformed_text_fields tests/unit/test_page_file.py::TestPageFile::test_init_rejects_malformed_sizes -q` failed 20 tests before the fix; every malformed `id`, `name`, `url`, `mime_type`, or `size` value reported `DID NOT RAISE`.
- GREEN: the same focused command passed 20 tests after `PageFile` scalar/text validation was added.
- `uv run pytest tests/unit/test_page_file.py -q` passed 78 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 696 tests.
- `uv run pytest tests/unit -q` passed 1880 tests.
- `uv run ruff check src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed.
- `uv run ruff format src/wikidot/module/page_file.py tests/unit/test_page_file.py` left 2 files unchanged.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 82 files already formatted.
- `uv run mypy src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed with no issues in 2 source files.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `uv run pyright src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test page fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client mock typing, invalid test cookie arguments, and site test mock typing issues. The changed source file and changed page-file test file pass pyright together.

## Acceptance Criteria

- `PageFile(id=None)`, `True`, `"123"`, and `123.0` raise `ValueError("id must be an integer")`.
- `PageFile(name=None)`, `True`, `123`, and `[]` raise `ValueError("name must be a string")`.
- `PageFile(url=None)`, `True`, `123`, and `[]` raise `ValueError("url must be a string")`.
- `PageFile(mime_type=None)`, `True`, `123`, and `[]` raise `ValueError("mime_type must be a string")`.
- `PageFile(size=None)`, `True`, `"1024"`, and `1024.0` raise `ValueError("size must be an integer")`.
- Valid non-boolean integer IDs/sizes and string names, URLs, and MIME types remain valid.
- Existing parser-side row/name/href/MIME/size diagnostics, direct acquisition, batch acquisition, duplicate cached file reuse, collection lookup, and lazy `Page.files` behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageFile.id`, `PageFile.name`, `PageFile.url`, `PageFile.mime_type`, and `PageFile.size` are the core attachment fields used by generated file inventories, migration ledgers, publication checks, page asset audits, and collection lookup. Parser paths already normalize or diagnose malformed row data before constructing files. Constructor validation keeps malformed direct file records out of fixtures, rehydrated records, generated ledgers, and downstream audit tooling while preserving parser and caller paths that construct valid files.

## Local Evidence

- Local rollout evidence used browser-free page-file reads, duplicate file-list reuse, attachment inventory checks, direct page-file acquisition, lazy `Page.files`, and generated file ledgers that construct or consume `PageFile` records directly.
- Existing local drafts covered page-file acquisition, retry behavior, duplicate request deduplication, parse reuse, cached duplicate file reuse, parser field diagnostics, response-body diagnostics, collection initialization validation, ID/name lookup validation, and direct parent-page validation, but did not cover direct `PageFile(id=..., name=..., url=..., mime_type=..., size=...)` construction.
- The focused RED failures showed invalid constructor scalar/text fields were accepted as dataclass state. The GREEN regressions cover missing, boolean, string, float, integer, and list values according to each field's expected type.
- This slice only validates page-file scalar/text constructor input. It does not change direct file acquisition, collection-level file acquisition, parser selectors, file URL normalization, MIME parsing, size parsing, cached duplicate behavior, `find(...)`, `find_by_name(...)`, page source/revision/vote behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, file URLs from private sites, attachment names from private pages, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates type only. It does not require non-empty strings, validate URL syntax, validate MIME syntax, require positive sizes, coerce strings to integers, compare file metadata against parent page metadata, or change live client authentication; those are separate parser, normalization, and workflow concerns.
