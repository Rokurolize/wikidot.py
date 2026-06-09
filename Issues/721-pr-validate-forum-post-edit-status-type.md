# PR Draft: Validate Forum Post Edit Status Type

## Summary

`ForumPost.edit(...)` fetches Wikidot's edit form, extracts `currentRevisionId`, sends the `saveEditPost` action, validates action `status`, then updates the local post title/source and clears revision/thread caches. Issue [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md) covered missing action `status` and explicit non-ok string statuses, but present non-string values such as `{"status": ["not-ok"]}` were still routed into `WikidotStatusCodeException` as if they were real Wikidot status codes. This change rejects malformed generated action data before treating the edit result as a status-code failure or a successful mutation.

## Outcome

Forum post edits now distinguish malformed action-response shape from real Wikidot status-code failures, preserving existing string-status behavior while surfacing type-corrupt generated responses with site, post, event, field, and type context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum post edits, migration scripts, moderation tooling, generated discussion workflows, cached forum ledgers, or local fixtures where a malformed edit action response must not be mistaken for a confirmed successful mutation.

## Current Evidence

Local rollout-backed drafts already identify forum post editing as a practical shared workflow. Existing drafts [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [185-pr-forum-post-edit-revision-site-context.md](185-pr-forum-post-edit-revision-site-context.md), [205-pr-forum-post-edit-revision-value-context.md](205-pr-forum-post-edit-revision-value-context.md), [210-pr-forum-post-edit-form-response-body-context.md](210-pr-forum-post-edit-form-response-body-context.md), and [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md) cover retry boundaries, generated edit-form parsing, revision diagnostics, malformed form-body diagnostics, missing save-action status, and explicit non-ok save-action strings.

Adjacent action-status type drafts [714-pr-validate-page-save-status-type.md](714-pr-validate-page-save-status-type.md), [715-pr-validate-private-message-send-status-type.md](715-pr-validate-private-message-send-status-type.md), [716-pr-validate-site-application-action-status-type.md](716-pr-validate-site-application-action-status-type.md), [717-pr-validate-site-member-action-status-type.md](717-pr-validate-site-member-action-status-type.md), [718-pr-validate-site-invite-action-status-type.md](718-pr-validate-site-invite-action-status-type.md), [719-pr-validate-forum-category-create-thread-status-type.md](719-pr-validate-forum-category-create-thread-status-type.md), and [720-pr-validate-forum-thread-reply-status-type.md](720-pr-validate-forum-thread-reply-status-type.md) establish the same module-level response-shape pattern on other mutation actions. Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) is not a duplicate: it covers raw Ajax Module Connector response envelope status typing before module-level action payload handling. This slice validates the `saveEditPost` action response consumed by `ForumPost.edit(...)`. No upstream issue was filed from this local workspace.

## Changes

- Add a type guard in the forum-post edit action status extractor.
- Raise `NoElementException` for a present non-string `status` with site, post ID, event, field, expected type, and actual type context.
- Preserve Issue 250 missing-status diagnostics.
- Preserve explicit non-ok string handling through `WikidotStatusCodeException`.
- Add a focused regression proving malformed status types are decoded once and preserve title, source, cached revisions, and cached thread posts.
- Add a compatibility regression proving explicit non-ok string statuses remain status-code failures and preserve the same local state.

## Type Of Change

