# PR Draft: Invalidate Page File Cache After Rename

## Summary

`Page.rename(...)` updates the calling `Page` object's `fullname`, `category`, and `name` after a successful `renamePage` action. One related cache was left behind: `_files` can contain `PageFile` entries whose static `url` was parsed from `/local--files/<old-page-name>/...`. After a successful rename, reusing that cached `PageFileCollection` can expose file URLs tied to the previous page path.

This follow-up invalidates `_files` after the rename action status is validated and the local page identity is updated. The next `page.files` access then reacquires file metadata for the renamed page instead of reusing stale URLs.

## Related Issue

Builds on [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md), [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), and [247-pr-page-rename-action-status-context.md](247-pr-page-rename-action-status-context.md). Those drafts established cached page file acquisition as a useful performance surface and rename action-status validation as the safe point for local mutation.

No upstream issue was filed from this local workspace.

## Changes

- Clear `Page._files` after a successful `Page.rename(...)`.
- Keep rename failure behavior unchanged by clearing the cache only after the existing `renamePage` status gate succeeds.
- Add a focused regression that seeds cached file metadata with an old `/local--files/test-page/...` URL and verifies the cache is dropped after a successful rename.

## Type Of Change

- Page rename local-state consistency
- Page file cache invalidation
- Browser-free page mutation ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Successful `Page.rename(...)` invalidates cached file metadata tied to the old page path. | `TestPageWriteMethods.test_rename_success_invalidates_cached_files` seeds `_files` with a `PageFile.url` under `/local--files/test-page/...`, calls `rename("component:new-name")`, and asserts `_files is None`. | Reusing the old `PageFileCollection` after rename rejects this local completion claim. |
| Rename failure paths do not mutate the file cache or local page identity before action status validation. | The implementation clears `_files` only after `_require_page_action_status(...)` returns and existing missing-status rename tests continue to pass. | Clearing `_files` or changing `fullname`, `category`, or `name` before status validation rejects this local completion claim. |
| Existing page write and file acquisition behavior remains intact. | `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_page_file.py -q` passed 105 tests. | Regressions in page write methods, page file acquisition, or cached page-file reuse reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `9460adf fix(page): invalidate file cache after rename`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_rename_success_invalidates_cached_files -q` failed before the fix because `_files` still referenced the cached `PageFileCollection` containing the old `/local--files/test-page/...` URL.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_rename_success_invalidates_cached_files -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_page_file.py -q` passed 105 tests.
- `uv run --extra test pytest tests/unit -q` passed 819 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Successful `Page.rename(...)` calls leave the calling page object's `_files` cache unset.
- The next `page.files` access may reacquire page files for the renamed page instead of reusing old-path URLs.
- Missing or non-`ok` rename action statuses still prevent local page identity changes and file-cache invalidation.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Page file URLs are parsed as static absolute URLs, and Wikidot file paths include the page name segment. Keeping a cached file collection after a successful rename can therefore expose stale paths even though the `Page` object itself has moved to a new `fullname`. Invalidating the cache is simpler and safer than attempting to rewrite file URLs locally, because the next acquisition can parse the server's actual post-rename file list.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts made page-file caching faster and more cache-aware. This slice keeps that performance behavior but drops cached file metadata when the owning page identity changes.
- This slice intentionally targets only `Page.rename(...)` and `_files`; source, revision, vote, metadata, discussion, and meta-tag cache behavior remain separate boundaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved page contents, source text from real pages, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This is a local-state consistency fix. It does not alter the remote rename request, file acquisition parser, or `PageFile` model; it only prevents a renamed page object from reusing file metadata derived from its previous page path.
