# PR Draft: Isolate Source Iterator Parse Failures

## Summary

Large source-collection scripts need one malformed ViewSource response to become a page-level failure, not a collection-level abort. `site.pages.iter_sources(...)` already retries unresolved source pages and yields `PageSourceResult` records, but a response missing the expected `div.page-source` wrapper still raised from `PageCollection.get_page_sources()` and stopped the whole iterator before later pages could be yielded.

The fix keeps the lower-level `PageCollection.get_page_sources()` raising behavior unchanged while making the high-level iterator catch source acquisition exceptions, retry pages that still have no parsed source, and return the remaining page-specific parse error through `PageSourceResult.error`.

## Related Issue

Drafted from the broader local feature draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md); no upstream issue filed yet.

## Changes

- Add an iterator-level source acquisition wrapper that records exceptions instead of aborting `iter_sources(...)`.
- Preserve successfully parsed source results from the same batch.
- Retry pages that remain without source through the configured fallback batches.
- For fallback batches that still fail, narrow the failure to individual pages before yielding final results.
- Return malformed source responses as `PageSourceResult(ok=False, source=None, error=NoElementException(...))` for the affected page.
- Keep `PageCollection.get_page_sources()` behavior unchanged for callers that expect direct exceptions.
- Add a regression test for a malformed source response in the middle of a successful source batch.

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

Local implementation commit: `3a4d63c fix(site): isolate source parse failures`

- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_reports_parse_failures_without_losing_other_pages -q` failed before the fix because a `NoElementException` from one malformed response aborted the iterator, and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed with 6 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 553 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` inspected current complexity leads.

## Acceptance Criteria

- A malformed source response for one page yields a failed `PageSourceResult` instead of aborting `site.pages.iter_sources(...)`.
- Successful pages before and after the malformed response remain successful results.
- The failed result exposes the original `result.page`.
- The failed result contains the parsing exception and includes the page fullname in the error text.
- Existing retry, fallback batch-size, result ordering, and lower-level `PageCollection.get_page_sources()` behavior remain unchanged.

## Upstream-Safe Motivation

Large Wikidot source collections are vulnerable to partial source response failures. A single malformed page response should be recoverable in the same way as a timeout or missing source result: callers should be able to persist the affected page and continue collecting the rest of the corpus.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence recorded source fetch timeout problems during large corpus collection, including retries for individual pages.
- Local rollout evidence also included an adapter that emitted per-page failures after fallback source fetch attempts.
- The broader source collection draft in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md) calls for structured per-page source failure records.

## Additional Notes

This slice does not change retry counts, source request construction, cache behavior, or the `PageSourceResult` dataclass fields. It only moves iterator-level parse failures into the same structured per-page failure path already used for unresolved source fetches.
