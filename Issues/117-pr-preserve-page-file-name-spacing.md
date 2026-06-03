# PR Draft: Preserve Page File Name Spacing

## Summary

`PageFileCollection._parse_file_fields_from_html(...)` parses `files/PageFilesModule` rows for direct `PageFileCollection.acquire(page)` calls and collection-level `PageCollection.get_page_files()` acquisition.

Before this fix, attached file names were extracted from the direct file link with `link_elem.get_text().strip()`. When a rendered file-name link contained adjacent formatted child elements, visible text could be concatenated. The focused regression changed the file-name link to `<span>First <em>part</em></span><span>Second part.txt</span>`; before the fix, `PageFile.name` became `First partSecond part.txt`.

This fix extracts page attachment file names with a space separator and `strip=True`, preserving visible word boundaries while keeping `files/PageFilesModule` request construction, retry handling, direct row/cell scoping, file ID parsing, URL normalization, MIME extraction, size parsing, duplicate page-id reuse, page-owned `PageFile` construction, collection-level file acquisition, and lazy `Page.files` behavior unchanged.

## Related Issue

Builds on [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), and [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), because those drafts established page attachment acquisition as a practical source collection path and tightened the shared file-row parser boundary.

The text-fidelity failure class is adjacent to [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), and [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md), because all of these fixes preserve user-visible text while avoiding accidental structural-parser changes.

No upstream issue was filed from this local workspace.

## Changes

- Extract page attachment file names with `get_text(" ", strip=True)` instead of `.get_text().strip()`.
- Add a public `PageFileCollection.acquire(page)` regression where adjacent formatted file-name chunks keep a space between visible text chunks.
- Preserve `files/PageFilesModule` request construction, retry handling, direct row/cell scoping, malformed row filtering, file ID parsing, URL normalization, MIME extraction, size parsing, duplicate page-id reuse, page-owned `PageFile` construction, collection-level file acquisition, and lazy `Page.files` behavior.

## Type Of Change

- Bug fix
- Parser/text fidelity improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Page attachment file names should not concatenate adjacent rendered filename chunks or formatted child text. | `TestPageFileCollectionAcquire.test_acquire_preserves_file_name_text_spacing` asserts `collection[0].name == "First part Second part.txt"` through `PageFileCollection.acquire(page)`. | The RED test failed before the fix because the parsed name was `First partSecond part.txt`. |
| Direct page-file acquisition behavior should remain unchanged. | `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire -q` passed 10 direct acquisition tests covering retry-aware AMC use, exhausted retry failure, normal acquisition, absolute URL preservation, malformed row IDs, empty results, multiple files, invalid rows, nested-row scoping, and filename spacing. | If request construction, retry handling, row filtering, direct row scoping, URL handling, MIME parsing, size parsing, or result construction regresses, the direct acquisition tests reject the local completion claim. |
| Adjacent page and lazy file workflows should remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py -q` passed 128 tests. | Regressions in page parsing, cached/lazy file access, batch file acquisition, source iteration, or page-file result construction reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `e523849 fix(page_file): preserve file name spacing`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_preserves_file_name_text_spacing -q` failed before the fix because `collection[0].name` was `First partSecond part.txt`.
- GREEN: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_preserves_file_name_text_spacing -q`
- `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire -q` passed 10 tests.
- `uv run pytest tests/unit/test_page_file.py -q` passed 28 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py -q` passed 128 tests.
- `uv run pytest tests/unit -q` passed 669 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Page attachment file names preserve a separator between adjacent rendered filename chunks and formatted child text.
- Direct `PageFileCollection.acquire(page)` still uses retry-aware AMC requests for `files/PageFilesModule`.
- Exhausted direct acquisition retries still raise `UnexpectedException`.
- Malformed file-row IDs, missing direct links, too-short rows, and nested fake file rows are still filtered.
- Relative and absolute file URLs still normalize as before.
- MIME type extraction and size parsing remain unchanged.
- Shared file-row parsing remains usable by `PageCollection.get_page_files()` and lazy `Page.files`.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Page attachment file names are visible text emitted by `files/PageFilesModule`. `PageFile.name` should preserve word boundaries from rendered HTML without changing page-file request flow, structural row parsing, URL handling, MIME parsing, size parsing, or collection behavior.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), and [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md) established page attachment acquisition as a practical local target.
- Issue 095 local evidence included browser-backed upload and `files/PageFilesModule` structural row probes, which makes page-file parsing an important source-collection surface.
- Text-fidelity drafts [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md) through [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md) established visible text spacing as a recurring HTML flattening risk.
- The refreshed complexity scan continues to flag shared parser and collection code as audit-worthy, including page-file acquisition paths.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and page content out of upstream discussion.

## Additional Notes

This slice does not change page-file request construction, retry policy, structural table/row/cell discovery, file ID parsing, URL normalization, MIME extraction, size parsing, duplicate page-id reuse, `PageFile` construction, direct acquisition errors, collection-level acquisition, or lazy `Page.files`. It only changes how visible file-name link text is flattened into `PageFile.name`.
