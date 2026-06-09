# PR Draft: Validate Site Invitation Action Status Type

## Summary

`Site.invite_user(...)` sends Wikidot's `inviteMember` action through `ManageSiteMembershipAction`, decodes the action response, and requires `status` before treating an invitation as complete. Issue [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md) covered missing status context and explicit non-ok string statuses, but present non-string values such as `{"status": ["not-ok"]}` were still routed into `WikidotStatusCodeException` as if they were real Wikidot status codes. This change rejects malformed generated response data before accepting the invitation result.

## Outcome

Site invitation workflows now distinguish malformed action-response shape from real Wikidot status-code failures, preserving existing string-status behavior while surfacing type-corrupt generated responses with site, user, event, field, and type context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free site invitations, onboarding jobs, moderation workflows, migration notifications, generated fixtures, or audit-driven membership operations where invitation action responses may come from synthetic tests, recorded traffic, adapters, or generated data.

## Current Evidence

Local rollout-backed drafts already identify site invitations and membership administration as practical shared workflows. Existing drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), [356-pr-validate-site-invite-text-input.md](356-pr-validate-site-invite-text-input.md), [370-pr-validate-site-invite-user-input.md](370-pr-validate-site-invite-user-input.md), [619-pr-validate-site-invite-user-client.md](619-pr-validate-site-invite-user-client.md), and [686-pr-validate-site-invite-user-id-range.md](686-pr-validate-site-invite-user-id-range.md) cover member acquisition, parser diagnostics, response-body diagnostics, invitation payloads, text/user/client validation, retained target-ID validation, duplicate-invitation mappings, and missing/non-ok action status behavior.

Adjacent membership action drafts [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [716-pr-validate-site-application-action-status-type.md](716-pr-validate-site-application-action-status-type.md), and [717-pr-validate-site-member-action-status-type.md](717-pr-validate-site-member-action-status-type.md) establish the same status-bearing action-response pattern for member role changes and site application moderation. Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) is not a duplicate: it covers raw Ajax Module Connector response status typing before module-level dispatch. Issues [714-pr-validate-page-save-status-type.md](714-pr-validate-page-save-status-type.md), [715-pr-validate-private-message-send-status-type.md](715-pr-validate-private-message-send-status-type.md), [716-pr-validate-site-application-action-status-type.md](716-pr-validate-site-application-action-status-type.md), and [717-pr-validate-site-member-action-status-type.md](717-pr-validate-site-member-action-status-type.md) are also not duplicates: they cover separate module-level action payloads. This slice validates the site-invitation action response consumed by `Site.invite_user(...)`. No upstream issue was filed from this local workspace.

## Changes

- Add a type guard in the site-invitation action status extractor.
- Raise `NoElementException` for a present non-string `status` with site, user, user ID, event, field, expected type, and actual type context.
- Preserve the Issue 253 missing-status diagnostic.
- Preserve explicit non-ok string handling through `WikidotStatusCodeException`, including the existing `already_invited` and `already_member` mappings.
- Add a focused regression proving malformed status types are decoded once and rejected as malformed action-response shape.

## Type Of Change

