# PR Draft: Reuse Cached Duplicate Page File Lists

## Summary

`PageCollection.get_page_files()` already skips pages whose file list is cached, deduplicates uncached duplicate page IDs before fetching `files/PageFilesModule`, and parses one successful file-list response once per unique page ID. Before this fix, a collection containing both a cached page and an uncached duplicate with the same resolved page ID still fetched the file list for the uncached duplicate instead of reusing the cached file list already present in the same collection.

This fix indexes cached page file collections by page ID, clones cached file data into uncached same-ID duplicate pages before building AMC requests, and only fetches page IDs that remain unresolved. Public collection membership and ordering remain unchanged, and the duplicate target receives its own `PageFileCollection` and `PageFile` objects bound to the duplicate `Page` object rather than sharing the cached page's objects.

## Related Issue

Builds directly on [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md), which established cached page-detail skipping, [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), which established that duplicate page IDs should not trigger duplicate file-list requests, and [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), which established that duplicate uncached page IDs should reuse parsed file-list rows. It also preserves failed-retry visibility from [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), direct file-list retry behavior from [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), parser scoping from [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), and file-name spacing from [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md). It follows the cached duplicate reuse pattern from [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md) and [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md).

No upstream issue was filed from this local workspace.

## Changes

- Build a `page.id -> PageFileCollection` map from already cached page file lists in the collection.
- Populate uncached duplicate pages from that map before constructing `files/PageFilesModule` requests.
- Preserve page ownership by creating a new `PageFileCollection(page=page, files=...)` and fresh `PageFile(page=page, ...)` objects for each duplicate target page.
- Reuse the existing `PageFileCollection._build_page_files(...)` helper so cached and fetched duplicate file-list propagation share the same page-owned construction path.
- Keep first-seen request order and existing uncached duplicate grouping for the remaining unresolved page IDs.
- Add a focused regression where one duplicate page has cached files and another duplicate with the same page ID is uncached.
- Preserve retry-aware file-list fetches, failed retry handling, file-row parser scoping, URL normalization, file-size values, lazy `Page.files`, and adjacent page/site workflows.

## Type Of Change

- Performance/reliability improvement
- Cache behavior improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Cached file lists from a duplicate page ID must be reused within the same collection. | `TestPageCollectionAcquire.test_acquire_files_reuses_cached_duplicate_page_files` asserts the uncached duplicate receives the cached file ID, name, URL, MIME type, and size. | The RED test failed before the fix because the duplicate path called `files/PageFilesModule` for the already cached page ID. |
| Reusing cached duplicate file lists must avoid unnecessary network work. | The same focused test asserts neither plain `amc_request(...)` nor retry-aware `amc_request_with_retry(...)` is called. | A regression that fetches the file list for the duplicate fails the not-called assertions. |
| Cached duplicate reuse must preserve page ownership. | The focused test asserts the duplicate target has a distinct `PageFileCollection`, a distinct `PageFile`, and `duplicate_page._files[0].page is duplicate_page`. | Sharing the cached page's collection or file object would make the file point at the wrong owning page object. |
| Existing page file-list behavior remains intact. | `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 28 tests, and `uv run pytest tests/unit/test_page.py -q` passed 104 tests. | Regressions in cached detail skipping, duplicate uncached request grouping, parsed-row reuse, failed retry handling, file-row scoping, URL normalization, file-size parsing, or lazy behavior reject this local completion claim. |
| Adjacent page workflows stay green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_site.py -q` passed 192 tests. | Regressions in page file access, direct page-file acquisition, page/site reads, source iteration, or publishing-adjacent search behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `0c0591c perf(page): reuse cached duplicate page files`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_reuses_cached_duplicate_page_files -q` failed before the fix because the uncached duplicate sent a `files/PageFilesModule` request for the already cached page ID.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_reuses_cached_duplicate_page_files -q`
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 28 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 104 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_site.py -q` passed 192 tests.
- `uv run pytest tests/unit -q` passed 685 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- A cached file list on one page object is reused for uncached collection entries with the same resolved page ID.
- No AMC file-list request is sent when every uncached page can be satisfied from cached duplicates in the same collection.
- The duplicate target page receives its own `PageFileCollection` whose `page` points at that target page.
- Every copied file receives its own `PageFile` object whose `page` points at the duplicate target page.
- File IDs, names, URLs, MIME types, and sizes are preserved.
- Uncached duplicate page IDs with no cached file list still use the existing one-request-per-ID file-list fetch path.
- Exhausted retry results still leave only unresolved page IDs unacquired.
- Existing file-list parsing, cached-detail skipping, duplicate uncached grouping, parsed-row reuse, failed retry behavior, lazy `Page.files`, page ID acquisition, direct file acquisition, source/revision/vote acquisition, and mutation paths remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Large page inspection, source auditing, publication verification, attachment review, and retry-ledger workflows can carry duplicate page objects from merged searches or caller-side queues. If one duplicate page object already has its file list, fetching the same `PageFilesModule` response again adds avoidable AMC work and another failure point. Reusing cached duplicate file lists keeps collection file acquisition consistent with the existing cached-detail skip, duplicate-ID dedupe, and parsed-row reuse rules while preserving the caller-visible collection shape.

## Local Evidence, Not For Upstream Paste

- Existing local drafts established page detail reads and attachment parsing as practical rollout-backed surfaces for large source collection, publication verification, page inspection, and audit workflows.
- Issue 009 established cached page-detail skipping, Issue 064 established duplicate page IDs as a realistic file-list performance lead, and Issue 075 showed that one parsed file-list response should populate duplicate uncached page objects.
- Issues 127, 128, and 129 showed the same cached-duplicate reuse gap after request deduplication in adjacent page source, revision-list, and vote-list paths.
- The refreshed complexity scan continues to flag `src/wikidot/module/page.py` around page acquisition as a worthwhile audit area.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not change file-list request construction, retry policy, file-row parsing, URL normalization, size parsing, failed retry behavior, duplicate uncached grouping, lazy property return types, source/revision/vote fetching, direct file acquisition, publishing, or mutation methods. It only lets already cached file lists satisfy duplicate uncached page entries in the same collection before any file-list request is built.
