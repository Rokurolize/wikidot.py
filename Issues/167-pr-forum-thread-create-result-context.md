# PR Draft: Include Context In Forum Thread Create Result Errors

## Summary

`ForumCategory.create_thread(...)` sends a Wikidot forum `newThread` action and expects the response body to contain an integer `threadId`. When that response was missing `threadId` or returned it with the wrong type, the method raised `NoElementException("Thread ID is not found.")`, which did not identify which site/category creation result failed.

This follow-up preserves login checking, the AMC request payload, successful thread creation, and the follow-up `ForumThread.get_from_id(...)` lookup, but includes the target site unix name and category ID in malformed create-thread response failures.

## Related Issue

Builds on [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), and [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), because those drafts established forum category/thread paths as practical rollout-backed surfaces. It also follows the recent parser/action-context direction in [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [162-pr-forum-post-edit-revision-error-context.md](162-pr-forum-post-edit-revision-error-context.md), and [166-pr-user-profile-parse-context.md](166-pr-user-profile-parse-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Include site unix name and category ID when `ForumCategory.create_thread(...)` receives a missing or non-integer `threadId`.
- Strengthen the existing missing/invalid `threadId` parametrized test to assert the contextual error message.
- Preserve the existing login gate, `newThread` action payload, title/description/source submission, successful integer `threadId` handling, and returned `ForumThread` lookup.
- Avoid including raw response bodies, thread source text, or user-provided thread content in the exception.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum thread creation result error-context ergonomics
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Missing `threadId` still fails. | `TestForumCategoryCreateThread.test_create_thread_missing_or_invalid_thread_id_raises` covers `{}`. | A change that silently accepts a response without `threadId` rejects this local completion claim. |
| Non-integer `threadId` still fails. | The same parametrized test covers `{"threadId": "3001"}`. | A change that coerces or accepts a string `threadId` rejects this local completion claim. |
| Malformed create-thread responses identify the failed target. | The focused test asserts `Thread ID is not found for site: test-site, category: 1001`. | The RED test failed before the fix because the message only said `Thread ID is not found.` |
| Successful thread creation remains unchanged. | `uv run pytest tests/unit/test_forum_category.py -q` passed 19 tests. | Regressions in login checking, request payload, integer `threadId` handling, or `ForumThread.get_from_id(...)` reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 148 tests. | Regressions in category/thread/post parsing or source/revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `f7c0f1c fix(forum_category): include context in create-thread errors`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_missing_or_invalid_thread_id_raises -q` failed before the fix because the message lacked site/category context.
- GREEN: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_missing_or_invalid_thread_id_raises -q`
- `uv run pytest tests/unit/test_forum_category.py -q` passed 19 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 148 tests.
- `uv run pytest tests/unit -q` passed 722 tests.
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Missing and non-integer create-thread `threadId` responses still raise `NoElementException`.
- Those exceptions include the site unix name and category ID.
- Successful thread creation, login checking, request payload construction, and returned `ForumThread` lookup remain unchanged.
- The exception does not expose raw response bodies, thread source text, thread description, credentials, or browser/session details.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Thread creation is a mutation path, so diagnostics should identify the failed target without logging raw submitted content. Site/category context gives maintainers enough information to map a malformed Wikidot response back to the attempted forum category while keeping user-provided title, description, and source out of the exception.

## Local Evidence, Not For Upstream Paste

- Earlier rollout-backed forum drafts established category/thread/post retrieval and parsing as practical local Codex surfaces.
- Recent parser/action-context slices showed that object-specific `NoElementException` messages improve resumable ledgers without changing successful behavior.
- The refreshed complexity memo continues to keep action/read boundaries and remaining direct property/parser failure messages as follow-up leads, but this slice only claims malformed create-thread response diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw thread source text, and raw response bodies out of upstream discussion.

## Additional Notes

This slice intentionally does not change the login gate, request module/action/event names, submitted title/description/source fields, accepted `threadId` type, `ForumThread.get_from_id(...)`, returned `ForumThread` shape, or live Wikidot behavior. It only adds site/category context to an existing malformed create-thread response failure.
