# PR Draft: Reuse Page File List Parsing For Duplicate Page IDs

## Summary

`PageCollection.get_page_files()` already deduplicates duplicate uncached `Page` objects by resolved `page.id` before sending `files/PageFilesModule` requests, then gives each duplicate page object its own `PageFileCollection`. The duplicate page objects still reparsed the same successful file-list HTML body and reran file-size parsing for each page object in the duplicate ID group.

This fix parses each successful file-list response once per unique page ID into page-independent file fields, then creates fresh page-owned `PageFile` instances for every duplicate `Page` object in that page-ID group. The public `PageCollection` shape, duplicate page entries, page-owned file collections, retry behavior, URL normalization, invalid-row skipping, and direct single-page acquisition remain unchanged.

## Related Issue

Builds directly on [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), which removed duplicate file-list requests while preserving duplicate page objects. It follows the duplicate-response parse reuse pattern from [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md) and [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md).

No upstream issue was filed from this local workspace.

## Changes

- Parse each unique successful `files/PageFilesModule` response once inside `PageCollection._acquire_page_files(...)`.
- Split page-independent file-row parsing from page-owned `PageFile` construction.
- Reuse parsed file ID, name, URL, MIME type, and size fields for duplicate page objects with the same resolved page ID.
- Preserve distinct `PageFileCollection` instances and distinct `PageFile` objects for every duplicate page object.
- Preserve `PageFile.page` ownership by constructing fresh file objects for each owning page.
- Preserve first-seen request deduplication, cached-file skipping, retry-aware AMC, `None` retry-result handling, direct `PageFileCollection.acquire(...)`, URL normalization, invalid-row skipping, and lazy `Page.files` behavior.
- Strengthen the duplicate page-ID regression test to assert one response JSON parse and one file-size parse per shared file-list response, not per duplicate page object.

## Type Of Change

- Performance improvement
- Refactoring
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Duplicate page IDs should not reparse the same file-list response body. | `TestPageCollectionAcquire.test_acquire_files_deduplicates_duplicate_page_ids` asserts `response.json.call_count == 1` for two duplicate page objects sharing one successful response. | Regressions that move JSON parsing into the duplicate-page loop would fail this count. |
| Duplicate page IDs should not rerun file-row size parsing for duplicate page objects. | The focused test asserts `mock_parse_size.call_count == 1` for one file row shared by two duplicate page objects. | The RED test failed before the fix with `assert 2 == 1` for `mock_parse_size.call_count`. |
| Duplicate page objects still receive page-owned file collections. | The focused test still asserts both pages have file collections and that each collection's first `PageFile.page` points at the owning page object. | Sharing one collection or one file object across duplicate pages would fail the ownership assertions. |
| Direct single-page file acquisition remains compatible. | `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_file.py -q` passed 119 tests. | Regressions in direct `PageFileCollection.acquire(...)`, file parsing, URL normalization, size parsing, or lazy file access reject the local completion claim. |
| Existing unit behavior stays green. | `uv run --extra test pytest tests/unit -q` passed 628 tests. | Regressions in adjacent page-detail paths, site workflows, private-message parsing, forum parsing, or broad unit behavior reject the local completion claim. |
| Static quality gates remain green. | `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Formatting, lint, type, or whitespace failures reject the local completion claim. |
| Complexity evidence is interpreted conservatively. | The refreshed scanner artifact is still required for the thread report; the claimed improvement is duplicate file-list parse reuse, not removal of all page/file complexity warnings. | Overclaiming that scanner warnings disappeared would reject the draft. |

## Testing

Implemented locally in commit `97bc563 perf(page): reuse parsed page file rows`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_deduplicates_duplicate_page_ids -q` failed before the fix with `assert 2 == 1` for `mock_parse_size.call_count`.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_deduplicates_duplicate_page_ids -q`
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_file.py -q` passed 119 tests.
- `uv run --extra test pytest tests/unit -q` passed 628 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not spawn the `pyright` executable.

## Acceptance Criteria

- Duplicate uncached `Page` objects with the same resolved `page.id` still send one file-list request.
- A successful file-list response is parsed once per unique page ID.
- File-size parsing runs once per file row in the shared response, not once per duplicate page object.
- Each duplicate page object receives its own `PageFileCollection`.
- Each duplicate page object's `PageFile` instances point back to that owning page object.
- First-seen unique page ID request order remains unchanged.
- Cached file collections are still skipped.
- A `None` retry result still leaves the affected page ID group unacquired.
- Invalid file rows are still skipped.
- Existing direct `PageFileCollection.acquire(...)`, lazy `Page.files`, URL normalization, size parsing, page ID acquisition, adjacent page-detail acquisition, and mutation paths remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Attached-file inspection is a read-heavy evidence surface for page review, publication verification, asset auditing, migration checks, and source collection workflows. Once duplicate page objects share the same resolved page ID and successful file-list response, reparsing the same HTML and recomputing the same file fields does not add information. Reusing parsed fields reduces avoidable CPU work while preserving page-owned file objects.

## Local Evidence, Not For Upstream Paste

- [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md) removed duplicate file-list requests but intentionally preserved duplicate page object outputs.
- The focused RED test demonstrated the remaining cost: duplicate page objects still parsed the same one-row file list twice.
- Prior local drafts hardened batched file-list retries, `Page.files` exhausted-retry visibility, and direct `PageFileCollection.acquire(...)` retries, showing attached-file lookup is an important practical workflow surface.
- Keep local rollout paths, account names, and corpus-specific identifiers out of any upstream discussion.

## Additional Notes

This slice does not change page source acquisition, page revision-list acquisition, page vote acquisition, direct network request batching, file row selectors, size semantics, URL normalization semantics, lazy property behavior, or mutation paths. It only avoids redoing the same successful file-list parse for duplicate `Page` objects that share a resolved page ID.