- Response-shape validation
- Forum post edit action hardening
- Generated response data diagnostics
- Cache/state consistency preservation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPost.edit(...)` must reject a non-string `saveEditPost` response `status` with `NoElementException` containing site, post ID, event, `field=status`, `expected=str`, and the actual type. |
| R2 | A missing `status` field must keep the existing Issue 250 missing-status diagnostic. |
| R3 | Explicit non-ok string statuses must still raise `WikidotStatusCodeException`. |
| R4 | Malformed and explicit non-ok action statuses must not update title/source, clear cached revisions, or clear cached thread posts. |
| R5 | Valid successful edits must remain unchanged. |
| R6 | Adjacent forum workflows and repository quality gates must remain green. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `{"status": ["not-ok"]}` fails with malformed edit action status context. | `test_edit_malformed_action_status_type_preserves_local_state_and_caches` failed RED with `WikidotStatusCodeException`, then passed GREEN after status typing was added. | Treating a list, dict, number, or object as a Wikidot status code rejects this local completion claim. | Forum post edit action response shape | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | `{}` still raises the Issue 250 missing-status message with site, post, event, and field context. | `test_edit_missing_save_action_status_does_not_update_local_state` passed unchanged. | Changing missing-status exception type, dropping context, or masking it behind type/status-code handling rejects this local completion claim. | Forum post missing action status | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | `{"status": "not_ok"}` keeps the status-code path. | `test_edit_explicit_non_ok_action_status_preserves_local_state_and_caches` passed and asserts `status_code == "not_ok"`. | Reclassifying non-ok strings as malformed response shape rejects this local completion claim. | Forum post status-code handling | `tests/unit/test_forum_post.py` |
| R4 | Malformed and explicit non-ok statuses preserve local post state and caches. | The new malformed-status and non-ok-string regressions assert one AMC call, one JSON decode, unchanged `title`, unchanged `_source`, preserved `_revisions`, and preserved thread `_posts`. | Updating title/source, clearing revisions, clearing thread posts, or decoding repeatedly rejects this local completion claim. | Forum post edit mutation/cache boundary | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R5 | Successful valid edit behavior remains stable. | `test_edit_success`, `test_edit_success_invalidates_cached_revisions`, `test_edit_success_invalidates_thread_posts_cache`, and `test_edit_with_new_title` passed in focused GREEN; `TestForumPostEdit` passed 36 tests. | Regressing login, edit-form fetches, revision parsing, save payload shape, successful local updates, or cache invalidation after confirmed edits rejects this local completion claim. | Edit workflow | `tests/unit/test_forum_post.py` |
| R6 | Adjacent forum behavior and repo quality gates remain green. | Forum-post passed 292 tests, adjacent forum suites passed 884 tests, full unit passed 3590 tests, ruff, mypy, pyright, and `git diff --check` passed. | Any test, lint, format, type, or whitespace failure rejects this local completion claim. | Repository quality gates | `tests/unit`, `src`, `tests` |
| R7 | No live site state or private material is needed to prove the behavior. | The regressions use synthetic unit-level response bodies and mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `c8ed69f fix(forum_post): validate edit status type`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_malformed_action_status_type_preserves_local_state_and_caches -q` failed before the fix with `WikidotStatusCodeException` instead of the expected malformed-shape `NoElementException`.
- GREEN focused: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_success tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_success_invalidates_cached_revisions tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_success_invalidates_thread_posts_cache tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_save_action_status_does_not_update_local_state tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_malformed_action_status_type_preserves_local_state_and_caches tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_explicit_non_ok_action_status_preserves_local_state_and_caches tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_with_new_title -q` passed 7 tests.
- `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit -q` passed 36 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 292 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 884 tests.
- `uv run pytest tests/unit -q` passed 3590 tests.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left both files unchanged.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `{"status": ["not-ok"]}` raises `NoElementException` with site, post ID, event, `field=status`, `expected=str`, and `actual=list` context.
- `{}` still raises the existing missing-status message from Issue 250.
- `{"status": "not_ok"}` still raises `WikidotStatusCodeException`.
- Malformed and explicit non-ok statuses do not update the local post title/source.
- Malformed and explicit non-ok statuses do not clear cached revisions.
- Malformed and explicit non-ok statuses do not clear cached thread posts.
- Successful valid edits keep the existing login check, retry-aware edit-form fetch, `currentRevisionId` parsing, save request payload, local title/source update, revision-cache invalidation, thread post-cache invalidation, and method-chaining return.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A caller may have relied on a non-string `status` object being formatted into a `WikidotStatusCodeException`. Mitigation: Wikidot action statuses are strings, Issue 403 already validates raw AMC statuses as strings, and module-level action responses should reject malformed generated data before business handling.
- Risk: This could be confused with edit-form response validation. Mitigation: Issues 124, 185, 205, and 210 cover generated edit-form controls and body/revision fields; this slice only covers the returned `saveEditPost` action payload after the save request.
- Risk: This could be confused with missing or explicit non-ok action status handling. Mitigation: Issue 250 covers missing status and non-ok string status; this slice covers a present status with malformed type.
- Risk: This could be confused with raw AMC response typing. Mitigation: Issue 403 covers the raw connector envelope; this slice covers the forum-post `saveEditPost` action payload used by `ForumPost.edit(...)`.
- Risk: Tightening action response shape could hide legitimate non-ok Wikidot string statuses. Mitigation: non-ok strings are deliberately preserved on the existing `WikidotStatusCodeException` path.
- Risk: The error could become too generic for generated fixtures. Mitigation: the diagnostic names the site, post ID, event, field, expected type, and actual type.

## Dependencies

- Existing `ForumPost.edit(...)` remains responsible for edit-form fetches, revision extraction, save request construction, and local state updates after confirmed saves.
- Existing `WikidotStatusCodeException` handling remains responsible for explicit non-ok string statuses.
- Existing `NoElementException` remains the parser/data-shape exception for missing or malformed response fields.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, complexity candidates, or status type guards outside this now-covered forum-post edit action status type path.

## Upstream-Safe Motivation

`ForumPost.edit(...)` treats `saveEditPost` responses as status-bearing action payloads before mutating local post state and clearing caches. Rejecting malformed status types at that boundary keeps generated or adapted response data from masquerading as a real Wikidot status code and makes edit failures easier to diagnose without changing successful edits or valid string status handling.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established browser-free forum post edits, forum mutation diagnostics, generated edit-form controls, cached revision lists, and cached thread post lists as practical consumers of `ForumPost.edit(...)`.
- Existing forum-post and raw AMC drafts covered missing action status context, explicit non-ok action strings, edit-form response shape, revision parsing, retained ID state, and raw connector envelope status typing; they did not validate the module-level `saveEditPost` action status type.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private forum content, private site data, edit source text from real sites, and source text from real sites out of upstream discussion.
