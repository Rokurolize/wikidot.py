# PR Draft: Validate Forum Post Edit Retained IDs

## Summary

`ForumPost.edit(...)` already validates public edit text inputs, revalidates retained `self.thread`, revalidates retained `thread.site`, fetches the generated edit form through retry-aware AMC, scopes `currentRevisionId` to the direct edit form, validates the save action status before local mutation, and validates direct `ForumPost(id=...)` and `ForumThread(id=...)` construction. The edit path still used retained `thread.id` and `self.id` directly for edit-form request payload construction, save request payload construction, and edit-form diagnostics. If a valid post or thread is later mutated, rehydrated, or fixture-loaded with corrupted retained ID state, `None`, strings, floats, booleans, negative integers, or unhashable values can reach login/form-fetch/save internals instead of producing the same deterministic ID diagnostics used elsewhere.

This change validates retained edit IDs before login or edit-form work. Malformed retained post IDs now raise `ValueError("id must be an integer")`, negative retained post IDs raise `ValueError("id must be non-negative")`, malformed retained thread IDs raise `ValueError("thread_id must be an integer")`, negative retained thread IDs raise `ValueError("thread_id must be non-negative")`, valid zero post/thread IDs remain accepted, and successful edits still use the existing edit-form fetch, revision-ID parsing, save action-status validation, local source/title update, and cache invalidation behavior.

## Outcome

