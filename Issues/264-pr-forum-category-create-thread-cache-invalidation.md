# PR Draft: Invalidate Forum Category Thread Cache After Creating A Thread

## Summary

`ForumCategory.create_thread(...)` returns the newly created `ForumThread`, but the calling category object could keep returning an already-loaded `category.threads` cache from before the write. Because `ForumThreadCollection.acquire_all_in_category(category)` returns `category._threads` directly when it is set, a caller that loaded the thread list before creating a thread could keep seeing a stale list that omits the new thread.

This follow-up clears the calling category object's cached thread list only after the existing `newThread` action status check succeeds. Failed login checks, malformed create responses, missing or invalid `threadId` values, and non-`ok` action statuses still do not gain a new local mutation path.

## Related Issue

Builds on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [167-pr-forum-thread-create-result-context.md](167-pr-forum-thread-create-result-context.md), [252-pr-forum-category-create-thread-action-status-context.md](252-pr-forum-category-create-thread-action-status-context.md), [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md), and [263-pr-forum-post-edit-revision-cache-invalidation.md](263-pr-forum-post-edit-revision-cache-invalidation.md). Those drafts established category thread-list acquisition as retry-aware and cache-aware, hardened create-thread result/status validation, and established caller-side cache invalidation after successful writes.

No upstream issue was filed from this local workspace.

## Changes

- Invalidate the calling `ForumCategory` object's cached `ForumThreadCollection` after a successful `ForumCategory.create_thread(...)`.
- Preserve login checks, request payloads, `threadId` validation, action status validation, created-thread lookup, and return value behavior.
- Preserve failure behavior by clearing `_threads` only after the existing create-thread status gate succeeds.
- Add a focused regression that seeds `_threads`, performs a successful thread creation, and asserts the cached thread list is cleared.

## Type Of Change

- Forum category cache consistency
- Thread-list cache invalidation
- Browser-free forum mutation ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A successful `ForumCategory.create_thread(...)` invalidates the calling category object's cached thread list. | `TestForumCategoryCreateThread.test_create_thread_success_invalidates_cached_threads` seeds `_threads`, performs a successful create, and asserts `_threads is None`. | Returning the pre-create `ForumThreadCollection` after successful thread creation rejects this local completion claim. |
| The method still returns the newly created thread resolved from the returned `threadId`. | The focused regression and existing `test_create_thread_success` both assert the returned thread ID and category relationship. | Clearing the cache but skipping created-thread lookup rejects this local completion claim. |
| Failed or malformed create attempts still do not mutate local thread-list state. | Existing missing/invalid `threadId`, non-`ok` status, and login-check tests continue to pass, and the new invalidation sits after the existing status gate. | Clearing `_threads` before status validation rejects this local completion claim. |
| Existing category thread-list acquisition remains compatible with the cache contract. | `uv run --extra test pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread tests/unit/test_forum_category.py::TestForumCategoryBasic tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds -q` passed 35 tests. | Regressions in category cache properties, thread-list acquisition, or direct thread acquisition reject this local completion claim. |
| Adjacent forum category and forum thread behavior remains unchanged. | `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py -q` passed 73 tests. | Regressions in forum category or forum thread unit tests reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `eeb1721 fix(forum_category): invalidate thread cache on create`.

- RED: `uv run --extra test pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_success_invalidates_cached_threads -q` failed before the fix because `_threads` still contained the old `ForumThreadCollection` after successful thread creation.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_success_invalidates_cached_threads -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread tests/unit/test_forum_category.py::TestForumCategoryBasic tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds -q` passed 35 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py -q` passed 73 tests.
- `uv run --extra test pytest tests/unit -q` passed 816 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- After a successful `ForumCategory.create_thread(...)`, the calling `ForumCategory` object clears its cached `ForumThreadCollection`.
- The next `category.threads` access can acquire a fresh category thread list instead of returning a pre-create cache.
- The method still validates the returned `threadId`, validates the `newThread` action status, resolves the created thread, and returns that `ForumThread`.
- Failed login checks, malformed create responses, missing or invalid `threadId` values, and non-`ok` action statuses do not clear the caller's cached thread list.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum category thread creation and category thread-list reads are part of the same mutation/read surface. After a successful create, a caller that had already loaded `category.threads` should not keep receiving the old collection from the same category object. Clearing `_threads` after the existing success gate keeps the lazy thread-list acquisition model coherent without changing requests, parsing, retries, action status handling, created-thread lookup, or public return values.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established category thread-list acquisition and create-thread handling as practical workflow surfaces with retry, cache skip, contextual errors, and action status validation.
- This slice intentionally targets only post-success thread-list cache invalidation on the original `ForumCategory` instance; thread-list parsing, direct thread lookup, retry policy, create payloads, and live Wikidot behavior remain separate boundaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved post contents, source text from real posts, thread IDs from real sites, and site contents out of upstream discussion.

## Additional Notes

This mirrors the caller-side cache consistency rule now used for `Page.edit(...)`, `Page.vote(...)`, and `ForumPost.edit(...)`: after a successful write, the original object should not keep returning a stale lazy-read cache for data that write just changed.
