# PR Draft: Validate Forum Post Edit Form Response Bodies

## Summary

`ForumPost.edit(...)` retrieves the current post edit form through `forum/sub/ForumEditPostFormModule` before sending `saveEditPost`. Earlier local slices made that read-before-mutation boundary retry-aware, scoped `currentRevisionId` lookup to direct edit-form controls, added site/post context to missing and malformed revision-ID failures, and kept `saveEditPost` on the existing non-retried action path. The remaining malformed response-body path still read `form_response.json()["body"]`, so an AMC response without a `body` field leaked a raw `KeyError` before revision-ID validation could report the affected post and before the no-save boundary could be asserted.

This follow-up keeps login checks, retry-exhausted edit-form fetch failures, request payloads, direct-child revision-ID scoping, missing and malformed revision-ID failures, `saveEditPost` payloads, title/source local-state updates, source fetching, post-list parsing, replies, and successful edit behavior unchanged. It only treats a missing edit-form response `body` as a malformed edit-form response and raises `NoElementException` with site/post context before BeautifulSoup parsing, `currentRevisionId` lookup, or any save action.

## Related Issue

Builds on [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [162-pr-forum-post-edit-revision-error-context.md](162-pr-forum-post-edit-revision-error-context.md), [173-pr-forum-post-edit-form-fetch-failure-context.md](173-pr-forum-post-edit-form-fetch-failure-context.md), [185-pr-forum-post-edit-revision-site-context.md](185-pr-forum-post-edit-revision-site-context.md), [205-pr-forum-post-edit-revision-value-context.md](205-pr-forum-post-edit-revision-value-context.md), and [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md). Those drafts established forum post edit-form acquisition as retry-aware, read-before-mutation, edit-form scoped, and diagnosable.

No upstream issue was filed from this local workspace.

## Changes

- Add a small forum post edit-form response-body helper that reads `form_response.json().get("body")`.
- Convert missing edit-form response `body` into site/post-specific `NoElementException`.
- Preserve retry-exhausted `None` response handling as an `UnexpectedException`.
- Preserve successful `currentRevisionId` parsing, malformed revision-ID errors, no-save-on-malformed-form behavior, save payloads, local title/source updates, source fetching, post-list parsing, and replies.
- Add a focused regression for missing forum post edit-form response body handling through public `ForumPost.edit(...)`.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post edit-form response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A forum post edit-form response without JSON `body` still fails before HTML parsing, revision-ID lookup, or save action. | `TestForumPostEdit.test_edit_missing_form_response_body_includes_site_and_post_context` returns `{}` from the edit-form AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, calls `saveEditPost`, or mutates local source/title rejects this local completion claim. |
| Malformed edit-form response errors identify the affected site and post. | The focused regression asserts `Forum post edit form response body is not found for site: test-site, post: 5001`. | A generic parser exception without site/post context rejects this local completion claim. |
| Retry-exhausted `None` edit-form responses remain distinct from malformed JSON body responses. | Existing `test_edit_raises_when_form_fetch_retry_is_exhausted` remains green and expects `UnexpectedException`. | A change that turns skipped/exhausted `None` responses into body-validation failures rejects this local completion claim. |
| Existing forum post edit behavior remains green. | `uv run pytest tests/unit/test_forum_post.py -q` passed 55 tests. | Regressions in login checks, retry behavior, current revision ID parsing, no-save-on-malformed-form, save payloads, local title/source updates, source fetching, post-list parsing, or replies reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py tests/unit/test_forum_category.py -q` passed 155 tests. | Regressions in category/thread/post/revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `74a5665 fix(forum_post): validate edit form response bodies`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_form_response_body_includes_site_and_post_context -q` failed before the fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_form_response_body_includes_site_and_post_context tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_success tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_current_revision_id_includes_site_and_post_context tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_raises_when_form_fetch_retry_is_exhausted -q` passed 4 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 55 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py tests/unit/test_forum_category.py -q` passed 155 tests.
- `uv run pytest tests/unit -q` passed 745 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Forum post edit-form requests still use `forum/sub/ForumEditPostFormModule`, the same thread ID, and the same post ID.
- Missing edit-form response JSON `body` raises `NoElementException` naming the site and post.
- Missing response-body handling does not call `saveEditPost`, update local title/source state, or convert retry-exhausted `None` responses into malformed-body failures.
- Successful edit-form parsing, retry behavior, direct-child `currentRevisionId` scoping, missing/non-numeric revision-ID failures, save request shape, local title/source updates, source fetching, post-list parsing, and replies remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post editing depends on Wikidot returning a JSON `body` field for the pre-save edit form before the current revision ID can be read. If that field is missing, wikidot.py should report a structured malformed-response failure with the site and post ID, and it should do so before any save request, so caller logs can route failures without preserving raw response JSON, edit-form HTML, post source text, credentials, local rollout paths, or account details.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum post edit-form acquisition as retry-aware, mutation-safe, direct-control scoped, and backed by site/post revision-ID context.
- The immediately prior forum post source response slice showed the same raw `KeyError` failure mode at the same `ForumEditPostFormModule` response-body boundary used for source reads.
- Recent context slices showed that compact site/post identifiers improve resumable ledgers without changing successful behavior or storing raw post source text.
- The refreshed complexity memo continues to list parser/source collection helpers and action/read boundaries as follow-up leads, but this slice only claims forum post edit-form response-body validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, edit-form HTML, post source text, and private deployment details out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, retry-exhausted `None` handling, login checks, direct-child `currentRevisionId` parsing, revision-ID value validation, save request construction, title/source state updates, source fetching, post-list parsing, replies, or live Wikidot behavior. It only converts missing forum post edit-form response `body` fields into site/post-context `NoElementException` failures before parser or mutation work.
