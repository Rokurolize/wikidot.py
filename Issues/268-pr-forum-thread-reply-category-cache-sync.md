# PR Draft: Sync Forum Category Cache After Thread Reply

## Summary

`ForumThread.reply(...)` already validates the `savePost` action response, clears the thread's own `_posts` cache, and increments `thread.post_count` after a successful reply. When the thread belongs to a `ForumCategory`, the owning category also changes: its aggregate `posts_count` increases and its cached thread list can be stale because the replied thread's list metadata or ordering may have changed.

This follow-up updates category-local state after successful replies on categorized threads. It increments `thread.category.posts_count` and invalidates `thread.category._threads` only after the existing reply action status gate succeeds.

## Related Issue

Builds on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [167-pr-forum-thread-create-result-context.md](167-pr-forum-thread-create-result-context.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), and [264-pr-forum-category-create-thread-cache-invalidation.md](264-pr-forum-category-create-thread-cache-invalidation.md). Those drafts established category thread-list caching, thread reply action-status validation, and category thread cache invalidation after category-level mutation.

No upstream issue was filed from this local workspace.

## Changes

- Increment `ForumThread.category.posts_count` after a successful reply when the thread has a category.
- Clear `ForumThread.category._threads` after a successful reply so later `category.threads` access can reacquire the category thread list.
- Preserve standalone thread behavior when `thread.category is None`.
- Preserve failed-reply behavior by applying category changes only after the existing `savePost` status gate succeeds.
- Add a focused regression for categorized replies with a seeded category thread-list cache.

## Type Of Change

- Forum reply local-state consistency
- Forum category cache invalidation
- Browser-free forum mutation ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Successful replies on categorized threads update the category aggregate post count. | `TestForumThreadReply.test_reply_success_updates_category_post_count_and_invalidates_threads` starts from a category with a cached thread list, replies, and asserts `category.posts_count` increased by one. | Leaving the category aggregate post count unchanged after a successful categorized reply rejects this local completion claim. |
| Successful replies on categorized threads invalidate cached category thread lists. | The same regression seeds `category._threads` and asserts it is `None` after the reply. | Reusing the cached category thread list after a successful reply rejects this local completion claim. |
| Failed reply responses do not mutate thread or category local state. | The implementation remains after `_require_forum_thread_action_status(...)`, and existing missing-status reply tests continue to pass. | Incrementing counts or clearing caches before status validation rejects this local completion claim. |
| Existing forum reply, category thread-list, and category behavior remains intact. | `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadReply tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll tests/unit/test_forum_category.py -q` passed 46 tests. | Regressions in reply behavior, category thread acquisition, or category create-thread behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `142248a fix(forum_thread): sync category cache on reply`.

- RED: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_success_updates_category_post_count_and_invalidates_threads -q` failed before the fix because `category.posts_count` stayed unchanged after a successful reply.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_success_updates_category_post_count_and_invalidates_threads -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadReply tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll tests/unit/test_forum_category.py -q` passed 46 tests.
- `uv run --extra test pytest tests/unit -q` passed 821 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Successful `ForumThread.reply(...)` calls on categorized threads increment the owning category's `posts_count`.
- Successful `ForumThread.reply(...)` calls on categorized threads clear the owning category's cached thread list.
- Standalone threads without a category keep existing behavior.
- Missing or non-`ok` reply action statuses still prevent thread and category local-state mutation.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

A successful reply is visible at both thread and category levels: the thread gains a post, and the category's aggregate post total changes. Cached category thread lists can also become stale because the replied thread may move in list ordering or show updated post metadata. Updating category-local counters and invalidating the category thread cache keeps browser-free forum workflows coherent without changing the reply request or failed-reply behavior.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts made category thread-list reads cache-aware and invalidated category thread caches after creating a new thread. This slice applies the same local-state rule to replies inside an existing categorized thread.
- This slice intentionally targets only category state reachable from the replying `ForumThread`; site-level forum category collections, live Wikidot ordering, and forum post source/revision behavior remain separate boundaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved forum contents, source text from real pages, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This is a local-state consistency fix. It does not alter the reply request, parent reply behavior, title handling, thread-local post cache clearing, or status parsing; it only updates the owning category after a confirmed successful reply.
