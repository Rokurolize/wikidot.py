# PR Draft: Validate Forum Post Edit Response Payload

## Summary

`ForumPost.edit(...)` now validates that decoded `saveEditPost` action responses are dictionaries before reading `status`. Non-mapping payloads such as `["not-ok"]` raise contextual `NoElementException` with site, post ID, event, expected type, and actual type context instead of leaking a raw list `TypeError`.

The change is intentionally narrow: valid `{"status": "ok"}` edits, missing `status` diagnostics, non-string `status` diagnostics, explicit non-ok string status handling, title/source updates after confirmed saves, cached revision invalidation, and cached thread-post invalidation remain unchanged.

## Problem Statement

Forum post edits fetch the generated edit form, extract `currentRevisionId`, send the `saveEditPost` mutation, and then treat the decoded save response as a status-bearing action object before updating local title/source state and clearing caches. Earlier local slices covered missing edit action `status`, explicit non-ok string statuses, present non-string statuses such as `{"status": ["not-ok"]}`, edit-form response-body shape, edit-form revision parsing, write text inputs, retained post/thread/site state, retained title state, and retained site/client boundaries. One response-shape gap remained: if `response.json()` returned a non-dictionary payload, `_require_forum_post_action_status(...)` attempted `data["status"]` and leaked raw `TypeError`.

