# PR Draft: Include Site Context In ListPages Fetch Failures

## Summary

`PageCollection.search_pages(...)` is the public ListPages read path used by page search, page lookup, and source/file/revision follow-up workflows. Earlier local slices made the first ListPages fetch retry-aware, moved additional pager requests through the retry helper, preserved private-site status mapping, and hardened parser/pager behavior, but exhausted retry failures still raised `UnexpectedException("Failed to get ListPages page at offset: ...")` with only the offset.

This follow-up keeps request payloads, retry counts, `try_again` handling, private-site `not_ok` mapping, pager discovery, `limit` math, partial-result rejection, parsing, and exception type unchanged, but includes the site unix name in both first-page and paginated exhausted-retry failures: `Failed to get ListPages page for site: <site>, offset: <offset>`.

## Related Issue

Builds on [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [092-pr-scope-listpages-pager-detection.md](092-pr-scope-listpages-pager-detection.md), [100-pr-ignore-listpages-field-pager-markup.md](100-pr-ignore-listpages-field-pager-markup.md), [111-pr-preserve-listpages-field-text-spacing.md](111-pr-preserve-listpages-field-text-spacing.md), and [116-pr-listpages-parse-context.md](116-pr-listpages-parse-context.md), because those drafts established ListPages as a retry-aware, paginated, parser-boundary-sensitive read surface.

No upstream issue was filed from this local workspace.

## Changes

- Include site unix name in exhausted retry failures for the first ListPages page.
- Include site unix name in exhausted retry failures for additional paginated ListPages pages.
- Tighten focused regressions for first-page and additional-page exhausted retry failures.
- Preserve request bodies, retry policy, private-site status mapping, pager parsing, `limit` behavior, partial-result rejection, parsed `Page` fields, and exception type.

## Type Of Change

- Bug fix / diagnostics improvement
- ListPages fetch failure context
- Test update

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| First-page ListPages retry exhaustion still raises `UnexpectedException`. | `TestPageCollectionSearchPages.test_search_pages_raises_when_first_page_retry_is_exhausted` forces retry exhaustion and expects `UnexpectedException`. | Returning an empty collection, treating the failed response as success, or changing private-site status mapping rejects this local completion claim. |
| First-page failures identify the affected site and offset. | The focused regression asserts `Failed to get ListPages page for site: test-site, offset: 500`. | The RED test failed before the fix because the message was only `Failed to get ListPages page at offset: 500`. |
| Additional paginated ListPages retry exhaustion still raises `UnexpectedException` without returning partial results. | `TestPageCollectionSearchPages.test_search_pages_failed_retry_additional_page_raises` succeeds on the first page, receives `None` for the additional page, and expects `UnexpectedException`. | Returning only page 1 results or silently skipping the failed additional page rejects this local completion claim. |
| Additional-page failures identify the affected site and offset. | The focused regression asserts `Failed to get ListPages page for site: test-site, offset: 600`. | The RED test failed before the fix because the message was only `Failed to get ListPages page at offset: 600`. |
| ListPages behavior remains green. | `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed 15 tests; `uv run pytest tests/unit/test_page.py -q` passed 109 tests. | Regressions in basic search, transient retry success, private-site mapping, query payloads, pager scoping, additional retry requests, limit handling, or page parsing reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `7d27caa fix(page): include site in listpages fetch failures`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_raises_when_first_page_retry_is_exhausted -q` failed before the fix because the message only said `Failed to get ListPages page at offset: 500`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_raises_when_first_page_retry_is_exhausted -q`.
- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_failed_retry_additional_page_raises -q` failed before the fix because the message only said `Failed to get ListPages page at offset: 600`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_failed_retry_additional_page_raises -q`.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages -q` passed 15 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 109 tests.
- `uv run pytest tests/unit -q` passed 727 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageCollection.search_pages(...)` still uses retry-aware handling for the first ListPages page and the retry helper for additional pager requests.
- If the first ListPages page exhausts retry, the method raises `UnexpectedException` naming both the site unix name and failed offset.
- If an additional paginated ListPages page exhausts retry, the method raises `UnexpectedException` naming both the site unix name and failed offset.
- Successful page search, transient retry success, private-site `not_ok` conversion, query payload generation, pager scoping, field-value pager filtering, `limit` behavior, partial-result rejection, and parsed `Page` fields remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

ListPages is a high-traffic read helper for scripts that inspect Wikidot state without browser context. When a ListPages fetch exhausts retry, logs should identify the affected site as well as the offset so callers can diagnose the failed read without storing raw response HTML, credentials, local rollout paths, or page contents.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established ListPages as a practical workflow surface by adding first-page retry handling, retry-aware pagination, parser-boundary hardening, field-value pager isolation, text-spacing preservation, and malformed-row parse context.
- Recent context slices showed that compact site/object identifiers improve resumable ledgers without changing successful behavior.
- This slice only claims fetch failure diagnostics. It does not claim any live Wikidot behavior change.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request bodies, retry policy, private-site `ForbiddenException` mapping, pager selection, pagination batching, offset math, `limit` calculation, parsing selectors, `Page` construction, page ID/source/file/revision APIs, publishing, or live Wikidot behavior. It only adds site unix name context to existing exhausted-retry ListPages failures.
