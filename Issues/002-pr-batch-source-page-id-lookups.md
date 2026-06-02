# PR Draft: Batch Page ID Lookups Before Batched Page Detail Fetches

## Summary

`PageCollection` already sends batched AMC requests for source, revisions, votes, and files, but some detail-fetch paths obtained missing page IDs through `page.id` inside request-body list comprehensions. For pages without cached IDs, that path calls page-id acquisition one page at a time before the intended AMC batch.

The fix is to acquire missing page IDs once for the whole collection before building each page-detail request batch.

## Related Issue

Drafted from local rollout evidence; no upstream issue filed yet.

## Changes

- Call `PageCollection._acquire_page_ids(site, pages)` before the `ViewSourceModule` request body is built.
- Call `PageCollection._acquire_page_ids(site, pages)` before batched revision, vote, and file request bodies are built.
- Add regression tests proving that two pages with missing IDs issue one GET batch for both direct page URLs, then one AMC batch for each detail-fetch path.

## Type Of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Performance improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Testing

Local implementation commits:

- `e188565 perf(page): batch source page id lookups`
- `2021378 perf(page): batch page id lookups for page details`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_batches_missing_page_ids -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_batches_missing_page_ids tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_batches_missing_page_ids tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_batches_missing_page_ids -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 59 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 518 tests.
- [x] `uv run --extra lint ruff check src tests`
- [x] `uv run --extra format ruff format --check src tests`
- [x] `uv run --extra lint mypy src tests --install-types --non-interactive`
- [x] `git diff --check`

## Acceptance Criteria

- For a `PageCollection` of N pages without IDs, source, revision, vote, and file fetching each perform one batched direct-page GET operation for IDs, not N separate single-page ID acquisitions.
- The subsequent detail AMC request remains batched.
- Existing behavior for pages that already have IDs is unchanged.
- Source, revision, vote, and file parsing behavior remains unchanged.

## Upstream-Safe Motivation

Large source collection workflows are latency-sensitive. If a caller requests source for many pages, the library should preserve batching through both phases: page-id discovery and source retrieval.

Revision, vote, and file collection have the same batching expectation: collection-level APIs should not silently degrade to per-page direct GETs before their batched AMC requests.

## Local Evidence, Not For Upstream Paste

- Local rollout `019df644-518c-74b1-a95b-3b89865f49ce` summarized bulk branch source collection: bounded ListPages worked, but larger source fetches and CN single-page source fetches timed out.
- Local rollout `019e6454-88fa-7332-a0dd-a0ad98b1289c` included an adapter that first tries `PageCollection(site, pages).get_page_sources()` and then falls back to per-page source fetch on failure, showing this path was operationally important.

## Additional Notes

This change is intentionally small and reviewable: a collection-level page-id preflight before each affected request batch plus focused regression tests.
