# PR Draft: Deduplicate Page File Fetch IDs

## Summary

`PageCollection.get_page_files()` previously built one `files/PageFilesModule` request for every uncached `Page` object in the collection. If callers carried duplicate `Page` objects for the same resolved `page_id`, the method sent duplicate file-list requests and expected a matching duplicate response count.

This fix groups uncached pages by first-seen `page.id` after page ID acquisition, sends one file-list request per unique page ID, and applies the successful file-list response to every duplicate page object. Each duplicate page still receives its own `PageFileCollection`, and every parsed `PageFile.page` points at the page object that owns that collection.

## Related Issue

Builds on [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), and [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), which hardened file-list acquisition and failure visibility. Complements [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), and [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), which remove the same duplicate-ID request shape from adjacent page detail paths.

No upstream issue was filed from this local workspace.

## Changes

- Group uncached `Page` entries by first-seen `page.id` inside `PageCollection._acquire_page_files(...)` after `_acquire_page_ids(...)`.
- Send one `files/PageFilesModule` request per unique page ID.
- Apply each successful file-list response to every duplicate page object in that ID group.
- Preserve duplicate public collection entries while creating page-owned `PageFileCollection` instances for each duplicate page.
- Preserve retry-aware AMC, `None` response handling, cached-file skipping, file-row parsing, URL normalization, size parsing, and lazy `Page.files` behavior.
- Add a focused public-interface regression test for duplicate page IDs in `PageCollection.get_page_files()`.

## Type Of Change

- Performance and reliability improvement
- Test-covered behavior fix

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Avoid duplicate file-list fetches for repeated uncached page IDs. | `TestPageCollectionAcquire.test_acquire_files_deduplicates_duplicate_page_ids` asserts one `files/PageFilesModule` request for two page objects with the same ID. | Reverting the grouping makes the RED test fail with `ValueError: zip() argument 2 is shorter than argument 1` when the response count matches unique IDs. |
| Preserve duplicate public collection entries and page-owned file objects. | The focused test keeps both `Page` objects and verifies both receive file collections whose first file points back to the owning page object. | Sharing a single `PageFileCollection` across duplicates would make `PageFile.page` point at the wrong page object. |
| Preserve normal file acquisition behavior. | `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire -q`; `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_site.py -q`; `uv run --extra test pytest tests/unit -q`. | Regression would break file parsing, URL normalization, size parsing, lazy file access, page/site tests, or broad unit tests. |
| Preserve static quality gates. | `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Formatting, lint, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `20294dc perf(page): deduplicate page file fetch ids`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_deduplicates_duplicate_page_ids -q` failed before the fix with `ValueError: zip() argument 2 is shorter than argument 1`.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_deduplicates_duplicate_page_ids -q`
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 19 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_site.py -q` passed 167 tests.
- `uv run --extra test pytest tests/unit -q` passed 619 tests.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

## Acceptance Criteria

- Duplicate uncached `Page` objects with the same resolved `page.id` send one file-list request.
- First-seen unique page ID order is preserved in request construction.
- The public `PageCollection` length, ordering, and duplicate object entries remain unchanged.
- Every duplicate page entry receives a `PageFileCollection` populated from the successful shared response.
- Parsed `PageFile.page` references point at the owning duplicate page object, not a shared first page.
- A `None` retry result leaves that page ID group unacquired.
- Cached file collections are still skipped.
- Existing file parsing, URL normalization, size parsing, invalid-row skipping, lazy `Page.files`, page ID acquisition, direct `PageFileCollection.acquire(...)`, and mutation paths are unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Attached-file inspection is a read-heavy evidence surface for page review, publication verification, asset auditing, and content migration workflows. If caller queues contain duplicate page objects for the same resolved ID, the library should not issue duplicate file-list requests just to preserve the caller's original queue shape.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence included browser-free publishing, attachment inspection, source/corpus workflows, and page-evidence checks where file presence or absence can affect downstream decisions.
- Prior local drafts hardened batched file-list retries, `Page.files` exhausted-retry visibility, and direct `PageFileCollection.acquire(...)` retries, showing attached-file lookup is an important practical workflow surface.
- The same duplicate-ID request pattern was previously found in source fetching, page revision-list fetching, page revision source/HTML fetching, private message details, forum post sources, forum post revisions, forum post revision HTML, and forum thread post/detail acquisition.
- Keep local rollout paths, account names, and corpus-specific identifiers out of any upstream discussion.

## Additional Notes

This slice does not deduplicate page source requests, revision-list requests, or direct single-page `PageFileCollection.acquire(...)` calls. The later follow-up [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md) covers vote requests, [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md) covers unresolved page ID lookup requests, and [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md) avoids reparsing the shared successful file-list response for duplicate page objects. This slice only removes duplicate page file-list requests after each page already has a resolved page ID.
