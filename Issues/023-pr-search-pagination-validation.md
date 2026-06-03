# PR Draft: Validate Search Pagination Parameters

## Summary

Large corpus scripts depend on explicit `offset` and `perPage` values when walking `ListPagesModule` results. `SearchPagesQuery` already validates that `limit` is not negative, but invalid pagination values such as `perPage=0` or `offset=-1` could still enter request construction and create ambiguous helper behavior.

The fix rejects invalid pagination inputs early: `offset` must be non-negative, and `perPage` must be positive when provided. Existing `limit <= 0` no-request behavior remains unchanged.

## Related Issue

Drafted from the broader local feature draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md); no upstream issue filed yet.

## Changes

- Validate `offset >= 0` when an offset is provided.
- Validate `perPage > 0` when a per-page value is provided.
- Preserve the existing `limit <= 0` empty-result behavior.
- Add unit coverage for invalid `perPage=0` and `offset=-1`.

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

Local implementation commit: `5982ad7 fix(page): validate search pagination parameters`

- [x] `uv run --extra test pytest tests/unit/test_search_pages_query.py::TestSearchPagesQueryValidation::test_per_page_must_be_positive tests/unit/test_search_pages_query.py::TestSearchPagesQueryValidation::test_offset_must_be_non_negative -q` failed before the fix because the invalid values did not raise and passed after the fix with 2 tests.
- [x] `uv run --extra test pytest tests/unit/test_search_pages_query.py -q` passed with 21 tests.
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestSearchPagesQuery tests/unit/test_page.py::TestPageCollectionSearchPages tests/unit/test_site.py::TestSitePagesAccessor -q` passed with 22 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 551 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` inspected current complexity leads.

## Acceptance Criteria

- `SearchPagesQuery(perPage=0)` raises `ValueError`.
- `SearchPagesQuery(offset=-1)` raises `ValueError`.
- Valid queries serialize as before.
- Existing `limit=0` and other non-positive `limit` calls still return no pages without making a ListPages request.
- Existing `iter_search(...)`, `iter_sources(...)`, and `site.pages.search(...)` tests continue to pass.

## Upstream-Safe Motivation

Bounded Wikidot collection workflows rely on predictable `ListPagesModule` pagination. Rejecting invalid pagination values at `SearchPagesQuery` construction prevents impossible request shapes from reaching both direct search calls and iterator helpers.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence for large corpus collection used explicit `limit=250`, `perPage=250`, and offsets to avoid broad unbounded searches.
- Local draft [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md) added `site.pages.iter_search(...)`, which depends on valid `perPage` and `offset` values to advance bounded chunks.
- Local draft [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md) added `site.pages.iter_sources(...)`, which reuses the same search pagination surface before fetching source text.

## Additional Notes

This slice is intentionally narrow. It does not change `ListPagesModule` retry behavior, source fallback behavior, or the collection helper API shape.
