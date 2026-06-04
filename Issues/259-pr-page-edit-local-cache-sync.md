# PR Draft: Sync Page Edit Local Title And Source Cache

## Summary

`Page.edit(...)` delegates the write to `Page.create_or_edit(...)` and returns the edited `Page` object from that helper. That return value was updated with the submitted title and source, but the original `Page` instance used to call `edit(...)` kept its old `title` and empty or stale `_source` cache. Callers that keep using the same page object after a successful edit could therefore observe stale local state even though the edit had succeeded.

This follow-up keeps `Page.create_or_edit(...)`, save request construction, edit-lock handling, stale ListPages fallback behavior, and the `Page.edit(...)` return value intact. After `Page.create_or_edit(...)` succeeds, `Page.edit(...)` now synchronizes the caller's local `title` and `source` cache to the submitted edit. Failed edit attempts still raise before local state is updated.

## Related Issue

Builds on [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), and [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md). Those drafts established browser-free page editing and publishing as practical workflow surfaces, hardened the edit action/read boundary, and established the adjacent pattern that successful mutation helpers update local state only after action success is classified.

No upstream issue was filed from this local workspace.

## Changes

- Synchronize the calling `Page` object's `title` after a successful `Page.edit(...)`.
- Synchronize the calling `Page` object's cached `source` as a `PageSource` bound to the same original `Page` instance after a successful edit.
- Preserve the existing edited-page return value from `Page.create_or_edit(...)`.
- Add a focused regression for successful `Page.edit(...)` local title/source cache synchronization.
- Preserve login checks, current-source defaulting, force-edit lock release, explicit empty source handling, save response validation, stale ListPages fallback, and publish helper behavior.

## Type Of Change

- Page edit cache consistency
- Browser-free page write ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A successful `Page.edit(title=..., source=...)` updates the returned edited page object. | `TestPageEdit.test_edit_updates_local_title_and_source_cache` asserts the returned page title and source. | Regressing the existing return-object behavior rejects this local completion claim. |
| A successful `Page.edit(title=..., source=...)` updates the calling `Page` object's `title`. | The same focused regression asserts `mock_page_with_id.title == "Updated Title"`. | Leaving the caller with the pre-edit title rejects this local completion claim. |
| A successful `Page.edit(title=..., source=...)` updates the calling `Page` object's cached source and binds it to the same original page object. | The same focused regression asserts `_source.wiki_text == "Updated source"` and `_source.page is mock_page_with_id`. | Storing no source, storing stale source, or binding the cache to a different returned page object rejects this local completion claim. |
| Existing `Page.edit(...)` behavior remains intact for login guard, force-edit payloads, empty source, create/edit, and publish paths. | `uv run --extra test pytest tests/unit/test_page.py::TestPageEdit tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_site.py::TestSitePageAccessor -q` passed 34 tests. | Regressions in unauthenticated guard behavior, force lock release, empty source handling, stale ListPages fallback, or publish create/edit behavior reject this local completion claim. |
| Adjacent page and site behavior remains unchanged. | `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 218 tests. | Regressions in page or site unit tests reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `464b830 fix(page): sync edit local source cache`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageEdit::test_edit_updates_local_title_and_source_cache -q` failed before the fix because the calling page title remained `Original Title` after the successful edit.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageEdit::test_edit_updates_local_title_and_source_cache -q` passed.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageEdit tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_site.py::TestSitePageAccessor -q` passed 34 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 218 tests.
- `uv run --extra test pytest tests/unit -q` passed 809 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Successful `Page.edit(...)` calls update the calling `Page` object's local title after the save succeeds.
- Successful `Page.edit(...)` calls update the calling `Page` object's cached source after the save succeeds.
- The cached source object is bound to the same calling `Page` instance.
- `Page.edit(...)` still returns the edited `Page` object produced by `Page.create_or_edit(...)`.
- Failed edit attempts do not gain a new local-state update path before the existing exceptions are raised.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

`Page.edit(...)` is part of the browser-free page writing surface used by higher-level publish helpers and direct page automation. After a successful edit, callers should not need to discard the object they already hold just to avoid stale local title or source state. Synchronizing the successful mutation result with the caller's local cache makes `Page.edit(...)` behave more like adjacent mutation helpers such as metadata setters and `ForumPost.edit(...)`, while preserving the existing returned page object for callers that already use it.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established browser-free page publishing, create/edit fallback behavior, source verification, page edit login boundaries, edit-lock diagnostics, save status diagnostics, and forum-post edit local-state guards as practical workflow surfaces.
- This slice intentionally targets only post-success local cache synchronization on the original `Page` instance; page creation, edit-lock acquisition, save response validation, metadata updates, source verification, retry policy, and live Wikidot behavior remain separate boundaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved page contents, source text from real pages, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `Page.create_or_edit(...)`, the `Page.edit(...)` return type, stale ListPages fallback behavior, metadata writes, source refresh behavior, publish result fields, or exception handling. It only updates the calling `Page` object's local title and source cache after the existing successful edit path has completed.
