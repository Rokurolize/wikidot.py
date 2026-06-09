# PR Draft: Validate Site Member Action Status Type

## Summary

`SiteMember.to_moderator()`, `remove_moderator()`, `to_admin()`, and `remove_admin()` route through `SiteMember._change_group(...)`, decode the `ManageSiteMembershipAction` response, and require `status` before treating a role-change action as complete. Issue [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md) covered missing status context and explicit non-ok string statuses, but present non-string values such as `{"status": ["not-ok"]}` were still routed into `WikidotStatusCodeException` as if they were real Wikidot status codes. This change rejects malformed generated response data before accepting the role-change result.

## Outcome

Site member permission-change workflows now distinguish malformed action-response shape from real Wikidot status-code failures, preserving existing string-status behavior while surfacing type-corrupt generated responses with site, user, event, field, and type context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free site member administration, permission audits, migration, generated-fixture, or moderation workflows where member action responses may come from synthetic tests, recorded traffic, adapters, or generated data.

## Current Evidence

Local rollout-backed drafts already identify site member reads and role changes as practical shared workflows. Existing drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [410-pr-validate-site-member-action-users.md](410-pr-validate-site-member-action-users.md), [499-pr-validate-site-member-joined-at-field.md](499-pr-validate-site-member-joined-at-field.md), [605-pr-validate-site-member-user-client.md](605-pr-validate-site-member-user-client.md), [688-pr-validate-site-member-action-user-id-range.md](688-pr-validate-site-member-action-user-id-range.md), [690-pr-validate-site-member-constructor-user-id-range.md](690-pr-validate-site-member-constructor-user-id-range.md), and [700-pr-validate-site-member-constructor-user-id-state.md](700-pr-validate-site-member-constructor-user-id-state.md) cover member acquisition, parser diagnostics, response-body diagnostics, role-change behavior, cache synchronization, user/site/joined-at validation, client coherence, retained-ID validation, and missing/non-ok action status behavior.

Adjacent membership action drafts [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), and [716-pr-validate-site-application-action-status-type.md](716-pr-validate-site-application-action-status-type.md) establish the same status-bearing action-response pattern for invitations and site application moderation. Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) is not a duplicate: it covers raw Ajax Module Connector response status typing before module-level dispatch. Issues [714-pr-validate-page-save-status-type.md](714-pr-validate-page-save-status-type.md), [715-pr-validate-private-message-send-status-type.md](715-pr-validate-private-message-send-status-type.md), and [716-pr-validate-site-application-action-status-type.md](716-pr-validate-site-application-action-status-type.md) are also not duplicates: they cover separate module-level action payloads. This slice validates the site-member action response consumed by `SiteMember._change_group(...)`. No upstream issue was filed from this local workspace.

## Changes

- Add a type guard in the site-member action status extractor.
- Raise `NoElementException` for a present non-string `status` with site, user, user ID, event, field, expected type, and actual type context.
- Preserve the Issue 255 missing-status diagnostic.
- Preserve explicit non-ok string handling through `WikidotStatusCodeException`, including the existing `not_already`, `already_admin`, and `already_moderator` mappings.
- Add a focused regression proving malformed status types are decoded once, leave role caches untouched, and are rejected as malformed action-response shape.

## Type Of Change

