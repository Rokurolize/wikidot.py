# PR Draft: Retry First ListPages Fetch

## Summary

`PageCollection.search_pages(...)` uses Wikidot's `list/ListPagesModule` as the entry point for page search, source collection, page lookup, and browser-free publish verification workflows. Previous local fixes made additional paginated ListPages requests retry-aware, but the first ListPages request still used a plain `site.amc_request(...)` call. A transient first-page AMC failure could therefore raise immediately or be parsed as a response before the retry-aware pagination logic ever ran.

The fix adds retry handling for the first ListPages page while preserving the existing private-site `not_ok` to `ForbiddenException` mapping. Exhausted first-page retries now raise `UnexpectedException` with the affected starting offset, matching the explicit failure model already used for failed additional ListPages offsets.

## Related Issue

Complements [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), which made additional ListPages pager requests retry-aware while intentionally preserving the original first-page path. No upstream issue filed yet.

## Changes

- Add a small first-page ListPages request helper used by `PageCollection.search_pages(...)`.
- Retry transient exceptions returned by `site.amc_request(..., return_exceptions=True)` for the first ListPages request.
- Preserve `WikidotStatusCodeException(status_code="not_ok")` as `ForbiddenException("Failed to get pages, target site may be private")`.
- Preserve direct re-raising for non-retryable Wikidot status errors other than exhausted `try_again`.
- Raise `UnexpectedException("Failed to get ListPages page at offset: ...")` when first-page retries are exhausted.
- Keep query construction, module body fields, pager detection, offset math, `limit` handling, and additional-page retry behavior unchanged.
- Add focused tests for transient first-page retry, exhausted first-page retry, and private-site status mapping.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [ ] Security/privacy hardening
- [x] Reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Requirements Traceability

| Requirement | Acceptance | Verification | Negative Control |
| --- | --- | --- | --- |
| R1: First ListPages request retries transient AMC failures | `search_pages(...)` succeeds after a transient first response and preserves the same parsed page output | `test_search_pages_retries_transient_first_page_failures` | The test failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` |
| R2: Exhausted first-page retry fails explicitly | `search_pages(...)` raises `UnexpectedException` naming the starting offset | `test_search_pages_raises_when_first_page_retry_is_exhausted` | No partial or empty `PageCollection` is returned |
| R3: Private-site behavior is preserved | `not_ok` still maps to `ForbiddenException` | `test_search_pages_preserves_private_site_status_mapping` | The retry helper does not collapse `not_ok` into generic retry exhaustion |
| R4: Existing pagination behavior is preserved | Additional ListPages offsets still use retry-aware batching and existing offset math | `TestPageCollectionSearchPages` full class | Existing additional-page retry tests remain green |

## Testing

Local implementation commit: `fdace27 fix(page): retry first listpages fetch`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_retries_transient_first_page_failures -q` failed before the fix because the transient exception was treated as a response and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed with 13 tests.
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 80 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 578 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed the current complexity leads.

## Acceptance Criteria

- A transient first-page ListPages AMC failure is retried before response parsing.
- Exhausted first-page retry raises `UnexpectedException` with the starting offset.
- Existing private-site `not_ok` behavior still raises `ForbiddenException`.
- Existing query parameter handling, module body generation, pager discovery, additional-page offset calculation, and `limit` capping remain unchanged.
- Additional ListPages pages continue using the previously added retry-aware batch path.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Large Wikidot source and page-search workflows depend on the first ListPages page to discover both the first result batch and the pager metadata for later offsets. Retrying only additional pages leaves the most important request in the workflow less reliable than the follow-up requests. This change makes first-page and additional-page ListPages behavior consistent without changing the public search API.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence repeatedly used `wikidot.py` for page lookup, source collection, large ListPages scans, and browser-free publish verification.
- The existing local issue [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md) identifies ListPages/source collection reliability as a major practical workflow need.
- The existing local issue [005-pr-bound-listpages-pagination-by-limit.md](005-pr-bound-listpages-pagination-by-limit.md) bounded large ListPages scans, and [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md) made additional pages retry-aware. This draft closes the remaining first-page reliability gap.
- The refreshed complexity scan still flags page collection fetch paths as high-value collection surfaces, which supports keeping this fix narrow and behavior-preserving rather than adding a broader abstraction.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice does not change `SearchPagesQuery`, page parsing, page object fields, source retrieval, page publishing, or additional ListPages pagination. It only makes the initial ListPages request retry-aware and keeps the existing error semantics observable through the public `PageCollection.search_pages(...)` interface.
