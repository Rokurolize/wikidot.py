# PR Draft: Validate Forum Post Edit Revision ID Values

## Summary

`ForumPost.edit(...)` fetches `forum/sub/ForumEditPostFormModule` before sending `saveEditPost`, because Wikidot requires the current `currentRevisionId` value in the mutation payload. Earlier local slices made that read retry-aware, scoped the generated edit-form controls to direct children, and added site/post context when the generated revision input is missing. The remaining malformed-value path still let BeautifulSoup attribute access or integer conversion leak as plain `KeyError` or `ValueError`.

This follow-up keeps the read-before-mutation boundary, login checks, retry-aware form fetch, direct-child control scoping, successful integer parsing, save request payload, title/source local state updates, source fetching, post-list parsing, and reply behavior unchanged. It only treats a missing or non-numeric `currentRevisionId` value as a malformed edit form and raises `NoElementException` with site/post context before any save action is sent.

## Related Issue

Builds on [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [162-pr-forum-post-edit-revision-error-context.md](162-pr-forum-post-edit-revision-error-context.md), [173-pr-forum-post-edit-form-fetch-failure-context.md](173-pr-forum-post-edit-form-fetch-failure-context.md), and [185-pr-forum-post-edit-revision-site-context.md](185-pr-forum-post-edit-revision-site-context.md). Those drafts established forum post editing as a retry-aware read-before-mutation boundary and made missing edit-form controls diagnosable without storing raw edit-form HTML.

No upstream issue was filed from this local workspace.

## Changes

- Check that the direct generated `input[name='currentRevisionId']` has a `value` attribute before parsing.
- Convert non-numeric revision values into site/post-specific `NoElementException` instead of leaking `ValueError`.
- Add focused regressions for missing and malformed revision ID values.
- Preserve the no-save-on-malformed-form guard and local source/title state.
- Preserve successful edit, edit-with-title, direct-child revision ID parsing, source fetching, post-list parsing, and reply behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post edit-form parser hardening
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A direct generated `currentRevisionId` input with no `value` still fails before mutation. | `TestForumPostEdit.test_edit_missing_current_revision_id_value_includes_site_and_post_context` replaces the direct hidden input with a value-less input and expects `NoElementException`. | A change that sends `saveEditPost`, fabricates a revision ID, raises `KeyError`, or updates local source/title rejects this local completion claim. |
| A direct generated `currentRevisionId` input with a non-numeric value still fails before mutation. | `TestForumPostEdit.test_edit_malformed_current_revision_id_value_includes_site_and_post_context` uses `value="not-a-number"` and expects `NoElementException`. | A change that sends `saveEditPost`, raises plain `ValueError`, silently coerces the value, or updates local source/title rejects this local completion claim. |
| Malformed revision value errors identify the affected site and post. | The focused regressions assert `Current revision ID value is not found for site: test-site, post: 5001` and `Current revision ID value is malformed for site: test-site, post: 5001`. | A generic parser or conversion exception without site/post context rejects this local completion claim. |
| Existing forum post editing behavior remains green. | `uv run pytest tests/unit/test_forum_post.py -q` passed 51 tests. | Regressions in edit success, edit-with-title, direct-child revision ID scoping, form retry, source fetching, lazy source, post-list parsing, or reply behavior reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 151 tests. | Regressions in forum category, thread, post, or post-revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `c15ad8d fix(forum_post): validate edit revision id values`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_current_revision_id_value_includes_site_and_post_context -q` failed before the fix with `KeyError: 'value'`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_current_revision_id_value_includes_site_and_post_context -q`.
- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_malformed_current_revision_id_value_includes_site_and_post_context -q` failed before the second fix with `ValueError: invalid literal for int() with base 10: 'not-a-number'`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_current_revision_id_value_includes_site_and_post_context tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_malformed_current_revision_id_value_includes_site_and_post_context -q`.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 51 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 151 tests.
- `uv run pytest tests/unit -q` passed 738 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `ForumPost.edit(...)` still fetches the edit form through retry-aware AMC before saving.
- If the edit form cannot be fetched after retries, the existing site/post-specific `UnexpectedException` behavior remains unchanged.
- If the generated direct `currentRevisionId` input is missing, the existing site/post-specific `NoElementException` behavior remains unchanged.
- If the generated direct `currentRevisionId` input lacks a value, `ForumPost.edit(...)` raises `NoElementException` naming the site unix name and post ID.
- If the generated direct `currentRevisionId` value is not an integer, `ForumPost.edit(...)` raises `NoElementException` naming the site unix name and post ID.
- Malformed edit-form parsing does not send the `saveEditPost` mutation or update local source/title state.
- Successful edit, edit-with-title, direct-child revision parsing, source fetching, post-list parsing, and reply behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Editing a forum post requires a fresh server-provided revision ID. If Wikidot returns an edit form with a missing or malformed revision ID value, wikidot.py should keep failing before mutation, but it should report a structured parser failure with the site and post so caller logs can route the failure without preserving raw edit-form HTML, raw AMC responses, credentials, local rollout paths, or post bodies.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum post edit-form fetching as a retry-aware read-before-mutation boundary and scoped edit-form controls to direct generated children.
- Recent context slices showed that site/object identifiers improve resumable multi-site ledgers without changing successful behavior.
- The refreshed complexity memo continues to list action/read boundaries and forum post edit revision-ID parser surfaces as follow-up leads, but this slice only claims malformed revision ID value handling.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw edit-form HTML, raw AMC responses, and post contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change edit-form request payloads, retry policy, login checks, save action retry semantics, title/source state updates, successful revision ID parsing, edit-form direct-child scoping, source fetching, post-list parsing, `ForumThread.reply(...)`, or live Wikidot behavior. It only converts missing and non-numeric generated revision ID values into site/post-context `NoElementException` failures before mutation.
