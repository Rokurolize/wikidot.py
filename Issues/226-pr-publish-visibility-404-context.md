# PR Draft: Report Publish Visibility 404 Context

## Summary

`site.page.publish(...)` can retry post-save page ID resolution before source verification, metadata updates, and result return. That retry loop already treats direct `404` page-ID probes as possible Wikidot visibility lag, but when all requested attempts were exhausted the final `404` escaped as a raw `httpx.HTTPStatusError`. Plain HTTP errors do not identify the high-level publish operation, site, page, or configured attempt count, so browser-free publishing logs can lose the context needed to route the failed page.

This change converts only the exhausted post-save `404` visibility case into `NotFoundException("Cannot resolve published page id for site: <site>, page: <fullname> after <attempts> attempts")`. Non-404 HTTP failures still propagate immediately as HTTP errors, and existing `NotFoundException` or `UnexpectedException` failures from page-ID lookup still retain their existing behavior.

## Related Issue

Builds on [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md), [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [190-pr-site-page-get-direct-id-error-surface.md](190-pr-site-page-get-direct-id-error-surface.md), [197-pr-page-id-site-context.md](197-pr-page-id-site-context.md), and [203-pr-site-page-get-miss-site-context.md](203-pr-site-page-get-miss-site-context.md). Those drafts established browser-free publishing, bounded post-save page visibility polling, publish audit records, page-ID diagnostics, and site-aware page lookup failures as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Convert final exhausted post-save direct `404` page-ID lookup failures in `SitePageAccessor._resolve_post_save_page_id(...)` into site/page/attempt-aware `NotFoundException`.
- Keep non-404 `httpx.HTTPStatusError` failures outside the visibility-lag path.
- Preserve successful publish sequencing, metadata updates, source verification, create/edit result fields, and retry counts.
- Add focused public `site.page.publish(...)` regressions for exhausted `404` context and non-404 HTTP propagation.

## Type Of Change

- Browser-free publishing diagnostics improvement
- Failure-context hardening
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Exhausted post-save direct `404` page-ID lookup failures identify the site, page, and attempt count. | `TestSitePageAccessor.test_publish_reports_context_when_post_save_visibility_404_exhausts` drives `site.page.publish(...)` through two direct `404` page-ID attempts and expects `NotFoundException("Cannot resolve published page id for site: test-site, page: new-page after 2 attempts")`. | Returning a raw `httpx.HTTPStatusError`, omitting site/page/attempt context, retrying fewer than the requested attempts, or requiring live Wikidot rejects this local completion claim. |
| Non-404 HTTP failures are not reclassified as ordinary post-save visibility lag. | `TestSitePageAccessor.test_publish_surfaces_non_404_post_save_visibility_http_errors` drives a direct `500` page-ID failure and expects the original `httpx.HTTPStatusError` after one attempt. | Converting server errors into `NotFoundException`, retrying non-404 HTTP failures, or masking the HTTP status rejects this local completion claim. |
| Failed post-save page-ID resolution does not run source verification or metadata updates. | Both focused failure tests assert `set_metadata` and `refresh_source` are not called. | Running metadata updates, source verification, or result creation after unresolved page visibility rejects this local completion claim. |
| Existing publish visibility retry success behavior is unchanged. | `TestSitePageAccessor.test_publish_retries_post_save_visibility_before_returning_page_id` still passes and returns the page ID after a transient first failure. | Regressions in successful retry, create/edit branching, source verification, metadata updates, or publish result fields reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `1f8b83e fix(site): report publish visibility 404 context`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_reports_context_when_post_save_visibility_404_exhausts -q` failed before the fix because the final direct `404` raised raw `httpx.HTTPStatusError: not found`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_reports_context_when_post_save_visibility_404_exhausts -q`.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_reports_context_when_post_save_visibility_404_exhausts tests/unit/test_site.py::TestSitePageAccessor::test_publish_surfaces_non_404_post_save_visibility_http_errors tests/unit/test_site.py::TestSitePageAccessor::test_publish_retries_post_save_visibility_before_returning_page_id -q` passed 3 tests.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed 18 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 74 tests.
- `uv run pytest tests/unit -q` passed 770 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable. A bare `uv run mypy` invocation was also not accepted without explicit targets; `uv run mypy src tests` passed.

## Acceptance Criteria

- `site.page.publish(..., post_save_visibility_attempts=N)` retries direct post-save `404` page-ID failures up to `N` attempts.
- If every post-save page-ID attempt returns direct `404`, the helper raises `NotFoundException` with the site unix name, page fullname, and configured attempt count.
- Direct non-404 HTTP failures still raise the original `httpx.HTTPStatusError` immediately.
- Failed page-ID resolution does not run source verification, metadata updates, or return a `PagePublishResult`.
- Successful publish create/edit, source verification, metadata update, retry, and result/audit behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, non-goals, verification, and false-positive rejection checks.
- `Issues/README.md` records the local draft and implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Browser-free publishing workflows need failure logs that identify which saved page could not be resolved after the caller-requested visibility wait. A raw HTTP 404 does not communicate whether the failure came from a pre-save lookup, post-save visibility polling, or another direct page probe. Converting only the exhausted post-save 404 case into a contextual library exception keeps server errors visible while making ordinary page-visibility exhaustion diagnosable without raw response bodies, local rollout paths, credentials, account names, or page contents.

## Local Evidence, Not For Upstream Paste

- The broader local browser-free publishing draft records practical workflows that saved pages, retried public page-ID visibility, verified source, updated metadata, and wrote ledgers.
- The post-save visibility retry draft explicitly treats direct `404` as a bounded eventual-consistency case while preserving non-404 HTTP failures.
- Later local diagnostics drafts added site/page context to page ID, source, property, and lookup failures because plain exceptions were hard to route in multi-page automation logs.
- Keep private rollout paths, sandbox account names, page contents, credentials, raw response bodies, and thread workspace details out of upstream discussion.

## Additional Notes

This slice intentionally does not retry the `savePage` write, change direct page URL construction, change page-ID parsing, alter `Page.id` failures, add partial publish result objects, write audit rows, or change live Wikidot behavior. It only changes the final exception surface for the exhausted post-save direct `404` visibility path inside `site.page.publish(...)`.
