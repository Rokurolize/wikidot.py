# PR Draft: Reject Boolean Forum Create-Thread IDs

## Summary

`ForumCategory.create_thread(...)` expects Wikidot's `newThread` action response to identify the created thread with an integer `threadId`. The existing returned-ID guard rejected missing values and string values, but it used plain `isinstance(value, int)`, so `threadId=True` passed because `bool` is an `int` subclass in Python. With `{"threadId": True, "status": "ok"}`, the method accepted the malformed server result, validated the action status, cleared the category's cached thread list, and only then failed inside `ForumThread.get_from_id(...)` as a caller-input-style `ValueError`.

This change treats boolean `threadId` values as malformed create-thread results before action-status validation, cache invalidation, or created-thread lookup. Valid integer `threadId` values, successful created-thread lookup, request payloads, text-input validation, action-status handling, and cache invalidation after confirmed successful creates remain unchanged.

## Outcome

Malformed boolean `threadId` values now raise the existing contextual `NoElementException("Thread ID is not found for site: ..., category: ...")` at the create-result boundary, and an already-loaded `ForumCategory.threads` cache is preserved because no successful create result has been proven.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum thread creation in migration scripts, moderation tooling, generated discussion workflows, audit jobs, or local tools that rely on cached category thread lists after failed mutation attempts.

## Current Evidence

Local rollout-backed drafts repeatedly established forum creation, forum thread lookup, forum action-status validation, and cached forum read/write coherence as practical surfaces. Earlier local slices made forum writes validate text inputs before login, made create-thread results identify the affected site/category, required returned action status before fetching created threads, and cleared cached category threads only after confirmed successful creation.

Those prior slices are not duplicates. [167-pr-forum-thread-create-result-context.md](167-pr-forum-thread-create-result-context.md) covered missing and string-valued `threadId` diagnostics, but not Python's boolean-as-integer edge. [252-pr-forum-category-create-thread-action-status-context.md](252-pr-forum-category-create-thread-action-status-context.md) validates returned `status` after the result ID guard. [264-pr-forum-category-create-thread-cache-invalidation.md](264-pr-forum-category-create-thread-cache-invalidation.md) clears stale thread-list caches after successful creates, but it relies on malformed create results staying before that cache mutation. [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md) validates caller-supplied text fields, not Wikidot's returned thread identity. [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md) validates public thread ID inputs, not returned create-thread result fields.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [167-pr-forum-thread-create-result-context.md](167-pr-forum-thread-create-result-context.md), [252-pr-forum-category-create-thread-action-status-context.md](252-pr-forum-category-create-thread-action-status-context.md), [264-pr-forum-category-create-thread-cache-invalidation.md](264-pr-forum-category-create-thread-cache-invalidation.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), and [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md).

## Changes

- Store the decoded `threadId` value once in `ForumCategory.create_thread(...)`.
- Reject values that are not `int` or are `bool` before returned action-status validation.
- Preserve the existing site/category `NoElementException` message for malformed create-thread IDs.
- Add a public `ForumCategory.create_thread(...)` regression proving `threadId=True` is malformed and preserves a preexisting category thread-list cache.

## Type Of Change

- Returned response-field validation fix
- Forum mutation boundary hardening
- Cache consistency preservation
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategory.create_thread(...)` must reject boolean `threadId` values as malformed create-thread results. |
| R2 | Boolean returned IDs must fail before action-status success can clear `ForumCategory._threads` or before created-thread detail lookup can run. |
| R3 | The malformed result must use the existing contextual create-result exception surface that names site and category. |
| R4 | Valid integer `threadId` values, `status: ok` creates, created-thread lookup, request payloads, text-input validation, missing/string `threadId` diagnostics, missing/non-ok status diagnostics, and successful cache invalidation must remain unchanged. |
| R5 | Tests and docs must not require live Wikidot, credentials, cookies, auth JSON, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent forum tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A create-thread response with `{"threadId": True, "status": "ok"}` raises `NoElementException` instead of treating `True` as a valid thread ID. | `TestForumCategoryCreateThread.test_create_thread_boolean_thread_id_is_malformed_and_preserves_cache` failed RED with `ValueError("thread_id must be an integer")`, then passed GREEN after boolean rejection was added to the create-result guard. | Accepting `True`, coercing it to `1`, or surfacing `ForumThread.get_from_id(...)` input validation rejects this local completion claim. | Forum category create result parsing | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | The boolean returned-ID path does not clear a cached category thread collection or fetch the created thread. | The public regression seeds `ForumCategory._threads`, expects one AMC call, and asserts the cached collection is still present after the malformed result exception. | Clearing `_threads`, calling created-thread lookup, or making a second AMC call rejects this local completion claim. | Forum category cache safety | `tests/unit/test_forum_category.py` |
| R3 | The malformed response identifies the affected site and category through the established message. | The focused regression matches `Thread ID is not found for site: test-site, category: 1001`. | Returning a generic bool/input-validation message or omitting site/category context rejects this local completion claim. | Create-result diagnostics | `tests/unit/test_forum_category.py` |
| R4 | Existing forum category/thread behavior remains stable. | `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread -q` passed 10 tests, category+thread tests passed 109 tests, the forum suite passed 265 tests, and full unit passed 1441 tests. | Regressing successful create, cache invalidation after success, text validation, action-status validation, missing/string `threadId`, thread detail reads, post workflows, or revision workflows rejects this local completion claim. | Forum create/read workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py` |
| R5 | The behavior is proven with synthetic mocked responses only. | All tests use local fixtures and mocked AMC responses; no live Wikidot action, credential, cookie, auth JSON, private forum content, raw rollout path, push, upstream Issue, or upstream PR is used. | Depending on live site state or private data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `eada06c fix(forum_category): reject boolean create thread ids`.

