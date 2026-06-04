# PR Draft: Include Post ID In Forum Post Edit Revision Errors

## Summary

`ForumPost.edit(...)` must fetch `forum/sub/ForumEditPostFormModule` before saving so it can send the current `currentRevisionId` with the `saveEditPost` action. The edit-form fetch already uses retry-aware AMC, and exhausted fetches already raise `Cannot retrieve forum post edit form: <post_id>`. If the form response was present but missing the generated direct `currentRevisionId` input, the parser still raised the generic `Current revision ID input is not found.`

This follow-up keeps the existing failure behavior and does not send the save action on malformed edit-form markup, but includes the affected post ID in that `NoElementException`. That makes pre-save edit-form structure failures diagnosable from plain logs without storing raw edit-form HTML or forum post content.

## Related Issue

Builds on [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), because those drafts established the edit-form fetch as a read-before-mutation boundary, scoped edit-form controls to generated direct children, and aligned forum post source errors with post-specific diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Change `ForumPost.edit(...)` so a missing direct `input[name='currentRevisionId']` raises `Current revision ID input is not found for post: <id>`.
- Add a focused malformed edit-form regression that removes the generated revision ID input, asserts the post-specific exception, and verifies `saveEditPost` is not sent.
- Preserve login checks, retry-aware edit-form fetches, exhausted-form-fetch behavior, successful edit payloads, title/source local state updates, edit-form direct-child scoping, source fetching, post-list parsing, and reply behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post edit-form error-context ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A malformed edit-form response missing the generated direct `currentRevisionId` input still raises `NoElementException`. | `TestForumPostEdit.test_edit_missing_current_revision_id_includes_post_context` removes the fixture's direct hidden input and expects an exception. | A change that sends `saveEditPost` without a current revision ID, fabricates a revision ID, or silently updates local source rejects this local completion claim. |
| The malformed edit-form error identifies the affected post. | The focused test asserts `Current revision ID input is not found for post: 5001`. | The RED test failed before the fix because the exception message was only `Current revision ID input is not found.` |
| A malformed pre-save edit form does not trigger the mutation action. | The focused test asserts `site.amc_request(...)` is not called and `_source` remains `None`. | A change that sends `saveEditPost` after a malformed form rejects this local completion claim. |
| Forum post workflows remain green. | `uv run pytest tests/unit/test_forum_post.py -q` passed 48 tests. | Regressions in source fetching, edit-form retry, edit-form control scoping, lazy source, post-list parsing, or reply behavior reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py -q` passed 90 tests. | Regressions in thread post access, thread parsing, source fetching, or edit behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `887b04d fix(forum_post): include post id in edit revision errors`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_current_revision_id_includes_post_context -q` failed before the fix because the exception message was only `Current revision ID input is not found.`
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_current_revision_id_includes_post_context -q`
- `uv run pytest tests/unit/test_forum_post.py -q` passed 48 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py -q` passed 90 tests.
- `uv run pytest tests/unit -q` passed 720 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `ForumPost.edit(...)` still fetches the edit form through retry-aware AMC before saving.
- If the edit form cannot be fetched after retries, the existing post-specific `UnexpectedException` behavior remains unchanged.
- If the edit form is present but missing the generated direct `currentRevisionId` input, the method raises `NoElementException` with the affected post ID.
- Malformed edit-form parsing does not send the `saveEditPost` mutation or update local source/title state.
- Successful edit, edit-with-title, direct-child revision parsing, source fetching, post-list parsing, and reply behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Editing a forum post requires a fresh server-provided revision ID. If Wikidot returns an edit form without the generated revision ID input, wikidot.py should keep failing before the mutation action, but the failure should identify the affected post so caller logs can distinguish one malformed edit-form response from another without storing raw edit-form HTML or post bodies.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum post edit-form fetching as a retry-aware read-before-mutation boundary and scoped edit-form controls to direct generated children.
- Recent direct property and parser context slices showed that object-specific failure messages improve resumable local ledgers without changing successful behavior.
- The refreshed complexity memo continues to list `src/wikidot/module/forum_post.py` as an audit-worthy parser/acquisition surface.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw edit-form HTML, and post contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change edit-form request payloads, retry policy, login checks, save action retry semantics, title/source state updates, successful revision ID parsing, source fetching, post-list parsing, `ForumThread.reply(...)`, or live Wikidot behavior. It only adds the post ID to an existing malformed edit-form revision-ID exception.
