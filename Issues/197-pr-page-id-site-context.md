# PR Draft: Include Site Context In Page ID Failures

## Summary

`PageCollection.get_page_ids()` and the `Page.id` property are shared recovery points for source, revision, vote, file, and publishing workflows. Earlier local slices made these failures page-aware, but the remaining page-ID diagnostics still named only the page fullname, for example `Cannot find page id: scp-001` or `Unexpected response type for page: scp-001`. That is still ambiguous in multi-site crawls where the same fullname exists on several Wikidot sites.

This follow-up keeps page-ID request construction, duplicate URL reuse, cached ID propagation, missing-ID classification, successful `WIKIREQUEST.info.pageId` parsing, exception types, and property lazy loading unchanged. It only adds the site unix name to three existing page-ID failure messages: non-HTTP direct response slots, direct responses missing `WIKIREQUEST.info.pageId`, and the final defensive `Page.id` property fallback when acquisition returns without setting `_id`.

## Related Issue

Builds on [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [186-pr-page-id-response-type-context.md](186-pr-page-id-response-type-context.md), [187-pr-page-id-property-context.md](187-pr-page-id-property-context.md), [190-pr-site-page-get-direct-id-error-surface.md](190-pr-site-page-get-direct-id-error-surface.md), [196-pr-page-property-site-context.md](196-pr-page-property-site-context.md), and the broader page-detail/source collection drafts. Those drafts established page ID lookup as a practical local recovery surface and showed that compact site/page exception context improves audit ledgers without changing successful behavior.

No upstream issue was filed from this local workspace.

## Changes

- Include `site.unix_name` and representative page fullname in `PageCollection.get_page_ids()` non-HTTP response-type `UnexpectedException` messages.
- Include `site.unix_name` and representative page fullname in `PageCollection.get_page_ids()` missing `WIKIREQUEST.info.pageId` `NotFoundException` messages.
- Include `self.site.unix_name` and `self.fullname` in the defensive `Page.id` property fallback `NotFoundException`.
- Preserve duplicate URL grouping, request URL order, cached ID propagation, successful ID assignment to all duplicate pages, exception classes, and lazy property behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Multi-site page-ID audit context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Non-HTTP page-ID response slots still raise `UnexpectedException`, but identify both site and page. | `TestPageCollectionAcquire.test_acquire_page_ids_unexpected_response_type_includes_page_context` asserts `Unexpected response type for site: test-site, page: test-page`. | Swallowing the response, changing exception type, changing request behavior, or leaving a page-only message rejects this local completion claim. |
| Direct page responses missing `WIKIREQUEST.info.pageId` still raise `NotFoundException`, but identify both site and page. | `TestPageCollectionAcquire.test_acquire_page_ids_missing_id_raises_not_found_with_page_context` asserts `Cannot find page id for site: test-site, page: test-page`. | Reclassifying missing ID markup as `UnexpectedException`, returning a fabricated page ID, or leaving a page-only message rejects this local completion claim. |
| `Page.id` still attempts lazy acquisition and raises only if `_id` remains unset, but its fallback identifies both site and page. | `TestPageProperties.test_id_property_includes_page_context_when_acquire_leaves_id_missing` patches acquisition to return without setting `_id` and asserts the site/page message. | Bypassing lazy acquisition, changing successful ID reads, or leaving a page-only fallback rejects this local completion claim. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 182 tests. | Regressions in source, revisions, votes, files, ListPages, direct page lookup, source iterators, or publish-adjacent page workflows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `1ad1996 fix(page): include site in page id failures`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_unexpected_response_type_includes_page_context -q` failed before the fix because the message was `Unexpected response type for page: test-page, type: <class 'wikidot.common.exceptions.UnexpectedException'>`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_unexpected_response_type_includes_page_context -q`.
- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_missing_id_raises_not_found_with_page_context -q` failed before the fix because the message was `Cannot find page id: test-page`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_missing_id_raises_not_found_with_page_context -q`.
- RED: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_id_property_includes_page_context_when_acquire_leaves_id_missing -q` failed before the fix because the message was `Cannot find page id: test-page`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_id_property_includes_page_context_when_acquire_leaves_id_missing -q`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_unexpected_response_type_includes_page_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_missing_id_raises_not_found_with_page_context tests/unit/test_page.py::TestPageProperties::test_id_property_includes_page_context_when_acquire_leaves_id_missing -q` passed 3 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 182 tests.
- `uv run pytest tests/unit -q` passed 733 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageCollection.get_page_ids()` still batches direct page-ID lookups through the same `norender/true/noredirect/true` URLs.
- Cached ID propagation and duplicate URL reuse remain unchanged.
- Successful `WIKIREQUEST.info.pageId` parsing still assigns the parsed ID to every page sharing that request URL.
- Non-HTTP response slots still raise `UnexpectedException`, now with site/page context.
- Missing page-ID markup still raises `NotFoundException`, now with site/page context.
- The `Page.id` property still lazily calls `PageCollection(...).get_page_ids()` and returns an acquired ID when present; its defensive fallback now includes site/page context.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Page ID acquisition is a common fallback when ListPages data is stale or incomplete and is used by source, revision, vote, file, and publishing paths. In multi-site automation, page-only ID errors force downstream ledgers to rely on surrounding context to identify which site failed. Adding the site unix name makes these existing strict failures self-contained while preserving request behavior and exception classes.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified page ID lookup as a recovery point for source, revision, vote, file, and publishing workflows.
- Recent site-context slices showed the same low-risk pattern: add compact site/object identifiers to existing plain-text exceptions without changing successful behavior.
- This slice only claims page-ID diagnostics. It does not claim any live Wikidot behavior change.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally keeps the existing representative-page wording for duplicate URL groups. Pages sharing the same URL still receive the same parsed ID, and a failed URL reports the first page in that request group just as the previous page-only message did.
