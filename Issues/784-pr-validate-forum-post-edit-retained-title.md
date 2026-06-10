# PR Draft: Validate Forum Post Edit Retained Title

## Summary

`ForumPost.edit(...)` validates caller-provided `source` and explicit `title` values, revalidates retained edit parent thread/site/ID state, fetches the generated edit form, reads `currentRevisionId`, confirms the `saveEditPost` action status, and invalidates local caches only after a successful save. One omitted-title path still trusted `self.title` after construction: when callers invoked `edit(source="...")` with `title=None`, the save payload used the retained post title directly. A valid `ForumPost` whose `title` was later mutated, fixture-loaded, or rehydrated as a non-string could therefore authenticate, fetch the edit form, send `saveEditPost`, update local `_source`, and clear caches before any deterministic title validation occurred.

This change validates the retained edit title when `title` is omitted. Malformed retained titles now raise `ValueError("title must be a string")` before login checks, edit-form fetches, save requests, local source updates, revision-cache invalidation, or thread post-cache invalidation. Valid omitted-title edits still use the current retained title in the save payload, and explicit valid title edits still update `self.title` after a successful save.

## Outcome

Forum post editing can no longer use a malformed retained `ForumPost.title` as the hidden save title for omitted-title edits. The failure is local, deterministic, side-effect free, and uses the same text-field diagnostic as explicit `title=` validation.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum editing, moderation fixtures, discussion migration tooling, generated ledgers, local tests, or serialized and rehydrated `ForumPost` records before calling `ForumPost.edit(source=...)`.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post editing as a practical workflow surface. Existing drafts [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [185-pr-forum-post-edit-revision-site-context.md](185-pr-forum-post-edit-revision-site-context.md), [205-pr-forum-post-edit-revision-value-context.md](205-pr-forum-post-edit-revision-value-context.md), [210-pr-forum-post-edit-form-response-body-context.md](210-pr-forum-post-edit-form-response-body-context.md), [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md), [263-pr-forum-post-edit-revision-cache-invalidation.md](263-pr-forum-post-edit-revision-cache-invalidation.md), [269-pr-forum-post-edit-thread-cache-invalidation.md](269-pr-forum-post-edit-thread-cache-invalidation.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md), [578-pr-validate-forum-post-edit-thread.md](578-pr-validate-forum-post-edit-thread.md), [579-pr-validate-forum-post-edit-thread-site.md](579-pr-validate-forum-post-edit-thread-site.md), and [683-pr-validate-forum-post-edit-retained-id-state.md](683-pr-validate-forum-post-edit-retained-id-state.md) establish edit-form reliability, revision diagnostics, save action-status validation, cache invalidation, explicit edit text-input validation, constructor title validation, and edit-time retained parent/ID validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issue 354 validates caller-provided forum write text inputs, including explicit `ForumPost.edit(title=3)`, before login or form fetch. It intentionally preserved `ForumPost.edit(title=None)` behavior but did not validate the retained `self.title` reused by that omitted-title path. Issue 460 validates `ForumPost(title=...)` at construction, but it cannot cover post-construction mutation, fixture mutation, or rehydrated state before a later edit call. Issues 578, 579, and 683 validate edit-time retained parent thread, parent site, and retained IDs, not the retained title that becomes the save payload when `title` is omitted.

The focused RED test demonstrated the gap: `mock_forum_post_no_http.title = 3` followed by `mock_forum_post_no_http.edit(source="Updated source")` completed without raising before the fix, reached the mocked successful edit path, and failed the regression with `DID NOT RAISE`.

## Related Issue / Non-Duplicate Analysis

Builds directly on [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md), [578-pr-validate-forum-post-edit-thread.md](578-pr-validate-forum-post-edit-thread.md), [579-pr-validate-forum-post-edit-thread-site.md](579-pr-validate-forum-post-edit-thread-site.md), and [683-pr-validate-forum-post-edit-retained-id-state.md](683-pr-validate-forum-post-edit-retained-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `self.title` with `validate_text_field("title", self.title)` when `ForumPost.edit(...)` is called without an explicit `title`.
- Reuse the validated `save_title` in the `saveEditPost` payload.
- Preserve explicit `title=` validation and post-save `self.title` updates.
- Preserve valid omitted-title edit behavior by sending the current retained title when it is a string.
- Add a focused regression for a mutated retained title that previously reached login/form-fetch/save behavior.

## Type Of Change

- State validation
- Forum post edit-path hardening
- Retained text-field integrity
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPost.edit(source=...)` with omitted `title` must reject a retained `post.title` that is not a string with `ValueError("title must be a string")`. |
| R2 | The retained-title rejection must happen before `login_check()`, edit-form fetches, `saveEditPost`, local source mutation, revision-cache invalidation, or thread post-cache invalidation. |
| R3 | Explicit malformed `title=` and malformed `source=` validation from Issue 354 must remain unchanged. |
| R4 | Valid omitted-title edits, valid explicit-title edits, edit-form retry/scoping, revision-ID diagnostics, save action-status diagnostics, local cache invalidation, and adjacent forum workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum content, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, edit coverage, adjacent forum coverage, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Omitted-title edit rejects malformed retained title state. | `TestForumPostEdit.test_edit_rejects_malformed_retained_title_before_login_or_form_fetch` failed RED with `DID NOT RAISE`, then passed GREEN after retained-title validation was added. | Accepting an integer or other non-string retained title, coercing it, or using it as the save title rejects this local completion claim. | `ForumPost.edit(...)` omitted-title preflight | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Validation is side-effect free. | The regression asserts `login_check`, `amc_request_with_retry`, and `amc_request` are not called, and that `_source`, `_revisions`, and `thread._posts` remain unchanged. | Authenticating, fetching the edit form, sending `saveEditPost`, updating `_source`, clearing `_revisions`, clearing `thread._posts`, or changing the corrupted retained title during failure rejects this local completion claim. | Forum post edit preflight | focused test |
| R3 | Existing explicit edit text-input validation remains stable. | `TestForumPostEdit` passed 38 tests, including `test_edit_rejects_non_string_text_inputs_before_login_or_form_fetch`. | Regressing explicit `source` or explicit `title` diagnostics, or checking omitted retained title before explicit bad inputs, rejects this local completion claim. | Public edit text inputs | `tests/unit/test_forum_post.py` |
| R4 | Valid edit behavior and adjacent forum workflows remain green. | `TestForumPostEdit` passed 38 tests; adjacent forum category/thread/post/revision coverage passed 912 tests; full unit passed 3806 tests. | Regressing valid omitted-title saves, explicit-title saves, edit-form diagnostics, action-status diagnostics, source reads, post-list acquisition, revision acquisition, forum category/thread/revision behavior, or full unit coverage rejects this local completion claim. | Forum post edit and adjacent workflows | `tests/unit` |
| R5 | The local proof stays unit-level and private-data-free. | All regressions use synthetic local fixtures and mocks. | Using live Wikidot, credentials, cookies, auth JSON, raw private forum content, raw rollout paths, private site names, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `8d92c91 fix(forum_post): validate retained edit title`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_rejects_malformed_retained_title_before_login_or_form_fetch -q --tb=short` failed before the fix with `DID NOT RAISE`.
- GREEN focused: the same focused command passed 1 test after the fix.
- Edit coverage: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit -q` passed 38 tests.
- Adjacent forum coverage: `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py -q` passed 912 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3806 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `ForumPost.edit(source=...)` raises `ValueError("title must be a string")` when the edited post's retained `title` is an integer or other non-string and the caller omits explicit `title`.
- The retained-title failure occurs before login checks, edit-form fetches, `saveEditPost`, local source mutation, revision-cache invalidation, or thread post-cache invalidation.
- The retained-title failure does not coerce or rewrite the corrupted retained `title`.
- Explicit invalid `source` and explicit invalid `title` inputs still raise the same `ValueError` diagnostics before request work.
- Valid omitted-title edits still send the current retained string title in `saveEditPost`.
- Valid explicit-title edits still update `self.title` after a confirmed successful save.
- Existing edit-form retry/scoping, revision-ID diagnostics, response-body diagnostics, save action-status validation, local cache invalidation, source reads, post-list acquisition, revision acquisition, and adjacent forum workflows remain green.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Callers with mutated or rehydrated malformed `ForumPost.title` values now fail before edit work. Mitigation: constructor validation already requires strings, and corrupted retained state should be fixed before request construction rather than coerced into a forum save payload.
- Risk: The retained title is now validated earlier than the edit-form fetch. Mitigation: this is the same local preflight model used for explicit text inputs and retained edit IDs, and the regression protects against login, fetch, save, and cache side effects.
- Risk: A valid omitted-title edit could accidentally stop sending the current title. Mitigation: the implementation uses a local `save_title` value that is either the explicit validated title or the retained validated title, and existing successful edit tests remain green.

## Dependencies

- Existing `validate_text_field(...)` remains the canonical text-field validator.
- Existing `ForumPost(title=...)` constructor validation remains unchanged.
- Existing `ForumPost.edit(...)` edit-form fetch, revision-ID parsing, save action-status validation, source/title local updates, revision-cache invalidation, and thread post-cache invalidation behavior remains unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, cache ownership boundaries, result ergonomics, or complexity candidates outside this now-covered omitted-title edit path.

## Upstream-Safe Motivation

`ForumPost.edit(source=...)` with omitted `title` still sends a title in the `saveEditPost` payload, using the post's current retained title. That retained title should satisfy the same string contract as explicit `title=` before any authentication, generated form read, save mutation, or cache mutation can happen. Validating it locally keeps corrupted fixture or rehydrated state from becoming a remote edit payload while preserving valid omitted-title and explicit-title behavior.

## Local Evidence

- Local rollout-backed work established forum post editing as a practical workflow through retry-aware edit-form reads, generated form parsing, action-status validation, cache invalidation, write input validation, constructor text-field validation, and retained edit parent/ID hardening.
- Existing local drafts covered explicit `ForumPost.edit(title=...)` input validation, constructor-time `ForumPost.title` validation, retained edit parent thread/site validation, retained edit ID validation, edit-form response diagnostics, revision-ID diagnostics, and save action-status validation; they did not cover post-construction malformed retained `self.title` state used by the omitted-title save path.
- The focused RED failure showed malformed retained title state could reach a mocked successful edit and update local state instead of failing before request work.
- This slice only validates the retained title used by omitted-title `ForumPost.edit(...)` calls. It does not change parser field extraction, title normalization, source text contents, edit-form selectors, revision-ID parsing, action-status parsing, source acquisition internals, post-list acquisition internals, forum post revision acquisition internals, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, rendered forum HTML, private thread text, private forum post content, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates type only. It does not reject empty titles, trim titles, coerce non-string values, reassign `self.title` when omitted, or change the local title update rule for explicit successful title edits.
