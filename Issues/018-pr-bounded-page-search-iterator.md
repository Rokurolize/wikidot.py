# PR Draft: Add Bounded Page Search Iterator

## Summary

Large corpus scripts often need to walk `ListPagesModule` results by explicit offsets instead of materializing a broad search into one `PageCollection`. The existing `site.pages.search(...)` remains useful, but it returns a collection and delegates pagination to `PageCollection.search_pages(...)`, so callers that want bounded streaming have to manage repeated offset queries themselves.

The fix adds `site.pages.iter_search(...)`, a generator that accepts the same search keyword arguments, requests bounded ListPages chunks, preserves filters, and yields pages in ListPages order.

## Related Issue

Drafted from the broader local feature draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md); no upstream issue filed yet.

## Changes

- Add `SitePagesAccessor.iter_search(...)`.
- Preserve existing `site.pages.search(...)` behavior unchanged.
- Reuse `SearchPagesQuery` validation and `PageCollection.search_pages(...)` for each chunk.
- Respect the caller's initial `offset`, `perPage`, and optional overall `limit`.
- Cap each chunk query to `perPage` or the remaining limit so a single iterator step does not request an unbounded result set.
- Stop when the remaining limit is exhausted, no pages are returned, or the final chunk returns fewer pages than requested.
- Add tests for limit-bounded offset progression and no-limit termination after a short final page.

## Type Of Change

- [ ] Bug fix
- [x] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Performance/reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Testing

Local implementation commit: `9f7b2da feat(site): iterate page searches in bounded chunks`

- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_search_fetches_bounded_offset_pages -q` failed before the fix with missing `SitePagesAccessor.iter_search` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed with 2 tests.
- [x] `uv run --extra test pytest tests/unit/test_site.py -q` passed with 37 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 544 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` inspected current complexity leads.

## Acceptance Criteria

- `site.pages.iter_search(...)` yields pages without requiring the caller to manually mutate `offset`.
- The iterator preserves search filters such as `category`, `tags`, and `parent`.
- With `limit=5` and `perPage=2`, the iterator requests offsets `0`, `2`, and `4` with chunk limits `2`, `2`, and `1`.
- With no overall limit, the iterator continues by `perPage` offsets and stops after a short final page.
- Existing `site.pages.search(...)` and `PageCollection.search_pages(...)` behavior remains unchanged.

## Upstream-Safe Motivation

Large Wikidot collection workflows need predictable bounded ListPages scans. A public iterator lets callers process pages incrementally, keep memory bounded, and resume by offset while preserving the existing collection-returning search API.

## Local Evidence, Not For Upstream Paste

- Local rollout `019df644-518c-74b1-a95b-3b89865f49ce` recorded that bounded EN listing worked with explicit `limit`, `perPage`, and offsets, while an unbounded listing path was too coarse and was interrupted after more than two minutes.
- The broader local feature draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md) calls for a page iterator that yields across ListPages pagination without loading an unbounded site into memory by default.
- Local drafts [005-pr-bound-listpages-pagination-by-limit.md](005-pr-bound-listpages-pagination-by-limit.md) and [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md) already hardened the underlying ListPages pagination behavior; this draft exposes an ergonomic iterator on top.

## Additional Notes

This slice does not add `iter_sources(...)`, source batch fallback, or structured per-page source failure records. Those are covered by the follow-up local draft in [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md).

Follow-up [023-pr-search-pagination-validation.md](023-pr-search-pagination-validation.md) rejects invalid `offset` and `perPage` values before iterator or ListPages request construction.
