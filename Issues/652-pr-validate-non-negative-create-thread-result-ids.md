# PR Draft: Validate Non-Negative Create-Thread Result IDs

## Summary

`ForumCategory.create_thread(...)` sends Wikidot's `newThread` action, reads the returned `threadId`, validates the `newThread` status, clears the category thread cache, and then fetches the created thread. Existing local drafts already reject missing, non-integer, and boolean returned `threadId` values, and direct `ForumThread` lookup IDs are now range-checked as non-negative. One response-boundary gap remained: a returned integer such as `{"threadId": -1, "status": "ok"}` passed the create-result guard, accepted the action status, cleared `ForumCategory._threads`, and only then failed through direct lookup validation with `ValueError("thread_id must be non-negative")`.

This change rejects negative returned create-thread IDs at the `ForumCategory.create_thread(...)` response boundary with `NoElementException("Thread ID must be non-negative for site: ..., category: ...")`. It deliberately preserves missing/non-integer/boolean `threadId` diagnostics, returned action-status validation, successful cache invalidation after valid creates, created-thread lookup, text-input validation, zero-ID compatibility, valid positive IDs, and adjacent forum workflows.

## Outcome

Malformed negative create-thread result IDs no longer clear cached category thread lists or get reclassified as caller-provided direct lookup errors. Valid create results keep the same behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum thread creation in generated discussion workflows, migration scripts, moderation tooling, local fixtures, adapters, or cached forum ledgers where failed create attempts must not corrupt local cache state.

## Current Evidence

Forum create-thread drafts [167-pr-forum-thread-create-result-context.md](167-pr-forum-thread-create-result-context.md), [252-pr-forum-category-create-thread-action-status-context.md](252-pr-forum-category-create-thread-action-status-context.md), [264-pr-forum-category-create-thread-cache-invalidation.md](264-pr-forum-category-create-thread-cache-invalidation.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), and [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md) establish `ForumCategory.create_thread(...)` as a practical mutation and cache boundary. Forum thread drafts [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), and [642-pr-validate-non-negative-forum-thread-ids.md](642-pr-validate-non-negative-forum-thread-ids.md) establish direct thread-ID validation, but those are caller/direct-record boundaries rather than returned create-result fields.

This slice is not a duplicate of those drafts. Issue 167 covers missing and non-integer `threadId` response context. Issue 407 covers Python boolean returned IDs before action-status and cache mutation. Issue 264 clears cached category thread lists only after a confirmed successful create. Issue 642 rejects negative direct `ForumThread` IDs and lookup inputs, but before this slice the negative returned ID reached that direct lookup validator after the create path had already treated the result as successful enough to clear the cache.

## Related Issue / Non-Duplicate Analysis

