# PR Draft: Require Page File Link Hrefs

## Summary

`PageFileCollection.acquire(page)` and `PageCollection.get_page_files()` parse `files/PageFilesModule` rows into `PageFile.url`. Before this slice, a structurally valid attachment row that had a file ID, link text, MIME title, and size cell but omitted the link `href` was accepted as a successful parse. Because `urljoin(site_url, "")` resolves to the site root, that malformed row produced a `PageFile.url` that looked valid but did not point to the attachment.

This follow-up treats a missing or blank `href` on a real attachment row as malformed input. It raises `NoElementException` with site, page, file name, file ID, and `field=href` context before constructing `PageFile` objects. Existing behavior for rows with no direct anchor remains unchanged: those structural non-file rows are skipped, while relative and absolute attachment URLs still parse normally.

## Related Issue

Builds on [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [230-pr-cache-direct-page-file-acquisition.md](230-pr-cache-direct-page-file-acquisition.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), and [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md). Those drafts established page attachment acquisition as a practical browser-free read path, tightened the shared file-row parser boundary, and made direct/batched file-list diagnostics, caching, URL, MIME, size, and parser context observable.

No upstream issue was filed from this local workspace.

## Changes

- Reject structurally valid page-file rows whose direct attachment anchor is missing a non-empty `href`.
- Include site, page, file name, file ID, and `field=href` context in the malformed-row `NoElementException`.
- Preserve existing row skipping for table rows that do not have a direct anchor at all.
- Preserve relative attachment URL normalization and absolute attachment URL preservation.
- Preserve existing MIME title and size validation.
- Add a focused public `PageFileCollection.acquire(page)` regression for a valid attachment row with `<a>file.txt</a>` but no `href`.

## Type Of Change

- Bug fix / diagnostics improvement
- Page attachment parser hardening
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Missing or blank file-link `href` on a structurally valid attachment row fails instead of fabricating a site-root URL. | `TestPageFileCollectionAcquire.test_acquire_requires_file_link_href` returns a file row with `file-row-100`, link text, MIME title, and size, but `<a>file.txt</a>` without `href`, then asserts `NoElementException`. | Returning a `PageFile` whose `url` is the site root rejects this local completion claim. |
| Malformed link errors identify the affected site, page, file, file ID, and field. | The focused regression asserts `Page file link href is not found for site: test-site, page: test-page, file: file.txt (id=100, field=href)`. | Omitting site, page, file, ID, or `field=href` context rejects this local completion claim. |
| Existing structural row filtering stays intact for rows with no direct anchor. | The focused GREEN run includes `TestPageFileCollectionAcquire.test_acquire_skips_invalid_rows`. | Raising for the existing `No link here` structural skip row rejects this local completion claim. |
| Valid absolute URLs remain valid. | The focused GREEN run includes `TestPageFileCollectionAcquire.test_acquire_preserves_absolute_file_url`. | Rewriting an absolute file URL through the site base rejects this local completion claim. |
| Batched page-file acquisition remains compatible with the shared helper. | `PYTHONPATH=src pytest tests/unit/test_page_file.py tests/unit/test_page.py -q` passed 186 tests. | Regressions in duplicate page-ID file batching, cached duplicate reuse, lazy `Page.files`, direct file acquisition, MIME validation, or size validation reject this local completion claim. |
| Broad unit and static quality gates remain green in the repo dependency environment. | `uv run --extra test pytest tests/unit/ -q`; `uv run --extra lint ruff check src tests`; `uv run --extra format ruff format --check src tests`; `uv run --extra lint mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `dcd6e67 fix(page_file): require file link hrefs`.

- RED: `PYTHONPATH=src pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_requires_file_link_href -q` failed before the fix with `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>`.
- GREEN: `PYTHONPATH=src pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_requires_file_link_href tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_preserves_absolute_file_url tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_skips_invalid_rows -q` passed 3 tests.
- `PYTHONPATH=src pytest tests/unit/test_page_file.py tests/unit/test_page.py -q` passed 186 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 834 tests.
- `uv run --extra lint ruff check src tests`.
- `uv run --extra format ruff format --check src tests`.
- `uv run --extra lint mypy src tests --install-types --non-interactive`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `PageFileCollection.acquire(page)` raises `NoElementException` when a structurally valid file row has a direct attachment anchor without a non-empty `href`.
- `PageCollection.get_page_files()` uses the same validation and includes the first affected page's site/page context in parser errors.
- Valid file rows still parse relative and absolute file URLs as before.
- Rows without a direct anchor continue to be skipped as structural non-file rows.
- Missing MIME titles, malformed sizes, invalid row IDs, too-short rows, nested fake rows, and no-file responses keep their existing behavior.
- No live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

`PageFile.url` is a parsed attachment download URL. A missing `href` on an otherwise valid file row is not equivalent to the site's root URL, and accepting that fallback can make asset audits or browser-free publication checks treat a malformed attachment record as a valid downloadable file. Raising a contextual parser exception keeps failed parses visible while preserving the existing structural skip rule for rows that are not valid attachment records.

## Local Evidence, Not For Upstream Paste

- Earlier local page-file drafts repeatedly identified attachment reads as a practical surface for source collection, publication verification, asset audits, retry handling, duplicate page-ID batching, parser scoping, cache reuse, and field-level diagnostics.
- This slice intentionally targets only missing link `href` values on otherwise valid file rows. It does not change request payloads, retry policy, empty file-list handling, URL normalization for valid URLs, MIME parsing, size parsing, cache invalidation, direct cache population, live Wikidot behavior, or page mutation methods.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved page contents, source text from real pages, page names from real sites, file contents, and site contents out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It removes a misleading site-root URL fallback at the row-acquisition boundary while preserving successful file-list parsing and the existing malformed-row skip boundary.
