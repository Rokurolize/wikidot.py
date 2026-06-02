# PR Draft: Bound ListPages Pagination By Query Limit

## Summary

`PageCollection.search_pages()` passes `limit` and `perPage` to `ListPagesModule`, but the client-side pager follow-up logic did not use `limit` when deciding how many additional pager offsets to request. If a response includes a pager, the library could request more pages than needed and return more parsed `Page` objects than the caller's limit.

The fix is to use `limit` and `perPage` to cap additional pager requests, then clamp parsed results to the requested limit.

## Related Issue

Drafted from local rollout evidence; no upstream issue filed yet.

## Changes

- Return an empty `PageCollection` without an AMC call when `limit <= 0`.
- Compute additional ListPages pager requests from `limit` and `perPage`.
- Skip the second AMC call when the first page can satisfy the requested limit.
- Clamp parsed pages to `query.limit` before returning.
- Add regression tests for avoiding unnecessary extra pager calls and for requesting only the additional pager pages needed by the limit.

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

Local implementation commit: `de3c6c5 perf(page): bound listpages pagination by limit`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_limit_within_first_page_skips_additional_pager_requests tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_limit_caps_additional_pager_requests -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 61 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 520 tests.
- [x] `uv run --extra lint ruff check src tests`
- [x] `uv run --extra format ruff format --check src tests`
- [x] `uv run --extra lint mypy src tests --install-types --non-interactive`
- [x] `git diff --check`

## Acceptance Criteria

- If `limit` is smaller than or equal to `perPage`, `search_pages()` does not make an additional pager AMC request.
- If `limit` spans only part of the next pager page, `search_pages()` requests only the additional pager page needed.
- Returned pages never exceed `query.limit`.
- Existing offset preservation for pager requests is unchanged.
- Existing behavior without a limit is unchanged.

## Upstream-Safe Motivation

Bounded corpus and search workflows depend on `limit`, `perPage`, and `offset` to keep ListPages scans predictable. Client-side pagination should preserve that bounded behavior even when the response includes a pager.

## Local Evidence, Not For Upstream Paste

- Local rollout `019df644-518c-74b1-a95b-3b89865f49ce` recorded that bounded ListPages scans with explicit `limit`, `perPage`, and offsets were practical, while an unbounded listing path was too coarse and was interrupted after more than two minutes.

## Additional Notes

This is a small immediate improvement for the broader large-corpus ergonomics draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md).
