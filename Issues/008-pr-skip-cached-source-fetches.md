# PR Draft: Skip Cached Source Fetches

## Summary

`PageCollection.get_page_sources()` fetched source for every page in the collection, even when some pages already had `_source` populated. This made retry workflows less efficient: after a partial source-fetch failure, a second call would re-fetch pages that had already succeeded.

The fix builds the `ViewSourceModule` batch from only pages whose source is still missing, while returning the original collection and preserving already cached source text.

## Related Issue

Drafted from local rollout evidence; no upstream issue filed yet.

## Changes

- Filter source acquisition to pages where `_source is None`.
- Acquire page IDs only for the pages that still need source retrieval.
- Preserve cached source values during subsequent `get_page_sources()` calls.
- Add a regression test for mixed cached and missing source pages.

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

Local implementation commit: `4e7f54b perf(page): skip cached source fetches`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_skips_already_acquired_pages -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_success tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_batches_missing_page_ids tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_skips_failed_retry_response tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_skips_already_acquired_pages -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 65 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 524 tests.
- [x] `uv run --extra lint ruff check src tests`
- [x] `uv run --extra format ruff format --check src tests`
- [x] `uv run --extra lint mypy src tests --install-types --non-interactive`
- [x] `git diff --check`

## Acceptance Criteria

- `PageCollection.get_page_sources()` sends `ViewSourceModule` requests only for pages whose source is not already cached.
- A retry after partial source-fetch failure can request only the remaining failed or missing pages.
- Cached source text is not overwritten by later collection source acquisition.
- Empty or fully cached collections return without an AMC source request.
- Existing retry behavior for missing source pages remains intact.

## Upstream-Safe Motivation

Large source collection scripts often need to retry after transient timeouts or partial failures. Cache-aware source acquisition avoids duplicate AMC requests for pages that have already succeeded, reducing load and making repeated collection calls more predictable.

## Local Evidence, Not For Upstream Paste

- Local rollout `019df644-518c-74b1-a95b-3b89865f49ce` recorded source fetch timeout problems for CN pages, including a single page that timed out three times.
- Local rollout `019e6454-88fa-7332-a0dd-a0ad98b1289c` included an adapter that tried batch source fetch first, then fell back to per-page source fetch and emitted per-page failures.
- The local source retry draft in [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md) covers partial retry failures; this draft covers the follow-up cache-aware retry ergonomics.

## Additional Notes

This is an immediate reliability and load-reduction improvement for the broader large-corpus source collection feature draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md).
