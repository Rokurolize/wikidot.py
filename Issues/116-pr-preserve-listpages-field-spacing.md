# PR Draft: Preserve ListPages Field Value Spacing

## Summary

`PageCollection.search_pages(...)` and `PageCollection._parse(...)` parse `list/ListPagesModule` responses generated from a custom module body that wraps requested page fields in `span.set`, `span.name`, and `span.value` elements.

Before this fix, generic string field values were extracted with `value_element.text.strip()`. When a rendered ListPages value contained adjacent formatted child elements, visible text could be concatenated. The focused regression changed the generated title value to `<span>First <em>part</em></span><span>Second part</span>`; before the fix, the parsed `Page.title` became `First partSecond part`.

This fix extracts generic ListPages string field values with a space separator and `strip=True`, preserving visible word boundaries while keeping ListPages request construction, first-page retry handling, private-site status mapping, structural field scoping, date/user/tag/numeric/rating parsing, pagination, limit handling, source iteration, publishing-adjacent search refreshes, and `Page` output shape unchanged.

## Related Issue

Builds on [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), and [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md), because those drafts established ListPages search and field parsing as heavily used practical paths. In particular, [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md) and [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md) established generated ListPages field values as page-controlled content that must not weaken parser boundaries or pagination.

The text-fidelity failure class is adjacent to [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), and [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), because all of these fixes preserve user-visible text while avoiding accidental structural-parser changes.

No upstream issue was filed from this local workspace.

## Changes

- Extract generic ListPages string field values with `get_text(" ", strip=True)` instead of `.text.strip()`.
- Add a public `PageCollection.search_pages(...)` regression where adjacent formatted title value chunks keep a space between visible text chunks.
- Preserve ListPages request construction, first-page retry handling, private-site status mapping, zero-limit behavior, real pagination, additional-page retry handling, offset preservation, limit-bounded pagination, structural field scoping, date/user/tag/numeric/rating parsing, source iteration, publishing-adjacent search refreshes, and `Page` field semantics.

## Type Of Change

- Bug fix
- Parser/text fidelity improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| ListPages string field values should not concatenate adjacent rendered value chunks or formatted child text. | `TestPageCollectionSearchPages.test_search_pages_preserves_field_value_text_spacing` asserts `pages[0].title == "First part Second part"` through `PageCollection.search_pages(...)`. | The RED test failed before the fix because the parsed title was `First partSecond part`. |
| ListPages parser boundaries and search behavior should remain unchanged. | `uv run pytest tests/unit/test_page.py::TestPageCollectionParse tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed 23 parse/search tests covering structural field parsing, nested value markup filtering, normal search, first-page retry, private-site status mapping, non-numeric pager handling, field-value pager filtering, real pagination, retry-aware additional pages, and limit-bounded pagination. | If request sequencing, parser-boundary filtering, field metadata parsing, pagination, retry, or limit behavior regresses, the focused parse/search tests reject the local completion claim. |
| Adjacent page, site, and file workflows should remain green. | `uv run pytest tests/unit/test_page.py -q` passed 100 tests; `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py -q` passed 186 tests. | Regressions in page parsing, search, source iteration, publish-adjacent refreshes, site APIs, or file acquisition reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `baefdaa fix(page): preserve listpages field spacing`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_preserves_field_value_text_spacing -q` failed before the fix because `pages[0].title` was `First partSecond part`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_preserves_field_value_text_spacing -q`
- `uv run pytest tests/unit/test_page.py::TestPageCollectionParse tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed 23 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 100 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py -q` passed 186 tests.
- `uv run pytest tests/unit -q` passed 668 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Generic ListPages string fields preserve a separator between adjacent rendered value chunks and formatted child text.
- Date fields still use direct `span.odate` parsing.
- Linked user fields still use direct `span.printuser` parsing.
- Tag fields still split whitespace into tag lists.
- Numeric, rating, and rating-percent fields still parse as numbers with the existing 5-star rating distinction.
- Existing first-page retry handling, private-site status mapping, zero-limit behavior, structural field scoping, nested ListPages-like value filtering, field-value pager filtering, real pagination, additional-page retry handling, offset preservation, limit-bounded pagination, source iteration, publishing-adjacent search refreshes, and `Page` field semantics remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

ListPages field values are page-controlled content inside generated result rows. `PageCollection.search_pages(...)` should preserve visible word boundaries for string values without changing ListPages request flow, pagination, parser boundaries, or typed field parsing.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [068-pr-preserve-required-tag-search-chunk-size.md](068-pr-preserve-required-tag-search-chunk-size.md), [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), and [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md) established ListPages search and field parsing as practical local targets.
- Text-fidelity drafts [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md) through [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md) established visible text spacing as a recurring HTML flattening risk.
- The refreshed complexity scan continues to flag `src/wikidot/module/page.py` around ListPages parsing and search as an audit-worthy shared path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and page content out of upstream discussion.

## Additional Notes

This slice does not change ListPages query construction, first-page retry policy, additional-page retry policy, batch sizing, limit handling, offset math, structural field discovery, date/user/tag/numeric/rating parsing, source iteration, publish helpers, or the `Page` dataclass. It only changes how generic string field values are flattened from rendered HTML into `Page` fields such as `title`.
