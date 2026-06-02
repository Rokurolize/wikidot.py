# PR Draft: Batch Page ID Lookups Before Batched Source Fetch

## Summary

`PageCollection.get_page_sources()` already sends a batched `viewsource/ViewSourceModule` AMC request, but it currently obtains missing page IDs through `page.id` inside the request-body list comprehension. For pages without cached IDs, that path calls page-id acquisition one page at a time.

The fix is to acquire missing page IDs once for the whole collection before building the source request batch.

## Related Issue

Drafted from local rollout evidence; no upstream issue filed yet.

## Changes

- Call `PageCollection._acquire_page_ids(site, pages)` before the `ViewSourceModule` request body is built.
- Add a regression test proving that two source pages with missing IDs issue one GET batch for both direct page URLs, then one AMC batch for both source requests.

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

Local implementation commit: `e188565 perf(page): batch source page id lookups`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_batches_missing_page_ids -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py -q`
- [x] `uv run --extra test pytest tests/unit -q` passed with 515 tests.
- [x] `uv run --extra lint ruff check src tests`
- [x] `uv run --extra format ruff format --check src tests`
- [x] `uv run --extra lint mypy src tests --install-types --non-interactive`
- [x] `git diff --check`

## Acceptance Criteria

- For a `PageCollection` of N pages without IDs, source fetching performs one batched direct-page GET operation for IDs, not N separate single-page ID acquisitions.
- The subsequent `ViewSourceModule` AMC request remains batched.
- Existing behavior for pages that already have IDs is unchanged.
- Source parsing and `NoElementException` behavior remain unchanged.

## Upstream-Safe Motivation

Large source collection workflows are latency-sensitive. If a caller requests source for many pages, the library should preserve batching through both phases: page-id discovery and source retrieval.

## Local Evidence, Not For Upstream Paste

- Local rollout `019df644-518c-74b1-a95b-3b89865f49ce` summarized bulk branch source collection: bounded ListPages worked, but larger source fetches and CN single-page source fetches timed out.
- Local rollout `019e6454-88fa-7332-a0dd-a0ad98b1289c` included an adapter that first tries `PageCollection(site, pages).get_page_sources()` and then falls back to per-page source fetch on failure, showing this path was operationally important.

## Additional Notes

This change is intentionally small and reviewable: one production line plus one regression test.
