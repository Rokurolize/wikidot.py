# PR Draft: Validate Forum Thread Reply Status Type

## Summary

`ForumThread.reply(...)` sends Wikidot's `savePost` action, validates action `status`, then clears the cached post list, increments `post_count`, and updates the parent category counters/caches. Issue [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md) covered missing action `status` and explicit non-ok string statuses, but present non-string values such as `{"status": ["not-ok"]}` were still routed into `WikidotStatusCodeException` as if they were real Wikidot status codes. This change rejects malformed generated action data before treating the reply as successful.

## Outcome

Forum replies now distinguish malformed action-response shape from real Wikidot status-code failures, preserving existing string-status behavior while surfacing type-corrupt generated responses with site, thread, event, field, and type context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum replies, moderation tooling, migration scripts, generated discussion workflows, cached forum ledgers, or local fixtures where a malformed reply action response must not be mistaken for a confirmed successful mutation.

## Current Evidence

Local rollout-backed drafts already identify forum mutation actions as practical shared workflows. Existing drafts [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [167-pr-forum-thread-create-result-context.md](167-pr-forum-thread-create-result-context.md), [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md), [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [369-pr-validate-forum-thread-reply-parent-id.md](369-pr-validate-forum-thread-reply-parent-id.md), and [684-pr-validate-forum-thread-reply-retained-id-state.md](684-pr-validate-forum-thread-reply-retained-id-state.md) cover retry boundaries, edit-form fetches, create-result diagnostics, adjacent forum-post edit action status, reply missing/non-ok action status, forum write text inputs, parent-post IDs, and retained reply thread IDs.

Adjacent action-status type drafts [714-pr-validate-page-save-status-type.md](714-pr-validate-page-save-status-type.md), [715-pr-validate-private-message-send-status-type.md](715-pr-validate-private-message-send-status-type.md), [716-pr-validate-site-application-action-status-type.md](716-pr-validate-site-application-action-status-type.md), [717-pr-validate-site-member-action-status-type.md](717-pr-validate-site-member-action-status-type.md), [718-pr-validate-site-invite-action-status-type.md](718-pr-validate-site-invite-action-status-type.md), and [719-pr-validate-forum-category-create-thread-status-type.md](719-pr-validate-forum-category-create-thread-status-type.md) establish the same module-level response-shape pattern on other mutation actions. Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) is not a duplicate: it covers raw Ajax Module Connector response envelope status typing before module-level action payload handling. This slice validates the `savePost` action response consumed by `ForumThread.reply(...)`. No upstream issue was filed from this local workspace.

## Changes

- Add a type guard in the forum-thread reply action status extractor.
- Raise `NoElementException` for a present non-string `status` with site, thread ID, event, field, expected type, and actual type context.
- Preserve Issue 251 missing-status diagnostics.
- Preserve explicit non-ok string handling through `WikidotStatusCodeException`.
- Add a focused regression proving malformed status types are decoded once, preserve cached posts, preserve thread/category post counts, and preserve cached category threads.
- Add a compatibility regression proving explicit non-ok string statuses remain status-code failures and preserve the same local state.

## Type Of Change

- Response-shape validation
- Forum reply action hardening
- Generated response data diagnostics
- Cache/count consistency preservation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThread.reply(...)` must reject a non-string `savePost` response `status` with `NoElementException` containing site, thread ID, event, `field=status`, `expected=str`, and the actual type. |
| R2 | A missing `status` field must keep the existing Issue 251 missing-status diagnostic. |
| R3 | Explicit non-ok string statuses must still raise `WikidotStatusCodeException`. |
| R4 | Malformed and explicit non-ok action statuses must not clear cached posts, increment thread post counts, increment category post counts, or invalidate cached category threads. |
| R5 | Valid successful replies must remain unchanged. |
| R6 | Adjacent forum workflows and repository quality gates must remain green. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `{"status": ["not-ok"]}` fails with malformed reply action status context. | `test_reply_malformed_action_status_type_preserves_cache_and_counts` failed RED with `WikidotStatusCodeException`, then passed GREEN after status typing was added. | Treating a list, dict, number, or object as a Wikidot status code rejects this local completion claim. | Forum thread action response shape | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | `{}` still raises the Issue 251 missing-status message with site, thread, event, and field context. | `test_reply_missing_action_status_does_not_update_local_state` passed unchanged. | Changing missing-status exception type, dropping context, or masking it behind type/status-code handling rejects this local completion claim. | Forum thread missing action status | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R3 | `{"status": "not_ok"}` keeps the status-code path. | `test_reply_explicit_non_ok_action_status_preserves_cache_and_counts` passed and asserts `status_code == "not_ok"`. | Reclassifying non-ok strings as malformed response shape rejects this local completion claim. | Forum thread status-code handling | `tests/unit/test_forum_thread.py` |
| R4 | Malformed and explicit non-ok statuses preserve thread/category local state. | The new malformed-status and non-ok-string regressions assert one AMC call, one JSON decode, unchanged `_posts`, unchanged `post_count`, unchanged category `posts_count`, and preserved cached category threads. | Clearing `_posts`, incrementing counts, invalidating category threads, or decoding repeatedly rejects this local completion claim. | Forum reply mutation/cache boundary | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R5 | Successful valid reply behavior remains stable. | `test_reply_success` and `test_reply_success_updates_category_post_count_and_invalidates_threads` passed in focused GREEN; `TestForumThreadReply` passed 27 tests. | Regressing login, request payloads, parent replies, valid title/source handling, cache invalidation after confirmed replies, or count updates rejects this local completion claim. | Reply workflow | `tests/unit/test_forum_thread.py` |
| R6 | Adjacent forum behavior and repo quality gates remain green. | Forum-thread passed 223 tests, adjacent forum suites passed 882 tests, full unit passed 3588 tests, ruff, mypy, pyright, and `git diff --check` passed. | Any test, lint, format, type, or whitespace failure rejects this local completion claim. | Repository quality gates | `tests/unit`, `src`, `tests` |
| R7 | No live site state or private material is needed to prove the behavior. | The regressions use synthetic unit-level response bodies and mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `e2a8842 fix(forum_thread): validate reply status type`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_malformed_action_status_type_preserves_cache_and_counts -q` failed before the fix with `WikidotStatusCodeException` instead of the expected malformed-shape `NoElementException`.
- GREEN focused: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_success tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_success_updates_category_post_count_and_invalidates_threads tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_rejects_malformed_retained_thread_ids_before_login tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_rejects_negative_retained_thread_id_before_login tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_missing_action_status_does_not_update_local_state tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_malformed_action_status_type_preserves_cache_and_counts tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_explicit_non_ok_action_status_preserves_cache_and_counts -q` passed 13 tests.
- `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadReply -q` passed 27 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 223 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 882 tests.
- `uv run pytest tests/unit -q` passed 3588 tests.
- `uv run ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` left both files unchanged.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `{"status": ["not-ok"]}` raises `NoElementException` with site, thread ID, event, `field=status`, `expected=str`, and `actual=list` context.
- `{}` still raises the existing missing-status message from Issue 251.
- `{"status": "not_ok"}` still raises `WikidotStatusCodeException`.
- Malformed and explicit non-ok statuses do not clear cached posts.
- Malformed and explicit non-ok statuses do not increment thread or category post counts.
- Malformed and explicit non-ok statuses do not invalidate cached category thread lists.
- Successful valid replies keep the existing login check, request payload shape, title/source handling, optional parent reply handling, cache invalidation, count updates, and method-chaining return.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A caller may have relied on a non-string `status` object being formatted into a `WikidotStatusCodeException`. Mitigation: Wikidot action statuses are strings, Issue 403 already validates raw AMC statuses as strings, and module-level action responses should reject malformed generated data before business handling.
- Risk: This could be confused with reply missing-status handling. Mitigation: Issue 251 covers missing/non-ok string status; this slice covers a present status with malformed type.
- Risk: This could be confused with raw AMC response typing. Mitigation: Issue 403 covers the raw connector envelope; this slice covers the forum-thread `savePost` action payload used by `ForumThread.reply(...)`.
- Risk: This could be confused with adjacent forum mutation actions. Mitigation: Issue 250 covers forum-post edit missing/non-ok status, Issue 719 covers forum-category create-thread status type, and this slice covers forum-thread replies.
- Risk: Tightening action response shape could hide legitimate non-ok Wikidot string statuses. Mitigation: non-ok strings are deliberately preserved on the existing `WikidotStatusCodeException` path.
- Risk: The error could become too generic for generated fixtures. Mitigation: the diagnostic names the site, thread ID, event, field, expected type, and actual type.

## Dependencies

- Existing `ForumThread.reply(...)` remains responsible for forum reply orchestration.
- Existing `WikidotStatusCodeException` handling remains responsible for explicit non-ok string statuses.
- Existing `NoElementException` remains the parser/data-shape exception for missing or malformed response fields.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, complexity candidates, or status type guards outside this now-covered forum-thread reply action status type path.

## Upstream-Safe Motivation

`ForumThread.reply(...)` treats `savePost` responses as status-bearing action payloads before mutating local thread and category state. Rejecting malformed status types at that boundary keeps generated or adapted response data from masquerading as a real Wikidot status code and makes forum reply failures easier to diagnose without changing successful replies or valid string status handling.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established browser-free forum replies, forum mutation diagnostics, generated discussion workflows, moderation tooling, cached thread post lists, and parent category counters/caches as practical consumers of `ForumThread.reply(...)`.
- Existing forum-thread and raw AMC drafts covered missing action status context, explicit non-ok action strings, text/parent-ID preflights, retained thread-ID shape/range, and raw connector envelope status typing; they did not validate the module-level `savePost` action status type.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private forum content, private site data, reply source text from real sites, and source text from real sites out of upstream discussion.
