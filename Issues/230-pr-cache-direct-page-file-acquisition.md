# PR Draft: Cache Direct Page File Acquisition

## Summary

`Page.files` caches the `PageFileCollection` it lazily reads from `PageCollection.get_page_files()`, and `PageFileCollection.acquire(page)` already checks `page._files` before making a direct `files/PageFilesModule` request. Before this fix, callers that used `PageFileCollection.acquire(page)` directly received the fetched file collection but left `page._files` unset. A later `page.files` access or repeated direct helper call could therefore refetch the same attachment list even though the direct helper already behaved as cache-aware at entry.

This change stores the successfully parsed direct file collection in `page._files` and returns that same object. Retry exhaustion and malformed response-body failures still raise before the cache assignment, so failed direct acquisition does not seed the page file cache. Existing cached-direct skips, collection-level duplicate file-list reuse, parser behavior, URL normalization, size parsing, and request payloads remain unchanged.

## Related Issue

Builds on [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), which made direct page-file reads retry-aware, [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md) and [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), which reduced duplicate batched file-list work, [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md) and [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), which hardened file parser behavior, [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), which reused cached duplicate page file lists, [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), which made the direct helper honor an existing `page._files` cache, and [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), and [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), which improved direct page-file failure context and response-body validation. It also follows the direct helper cache consistency pattern from [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [228-pr-cache-direct-thread-post-acquisition.md](228-pr-cache-direct-thread-post-acquisition.md), and [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md).

No upstream issue was filed from this local workspace.

## Changes

- Populate `page._files` when `PageFileCollection.acquire(page)` completes successfully.
- Return the same `PageFileCollection` object that is stored in the page cache.
- Preserve the existing cached-direct fast path for pages that already carry a `PageFileCollection`.
- Preserve retry exhaustion and missing response-body behavior by keeping the cache write after successful response validation and parsing.
- Add a focused regression proving direct acquisition populates the page cache and a later `page.files` access does not refetch.

## Type Of Change

- Performance improvement
- Cache consistency hardening
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Successful direct page-file acquisition must populate `page._files` with the returned collection. | `TestPageFileCollectionAcquire.test_acquire_populates_page_files_cache` asserts `mock_page_with_id._files is collection` immediately after direct acquisition. | The RED test failed before the fix because `_files` stayed `None` after the helper returned. |
| A later `page.files` access after direct acquisition must reuse the same collection without another AMC request. | The focused test asserts `mock_page_with_id.files is collection` and `amc_request_with_retry.assert_called_once()`. | A second fetch, a distinct collection object, or a property cache miss rejects this local completion claim. |
| Existing cached-direct behavior remains unchanged. | `TestPageFileCollectionAcquire.test_acquire_skips_cached_page_files` still returns the preseeded `PageFileCollection` without AMC calls. | Fetching when `_files` is already set or returning a different object rejects this local completion claim. |
| Failed direct file-list acquisition must not seed the cache. | Existing exhausted retry and missing response-body tests still pass; the new cache write is reached only after successful response validation and parsing. | Caching after a `None` response, missing JSON `body`, or parser failure rejects this local completion claim. |
| Collection-level page file batching remains unchanged. | `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_page_file.py -q` passed 69 tests. | Regressions in duplicate page-ID file batching, cached duplicate reuse, direct file acquisition, file parsing, or lazy file access reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `240c3fe perf(page_file): cache direct file acquisition`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_populates_page_files_cache -q` failed before the fix because `_files` remained `None` after a successful direct fetch.
- GREEN: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_populates_page_files_cache -q`.
- `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire -q` passed 13 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_page_file.py -q` passed 69 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run pytest tests/unit -q` passed 775 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageFileCollection.acquire(page)` returns the same collection it stores in `page._files` after a successful direct read.
- A following `page.files` access returns that stored collection without another AMC request.
- Existing `page._files` values still satisfy direct acquisition without fetching.
- Retry exhaustion, missing response bodies, parser behavior, URL normalization, MIME parsing, file-size parsing, empty file-list responses, lazy `Page.files`, collection-level file batching, cached duplicate page file reuse, and request payloads remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, non-goals, verification, and false-positive rejection checks.
- `Issues/README.md` records the local draft and implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Callers can naturally use `PageFileCollection.acquire(page)` directly while collecting page attachments, composing retry queues, or avoiding property syntax in helper code. Because the helper already checks `page._files`, a successful direct read should become the cache source for the same page object. Populating the cache after complete acquisition avoids redundant AMC work while preserving explicit refresh through cache clearing or replacement.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed page-file drafts repeatedly identified attachment reads as a practical read-heavy surface, including retry hardening, duplicate page-ID batching, parse reuse, cached first-seen skips, cached duplicate reuse, cached direct skips, parser scoping, response-body validation, file-name spacing, and site/page diagnostics.
- Prior cache-aware local drafts established that direct helpers should avoid repeat reads when the target object already carries the requested data, and Issues 227 through 229 applied the same direct-helper cache consistency rule to forum category, thread, and post revision surfaces.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not add a public refresh method, change `Page.files`, alter file parser output, change URL normalization, change file-size parsing, alter collection-level file batching, or change mutation methods. It only stores complete successful direct page-file acquisitions in the cache that the helper already respects.
