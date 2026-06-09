# PR Draft: Validate Site Application Action Status Type

## Summary

`SiteApplication.accept()` and `SiteApplication.decline()` route through `SiteApplication._process(...)`, decode the `ManageSiteMembershipAction` response, and require `status` before treating the application action as complete. Issue [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md) covered missing status context and explicit non-ok string statuses, but present non-string values such as `{"status": ["not-ok"]}` were still routed into `WikidotStatusCodeException` as if they were real Wikidot status codes. This change rejects malformed generated response data before accepting the application action result.

## Outcome

Site application accept/decline workflows now distinguish malformed action-response shape from real Wikidot status-code failures, preserving existing string-status behavior while surfacing type-corrupt generated responses with site, user, event, action type, field, and type context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free site application review, membership moderation, migration, generated-fixture, or administration workflows where application action responses may come from synthetic tests, recorded traffic, adapters, or generated data.

## Current Evidence

Local rollout-backed drafts already identify site applications and membership administration as practical shared workflows. Existing drafts [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [155-pr-site-application-mismatch-context.md](155-pr-site-application-mismatch-context.md), [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [271-pr-site-application-accept-member-cache-invalidation.md](271-pr-site-application-accept-member-cache-invalidation.md), [308-pr-site-application-user-context.md](308-pr-site-application-user-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md), [449-pr-validate-site-application-user-field.md](449-pr-validate-site-application-user-field.md), [450-pr-validate-site-application-text-field.md](450-pr-validate-site-application-text-field.md), [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md), [606-pr-validate-site-application-user-client.md](606-pr-validate-site-application-user-client.md), [687-pr-validate-site-application-user-id-range.md](687-pr-validate-site-application-user-id-range.md), [689-pr-validate-site-application-constructor-user-id-range.md](689-pr-validate-site-application-constructor-user-id-range.md), and [699-pr-validate-site-application-constructor-user-id-state.md](699-pr-validate-site-application-constructor-user-id-state.md) cover application acquisition, response reuse, text behavior, parser diagnostics, body-shape diagnostics, accept/decline behavior, cache synchronization, user/site/text validation, and missing/non-ok action status behavior.

Adjacent membership action drafts [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md) and [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md) establish the same status-bearing action-response pattern for invitations and member role changes. Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) is not a duplicate: it covers raw Ajax Module Connector response status typing before module-level dispatch. Issues [714-pr-validate-page-save-status-type.md](714-pr-validate-page-save-status-type.md) and [715-pr-validate-private-message-send-status-type.md](715-pr-validate-private-message-send-status-type.md) are also not duplicates: they cover separate module-level action payloads. This slice validates the site-application action response consumed by `SiteApplication._process(...)`. No upstream issue was filed from this local workspace.

## Changes

- Add a type guard in the site-application action status extractor.
- Raise `NoElementException` for a present non-string `status` with site, user, user ID, event, action type, field, expected type, and actual type context.
- Preserve the Issue 256 missing-status diagnostic.
- Preserve explicit non-ok string handling through `WikidotStatusCodeException`, including the existing `no_application` mapping.
- Add a focused regression proving malformed status types are decoded once, leave the member cache untouched, and are rejected as malformed action-response shape.

## Type Of Change

- Response-shape validation
- Site application action hardening
- Generated response data diagnostics
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteApplication.accept(...)` and the shared `_process(...)` path must reject a non-string action response `status` with `NoElementException` containing site, user, user ID, event, action type, `field=status`, `expected=str`, and the actual type. |
| R2 | A missing `status` field must keep the existing Issue 256 missing-status diagnostic. |
| R3 | Explicit non-ok string statuses must still raise `WikidotStatusCodeException` and must not be reclassified as malformed shape. |
| R4 | The malformed status path must decode the response body once and must not clear the cached member list. |
| R5 | Adjacent site application parsing and action behavior must remain green. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `{"status": ["not-ok"]}` fails with malformed site-application action status context before completion is accepted. | `test_accept_malformed_action_status_type_includes_site_user_event_type_and_type_context` failed RED with `WikidotStatusCodeException`, then passed GREEN after status typing was added. | Treating a list, dict, number, or object as a Wikidot status code rejects this local completion claim. | Site application action response shape | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R2 | `{}` still raises the Issue 256 missing-status message with site, user, id, event, action type, and field context. | `test_accept_missing_action_status_includes_site_user_event_type_and_field_context` passed unchanged. | Changing the missing-status exception type, dropping context, or masking it behind status-code handling rejects this local completion claim. | Site application missing field handling | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R3 | `{"status": "other_error"}` still routes through `WikidotStatusCodeException`. | `test_accept_explicit_non_ok_action_status_raises_status_exception` passed unchanged. | Reclassifying non-ok strings as malformed response shape rejects this local completion claim. | Site application status-code handling | `tests/unit/test_site_application.py` |
| R4 | The malformed status path decodes the response JSON once and leaves `site._members` unchanged. | The new regression asserts `mock_response.json.call_count == 1` and cache identity preservation. | Reintroducing duplicate decode work or clearing member caches on malformed response shape rejects this local completion claim. | Site application response decoding/cache safety | `tests/unit/test_site_application.py` |
| R5 | Adjacent site application behavior remains stable. | `TestSiteApplicationProcess` passed 22 tests and `tests/unit/test_site_application.py` passed 69 tests. | Regressing application list parsing, accept/decline payloads, invalid action handling, cache behavior, user/site/text validation, or parser diagnostics rejects this local completion claim. | Site application workflows | `tests/unit/test_site_application.py` |
| R6 | No live site state or private material is needed to prove the behavior. | The regression uses synthetic unit-level response bodies and mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private content, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `d846bdd fix(site_application): validate action status type`.

- RED: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_malformed_action_status_type_includes_site_user_event_type_and_type_context -q` failed before the fix with `WikidotStatusCodeException` instead of the expected malformed-shape `NoElementException`.
- GREEN focused: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_missing_action_status_includes_site_user_event_type_and_field_context tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_explicit_non_ok_action_status_raises_status_exception tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_malformed_action_status_type_includes_site_user_event_type_and_type_context -q` passed 3 tests.
- `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationProcess -q` passed 22 tests.
- `uv run pytest tests/unit/test_site_application.py -q` passed 69 tests.
- `uv run ruff format src/wikidot/module/site_application.py tests/unit/test_site_application.py` left both files unchanged.
- `uv run ruff check src/wikidot/module/site_application.py tests/unit/test_site_application.py` passed.
- `git diff --check` passed.

## Acceptance Criteria

- `{"status": ["not-ok"]}` raises `NoElementException` with site, user, id, event, action type, `field=status`, `expected=str`, and `actual=list` context.
- `{}` still raises the existing missing-status message from Issue 256.
- `{"status": "other_error"}` still raises `WikidotStatusCodeException`.
- The malformed non-string status path still decodes the response JSON once and does not clear `site._members`.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A caller may have relied on a non-string `status` object being formatted into a `WikidotStatusCodeException`. Mitigation: Wikidot action statuses are strings, Issue 403 already validates raw AMC statuses as strings, and module-level action responses should reject malformed generated data before business handling.
- Risk: This could be confused with raw AMC response typing. Mitigation: Issue 403 covers the raw connector response envelope; this slice covers the site-application action payload used by `SiteApplication._process(...)`.
- Risk: This could be confused with adjacent module-level status typing. Mitigation: Issues 714 and 715 cover page save and private-message send respectively; this slice covers site application accept/decline actions.
- Risk: Tightening action response shape could hide legitimate non-ok Wikidot string statuses. Mitigation: non-ok strings are deliberately preserved on the existing `WikidotStatusCodeException` path.
- Risk: The error could become too generic for generated fixtures. Mitigation: the diagnostic names the site, user, id, event, action type, field, expected type, and actual type.

## Dependencies

- Existing `SiteApplication._process(...)` remains responsible for accept/decline orchestration.
- Existing `WikidotStatusCodeException` handling remains responsible for explicit non-ok string statuses.
- Existing `NoElementException` remains the parser/data-shape exception for missing or malformed response fields.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered site-application action status type path.

## Upstream-Safe Motivation

`SiteApplication._process(...)` treats accept/decline action responses as status-bearing action payloads. Rejecting malformed status types at that boundary keeps generated or adapted response data from masquerading as a real Wikidot status code and makes application moderation failures easier to diagnose.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established site application reads, accept/decline actions, generated-fixture, migration, membership administration, and moderation workflows as practical consumers of site-application behavior.
- Existing application and raw AMC drafts covered missing action status context, explicit non-ok action strings, and raw connector envelope status typing; they did not validate the module-level site-application action status type.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, application text from real sites, and source text from real sites out of upstream discussion.
