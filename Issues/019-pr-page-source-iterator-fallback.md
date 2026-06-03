# PR Draft: Add Page Source Iterator With Fallback

## Summary

Large corpus scripts often need to discover pages, fetch source text, keep memory bounded, and continue after partial Wikidot source-fetch failures. Existing `PageCollection.get_page_sources()` is retry-aware and cache-aware, but callers still have to manually batch pages, retry failed pages in smaller groups, and turn unresolved pages into structured records.

The fix adds `site.pages.iter_sources(...)`, a generator that accepts normal page search keyword arguments, discovers pages through `site.pages.iter_search(...)`, fetches source in configurable batches, retries unresolved pages in smaller fallback batches, and yields one `PageSourceResult` per page in search order.

## Related Issue

Drafted from the broader local feature draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md); no upstream issue filed yet.

## Changes

- Add `PageSourceResult` with `page`, `source`, `error`, and `ok`.
- Add `SitePagesAccessor.iter_sources(...)`.
- Preserve existing `site.pages.search(...)`, `site.pages.iter_search(...)`, and `PageCollection.get_page_sources()` behavior.
- Reuse `iter_search(...)` for bounded page discovery instead of duplicating offset logic.
- Fetch source in `source_batch_size` chunks and retry pages still missing source in `fallback_batch_size` chunks.
- Preserve search order in yielded results even when fallback retries happen later.
- Report permanently unresolved pages with a per-page `NotFoundException` result instead of aborting the whole iterator.
- Add unit tests for batch sizing, parsed source results, fallback retry calls, ordered results, and per-page failure reporting.

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

Local implementation commit: `9d82979 feat(site): iterate page sources with fallback`

- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_yields_sources_in_search_order -q` failed before the fix with missing `SitePagesAccessor.iter_sources` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_falls_back_and_reports_page_failures -q` failed before fallback support with only the primary source batch attempted and passed after the fallback fix.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed with 4 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 546 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` inspected current complexity leads.

## Acceptance Criteria

- `site.pages.iter_sources(...)` accepts normal `SearchPagesQuery` keyword arguments plus `source_batch_size` and `fallback_batch_size`.
- The iterator yields one structured result per matching page in the same order as `site.pages.iter_search(...)`.
- Successful results expose `result.ok is True`, `result.page`, and `result.source`.
- Permanently unresolved source fetches yield `result.ok is False` and a per-page `result.error` without discarding successful pages from the same source batch.
- Primary source fetches use the requested `source_batch_size`.
- Fallback source fetches retry only pages that remain without source, using the requested `fallback_batch_size`.
- Existing `site.pages.search(...)`, `site.pages.iter_search(...)`, and `PageCollection.get_page_sources()` behavior remains unchanged.

## Upstream-Safe Motivation

Large Wikidot collection workflows need a caller-facing way to collect source text incrementally and tolerate partial source-fetch failures. A source iterator keeps memory bounded, centralizes retry/fallback mechanics, and lets callers persist successes and failures without writing ad hoc batch loops around the lower-level collection API.

## Local Evidence, Not For Upstream Paste

- Local rollout `019df644-518c-74b1-a95b-3b89865f49ce` recorded source fetch timeout problems for CN pages, including a single page that timed out three times.
- Local rollout `019e6454-88fa-7332-a0dd-a0ad98b1289c` included an adapter that tried batch source fetch first, then fell back to per-page source fetch and emitted per-page failures.
- The broader local feature draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md) calls for a source iterator or helper with structured success/failure records and configurable source/fallback batch sizes.

## Additional Notes

This slice builds on the bounded search iterator in [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), the source retry draft in [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md), and the cache-aware source retry draft in [008-pr-skip-cached-source-fetches.md](008-pr-skip-cached-source-fetches.md).

Follow-up [022-pr-source-iterator-large-fallback-batch.md](022-pr-source-iterator-large-fallback-batch.md) keeps fallback retry active when `fallback_batch_size` is larger than the primary source batch.

Follow-up [025-pr-source-result-error-page-context.md](025-pr-source-result-error-page-context.md) keeps the same `PageSourceResult` shape but includes the failed page fullname in unresolved-source error messages.

Follow-up [026-pr-source-iterator-parse-failure-isolation.md](026-pr-source-iterator-parse-failure-isolation.md) keeps malformed source response parsing failures inside the same per-page `PageSourceResult.error` path instead of aborting the iterator.
