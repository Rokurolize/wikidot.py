# PR Draft: Validate ListPages Response Bodies

## Summary

`PageCollection.search_pages()` retrieves generated `list/ListPagesModule` markup, parses the first page, detects pager targets, and optionally fetches additional pages through retry-aware AMC. Earlier local slices made ListPages first-page and additional-page fetch failures retry-aware and site/offset-context-rich. The remaining malformed response-body paths still read `response.json()["body"]`, so an AMC response without a `body` field leaked a raw `KeyError` before the search boundary could report which site and offset produced the malformed response.

This follow-up keeps the ListPages request payload, private-site `not_ok` mapping, retry-exhausted `None` handling, pager detection, offset preservation, limit capping, field-value parsing, and page parsing unchanged. It only treats first and additional ListPages responses without JSON `body` fields as malformed generated-module responses and raises `NoElementException` with site and offset context before BeautifulSoup parsing.

## Related Issue

Builds on [041-pr-retry-listpages-search.md](041-pr-retry-listpages-search.md), [073-pr-scope-listpages-pager-detection.md](073-pr-scope-listpages-pager-detection.md), [075-pr-preserve-listpages-offset-pagination.md](075-pr-preserve-listpages-offset-pagination.md), [076-pr-retry-listpages-additional-pages.md](076-pr-retry-listpages-additional-pages.md), [077-pr-limit-listpages-pagination.md](077-pr-limit-listpages-pagination.md), [081-pr-preserve-listpages-field-spacing.md](081-pr-preserve-listpages-field-spacing.md), and [191-pr-listpages-fetch-site-context.md](191-pr-listpages-fetch-site-context.md). Those drafts established `search_pages()` as a practical retry-aware, pagination-sensitive workflow with site/offset diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Add a ListPages response-body helper that reads `response.json().get("body")`.
- Convert missing first ListPages response `body` fields into `NoElementException` with site and offset context.
- Convert missing additional ListPages response `body` fields into `NoElementException` with site and offset context.
- Preserve retry-exhausted `None` handling as `UnexpectedException`.
- Preserve private-site `not_ok` to `ForbiddenException` mapping.
- Preserve pager detection, additional-page retry use, offset calculation, limit capping, field-value spacing, and page parsing.
- Add focused regressions for missing first and additional ListPages response bodies through public `PageCollection.search_pages()`.

## Type Of Change

- Bug fix / diagnostics improvement
- ListPages response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A first ListPages response without JSON `body` fails before BeautifulSoup parsing. | `TestPageCollectionSearchPages.test_search_pages_missing_first_response_body_includes_site_and_offset_context` returns `{}` from the first AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, silently returns an empty collection, or starts parsing missing body content rejects this local completion claim. |
| An additional ListPages response without JSON `body` fails before BeautifulSoup parsing. | `TestPageCollectionSearchPages.test_search_pages_missing_additional_response_body_includes_site_and_offset_context` returns `{}` from the additional AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, returns partial first-page results, or drops the additional-page offset rejects this local completion claim. |
| Malformed ListPages response errors identify site and offset. | The focused regressions assert `ListPages response body is not found for site: test-site, offset: 500` and `ListPages response body is not found for site: test-site, offset: 600`. | An exception without site/offset context rejects this local completion claim. |
| Retry-exhausted `None` responses remain distinct from malformed response bodies. | Existing first-page and additional-page retry-exhausted tests remain green and preserve `UnexpectedException`. | A change that turns retry exhaustion into body-validation failure rejects this local completion claim. |
| Existing ListPages behavior remains green. | `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed 17 tests. | Regressions in private-site mapping, pager detection, offset preservation, retry use, limit capping, field spacing, or page parsing reject this local completion claim. |
| Page and adjacent site workflows remain green. | `uv run pytest tests/unit/test_page.py -q` passed 120 tests; `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 267 tests. | Regressions in page source/revision/vote/file/site flows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `9a0f172 fix(page): validate ListPages response bodies`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_missing_first_response_body_includes_site_and_offset_context tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_missing_additional_response_body_includes_site_and_offset_context -q` failed before the fix with `KeyError: 'body'` on both missing-body paths.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_missing_first_response_body_includes_site_and_offset_context tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_missing_additional_response_body_includes_site_and_offset_context -q` passed after the fix.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed 17 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 120 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 267 tests.
- `uv run pytest tests/unit -q` passed 763 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageCollection.search_pages()` still uses the same `list/ListPagesModule` request payload.
- First ListPages fetches still use the existing retry-aware helper.
- Additional ListPages fetches still use `site.amc_request_with_retry()`.
- Missing first ListPages response JSON `body` raises `NoElementException` naming the site and offset.
- Missing additional ListPages response JSON `body` raises `NoElementException` naming the site and offset.
- Missing response-body handling does not convert retry-exhausted `None` responses into malformed-body failures.
- Private-site mapping, pager detection, offset preservation, retry use, limit capping, field-value spacing, and page parsing remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, non-goals, verification, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

ListPages is one of wikidot.py's core read paths. If Wikidot returns a malformed generated-module response, wikidot.py should report a structured failure with the site and offset, not a raw dictionary `KeyError`, so caller logs can route the failure without preserving raw response JSON, generated HTML, credentials, local rollout paths, site content, or private search parameters.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established ListPages search as retry-aware and pagination-sensitive, with site/offset context for exhausted fetches.
- Recent response-body validation slices across private-message, forum-post, forum-category, forum-thread, site-application, site-member, page-file, page-revision, forum-post-revision, recent-changes, and page auxiliary modules showed the same raw `KeyError` failure mode at AMC response-body boundaries.
- The refreshed complexity memo continues to list raw response-body boundaries in page collection batch helpers as follow-up leads after this slice removes the direct `search_pages()` raw body reads.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated ListPages HTML, site content, and private search parameters out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, retry-exhausted `None` handling, private-site status mapping, pager detection, offset preservation, limit capping, field-value spacing, page parsing, or live Wikidot behavior. It only converts missing first and additional ListPages response `body` fields into site/offset-context `NoElementException` failures before parser work.
