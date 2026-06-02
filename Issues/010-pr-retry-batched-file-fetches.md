# PR Draft: Retry Batched File Fetches

## Summary

`PageCollection.get_page_files()` retrieved page file lists through a batched `files/PageFilesModule` AMC request, but it used the plain `site.amc_request(...)` path. Source, revision, and vote collection paths already use `site.amc_request_with_retry(...)`, which can split batches, retry failed items, and return `None` for permanently failed requests without discarding successful results.

The fix routes file-fetch batches through `amc_request_with_retry(...)` and leaves a page's file collection unset when that page's retry result is permanently unavailable.

## Related Issue

Drafted from local rollout evidence; no upstream issue filed yet.

## Changes

- Use `site.amc_request_with_retry(...)` for `files/PageFilesModule` batches.
- Skip `None` retry results so successfully fetched pages keep their parsed file collection while failed pages remain explicitly unacquired.
- Update file acquisition tests to assert the retry path is used.
- Add a regression test for partial file-fetch failure.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Performance/reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Testing

Local implementation commit: `b5cd8ce fix(page): retry batched file fetches`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_skips_failed_retry_response -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed with 14 tests.
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 70 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 529 tests.
- [x] `uv run --extra lint ruff check src tests`
- [x] `uv run --extra format ruff format --check src tests`
- [x] `uv run --extra lint mypy src tests --install-types --non-interactive`
- [x] `git diff --check`

## Acceptance Criteria

- `PageCollection.get_page_files()` uses `site.amc_request_with_retry(...)`, not the plain AMC request path.
- A permanently failed retry response does not discard successful file results from the same collection batch.
- Failed pages remain without `_files`, so callers can distinguish direct collection acquisition failure from a successfully parsed empty file list.
- Existing page-id batching and cache-aware file acquisition remain intact.
- Existing `PageFileCollection._parse_from_html(...)` behavior is unchanged for successful responses.

## Upstream-Safe Motivation

File detail collection should have the same retry and partial-failure tolerance as source, revision, and vote collection. This keeps collection-level page detail APIs consistent and reduces the chance that one transient file-module failure discards an otherwise successful batch.

## Local Evidence, Not For Upstream Paste

- Local rollout `019df644-518c-74b1-a95b-3b89865f49ce` recorded large page listing and source collection workflows where bounded requests and retry-friendly collection operations mattered.
- Local rollout `019e6454-88fa-7332-a0dd-a0ad98b1289c` included an adapter that retried page detail/source collection in smaller units after batch failures.
- The local source retry draft in [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md) covers the same reliability gap for `ViewSourceModule`.
- The local cached detail draft in [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md) covers cache-aware acquisition for revision, vote, and file details; this draft covers retry behavior for file details.

## Additional Notes

This is a small consistency and reliability improvement for page detail collection, separate from the broader large-corpus source collection feature draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md).
