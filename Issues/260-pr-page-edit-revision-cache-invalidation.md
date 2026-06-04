# PR Draft: Invalidate Page Edit Revision Cache

## Summary

`Page.edit(...)` updates the page through `Page.create_or_edit(...)` and, after the previous local cache-sync slice, updates the calling `Page` object's title and source cache after a successful save. One adjacent stale-cache gap remained: if the caller had already loaded `page.revisions`, the original `Page` instance kept that old `PageRevisionCollection` after a successful edit. The next `page.revisions` read could therefore return a pre-edit revision list even though the edit had just created a new revision.

This follow-up keeps `Page.create_or_edit(...)`, save request construction, edit-lock handling, source defaulting, source cache synchronization, and the `Page.edit(...)` return value intact. After `Page.create_or_edit(...)` succeeds, `Page.edit(...)` now invalidates the calling page object's local revision cache so the next revision access fetches fresh history.

## Related Issue

Builds on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), and [259-pr-page-edit-local-cache-sync.md](259-pr-page-edit-local-cache-sync.md). Those drafts established browser-free page editing and publishing as practical workflow surfaces, made page revision reads fail visibly, hardened the edit action/read boundary, and synchronized successful edit source state on the calling page object.

No upstream issue was filed from this local workspace.

## Changes

- Invalidate the calling `Page` object's cached `PageRevisionCollection` after a successful `Page.edit(...)`.
- Preserve the existing edited-page return value from `Page.create_or_edit(...)`.
- Preserve local title and source cache synchronization from the prior slice.
- Add a focused regression for successful edit revision-cache invalidation.
- Preserve login checks, current-source defaulting, force-edit lock release, explicit empty source handling, save response validation, stale ListPages fallback, and publish helper behavior.

## Type Of Change

- Page edit cache consistency
- Revision history cache invalidation
- Browser-free page write ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A successful `Page.edit(...)` invalidates the calling page object's cached revisions. | `TestPageEdit.test_edit_invalidates_local_revision_cache` seeds `_revisions`, performs a successful edit, and asserts `_revisions is None`. | Reusing a pre-edit revision collection after a successful edit rejects this local completion claim. |
| `Page.edit(...)` still returns the edited page object from `Page.create_or_edit(...)`. | The same focused regression asserts the returned object is the object returned by the patched `Page.create_or_edit(...)`. | Replacing the return value with the calling page object rejects this local completion claim. |
| Existing `Page.edit(...)` title/source cache behavior remains intact. | `TestPageEdit.test_edit_updates_local_title_and_source_cache` remains in the adjacent test slice. | Regressing caller title or source cache synchronization rejects this local completion claim. |
| Existing `Page.edit(...)`, `Page.create_or_edit(...)`, page property, and publish behavior remains intact. | `uv run --extra test pytest tests/unit/test_page.py::TestPageEdit tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageProperties tests/unit/test_site.py::TestSitePageAccessor -q` passed 52 tests. | Regressions in login guards, source defaulting, force edit, empty source, revision reads, stale ListPages fallback, or publish create/edit behavior reject this local completion claim. |
| Adjacent page and site behavior remains unchanged. | `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 219 tests. | Regressions in page or site unit tests reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `32fd2f0 fix(page): invalidate edit revision cache`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageEdit::test_edit_invalidates_local_revision_cache -q` failed before the fix because `_revisions` still contained the old `PageRevisionCollection` after a successful edit.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageEdit::test_edit_invalidates_local_revision_cache -q` passed.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageEdit tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageProperties tests/unit/test_site.py::TestSitePageAccessor -q` passed 52 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 219 tests.
- `uv run --extra test pytest tests/unit -q` passed 810 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Successful `Page.edit(...)` calls clear the calling `Page` object's cached revisions after the save succeeds.
- The next `page.revisions` access can acquire fresh revision history instead of returning a pre-edit cache.
- `Page.edit(...)` still returns the edited `Page` object produced by `Page.create_or_edit(...)`.
- Successful edit title and source cache synchronization remains intact.
- Failed edit attempts do not gain a new revision-cache invalidation path before the existing exceptions are raised.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

`Page.edit(...)` is part of the browser-free page writing surface used by direct page automation and higher-level publish helpers. A successful edit creates a new page revision, so a caller that had already loaded `page.revisions` should not keep seeing the old revision list after the write completes. Invalidating the local revision cache keeps direct edit workflows consistent with the existing lazy revision acquisition model without changing save requests, page lookup, returned objects, or live Wikidot behavior.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established browser-free page publishing, create/edit fallback behavior, source verification, page edit login boundaries, edit-lock diagnostics, save status diagnostics, page revision read diagnostics, and Page.edit local source cache synchronization as practical workflow surfaces.
- This slice intentionally targets only post-success revision-cache invalidation on the original `Page` instance; page creation, edit-lock acquisition, save response validation, revision fetching, metadata updates, source verification, retry policy, and live Wikidot behavior remain separate boundaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved page contents, source text from real pages, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `Page.create_or_edit(...)`, the `Page.edit(...)` return type, stale ListPages fallback behavior, metadata writes, source refresh behavior, publish result fields, or exception handling. It only invalidates the calling `Page` object's cached revision collection after the existing successful edit path has completed.
