# PR Draft: Include Site Context In Forum Post Edit Form Fetch Failures

## Summary

`ForumPost.edit(...)` must fetch `forum/sub/ForumEditPostFormModule` before saving so it can send the current `currentRevisionId` with the `saveEditPost` action. The edit-form fetch already uses retry-aware AMC, and exhausted fetches already fail before the mutation action, but the failure message only identified the post ID: `Cannot retrieve forum post edit form: ...`.

This follow-up preserves the retry-aware read-before-mutation boundary, successful edit payloads, malformed edit-form revision-ID handling, title/source local-state updates, and no-save-on-failed-form behavior, but includes site unix name and post ID when the edit-form fetch exhausts retries.

## Related Issue

Builds on [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), which introduced retry-aware edit-form fetching and the exhausted-fetch guard before `saveEditPost`. It also follows [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [162-pr-forum-post-edit-revision-error-context.md](162-pr-forum-post-edit-revision-error-context.md), and [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), because those drafts established the edit form as a generated-control boundary and aligned adjacent forum post/revision failures with contextual diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Include site unix name and post ID when `ForumPost.edit(...)` cannot retrieve the edit form after retries.
- Strengthen the exhausted edit-form fetch regression to assert the contextual message.
- Preserve login checks, retry-aware edit-form request shape, no-save-on-failed-form behavior, successful edit payloads, title/source local state updates, edit-form direct-child scoping, malformed revision-ID handling, source fetching, post-list parsing, and reply behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post edit-form fetch failure context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Exhausted retry edit-form fetches still fail before saving. | `TestForumPostEdit.test_edit_raises_when_form_fetch_retry_is_exhausted` raises `UnexpectedException` when the retry helper returns `None`. | A change that sends `saveEditPost`, updates `_source`, or returns successfully after a failed edit-form fetch rejects this local completion claim. |
| Exhausted edit-form fetch failures identify the failed site and post. | The focused test asserts `Cannot retrieve forum post edit form for site: test-site, post: 5001`. | The RED test failed before the fix because the message only named the post ID. |
| Forum post workflows remain green. | `uv run pytest tests/unit/test_forum_post.py -q` passed 48 tests. | Regressions in post-list parsing, source fetching, edit-form retry, edit-form direct-child scoping, lazy source, edit-with-title, or reply behavior reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 148 tests. | Regressions in category/thread/post/revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `e1b4267 fix(forum_post): include site in edit form failures`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_raises_when_form_fetch_retry_is_exhausted -q` failed before the fix because the exhausted-fetch message only named the post ID.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_raises_when_form_fetch_retry_is_exhausted -q`
- `uv run pytest tests/unit/test_forum_post.py -q` passed 48 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 148 tests.
- `uv run pytest tests/unit -q` passed 722 tests.
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `ForumPost.edit(...)` still fetches the edit form through retry-aware AMC before saving.
- If the edit form cannot be fetched after retries, the method raises `UnexpectedException` before sending `saveEditPost`.
- That exception includes the site unix name and post ID.
- Successful edit, edit-with-title, direct-child revision parsing, malformed revision-ID failure behavior, source fetching, post-list parsing, and reply behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Editing a forum post requires a fresh server-provided revision ID. If the edit form cannot be fetched after retries, wikidot.py should keep failing before mutation, and the failure should identify the site and post so caller logs can route the failure without storing raw edit-form HTML, AMC responses, or post bodies.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum post edit-form fetching as a retry-aware read-before-mutation boundary and scoped edit-form controls to direct generated children.
- Recent forum context slices showed that site-specific exhausted-retry messages improve multi-site ledgers without changing successful behavior.
- The refreshed complexity memo continues to list action/read boundaries and direct property/parser failure messages as follow-up leads, but this slice only claims edit-form fetch diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw edit-form HTML, raw AMC responses, and post contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change edit-form request payloads, retry policy, login checks, save action retry semantics, title/source state updates, successful revision ID parsing, malformed revision-ID handling, source fetching, post-list parsing, `ForumThread.reply(...)`, or live Wikidot behavior. It only adds site context to an existing exhausted retry-aware forum post edit-form fetch failure.