- Response-shape validation
- Site invitation action hardening
- Generated response data diagnostics
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.invite_user(...)` must reject a non-string action response `status` with `NoElementException` containing site, user, user ID, event, `field=status`, `expected=str`, and the actual type. |
| R2 | A missing `status` field must keep the existing Issue 253 missing-status diagnostic. |
| R3 | Explicit non-ok string statuses must still raise `WikidotStatusCodeException` and retain `TargetErrorException` mappings for `already_invited` and `already_member`. |
| R4 | The malformed status path must decode the response body once. |
| R5 | Adjacent site invitation behavior must remain green. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `{"status": ["not-ok"]}` fails with malformed site-invitation action status context before completion is accepted. | `test_invite_user_malformed_action_status_type_includes_site_user_event_and_type_context` failed RED with `WikidotStatusCodeException`, then passed GREEN after status typing was added. | Treating a list, dict, number, or object as a Wikidot status code rejects this local completion claim. | Site invitation action response shape | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | `{}` still raises the Issue 253 missing-status message with site, user, id, event, and field context. | `test_invite_user_missing_action_status_includes_site_user_event_and_field_context` passed unchanged. | Changing the missing-status exception type, dropping context, or masking it behind status-code handling rejects this local completion claim. | Site invitation missing field handling | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Existing mapped and unmapped non-ok string statuses keep the status-code path. | `test_invite_user_other_error_reraises`, `test_invite_user_already_invited`, and `test_invite_user_already_member` passed unchanged. | Reclassifying non-ok strings as malformed response shape or losing mapped target errors rejects this local completion claim. | Site invitation status-code handling | `tests/unit/test_site.py` |
| R4 | The malformed status path decodes the response JSON once. | The new regression asserts `mock_response.json.call_count == 1`. | Reintroducing duplicate decode work or accepting the malformed response as successful rejects this local completion claim. | Site invitation response decoding safety | `tests/unit/test_site.py` |
| R5 | Adjacent site invitation behavior remains stable. | `TestSiteInviteUser` passed 16 tests and `tests/unit/test_site.py` passed 351 tests. | Regressing invitation payloads, text/user/client validation, target ID validation, missing-status diagnostics, mapped duplicate statuses, login-required behavior, or site workflows rejects this local completion claim. | Site invitation workflows | `tests/unit/test_site.py` |
| R6 | No live site state or private material is needed to prove the behavior. | The regression uses synthetic unit-level response bodies and mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private invitation text, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `e247364 fix(site): validate invite status type`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_malformed_action_status_type_includes_site_user_event_and_type_context -q` failed before the fix with `WikidotStatusCodeException` instead of the expected malformed-shape `NoElementException`.
- GREEN focused: `uv run pytest tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_missing_action_status_includes_site_user_event_and_field_context tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_malformed_action_status_type_includes_site_user_event_and_type_context tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_already_invited tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_already_member tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_other_error_reraises -q` passed 5 tests.
- `uv run pytest tests/unit/test_site.py::TestSiteInviteUser -q` passed 16 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 351 tests.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` left both files unchanged.
- `uv run ruff check src/wikidot/module/site.py tests/unit/test_site.py` passed.
- `git diff --check` passed.

## Acceptance Criteria

- `{"status": ["not-ok"]}` raises `NoElementException` with site, user, id, event, `field=status`, `expected=str`, and `actual=list` context.
- `{}` still raises the existing missing-status message from Issue 253.
- `{"status": "other_error"}` still raises `WikidotStatusCodeException`.
- Existing `already_invited` and `already_member` mappings still raise `TargetErrorException`.
- The malformed non-string status path still decodes the response JSON once.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A caller may have relied on a non-string `status` object being formatted into a `WikidotStatusCodeException`. Mitigation: Wikidot action statuses are strings, Issue 403 already validates raw AMC statuses as strings, and module-level action responses should reject malformed generated data before business handling.
- Risk: This could be confused with raw AMC response typing. Mitigation: Issue 403 covers the raw connector response envelope; this slice covers the site-invitation action payload used by `Site.invite_user(...)`.
- Risk: This could be confused with adjacent module-level status typing. Mitigation: Issues 714, 715, 716, and 717 cover page save, private-message send, site-application, and site-member actions respectively; this slice covers site invitation actions.
- Risk: Tightening action response shape could hide legitimate non-ok Wikidot string statuses. Mitigation: non-ok strings are deliberately preserved on the existing `WikidotStatusCodeException` path.
- Risk: The error could become too generic for generated fixtures. Mitigation: the diagnostic names the site, user, id, event, field, expected type, and actual type.

## Dependencies

- Existing `Site.invite_user(...)` remains responsible for invitation orchestration.
- Existing `WikidotStatusCodeException` handling remains responsible for explicit non-ok string statuses.
- Existing `TargetErrorException` mappings remain responsible for known invitation status strings.
- Existing `NoElementException` remains the parser/data-shape exception for missing or malformed response fields.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered site-invitation action status type path.

## Upstream-Safe Motivation

`Site.invite_user(...)` treats invitation responses as status-bearing action payloads. Rejecting malformed status types at that boundary keeps generated or adapted response data from masquerading as a real Wikidot status code and makes membership invitation failures easier to diagnose.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established site invitations, generated onboarding jobs, migration notifications, membership administration, and moderation workflows as practical consumers of site-invitation behavior.
- Existing site-invitation and raw AMC drafts covered missing action status context, explicit non-ok action strings, mapped duplicate-invitation errors, and raw connector envelope status typing; they did not validate the module-level site-invitation action status type.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, invitation text from real sites, and source text from real sites out of upstream discussion.
