# PR Draft: Validate Site Member Response Payload

## Summary

`SiteMember.to_moderator()`, `remove_moderator()`, `to_admin()`, and `remove_admin()` now validate that decoded `ManageSiteMembershipAction` responses are dictionaries before reading `status`. Non-mapping payloads such as `["not-ok"]` raise contextual `NoElementException` with site, user, user ID, event, expected type, and actual type context instead of leaking raw list `TypeError`.

The change is intentionally narrow: valid `{"status": "ok"}` role changes, missing `status` diagnostics, non-string `status` diagnostics, explicit non-ok string handling, mapped role-change errors, and role-cache invalidation remain unchanged.

## Problem Statement

Site member role changes route through `_change_group(...)`, send `ManageSiteMembershipAction`, decode the action response, and validate `status` before accepting the role change as complete. Earlier local slices covered missing action `status`, explicit non-ok statuses, present non-string statuses such as `{"status": ["not-ok"]}`, member user/site/joined-at validation, retained user ID validation, retained site/client validation, and role-cache invalidation. One response-shape gap remained: if `response.json()` returned a non-dictionary payload, `_require_site_member_action_status(...)` attempted `data["status"]` and leaked raw `TypeError`.

That failure gives callers neither the site member action context nor a stable wikidot.py data-shape exception. Generated fixtures, response adapters, recorded traffic, or mocked responses should be classified before field access, and failed role-change responses must not clear role caches.

## Rollout Evidence

Local rollout-backed drafts identify site member reads and role changes as practical browser-free workflows: [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md), [410-pr-validate-site-member-action-users.md](410-pr-validate-site-member-action-users.md), [605-pr-validate-site-member-user-client.md](605-pr-validate-site-member-user-client.md), [688-pr-validate-site-member-action-user-id-range.md](688-pr-validate-site-member-action-user-id-range.md), [700-pr-validate-site-member-constructor-user-id-state.md](700-pr-validate-site-member-constructor-user-id-state.md), [717-pr-validate-site-member-action-status-type.md](717-pr-validate-site-member-action-status-type.md), and [803-pr-validate-site-admin-action-clients.md](803-pr-validate-site-admin-action-clients.md).

This slice is not a duplicate of [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md). Issue 255 covered mapping responses with missing `status` and explicit non-ok string statuses.

This slice is not a duplicate of [717-pr-validate-site-member-action-status-type.md](717-pr-validate-site-member-action-status-type.md). Issue 717 covered a present non-string `status` field inside a mapping, such as `{"status": ["not-ok"]}`. This slice covers the decoded role-change action response payload not being a mapping before status lookup starts.

Adjacent membership action drafts [815-pr-validate-site-invite-response-payload.md](815-pr-validate-site-invite-response-payload.md) and [816-pr-validate-site-application-response-payload.md](816-pr-validate-site-application-response-payload.md) cover separate module-level action payloads. Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) covers the raw Ajax Module Connector response envelope before module-level action payload handling.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free site member role changes through `SiteMember` role helpers.
- Membership administration tools that promote or demote members.
- Generated fixtures and recorded-response tests that decode action responses before returning them to wikidot.py module code.

## Proposed Fix

- Validate the decoded role-change action response payload as a dictionary in `_require_site_member_action_status(...)`.
- Reject non-dictionary payloads with `NoElementException` before `status` lookup.
- Include only structural context and type names in the diagnostic, not raw response data.
- Preserve existing dictionary `status` validation, status-code handling, mapped target errors, and role-cache invalidation timing.

## Implementation Notes

Implemented locally in commit `fde5538 fix(site_member): validate action response payload`.

The implementation widens `_require_site_member_action_status(...)` to accept `object` and adds one preflight guard:

```python
if not isinstance(data, dict):
    raise NoElementException(
        f"Site member action response is malformed for site: {member.site.unix_name}, "
        f"user: {member.user.name} (id={member.user.id}, event={event}, "
        f"expected=dict, actual={type(data).__name__})"
    )
```

