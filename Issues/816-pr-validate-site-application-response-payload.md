# PR Draft: Validate Site Application Response Payload

## Summary

`SiteApplication.accept()` / `decline()` now validate that decoded `ManageSiteMembershipAction` responses are dictionaries before reading `status`. Non-mapping payloads such as `["not-ok"]` raise contextual `NoElementException` with site, user, user ID, event, action type, expected type, and actual type context instead of leaking raw list `TypeError`.

The change is intentionally narrow: valid `{"status": "ok"}` application actions, missing `status` diagnostics, non-string `status` diagnostics, explicit non-ok string handling, the existing `no_application` mapping, and accepted-member cache invalidation remain unchanged.

## Problem Statement

Site application moderation routes `accept()` and `decline()` through `_process(...)`, sends `ManageSiteMembershipAction`, decodes the action response, and validates `status` before accepting the action as complete. Earlier local slices covered missing action `status`, explicit non-ok statuses, present non-string statuses such as `{"status": ["not-ok"]}`, application user/site/text validation, retained user ID validation, retained site/client validation, and accept-cache invalidation. One response-shape gap remained: if `response.json()` returned a non-dictionary payload, `_require_site_application_action_status(...)` attempted `data["status"]` and leaked raw `TypeError`.

That failure gives callers neither the site application action context nor a stable wikidot.py data-shape exception. Generated fixtures, response adapters, recorded traffic, or mocked responses should be classified before field access, and failed accept responses must not clear cached members.

## Rollout Evidence

Local rollout-backed drafts identify pending application moderation as a practical browser-free workflow: [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [271-pr-site-application-accept-member-cache-invalidation.md](271-pr-site-application-accept-member-cache-invalidation.md), [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md), [687-pr-validate-site-application-user-id-range.md](687-pr-validate-site-application-user-id-range.md), [716-pr-validate-site-application-action-status-type.md](716-pr-validate-site-application-action-status-type.md), and [803-pr-validate-site-admin-action-clients.md](803-pr-validate-site-admin-action-clients.md).

This slice is not a duplicate of [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md). Issue 256 covered mapping responses with missing `status` and explicit non-ok string statuses.

This slice is not a duplicate of [716-pr-validate-site-application-action-status-type.md](716-pr-validate-site-application-action-status-type.md). Issue 716 covered a present non-string `status` field inside a mapping, such as `{"status": ["not-ok"]}`. This slice covers the decoded application action response payload not being a mapping before status lookup starts.

Adjacent membership action drafts [815-pr-validate-site-invite-response-payload.md](815-pr-validate-site-invite-response-payload.md) and [717-pr-validate-site-member-action-status-type.md](717-pr-validate-site-member-action-status-type.md) cover separate module-level action payloads. Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) covers the raw Ajax Module Connector response envelope before module-level action payload handling.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free site application acceptance and decline through `SiteApplication.accept()` / `decline()`.
- Membership moderation tools that process pending applications.
- Generated fixtures and recorded-response tests that decode action responses before returning them to wikidot.py module code.

## Proposed Fix

- Validate the decoded application action response payload as a dictionary in `_require_site_application_action_status(...)`.
- Reject non-dictionary payloads with `NoElementException` before `status` lookup.
- Include only structural context and type names in the diagnostic, not raw response data.
- Preserve existing dictionary `status` validation, status-code handling, `no_application` mapping, and accept-cache invalidation timing.

## Implementation Notes

Implemented locally in commit `e608872 fix(site_application): validate process response payload`.

The implementation widens `_require_site_application_action_status(...)` to accept `object` and adds one preflight guard:

```python
if not isinstance(data, dict):
    raise exceptions.NoElementException(
        f"Site application action response is malformed for site: {_site_name(application.site)}, "
        f"user: {application.user.name} "
        f"(id={application.user.id}, event={event}, type={action}, "
        f"expected=dict, actual={type(data).__name__})"
    )
```