That failure gives callers neither the forum post edit action context nor a stable wikidot.py data-shape exception. Generated fixtures, response adapters, recorded traffic, or mocked responses should be classified before field access, and failed edit responses must not update title/source state or clear cached revisions/thread posts.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free forum post edits, generated edit-form controls, migration tooling, moderation utilities, cached forum ledgers, and local fixtures as practical automation surfaces: [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [185-pr-forum-post-edit-revision-site-context.md](185-pr-forum-post-edit-revision-site-context.md), [205-pr-forum-post-edit-revision-value-context.md](205-pr-forum-post-edit-revision-value-context.md), [210-pr-forum-post-edit-form-response-body-context.md](210-pr-forum-post-edit-form-response-body-context.md), [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md), [263-pr-forum-post-edit-revision-cache-invalidation.md](263-pr-forum-post-edit-revision-cache-invalidation.md), [269-pr-forum-post-edit-thread-cache-invalidation.md](269-pr-forum-post-edit-thread-cache-invalidation.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [649-pr-validate-non-negative-forum-post-edit-revision-ids.md](649-pr-validate-non-negative-forum-post-edit-revision-ids.md), [721-pr-validate-forum-post-edit-status-type.md](721-pr-validate-forum-post-edit-status-type.md), [765-pr-validate-forum-post-edit-revision-ascii-shape.md](765-pr-validate-forum-post-edit-revision-ascii-shape.md), [784-pr-validate-forum-post-edit-retained-title.md](784-pr-validate-forum-post-edit-retained-title.md), and [802-pr-validate-forum-action-site-clients.md](802-pr-validate-forum-action-site-clients.md).

This slice is not a duplicate of [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md). Issue 250 covered mapping responses with missing `status` and explicit non-ok string statuses.

This slice is not a duplicate of [721-pr-validate-forum-post-edit-status-type.md](721-pr-validate-forum-post-edit-status-type.md). Issue 721 covered a present non-string `status` field inside a mapping, such as `{"status": ["not-ok"]}`. This slice covers the decoded `saveEditPost` response payload not being a mapping before status lookup starts.

This slice is not a duplicate of [813-pr-validate-forum-thread-reply-response-payload.md](813-pr-validate-forum-thread-reply-response-payload.md) or [812-pr-validate-forum-category-create-response-payload.md](812-pr-validate-forum-category-create-response-payload.md). Those issues cover adjacent forum mutation actions. This slice covers `ForumPost.edit(...)`.

Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) covers the raw Ajax Module Connector response envelope before module-level action payload handling.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free forum post edits through `ForumPost.edit(...)`.
- Discussion migration and moderation tools that edit existing forum posts.
- Generated forum ledgers, fixtures, and recorded-response tests that decode action responses before returning them to wikidot.py module code.

## Proposed Fix

- Validate the decoded `saveEditPost` response payload as a dictionary in `_require_forum_post_action_status(...)`.
- Reject non-dictionary payloads with `NoElementException` before `status` lookup.
- Include only structural context and type names in the diagnostic, not raw response data.
- Preserve existing dictionary `status` validation and status-code handling.

## Implementation Notes

Implemented locally in commit `ad6b066 fix(forum_post): validate edit response payload`.

The implementation widens `_require_forum_post_action_status(...)` to accept `object` and adds one preflight guard:

```python
if not isinstance(data, dict):
    raise NoElementException(
        f"Forum post action response is malformed for site: {post.thread.site.unix_name}, post: {post.id} "
        f"(event={event}, expected=dict, actual={type(data).__name__})"
    )
```

The RED regression mocked `ForumPost.edit(...)`'s `saveEditPost` response as `["not-ok"]`. Before the fix, the helper leaked `TypeError: list indices must be integers or slices, not str`. After the fix, the same case raises contextual `NoElementException`, decodes the save response once, preserves title/source state, preserves cached revisions, and preserves cached thread posts.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Non-dictionary edit payloads fail before `status` lookup. | `test_edit_malformed_action_response_type_preserves_local_state_and_caches` failed RED with raw `TypeError`, then passed GREEN. | Reaching `data["status"]`, leaking `TypeError`, coercing the payload, or treating a list as an edit result rejects this claim. |
| Missing `status` in a dictionary keeps the existing Issue 250 diagnostic. | Focused GREEN included `test_edit_missing_save_action_status_does_not_update_local_state`. | Reclassifying `{}` as the payload-type branch or dropping `field=status` rejects this claim. |
| Present non-string `status` keeps the existing Issue 721 diagnostic. | Focused GREEN included `test_edit_malformed_action_status_type_preserves_local_state_and_caches`. | Reclassifying `{"status": ["not-ok"]}` as a payload-type error rejects this claim. |
| Explicit non-ok string statuses still use `WikidotStatusCodeException`. | Focused GREEN included `test_edit_explicit_non_ok_action_status_preserves_local_state_and_caches`. | Reclassifying non-ok strings as malformed response shape rejects this claim. |
| Failed edit payloads do not mutate local state or caches. | The new regression asserts one save request, one JSON decode, preserved title, preserved `_source`, preserved `_revisions`, and preserved thread `_posts`. | Updating title/source or clearing cached revisions/thread posts before confirmed success rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3911 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `ad6b066 fix(forum_post): validate edit response payload`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_malformed_action_response_type_preserves_local_state_and_caches -q` failed before the fix with raw `TypeError: list indices must be integers or slices, not str`.
- GREEN focused: the same new regression passed after the payload guard.
- Edit response coverage: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_success tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_success_invalidates_cached_revisions tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_success_invalidates_thread_posts_cache tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_save_action_status_does_not_update_local_state tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_malformed_action_status_type_preserves_local_state_and_caches tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_malformed_action_response_type_preserves_local_state_and_caches tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_explicit_non_ok_action_status_preserves_local_state_and_caches tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_with_new_title -q` passed 8 tests.
- Forum post module coverage: `uv run pytest tests/unit/test_forum_post.py -q` passed 298 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3911 tests.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left both files unchanged.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `ForumPost.edit(...)` with `response.json()` returning `["not-ok"]` raises `NoElementException` matching `Forum post action response is malformed for site: test-site, post: 5001 (event=saveEditPost, expected=dict, actual=list)`.
- `{}` still raises the existing missing-status message with `field=status`.
- `{"status": ["not-ok"]}` still raises the existing malformed status-type message with `expected=str, actual=list`.
- Explicit non-ok string statuses still raise `WikidotStatusCodeException`.
- The malformed payload branch decodes the save response JSON once, preserves title/source state, preserves cached revisions, preserves cached thread posts, and does not include raw response data.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: A caller may have relied on raw `TypeError` from malformed synthetic responses. Mitigation: the public module expects a status-bearing result object, and repo validation style consistently routes malformed generated response shape through contextual `NoElementException`.
- Risk: This could be confused with edit-form response validation. Mitigation: edit-form body and revision diagnostics run before `saveEditPost`; this slice only covers the returned save action payload.
- Risk: This could hide raw payload details useful for debugging. Mitigation: the diagnostic includes site, post ID, event, expected type, and actual type while avoiding raw response data that could contain private forum content or account material.

## Dependencies

- Forum post edit save responses remain expected to decode as JSON objects with string `status`.
- `WikidotStatusCodeException` remains responsible for explicit non-ok string statuses.
- `NoElementException` remains the parser/data-shape exception for malformed module response payloads.

## Open Questions

None for this local slice. Similar non-mapping action-payload guards may be useful on site-invitation, site-application, and site-member mutation helpers, but each surface should receive its own duplicate check against the existing action-status and status-type issue series before implementation.

## Rationale for Upstream Suitability

The patch is small, local, and consistent with existing wikidot.py response-shape diagnostics. It improves failure classification for malformed forum post edit responses without changing successful edits, edit-form parsing, local state update timing, cache invalidation timing, or existing status-code behavior.

## Local Evidence

- Local rollout-backed forum drafts established forum post edits, post-source/edit-form handling, forum mutation diagnostics, generated discussion workflows, moderation tooling, cached revisions, cached thread posts, and fixtures as practical consumers of forum post behavior.
- Existing local drafts covered missing edit action status context, present non-string edit action status values, raw connector envelope status typing, edit-form body/revision diagnostics, edit cache invalidation, forum write text inputs, retained post/thread/site/title state, and retained site/client state. They did not cover a decoded `saveEditPost` response payload that is not a mapping before status lookup.
- This slice only validates forum post edit payload shape. It does not change request construction, login checks, retry behavior, forum category creation, forum thread replies, site administration handling, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw forum content, raw response bodies, private site data, and private source text out of upstream discussion.
