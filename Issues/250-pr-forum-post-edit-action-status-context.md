# PR Draft: Validate ForumPost.edit Save Action Status Before Updating Local State

## Summary

`ForumPost.edit(...)` fetches Wikidot's edit form, extracts the current `currentRevisionId`, sends the `saveEditPost` action, and then updates the local post title/source. Earlier local slices hardened the read-before-mutation boundary, but the save response itself was still accepted without checking its decoded `status` field. A malformed save response such as `{"body": ""}` could therefore make the method return as successful and update local state even though Wikidot did not confirm the edit.

This follow-up validates the returned `saveEditPost` response before mutating `ForumPost.title` or `_source`. A missing `status` raises `NoElementException` with site, post, event, and field context. Explicit non-`ok` statuses raise `WikidotStatusCodeException`. Successful edit-form parsing, save request construction, and local updates after `status: ok` remain unchanged.

## Related Issue

Builds on [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [185-pr-forum-post-edit-revision-site-context.md](185-pr-forum-post-edit-revision-site-context.md), [205-pr-forum-post-edit-revision-value-context.md](205-pr-forum-post-edit-revision-value-context.md), and [210-pr-forum-post-edit-form-response-body-context.md](210-pr-forum-post-edit-form-response-body-context.md). Those drafts established the edit form as a practical generated-control boundary and kept the actual `saveEditPost` mutation on the existing non-retried path.

No upstream issue was filed from this local workspace.

## Changes

- Validate the returned `saveEditPost` action response before updating local forum post state.
- Convert a missing save-action `status` into `NoElementException` with site unix name, post ID, event, and field context.
- Preserve explicit non-`ok` status handling through `WikidotStatusCodeException`.
- Add a focused public-interface regression for malformed forum post edit save responses.
- Preserve login checks, retry-aware edit-form fetches, direct-child `currentRevisionId` parsing, save request payloads, and successful title/source updates.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post edit action response validation
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A forum post edit save response missing `status` fails with contextual `NoElementException`. | `TestForumPostEdit.test_edit_missing_save_action_status_does_not_update_local_state` returns `{"body": ""}` from the `saveEditPost` response and asserts `NoElementException`. | Returning success, raising a raw `KeyError`, fabricating success, or omitting action context rejects this local completion claim. |
| The malformed save-action message identifies site, post, event, and missing field. | The focused regression asserts `Forum post action response is malformed for site: test-site, post: 5001 (event=saveEditPost, field=status)`. | Omitting site unix name, post ID, event, or field context makes the failure ambiguous and rejects this local completion claim. |
| Malformed save responses do not update local forum post state. | The focused regression sets an original title/source and asserts both remain unchanged after the exception. | Updating `title` or `_source` before validating the returned action status rejects this local completion claim. |
| Successful edit behavior remains unchanged. | `TestForumPostEdit` passes, including successful edit, title update, retry-aware edit-form fetch, exhausted retry, direct-child revision scoping, and malformed form-body/revision guards. | Regressions in login checks, edit-form fetches, revision parsing, save payload shape, or successful local state updates reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `3b753a8 fix(forum_post): guard edit action status`.

- RED: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_save_action_status_does_not_update_local_state -q` failed before the fix with `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>` and `_source='Updated source'`.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_save_action_status_does_not_update_local_state -q` passed.
- `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostEdit -q` passed 11 tests.
- `uv run --extra test pytest tests/unit/test_forum_post.py -q` passed 59 tests.
- `uv run --extra test pytest tests/unit -q` passed 800 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `ForumPost.edit(...)` raises `NoElementException` when the returned `saveEditPost` action response lacks `status`.
- The malformed-response message includes site `unix_name`, post ID, action event, and missing field.
- Explicit non-`ok` save-action statuses are not treated as successful edits.
- Local `title` and `_source` are updated only after the returned action status has been validated.
- Successful edit paths keep the existing edit-form request, `currentRevisionId` parsing, save request payload, login check, and local title/source update behavior.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post editing is a browser-free mutation workflow that already depends on a fresh generated revision ID before saving. Validating the corresponding save-action status prevents callers from observing a locally edited post object after an unclassified Wikidot response, and gives them an event-specific retry/debug signal when the required status field is missing.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts show `ForumPost.edit(...)` is part of the practical forum-post workflow surface, and several adjacent slices already hardened its pre-save edit-form boundary.
- Recent page write slices hardened analogous action-response boundaries before local state updates for rename, delete, direct metadata, and meta setter operations.
- The immediately related forum post edit-form drafts intentionally kept `saveEditPost` on the non-retried mutation path and did not claim save-action response validation; this slice closes that remaining response boundary without changing retry semantics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, forum post content, page source text, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not retry forum post edit writes, change request construction, add per-action result objects, alter source acquisition, change forum post list parsing, touch `ForumThread.reply(...)`, touch `ForumCategory.create_thread(...)`, or modify live Wikidot behavior. It only validates the returned `saveEditPost` action response before treating the edit as successful and updating local post state.
