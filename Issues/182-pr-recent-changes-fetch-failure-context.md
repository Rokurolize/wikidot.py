# PR Draft: Include Site Context In Recent-Changes Fetch Failures

## Summary

`Site.get_recent_changes(...)` is the public read helper for `changes/SiteChangesListModule`. Earlier local slices made that path retry-aware, batched later pages, scoped parser boundaries, preserved text spacing, and added malformed-item parse context, but exhausted retry failures still raised `UnexpectedException("Cannot retrieve recent changes page: ...")` with only the recent-changes page number.

This follow-up keeps retry-aware recent-changes acquisition, first-page-before-pager behavior, batched later-page fetches, `limit` handling, empty-result behavior, parser scoping, text extraction, and exception type unchanged, but includes the site unix name in first-page and later-page exhausted-retry failures: `Cannot retrieve recent changes for site: <site>, page: <page>`.

## Related Issue

Builds on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), and [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), because those drafts established recent changes as a retry-aware, paginated, parser-boundary-sensitive, read-heavy workflow surface.

No upstream issue was filed from this local workspace.

## Changes

- Include site unix name in exhausted retry failures for the first recent-changes page.
- Include site unix name in exhausted retry failures for paginated recent-changes pages after page 1.
- Add focused regressions for first-page and paginated exhausted retry failures.
- Preserve request payloads, retry policy, pagination batching, `limit` math, empty-response behavior, parser selectors, comment filtering, text spacing, `SiteChange` fields, and exception type.

## Type Of Change

- Bug fix / diagnostics improvement
- Recent-changes fetch failure context
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| First-page recent-changes retry exhaustion still raises `UnexpectedException`. | `TestSiteGetRecentChanges.test_get_recent_changes_first_page_retry_exhaustion_includes_site_context` forces `(None,)` from retry handling and expects `UnexpectedException`. | Returning an empty list, parsing a missing response, or silently skipping page 1 rejects this local completion claim. |
| First-page failures identify the affected site and page. | The focused regression asserts `Cannot retrieve recent changes for site: test, page: 1`. | The RED test failed before the fix because the message was only `Cannot retrieve recent changes page: 1`. |
| Paginated recent-changes retry exhaustion still raises `UnexpectedException`. | `TestSiteGetRecentChanges.test_get_recent_changes_paginated_retry_exhaustion_includes_site_context` succeeds on page 1, exhausts page 2, and expects `UnexpectedException`. | Returning partial results after page 1 or silently stopping at page 2 rejects this local completion claim. |
| Paginated failures identify the affected site and page. | The focused regression asserts `Cannot retrieve recent changes for site: test, page: 2`. | The RED test failed before the fix because the message was only `Cannot retrieve recent changes page: 2`. |
| Recent-changes behavior remains green. | `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 15 tests; `uv run pytest tests/unit/test_site.py -q` passed 67 tests. | Regressions in normal parsing, transient retry success, empty results, limit handling, pager filtering, batching, comment isolation, text spacing, or site helpers reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `30aaa07 fix(site): include site in recent changes fetch failures`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_retry_exhaustion_includes_site_context -q` failed before the fix because the message only said `Cannot retrieve recent changes page: 1`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_retry_exhaustion_includes_site_context -q`.
- RED: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_retry_exhaustion_includes_site_context -q` failed before the fix because the message only said `Cannot retrieve recent changes page: 2`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_retry_exhaustion_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_retry_exhaustion_includes_site_context -q`.
- `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 15 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 67 tests.
- `uv run pytest tests/unit -q` passed 727 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Site.get_recent_changes(...)` still uses retry-aware AMC requests for page 1 and later pages.
- If page 1 retry handling is exhausted, the method raises `UnexpectedException` naming both the site unix name and page 1.
- If a later paginated retry is exhausted, the method raises `UnexpectedException` naming both the site unix name and failed page number.
- Successful recent-change parsing, transient retry success, empty responses, zero and positive `limit` behavior, pager parsing, batched later-page requests, comment-markup filtering, comment-pager filtering, text spacing, and `SiteChange` field semantics remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Recent-changes reads are commonly used for read-only audit and reconciliation workflows. When fetching a recent-changes page exhausts retry, logs should identify the affected site as well as the recent-changes page number so callers can diagnose the failed read without storing raw response HTML, credentials, local rollout paths, or page contents.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established recent changes as a practical workflow surface by adding retry-aware fetching, batching, parser-boundary hardening, authored-comment isolation, text-spacing preservation, and malformed-item parse context.
- Recent context slices showed that compact site/object identifiers improve resumable ledgers without changing successful behavior.
- This slice only claims fetch failure diagnostics. It does not claim any live Wikidot behavior change.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved recent-change comments out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, retry policy, page batching, limit math, structural pager discovery, top-level change filtering, title/date/revision/user extraction rules, comment extraction, flags, `SiteChange` fields, page APIs, publishing, or live Wikidot behavior. It only adds site unix name context to existing exhausted-retry failures.