The RED regression mocked `SiteMember.to_moderator()`'s action response as `["not-ok"]`. Before the fix, the helper leaked `TypeError: list indices must be integers or slices, not str`. After the fix, the same case raises contextual `NoElementException`, decodes the response once, and preserves cached moderator/admin lists.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Non-dictionary member action payloads fail before `status` lookup. | `test_change_group_malformed_action_response_type_includes_site_user_event_and_type_context` failed RED with raw `TypeError`, then passed GREEN. | Reaching `data["status"]`, leaking `TypeError`, coercing the payload, or treating a list as a role-change result rejects this claim. |
| Missing `status` in a dictionary keeps the existing Issue 255 diagnostic. | Focused GREEN included `test_change_group_missing_action_status_includes_site_user_event_and_field_context`. | Reclassifying `{}` as the payload-type branch or dropping `field=status` rejects this claim. |
| Present non-string `status` keeps the existing Issue 717 diagnostic. | Focused GREEN included `test_change_group_malformed_action_status_type_includes_site_user_event_and_type_context`. | Reclassifying `{"status": ["not-ok"]}` as a payload-type error rejects this claim. |
| Explicit non-ok string statuses still use `WikidotStatusCodeException` and mapped statuses still become `TargetErrorException`. | Focused GREEN included `test_change_group_other_error_reraises`, `test_change_group_already_moderator_error`, and `test_change_group_not_already_error`. | Reclassifying non-ok strings as malformed response shape or losing mapped target errors rejects this claim. |
| Failed role-change payloads do not clear role caches. | The new regression asserts cached moderator/admin lists are preserved after malformed payload failure. | Clearing `_moderators` or `_admins` before confirmed `status: ok` rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3914 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `fde5538 fix(site_member): validate action response payload`.

- RED: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_malformed_action_response_type_includes_site_user_event_and_type_context -q --tb=short` failed before the fix with raw `TypeError: list indices must be integers or slices, not str`.
- GREEN focused: the new regression passed with role-change success, role-cache invalidation, missing-status, malformed-status-type, unmapped non-ok status, and mapped role-change error tests.
- Site member module coverage: `uv run pytest tests/unit/test_site_member.py -q --tb=short` passed 90 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3914 tests.
- `uv run ruff format src/wikidot/module/site_member.py tests/unit/test_site_member.py` left both files unchanged.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `SiteMember.to_moderator()` with `response.json()` returning `["not-ok"]` raises `NoElementException` matching `Site member action response is malformed for site: test-site, user: TestUser (id=12345, event=toModerators, expected=dict, actual=list)`.
- `{}` still raises the existing missing-status message with `field=status`.
- `{"status": ["not-ok"]}` still raises the existing malformed status-type message with `expected=str, actual=list`.
- Explicit non-ok string statuses still raise `WikidotStatusCodeException`, and mapped role-change statuses still raise `TargetErrorException`.
- The malformed payload branch decodes the response JSON once, preserves cached moderator/admin lists, and does not include raw response data.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: A caller may have relied on raw `TypeError` from malformed synthetic responses. Mitigation: the public module expects a status-bearing result object, and repo validation style consistently routes malformed generated response shape through contextual `NoElementException`.
- Risk: This could be confused with raw AMC response validation. Mitigation: Issue 403 covers the raw connector response envelope; this slice only covers the role-change action payload consumed by `SiteMember._change_group(...)`.
- Risk: This could hide raw payload details useful for debugging. Mitigation: the diagnostic includes site, user, user ID, event, expected type, and actual type while avoiding raw response data that could contain private membership details.

## Dependencies

- Site member action responses remain expected to decode as JSON objects with string `status`.
- `WikidotStatusCodeException` remains responsible for explicit non-ok string statuses.
- `NoElementException` remains the parser/data-shape exception for malformed module response payloads.

## Open Questions

None for this local slice.

## Rationale for Upstream Suitability

The patch is small, local, and consistent with existing wikidot.py response-shape diagnostics. It improves failure classification for malformed site member role-change responses without changing successful role changes, request construction, login checks, mapped target errors, or existing status-code behavior.

## Local Evidence

- Local rollout-backed membership drafts established site member acquisition, role changes, role-cache invalidation, and membership administration as practical workflow surfaces.
- Existing local drafts covered missing member action status context, present non-string member action status values, raw connector envelope status typing, member user/site/joined-at validation, retained user ID validation, retained site/client validation, and role-cache invalidation. They did not cover a decoded member role-change response payload that is not a mapping before status lookup.
- This slice only validates site member role-change payload shape. It does not change request construction, login checks, retry behavior, member-list parsing, site invitation handling, site application moderation, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw membership content, raw response bodies, private site data, and private source text out of upstream discussion.
