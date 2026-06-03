# PR Draft: Preserve Required-Tag Search Chunk Size

## Summary

`site.pages.iter_search(..., required_tags=..., limit=...)` counts the caller's `limit` as the number of yielded pages that satisfy the local required-tag filter. Before this fix, the same remaining matching-page count was also used as the remote `SearchPagesQuery.limit`. Because `PageCollection.search_pages(...)` truncates parsed ListPages results to that remote limit, the iterator could shrink a broad page chunk after skipping a nonmatching page and miss a later matching page in the same remote `perPage` window.

This fix keeps the remote ListPages request size at `perPage` while local required-tag filtering is active. The iterator still decrements the caller-visible remaining count only by yielded matching pages, advances offsets by `perPage`, and preserves the existing smaller remote-limit behavior when no local required-tag filter is active. `site.pages.iter_sources(...)` inherits the same correctness fix because it delegates page discovery through `iter_search(...)`.

## Related Issue

Builds directly on [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), which introduced the iterator-only `required_tags` filter for broad ListPages discovery plus exact local tag filtering. It also complements [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), and [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md).

No upstream issue was filed from this local workspace.

## Changes

- Keep `iter_search(..., required_tags=...)` remote `SearchPagesQuery.limit` at `perPage` for every broad ListPages chunk.
- Continue counting `limit` as yielded matching pages when `required_tags` is active.
- Preserve unfiltered iterator behavior, where a finite remaining limit can still reduce the remote request size.
- Add a regression test where a nonmatching broad result appears before a matching result after the caller-visible remaining count drops below `perPage`.
- Update the existing required-tags test to assert that the second remote query keeps the full chunk size instead of shrinking to one page.

## Type Of Change

- Bug fix
- Reliability improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Do not let a skipped nonmatching page hide a later matching page in the same broad ListPages window. | `TestSitePagesAccessor.test_iter_search_required_tags_keeps_remote_chunk_size_after_skips` returns `["fr:scp-001", "fr:scp-002"]` from broad pages `[match, nonmatch, nonmatch, match]`. | The RED test failed before the fix because only `["fr:scp-001"]` was yielded. |
| Preserve full remote chunk size while required-tag filtering is local. | The focused regression test asserts remote query offsets `[0, 2]` and remote query limits `[2, 2]` with `perPage=2` and caller `limit=2`. | Reverting the batch-limit condition shrinks the second remote query to `limit=1`, which truncates the broad chunk before the second matching page. |
| Keep caller-visible `limit` semantics as yielded matching pages. | The iterator stops after two required-tag matches, not after seeing two broad ListPages rows. | Counting broad skipped pages against the public limit would return only the first match. |
| Preserve existing `iter_sources(...)` required-tag filtering behavior. | `test_iter_sources_required_tags_skips_source_fetch_for_nonmatching_pages` still passes through the delegated search path. | A regression would fetch source for excluded broad pages or stop before checking the next search offset. |
| Preserve static and broad unit-test quality gates. | `tests/unit/test_site.py tests/unit/test_search_pages_query.py`; `tests/unit`; ruff; mypy; diff check. | Formatting, lint, type, whitespace, or broad unit failures reject the local completion claim. |

## Testing

Implemented locally in commit `0706779 fix(site): keep required-tag search chunks broad`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_search_required_tags_keeps_remote_chunk_size_after_skips -q` failed before the fix because only `["fr:scp-001"]` was yielded instead of both matching pages.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_search_required_tags_keeps_remote_chunk_size_after_skips tests/unit/test_site.py::TestSitePagesAccessor::test_iter_search_required_tags_filters_client_side tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_required_tags_skips_source_fetch_for_nonmatching_pages -q` passed 3 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_search_pages_query.py -q` passed 72 tests.
- `uv run --extra test pytest tests/unit -q` passed 623 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`
- `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed current complexity leads.

## Acceptance Criteria

- `site.pages.iter_search(tags="scp", required_tags=["scp", "fr"], perPage=2, limit=2)` keeps remote query limits at `[2, 2]` across the first two broad chunks.
- A broad result sequence containing `[matching page, nonmatching page, nonmatching page, matching page]` yields both matching pages.
- Nonmatching broad pages do not count against the caller's yielded-page `limit` while `required_tags` is active.
- Finite unfiltered iterator calls can still reduce the final remote query size to the remaining caller limit.
- `site.pages.iter_sources(...)` continues to avoid source fetches for pages excluded by required tags.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Large source-collection workflows use broad ListPages queries plus exact local required-tag filtering when Wikidot's compound tag query behavior is not reliable enough for the desired corpus boundary. In that mode, a caller's finite `limit` should mean "yield this many exact matches", not "truncate each remaining broad remote chunk to this many pages". Keeping the remote chunk at `perPage` avoids missing valid pages behind skipped broad results while preserving bounded traversal and existing unfiltered behavior.

## Local Evidence, Not For Upstream Paste

- Local required-tag iterator work in [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md) established broad ListPages discovery plus exact local tag filtering as an observed large-corpus need.
- The same source-collection surface already has local drafts for bounded search iteration, source iterator fallback, source failure isolation, and source result context properties.
- Keep private rollout paths, corpus identifiers, account names, thread workspace paths, raw command transcripts, and sandbox details out of upstream discussion.

## Additional Notes

This slice intentionally changes only the required-tag iterator chunk sizing. It does not reinterpret Wikidot ListPages tag syntax, does not change `SearchPagesQuery`, and does not change `site.pages.search(...)`.
