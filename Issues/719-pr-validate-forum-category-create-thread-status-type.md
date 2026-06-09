# PR Draft: Validate Forum Category Create-Thread Status Type

## Summary

`ForumCategory.create_thread(...)` sends Wikidot's `newThread` action, validates the returned `threadId`, validates action `status`, clears the cached category thread list, and fetches the created thread. Issue [252-pr-forum-category-create-thread-action-status-context.md](252-pr-forum-category-create-thread-action-status-context.md) covered missing action `status` and explicit non-ok string statuses, but present non-string values such as `{"threadId": 3001, "status": ["not-ok"]}` were still routed into `WikidotStatusCodeException` as if they were real Wikidot status codes. This change rejects malformed generated action data before treating thread creation as successful.

## Outcome

Forum thread creation now distinguishes malformed action-response shape from real Wikidot status-code failures, preserving existing string-status behavior while surfacing type-corrupt generated responses with site, category, event, field, and type context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum thread creation, migration scripts, moderation tooling, generated discussion workflows, fixtures, adapters, or cached forum ledgers where a malformed create-thread action response must not be mistaken for a confirmed successful mutation.

## Current Evidence

Local rollout-backed drafts already identify forum thread creation and forum mutation actions as practical shared workflows. Existing drafts [167-pr-forum-thread-create-result-context.md](167-pr-forum-thread-create-result-context.md), [252-pr-forum-category-create-thread-action-status-context.md](252-pr-forum-category-create-thread-action-status-context.md), [264-pr-forum-category-create-thread-cache-invalidation.md](264-pr-forum-category-create-thread-cache-invalidation.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md), and [652-pr-validate-non-negative-create-thread-result-ids.md](652-pr-validate-non-negative-create-thread-result-ids.md) cover create-result diagnostics, missing/non-ok action status, cache invalidation after confirmed creates, text preflights, boolean returned IDs, and negative returned IDs.

Adjacent action-status type drafts [714-pr-validate-page-save-status-type.md](714-pr-validate-page-save-status-type.md), [715-pr-validate-private-message-send-status-type.md](715-pr-validate-private-message-send-status-type.md), [716-pr-validate-site-application-action-status-type.md](716-pr-validate-site-application-action-status-type.md), [717-pr-validate-site-member-action-status-type.md](717-pr-validate-site-member-action-status-type.md), and [718-pr-validate-site-invite-action-status-type.md](718-pr-validate-site-invite-action-status-type.md) establish the same module-level response-shape pattern on other mutation actions. Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) is not a duplicate: it covers raw Ajax Module Connector response envelope status typing before module-level action payload handling. This slice validates the `newThread` action response consumed by `ForumCategory.create_thread(...)`. No upstream issue was filed from this local workspace.

## Changes

- Add a type guard in the forum-category create-thread action status extractor.
- Raise `NoElementException` for a present non-string `status` with site, category ID, event, field, expected type, and actual type context.
- Preserve Issue 252 missing-status diagnostics.
- Preserve explicit non-ok string handling through `WikidotStatusCodeException`.
- Preserve returned `threadId` validation order: missing, non-integer, boolean, and negative returned IDs remain rejected before action-status validation.
- Add a focused regression proving malformed status types are decoded once, preserve a cached thread list, and do not fetch created-thread details.
- Add a compatibility regression proving explicit non-ok string statuses remain status-code failures and do not fetch created-thread details.

## Type Of Change

