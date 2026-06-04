# PR Draft: Require Page File MIME Title

## Summary

`PageFileCollection.acquire(page)` and `PageCollection.get_page_files()` parse `files/PageFilesModule` rows into `PageFile.mime_type`. Before this slice, a structurally valid attachment row that had a file ID, direct link, and size cell but omitted the MIME `<span title="...">` value was accepted as a successful parse and converted to `mime_type == ""`.

This follow-up treats a missing MIME title on a real attachment row as malformed input. It raises `NoElementException` with site, page, file name, file ID, and missing-field context before constructing `PageFile` objects. Existing malformed-row filtering remains unchanged for invalid row IDs, missing direct links, too-short rows, nested fake rows, empty file lists, URL normalization, size parsing, direct acquisition, cached acquisition, duplicate page-ID batching, and lazy `Page.files`.

## Related Issue

Builds on [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), and [230-pr-cache-direct-page-file-acquisition.md](230-pr-cache-direct-page-file-acquisition.md). Those drafts established page attachment acquisition as a practical browser-free read path, tightened the shared file-row parser boundary, and made direct/batched file-list diagnostics and caching observable.

No upstream issue was filed from this local workspace.

## Changes

- Reject structurally valid page-file rows that lack a direct MIME `span[title]` value.
- Include site, page, file name, file ID, and `field=mime_type` context in the malformed-row `NoElementException`.
- Pass the same parser context through direct `PageFileCollection.acquire(page)` and batched `PageCollection.get_page_files()`.
- Preserve existing structural row filtering for invalid row IDs, missing direct links, too-short rows, nested fake rows, and empty file-list responses.
- Add a focused public `PageFileCollection.acquire(page)` regression for a valid attachment row with `<span>TXT</span>` but no `title`.

## Type Of Change

- Bug fix / diagnostics improvement
- Page attachment parser hardening
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Missing MIME title on a structurally valid attachment row fails instead of fabricating an empty MIME type. | `TestPageFileCollectionAcquire.test_acquire_requires_file_mime_title` returns a file row with `file-row-100`, direct link, and size, but `<span>TXT</span>` without `title`, then asserts `NoElementException`. | Returning a `PageFile` with `mime_type == ""` rejects this local completion claim. |
| Malformed MIME errors identify the affected site, page, file, file ID, and field. | The focused regression asserts `Page file MIME type title is not found for site: test-site, page: test-page, file: file.txt (id=100, field=mime_type)`. | Omitting site, page, file, ID, or `field=mime_type` context rejects this local completion claim. |
| Existing malformed-row filtering stays intact. | Existing `tests/unit/test_page_file.py` regressions still cover malformed row IDs, missing direct links, too-short rows, nested fake rows, empty file-list responses, absolute/relative URLs, file-name spacing, multiple rows, and cache behavior. | Raising for intentionally skipped structural rows or parsing nested fake rows rejects this local completion claim. |
| Batched page-file acquisition remains compatible with the shared helper. | `PYTHONPATH=src pytest tests/unit/test_page_file.py tests/unit/test_page.py -q` passed 184 tests. | Regressions in duplicate page-ID file batching, cached duplicate reuse, lazy `Page.files`, or direct file acquisition reject this local completion claim. |
| Broad unit and static quality gates remain green in the repo dependency environment. | `uv run --extra test pytest tests/unit/ -q`; `uv run --extra lint ruff check src tests`; `uv run --extra format ruff format --check src tests`; `uv run --extra lint mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `120ca2f fix(page_file): require MIME title for parsed file rows`.

- RED: `PYTHONPATH=src pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_requires_file_mime_title -q` failed before the fix with `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>`.
- GREEN: `PYTHONPATH=src pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_requires_file_mime_title -q` passed 1 test.
- `PYTHONPATH=src pytest tests/unit/test_page_file.py tests/unit/test_page.py -q` passed 184 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 832 tests.
- `uv run --extra lint ruff check src tests`.
- `uv run --extra format ruff format --check src tests`.
- `uv run --extra lint mypy src tests --install-types --non-interactive`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable. A direct bare-interpreter full-suite run, `PYTHONPATH=src pytest tests/unit -q`, also could not collect tests that import `pytest_httpx`; the locked `uv --extra test` environment above includes the declared test extra and passed the full unit suite.

## Acceptance Criteria

- `PageFileCollection.acquire(page)` raises `NoElementException` when a structurally valid file row omits MIME `span[title]`.
- `PageCollection.get_page_files()` uses the same validation and includes the first affected page's site/page context in parser errors.
- Valid file rows still parse `PageFile.id`, `name`, `url`, `mime_type`, and `size` as before.
- Invalid row IDs, missing direct links, too-short rows, nested fake rows, and no-file responses keep their existing behavior.
- No live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

`PageFile.mime_type` is a parsed field, not an optional local annotation. A missing MIME title on an otherwise parseable attachment row is a parser contract failure, and accepting it as an empty MIME type makes asset audits and browser-free publication checks unable to distinguish unknown markup from a real server-provided MIME value. Raising a contextual parser exception keeps failed parses visible while preserving the existing structural skip rules for rows that are not valid attachment records.

## Local Evidence, Not For Upstream Paste

- Earlier local page-file drafts repeatedly identified attachment reads as a practical surface for source collection, publication verification, asset audits, retry handling, duplicate page-ID batching, parser scoping, and cache reuse.
- This slice intentionally targets only missing MIME titles on otherwise valid file rows. It does not change request payloads, retry policy, empty file-list handling, URL normalization, file-size parsing, cache invalidation, direct cache population, live Wikidot behavior, or page mutation methods.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved page contents, source text from real pages, page names from real sites, file contents, and site contents out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It removes a misleading absent-field fallback while preserving successful file-list parsing and the existing malformed-row boundary.
