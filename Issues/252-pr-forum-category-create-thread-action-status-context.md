# PR Draft: Validate ForumCategory.create_thread Action Status Before Fetching Created Thread

## Summary

`ForumCategory.create_thread(...)` sends Wikidot's `newThread` action, validates the returned `threadId`, and then fetches the created thread. The method previously accepted a valid integer `threadId` as enough proof of success even when the action response lacked `status`, so callers could perform a follow-up thread detail fetch after an unclassified creation response.

This follow-up validates the returned `newThread` action status after the existing `threadId` validation and before `ForumThread.get_from_id(...)`. A missing `status` raises `NoElementException` with site, category, event, and field context. Explicit non-`ok` statuses raise `WikidotStatusCodeException`. Successful `status: ok` creation, title/description/source payloads, login checks, and the existing missing or invalid `threadId` failure behavior remain unchanged.

## Related Issue

Builds on [167-pr-forum-thread-create-result-context.md](167-pr-forum-thread-create-result-context.md), [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md), and [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md). Issue 167 established contextual `threadId` validation for `ForumCategory.create_thread(...)`; Issues 250 and 251 established adjacent forum mutation action-status validation before local state is treated as successful.

No upstream issue was filed from this local workspace.

## Changes

- Validate the returned `newThread` action response before fetching the created thread by ID.
- Convert a missing create-thread action `status` into `NoElementException` with site unix name, category ID, event, and field context.
- Preserve explicit non-`ok` status handling through `WikidotStatusCodeException`.
- Add a focused public-interface regression for malformed forum category create-thread responses.
- Preserve login checks, request payload construction, title/description/source submission, existing missing or invalid `threadId` behavior, and successful `status: ok` created-thread lookup.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum category create-thread action response validation
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A forum category create-thread response with integer `threadId` but missing `status` fails with contextual `NoElementException`. | `TestForumCategoryCreateThread.test_create_thread_missing_action_status_does_not_fetch_created_thread` returns `{"threadId": 3001}` from the `newThread` response and asserts `NoElementException`. | Treating the response as successful, raising a raw `KeyError`, or fetching the created thread rejects this local completion claim. |
| The malformed action-status message identifies site, category, event, and missing field. | The focused regression asserts `Forum category action response is malformed for site: test-site, category: 1001 (event=newThread, field=status)`. | Omitting site unix name, category ID, event, or field context makes the failure ambiguous and rejects this local completion claim. |
| Existing `threadId` validation remains the first create-result guard. | `TestForumCategoryCreateThread.test_create_thread_missing_or_invalid_thread_id_raises` still covers `{}` and `{"threadId": "3001"}` before action-status validation. | Reordering the checks so missing or invalid `threadId` responses report an action-status failure rejects this local completion claim. |
| Malformed action-status responses do not fetch created-thread details. | The focused regression sets a second mocked thread-detail response and asserts `site.amc_request.call_count == 1`. | Performing the follow-up `ForumThread.get_from_id(...)` request before validating `status` rejects this local completion claim. |
| Successful create-thread behavior remains unchanged. | `TestForumCategoryCreateThread` passes, including successful creation, login guard, payload fields, and created-thread lookup. | Regressions in login checks, request payload shape, integer `threadId` handling, or successful created-thread lookup reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `69edf40 fix(forum_category): guard create thread action status`.

- RED: `uv run --extra test pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_missing_action_status_does_not_fetch_created_thread -q` failed before the fix with `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>`.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_missing_action_status_does_not_fetch_created_thread -q` passed.
- `uv run --extra test pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread -q` passed 5 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py -q` passed 23 tests.
- `uv run --extra test pytest tests/unit -q` passed 802 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `ForumCategory.create_thread(...)` raises `NoElementException` when the returned `newThread` action response has a valid integer `threadId` but lacks `status`.
- The malformed-response message includes site `unix_name`, category ID, action event, and missing field.
- Explicit non-`ok` create-thread action statuses are not treated as successful thread creation.
- Existing missing and invalid `threadId` failures keep their current contextual `Thread ID is not found for site: test-site, category: 1001` behavior.
- A malformed action-status response does not perform the created-thread detail lookup.
- Successful create-thread paths keep the existing login check, request payload shape, title/description/source handling, integer `threadId` handling, and returned `ForumThread` lookup behavior.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Thread creation is a non-retried forum mutation workflow. Once the library has confirmed the response identifies a candidate thread ID, it should still require Wikidot's action status before treating the mutation as successful enough to perform the follow-up created-thread lookup. This makes create-thread behavior consistent with adjacent forum edit and reply helpers and gives callers an event-specific retry/debug signal when Wikidot omits the required status field.

## Local Evidence, Not For Upstream Paste

- Issue 167 established that missing or non-integer `threadId` values are malformed create-thread results and should retain site/category context.
- Issues 250 and 251 established the adjacent forum mutation pattern: validate the non-retried action response before updating local state or accepting the action as successful.
- This slice intentionally targets only `ForumCategory.create_thread(...)`; `ForumPost.edit(...)` and `ForumThread.reply(...)` are already covered by separate local commits and drafts.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, forum post content, page source text, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not retry forum thread creation writes, change request construction, add per-action result objects, alter thread detail parsing, touch `ForumPost.edit(...)`, touch `ForumThread.reply(...)`, or modify live Wikidot behavior. It only validates the returned `newThread` action response after the existing `threadId` guard and before the created-thread detail fetch.