- Response-shape validation
- Forum create-thread action hardening
- Generated response data diagnostics
- Cache consistency preservation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategory.create_thread(...)` must reject a non-string `newThread` response `status` with `NoElementException` containing site, category ID, event, `field=status`, `expected=str`, and the actual type. |
| R2 | A missing `status` field must keep the existing Issue 252 missing-status diagnostic. |
| R3 | Explicit non-ok string statuses must still raise `WikidotStatusCodeException`. |
| R4 | Returned `threadId` validation must remain the first create-result guard for missing, non-integer, boolean, and negative IDs. |
| R5 | Malformed and explicit non-ok action statuses must not fetch created-thread details or clear a cached category thread list. |
| R6 | Valid successful thread creation must remain unchanged. |
| R7 | Adjacent forum workflows and repository quality gates must remain green. |
| R8 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `{"threadId": 3001, "status": ["not-ok"]}` fails with malformed create-thread action status context. | `test_create_thread_malformed_action_status_type_preserves_cache_and_does_not_fetch_created_thread` failed RED with `WikidotStatusCodeException`, then passed GREEN after status typing was added. | Treating a list, dict, number, or object as a Wikidot status code rejects this local completion claim. | Forum category action response shape | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | `{"threadId": 3001}` still raises the Issue 252 missing-status message with site, category, event, and field context. | `test_create_thread_missing_action_status_does_not_fetch_created_thread` passed unchanged. | Changing missing-status exception type, dropping context, or masking it behind type/status-code handling rejects this local completion claim. | Forum category missing action status | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R3 | `{"threadId": 3001, "status": "not_ok"}` keeps the status-code path. | `test_create_thread_explicit_non_ok_action_status_preserves_cache_and_does_not_fetch_created_thread` passed and asserts `status_code == "not_ok"`. | Reclassifying non-ok strings as malformed response shape rejects this local completion claim. | Forum category status-code handling | `tests/unit/test_forum_category.py` |
| R4 | Returned `threadId` guards remain ordered before action-status validation. | Focused GREEN covered `test_create_thread_missing_or_invalid_thread_id_raises`, `test_create_thread_boolean_thread_id_is_malformed_and_preserves_cache`, and `test_create_thread_negative_thread_id_is_malformed_and_preserves_cache`. | Reporting action-status errors for malformed returned IDs, accepting booleans, accepting negative IDs, or coercing strings rejects this local completion claim. | Create-result ID diagnostics | `tests/unit/test_forum_category.py` |
| R5 | Malformed and explicit non-ok statuses stop before created-thread lookup and preserve cached threads. | The new malformed-status and non-ok-string regressions each assert one AMC call and preserved `_threads`. | Performing `ForumThread.get_from_id(...)`, clearing `_threads`, or mutating local cache state rejects this local completion claim. | Forum category mutation/cache boundary | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R6 | Successful valid create-thread behavior remains stable. | `test_create_thread_success_invalidates_cached_threads` passed in focused GREEN; `TestForumCategoryCreateThread` passed 14 tests. | Regressing login, request payloads, valid returned IDs, cache invalidation after confirmed creates, or created-thread lookup rejects this local completion claim. | Create-thread workflow | `tests/unit/test_forum_category.py` |
| R7 | Adjacent forum behavior and repo quality gates remain green. | Forum-category passed 140 tests, adjacent forum suites passed 880 tests, full unit passed 3586 tests, ruff, mypy, pyright, and `git diff --check` passed. | Any test, lint, format, type, or whitespace failure rejects this local completion claim. | Repository quality gates | `tests/unit`, `src`, `tests` |
| R8 | No live site state or private material is needed to prove the behavior. | The regressions use synthetic unit-level response bodies and mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `685cf72 fix(forum_category): validate create thread status type`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_malformed_action_status_type_preserves_cache_and_does_not_fetch_created_thread -q` failed before the fix with `WikidotStatusCodeException` instead of the expected malformed-shape `NoElementException`.
- GREEN focused: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_missing_or_invalid_thread_id_raises tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_boolean_thread_id_is_malformed_and_preserves_cache tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_negative_thread_id_is_malformed_and_preserves_cache tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_missing_action_status_does_not_fetch_created_thread tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_malformed_action_status_type_preserves_cache_and_does_not_fetch_created_thread tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_explicit_non_ok_action_status_preserves_cache_and_does_not_fetch_created_thread tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_success_invalidates_cached_threads -q` passed 9 tests.
- `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread -q` passed 14 tests.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 140 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 880 tests.
- `uv run pytest tests/unit -q` passed 3586 tests.
- `uv run ruff format src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` left both files unchanged.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `{"threadId": 3001, "status": ["not-ok"]}` raises `NoElementException` with site, category ID, event, `field=status`, `expected=str`, and `actual=list` context.
- `{"threadId": 3001}` still raises the existing missing-status message from Issue 252.
- `{"threadId": 3001, "status": "not_ok"}` still raises `WikidotStatusCodeException`.
- Missing, non-integer, boolean, and negative returned `threadId` values keep their existing response-boundary diagnostics before action-status validation.
- Malformed and explicit non-ok statuses do not fetch created-thread details.
- Malformed and explicit non-ok statuses do not clear a cached category thread collection.
- Successful valid creates keep the existing login check, request payload shape, title/description/source handling, integer `threadId` handling, cache invalidation, and returned `ForumThread` lookup behavior.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A caller may have relied on a non-string `status` object being formatted into a `WikidotStatusCodeException`. Mitigation: Wikidot action statuses are strings, Issue 403 already validates raw AMC statuses as strings, and module-level action responses should reject malformed generated data before business handling.
- Risk: This could be confused with create-result `threadId` validation. Mitigation: Issues 167, 407, and 652 cover returned thread ID shape/range; this slice only covers action `status` after a valid returned ID is present.
- Risk: This could be confused with raw AMC response typing. Mitigation: Issue 403 covers the raw connector envelope; this slice covers the forum-category `newThread` action payload used by `ForumCategory.create_thread(...)`.
- Risk: Tightening action response shape could hide legitimate non-ok Wikidot string statuses. Mitigation: non-ok strings are deliberately preserved on the existing `WikidotStatusCodeException` path.
- Risk: The error could become too generic for generated fixtures. Mitigation: the diagnostic names the site, category ID, event, field, expected type, and actual type.

## Dependencies

- Existing `ForumCategory.create_thread(...)` remains responsible for forum thread creation orchestration.
- Existing returned `threadId` validation remains responsible for create-result identity fields.
- Existing `WikidotStatusCodeException` handling remains responsible for explicit non-ok string statuses.
- Existing `NoElementException` remains the parser/data-shape exception for missing or malformed response fields.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, complexity candidates, or status type guards outside this now-covered forum-category create-thread action status type path.

## Upstream-Safe Motivation

`ForumCategory.create_thread(...)` treats `newThread` responses as status-bearing action payloads after a valid returned thread ID is present. Rejecting malformed status types at that boundary keeps generated or adapted response data from masquerading as a real Wikidot status code and makes forum creation failures easier to diagnose without changing successful creates or valid string status handling.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established browser-free forum creation, forum mutation diagnostics, generated discussion workflows, moderation tooling, cached category thread lists, and created-thread lookup as practical consumers of `ForumCategory.create_thread(...)`.
- Existing forum-category and raw AMC drafts covered missing action status context, explicit non-ok action strings, returned `threadId` shape/range, cache invalidation after successful creates, and raw connector envelope status typing; they did not validate the module-level `newThread` action status type.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private forum content, private site data, thread source text from real sites, and source text from real sites out of upstream discussion.
