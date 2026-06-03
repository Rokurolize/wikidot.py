# PR Draft: Scope ListPages Field Markup Parsing

## Summary

`PageCollection._parse(...)` parses `list/ListPagesModule` responses generated from a custom module body that wraps each requested field in `span.set`, `span.name`, and `span.value` elements.

Before this fix, the parser selected all descendant `span.set` elements inside each `div.page`, then selected descendant `span.name` and `span.value` elements from each set. If a page-controlled field value rendered ListPages-looking markup, that nested content could be interpreted as another structural field and override a real value. A nested `span.set fullname` inside the title value could change `Page.fullname` from the structural `scp-001` to `content:fake`.

This fix keeps the existing `SearchPagesQuery`, ListPages request body, pagination, retry, rating parsing, and `Page` API behavior, but reads only direct generated field spans from the structural page paragraph. Nested markup inside values remains content; it no longer changes parsed page metadata.

## Related Issue

Builds on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), and [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md), because those drafts established ListPages parsing as a heavily used practical path. The parser-boundary motivation follows [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), and [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md).

No upstream issue was filed from this local workspace.

## Changes

- Parse only top-level `div.page` wrappers from the ListPages response body.
- Resolve each page's structural field container to the direct generated paragraph when present.
- Parse direct child `span.set` elements only, instead of every descendant `span.set`.
- Parse direct `span.name` and `span.value` children from each structural set.
- Parse direct `span.odate`, `span.printuser`, and 5-star rating marker children from structural values/sets.
- Add a public `PageCollection._parse(...)` regression where a title value contains nested ListPages-looking `span.set fullname` markup.
- Preserve existing single-page, multiple-page, empty-result, optional-field, 5-star rating, search, pagination, retry, and page-save dependent behavior.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| ListPages field metadata should come from generated structural field spans, not value content. | `TestPageCollectionParse.test_parse_ignores_nested_listpages_markup_in_values` asserts the parsed page keeps `fullname == "scp-001"` even when the title value contains a nested fake `span.set fullname`. | The RED test failed before the fix because `Page.fullname` became `content:fake`. |
| Existing page parsing behavior should remain green. | `uv run pytest tests/unit/test_page.py -q` passed 95 tests. | Regressions in single/multiple page parsing, optional fields, 5-star rating parsing, search, pagination, retry, or save flows reject the local completion claim. |
| Adjacent page/site/file behavior stays green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_site.py -q` passed 177 tests. | Regressions in page file acquisition or site APIs that consume parsed pages reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `4ee7d03 fix(page): scope listpages field parsing`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_ignores_nested_listpages_markup_in_values -q` failed before the fix because `pages[0].fullname` was `content:fake` instead of `scp-001`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_ignores_nested_listpages_markup_in_values -q`
- `uv run pytest tests/unit/test_page.py -q` passed 95 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_site.py -q` passed 177 tests.
- `uv run pytest tests/unit -q` passed 644 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- ListPages parser only treats direct generated `span.set` elements as structural fields.
- Nested ListPages-looking markup inside a field value cannot override `fullname`, tags, counts, ratings, user fields, dates, or other structural page metadata.
- Direct structural `span.odate`, `span.printuser`, and 5-star rating marker parsing continues to work.
- Existing search, pagination, retry, page refresh, and save-adjacent workflows remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

ListPages is a core read path used by page search, source iteration, publication verification, and several post-save refresh flows. The parser already controls the generated module body, so it can treat the direct generated wrappers as the structural boundary. This prevents page-controlled values from being interpreted as metadata while preserving the public `PageCollection` behavior.

## Local Evidence, Not For Upstream Paste

- The rollout ledger for this research run records broad practical `wikidot.py` usage with ListPages-backed search/source/publish flows as repeatedly hardened local surfaces.
- Earlier ListPages drafts [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), and [080-pr-reuse-page-save-response-data.md](080-pr-reuse-page-save-response-data.md) established this parser as a practical target rather than a speculative helper.
- Parser-boundary drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md) through [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md) established the concrete failure pattern: user-controlled or authored markup can collide with descendant structural selectors.
- The refreshed complexity scan continues to flag `src/wikidot/module/page.py` ListPages parsing as an audit-worthy shared path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and page content out of upstream discussion.

## Additional Notes

This slice does not change ListPages query construction, paging, retry policy, limit handling, `SearchPagesQuery`, or the `Page` dataclass. It only narrows generated-field parsing to direct structural elements.
