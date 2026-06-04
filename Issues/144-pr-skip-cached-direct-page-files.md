# PR Draft: Skip Cached Direct Page File Fetches

## Summary

`PageCollection.get_page_files()` already skips pages whose `_files` collection is populated, and it can reuse cached file lists from duplicate same-ID `Page` objects. Before this fix, the direct single-page helper `PageFileCollection.acquire(page)` did not share that cache-aware behavior: even when `page._files` already held a `PageFileCollection`, the helper still built a `files/PageFilesModule` request and could fail or perform a redundant AMC round trip.

This fix adds a small fast path at the start of `PageFileCollection.acquire(page)`. When the target page already owns a real `PageFileCollection`, the direct helper returns that collection immediately. Uncached direct acquisition still uses the existing retry-aware request, parser, URL normalization, size parsing, and exhausted-retry error behavior.

## Related Issue

Builds on [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), which made direct file-list acquisition retry-aware, [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md), which made page detail collections cache-aware, and [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), which reused cached duplicate page file lists in the collection helper.

No upstream issue was filed from this local workspace.

## Changes

- Return cached `page._files` immediately from `PageFileCollection.acquire(page)` when it is a `PageFileCollection`.
- Keep uncached direct acquisition on the existing `amc_request_with_retry(...)` and parser path.
- Add a focused regression that seeds `page._files`, makes AMC helpers fail if called, and asserts the cached collection is returned unchanged.
- Avoid treating arbitrary mock or non-collection `_files` values as a direct file cache.

## Type Of Change

- Performance improvement
- Cache-aware direct helper
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Direct page-file acquisition must not refetch an already cached `PageFileCollection`. | `TestPageFileCollectionAcquire.test_acquire_skips_cached_page_files` asserts both plain and retry-aware AMC helpers are not called. | The RED test failed before the fix because the helper ignored the cache and raised `UnexpectedException` from the forced `None` retry result. |
| Cached direct acquisition should preserve object identity. | The focused test asserts the returned collection is the exact cached `PageFileCollection` object. | Copying or reparsing the files would change identity and make direct cache behavior less predictable. |
| Uncached direct acquisition remains retry-aware and parser-backed. | `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire -q` passed 11 tests, including ordinary acquisition, exhausted retry, row parsing, URL preservation, and invalid-row handling. | Regressions in parser output, request module name, retry-exhaustion error handling, file-name spacing, or URL normalization reject this local completion claim. |
| Page-level file behavior remains stable. | `uv run pytest tests/unit/test_page_file.py tests/unit/test_page.py -q` passed 134 tests. | Regressions in lazy `Page.files`, collection-level cached skip, cached duplicate reuse, page ID batching, or adjacent page behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check HEAD~1..HEAD`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `60f156d perf(page_file): skip cached direct page files`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_skips_cached_page_files -q` failed before the fix because the direct helper ignored `page._files`, called the retry-aware AMC helper, and raised `UnexpectedException: Cannot retrieve page files`.
- GREEN: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_skips_cached_page_files -q`
- `uv run pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire -q` passed 11 tests.
- `uv run pytest tests/unit/test_page_file.py -q` passed 29 tests.
- `uv run pytest tests/unit/test_page_file.py tests/unit/test_page.py -q` passed 134 tests.
- `uv run pytest tests/unit -q` passed 708 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check HEAD~1..HEAD`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- `PageFileCollection.acquire(page)` returns cached `page._files` without making an AMC request when `page._files` is a `PageFileCollection`.
- The returned direct cached collection is the same object stored on the page.
- Uncached direct acquisition still uses `files/PageFilesModule` through `amc_request_with_retry(...)`.
- Existing direct retry exhaustion handling remains unchanged.
- Existing file-list parsing, malformed-row skipping, file-name spacing, URL normalization, size parsing, lazy `Page.files`, collection-level cached skip, and cached duplicate file-list reuse remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Callers can reach page attachments through both `page.files` and the public `PageFileCollection.acquire(page)` helper. When the page object already carries its file collection, the direct helper should not issue another network request for the same file list. This avoids a redundant AMC round trip and keeps direct file acquisition consistent with the cache-aware collection helper.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed page drafts repeatedly identified page file acquisition as a practical read-heavy surface, including retry hardening, cached page-detail skipping, duplicate page-ID batching, parsed file-row reuse, cached duplicate reuse, parser scoping, URL preservation, and file-name spacing.
- This slice came from comparing the cache-aware collection file helper with the still-uncached direct helper and then proving the direct helper's redundant fetch with a RED no-fetch mock.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not add a public refresh method, mutate cached collections, change file parser output, alter collection-level page-file batching, change retry policy, or change lazy `Page.files`. It only makes the direct page file-list helper honor an already populated real `PageFileCollection` before building a new file-list AMC request.
