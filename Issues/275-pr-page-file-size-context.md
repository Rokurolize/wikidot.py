# PR Draft: Require Parseable Page File Sizes

## Summary

`PageFileCollection.acquire(page)` and `PageCollection.get_page_files()` parse `files/PageFilesModule` rows into `PageFile.size`. Before this slice, a structurally valid attachment row that had a file ID, direct link, MIME title, and malformed size text such as `unknown` was accepted as a successful parse and converted to `size == 0`.

This follow-up treats malformed size text on a real attachment row as malformed input. It raises `NoElementException` with site, page, file name, file ID, `field=size`, and the original size value before constructing `PageFile` objects. The low-level `_parse_size("unknown") == 0` fallback remains available for callers that use the utility directly, while acquisition paths validate rows before using that fallback-backed helper.

## Related Issue

Builds on [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [230-pr-cache-direct-page-file-acquisition.md](230-pr-cache-direct-page-file-acquisition.md), and [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md). Those drafts established page attachment acquisition as a practical browser-free read path, tightened the shared file-row parser boundary, and made direct/batched file-list diagnostics, caching, MIME fields, and parser context observable.

No upstream issue was filed from this local workspace.

## Changes

- Reject structurally valid page-file rows whose size cell does not match a supported numeric unit.
- Include site, page, file name, file ID, `field=size`, and the raw malformed value in the `NoElementException`.
- Keep `_parse_size(...)` fallback behavior for direct utility callers by introducing a nullable parse helper used for validation.
- Preserve existing parsing for `B`, `byte`, `bytes`, `KB`, `MB`, and `GB`, including decimal values and whitespace.
- Preserve existing structural row filtering for invalid row IDs, missing direct links, too-short rows, nested fake rows, missing MIME titles, and empty file-list responses.
- Add a focused public `PageFileCollection.acquire(page)` regression for a valid attachment row with `unknown` size text.

## Type Of Change

- Bug fix / diagnostics improvement
- Page attachment parser hardening
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed size text on a structurally valid attachment row fails instead of fabricating a zero-byte file. | `TestPageFileCollectionAcquire.test_acquire_requires_parseable_file_size` returns a file row with `file-row-100`, direct link, MIME title, and `unknown` size text, then asserts `NoElementException`. | Returning a `PageFile` with `size == 0` for that row rejects this local completion claim. |
| Malformed size errors identify the affected site, page, file, file ID, field, and raw value. | The focused regression asserts `Page file size is malformed for site: test-site, page: test-page, file: file.txt (id=100, field=size, value=unknown)`. | Omitting site, page, file, ID, `field=size`, or `value=unknown` context rejects this local completion claim. |
| The utility parser's existing unknown-value fallback remains stable. | `TestPageFileCollectionParseSize.test_parse_unknown_returns_zero` remains green in the focused run. | Changing `_parse_size("unknown")` away from `0` rejects this local completion claim because it broadens behavior beyond this row-parser slice. |
| Batched page-file acquisition remains compatible with the shared helper and existing mock-based duplicate-page regression. | `PYTHONPATH=src pytest tests/unit/test_page_file.py tests/unit/test_page.py -q` passed 185 tests after the fix. | Regressions in duplicate page-ID file batching, cached duplicate reuse, lazy `Page.files`, direct file acquisition, or `_parse_size` call-count expectations reject this local completion claim. |
| Broad unit and static quality gates remain green in the repo dependency environment. | `uv run --extra test pytest tests/unit/ -q`; `uv run --extra lint ruff check src tests`; `uv run --extra format ruff format --check src tests`; `uv run --extra lint mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `bb1ca90 fix(page_file): require parseable file sizes`.

- RED: `PYTHONPATH=src pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_requires_parseable_file_size -q` failed before the fix with `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>`.
- GREEN: `PYTHONPATH=src pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_requires_parseable_file_size tests/unit/test_page_file.py::TestPageFileCollectionParseSize::test_parse_unknown_returns_zero -q` passed 2 tests.
- `PYTHONPATH=src pytest tests/unit/test_page_file.py tests/unit/test_page.py -q` passed 185 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 833 tests.
- `uv run --extra lint ruff check src tests`.
- `uv run --extra format ruff format --check src tests`.
- `uv run --extra lint mypy src tests --install-types --non-interactive`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `PageFileCollection.acquire(page)` raises `NoElementException` when a structurally valid file row contains malformed size text.
- `PageCollection.get_page_files()` uses the same validation and includes the first affected page's site/page context in parser errors.
- Valid file rows still parse `PageFile.id`, `name`, `url`, `mime_type`, and `size` as before.
- Direct `_parse_size("unknown")` behavior remains `0`.
- Invalid row IDs, missing direct links, too-short rows, nested fake rows, missing MIME titles, and no-file responses keep their existing behavior.
- No live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

`PageFile.size` is used as a parsed attachment property, and a malformed size string on an otherwise valid file row is not the same thing as a server-reported zero-byte file. Accepting malformed text as `0` makes asset audits and browser-free publication checks unable to distinguish missing/changed markup from a legitimate empty file. Raising a contextual parser exception keeps failed parses visible while preserving the existing `_parse_size` utility fallback and structural skip rules for rows that are not valid attachment records.

## Local Evidence, Not For Upstream Paste

- Earlier local page-file drafts repeatedly identified attachment reads as a practical surface for source collection, publication verification, asset audits, retry handling, duplicate page-ID batching, parser scoping, cache reuse, and field-level diagnostics.
- This slice intentionally targets only malformed size text on otherwise valid file rows. It does not change request payloads, retry policy, empty file-list handling, URL normalization, MIME parsing, cache invalidation, direct cache population, live Wikidot behavior, or page mutation methods.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved page contents, source text from real pages, page names from real sites, file contents, and site contents out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It removes a misleading field fallback at the row-acquisition boundary without changing the lower-level utility fallback or successful file-list parsing.
