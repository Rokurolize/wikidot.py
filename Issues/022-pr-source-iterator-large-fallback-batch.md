# PR Draft: Retry Source Iterator Fallback For Any Missing Pages

## Summary

`site.pages.iter_sources(...)` is meant to retry pages that remain without source after a primary source batch. Before this fix, fallback was skipped when `fallback_batch_size` was greater than or equal to the original primary batch size, even if only one page was still missing.

The fix retries any missing pages in fallback chunks regardless of whether the configured fallback chunk is smaller or larger than the primary source batch.

## Related Issue

Drafted from the broader local feature draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md); no upstream issue filed yet.

## Changes

- Update `SitePagesAccessor._source_results(...)` so fallback retries run whenever `missing_pages` is non-empty.
- Preserve `fallback_batch_size` as the chunk size for missing pages.
- Preserve ordered `PageSourceResult` output.
- Add a regression test where a primary batch leaves one page unresolved and `fallback_batch_size` is larger than the primary batch.

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

Local implementation commit: `52cf6ce fix(site): retry missing source fallback batches`

- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_retries_missing_pages_when_fallback_batch_is_large -q` failed before the fix with only the primary source batch attempted and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed with 5 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 549 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` inspected current complexity leads.

## Acceptance Criteria

- Missing source pages are retried after a primary source batch leaves them unresolved.
- Fallback retry happens even when `fallback_batch_size` is larger than the primary `source_batch_size`.
- The fallback retry requests only the missing pages.
- Result order remains the same as search order.
- Existing source iterator fallback and per-page failure behavior remains unchanged.

## Upstream-Safe Motivation

Callers should not have to know that fallback batch size must be smaller than the primary source batch. If pages remain unresolved, the iterator should use the configured fallback chunk size to retry those unresolved pages.

## Local Evidence, Not For Upstream Paste

- Local rollout `019e6454-88fa-7332-a0dd-a0ad98b1289c` included an adapter that tried batch source fetch first, then fell back to per-page source fetch and emitted per-page failures.
- The broader local feature draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md) calls for configurable source/fallback batch sizes and structured source success/failure records.
- The source iterator draft in [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md) established fallback retry as part of the intended iterator contract.

## Additional Notes

This slice does not change the primary source batch request or the final per-page `NotFoundException` result for pages that still have no source after fallback.
