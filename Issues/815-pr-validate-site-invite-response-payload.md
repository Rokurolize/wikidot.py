# PR Draft: Validate Site Invite Response Payload

## Summary

`Site.invite_user(...)` now validates that decoded `inviteMember` action responses are dictionaries before reading `status`. Non-mapping payloads such as `["not-ok"]` raise contextual `NoElementException` with site, user, user ID, event, expected type, and actual type context instead of leaking a raw list `TypeError`.

The change is intentionally narrow: valid `{"status": "ok"}` invitations, missing `status` diagnostics, non-string `status` diagnostics, explicit non-ok string handling, and the existing `already_invited` / `already_member` mappings remain unchanged.

## Problem Statement

Site invitations send Wikidot's `inviteMember` action through `ManageSiteMembershipAction`, decode the action response, and require a status-bearing result before treating the invitation as complete. Earlier local slices covered invitation text/user validation, retained target ID validation, retained client validation, missing action `status`, explicit non-ok statuses, and present non-string statuses such as `{"status": ["not-ok"]}`. One response-shape gap remained: if `response.json()` returned a non-dictionary payload, `_require_site_invitation_action_status(...)` attempted `data["status"]` and leaked raw `TypeError`.

That failure gives callers neither the invitation action context nor a stable wikidot.py data-shape exception. Generated fixtures, response adapters, recorded traffic, or mocked responses should be classified before field access.

## Rollout Evidence

Local rollout-backed drafts identify site invitations and membership administration as practical browser-free workflows: [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), [356-pr-validate-site-invite-text-input.md](356-pr-validate-site-invite-text-input.md), [370-pr-validate-site-invite-user-input.md](370-pr-validate-site-invite-user-input.md), [619-pr-validate-site-invite-user-client.md](619-pr-validate-site-invite-user-client.md), [686-pr-validate-site-invite-user-id-range.md](686-pr-validate-site-invite-user-id-range.md), and [718-pr-validate-site-invite-action-status-type.md](718-pr-validate-site-invite-action-status-type.md).

This slice is not a duplicate of [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md). Issue 253 covered mapping responses with missing `status` and explicit non-ok string statuses.

This slice is not a duplicate of [718-pr-validate-site-invite-action-status-type.md](718-pr-validate-site-invite-action-status-type.md). Issue 718 covered a present non-string `status` field inside a mapping, such as `{"status": ["not-ok"]}`. This slice covers the decoded `inviteMember` response payload not being a mapping before status lookup starts.

Adjacent membership action drafts [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [716-pr-validate-site-application-action-status-type.md](716-pr-validate-site-application-action-status-type.md), and [717-pr-validate-site-member-action-status-type.md](717-pr-validate-site-member-action-status-type.md) cover separate module-level action payloads. Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) covers the raw Ajax Module Connector response envelope before module-level action payload handling.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free site invitations through `Site.invite_user(...)`.
- Membership administration tools that invite users and classify duplicate-invitation responses.
- Generated fixtures and recorded-response tests that decode action responses before returning them to wikidot.py module code.

## Proposed Fix

- Validate the decoded `inviteMember` response payload as a dictionary in `_require_site_invitation_action_status(...)`.
- Reject non-dictionary payloads with `NoElementException` before `status` lookup.
- Include only structural context and type names in the diagnostic, not raw response data.
- Preserve existing dictionary `status` validation, status-code handling, and duplicate-invitation mappings.

## Implementation Notes

Implemented locally in commit `1a7591e fix(site): validate invite response payload`.

The implementation widens `_require_site_invitation_action_status(...)` to accept `object` and adds one preflight guard:

```python
if not isinstance(data, dict):
    raise exceptions.NoElementException(
        f"Site invitation action response is malformed for site: {site.unix_name}, user: {user.name} "
        f"(id={user.id}, event={event}, expected=dict, actual={type(data).__name__})"
    )
```

