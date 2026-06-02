# PR Draft: Skip Cached Page Detail Fetches

## Summary

`PageCollection.get_page_revisions()`, `get_page_votes()`, and `get_page_files()` requested detail modules for every page in the collection even when some pages already had the corresponding detail collection cached. That made repeated collection calls do unnecessary AMC work and could overwrite already acquired details after a partial retry scenario.

The fix builds each detail request batch from only pages whose relevant cache is still missing, while preserving the original collection return value and existing parsing behavior.

## Related Issue

Drafted from local rollout evidence; no upstream issue filed yet.

## Changes

- Filter revision acquisition to pages where `_revisions is None`.
- Filter vote acquisition to pages where `_votes is None`.
- Filter file acquisition to pages where `_files is None`.
- Acquire missing page IDs only for pages that still need the requested detail collection.
- Add regression tests for mixed cached and missing revision, vote, and file details.

## Type Of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Performance/reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Testing

Local implementation commit: `c505a11 perf(page): skip cached detail fetches`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_skips_already_acquired_pages tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_skips_already_acquired_pages tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_skips_already_acquired_pages -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed with 13 tests.
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 69 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 528 tests.
- [x] `uv run --extra lint ruff check src tests`
- [x] `uv run --extra format ruff format --check src tests`
- [x] `uv run --extra lint mypy src tests --install-types --non-interactive`
- [x] `git diff --check`

## Acceptance Criteria

- `PageCollection.get_page_revisions()` sends `PageRevisionListModule` requests only for pages whose revisions are not already cached.
- `PageCollection.get_page_votes()` sends `WhoRatedPageModule` requests only for pages whose votes are not already cached.
- `PageCollection.get_page_files()` sends `PageFilesModule` requests only for pages whose file collection is not already cached.
- Cached detail collections are not overwritten by later collection acquisition calls.
- Existing missing-page-id batching and retry behavior for still-missing revision and vote details remains intact.

## Upstream-Safe Motivation

Collection detail fetches should preserve cache semantics consistently across source, revisions, votes, and files. Large page-processing workflows often call detail acquisition helpers repeatedly after partial failures or staged processing; skipping already acquired details reduces duplicate AMC requests and keeps successful results stable.

## Local Evidence, Not For Upstream Paste

- Local rollout `019df644-518c-74b1-a95b-3b89865f49ce` recorded large page listing and source collection workflows where bounded requests and retry-friendly collection operations mattered.
- Local rollout `019e6454-88fa-7332-a0dd-a0ad98b1289c` included an adapter that retried page detail/source collection in smaller units after batch failures.
- The local page-detail batching draft in [002-pr-batch-source-page-id-lookups.md](002-pr-batch-source-page-id-lookups.md) covers page-id batching for source, revision, vote, and file details; this draft covers follow-up cache-aware acquisition for the same detail families.
- The local cached source draft in [008-pr-skip-cached-source-fetches.md](008-pr-skip-cached-source-fetches.md) applies the same idea to page source acquisition.

## Additional Notes

This is an immediate performance and retry-ergonomics improvement for the broader large-corpus source collection feature draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md).
