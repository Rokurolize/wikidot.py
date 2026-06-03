# PR Draft: Retry Batched Source Fetches

## Summary

`PageCollection.get_page_sources()` retrieves page source through a batched `viewsource/ViewSourceModule` AMC request, but it used the plain `site.amc_request(...)` path. Other collection detail fetches such as revisions and votes already use `site.amc_request_with_retry(...)`, which splits batches, retries failed items, and returns `None` for permanently failed requests.

The fix is to route source fetches through `amc_request_with_retry(...)` and leave a page's source unset when that page's retry result is permanently unavailable.

## Related Issue

Drafted from local rollout evidence; no upstream issue filed yet.

## Changes

- Use `site.amc_request_with_retry(...)` for `viewsource/ViewSourceModule` batches.
- Skip `None` retry results so successfully fetched pages keep their source while failed pages remain explicitly unacquired.
- Update source acquisition tests to assert the retry path is used.
- Add a regression test for partial source-fetch failure.

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

Local implementation commit: `4964296 fix(page): retry batched source fetches`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_success tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_batches_missing_page_ids tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_skips_failed_retry_response -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 63 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 522 tests.
- [x] `uv run --extra lint ruff check src tests`
- [x] `uv run --extra format ruff format --check src tests`
- [x] `uv run --extra lint mypy src tests --install-types --non-interactive`
- [x] `git diff --check`

## Acceptance Criteria

- `PageCollection.get_page_sources()` uses `site.amc_request_with_retry(...)`, not the plain AMC request path.
- A permanently failed retry response does not discard successful source results from the same collection batch.
- Failed pages remain without `_source`, so existing `Page.source` access can still surface a `NotFoundException` when source is actually unavailable.
- Existing `NoElementException` behavior is preserved for successful responses whose body lacks `div.page-source`.
- Existing page-id batching remains intact.

## Upstream-Safe Motivation

Large source collection workflows are vulnerable to transient Wikidot failures and timeouts. Source fetching should have the same retry and partial-failure tolerance already used by other batched page detail operations.

## Local Evidence, Not For Upstream Paste

- Local rollout `019df644-518c-74b1-a95b-3b89865f49ce` recorded source fetch timeout problems for CN pages, including a single page that timed out three times.
- Local rollout `019e6454-88fa-7332-a0dd-a0ad98b1289c` included an adapter that tried `PageCollection(site, pages).get_page_sources()` first, then fell back to per-page source fetch and emitted per-page failures.

## Additional Notes

This is an immediate reliability improvement for the broader large-corpus source collection feature draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md).

Follow-up: [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md) removes duplicate source requests for repeated resolved page IDs while preserving the retry-aware behavior from this slice.