The RED regression mocked `Site.invite_user(...)`'s `inviteMember` response as `["not-ok"]`. Before the fix, the helper leaked `TypeError: list indices must be integers or slices, not str`. After the fix, the same case raises contextual `NoElementException` and decodes the response once.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Non-dictionary invitation payloads fail before `status` lookup. | `test_invite_user_malformed_action_response_type_includes_site_user_event_and_type_context` failed RED with raw `TypeError`, then passed GREEN. | Reaching `data["status"]`, leaking `TypeError`, coercing the payload, or treating a list as an invitation result rejects this claim. |
| Missing `status` in a dictionary keeps the existing Issue 253 diagnostic. | Focused GREEN included `test_invite_user_missing_action_status_includes_site_user_event_and_field_context`. | Reclassifying `{}` as the payload-type branch or dropping `field=status` rejects this claim. |
| Present non-string `status` keeps the existing Issue 718 diagnostic. | Focused GREEN included `test_invite_user_malformed_action_status_type_includes_site_user_event_and_type_context`. | Reclassifying `{"status": ["not-ok"]}` as a payload-type error rejects this claim. |
| Explicit non-ok string statuses still use `WikidotStatusCodeException` and mapped duplicate statuses still become `TargetErrorException`. | Focused GREEN included `test_invite_user_already_invited`, `test_invite_user_already_member`, and `test_invite_user_other_error_reraises`. | Reclassifying non-ok strings as malformed response shape or losing mapped target errors rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3912 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `1a7591e fix(site): validate invite response payload`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_malformed_action_response_type_includes_site_user_event_and_type_context -q --tb=short` failed before the fix with raw `TypeError: list indices must be integers or slices, not str`.
- GREEN focused: `uv run pytest tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_success tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_missing_action_status_includes_site_user_event_and_field_context tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_malformed_action_status_type_includes_site_user_event_and_type_context tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_malformed_action_response_type_includes_site_user_event_and_type_context tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_already_invited tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_already_member tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_other_error_reraises -q --tb=short` passed 7 tests.
- Site module coverage: `uv run pytest tests/unit/test_site.py -q --tb=short` passed 377 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3912 tests.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` left both files unchanged.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Site.invite_user(...)` with `response.json()` returning `["not-ok"]` raises `NoElementException` matching `Site invitation action response is malformed for site: test, user: test-user (id=12345, event=inviteMember, expected=dict, actual=list)`.
- `{}` still raises the existing missing-status message with `field=status`.
- `{"status": ["not-ok"]}` still raises the existing malformed status-type message with `expected=str, actual=list`.
- Explicit non-ok string statuses still raise `WikidotStatusCodeException`, and `already_invited` / `already_member` still map to `TargetErrorException`.
- The malformed payload branch decodes the response JSON once and does not include raw response data.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: A caller may have relied on raw `TypeError` from malformed synthetic responses. Mitigation: the public module expects a status-bearing result object, and repo validation style consistently routes malformed generated response shape through contextual `NoElementException`.
- Risk: This could be confused with raw AMC response validation. Mitigation: Issue 403 covers the raw connector response envelope; this slice only covers the `inviteMember` action payload consumed by `Site.invite_user(...)`.
- Risk: This could hide raw payload details useful for debugging. Mitigation: the diagnostic includes site, user, user ID, event, expected type, and actual type while avoiding raw response data that could contain private membership details.

## Dependencies

- Site invitation responses remain expected to decode as JSON objects with string `status`.
- `WikidotStatusCodeException` remains responsible for explicit non-ok string statuses.
- `NoElementException` remains the parser/data-shape exception for malformed module response payloads.

## Open Questions

None for this local slice. Similar non-mapping action-payload guards may be useful on site-application and site-member mutation helpers, but each surface should receive its own duplicate check against the existing action-status and status-type issue series before implementation.

## Rationale for Upstream Suitability

The patch is small, local, and consistent with existing wikidot.py response-shape diagnostics. It improves failure classification for malformed site invitation responses without changing successful invitations, request construction, login checks, duplicate-invitation mappings, or existing status-code behavior.

## Local Evidence

- Local rollout-backed membership drafts established site invitations, membership administration, member-list acquisition, parser diagnostics, response-body diagnostics, duplicate-invitation mappings, invitation input validation, retained target-ID validation, and retained client validation as practical workflow surfaces.
- Existing local drafts covered missing invitation action status context, present non-string invitation action status values, raw connector envelope status typing, invitation text/user/client validation, and retained user ID validation. They did not cover a decoded `inviteMember` response payload that is not a mapping before status lookup.
- This slice only validates site invitation payload shape. It does not change request construction, login checks, retry behavior, member-list parsing, site application moderation, site member role changes, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw membership content, raw response bodies, private site data, and private source text out of upstream discussion.