Builds directly on [167-pr-forum-thread-create-result-context.md](167-pr-forum-thread-create-result-context.md), [252-pr-forum-category-create-thread-action-status-context.md](252-pr-forum-category-create-thread-action-status-context.md), [264-pr-forum-category-create-thread-cache-invalidation.md](264-pr-forum-category-create-thread-cache-invalidation.md), [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md), and [642-pr-validate-non-negative-forum-thread-ids.md](642-pr-validate-non-negative-forum-thread-ids.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject negative returned `ForumCategory.create_thread(...)` response `threadId` values with `NoElementException("Thread ID must be non-negative for site: ..., category: ...")`.
- Validate the non-negative range after the existing non-boolean integer response check and before returned action-status validation.
- Preserve `NoElementException("Thread ID is not found for site: ..., category: ...")` for missing, non-integer, and boolean returned IDs.
- Preserve action-status validation before created-thread lookup for valid non-negative integer returned IDs.
- Preserve cache invalidation after confirmed successful valid creates.
- Preserve valid positive IDs and zero-ID compatibility.
- Leave live Wikidot behavior, pushes, upstream Issues, and upstream PRs unchanged.

## Type Of Change

- Returned response-field validation
- Forum mutation-boundary hardening
- Cache consistency preservation
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A returned create-thread `threadId` such as `-1` or `-100` must raise `NoElementException("Thread ID must be non-negative for site: ..., category: ...")` before created-thread lookup. |
| R2 | Negative returned IDs must not clear a preexisting `ForumCategory._threads` cache. |
| R3 | Existing missing, non-integer, and boolean returned `threadId` diagnostics must remain unchanged. |
| R4 | Missing returned action status must still fail after a valid returned ID and before created-thread lookup. |
| R5 | Valid successful creates must still clear stale category thread caches and fetch the created thread. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, create-thread tests, forum-category tests, adjacent forum tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative create-thread result IDs fail at the response boundary. | `test_create_thread_negative_thread_id_is_malformed_and_preserves_cache` failed RED for `-1` and `-100` because both values reached `ForumThread.get_from_id(...)` and raised `ValueError("thread_id must be non-negative")`, then passed GREEN after the create-result guard rejected values below zero. | Accepting negative returned IDs, surfacing direct lookup `ValueError`, coercing values, or fetching created-thread details rejects this local completion claim. | `ForumCategory.create_thread` response parsing | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Negative returned IDs preserve cached category threads. | The new regression seeds `ForumCategory._threads`, expects one AMC call, and asserts the cache object is still present after the malformed result exception. | Clearing `_threads`, making a second AMC call, or mutating local category cache state rejects this local completion claim. | Forum category cache state | `tests/unit/test_forum_category.py` |
| R3 | Existing malformed returned-ID diagnostics remain stable. | Missing/non-integer returned-ID tests and boolean returned-ID cache-preservation tests passed in the focused RED and GREEN commands. | Changing the existing `Thread ID is not found...` message, accepting booleans, or coercing strings rejects this local completion claim. | Create-result ID diagnostics | `tests/unit/test_forum_category.py` |
| R4 | Missing action-status handling remains after valid returned-ID parsing. | `test_create_thread_missing_action_status_does_not_fetch_created_thread` passed in the focused RED and GREEN commands. | Checking status before malformed returned-ID range validation, fetching created-thread details, or changing status diagnostics rejects this local completion claim. | Create-result action status | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R5 | Valid create-thread behavior remains stable. | `test_create_thread_success_invalidates_cached_threads` passed in the focused RED and GREEN commands, the create-thread class passed 12 tests, forum-category passed 111 tests, adjacent forum suites passed 583 tests, and full unit passed 2949 tests. | Regressing successful creates, request payloads, cache invalidation, created-thread lookup, text validation, forum category/thread/post/revision behavior, or any existing unit test rejects this local completion claim. | Forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic responses and mocks only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum markup from real sites, thread source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, create-thread class, forum-category suite, adjacent forum suites, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `09e4eaa fix(forum_category): validate create thread ids`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_missing_or_invalid_thread_id_raises tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_boolean_thread_id_is_malformed_and_preserves_cache tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_negative_thread_id_is_malformed_and_preserves_cache tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_missing_action_status_does_not_fetch_created_thread tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_success_invalidates_cached_threads -q` failed 2 negative returned-ID cases before the fix; 5 missing/non-integer/boolean/status/success guards stayed green.
- GREEN: `uv run ruff format src/wikidot/module/forum_category.py tests/unit/test_forum_category.py && uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_missing_or_invalid_thread_id_raises tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_boolean_thread_id_is_malformed_and_preserves_cache tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_negative_thread_id_is_malformed_and_preserves_cache tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_missing_action_status_does_not_fetch_created_thread tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_success_invalidates_cached_threads -q` left 2 files unchanged and passed 7 tests.
- `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread -q` passed 12 tests.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 111 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 583 tests.
- `uv run pytest tests/unit -q` passed 2949 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumCategory.create_thread(...)` rejects returned `threadId=-1` and `threadId=-100` with `NoElementException`.
- The exception message includes `Thread ID must be non-negative`, the site unix name, and the category ID.
- Negative returned IDs do not clear a cached category thread collection.
- Negative returned IDs do not trigger created-thread detail lookup.
- Missing, non-integer, and boolean returned IDs keep the existing `Thread ID is not found...` diagnostic.
- Missing action status for a valid returned ID still fails before created-thread lookup.
- Successful valid creates still clear stale category thread caches and return the fetched `ForumThread`.
- Live Wikidot behavior, pushes, upstream Issues, and upstream PRs remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Returned `threadId` is a server-result field, so `ForumCategory.create_thread(...)` should classify impossible IDs before treating the create as successful enough to clear local cache state. Rejecting negative returned IDs at this boundary avoids a misleading public direct-lookup error and prevents failed create attempts from mutating cached category thread lists.

## Local Evidence

- Local rollout-backed drafts repeatedly identify browser-free forum creation, forum action responses, direct created-thread lookup, cached category thread lists, migration scripts, moderation tooling, and generated discussion workflows as practical surfaces.
- Existing local drafts covered missing/non-integer returned IDs, boolean returned IDs, returned action-status diagnostics, cache invalidation after successful creates, forum write text validation, and direct thread-ID range validation, but did not cover negative integer returned `threadId` values at the create-result boundary.
- The focused RED failure showed negative returned IDs reached direct thread lookup and raised a public lookup `ValueError` before this slice.
- This slice only validates non-negative create-thread result IDs. It does not change login behavior, request construction, title/description/source validation, returned action-status validation, created-thread detail parsing, valid cache invalidation, direct thread lookup APIs, live Wikidot behavior, or upstream actions.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum markup from real sites, private post data, thread source text, and private site data out of upstream discussion.

## Additional Notes

This change intentionally does not require positive IDs. It preserves the local project's zero-ID compatibility pattern for direct identity hardening while rejecting the impossible negative range before cache mutation.
