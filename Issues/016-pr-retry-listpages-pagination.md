# PR Draft: Retry ListPages Pagination Requests

## Summary

`PageCollection.search_pages()` fetches the first `ListPagesModule` page with `site.amc_request(...)`, then batches additional pager offsets when Wikidot reports multiple result pages. The additional pager batch previously used plain `site.amc_request(...)`, so transient failures in the second or later ListPages pages could abort large searches without the retry behavior already used by other batched collection fetches.

The fix routes additional ListPages pager requests through `site.amc_request_with_retry(...)`. If a retried additional page still fails, `search_pages()` raises `UnexpectedException` with the affected offset instead of silently returning an incomplete page list.

## Related Issue

Drafted from local rollout evidence; no upstream issue filed yet.

## Changes

- Use `site.amc_request_with_retry(...)` for batched additional ListPages pager requests.
- Preserve the existing first-page request path and private-site `ForbiddenException` handling.
- Preserve existing `offset`, `perPage`, and `limit` calculations for additional pager bodies.
- Raise `UnexpectedException` with the failed offset when a retry result remains `None`.
- Add regression tests for retry-aware additional pager requests and for avoiding silent partial results after unrecoverable retry failure.

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

Local implementation commit: `8f09f91 fix(page): retry listpages pagination`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_additional_pager_requests_use_retry -q` failed before the fix and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed with 10 tests.
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 77 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 539 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`

## Acceptance Criteria

- Additional ListPages pager requests use `site.amc_request_with_retry(...)`, not a second plain `site.amc_request(...)` batch.
- The first ListPages request remains unchanged so existing forbidden/private-site error mapping is preserved.
- Existing offset preservation for additional pager pages remains unchanged.
- Existing limit-bounded pagination remains unchanged.
- A permanently failed additional pager response raises an explicit exception naming the failed offset instead of returning a silently truncated result.

## Upstream-Safe Motivation

Large Wikidot corpus and search workflows depend on ListPages pagination staying reliable across multiple offsets. Additional pager requests are batched collection requests, so they should get the same retry behavior used by page source, revision, vote, file, and revision source/HTML collection paths while still avoiding silent partial result sets.

## Local Evidence, Not For Upstream Paste

- Local rollout `019df644-518c-74b1-a95b-3b89865f49ce` recorded that bounded ListPages scans with explicit `limit`, `perPage`, and offsets were practical, while an unbounded listing path was too coarse and was interrupted after more than two minutes.
- The same rollout recorded source-fetch timeout problems during large collection work, showing that long multi-request Wikidot collection workflows need retry-friendly request handling.
- The broader local feature draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md) calls out ListPages pagination, source retrieval, and fallback behavior as part of the large-corpus ergonomics problem.
- The prior local ListPages draft in [005-pr-bound-listpages-pagination-by-limit.md](005-pr-bound-listpages-pagination-by-limit.md) bounded how many additional pages are requested; this draft makes those remaining additional page requests retry-aware.

## Additional Notes

This does not add a streaming search iterator or structured per-page failure records. Those remain part of the broader large-corpus feature draft.
