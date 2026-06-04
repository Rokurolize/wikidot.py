# PR Draft: Clear Page-Bound Caches After Destroy

## Summary

`Page.destroy()` now validates the `deletePage` action response before accepting deletion success, but the original `Page` object could still retain read caches populated before the delete. That means callers could delete a page and then keep reading cached `source`, `revisions`, `votes`, `metas`, `discussion`, or `files` from the same local object without any fresh remote check.

This follow-up clears those page-bound caches after successful delete status validation. The page identity and known page ID are left intact for caller bookkeeping, while stale read data is no longer reused as if the deleted page still existed.

## Related Issue

Builds on [248-pr-page-delete-action-status-context.md](248-pr-page-delete-action-status-context.md), [259-pr-page-edit-local-cache-sync.md](259-pr-page-edit-local-cache-sync.md), [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [262-pr-page-edit-revision-count-sync.md](262-pr-page-edit-revision-count-sync.md), and [266-pr-page-rename-file-cache-invalidation.md](266-pr-page-rename-file-cache-invalidation.md). Those drafts established action-status validation and local cache consistency as practical page mutation requirements.

No upstream issue was filed from this local workspace.

## Changes

- Clear `_source`, `_revisions`, `_votes`, `_metas`, `_discussion`, `_discussion_checked`, and `_files` after a successful `Page.destroy()`.
- Preserve failed-delete behavior by clearing caches only after the existing `deletePage` status gate succeeds.
- Preserve page identity and known page ID so callers can still log or inspect the object that was deleted.
- Add a focused regression that seeds every page-bound read cache before a successful delete and asserts each cache is cleared afterward.

## Type Of Change

- Page deletion local-state consistency
- Cache invalidation
- Browser-free page mutation ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Successful `Page.destroy()` clears page-bound read caches from the deleted page object. | `TestPageWriteMethods.test_destroy_success_clears_page_bound_caches` seeds source, revisions, votes, metas, discussion, and files caches, calls `destroy()`, and asserts each cache is unset. | Returning cached page data after confirmed delete rejects this local completion claim. |
| Failed delete responses do not clear local caches. | The implementation clears caches only after `_require_page_action_status(...)` succeeds and existing missing-status delete tests continue to pass. | Clearing caches before delete status validation rejects this local completion claim. |
| Existing page write and page-bound read behavior remains intact. | `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_page.py::TestPageProperties tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py -q` passed 128 tests. | Regressions in page write methods, page properties, files, revisions, or votes reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `9c2fe8e fix(page): clear caches after destroy`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_destroy_success_clears_page_bound_caches -q` failed before the fix because `_source` and the other seeded page-bound caches survived successful `destroy()`.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_destroy_success_clears_page_bound_caches -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_page.py::TestPageProperties tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py -q` passed 128 tests.
- `uv run --extra test pytest tests/unit -q` passed 820 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Successful `Page.destroy()` calls clear the original page object's source, revisions, votes, metas, discussion, discussion-checked flag, and files caches.
- Missing or non-`ok` delete action statuses still prevent cache clearing.
- Page identity fields and known page ID remain available for caller bookkeeping after deletion.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Deletion is a stronger lifecycle transition than edit, vote, parent update, or rename. Once the remote page has been deleted, local read caches from before the delete should not make the object look like the page is still readable. Clearing page-bound caches after the existing status gate keeps successful delete semantics coherent without changing the delete request or failed-delete behavior.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts hardened `Page.destroy()` action-status validation and several page cache invalidation paths. This slice applies the same principle to the delete lifecycle boundary.
- This slice intentionally targets only cached read data on the original `Page` object; page ID invalidation, site-level page registries, live Wikidot behavior, and delete workflows in other modules remain separate boundaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved page contents, source text from real pages, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This is a local-state consistency fix. It does not alter the delete action request, status parsing, exception mapping, or page identity fields; it only prevents a deleted page object from serving cached read data captured before deletion.
