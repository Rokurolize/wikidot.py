# PR Draft: Surface Direct Page ID Probe Errors In Site Page Get

## Summary

`Site.page.get(...)` first searches ListPages, then falls back to a direct `/norender/true/noredirect/true` page-ID probe for pages that exist but are not yet visible in ListPages. Before this local fix, the direct fallback treated every `UnexpectedException` from page-ID acquisition as "page not found". That hid structural probe failures such as non-HTTP response objects and could convert a diagnosable page-ID fetch problem into `None` or `Page is not found: <fullname>`.

This follow-up separates the two outcomes. Missing `WIKIREQUEST.info.pageId` is now a `NotFoundException` with page context. `Site.page.get(...)` still treats `404` and page-ID `NotFoundException` as "not found", but it now lets structural `UnexpectedException` failures propagate to callers.

## Related Issue

Builds on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [186-pr-page-id-response-type-context.md](186-pr-page-id-response-type-context.md), [187-pr-page-id-property-context.md](187-pr-page-id-property-context.md), and [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md). Those drafts established direct page lookup, browser-free publishing, page-ID diagnostics, fallback page-ID context, and action/read-boundary behavior as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Change missing page-ID extraction in `PageCollection._acquire_page_ids(...)` from `UnexpectedException` to `NotFoundException`.
- Keep non-HTTP response objects classified as `UnexpectedException` with representative page context.
- Change `SitePageAccessor._get_by_direct_page_id(...)` so it swallows only `404` HTTP failures and page-ID `NotFoundException`.
- Add a focused regression proving `Site.page.get(..., raise_when_not_found=False)` surfaces unexpected direct page-ID probe errors.
- Add a focused regression proving missing `WIKIREQUEST.info.pageId` remains a page-context `NotFoundException`.

## Type Of Change

- Bug fix / diagnostics preservation
- Page lookup fallback correctness
- Exception classification cleanup
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Direct page-ID probe structural errors are not hidden by `Site.page.get(...)`. | `TestSitePageAccessor.test_get_surfaces_unexpected_direct_page_id_probe_errors` patches the ListPages search empty and direct page-ID acquisition to raise `UnexpectedException`, then expects that exception from `Site.page.get(..., raise_when_not_found=False)`. | A change that returns `None` or raises generic `Page is not found` for non-HTTP response-type errors rejects this local completion claim. |
| Missing page-ID markup is treated as "not found", not as a structural unexpected error. | `TestPageCollectionAcquire.test_acquire_page_ids_missing_id_raises_not_found_with_page_context` expects `NotFoundException("Cannot find page id: test-page")` for a direct page response without `WIKIREQUEST.info.pageId`. | A change that classifies missing page-ID markup as `UnexpectedException` rejects this local completion claim. |
| Stale ListPages direct fallback still returns a synthesized page when direct page ID is found. | `uv run pytest tests/unit/test_site.py::TestSitePageAccessor ...` includes the stale ListPages fallback test and passed. | Regressions in direct fallback construction, fullname/category/name assignment, or page ID propagation reject this local completion claim. |
| Page ID response-type diagnostics remain intact. | The adjacent page ID response-type regression still passes and asserts page-context `UnexpectedException`. | Regressions that swallow or downgrade non-HTTP page-ID responses reject this local completion claim. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 181 tests. | Regressions in page search, direct page lookup, publish, source iteration, site parsing, or page ID acquisition reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `2f7490d fix(site): surface direct page id probe errors`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_get_surfaces_unexpected_direct_page_id_probe_errors -q` failed before the fix because `Site.page.get(..., raise_when_not_found=False)` returned without raising the direct `UnexpectedException`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_get_surfaces_unexpected_direct_page_id_probe_errors -q`.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_unexpected_response_type_includes_page_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_missing_id_raises_not_found_with_page_context tests/unit/test_page.py::TestPageProperties::test_id_property_includes_page_context_when_acquire_leaves_id_missing -q` passed 18 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 181 tests.
- `uv run pytest tests/unit -q` passed 732 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Site.page.get(...)` continues to return a synthesized page when ListPages is stale but the direct page-ID probe succeeds.
- `Site.page.get(..., raise_when_not_found=False)` still returns `None` for a direct `404` probe.
- `Site.page.get(..., raise_when_not_found=False)` still returns `None` for a direct probe that has no page ID and is therefore classified as `NotFoundException`.
- `Site.page.get(...)` no longer swallows `UnexpectedException` from the direct page-ID probe.
- `PageCollection.get_page_ids()` still raises page-context `UnexpectedException` for non-HTTP response objects.
- `PageCollection.get_page_ids()` now raises page-context `NotFoundException` when the direct page response lacks `WIKIREQUEST.info.pageId`.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Direct page-ID fallback exists for practical browser-free page publishing and lookup workflows where ListPages can lag behind a newly saved page. Treating all direct probe `UnexpectedException` values as page absence makes those workflows harder to debug: transient or malformed response problems disappear behind an absent-page result. Separating not-found from unexpected response structure preserves the useful stale-ListPages fallback without hiding diagnostics.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established browser-free publishing, post-save page visibility, page-ID response diagnostics, and final page-ID fallback context as practical local surfaces.
- The refreshed complexity memo continues to list parser/source collection helpers, action/read boundaries, and direct property/fallback failure messages as follow-up leads; this slice only claims direct page-ID probe exception classification and propagation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, raw page source text, and account details out of upstream discussion.

## Additional Notes

This slice intentionally does not change ListPages query construction, direct page URL construction, duplicate page-ID URL reuse, successful page-ID extraction, `Page.id` cached reads, `Page.id` final fallback behavior, `Site.page.publish(...)`, page creation/editing, metadata updates, source verification, or live Wikidot behavior. It only stops `Site.page.get(...)` from masking structural direct page-ID probe errors as ordinary page absence.
