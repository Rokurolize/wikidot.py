# PR Draft: Include Site Context In Forum Post Edit Revision Errors

## Summary

`ForumPost.edit(...)` must fetch `forum/sub/ForumEditPostFormModule` before saving so it can send Wikidot's current `currentRevisionId` with the `saveEditPost` action. Earlier local slices made that edit-form fetch retry-aware, scoped the generated edit-form controls to direct children, added post ID context to malformed revision-ID errors, and added site/post context to exhausted edit-form fetch failures. The remaining malformed revision-ID parser error still identified only the post ID.

This follow-up keeps the read-before-mutation boundary, login checks, request payloads, retry-aware edit-form fetch, no-save-on-malformed-form behavior, successful edit payloads, title/source local state updates, and exception type unchanged, but includes both site unix name and post ID when the generated `currentRevisionId` input is missing: `Current revision ID input is not found for site: <site>, post: <id>`.

## Related Issue

Builds on [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [162-pr-forum-post-edit-revision-error-context.md](162-pr-forum-post-edit-revision-error-context.md), and [173-pr-forum-post-edit-form-fetch-failure-context.md](173-pr-forum-post-edit-form-fetch-failure-context.md), because those drafts established forum post editing as a retry-aware read-before-mutation boundary and aligned edit-form fetch failures with site/post diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Include site unix name as well as post ID in malformed edit-form `currentRevisionId` errors.
- Rename and tighten the focused malformed edit-form regression to assert site/post context.
- Preserve the no-save-on-malformed-form guard and local source/title state.
- Preserve successful edit, edit-with-title, direct-child revision ID parsing, source fetching, post-list parsing, and reply behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post edit-form parser context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A malformed edit-form response missing the generated direct `currentRevisionId` input still raises `NoElementException`. | `TestForumPostEdit.test_edit_missing_current_revision_id_includes_site_and_post_context` removes the fixture's direct hidden input and expects an exception. | A change that sends `saveEditPost`, fabricates a revision ID, or silently updates local source/title rejects this local completion claim. |
| The malformed edit-form error identifies the affected site and post. | The focused regression asserts `Current revision ID input is not found for site: test-site, post: 5001`. | The RED test failed before the fix because the message was only `Current revision ID input is not found for post: 5001`. |
| A malformed pre-save edit form does not trigger the mutation action. | The focused test asserts `site.amc_request(...)` is not called and `_source` remains `None`. | A change that sends `saveEditPost` after a malformed form rejects this local completion claim. |
| Forum post workflows remain green. | `uv run pytest tests/unit/test_forum_post.py -q` passed 49 tests. | Regressions in source fetching, edit-form retry, edit-form control scoping, lazy source, post-list parsing, or reply behavior reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 149 tests. | Regressions in category, thread, post, or post-revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `5938960 fix(forum_post): include site in edit revision errors`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_current_revision_id_includes_site_and_post_context -q` failed before the fix because the exception message only said `Current revision ID input is not found for post: 5001`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_current_revision_id_includes_site_and_post_context -q`.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 49 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 149 tests.
- `uv run pytest tests/unit -q` passed 727 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `ForumPost.edit(...)` still fetches the edit form through retry-aware AMC before saving.
- If the edit form cannot be fetched after retries, the existing site/post-specific `UnexpectedException` behavior remains unchanged.
- If the edit form is present but missing the generated direct `currentRevisionId` input, the method raises `NoElementException` naming both the site unix name and post ID.
- Malformed edit-form parsing does not send the `saveEditPost` mutation or update local source/title state.
- Successful edit, edit-with-title, direct-child revision parsing, source fetching, post-list parsing, and reply behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Editing a forum post requires a fresh server-provided revision ID. If Wikidot returns an edit form without the generated revision ID input, wikidot.py should keep failing before mutation, and the failure should identify both site and post so caller logs can route the failure without storing raw edit-form HTML, raw AMC responses, credentials, local rollout paths, or post bodies.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum post edit-form fetching as a retry-aware read-before-mutation boundary and scoped edit-form controls to direct generated children.
- Recent context slices showed that site/object identifiers improve resumable multi-site ledgers without changing successful behavior.
- The refreshed complexity memo continues to list action/read boundaries and direct property/parser failure messages as follow-up leads, but this slice only claims malformed edit-form revision-ID diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw edit-form HTML, raw AMC responses, and post contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change edit-form request payloads, retry policy, login checks, save action retry semantics, title/source state updates, successful revision ID parsing, edit-form direct-child scoping, source fetching, post-list parsing, `ForumThread.reply(...)`, or live Wikidot behavior. It only adds site context to an existing malformed edit-form revision-ID exception.
