# PR Draft: Validate Recent Changes Response Bodies

## Summary

`Site.get_recent_changes()` retrieves generated `changes/SiteChangesListModule` response bodies for the first recent-changes page and, when pagination is present, for additional pages. Earlier local slices made this workflow retry-aware, site-context-rich for exhausted fetches, parser-context-rich for malformed rows, text-spacing-preserving, comment-pager-aware, and batched for later pages. The remaining malformed response-body paths still read `response.json()["body"]`, so an AMC response without a `body` field leaked a raw `KeyError` before the recent-changes boundary could report which site and page produced the malformed response.

This follow-up keeps request payloads, retry-exhausted `None` handling, zero-limit fast return, empty first-page behavior, first-page-before-pager behavior, limit-based pagination trimming, batched later-page requests, pager parsing, comment-pager filtering, successful row parsing, text spacing, and parser exception context unchanged. It only treats recent-changes responses without JSON `body` fields as malformed generated-module responses and raises `NoElementException` with site and recent-changes page context before BeautifulSoup parsing.

## Related Issue

Builds on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), and [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md). Those drafts established recent-changes acquisition as a practical retry-aware workflow with parser scoping, pagination handling, text preservation, and site/page diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Read the first recent-changes response body with `response.json().get("body")`.
- Read paginated recent-changes response bodies with `response.json().get("body")`.
- Convert missing `changes/SiteChangesListModule` response `body` fields into `NoElementException` with site and recent-changes page context.
- Preserve retry-exhausted `None` handling as `UnexpectedException`.
- Preserve zero-limit behavior, successful first-page parsing, empty first-page return, structural pager parsing, comment-pager filtering, paginated batch requests, limit-based page trimming, row parser context, and text-spacing behavior.
- Add focused regressions for missing first-page and paginated recent-changes response bodies through the public `Site.get_recent_changes()` API.

## Type Of Change

- Bug fix / diagnostics improvement
- Recent changes response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A first-page recent-changes response without JSON `body` fails before BeautifulSoup parsing. | `TestSiteGetRecentChanges.test_get_recent_changes_first_page_missing_response_body_includes_site_context` returns `{}` from the first AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, fabricates an empty changes list from missing `body`, or enters parser work rejects this local completion claim. |
| A paginated recent-changes response without JSON `body` identifies the affected page. | `TestSiteGetRecentChanges.test_get_recent_changes_paginated_missing_response_body_includes_site_context` returns a valid first response with pager page 2 and `{}` for page 2, then expects `NoElementException`. | A generic pagination failure, raw `KeyError`, wrong page number, or silent truncation rejects this local completion claim. |
| Malformed recent-changes response errors identify the site and recent-changes page number. | The focused regressions assert `Recent changes response body is not found for site: test, page: 1` and `Recent changes response body is not found for site: test, page: 2`. | An exception without site/page context rejects this local completion claim. |
| Retry-exhausted `None` responses remain distinct from malformed response bodies. | Existing first-page and paginated retry-exhausted tests remain green and preserve `UnexpectedException`. | A change that turns retry exhaustion into body-validation failure rejects this local completion claim. |
| Existing recent-changes behavior remains green. | `uv run pytest tests/unit/test_site.py -q` passed 71 tests. | Regressions in successful parsing, empty response behavior, limit handling, retry handling, pager handling, batched pagination, comment-pager filtering, parse context, or text spacing reject this local completion claim. |
| Adjacent site/page workflows remain green. | `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_page.py -q` passed 237 tests. | Regressions in site accessors, site member/application flows, or page workflows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `f700e69 fix(site): validate recent changes response bodies`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_missing_response_body_includes_site_context -q` failed before the first-page fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_missing_response_body_includes_site_context -q` passed after the first-page fix.
- RED: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_missing_response_body_includes_site_context -q` failed before the paginated fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_missing_response_body_includes_site_context -q` passed after the paginated fix.
- `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_missing_response_body_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_missing_response_body_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_success tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_retry_exhaustion_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_retry_exhaustion_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_batches_paginated_pages tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_batches_only_pages_needed_for_limit -q` passed 7 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 71 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_page.py -q` passed 237 tests.
- `uv run pytest tests/unit -q` passed 759 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Site.get_recent_changes()` still uses retry-aware AMC and the same `changes/SiteChangesListModule` request payload for page 1.
- `Site.get_recent_changes()` still uses retry-aware AMC and the same per-page request payloads for later pages.
- A missing first-page response JSON `body` raises `NoElementException` naming the site and recent-changes page 1.
- A missing later-page response JSON `body` raises `NoElementException` naming the site and affected recent-changes page number.
- Missing response-body handling does not convert retry-exhausted `None` responses into malformed-body failures.
- Zero-limit behavior, successful first-page parsing, empty first-page return, structural pager parsing, comment-pager filtering, batched pagination, limit-based page trimming, row parser context, and text-spacing behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, non-goals, verification, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Recent changes inspection depends on Wikidot returning generated module responses with `body` fields. If one response is malformed, wikidot.py should report a structured failure with the site and recent-changes page number, not a raw dictionary `KeyError`, so caller logs can route the failure without preserving raw response JSON, generated HTML, credentials, local rollout paths, or private recent-change comments.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established recent-changes acquisition as retry-aware, batched for later pages, parser-scoped, pager-filtered, and text-preserving.
- Recent response-body validation slices in private-message, forum-post, forum-category, forum-thread, site-application, site-member, page-file, page-revision, and forum-post-revision modules showed the same raw `KeyError` failure mode at AMC response-body boundaries.
- The refreshed complexity memo continues to list raw response-body boundaries in `page` as follow-up leads after this slice removes the remaining `site` direct `response.json()["body"]` reads.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated recent-changes HTML, and private edit comments out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, retry-exhausted `None` handling, zero-limit behavior, empty first-page behavior, first-page-before-pager behavior, structural pager parsing, comment-pager filtering, batched later-page requests, limit-based page trimming, row parsing, text spacing, or live Wikidot behavior. It only converts missing recent-changes response `body` fields into site/page-context `NoElementException` failures before parser work.
