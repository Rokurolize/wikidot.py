# PR Draft: Validate Forum Thread Reply Response Payload

## Summary

`ForumThread.reply(...)` now validates that decoded `savePost` action responses are dictionaries before reading `status`. Non-mapping payloads such as `["not-ok"]` raise contextual `NoElementException` with site, thread ID, event, expected type, and actual type context instead of leaking a raw list `TypeError`.

The change is intentionally narrow: valid `{"status": "ok"}` replies, missing `status` diagnostics, non-string `status` diagnostics, explicit non-ok string status handling, cached post invalidation, thread post counts, category post counts, and category thread-cache invalidation remain unchanged.

## Problem Statement

Forum replies treat the decoded `savePost` response as a status-bearing action object before clearing cached posts and incrementing local thread/category counters. Earlier local slices covered missing reply action `status`, explicit non-ok string statuses, present non-string statuses such as `{"status": ["not-ok"]}`, write text inputs, parent-post IDs, retained thread IDs, and retained site/client boundaries. One response-shape gap remained: if `response.json()` returned a non-dictionary payload, `_require_forum_thread_action_status(...)` attempted `data["status"]` and leaked raw `TypeError`.

That failure gives callers neither the forum reply action context nor a stable wikidot.py data-shape exception. Generated fixtures, response adapters, recorded traffic, or mocked responses should be classified before field access, and failed reply responses must not clear cached posts or update local counters.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free forum replies, generated discussion workflows, migration tooling, moderation utilities, cached forum ledgers, and local fixtures as practical automation surfaces: [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md), [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [369-pr-validate-forum-thread-reply-parent-id.md](369-pr-validate-forum-thread-reply-parent-id.md), [684-pr-validate-forum-thread-reply-retained-id-state.md](684-pr-validate-forum-thread-reply-retained-id-state.md), [720-pr-validate-forum-thread-reply-status-type.md](720-pr-validate-forum-thread-reply-status-type.md), and [802-pr-validate-forum-action-site-clients.md](802-pr-validate-forum-action-site-clients.md).

This slice is not a duplicate of [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md). Issue 251 covered mapping responses with missing `status` and explicit non-ok string statuses.

This slice is not a duplicate of [720-pr-validate-forum-thread-reply-status-type.md](720-pr-validate-forum-thread-reply-status-type.md). Issue 720 covered a present non-string `status` field inside a mapping, such as `{"status": ["not-ok"]}`. This slice covers the decoded `savePost` response payload not being a mapping before status lookup starts.

This slice is not a duplicate of [812-pr-validate-forum-category-create-response-payload.md](812-pr-validate-forum-category-create-response-payload.md). Issue 812 covers the adjacent `ForumCategory.create_thread(...)` `newThread` response payload, which also validates returned `threadId` and created-thread lookup behavior. This slice covers `ForumThread.reply(...)`.

Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) covers the raw Ajax Module Connector response envelope before module-level action payload handling.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free forum replies through `ForumThread.reply(...)`.
- Discussion migration and moderation tools that reply to existing forum threads.
- Generated forum ledgers, fixtures, and recorded-response tests that decode action responses before returning them to wikidot.py module code.

## Proposed Fix

- Validate the decoded `savePost` response payload as a dictionary in `_require_forum_thread_action_status(...)`.
- Reject non-dictionary payloads with `NoElementException` before `status` lookup.
- Include only structural context and type names in the diagnostic, not raw response data.
- Preserve existing dictionary `status` validation and status-code handling.

## Implementation Notes

Implemented locally in commit `678a8c1 fix(forum_thread): validate reply response payload`.

The implementation widens `_require_forum_thread_action_status(...)` to accept `object` and adds one preflight guard:

```python
if not isinstance(data, dict):
    raise NoElementException(
        f"Forum thread action response is malformed for site: {thread.site.unix_name}, thread: {thread.id} "
        f"(event={event}, expected=dict, actual={type(data).__name__})"
    )
```

