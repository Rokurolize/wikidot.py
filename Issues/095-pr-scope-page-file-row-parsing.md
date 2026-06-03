# PR Draft: Scope Page File Row Parsing

## Summary

`PageFileCollection._parse_file_fields_from_html(...)` parses `files/PageFilesModule` output into attached-file field tuples used by both direct `PageFileCollection.acquire(page)` and collection-level `PageCollection.get_page_files()`.

Before this fix, the parser used descendant selectors under `table.page-files`: `files_table.select("tbody tr[id^='file-row-']")`, `row.select("td")`, and descendant filename/MIME lookups. If a structural file row contained nested table markup before the real filename link, the parser could treat nested file-like rows as real attached files and could also read the nested link as the outer row's filename. The focused regression produced two parsed files, both named `fake.txt`, even though the response had one direct structural `file-row-100` row whose real file was `real.txt`.

This fix keeps request construction, retry behavior, URL normalization, size parsing, duplicate page-id reuse, page-owned `PageFile` construction, and direct acquisition behavior unchanged, but treats only direct `tbody > tr` rows and direct row cells as structural file rows.

## Related Issue

Builds on [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), and [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), because those drafts established page-file acquisition as a practical attached-file workflow rather than speculative code. The parser-boundary motivation follows [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), and [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md).

No upstream issue was filed from this local workspace.

## Changes

- Parse direct `tbody` children under the generated `table.page-files` table.
- Parse only direct `tr` children of that structural `tbody`.
- Parse only direct `td` children of each structural file row.
- Parse the filename link and MIME span from direct structural cells.
- Add a regression where nested file-like table markup inside a file row does not create extra `PageFile` records or override the real file link.
- Preserve successful direct acquisition, empty file responses, invalid-row skipping, absolute URL preservation, size parsing, collection-level file parsing, and duplicate page ownership behavior.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| File-list rows should come from direct structural `table.page-files > tbody > tr` rows, not descendant rows. | `TestPageFileCollectionAcquire.test_acquire_ignores_nested_file_rows` inserts a nested `file-row-999` table inside the structural row and asserts only `file-row-100` is parsed. | The RED test failed before the fix because two file records were parsed from one structural row. |
| Filename, MIME, and size columns should come from direct structural row cells. | The same focused test asserts the parsed file is `real.txt`, MIME type `text/plain`, and size `1000` bytes despite a nested `fake.txt` row before the real link. | The RED test failed before the fix because descendant cell/link parsing used the nested `fake.txt` row. |
| Existing page-file behavior should remain green. | `uv run pytest tests/unit/test_page_file.py -q` passed 27 tests, and `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py -q` passed 124 tests. | Regressions in direct acquisition, collection-level acquisition, URL normalization, invalid-row handling, size parsing, or lazy `Page.files` reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `572d946 fix(page_file): scope file row parsing`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_ignores_nested_file_rows -q` failed before the fix because `len(collection)` was `2` and the parsed name was `fake.txt`.
- GREEN: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_ignores_nested_file_rows -q`
- `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_success -q`
- `uv run pytest tests/unit/test_page_file.py -q` passed 27 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py -q` passed 124 tests.
- `uv run pytest tests/unit -q` passed 647 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- Page-file parser treats only direct `tbody > tr` rows as attached-file rows.
- Nested `tr[id^='file-row-']` markup inside a file row cannot create extra `PageFile` records.
- Nested links or cells inside a file row cannot override the structural filename, MIME type, or size columns.
- Existing valid file rows still produce the same `PageFile.id`, `name`, `url`, `mime_type`, and `size` values.
- Existing empty-response, malformed-row, absolute-URL, direct-acquire, batched-acquire, duplicate page-id, and lazy `Page.files` behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Attached-file lookup is a practical page inspection workflow for source collection, browser-file upload verification, and publication audits. The files module emits a fixed table schema, so the parser should use direct generated table rows and cells as the structural boundary. That avoids confusing nested table markup with attached-file rows while preserving the public `PageFile` behavior.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), and [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md) established attached-file acquisition as a repeatedly used surface.
- Local rollout evidence includes browser data-form file upload probes that inspect `files/PageFilesModule` output to verify uploaded file rows and downloadable payloads.
- Parser-boundary drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md) through [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md) established the concrete failure class: descendant selectors can confuse generated module structure with nested markup.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, filenames from private probes, and page content out of upstream discussion.

## Additional Notes

This slice does not change `files/PageFilesModule` request construction, retry policy, file URL normalization, size unit conversion, duplicate page-id grouping, page-owned `PageFile` construction, lazy `Page.files`, or mutation paths. It only narrows file row and cell discovery to direct structural elements.
