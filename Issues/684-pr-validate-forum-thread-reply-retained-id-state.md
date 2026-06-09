# PR Draft: Validate Forum Thread Reply Retained ID State

## Summary

`ForumThread.reply(...)` already validates public reply text inputs, optional `parent_post_id`, retained `self.site`, action status, direct `ForumThread(id=...)` construction, and direct thread lookup IDs. The reply path still used retained `self.id` directly when constructing Wikidot's `savePost` `threadId` payload. If a valid thread object is later mutated, rehydrated, or fixture-loaded with corrupted retained ID state, `None`, booleans, strings, floats, lists, or negative integers can reach login, request construction, mocked action-status handling, or local reply cache/count mutation paths instead of producing the same deterministic thread-ID diagnostics used elsewhere.

This change validates the retained reply thread ID before login or `savePost` work. Malformed retained thread IDs now raise `ValueError("thread_id must be an integer")`, negative retained thread IDs raise `ValueError("thread_id must be non-negative")`, valid zero retained thread IDs remain accepted, and successful replies still use the existing `savePost` action-status validation, thread post-cache invalidation, post-count increment, and category cache/count synchronization behavior.

## Outcome

Forum-thread replies no longer authenticate, build `savePost` payloads, diagnose action-status failures, or update local reply state through corrupted retained thread IDs. Valid direct replies, parent replies, zero-ID compatibility, text-input validation, parent-post ID validation, retained-site validation, action-status diagnostics, thread/category cache synchronization, and adjacent forum/site workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum replies, generated discussion workflows, migration scripts, moderation tooling, local fixtures, or serialized and rehydrated `ForumThread` records before calling `ForumThread.reply(...)`.

## Current Evidence

