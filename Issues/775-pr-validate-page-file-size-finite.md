# PR Draft: Validate Page File Size Finite Values

## Summary

`PageFileCollection.acquire(page)` parses generated `files/PageFilesModule` rows into `PageFile` records for attachment inventories, file lookup, page audit ledgers, and publish-adjacent verification. Existing parser hardening reports ordinary malformed size text such as `unknown` with site, page, file, field, and value context. One numeric boundary remained: `_parse_size_value(...)` matched very large decimal text, converted it through `float(...)`, and then called `int(value * multiplier)`. A generated size value large enough to become `inf` leaked `OverflowError: cannot convert float infinity to integer` instead of the existing contextual page-file size diagnostic.

This change rejects non-finite parsed byte counts before integer conversion. Valid generated sizes such as `500 Bytes`, `1.5 kB`, `2 MB`, and `1 GB` keep their existing byte values, while overflow-sized generated text now follows the same `Page file size is malformed ...` path as other unparseable size cells.

## Outcome

Page file acquisition no longer exposes a low-level Python numeric overflow for generated attachment-size metadata. Oversized file-size cells fail at the parser boundary with the existing page/file context and without constructing a `PageFile` from non-finite numeric state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page attachment inventories, file audits, generated migration ledgers, publication checks, duplicate cached file reuse, lazy `Page.files`, or local fixtures derived from `files/PageFilesModule` output.

## Current Evidence

Local rollout-backed drafts repeatedly identify page-file acquisition as a practical workflow. Existing drafts cover retry-aware direct and batched page-file reads, missing and non-string response bodies, row scoping, row ID shape and ASCII checks, link href presence and route validation, MIME title presence, blank file names, direct `PageFile` scalar validation, direct non-negative file sizes, and collection/cache ownership. None covers non-finite numeric overflow while parsing generated file-size text.

The focused RED test demonstrated the gap: a structurally valid file row with a 400-digit `GB` size value raised raw `OverflowError` from `int(inf)` before the existing contextual malformed-size exception could run.

## Related Issue / Non-Duplicate Analysis