- Response-shape validation
- Site member role-change action hardening
- Generated response data diagnostics
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteMember.to_moderator(...)` and the shared `_change_group(...)` path must reject a non-string action response `status` with `NoElementException` containing site, user, user ID, event, `field=status`, `expected=str`, and the actual type. |
| R2 | A missing `status` field must keep the existing Issue 255 missing-status diagnostic. |
| R3 | Explicit non-ok string statuses must still raise `WikidotStatusCodeException` and retain `TargetErrorException` mappings for `not_already`, `already_admin`, and `already_moderator`. |
| R4 | The malformed status path must decode the response body once and must not clear cached moderator or admin lists. |
| R5 | Adjacent site member parsing and action behavior must remain green. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `{"status": ["not-ok"]}` fails with malformed site-member action status context before completion is accepted. | `test_change_group_malformed_action_status_type_includes_site_user_event_and_type_context` failed RED with `WikidotStatusCodeException`, then passed GREEN after status typing was added. | Treating a list, dict, number, or object as a Wikidot status code rejects this local completion claim. | Site member action response shape | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R2 | `{}` still raises the Issue 255 missing-status message with site, user, id, event, and field context. | `test_change_group_missing_action_status_includes_site_user_event_and_field_context` passed unchanged. | Changing the missing-status exception type, dropping context, or masking it behind status-code handling rejects this local completion claim. | Site member missing field handling | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R3 | Existing mapped and unmapped non-ok string statuses keep the status-code path. | `test_change_group_other_error_reraises`, `test_change_group_already_moderator_error`, and `test_change_group_not_already_error` passed unchanged. | Reclassifying non-ok strings as malformed response shape or losing mapped target errors rejects this local completion claim. | Site member status-code handling | `tests/unit/test_site_member.py` |
| R4 | The malformed status path decodes the response JSON once and leaves `_moderators` and `_admins` unchanged. | The new regression asserts `mock_response.json.call_count == 1` and cache identity preservation. | Reintroducing duplicate decode work or clearing role caches on malformed response shape rejects this local completion claim. | Site member response decoding/cache safety | `tests/unit/test_site_member.py` |
| R5 | Adjacent site member behavior remains stable. | `TestSiteMemberChangeGroup` passed 34 tests and `tests/unit/test_site_member.py` passed 87 tests. | Regressing member-list parsing, role-change payloads, invalid event handling, cache behavior, user/site/joined-at validation, or parser diagnostics rejects this local completion claim. | Site member workflows | `tests/unit/test_site_member.py` |
| R6 | No live site state or private material is needed to prove the behavior. | The regression uses synthetic unit-level response bodies and mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private content, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `01e7609 fix(site_member): validate action status type`.

- RED: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_malformed_action_status_type_includes_site_user_event_and_type_context -q` failed before the fix with `WikidotStatusCodeException` instead of the expected malformed-shape `NoElementException`.
- GREEN focused: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_missing_action_status_includes_site_user_event_and_field_context tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_malformed_action_status_type_includes_site_user_event_and_type_context tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_other_error_reraises tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_already_moderator_error tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_not_already_error -q` passed 5 tests.
- `uv run pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup -q` passed 34 tests.
- `uv run pytest tests/unit/test_site_member.py -q` passed 87 tests.
- `uv run ruff format src/wikidot/module/site_member.py tests/unit/test_site_member.py` left both files unchanged.
- `uv run ruff check src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed.
- `git diff --check` passed.

## Acceptance Criteria

- `{"status": ["not-ok"]}` raises `NoElementException` with site, user, id, event, `field=status`, `expected=str`, and `actual=list` context.
- `{}` still raises the existing missing-status message from Issue 255.
- `{"status": "some_other_error"}` still raises `WikidotStatusCodeException`.
- Existing `not_already`, `already_admin`, and `already_moderator` mappings still raise `TargetErrorException`.
- The malformed non-string status path still decodes the response JSON once and does not clear `site._moderators` or `site._admins`.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A caller may have relied on a non-string `status` object being formatted into a `WikidotStatusCodeException`. Mitigation: Wikidot action statuses are strings, Issue 403 already validates raw AMC statuses as strings, and module-level action responses should reject malformed generated data before business handling.
- Risk: This could be confused with raw AMC response typing. Mitigation: Issue 403 covers the raw connector response envelope; this slice covers the site-member action payload used by `SiteMember._change_group(...)`.
- Risk: This could be confused with adjacent module-level status typing. Mitigation: Issues 714, 715, and 716 cover page save, private-message send, and site-application actions respectively; this slice covers site member role-change actions.
- Risk: Tightening action response shape could hide legitimate non-ok Wikidot string statuses. Mitigation: non-ok strings are deliberately preserved on the existing `WikidotStatusCodeException` path.
- Risk: The error could become too generic for generated fixtures. Mitigation: the diagnostic names the site, user, id, event, field, expected type, and actual type.

## Dependencies

- Existing `SiteMember._change_group(...)` remains responsible for role-change orchestration.
- Existing `WikidotStatusCodeException` handling remains responsible for explicit non-ok string statuses.
- Existing `TargetErrorException` mappings remain responsible for known role-change status strings.
- Existing `NoElementException` remains the parser/data-shape exception for missing or malformed response fields.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered site-member action status type path.

## Upstream-Safe Motivation

`SiteMember._change_group(...)` treats role-change action responses as status-bearing action payloads. Rejecting malformed status types at that boundary keeps generated or adapted response data from masquerading as a real Wikidot status code and makes membership administration failures easier to diagnose.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established site member reads, moderator/admin role changes, generated-fixture, migration, membership administration, and moderation workflows as practical consumers of site-member behavior.
- Existing site-member and raw AMC drafts covered missing action status context, explicit non-ok action strings, mapped role-change errors, and raw connector envelope status typing; they did not validate the module-level site-member action status type.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, member names from real sites, and source text from real sites out of upstream discussion.