The RED regression mocked `SiteApplication.accept()`'s action response as `["not-ok"]`. Before the fix, the helper leaked `TypeError: list indices must be integers or slices, not str`. After the fix, the same case raises contextual `NoElementException`, decodes the response once, and preserves the cached member list.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Non-dictionary application action payloads fail before `status` lookup. | `test_accept_malformed_action_response_type_includes_site_user_event_type_and_type_context` failed RED with raw `TypeError`, then passed GREEN. | Reaching `data["status"]`, leaking `TypeError`, coercing the payload, or treating a list as an application result rejects this claim. |
| Missing `status` in a dictionary keeps the existing Issue 256 diagnostic. | Focused GREEN included `test_accept_missing_action_status_includes_site_user_event_type_and_field_context`. | Reclassifying `{}` as the payload-type branch or dropping `field=status` rejects this claim. |
| Present non-string `status` keeps the existing Issue 716 diagnostic. | Focused GREEN included `test_accept_malformed_action_status_type_includes_site_user_event_type_and_type_context`. | Reclassifying `{"status": ["not-ok"]}` as a payload-type error rejects this claim. |
| Explicit non-ok string statuses still use `WikidotStatusCodeException`, and `no_application` still maps to `NotFoundException`. | Focused GREEN included `test_accept_explicit_non_ok_action_status_raises_status_exception` and `test_process_application_not_found`. | Reclassifying non-ok strings as malformed response shape or losing the missing-application mapping rejects this claim. |
| Failed accept payloads do not clear cached members. | The new regression asserts the cached member list is preserved after malformed payload failure. | Clearing `_members` before confirmed `status: ok` rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3913 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `e608872 fix(site_application): validate process response payload`.

- RED: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_malformed_action_response_type_includes_site_user_event_type_and_type_context -q --tb=short` failed before the fix with raw `TypeError: list indices must be integers or slices, not str`.
- GREEN focused: the new regression passed with accept success, accept cache invalidation, decline success, decline cache preservation, missing-status, malformed-status-type, explicit non-ok status, and `no_application` mapping tests.
- Site application module coverage: `uv run pytest tests/unit/test_site_application.py -q --tb=short` passed 72 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3913 tests.
- `uv run ruff format src/wikidot/module/site_application.py tests/unit/test_site_application.py` left both files unchanged.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `SiteApplication.accept()` with `response.json()` returning `["not-ok"]` raises `NoElementException` matching `Site application action response is malformed for site: test-site, user: TestUser (id=12345, event=acceptApplication, type=accept, expected=dict, actual=list)`.
- `{}` still raises the existing missing-status message with `field=status`.
- `{"status": ["not-ok"]}` still raises the existing malformed status-type message with `expected=str, actual=list`.
- Explicit non-ok string statuses still raise `WikidotStatusCodeException`, and `no_application` still maps to `NotFoundException`.
- The malformed payload branch decodes the response JSON once, preserves cached members, and does not include raw response data.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: A caller may have relied on raw `TypeError` from malformed synthetic responses. Mitigation: the public module expects a status-bearing result object, and repo validation style consistently routes malformed generated response shape through contextual `NoElementException`.
- Risk: This could be confused with raw AMC response validation. Mitigation: Issue 403 covers the raw connector response envelope; this slice only covers the application action payload consumed by `SiteApplication._process(...)`.
- Risk: This could hide raw payload details useful for debugging. Mitigation: the diagnostic includes site, user, user ID, event, action type, expected type, and actual type while avoiding raw response data that could contain private membership details.

## Dependencies

- Site application action responses remain expected to decode as JSON objects with string `status`.
- `WikidotStatusCodeException` remains responsible for explicit non-ok string statuses.
- `NoElementException` remains the parser/data-shape exception for malformed module response payloads.

## Open Questions

None for this local slice. Similar non-mapping action-payload guards may be useful on site-member mutation helpers, but that surface should receive its own duplicate check against the existing action-status and status-type issue series before implementation.

## Rationale for Upstream Suitability

The patch is small, local, and consistent with existing wikidot.py response-shape diagnostics. It improves failure classification for malformed site application action responses without changing successful accept/decline behavior, request construction, login checks, missing-application mapping, or existing status-code behavior.

## Local Evidence

- Local rollout-backed membership drafts established site applications, application-list acquisition, application moderation, member-cache invalidation, and membership administration as practical workflow surfaces.
- Existing local drafts covered missing application action status context, present non-string application action status values, raw connector envelope status typing, application user/site/text validation, retained user ID validation, retained site/client validation, and accept-cache invalidation. They did not cover a decoded application action response payload that is not a mapping before status lookup.
- This slice only validates site application action payload shape. It does not change request construction, login checks, retry behavior, application-list parsing, site invitation handling, site member role changes, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw membership content, raw response bodies, private site data, and private source text out of upstream discussion.
