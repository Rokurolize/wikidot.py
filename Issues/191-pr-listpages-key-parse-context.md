# PR Draft: Include Site And Field Context In ListPages Key Parse Errors

## Summary

`PageCollection._parse(...)` parses `ListPagesModule` HTML by walking direct `span.set` fields for each page. Before this local fix, a malformed structural field without its direct `span.name` raised `NoElementException("Cannot find key element in set for page: <fullname>")`. That identified the page only after `fullname` had already been parsed, but it did not identify the site or which ListPages field failed.

This follow-up keeps successful ListPages parsing, field scoping, text spacing, rating parsing, request construction, pagination, retries, and exception type unchanged. It adds the site unix name and 1-based field index to the existing malformed-field exception: `Cannot find key element in set for site: <site>, page: <fullname>, field: <n>`.

## Related Issue

Builds on [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md), and [183-pr-listpages-fetch-failure-context.md](183-pr-listpages-fetch-failure-context.md). Those drafts established ListPages field parsing, string-field value preservation, and ListPages fetch diagnostics as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Track the 1-based structural field index while parsing direct `span.set` fields.
- Include `site.unix_name`, parsed page fullname when available, and field index when a required `span.name` is missing.
- Add a focused regression proving malformed ListPages field-name markup includes site, page, and field context.

## Type Of Change

- Bug fix / diagnostics improvement
- ListPages parser context
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed ListPages field-name markup still raises `NoElementException`. | `TestPageCollectionParse.test_parse_missing_key_element_includes_site_page_and_field_context` removes the `span.name` from the title field and expects `NoElementException`. | A change that silently accepts a nameless structural field, fabricates a key, or returns a partial page rejects this local completion claim. |
| The parser error identifies the failed site, page, and field position. | The focused regression asserts `Cannot find key element in set for site: test-site, page: scp-001, field: 4`. | The RED test failed before the fix because the message only said `Cannot find key element in set for page: scp-001`. |
| Successful ListPages parsing remains unchanged. | `uv run pytest tests/unit/test_page.py::TestPageCollectionParse -q` passed 9 parser tests. | Regressions in single-page parsing, nested field scoping, multiple pages, empty results, PM rating, 5-star rating, optional fields, or existing malformed responses reject this local completion claim. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 182 tests. | Regressions in page search, source acquisition, page IDs, page publishing, direct page lookup, or site accessors reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `4cf4b9b fix(page): include context in listpages key errors`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_missing_key_element_includes_site_page_and_field_context -q` failed before the fix because the exception message was `Cannot find key element in set for page: scp-001`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionParse::test_parse_missing_key_element_includes_site_page_and_field_context -q`.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionParse -q` passed 9 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 182 tests.
- `uv run pytest tests/unit -q` passed 733 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageCollection._parse(...)` still parses normal ListPages responses into the same `PageCollection`.
- Direct nested `span.set` scoping behavior remains unchanged.
- String field spacing behavior remains unchanged.
- PM and 5-star rating parsing behavior remains unchanged.
- Existing malformed ListPages responses still raise `NoElementException`.
- A malformed structural field without a direct `span.name` now names the site, parsed page fullname, and 1-based field index.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Large crawler and publishing workflows often collect many ListPages batches across multiple sites. When one malformed structural field breaks parsing, logs should identify the site, page, and field position without storing raw HTML. This preserves the current strict parser behavior while making failure routing practical for resumable callers.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established ListPages parsing as an active practical surface by fixing nested field scoping, field text spacing, retry/fetch diagnostics, pagination behavior, and source collection helpers.
- The refreshed complexity memo continues to list parser/source collection helpers and direct parser failure messages as follow-up leads; this slice only claims malformed ListPages field-key diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, raw page source text, and account details out of upstream discussion.

## Additional Notes

This slice intentionally does not change ListPages request construction, pagination, retry policy, direct field scoping, value parsing, date/user/tag/rating conversions, returned page objects, source acquisition, page-ID acquisition, or live Wikidot behavior. It only enriches one existing malformed structural field exception path.
