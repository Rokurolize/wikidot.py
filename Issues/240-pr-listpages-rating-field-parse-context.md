# PR Draft: Include Context In ListPages Rating Field Parse Errors

## Summary

`PageCollection._parse(...)` parses `list/ListPagesModule` rating fields for page search, source iteration, page lookup refreshes, and publish-adjacent verification flows. Earlier local slices made ListPages acquisition retry-aware, response-body-aware, structurally scoped, text-spacing-safe, field-key parser errors site/page/field-aware, and generated integer fields site/page/field/value-aware. One adjacent value parser gap remained: `rating`, 5-star `rating`, and 5-star `rating_percent` still used direct `int(...)` or `float(...)` conversions, so malformed generated rating values leaked raw Python `ValueError` exceptions without the affected site, page, field, or value.

This follow-up keeps successful PM rating and 5-star rating parsing unchanged, but routes generated rating values through the existing integer parser and a small float parser helper. Malformed rating values now raise `NoElementException` with site, parsed page fullname, field name, and raw value context, so plain-text logs can identify the broken generated field without retaining raw ListPages HTML or page content.

## Related Issue

Builds on [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md), [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md), [183-pr-listpages-fetch-failure-context.md](183-pr-listpages-fetch-failure-context.md), [191-pr-listpages-key-parse-context.md](191-pr-listpages-key-parse-context.md), [220-pr-listpages-response-body-context.md](220-pr-listpages-response-body-context.md), and [239-pr-listpages-integer-field-parse-context.md](239-pr-listpages-integer-field-parse-context.md). Those drafts established ListPages parsing as a practical, heavily used read path and established the adjacent diagnostic pattern for malformed generated ListPages structure and values.

No upstream issue was filed from this local workspace.

## Changes

- Add a small ListPages float-field parser that raises contextual `NoElementException` on malformed generated float values.
- Route 5-star `rating` through the float parser helper.
- Route non-5-star `rating` through the existing integer parser helper.
- Route 5-star `rating_percent` through the float parser helper after preserving the existing trailing-percent normalization.
- Add focused regressions for malformed non-5-star `rating`, 5-star `rating`, and 5-star `rating_percent` field text in generated ListPages responses.
- Preserve successful ListPages parsing, direct structural field scoping, string field spacing, date/user/tag parsing, integer count parsing, PM rating parsing, 5-star rating parsing, rating-percent normalization, pagination, retry behavior, source iteration, and publish-adjacent workflows.

## Type Of Change

- Bug fix / diagnostics improvement
- ListPages parser error-context ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed non-5-star generated `rating` values fail with wikidot.py's contextual parser exception rather than a raw integer conversion exception. | `TestPageCollectionParse.test_parse_malformed_rating_includes_site_page_and_value_context` mutates generated `rating` to `not-a-rating` and asserts `NoElementException`. | A raw `ValueError`, fabricated zero, silent page skip, or partially malformed `Page` rejects this local completion claim. |
| Malformed 5-star generated `rating` values fail with wikidot.py's contextual parser exception rather than a raw float conversion exception. | `TestPageCollectionParse.test_parse_malformed_5star_rating_includes_site_page_and_value_context` mutates generated 5-star `rating` to `not-a-rating` and asserts `NoElementException`. | A raw `ValueError`, fabricated float, silent page skip, or partially malformed `Page` rejects this local completion claim. |
| Malformed 5-star generated `rating_percent` values fail with wikidot.py's contextual parser exception rather than a raw float conversion exception. | `TestPageCollectionParse.test_parse_malformed_rating_percent_includes_site_page_and_value_context` mutates generated `rating_percent` to `not-a-percent` and asserts `NoElementException`. | A raw `ValueError`, fabricated percentage, silent page skip, or partially malformed `Page` rejects this local completion claim. |
| Rating parse errors identify the affected site, page, field, and raw value. | The focused regressions assert messages for `site: test-site`, `page: test-page`, the affected `field`, and malformed values `not-a-rating` or `not-a-percent`. | Omitting site, page fullname, field, or raw value makes the failure ambiguous and rejects this local completion claim. |
| Successful ListPages parser and search behavior remain unchanged. | `uv run pytest tests/unit/test_page.py::TestPageCollectionParse tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed 30 tests. | Regressions in structural field scoping, missing-key diagnostics, integer field diagnostics, string spacing, PM rating, 5-star rating, optional fields, search, pagination, retry, or limit behavior reject this local completion claim. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 281 tests. | Regressions in page source/revision/vote/file acquisition, site page accessors, publish helpers, or page mutation boundaries reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `bcaa9d9 fix(page): report malformed listpages rating fields`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_rating_percent_includes_site_page_and_value_context -q` failed before the fix with raw `ValueError: could not convert string to float: 'not-a-percent'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_rating_percent_includes_site_page_and_value_context -q` passed 1 test.
- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_rating_includes_site_page_and_value_context -q` failed before the fix with raw `ValueError: invalid literal for int() with base 10: 'not-a-rating'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_rating_includes_site_page_and_value_context -q` passed 1 test.
- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_5star_rating_includes_site_page_and_value_context -q` failed before the fix with raw `ValueError: could not convert string to float: 'not-a-rating'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_rating_percent_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_5star_rating_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_rating_includes_site_page_and_value_context -q` passed 3 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionParse tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed 30 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 281 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` reformatted 1 file and left 1 file unchanged.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run pytest tests/unit -q` passed 787 tests.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A generated ListPages response whose non-5-star `rating` value contains non-integer text raises `NoElementException`.
- A generated ListPages response whose 5-star `rating` value contains non-float text raises `NoElementException`.
- A generated ListPages response whose 5-star `rating_percent` value contains non-float text, after the existing trailing-percent normalization, raises `NoElementException`.
- The malformed rating messages include the site `unix_name`, parsed page fullname when available, affected field name, and raw malformed value.
- Successful ListPages parsing, field scoping, string value spacing, date/user/tag parsing, integer count parsing, PM rating parsing, 5-star rating parsing, rating-percent normalization, pagination, retry behavior, source iteration, publish-adjacent search refreshes, and `Page` object construction remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

ListPages is a core read surface for page search, metadata hydration, source collection, and publication verification. When Wikidot returns malformed generated rating fields, wikidot.py should fail rather than inventing scores or leaking generic Python conversion errors. The failure should identify the site, page, field, and raw value so maintainers can triage from logs without storing raw ListPages HTML.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified ListPages as a practical workflow surface by improving first-page and paginated retry behavior, source iteration, required-tag filtering, field scoping, pager filtering, field spacing, fetch diagnostics, field-key diagnostics, response-body validation, and integer field value diagnostics.
- Adjacent parser-value slices showed that field/value-aware `NoElementException` messages improve resumable plain-text diagnostics without changing successful parser output or live Wikidot behavior.
- The refreshed complexity scanner continues to flag shared parser/acquisition paths as hotspots, but this slice deliberately avoids broad parser rewrites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw ListPages HTML, and page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change ListPages request construction, paging, retry policy, source iteration, direct field scoping, string/date/user/tag parsing, returned page object shape, page-ID acquisition, mutation methods, or live Wikidot behavior. It only converts malformed generated rating field values into contextual parser errors.
