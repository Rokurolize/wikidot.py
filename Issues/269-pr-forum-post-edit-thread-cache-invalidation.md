# PR Draft: Invalidate Thread Post Cache After Forum Post Edit

## Summary

`ForumPost.edit(...)` already validates the `saveEditPost` action response before updating the edited post object's title, source cache, and revision cache. However, a `ForumThread` can also hold a cached `ForumPostCollection` in `thread._posts`. When that collection contains a different `ForumPost` instance for the same post ID, successful edits can leave later `thread.posts` reads with stale post title/text/source data from the old cached collection.

This follow-up invalidates the owning thread's post-list cache after a confirmed successful edit. The change is intentionally local: it does not alter the edit request, edit-form parsing, revision ID handling, title handling, or failed-save behavior.

## Related Issue

Builds on [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [162-pr-forum-post-edit-revision-error-context.md](162-pr-forum-post-edit-revision-error-context.md), [205-pr-forum-post-edit-revision-value-context.md](205-pr-forum-post-edit-revision-value-context.md), [210-pr-forum-post-edit-form-response-body-context.md](210-pr-forum-post-edit-form-response-body-context.md), [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md), and [263-pr-forum-post-edit-revision-cache-invalidation.md](263-pr-forum-post-edit-revision-cache-invalidation.md). Those drafts established retry-safe edit form fetches, scoped revision ID parsing, action-status validation, and revision-cache invalidation after edits.

No upstream issue was filed from this local workspace.

## Changes

- Clear `ForumPost.thread._posts` after a successful `ForumPost.edit(...)` call so later `thread.posts` access reacquires the post list.
- Keep the existing edited-object updates: optional title update, `_source` refresh, and `_revisions` invalidation.
- Preserve failed-save behavior by applying thread post-list invalidation only after `saveEditPost` status validation succeeds.
- Add a focused regression that seeds `thread._posts` with a stale copied post object and asserts successful edit invalidates the cached collection.
- Extend the malformed save-status regression to assert the cached thread post list is preserved when the edit is rejected.

## Type Of Change

- Forum post edit local-state consistency
- Forum thread post-list cache invalidation
- Browser-free forum mutation ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Successful forum post edits invalidate the owning thread's cached post list. | `TestForumPostEdit.test_edit_success_invalidates_thread_posts_cache` seeds `thread._posts` with a stale copied post, edits the target post, and asserts `thread._posts is None`. | Reusing a cached `ForumPostCollection` after a successful edit rejects this local completion claim. |
| The edited object still updates its local title, source, and revision cache consistently. | Existing `TestForumPostEdit.test_edit_success`, `test_edit_success_invalidates_cached_revisions`, and `test_edit_with_new_title` continue to pass. | Dropping the existing object-local updates rejects this local completion claim. |
| Failed edit save responses do not mutate local post or thread cache state. | `TestForumPostEdit.test_edit_missing_save_action_status_does_not_update_local_state` now asserts title, source, and `thread._posts` remain unchanged after a malformed save response. | Clearing thread caches before action-status validation rejects this local completion claim. |
| Existing forum post acquisition and reply behavior remains intact. | `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostEdit tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll tests/unit/test_forum_thread.py::TestForumThreadReply -q` passed 37 tests. | Regressions in edit, cached post-list acquisition, or reply cache handling reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `249d3da fix(forum_post): invalidate thread posts on edit`.

- RED: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_success_invalidates_thread_posts_cache -q` failed before the fix because `thread._posts` still referenced the stale cached `ForumPostCollection`.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_success_invalidates_thread_posts_cache -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostEdit tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll tests/unit/test_forum_thread.py::TestForumThreadReply -q` passed 37 tests.
- `uv run --extra test pytest tests/unit -q` passed 822 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Successful `ForumPost.edit(...)` calls clear the owning `ForumThread` post-list cache.
- Successful edits still update the edited `ForumPost` object's local title, source, and revision cache as before.
- Missing or non-`ok` edit action statuses still prevent edited-object and thread-cache local-state mutation.
- Existing thread post-list acquisition can continue to skip cached lists until a successful mutation invalidates that cache.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum edit workflows often operate without a browser by acquiring a thread's posts, selecting one post, editing it, and then reading the thread again. If `thread.posts` has already been cached and holds a separate `ForumPost` instance, the edit path updates only the edited object while later thread-level reads can keep returning the stale cached collection. Clearing the thread cache after confirmed edit success gives subsequent thread-level reads a coherent view without changing network behavior or failed-save semantics.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts made thread post-list reads cache-aware and validated forum post edit action statuses before local mutation. This slice connects those two behaviors by invalidating the read cache after the write succeeds.
- This slice intentionally targets only the owning thread's cached post list. Category-level thread caches, site-level category collections, live Wikidot ordering, and forum post revision/source acquisition remain separate boundaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved forum contents, source text from real pages, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This is a local-state consistency fix. It does not alter form fetch retries, edit-form parsing, revision ID validation, edit request payloads, source retrieval, revision retrieval, or action-status parsing; it only invalidates the thread-level post-list cache after a confirmed successful edit.
