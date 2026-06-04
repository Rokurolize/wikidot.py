# PR Draft: Validate ForumThread.reply Action Status Before Updating Local State

## Summary

`ForumThread.reply(...)` sends Wikidot's `savePost` action and then clears the cached post collection and increments `post_count`. The method previously accepted any returned response object as success. If Wikidot returned a malformed action response without `status`, callers could observe a locally incremented thread and cleared post cache even though the reply action was not confirmed.

This follow-up validates the returned `savePost` response before mutating local thread state. A missing `status` raises `NoElementException` with site, thread, event, and field context. Explicit non-`ok` statuses raise `WikidotStatusCodeException`. Successful reply payloads, parent reply payloads, and local updates after `status: ok` remain unchanged.

## Related Issue

Builds on [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), and [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md). Those drafts established forum mutation paths as non-retried action writes and then validated the adjacent `ForumPost.edit(...)` save action before local state updates.

No upstream issue was filed from this local workspace.

## Changes

- Validate the returned `savePost` action response before clearing `ForumThread._posts` or incrementing `post_count`.
- Convert a missing reply-action `status` into `NoElementException` with site unix name, thread ID, event, and field context.
- Preserve explicit non-`ok` status handling through `WikidotStatusCodeException`.
- Add a focused public-interface regression for malformed forum thread reply responses.
- Preserve login checks, direct reply payloads, parent reply payloads, title payloads, successful cache clearing, and successful post-count increments.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum thread reply action response validation
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A forum thread reply response missing `status` fails with contextual `NoElementException`. | `TestForumThreadReply.test_reply_missing_action_status_does_not_update_local_state` returns `{"body": ""}` from the `savePost` response and asserts `NoElementException`. | Returning success, raising a raw `KeyError`, fabricating success, or omitting action context rejects this local completion claim. |
| The malformed reply-action message identifies site, thread, event, and missing field. | The focused regression asserts `Forum thread action response is malformed for site: test-site, thread: 3001 (event=savePost, field=status)`. | Omitting site unix name, thread ID, event, or field context makes the failure ambiguous and rejects this local completion claim. |
| Malformed reply responses do not update local thread state. | The focused regression stores an original `post_count` and cached `_posts` object and asserts both remain unchanged after the exception. | Incrementing `post_count` or clearing `_posts` before validating the returned action status rejects this local completion claim. |
| Successful reply behavior remains unchanged. | `TestForumThreadReply` passes, including successful reply, title payload, parent reply payload, login guard, cache clearing, and post-count increment. | Regressions in login checks, request payload shape, parent reply IDs, successful cache invalidation, or successful post-count updates reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `a599374 fix(forum_thread): guard reply action status`.

- RED: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_missing_action_status_does_not_update_local_state -q` failed before the fix with `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>`.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_missing_action_status_does_not_update_local_state -q` passed.
- `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadReply -q` passed 5 tests.
- `uv run --extra test pytest tests/unit/test_forum_thread.py -q` passed 49 tests.
- `uv run --extra test pytest tests/unit -q` passed 801 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `ForumThread.reply(...)` raises `NoElementException` when the returned `savePost` action response lacks `status`.
- The malformed-response message includes site `unix_name`, thread ID, action event, and missing field.
- Explicit non-`ok` reply-action statuses are not treated as successful replies.
- Local `_posts` and `post_count` are updated only after the returned action status has been validated.
- Successful reply paths keep the existing login check, request payload shape, parent reply handling, title handling, cache clearing, post-count increment, and method chaining behavior.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Thread replies are a browser-free forum mutation workflow. Callers should not observe a locally incremented thread or forced post-list refresh from an unclassified Wikidot response. Validating the returned action status makes reply behavior consistent with adjacent forum post editing and page write helpers, and gives callers an event-specific retry/debug signal when Wikidot omits the required status field.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts show forum read paths are retry-aware, while forum mutation actions intentionally stay non-retried to avoid duplicate writes.
- Issue 250 established the adjacent `ForumPost.edit(...)` pattern: validate a non-retried forum save action response before updating local state.
- This slice intentionally targets only `ForumThread.reply(...)`; `ForumCategory.create_thread(...)` remains a separate action boundary because it also returns and resolves a new thread ID.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, forum post content, page source text, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not retry forum thread reply writes, change request construction, add per-action result objects, alter post-list acquisition, touch `ForumPost.edit(...)`, touch `ForumCategory.create_thread(...)`, or modify live Wikidot behavior. It only validates the returned `savePost` action response before treating the reply as successful and updating local thread state.