Forum post editing no longer authenticates, fetches generated edit forms, saves edits, diagnoses edit-form failures, or updates local caches through corrupted retained post or thread IDs. Valid edits, zero-ID compatibility, edit-form retry behavior, revision-ID diagnostics, save action-status diagnostics, local title/source mutation, revision-cache invalidation, thread post-cache invalidation, source reads, post-list reads, revision reads, and adjacent forum/site workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum editing, moderation fixtures, discussion migration tooling, local tests, or serialized and rehydrated `ForumPost` / `ForumThread` records before calling `ForumPost.edit(...)`.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post editing as a practical workflow surface. Existing drafts [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [185-pr-forum-post-edit-revision-site-context.md](185-pr-forum-post-edit-revision-site-context.md), [205-pr-forum-post-edit-revision-value-context.md](205-pr-forum-post-edit-revision-value-context.md), [210-pr-forum-post-edit-form-response-body-context.md](210-pr-forum-post-edit-form-response-body-context.md), [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md), [263-pr-forum-post-edit-revision-cache-invalidation.md](263-pr-forum-post-edit-revision-cache-invalidation.md), [269-pr-forum-post-edit-thread-cache-invalidation.md](269-pr-forum-post-edit-thread-cache-invalidation.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [578-pr-validate-forum-post-edit-thread.md](578-pr-validate-forum-post-edit-thread.md), [579-pr-validate-forum-post-edit-thread-site.md](579-pr-validate-forum-post-edit-thread-site.md), [641-pr-validate-non-negative-forum-post-ids.md](641-pr-validate-non-negative-forum-post-ids.md), [642-pr-validate-non-negative-forum-thread-ids.md](642-pr-validate-non-negative-forum-thread-ids.md), and [682-pr-validate-forum-post-source-acquisition-retained-id-state.md](682-pr-validate-forum-post-source-acquisition-retained-id-state.md) establish edit-form retry behavior, edit-form scoping, revision-ID diagnostics, response-body diagnostics, save action-status validation, edit cache invalidation, write text input validation, edit-time retained thread/site validation, direct post/thread ID validation, and source-acquisition retained-ID validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issues 044, 124, 185, 205, 210, 250, 263, 269, and 354 cover edit-form fetch/parsing, save action-status validation, cache invalidation, and public text inputs after a valid post/thread identity is assumed. Issues 578 and 579 validate retained edit parent objects and parent sites, not their retained integer IDs. Issues 641 and 642 validate direct constructor and lookup IDs, but they cannot cover valid objects whose IDs are corrupted after construction and then edited. Issue 682 validates retained IDs during source acquisition, not edit-form fetch or `saveEditPost` request construction.

## Related Issue / Non-Duplicate Analysis

Builds directly on [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [185-pr-forum-post-edit-revision-site-context.md](185-pr-forum-post-edit-revision-site-context.md), [205-pr-forum-post-edit-revision-value-context.md](205-pr-forum-post-edit-revision-value-context.md), [210-pr-forum-post-edit-form-response-body-context.md](210-pr-forum-post-edit-form-response-body-context.md), [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md), [263-pr-forum-post-edit-revision-cache-invalidation.md](263-pr-forum-post-edit-revision-cache-invalidation.md), [269-pr-forum-post-edit-thread-cache-invalidation.md](269-pr-forum-post-edit-thread-cache-invalidation.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [578-pr-validate-forum-post-edit-thread.md](578-pr-validate-forum-post-edit-thread.md), [579-pr-validate-forum-post-edit-thread-site.md](579-pr-validate-forum-post-edit-thread-site.md), [641-pr-validate-non-negative-forum-post-ids.md](641-pr-validate-non-negative-forum-post-ids.md), [642-pr-validate-non-negative-forum-thread-ids.md](642-pr-validate-non-negative-forum-thread-ids.md), and [682-pr-validate-forum-post-source-acquisition-retained-id-state.md](682-pr-validate-forum-post-source-acquisition-retained-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained parent `thread.id` before `ForumPost.edit(...)` can call `login_check()`, fetch the edit form, build `saveEditPost` payloads, update local title/source state, or invalidate caches.
- Validate retained `self.id` before `ForumPost.edit(...)` can call `login_check()`, fetch the edit form, build `saveEditPost` payloads, update local title/source state, or invalidate caches.
- Reuse the validated integer thread ID and post ID for edit-form request payloads and save request payloads.
- Reuse the validated post ID for edit-form revision diagnostics owned by `ForumPost.edit(...)`.
- Reject malformed retained post IDs such as `None`, `True`, `False`, `"5001"`, `5001.0`, and `[]` with `ValueError("id must be an integer")`.
- Reject negative retained post IDs with `ValueError("id must be non-negative")`.
- Reject malformed retained thread IDs such as `None`, `True`, `False`, `"3001"`, `3001.0`, and `[]` with `ValueError("thread_id must be an integer")`.
- Reject negative retained thread IDs with `ValueError("thread_id must be non-negative")`.
- Preserve valid zero retained post/thread IDs for edit-form and save request payloads.
- Preserve valid edit behavior, edit-form retry/scoping diagnostics, revision-ID diagnostics, save action-status diagnostics, source/title local updates, revision-cache invalidation, thread post-cache invalidation, and adjacent forum/site workflows.

## Type Of Change

- State validation
- Forum post edit-path hardening
- Retained identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPost.edit(...)` must reject retained `post.id` values such as `None`, `True`, `False`, `"5001"`, `5001.0`, and `[]` with `ValueError("id must be an integer")` before login, edit-form fetch, save request construction, or local mutation. |
| R2 | The same path must reject retained `post.id=-1` with `ValueError("id must be non-negative")` before edit work uses it. |
| R3 | The same path must reject retained parent `thread.id` values such as `None`, `True`, `False`, `"3001"`, `3001.0`, and `[]` with `ValueError("thread_id must be an integer")` before login, edit-form fetch, save request construction, or local mutation. |
| R4 | The same path must reject retained parent `thread.id=-1` with `ValueError("thread_id must be non-negative")` before edit work uses it. |
| R5 | Valid retained post ID `0` and retained thread ID `0` must remain accepted and must produce edit-form request payloads with `"postId": 0` and `"threadId": 0`, plus save payloads with `"postId": 0`. |
| R6 | Valid edits, text-input validation precedence, retained thread/site validation, edit-form retry behavior, revision-ID diagnostics, response-body diagnostics, save action-status validation, source/title local updates, revision-cache invalidation, thread post-cache invalidation, source reads, post-list reads, revision reads, and adjacent forum/site workflows must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, rendered forum HTML, or private forum content. |
| R8 | Focused RED/GREEN, edit tests, forum-post tests, adjacent forum/site workflow tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained post IDs fail before login, edit-form fetch, save payload construction, or local mutation. | `test_edit_rejects_malformed_retained_post_ids_before_login_or_form_fetch` failed RED for six retained values, then passed GREEN after retained post-ID validation was added. | Calling `login_check()`, fetching the edit form, sending `saveEditPost`, accepting booleans/floats, coercing values, raising edit-form parser diagnostics, updating local source/title, or clearing caches rejects this local completion claim. | `ForumPost.edit(...)` retained post ID | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Negative retained post IDs fail with the existing non-negative diagnostic before edit work uses them. | `test_edit_rejects_negative_retained_post_id_before_login_or_form_fetch` failed RED as an edit-form parser failure, then passed GREEN. | Treating a negative retained post ID as a request ID, diagnostic context, save payload ID, or valid local cache owner rejects this local completion claim. | `ForumPost.edit(...)` retained post ID | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Malformed retained parent thread IDs fail before login, edit-form fetch, save payload construction, or local mutation. | `test_edit_rejects_malformed_retained_thread_ids_before_login_or_form_fetch` failed RED for six retained values, then passed GREEN after retained thread-ID validation was added. | Calling `login_check()`, fetching the edit form, accepting booleans/floats, coercing values, sending malformed `threadId`, updating local source/title, or clearing caches rejects this local completion claim. | `ForumPost.edit(...)` retained parent thread ID | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R4 | Negative retained parent thread IDs fail with the existing non-negative diagnostic before edit work uses them. | `test_edit_rejects_negative_retained_thread_id_before_login_or_form_fetch` failed RED as an edit-form parser failure, then passed GREEN. | Treating a negative retained thread ID as a request ID, valid route, or valid cache owner rejects this local completion claim. | `ForumPost.edit(...)` retained parent thread ID | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R5 | Valid zero retained post/thread IDs remain accepted for edit-form and save requests. | `test_edit_accepts_zero_retained_post_and_thread_ids` passed RED and GREEN, asserting edit-form payload `"threadId": 0`, edit-form payload `"postId": 0`, and save payload `"postId": 0`. | Rejecting zero IDs or changing valid zero-ID edit request payloads rejects this local completion claim. | `ForumPost.edit(...)` request payloads | `tests/unit/test_forum_post.py` |
| R6 | Existing edit behavior and adjacent forum/site workflows remain green. | `TestForumPostEdit` passed 34 tests, `tests/unit/test_forum_post.py` passed 271 tests, adjacent forum/site coverage passed 1161 tests, and full unit coverage passed 3367 tests. | Regressing edit-form retry/scoping, revision-ID diagnostics, response-body diagnostics, action-status diagnostics, local cache invalidation, source reads, post-list acquisition, revision acquisition, forum category/thread/revision behavior, site behavior, or any unit test rejects this local completion claim. | Forum post edit and adjacent workflows | `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft excludes private content. | Using credentials, cookies, auth JSON, raw rollout paths, private forum content, rendered forum HTML, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, full edit/forum-post/adjacent tests, full unit, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `8a23374 fix(forum_post): validate edit retained ids`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit -k "retained_post or retained_thread" -q` selected 15 retained edit tests; 14 malformed/negative retained-ID cases failed before the fix while 1 zero-ID compatibility guard passed.
- GREEN: the same focused command passed 15 tests after retained edit ID validation was added.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit -q` passed 34 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 271 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py tests/unit/test_site.py -q` passed 1161 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run pytest tests/unit -q` passed 3367 tests.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `ForumPost.edit(...)` raises `ValueError("id must be an integer")` when the edited post's retained `post.id` is `None`, `True`, `False`, `"5001"`, `5001.0`, or `[]`.
- The same method raises `ValueError("id must be non-negative")` when the edited post's retained `post.id` is `-1`.
- The same method raises `ValueError("thread_id must be an integer")` when the parent thread's retained `thread.id` is `None`, `True`, `False`, `"3001"`, `3001.0`, or `[]`.
- The same method raises `ValueError("thread_id must be non-negative")` when the parent thread's retained `thread.id` is `-1`.
- Malformed and negative retained post/thread IDs fail before `login_check()`, edit-form fetches, `saveEditPost`, local title/source updates, revision-cache invalidation, or thread post-cache invalidation.
- Valid retained post ID `0` and retained thread ID `0` still produce edit-form request payloads with `"postId": 0` and `"threadId": 0`, and save request payloads with `"postId": 0`.
- Existing public edit text validation, retained thread/site validation, edit-form retry behavior, revision-ID diagnostics, response-body diagnostics, save action-status diagnostics, local title/source updates, revision-cache invalidation, thread post-cache invalidation, source reads, post-list acquisition, revision acquisition, and adjacent forum/site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, rendered forum HTML, or private forum content.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rehydrated posts or parent threads with malformed retained IDs now fail before edit work. Mitigation: corrupted retained identity state should be corrected before request construction; deterministic diagnostics are preferable to invalid `threadId`/`postId` payloads, bool/float equality surprises, parser failures, or cache mutation through malformed identity.
- Risk: Valid zero IDs could be accidentally rejected if validation were changed to positive-only. Mitigation: the focused zero-ID guard asserts edit-form and save payload compatibility for `0`.
- Risk: Diagnostics could expose private forum context. Mitigation: the new validation diagnostics include only field names and expected/range constraints, and existing edit-form diagnostics continue using compact site/post context without forum source text, rendered HTML, account details, or private thread content.

## Dependencies

- Existing `_validate_post_id(...)` remains the canonical forum post ID validator.
- Existing `_validate_forum_thread_id(...)` remains the canonical forum thread ID validator.
- Existing `ForumPost(id=...)` and `ForumThread(id=...)` constructor validation remains unchanged.
- Existing edit-form retry behavior, edit-form response-body diagnostics, revision-ID parsing, save action-status validation, local cache invalidation, source acquisition, post-list acquisition, and forum post-revision acquisition remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, or complexity candidates outside this now-covered forum post edit retained-ID boundary.

## Upstream-Safe Motivation

Forum post editing uses retained parent thread IDs and retained post IDs to route the pre-save edit-form request and save the edit. Those retained IDs should satisfy the same integer/non-negative contract as directly constructed posts and threads before they leave local state. Validating stored fields prevents corrupted local state from becoming invalid request IDs or misleading edit-form diagnostics, while preserving valid zero IDs, retry behavior, save confirmation, cache invalidation, and all forum/site behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established forum post editing as a practical workflow through retry-aware edit-form reads, generated form parsing, action-status validation, cache invalidation, write input validation, and retained parent-state hardening.
- Existing local drafts covered edit-form reliability, edit-form selectors, revision-ID diagnostics, response-body diagnostics, save action-status validation, edit cache invalidation, text input validation, retained thread/site validation, direct constructor identity validation, and source-acquisition retained-ID validation; they did not validate retained stored `ForumPost.id` or edit parent `ForumThread.id` before edit-form request or `saveEditPost` payload construction.
- The focused RED failure showed malformed retained IDs could reach mocked edit-form parsing and diagnostics instead of deterministic ID diagnostics. The GREEN regressions cover malformed rejection, negative rejection, zero-ID compatibility, edit behavior, adjacent forum/site workflows, and full unit compatibility.
- This slice only validates retained stored IDs at the forum post edit boundary. It does not change parser field extraction, source text contents, forum post source acquisition internals, post-list acquisition internals, forum post revision acquisition internals, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, rendered forum HTML, private thread text, private forum post content, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates retained IDs once at edit entry and then reuses those validated integers for edit-form and save request payloads. The validation happens before login so corrupted retained identity cannot influence authentication, request routing, parser diagnostics, or local cache mutation. This keeps the change local to the edit boundary while preserving the existing public API surface.