The RED regression mocked `ForumThread.reply(...)`'s `savePost` response as `["not-ok"]`. Before the fix, the helper leaked `TypeError: list indices must be integers or slices, not str`. After the fix, the same case raises contextual `NoElementException`, decodes the response once, preserves cached posts, preserves cached category threads, and does not update thread or category post counts.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Non-dictionary reply payloads fail before `status` lookup. | `test_reply_malformed_action_response_type_preserves_cache_and_counts` failed RED with raw `TypeError`, then passed GREEN. | Reaching `data["status"]`, leaking `TypeError`, coercing the payload, or treating a list as a reply result rejects this claim. |
| Missing `status` in a dictionary keeps the existing Issue 251 diagnostic. | Focused GREEN included `test_reply_missing_action_status_does_not_update_local_state`. | Reclassifying `{}` as the payload-type branch or dropping `field=status` rejects this claim. |
| Present non-string `status` keeps the existing Issue 720 diagnostic. | Focused GREEN included `test_reply_malformed_action_status_type_preserves_cache_and_counts`. | Reclassifying `{"status": ["not-ok"]}` as a payload-type error rejects this claim. |
| Explicit non-ok string statuses still use `WikidotStatusCodeException`. | Focused GREEN included `test_reply_explicit_non_ok_action_status_preserves_cache_and_counts`. | Reclassifying non-ok strings as malformed response shape rejects this claim. |
| Failed reply payloads do not mutate local state. | The new regression asserts one AMC request, one JSON decode, preserved `_posts`, preserved thread `post_count`, preserved category `posts_count`, and preserved cached category threads. | Clearing cached posts, incrementing counts, or invalidating category threads before confirmed success rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3910 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `678a8c1 fix(forum_thread): validate reply response payload`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_malformed_action_response_type_preserves_cache_and_counts -q` failed before the fix with raw `TypeError: list indices must be integers or slices, not str`.
- GREEN focused: the same new regression passed after the payload guard.
- Reply response coverage: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_success tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_success_updates_category_post_count_and_invalidates_threads tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_rejects_malformed_retained_thread_ids_before_login tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_rejects_negative_retained_thread_id_before_login tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_missing_action_status_does_not_update_local_state tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_malformed_action_status_type_preserves_cache_and_counts tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_malformed_action_response_type_preserves_cache_and_counts tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_explicit_non_ok_action_status_preserves_cache_and_counts -q` passed 14 tests.
- Forum thread module coverage: `uv run pytest tests/unit/test_forum_thread.py -q` passed 238 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3910 tests.
- `uv run ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` left both files unchanged.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `ForumThread.reply(...)` with `response.json()` returning `["not-ok"]` raises `NoElementException` matching `Forum thread action response is malformed for site: test-site, thread: 3001 (event=savePost, expected=dict, actual=list)`.
- `{}` still raises the existing missing-status message with `field=status`.
- `{"status": ["not-ok"]}` still raises the existing malformed status-type message with `expected=str, actual=list`.
- Explicit non-ok string statuses still raise `WikidotStatusCodeException`.
- The malformed payload branch decodes the response JSON once, preserves cached posts, preserves cached category threads, does not increment thread or category post counts, and does not include raw response data.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: A caller may have relied on raw `TypeError` from malformed synthetic responses. Mitigation: the public module expects a status-bearing result object, and repo validation style consistently routes malformed generated response shape through contextual `NoElementException`.
- Risk: This could be confused with reply missing-status handling. Mitigation: dictionary payloads still follow the existing missing-status guard and retain `field=status`.
- Risk: This could hide raw payload details useful for debugging. Mitigation: the diagnostic includes site, thread ID, event, expected type, and actual type while avoiding raw response data that could contain private forum content or account material.

## Dependencies

- Forum thread reply responses remain expected to decode as JSON objects with string `status`.
- `WikidotStatusCodeException` remains responsible for explicit non-ok string statuses.
- `NoElementException` remains the parser/data-shape exception for malformed module response payloads.

## Open Questions

None for this local slice. Similar non-mapping action-payload guards may be useful on forum post edit, site-invitation, site-application, and site-member mutation helpers, but each surface should receive its own duplicate check against the existing action-status and status-type issue series before implementation.

## Rationale for Upstream Suitability

The patch is small, local, and consistent with existing wikidot.py response-shape diagnostics. It improves failure classification for malformed forum reply responses without changing successful replies, cache/count update timing, or existing status-code behavior.

## Local Evidence

- Local rollout-backed forum drafts established forum replies, post-source/edit-form handling, forum mutation diagnostics, generated discussion workflows, moderation tooling, cached post lists, category counters, and fixtures as practical consumers of forum thread behavior.
- Existing local drafts covered missing reply action status context, present non-string reply action status values, raw connector envelope status typing, reply cache/category count synchronization, forum write text inputs, parent-post IDs, retained thread IDs, and retained site/client state. They did not cover a decoded `savePost` response payload that is not a mapping before status lookup.
- This slice only validates forum thread reply payload shape. It does not change request construction, login checks, retry behavior, forum category creation, forum post editing, site administration handling, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw forum content, raw response bodies, private site data, and private source text out of upstream discussion.