- RED tracer: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_boolean_thread_id_is_malformed_and_preserves_cache -q` failed before the fix because `threadId=True` reached `ForumThread.get_from_id(...)` and raised `ValueError("thread_id must be an integer")` after the create path had already accepted the malformed ID.
- GREEN tracer: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_boolean_thread_id_is_malformed_and_preserves_cache -q` passed 1 test.
- Focused create-thread class: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread -q` passed 10 tests.
- Adjacent category/thread tests: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py -q` passed 109 tests.
- Wider forum suite: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 265 tests.
- Full unit: `uv run pytest tests/unit -q` passed 1441 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 81 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files.
- `git diff --check` passed before the code commit.

Not run successfully: `command -v pyright` exited nonzero because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `ForumCategory.create_thread(...)` rejects returned boolean `threadId` values.
- The exception remains the existing contextual create-result `NoElementException` naming site and category.
- Boolean returned IDs do not clear a cached category thread collection.
- Boolean returned IDs do not trigger created-thread detail lookup.
- Valid integer create results, successful cache invalidation, existing action-status validation, forum write text validation, thread lookup, and adjacent forum workflows remain unchanged.
- The new test uses unit-level code only and does not require live Wikidot, credentials, cookies, auth JSON, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting boolean IDs could be interpreted as changing the public `ForumThread.get_from_id(...)` input boundary. Mitigation: that boundary already rejects booleans; this slice moves returned create-result classification to the correct response boundary before action status, cache mutation, or created-thread lookup.
- Risk: Tightening create-result validation could accidentally reject valid integer IDs. Mitigation: the check still accepts non-boolean integers, and existing successful create tests remained green.
- Risk: Cache behavior could regress on failed creates. Mitigation: the new regression seeds a cached thread collection and asserts it survives the malformed boolean ID path.

## Dependencies

- Existing `ForumCategory.create_thread(...)` remains the source of truth for forum thread creation.
- Existing `_require_forum_category_action_status(...)` remains the source of truth for returned `newThread` action-status validation after a valid returned thread ID is present.
- Existing `ForumThread.get_from_id(...)` remains the source of truth for public direct thread lookup input validation and created-thread detail acquisition.
- Existing `ForumCategory.threads` lazy cache behavior remains unchanged except that malformed boolean returned IDs no longer clear the cache.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-body field-type checks, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered boolean create-thread returned-ID path.

## Upstream-Safe Motivation

Returned `threadId` is a server-result field, so `ForumCategory.create_thread(...)` should classify malformed values at that boundary. Rejecting booleans there avoids a misleading public thread-ID input error and prevents failed create attempts from mutating local cached thread-list state.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established forum creation, forum action-status validation, thread lookup, thread-list caching, cache invalidation after successful creates, forum write text validation, and direct thread ID input validation as practical surfaces.
- Existing drafts covered missing/string returned `threadId`, returned action status, cache invalidation after successful creates, public forum write text inputs, and direct thread ID inputs. They did not cover Python boolean values inside the returned create-thread result.
- This slice only changes the returned create-thread ID guard. It does not change request module/action/event names, title/description/source validation, login checks, action-status validation, successful created-thread lookup, thread detail parsing, direct public thread lookup validation, forum post workflows, forum revision workflows, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private forum content, private site data, real token values, and private message contents out of upstream discussion.