Forum reply drafts [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [369-pr-validate-forum-thread-reply-parent-id.md](369-pr-validate-forum-thread-reply-parent-id.md), [574-pr-validate-forum-thread-reply-site.md](574-pr-validate-forum-thread-reply-site.md), and [650-pr-validate-non-negative-forum-thread-reply-parent-ids.md](650-pr-validate-non-negative-forum-thread-reply-parent-ids.md) establish `ForumThread.reply(...)`, reply payloads, action-status validation, local cache synchronization, text input validation, parent-post ID validation, retained-site validation, and parent-post ID range validation as practical mutation-boundary surfaces.

Related retained-ID drafts [642-pr-validate-non-negative-forum-thread-ids.md](642-pr-validate-non-negative-forum-thread-ids.md), [673-pr-validate-forum-thread-collection-retained-id-state.md](673-pr-validate-forum-thread-collection-retained-id-state.md), [680-pr-validate-forum-post-list-acquisition-retained-thread-id-state.md](680-pr-validate-forum-post-list-acquisition-retained-thread-id-state.md), [682-pr-validate-forum-post-source-acquisition-retained-id-state.md](682-pr-validate-forum-post-source-acquisition-retained-id-state.md), and [683-pr-validate-forum-post-edit-retained-id-state.md](683-pr-validate-forum-post-edit-retained-id-state.md) establish direct thread-ID validation, collection lookup retained-ID validation, post-list retained thread-ID validation, source-acquisition retained-ID validation, and edit retained-ID validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issues 354, 369, and 650 validate caller-supplied reply inputs before `savePost`, but they do not validate the retained `ForumThread.id` already stored on the receiver. Issue 574 validates retained `self.site`, not retained integer identity. Issue 251 validates malformed `savePost` responses after a request path has started. Issue 642 validates direct construction and lookup IDs, but it cannot cover a valid thread whose `id` is corrupted after construction and then replied to. Issue 673 validates retained IDs during `ForumThreadCollection.find(...)` lookup only. Issues 680, 682, and 683 validate retained thread IDs in post-list acquisition, source acquisition, and post editing, not the forum-thread reply `savePost.threadId` payload.

## Related Issue / Non-Duplicate Analysis

Builds directly on [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [369-pr-validate-forum-thread-reply-parent-id.md](369-pr-validate-forum-thread-reply-parent-id.md), [574-pr-validate-forum-thread-reply-site.md](574-pr-validate-forum-thread-reply-site.md), [650-pr-validate-non-negative-forum-thread-reply-parent-ids.md](650-pr-validate-non-negative-forum-thread-reply-parent-ids.md), [642-pr-validate-non-negative-forum-thread-ids.md](642-pr-validate-non-negative-forum-thread-ids.md), [673-pr-validate-forum-thread-collection-retained-id-state.md](673-pr-validate-forum-thread-collection-retained-id-state.md), [680-pr-validate-forum-post-list-acquisition-retained-thread-id-state.md](680-pr-validate-forum-post-list-acquisition-retained-thread-id-state.md), [682-pr-validate-forum-post-source-acquisition-retained-id-state.md](682-pr-validate-forum-post-source-acquisition-retained-id-state.md), and [683-pr-validate-forum-post-edit-retained-id-state.md](683-pr-validate-forum-post-edit-retained-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `self.id` inside `ForumThread.reply(...)` after text input, parent-post ID, and retained-site preflight, but before `login_check()` or `savePost` request construction.
- Reuse the validated integer thread ID for the `savePost` `"threadId"` payload.
- Reject malformed retained thread IDs such as `None`, `True`, `False`, `"3001"`, `3001.0`, and `[]` with `ValueError("thread_id must be an integer")`.
- Reject negative retained thread IDs with `ValueError("thread_id must be non-negative")`.
- Preserve valid retained thread ID `0` and serialize it as `"threadId": "0"`.
- Preserve valid replies, parent replies, reply input validation precedence, retained-site validation, action-status diagnostics, post-count/cache updates, category cache synchronization, and adjacent forum/site workflows.

## Type Of Change

- State validation
- Forum reply mutation-boundary hardening
- Retained identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThread.reply(...)` must reject retained `thread.id` values such as `None`, `True`, `False`, `"3001"`, `3001.0`, and `[]` with `ValueError("thread_id must be an integer")` before login, `savePost` request construction, action-status parsing, or local mutation. |
| R2 | The same path must reject retained `thread.id=-1` and `thread.id=-100` with `ValueError("thread_id must be non-negative")` before reply work uses them. |
| R3 | Valid retained thread ID `0` must remain accepted and must produce a `savePost` payload with `"threadId": "0"`. |
| R4 | Valid replies, public text validation, parent-post ID validation, retained-site validation, action-status diagnostics, thread post-count/cache updates, category post-count/cache updates, and adjacent forum/site workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, rendered forum HTML, or private forum content. |
| R6 | Focused RED/GREEN, reply tests, forum-thread tests, adjacent forum/site workflow tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained thread IDs fail before login, request construction, action-status parsing, or local mutation. | `test_reply_rejects_malformed_retained_thread_ids_before_login` failed RED for six retained values, then passed GREEN after retained thread-ID validation was added. | Calling `login_check()`, sending `savePost`, accepting booleans/floats, coercing values, surfacing action-status diagnostics, incrementing `post_count`, clearing `_posts`, or mutating category counts/caches rejects this local completion claim. | `ForumThread.reply(...)` retained thread ID | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Negative retained thread IDs fail with the existing non-negative diagnostic before reply work uses them. | `test_reply_rejects_negative_retained_thread_id_before_login` failed RED for `-1` and `-100`, then passed GREEN. | Treating negative retained thread IDs as request IDs, valid cache owners, valid diagnostic context, or ordinary action-status failures rejects this local completion claim. | `ForumThread.reply(...)` retained thread ID | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R3 | Valid zero retained thread IDs remain accepted for reply payload construction. | `test_reply_accepts_zero_retained_thread_id` passed RED and GREEN, asserting the `savePost` payload uses `"threadId": "0"`. | Rejecting zero, converting it to an empty value, or changing valid zero-ID reply request payloads rejects this local completion claim. | `ForumThread.reply(...)` request payload | `tests/unit/test_forum_thread.py` |
| R4 | Existing reply behavior and adjacent forum/site workflows remain green. | `TestForumThreadReply` passed 25 tests, `tests/unit/test_forum_thread.py` passed 212 tests, adjacent forum/site coverage passed 1170 tests, and full unit coverage passed 3376 tests. | Regressing text validation, parent-post ID validation, retained-site validation, parent replies, action-status diagnostics, thread/category count updates, cache invalidation, forum category/post/revision behavior, site behavior, or any unit test rejects this local completion claim. | Forum reply and adjacent workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft excludes private content. | Using credentials, cookies, auth JSON, raw rollout paths, private forum content, rendered forum HTML, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, reply/forum-thread/adjacent tests, full unit, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `abe2b11 fix(forum_thread): validate reply retained id`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadReply -k retained_thread_id -q` selected 9 retained reply tests; 8 malformed/negative retained-ID cases failed before the fix while 1 zero-ID compatibility guard passed.
- GREEN: the same focused command passed 9 tests after retained reply thread-ID validation was added.
- `uv run ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadReply -q` passed 25 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 212 tests.
- `uv run pytest tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_site.py -q` passed 1170 tests.
- `uv run pytest tests/unit -q` passed 3376 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `ForumThread.reply(...)` raises `ValueError("thread_id must be an integer")` when the receiver thread's retained `thread.id` is `None`, `True`, `False`, `"3001"`, `3001.0`, or `[]`.
- The same method raises `ValueError("thread_id must be non-negative")` when the receiver thread's retained `thread.id` is `-1` or `-100`.
- Malformed and negative retained thread IDs fail before `login_check()`, `savePost`, action-status parsing, thread `post_count` updates, thread `_posts` invalidation, category `posts_count` updates, or category `_threads` invalidation.
- Valid retained thread ID `0` still produces a `savePost` request payload with `"threadId": "0"`.
- Existing public reply text validation, `parent_post_id` validation, retained-site validation, valid direct replies, valid parent replies, action-status diagnostics, local post-count/cache updates, category cache synchronization, and adjacent forum/site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, rendered forum HTML, or private forum content.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rehydrated threads with malformed retained IDs now fail before reply work. Mitigation: corrupted retained identity state should be corrected before mutation request construction; deterministic diagnostics are preferable to invalid `threadId` payloads or misleading action-status failures.
- Risk: Valid zero IDs could be accidentally rejected if validation were changed to positive-only. Mitigation: the focused zero-ID guard asserts `threadId == "0"`.
- Risk: Validation precedence could regress existing public input diagnostics. Mitigation: the retained-ID validation runs after existing text, parent-post ID, and retained-site preflight, and the existing reply test class remains green.

## Dependencies

- Existing `_validate_thread_id(...)` remains the canonical forum thread ID validator.
- Existing `ForumThread(id=...)` constructor validation and direct thread lookup validation remain unchanged.
- Existing `ForumThread.reply(...)` text input validation, optional parent-post ID validation, retained-site validation, action-status validation, local cache invalidation, and category synchronization remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, or complexity candidates outside this now-covered forum-thread reply retained-ID boundary.

## Upstream-Safe Motivation

Forum-thread replies use the receiver thread's retained ID to route Wikidot's `savePost` mutation. That retained ID should satisfy the same integer/non-negative contract as directly constructed and directly acquired threads before it leaves local state. Validating stored identity prevents corrupted fixtures, generated records, or rehydrated objects from becoming invalid mutation payloads while preserving valid zero IDs, direct replies, parent replies, action confirmation, and local cache synchronization.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established forum replies as a practical workflow through action-status validation, category cache synchronization, write input validation, parent-post ID validation, retained-site hardening, and retained-ID hardening in adjacent post-list/source/edit paths.
- Existing local drafts covered reply text inputs, reply action-status responses, reply category synchronization, malformed and negative `parent_post_id`, retained reply site state, direct constructor identity validation, collection lookup retained IDs, post-list acquisition retained thread IDs, source-acquisition retained IDs, and post edit retained IDs; they did not validate retained stored `ForumThread.id` before reply `savePost` payload construction.
- The focused RED failure showed malformed and negative retained thread IDs reached mocked `savePost` handling and action-status diagnostics instead of deterministic thread-ID diagnostics. The GREEN regressions cover malformed rejection, negative rejection, zero-ID compatibility, reply behavior, adjacent forum/site workflows, and full unit compatibility.
- This slice only validates retained stored IDs at the forum-thread reply boundary. It does not change parser field extraction, forum post-list acquisition internals, forum post source acquisition internals, forum post edit internals, forum post revision internals, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, rendered forum HTML, private thread text, private forum post content, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates retained `self.id` once at reply entry and then reuses the validated integer for the `savePost` payload. The validation happens before login so corrupted retained identity cannot influence authentication, request routing, response diagnostics, or local cache mutation. This keeps the change local to the reply boundary while preserving the existing public API surface.
