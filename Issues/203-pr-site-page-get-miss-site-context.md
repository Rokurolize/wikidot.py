# PR Draft: Include Site Context In Page Lookup Misses

## Summary

`Site.page.get(fullname)` first searches ListPages, then falls back to a direct `/norender/true/noredirect/true` page-ID probe for pages that exist but are not yet visible in ListPages. Earlier local slices made the direct probe diagnostics site-aware, but the final ordinary miss still raised only `Page is not found: <fullname>` when `raise_when_not_found=True`.

This follow-up keeps ListPages lookup, direct page-ID fallback, `404` handling, missing page-ID classification, `raise_when_not_found=False`, page synthesis for stale ListPages, publish/create callers, and exception type unchanged. It only adds the site unix name to the final ordinary page lookup miss: `Page is not found for site: <site>, page: <fullname>`.

## Related Issue

Builds on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [190-pr-site-page-get-direct-id-error-surface.md](190-pr-site-page-get-direct-id-error-surface.md), [197-pr-page-id-site-context.md](197-pr-page-id-site-context.md), and [196-pr-page-property-site-context.md](196-pr-page-property-site-context.md). Those drafts established `Site.page.get(...)` as a practical fallback path for stale ListPages, direct page-ID probing, browser-free publishing, and site-aware page-ID/property diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Include `self.site.unix_name` and the requested fullname in the final `Site.page.get(...)` `NotFoundException` when both ListPages lookup and direct page-ID fallback miss.
- Add a focused regression proving a direct `404` miss with default `raise_when_not_found=True` raises the new site/page message.
- Preserve successful ListPages hits, stale-ListPages direct page-ID recovery, `raise_when_not_found=False` returning `None`, direct `404` classification, page-ID `NotFoundException` classification, and structural direct probe error propagation.

## Type Of Change

- Bug fix / diagnostics improvement
- Page lookup miss ledger context
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Ordinary page lookup misses still raise `NotFoundException` when `raise_when_not_found=True`. | `TestSitePageAccessor.test_get_not_found_raises_with_site_context` patches ListPages to return empty and direct page-ID lookup to raise `HTTPStatusError(404)`, then expects `NotFoundException`. | Returning `None`, changing the exception type, or fabricating a page rejects this local completion claim. |
| The lookup miss identifies the affected site and requested page fullname. | The focused regression asserts `Page is not found for site: test-site, page: missing`. | The RED test failed before the fix because the message was only `Page is not found: missing`. |
| `raise_when_not_found=False` and direct fallback behavior remain green. | `uv run pytest tests/unit/test_site.py::TestSitePageAccessor tests/unit/test_page.py tests/unit/test_site.py -q` passed 185 tests. | Regressions in `None` return behavior, stale ListPages direct page-ID recovery, direct probe structural error propagation, publish helpers, or page/site workflows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `8c08582 fix(site): include site in page lookup misses`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_get_not_found_raises_with_site_context -q` failed before the fix because `Site.page.get("missing")` raised `Page is not found: missing`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_get_not_found_raises_with_site_context -q`.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor tests/unit/test_page.py tests/unit/test_site.py -q` passed 185 tests.
- `uv run pytest tests/unit -q` passed 736 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Site.page.get(...)` continues to return a ListPages result when the page is found by fullname.
- `Site.page.get(...)` continues to return a synthesized page when ListPages is stale but the direct page-ID probe succeeds.
- `Site.page.get(..., raise_when_not_found=False)` continues to return `None` for direct `404` and page-ID `NotFoundException` misses.
- `Site.page.get(..., raise_when_not_found=True)` raises `NotFoundException` naming both site unix name and requested fullname when both lookup paths miss.
- `Site.page.get(...)` still lets structural `UnexpectedException` direct page-ID probe failures propagate.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Page lookup misses can happen during browser-free publishing, source collection, and migration scripts that touch multiple Wikidot sites. If a missing-page log line only names the page fullname, callers need surrounding ledger context to distinguish same-name pages on different sites. Adding the site unix name makes the existing strict miss self-contained without changing lookup behavior or live Wikidot requests.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established `Site.page.get(...)`, direct page-ID fallback, post-save visibility retries, and browser-free publishing as practical local surfaces.
- Recent site-context slices showed the same low-risk pattern: add compact site/object identifiers to existing plain-text exceptions without changing successful behavior.
- This slice only claims the final ordinary page lookup miss. It does not claim direct probe classification, page-ID parsing, publishing, or live Wikidot behavior changes.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change ListPages query construction, direct page URL construction, duplicate page-ID URL reuse, successful page-ID extraction, direct `404` handling, missing page-ID handling, `raise_when_not_found=False`, `Site.page.publish(...)`, page creation/editing, metadata updates, source verification, or live Wikidot behavior. It only adds site/page context to the final `Site.page.get(...)` miss exception.
