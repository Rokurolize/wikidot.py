# PR Draft: Report Malformed Page File Row IDs

## Summary

`PageFileCollection.acquire(page)` and `PageCollection.get_page_files()` parse `files/PageFilesModule` rows whose structural IDs use the `file-row-<id>` form. Before this slice, a row inside the direct `table.page-files > tbody` whose `id` started with `file-row-` but did not contain a numeric token was treated the same as a non-file row and silently skipped. Callers could receive a successful `PageFileCollection` missing an attachment row with no site, page, row, field, or observed value explaining the loss.

This follow-up preserves the existing skip behavior for rows without a `file-row-` structural marker, but raises `NoElementException` when a present `file-row-*` marker has a malformed numeric file ID. The error includes site, page, structural row number, `field=id`, and the observed row ID value. Valid file rows, non-file structural rows, direct and batched acquisition, URL normalization, MIME title validation, size validation, file-name validation, cache reuse, and retry behavior remain unchanged.

## Related Issue

Builds on [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [230-pr-cache-direct-page-file-acquisition.md](230-pr-cache-direct-page-file-acquisition.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), and [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md). Those drafts established page attachment acquisition as a practical browser-free read path, tightened the shared file-row parser boundary, and made direct/batched file-list diagnostics, caching, URL, name, MIME, size, and parser context observable.

No upstream issue was filed from this local workspace.

## Changes

- Reject direct `table.page-files > tbody` rows whose ID starts with `file-row-` but whose file ID token is malformed.
- Include site, page, structural row number, `field=id`, and the observed row ID value in the malformed-row `NoElementException`.
- Preserve existing row skipping for rows that lack an ID or do not carry the `file-row-` structural marker.
- Preserve successful parsing of valid file rows.
- Preserve existing file name, `href`, MIME title, and size validation.
- Add a focused public `PageFileCollection.acquire(page)` regression for `id="file-row-not-a-number"`.

## Type Of Change

- Bug fix / diagnostics improvement
- Page attachment parser hardening
- Test update

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A structural page-file row with a present but malformed `file-row-*` ID fails instead of silently disappearing from the collection. | `TestPageFileCollectionAcquire.test_acquire_malformed_file_row_id_includes_page_row_and_value_context` returns a `file-row-not-a-number` row followed by a valid row and expects `NoElementException`. | Returning only the valid later row, fabricating a file ID, or leaking an unrelated exception rejects this local completion claim. |
| Malformed row-ID errors identify the affected site, page, row, field, and observed row ID value. | The focused regression asserts `Page file row ID is malformed for site: test-site, page: test-page (row=1, field=id, value=file-row-not-a-number)`. | Omitting site, page, row, `field=id`, or the raw row ID value rejects this local completion claim. |
| Existing non-file row skipping stays intact. | The implementation only raises after the row ID starts with `file-row-`; rows with no ID or no `file-row-` marker keep the skip path. Existing `test_acquire_skips_invalid_rows` remains green in the page-file suite. | Raising for table rows that do not advertise themselves as file rows rejects this local completion claim. |
| Existing page-file field diagnostics stay intact. | Focused GREEN included MIME title, size, link `href`, file name, and success tests. | Regressing any adjacent page-file field diagnostic rejects this local completion claim. |
| Batched page-file acquisition remains compatible with the shared helper. | `uv run --extra test pytest tests/unit/test_page_file.py tests/unit/test_page.py -q` passed 187 tests. | Regressions in duplicate page-ID file batching, cached duplicate reuse, lazy `Page.files`, direct file acquisition, URL normalization, MIME validation, size validation, or name validation reject this local completion claim. |
| Broad unit and static quality gates remain green in the repo dependency environment. | `uv run --extra test pytest tests/unit/ -q`; `uv run --extra lint ruff check src tests`; `uv run --extra format ruff format --check src tests`; `uv run --extra lint mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `bbd89b5 fix(page_file): report malformed file row IDs`.

- RED: `uv run --extra test pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_malformed_file_row_id_includes_page_row_and_value_context -q` failed before the fix with `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>` because `file-row-not-a-number` was silently skipped.
- GREEN: `uv run --extra test pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_malformed_file_row_id_includes_page_row_and_value_context tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_requires_file_mime_title tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_requires_parseable_file_size tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_requires_file_link_href tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_requires_file_name tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_success -q` passed 6 tests.
- `uv run --extra test pytest tests/unit/test_page_file.py -q` passed 35 tests.
- `uv run --extra test pytest tests/unit/test_page_file.py tests/unit/test_page.py -q` passed 187 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 843 tests.
- `uv run --extra lint ruff check src tests`.
- `uv run --extra format ruff format --check src tests`.
- `uv run --extra lint mypy src tests --install-types --non-interactive`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `PageFileCollection.acquire(page)` raises `NoElementException` when a direct page-file table row has an ID that starts with `file-row-` but does not contain a numeric file ID.
- `PageCollection.get_page_files()` uses the same validation and includes the first affected page's site/page context in parser errors.
- Rows with no row ID, rows whose ID does not start with `file-row-`, rows with too few direct cells, and rows without a direct attachment anchor continue to follow the existing structural skip behavior.
- Valid file rows still parse IDs, names, relative/absolute URLs, MIME titles, and sizes as before.
- Missing file names, missing `href`, missing MIME titles, malformed sizes, nested fake rows, empty file-list responses, retry handling, and cache population keep their existing behavior.
- No live Wikidot action, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

Page attachments are a browser-free audit and publication surface. A row marked as `file-row-*` inside the file table is claiming to be an attachment record; if its ID token is malformed, silently dropping it can make the returned collection look complete while hiding a remote attachment. Reporting the malformed row ID with site/page/row context makes the generated-module failure actionable while preserving permissive skipping for rows that are not file records.

## Local Evidence, Not For Upstream Paste

- Earlier local page-file drafts repeatedly identified attachment reads as a practical surface for source collection, publication verification, asset audits, retry handling, duplicate page-ID batching, parser scoping, cache reuse, and field-level diagnostics.
- This slice intentionally targets only malformed present `file-row-*` IDs in direct page-file table rows. It does not change request payloads, retry policy, empty file-list handling, URL normalization, MIME parsing, size parsing, file-name parsing, cache invalidation, direct cache population, live Wikidot behavior, or page mutation methods.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved page contents, source text from real pages, page names from real sites, file contents, and site contents out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It turns a silent attachment-row loss path into a contextual parser error only when the row already advertises itself as a file row through the `file-row-` structural marker.
