# PR Draft: Filter Page Iterators By Required Tags

## Summary

`site.pages.iter_search(...)` and `site.pages.iter_sources(...)` already support bounded ListPages traversal and chunked source collection. Rollout evidence for large corpus work showed that compound ListPages tag queries such as `tags="fr scp"` were unsafe for at least one observed workflow, so callers used a broad ListPages selector and then filtered parsed page tags client-side.

This change adds an optional iterator-only `required_tags` filter. Callers can keep broad ListPages selection such as `tags="scp"` while asking the iterator to yield only pages whose parsed `Page.tags` include every required tag. `iter_sources(...)` applies the same filter before source fetching, so filtered-out pages do not trigger unnecessary source requests.

## Related Issue

Complements the large-corpus feature draft [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), especially the rollout note that compound ListPages tag queries were unsafe as an AND filter for the observed corpus workflow. It also builds on [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [022-pr-source-iterator-large-fallback-batch.md](022-pr-source-iterator-large-fallback-batch.md), and [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md). No upstream issue filed yet.

## Changes

- Add optional `required_tags` support to `SitePagesAccessor.iter_search(...)`.
- Add optional `required_tags` support to `SitePagesAccessor.iter_sources(...)` and pass it through to `iter_search(...)`.
- Normalize `required_tags` from either a whitespace-delimited string such as `"scp fr"` or a list such as `["scp", "fr"]`.
- Filter parsed `Page.tags` client-side while preserving the original ListPages query parameters.
- Count only yielded matching pages toward the iterator `limit` when `required_tags` is active.
- Avoid source fetching for broad ListPages results that do not satisfy `required_tags`.
- Leave `SearchPagesQuery` and `site.pages.search(...)` behavior unchanged.

## Type Of Change

- [ ] Bug fix
- [x] New feature
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
| R1: Page search iterators can enforce required tags client-side | `iter_search(tags="scp", required_tags=["scp", "fr"])` yields only pages whose parsed tags contain both tags | `test_iter_search_required_tags_filters_client_side` | The test failed before the fix with `ValueError: Invalid query parameters: required_tags` because the new argument was forwarded to `SearchPagesQuery` |
| R2: Nonmatching pages do not consume the requested matching-page limit | With `limit=2`, a nonmatching page in the first broad ListPages batch is skipped and the iterator requests the next offset to find the second match | `test_iter_search_required_tags_filters_client_side` checks offsets `[0, 2]` and query limits `[2, 1]` | The broad ListPages query still uses `tags="scp"` for both requests, proving the exact filter is local to the iterator |
| R3: Source iteration skips source fetches for pages excluded by required tags | `iter_sources(tags="scp", required_tags="scp fr", source_batch_size=2)` fetches source only for matching page IDs | `test_iter_sources_required_tags_skips_source_fetch_for_nonmatching_pages` | The source request body contains only the matching page ID and the test asserts no plain `amc_request(...)` calls |
| R4: Existing search and source APIs remain stable | Existing site/page search tests and search-query validation tests still pass | `tests/unit/test_site.py tests/unit/test_search_pages_query.py`; `tests/unit` | `SearchPagesQuery` is not expanded, so `site.pages.search(...)` keeps its current accepted parameters |

## Testing

Local implementation commit: `b5d13b3 feat(site): filter iterators by required tags`

- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_search_required_tags_filters_client_side -q` failed before the fix with `ValueError: Invalid query parameters: required_tags` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_search_required_tags_filters_client_side tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_required_tags_skips_source_fetch_for_nonmatching_pages -q` passed with 2 tests.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed with 9 tests.
- [x] `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_search_pages_query.py -q` passed with 70 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 603 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] Complexity scan refreshed at `/home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/artifacts/complexity_analysis_wikidot.md`

## Acceptance Criteria

- `site.pages.iter_search(...)` accepts `required_tags` as either a string or list.
- Required tags are evaluated against parsed `Page.tags`, not appended to the ListPages `tags` query.
- Pages missing any required tag are not yielded.
- When `required_tags` is active, skipped pages do not count against the caller's yielded-page `limit`.
- `site.pages.iter_sources(...)` accepts the same `required_tags` option and does not fetch source for pages filtered out by tags.
- `site.pages.search(...)` and `SearchPagesQuery` remain unchanged.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Large Wikidot collection scripts often need broad discovery plus exact local filtering. Relying on compound ListPages tag syntax for exact AND-like semantics was unsafe in observed corpus work, while forcing every caller to repeat the same client-side filtering makes source collection easier to get wrong. An iterator-only `required_tags` option keeps the remote ListPages query broad, uses parsed page metadata for the exact filter, and avoids fetching source for pages that will be discarded.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence recorded that compound ListPages tag queries such as `tags="fr scp"` were unsafe as an AND filter for the observed large-corpus workflow.
- The same feature area already produced local iterator and source-collection drafts for bounded page discovery, source fetch fallback, source failure isolation, and source text ergonomics.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

The change is intentionally scoped to the higher-level iterators. It does not attempt to reinterpret Wikidot ListPages tag query semantics, and it does not broaden `SearchPagesQuery` or `site.pages.search(...)` parameters.
