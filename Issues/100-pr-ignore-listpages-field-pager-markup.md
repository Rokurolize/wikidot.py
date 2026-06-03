# PR Draft: Ignore ListPages Field Pager Markup

## Summary

`PageCollection.search_pages(...)` fetches the first `list/ListPagesModule` page, parses generated page result blocks, and then inspects `div.pager span.target` to decide whether additional ListPages pages should be requested.

Before this fix, pagination discovery selected `div.pager` response-wide. If a page-controlled ListPages field value rendered pager-like markup, the search path treated that value markup as structural pagination. The focused regression inserted a `div.pager` with numeric targets `1` and `2` inside the generated title field value; before the fix the method fetched a phantom second page and returned two pages instead of the one page actually present on the first response.

This fix keeps real ListPages pagination unchanged, but ignores pager elements nested inside generated `div.page` result blocks.

## Related Issue

Builds on [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), and [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), because those drafts established ListPages search and field parsing as heavily used practical paths. In particular, [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md) established generated ListPages field values as page-controlled parser-boundary content.

The pagination failure class is adjacent to [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), and [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md): all four fixes prevent authored or value-controlled markup from queueing extra AMC page requests while preserving structural pagers.

No upstream issue was filed from this local workspace.

## Changes

- Add `PageCollection._pager_from_listpages_html(...)` to return the first structural ListPages pager outside generated page result blocks.
- Add `PageCollection._is_inside_listpages_result(...)` to identify pager candidates nested under generated `div.page` results.
- Use the structural-pager helper before deriving the ListPages total page count.
- Add a regression where a title field value containing `div.pager` with numeric targets does not trigger an additional `list/ListPagesModule` request.
- Preserve normal parsing, first-page retry handling, private-site status mapping, zero-limit behavior, non-numeric pager handling, real pagination, retry-aware additional page fetching, offset preservation, limit-bounded pagination, page field parsing, and `Page` output fields.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Pager-like markup inside a ListPages field value should not be treated as ListPages pagination. | `TestPageCollectionSearchPages.test_search_pages_ignores_field_value_pager_markup` inserts a `div.pager` with numeric targets inside the title value, asserts one page is returned, and asserts `amc_request_with_retry(...)` is not called. | The RED test failed before the fix because two pages were returned after a phantom second-page fetch. |
| Real structural ListPages pagination should continue to request additional pages. | The neighboring pagination tests, including `test_search_pages_pagination_preserves_query_offset`, `test_search_pages_additional_pager_requests_use_retry`, and `test_search_pages_limit_caps_additional_pager_requests`, remained green. | If a real structural pager stops queuing page 2, the existing pagination tests reject the local completion claim. |
| Existing page and adjacent site workflows should remain green. | `uv run pytest tests/unit/test_page.py -q` passed 98 tests, and `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 155 tests. | Regressions in page parsing, search, pagination, retry, source/page collection, publishing-adjacent helpers, or site APIs reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `eabac4b fix(page): ignore listpages field pager markup`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_ignores_field_value_pager_markup -q` failed before the fix because `len(pages)` was `2` after a title-value pager triggered an extra ListPages page fetch.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_ignores_field_value_pager_markup -q`
- `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_ignores_pager_without_numeric_targets tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_ignores_field_value_pager_markup tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_pagination_preserves_query_offset tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_additional_pager_requests_use_retry tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_limit_within_first_page_skips_additional_pager_requests tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_limit_caps_additional_pager_requests -q` passed 6 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 98 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 155 tests.
- `uv run pytest tests/unit -q` passed 652 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- `div.pager` markup inside generated `div.page` ListPages result blocks is treated as page result content only.
- Field-value pager markup cannot queue additional `list/ListPagesModule` requests.
- Real structural ListPages pagination still queues additional pages.
- Non-numeric pager target handling remains unchanged.
- Existing first-page retry handling, private-site status mapping, zero-limit behavior, real pagination, additional-page retry handling, offset preservation, limit-bounded pagination, page parsing, and `Page` field semantics remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

ListPages field values are page-controlled content inside generated result rows. `PageCollection.search_pages(...)` should use the module-level structural pager to decide additional page requests and ignore pager-like markup that is part of a page result value.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), and [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md) established ListPages search and field parsing as practical local targets.
- Pager drafts [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), and [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md) established the adjacent pagination failure class: authored markup can otherwise queue phantom page requests.
- The refreshed complexity scan continues to flag `src/wikidot/module/page.py` around ListPages parsing and search as an audit-worthy shared path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and page content out of upstream discussion.

## Additional Notes

This slice does not change ListPages query construction, first-page retry policy, additional-page retry policy, batch sizing, limit handling, offset math, field parsing, `SearchPagesQuery`, or the `Page` dataclass. It only narrows pager discovery before additional ListPages page requests are queued.
