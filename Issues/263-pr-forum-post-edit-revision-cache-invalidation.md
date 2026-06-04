# PR Draft: Invalidate Forum Post Revision Cache After Edit

## Summary

`ForumPost.edit(...)` updates the calling post object's local title and source after a successful `saveEditPost` action. One adjacent stale-cache gap remained: if the caller had already loaded `post.revisions`, the original `ForumPost` instance kept the old `ForumPostRevisionCollection` after the edit. The next `post.revisions` read could therefore return pre-edit forum post history even though the source mutation had just succeeded.

This follow-up clears the calling post object's cached revision list only after the existing save response status check succeeds. Failed form fetches, malformed edit forms, malformed save responses, and non-`ok` action statuses still leave local title/source/revision state unchanged.

## Related Issue

Builds on [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [162-pr-forum-post-edit-revision-error-context.md](162-pr-forum-post-edit-revision-error-context.md), [205-pr-forum-post-edit-revision-value-context.md](205-pr-forum-post-edit-revision-value-context.md), [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md), [259-pr-page-edit-local-cache-sync.md](259-pr-page-edit-local-cache-sync.md), and [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md). Those drafts established forum post source/revision acquisition as retry-aware, cache-aware, duplicate-aware, and context-rich, while the Page edit follow-ups established caller-side mutation cache consistency as a useful local pattern.

No upstream issue was filed from this local workspace.

## Changes

- Invalidate the calling `ForumPost` object's cached `ForumPostRevisionCollection` after a successful `ForumPost.edit(...)`.
- Preserve successful local source updates and optional title updates.
- Preserve login checks, retry-aware edit-form fetches, direct-child `currentRevisionId` parsing, save request payloads, action status validation, and method chaining.
- Add a focused regression that seeds `_revisions`, performs a successful edit, and asserts the cached revision list is cleared.

## Type Of Change

- Forum post edit cache consistency
- Revision-list cache invalidation
- Browser-free forum mutation ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A successful `ForumPost.edit(...)` invalidates the calling post object's cached revisions. | `TestForumPostEdit.test_edit_success_invalidates_cached_revisions` seeds `_revisions`, performs a successful edit, and asserts `_revisions is None`. | Reusing a pre-edit `ForumPostRevisionCollection` after successful edit rejects this local completion claim. |
| Successful edits still update local source and optional title state. | The focused regression asserts `_source == "Updated source"`, and existing `test_edit_success` / `test_edit_with_new_title` continue to pass. | Dropping local source or title updates rejects this local completion claim. |
| Failed or malformed edit attempts still do not mutate local state. | Existing form-fetch, missing-body, malformed currentRevisionId, and missing save-status tests continue to pass. | Clearing revision caches or updating source/title before the existing status gate rejects this local completion claim. |
| Existing forum post source and revision acquisition behavior remains intact. | `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostEdit tests/unit/test_forum_post.py::TestForumPostSource tests/unit/test_forum_post.py::TestForumPostCollectionGetSources tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts -q` passed 43 tests. | Regressions in edit-form handling, source caching, revision caching, duplicate post handling, or direct revision acquisition reject this local completion claim. |
| Adjacent forum post and forum post revision behavior remains unchanged. | `uv run --extra test pytest tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 103 tests. | Regressions in forum post or forum post revision unit tests reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `6dc5e1f fix(forum_post): invalidate edit revision cache`.

- RED: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_success_invalidates_cached_revisions -q` failed before the fix because `_revisions` still contained the old `ForumPostRevisionCollection` after a successful edit.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_success_invalidates_cached_revisions -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostEdit tests/unit/test_forum_post.py::TestForumPostSource tests/unit/test_forum_post.py::TestForumPostCollectionGetSources tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts -q` passed 43 tests.
- `uv run --extra test pytest tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 103 tests.
- `uv run --extra test pytest tests/unit -q` passed 815 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Successful `ForumPost.edit(...)` calls clear the calling `ForumPost` object's cached revision list after the save action status is confirmed.
- The next `post.revisions` access can acquire fresh forum post history instead of returning a pre-edit cache.
- Successful edit calls still update the local source and optional title fields.
- Failed form fetches, malformed edit forms, malformed save responses, and non-`ok` save statuses do not gain a new local mutation path.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post source edits and forum post revision history are part of the same mutation/read surface. After a successful edit, a caller that had already loaded `post.revisions` should not continue seeing the old revision collection from the same object. Clearing `_revisions` after the existing success gate keeps the lazy revision acquisition model coherent without changing requests, parsing, retries, action status handling, source updates, or public return values.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum post source and revision acquisition as common practical workflow surfaces with retry, duplicate reuse, cache skip, and contextual error handling.
- This slice intentionally targets only post-success revision-cache invalidation on the original `ForumPost` instance; revision acquisition, revision parsing, edit-form parsing, retry policy, source fetching, and live Wikidot behavior remain separate boundaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved post contents, source text from real posts, thread IDs from real sites, and site contents out of upstream discussion.

## Additional Notes

This mirrors the caller-side cache consistency rule now used for `Page.edit(...)`: after a successful write, the original object should not keep returning a stale lazy-read cache for the data that write just changed.
