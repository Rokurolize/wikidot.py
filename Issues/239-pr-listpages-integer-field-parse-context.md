# PR Draft: Include Context In ListPages Integer Field Parse Errors

## Summary

`PageCollection._parse(...)` parses `list/ListPagesModule` fields for page search, source iteration, page lookup refreshes, and publish-adjacent verification flows. Earlier local slices made ListPages acquisition retry-aware, response-body-aware, structurally scoped, text-spacing-safe, and field-key parser errors site/page/field-aware. One adjacent value parser gap remained: generated integer fields such as `comments`, `size`, `children`, `rating_votes`, and `revisions` still used a direct `int(value_element.text.strip())`, so malformed generated values leaked a raw `ValueError` without the affected site, page, field, or value.

This follow-up keeps successful ListPages parsing unchanged, but routes integer ListPages fields through a small parser helper. Malformed integer values now raise `NoElementException` with site, parsed page fullname, field name, and raw value context, so plain-text logs can identify the broken generated field without retaining raw ListPages HTML or page content.

## Related Issue

Builds on [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md), [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md), [183-pr-listpages-fetch-failure-context.md](183-pr-listpages-fetch-failure-context.md), [191-pr-listpages-key-parse-context.md](191-pr-listpages-key-parse-context.md), and [220-pr-listpages-response-body-context.md](220-pr-listpages-response-body-context.md). Those drafts established ListPages parsing as a practical, heavily used read path and established the adjacent diagnostic pattern for malformed generated ListPages structure.

No upstream issue was filed from this local workspace.

## Changes

- Add a small ListPages integer-field parser that raises contextual `NoElementException` on malformed generated integer values.
- Route `rating_votes`, `comments`, `size`, `children`, and `revisions` through that helper.
- Add a focused regression for malformed `comments` field text in a generated ListPages response.
- Preserve successful ListPages parsing, direct structural field scoping, string field spacing, date/user/tag parsing, rating parsing, rating-percent parsing, pagination, retry behavior, source iteration, and publish-adjacent workflows.

## Type Of Change

- Bug fix / diagnostics improvement
- ListPages parser error-context ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed generated integer ListPages field values fail with wikidot.py's contextual parser exception rather than a raw integer conversion exception. | `TestPageCollectionParse.test_parse_malformed_integer_field_includes_site_page_and_value_context` mutates the generated `comments` value to `not-a-number` and asserts `NoElementException`. | A raw `ValueError`, fabricated zero, silent page skip, or partially malformed `Page` rejects this local completion claim. |
| The malformed integer-field error identifies the affected site, page, field, and raw value. | The focused regression asserts `ListPages integer field is malformed for site: test-site, page: scp-001 (field=comments, value=not-a-number)`. | Omitting site, page fullname, field, or raw value makes the failure ambiguous and rejects this local completion claim. |
| Successful ListPages parser and search behavior remain unchanged. | `uv run pytest tests/unit/test_page.py::TestPageCollectionParse tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed 27 tests. | Regressions in structural field scoping, missing-key diagnostics, string spacing, PM rating, 5-star rating, optional fields, search, pagination, retry, or limit behavior reject this local completion claim. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 278 tests. | Regressions in page source/revision/vote/file acquisition, site page accessors, publish helpers, or page mutation boundaries reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `ac8a924 fix(page): report malformed listpages integer fields`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_integer_field_includes_site_page_and_value_context -q` failed before the fix with raw `ValueError: invalid literal for int() with base 10: 'not-a-number'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_malformed_integer_field_includes_site_page_and_value_context -q` passed 1 test.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionParse tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed 27 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 278 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left 2 files unchanged.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run pytest tests/unit -q` passed 784 tests.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A generated ListPages response whose structural integer field contains non-integer text raises `NoElementException`.
- The malformed integer message includes the site `unix_name`, parsed page fullname when available, affected field name, and raw malformed value.
- Successful ListPages parsing, field scoping, string value spacing, date/user/tag parsing, PM rating parsing, 5-star rating parsing, pagination, retry behavior, source iteration, publish-adjacent search refreshes, and `Page` object construction remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

ListPages is a core read surface for page search, metadata hydration, source collection, and publication verification. When Wikidot returns malformed generated integer fields, wikidot.py should fail rather than inventing counts or leaking a generic Python conversion error. The failure should identify the site, page, field, and raw value so maintainers can triage from logs without storing raw ListPages HTML.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified ListPages as a practical workflow surface by improving first-page and paginated retry behavior, source iteration, required-tag filtering, field scoping, pager filtering, field spacing, fetch diagnostics, field-key diagnostics, and response-body validation.
- Adjacent parser-value slices showed that field/value-aware `NoElementException` messages improve resumable plain-text diagnostics without changing successful parser output or live Wikidot behavior.
- The refreshed complexity scanner continues to flag `src/wikidot/module/page.py` as a shared parser/acquisition hotspot, but this slice deliberately avoids broad parser rewrites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw ListPages HTML, and page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change ListPages request construction, paging, retry policy, source iteration, direct field scoping, string/date/user/tag parsing, rating or rating-percent conversion, returned page object shape, page-ID acquisition, mutation methods, or live Wikidot behavior. It only converts malformed integer ListPages field values into contextual parser errors.