Builds on [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md), [630-pr-validate-blank-page-file-names.md](630-pr-validate-blank-page-file-names.md), [632-pr-validate-non-negative-page-file-sizes.md](632-pr-validate-non-negative-page-file-sizes.md), [739-pr-validate-page-file-link-href-routes.md](739-pr-validate-page-file-link-href-routes.md), and [744-pr-validate-page-file-row-id-ascii-shape.md](744-pr-validate-page-file-row-id-ascii-shape.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a finite-value guard after multiplying the parsed file-size float by the selected unit multiplier.
- Return `None` for non-finite parsed byte counts so direct and lazy file acquisition use the existing `Page file size is malformed ...` diagnostic.
- Preserve existing `_parse_size(...)` compatibility and valid byte/kB/MB/GB conversions.
- Add a focused RED/GREEN regression for a generated size cell whose decimal text overflows to infinity.

## Type Of Change

- Bug fix
- Parser boundary hardening
- Numeric overflow diagnostic fix
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated page-file size cell whose parsed byte count is non-finite must raise `NoElementException`, not raw `OverflowError`. |
| R2 | The malformed-size diagnostic must include site, page, file name, file ID, `field=size`, and the observed size text using the existing message family. |
| R3 | Valid byte, kB, MB, GB, case-insensitive unit, and surrounding-whitespace size parsing must remain unchanged. |
| R4 | Existing ordinary malformed-size behavior, link href parsing, MIME parsing, row ID parsing, direct file construction, collection ownership, lazy `Page.files`, batched page-file acquisition, and adjacent page/site workflows must remain stable. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private file names, raw generated file-list HTML from real sites, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, full page-file tests, adjacent page/site tests, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A structurally valid file row with a 400-digit `GB` size value raises contextual `NoElementException`. | `TestPageFileCollectionAcquire.test_acquire_rejects_non_finite_file_size` failed RED with `OverflowError: cannot convert float infinity to integer`, then passed GREEN after the finite guard was added. | Leaking `OverflowError`, constructing a `PageFile`, returning size `0`, or silently skipping the row rejects this local completion claim. | Page-file generated size parser | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | The exception uses the existing malformed-size message shape. | The regression asserts `Page file size is malformed for site: test-site, page: test-page, file: file.txt (id=100, field=size, value=...)` and checks the observed generated size text is present. | A generic numeric error, omitted site/page/file context, omitted field/value, or raw parser internals rejects this local completion claim. | Parser diagnostics | focused test |
| R3 | Valid generated size parsing remains supported. | `TestPageFileCollectionParseSize` passed, including bytes, kB, uppercase KB, singular Byte, MB, GB, unknown-to-zero direct helper behavior, and whitespace cases. | Changing valid byte counts, rejecting uppercase unit text, or changing `_parse_size("unknown") == 0` rejects this local completion claim. | Size parser compatibility | `tests/unit/test_page_file.py` |
| R4 | Adjacent page-file and page workflows remain green. | Full `tests/unit/test_page_file.py` passed 124 tests, adjacent page/page_revision/page_votes/site coverage passed 1133 tests, and full unit passed 3786 tests. | Regressing file link parsing, MIME parsing, row ID parsing, direct file construction, cache reuse, lazy file access, page collection acquisition, or site workflows rejects this local completion claim. | Page-file and page workflows | `tests/unit` |
| R5 | The local proof stays unit-level and private-data-free. | The regression uses synthetic generated file-list markup and a synthetic file name only. | Using live Wikidot, credentials, cookies, auth JSON, raw private file-list HTML, private file names, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4bdb400 fix(page_file): validate finite file sizes`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_rejects_non_finite_file_size -q` failed before the fix with `OverflowError: cannot convert float infinity to integer`.
- GREEN focused: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_rejects_non_finite_file_size tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_requires_parseable_file_size tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_success tests/unit/test_page_file.py::TestPageFileCollectionParseSize -q` passed 11 tests.
- Hook compatibility: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_deduplicates_duplicate_page_ids tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_rejects_non_finite_file_size -q` passed 2 tests.
- `uv run pytest tests/unit/test_page_file.py -q` passed 124 tests.
- `uv run pytest tests/unit/test_page_file.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1133 tests.
- `uv run pytest tests/unit -q` passed 3786 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: CLI `0.5.0`, local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `PageFileCollection.acquire(page)` raises contextual `NoElementException` for generated file-size values that overflow to non-finite byte counts.
- The malformed-size diagnostic includes site, page, file name, file ID, field, and observed synthetic size value.
- Valid generated size values keep their existing parsed byte counts.
- Existing ordinary malformed-size values still use the same malformed-size path.
- Existing page-file, page, page-revision, page-vote, and site workflows remain green.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Generated page-file size metadata is protocol output. If it is too large for Python's float path to represent as finite bytes, wikidot.py should report a malformed generated size cell, not expose low-level numeric overflow. Returning `None` for non-finite parsed byte counts keeps the existing parser contract intact while preserving valid Wikidot attachment rows.

## Local Evidence

- Local rollout-backed drafts use page-file acquisition for browser-free attachment inventories, page asset audits, publication verification, generated migration ledgers, lazy `Page.files`, and duplicate cached file reuse.
- Existing local drafts covered ordinary malformed size cells, response-body context, row scoping, row ID shape and ASCII validation, link href route validation, MIME title validation, direct file scalar/range validation, and collection/cache ownership. They did not cover non-finite parsed byte counts from oversized generated size text.
- The focused RED failure showed a 400-digit generated `GB` value leaked `OverflowError` before the existing malformed-size diagnostic.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw file-list HTML from real sites, private file names, page source text, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally keeps `_parse_size(...)` behavior unchanged for direct unknown values, returning `0` when `_parse_size_value(...)` returns `None`. The acquisition path still validates `_parse_size_value(...)` first, so malformed generated file rows raise contextual parser errors before `_parse_size(...)` is called.
