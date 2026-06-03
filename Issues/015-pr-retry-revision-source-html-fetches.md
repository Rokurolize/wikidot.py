# PR Draft: Retry Revision Source And HTML Fetches

## Summary

`PageRevisionCollection.get_sources()` and `PageRevisionCollection.get_htmls()` batch `history/PageSourceModule` and `history/PageVersionModule` requests for page revisions. The shared acquisition helper previously used the plain `page.site.amc_request(...)` path, so one transient or permanently failed response could abort processing for an otherwise successful revision batch.

The fix routes revision source and HTML batches through `page.site.amc_request_with_retry(...)` and leaves only the permanently failed revision item unacquired when the retry helper returns `None`.

## Related Issue

Drafted from local rollout evidence and local code inspection; no upstream issue filed yet.

## Changes

- Use `page.site.amc_request_with_retry(...)` inside `PageRevisionCollection._generic_acquire(...)`.
- Skip `None` retry results so successful revision source/HTML responses are still parsed and cached.
- Keep existing lazy-load behavior for `PageRevision.source` and `PageRevision.html`.
- Keep existing response-length safety through `zip(..., strict=True)`.
- Add regression tests for partial retry failure in revision source and revision HTML acquisition.
- Update existing revision tests to assert the retry-aware request path is used.

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

Local implementation commit: `2d79241 fix(page_revision): retry revision fetches`

- [x] `uv run --extra test pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_skips_failed_retry_response -q` failed before the fix and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_skips_failed_retry_response -q`
- [x] `uv run --extra test pytest tests/unit/test_page_revision.py -q` passed with 28 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 537 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`

## Acceptance Criteria

- `PageRevisionCollection.get_sources()` uses `page.site.amc_request_with_retry(...)`, not the plain AMC request path.
- `PageRevisionCollection.get_htmls()` uses `page.site.amc_request_with_retry(...)`, not the plain AMC request path.
- A permanently failed retry response does not discard successful revision source or HTML results from the same batch.
- Failed revisions remain with `_source is None` or `_html is None`, preserving existing lazy acquisition semantics.
- Existing parsing behavior for successful revision source and HTML responses remains unchanged.

## Upstream-Safe Motivation

Revision source and HTML collection are the revision-level equivalents of current page source/detail collection. They should have the same retry and partial-failure tolerance as other batched collection fetches, especially for scripts that inspect history, compare source snapshots, or build resumable corpus ledgers.

## Local Evidence, Not For Upstream Paste

- Local rollout `019e7a39-505b-76b3-bfb4-b68be3c71fb9` used source revision counts as part of a publish ledger and stored them through `codex-source-revision` metadata, showing revision history data was part of practical Wikidot publishing traceability.
- Local rollout `019df644-518c-74b1-a95b-3b89865f49ce` recorded source fetch timeout problems during large collection work, including a single page that timed out three times. That evidence is direct for current page source batches and supports applying the same retry pattern to analogous revision source/HTML batches.
- Local rollout `019e6454-88fa-7332-a0dd-a0ad98b1289c` included an adapter that tried batch source fetch first, then fell back to smaller units and emitted per-page failures.
- The local retry drafts in [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md) and [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md) cover the same collection-level reliability gap for current page source and files.

## Additional Notes

This is a small consistency fix. It does not add a new history iterator, revision diff API, or high-level corpus collection helper.
