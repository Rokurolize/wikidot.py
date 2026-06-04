# PR Draft: Validate SiteApplication Accept/Decline Action Status Before Accepting Success

## Summary

`SiteApplication.accept()` and `SiteApplication.decline()` route through `SiteApplication._process(...)`, which sends Wikidot's `ManageSiteMembershipAction` with the `acceptApplication` event and an action-specific `type`. The helper already maps explicit `no_application` failures to `NotFoundException`, but it previously accepted any decoded action response object as success when the lower-level AMC connector did not raise.

This follow-up validates the returned site-application action status before treating accept or decline as complete. A missing `status` raises `NoElementException` with site, user, user ID, event, action type, and field context. Explicit non-`ok` statuses still flow through `WikidotStatusCodeException`, preserving the existing `no_application` to `NotFoundException` mapping. Successful `status: ok` accept/decline behavior and request payload construction remain unchanged.

## Related Issue

Builds on the pending-application workflow drafts [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), and [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md). Those drafts established site applications, invitations, and member role changes as practical membership workflow surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Validate the returned `SiteApplication._process(...)` action response before treating application accept/decline as successful.
- Convert a missing application action `status` into `NoElementException` with site unix name, user name, user ID, event, action type, and field context.
- Preserve explicit non-`ok` status handling through `WikidotStatusCodeException`.
- Preserve the existing `no_application` mapping to `NotFoundException`.
- Add focused public-interface regressions through `SiteApplication.accept(...)`.
- Preserve login checks, request payload construction, accepted/declined notification text, successful no-return behavior, invalid action handling, and the public `accept()`/`decline()` wrappers.

## Type Of Change

- Bug fix / diagnostics improvement
- Site application accept/decline action response validation
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A site application accept response missing `status` fails with contextual `NoElementException`. | `TestSiteApplicationProcess.test_accept_missing_action_status_includes_site_user_event_type_and_field_context` returns `{}` from the action response and asserts `NoElementException`. | Treating the response as successful, raising a raw `KeyError`, or omitting site/user/action context rejects this local completion claim. |
| The malformed action-status message identifies site, user, user ID, event, action type, and missing field. | The focused regression asserts `Site application action response is malformed for site: test-site, user: TestUser (id=12345, event=acceptApplication, type=accept, field=status)`. | Omitting site unix name, user name, user ID, event, action type, or field context makes the failure ambiguous and rejects this local completion claim. |
| Explicit non-`ok` action statuses are not treated as successful accept/decline actions. | `TestSiteApplicationProcess.test_accept_explicit_non_ok_action_status_raises_status_exception` returns `{"status": "other_error"}` and asserts `WikidotStatusCodeException.status_code == "other_error"`. | Returning successfully, swallowing the status, or reclassifying it as `NoElementException` rejects this local completion claim. |
| Existing `no_application` behavior remains unchanged. | `TestSiteApplicationProcess.test_process_application_not_found` still maps `WikidotStatusCodeException("no_application")` to `NotFoundException`. | Converting missing applications into a generic status exception rejects this local completion claim. |
| Successful accept/decline behavior remains unchanged. | `TestSiteApplicationProcess.test_accept_success` and `test_decline_success` pass with `status: ok` fixtures and still assert action payload fields, type, user ID, and decline notification text. | Regressions in login checks, request payload shape, `acceptApplication` event, `type`, user ID submission, or notification text reject this local completion claim. |
| Adjacent membership workflows remain unchanged. | `uv run --extra test pytest tests/unit/test_site_application.py tests/unit/test_site_member.py tests/unit/test_site.py::TestSiteInviteUser -q` passed 59 tests. | Regressions in application parsing/actions, member role changes, or invitations reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `08432b6 fix(site_application): guard process action status`.

- RED: `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_missing_action_status_includes_site_user_event_type_and_field_context -q` failed before the fix with `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>`.
- GREEN: `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_missing_action_status_includes_site_user_event_type_and_field_context tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_success tests/unit/test_site_application.py::TestSiteApplicationProcess::test_decline_success tests/unit/test_site_application.py::TestSiteApplicationProcess::test_process_application_not_found -q` passed 4 tests.
- `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationProcess -q` passed 8 tests.
- `uv run --extra test pytest tests/unit/test_site_application.py -q` passed 22 tests.
- `uv run --extra test pytest tests/unit/test_site_application.py tests/unit/test_site_member.py tests/unit/test_site.py::TestSiteInviteUser -q` passed 59 tests.
- `uv run --extra test pytest tests/unit -q` passed 808 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `SiteApplication.accept(...)` raises `NoElementException` when the returned application action response lacks `status`.
- The malformed-response message includes site `unix_name`, user name, user ID, action event, action type, and missing field.
- Explicit non-`ok` application action statuses are not treated as successful accept/decline actions.
- Existing `no_application` status handling still maps to `NotFoundException`.
- Successful accept and decline paths keep the existing login check, request payload shape, `acceptApplication` event, `type`, user ID submission, notification text, and no-return behavior.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Site application accept/decline operations are non-retried membership mutation workflows. Callers should not accept an unclassified Wikidot response as proof that an applicant was accepted or declined merely because the response object decoded without crashing. Validating the returned action status makes application processing consistent with invitations and member role changes, and gives operators a compact site/user/event/type signal when Wikidot omits the required status field.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established pending-application reads, application text parsing, site invitations, and site member role changes as practical membership workflow surfaces.
- Issues 253 through 255 established the adjacent action-status pattern for non-retried membership and private-message mutation helpers.
- This slice intentionally targets only `SiteApplication._process(...)`; list parsing, site invitations, site member permission changes, and private-message send actions remain separate boundaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, application text from real sites, member names from real sites, page source text, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not retry site application mutation actions, change request construction, add per-action result objects, change application-list parsing, touch site invitations, touch site member permission mutation helpers, touch private-message send behavior, or modify live Wikidot behavior. It only validates the returned `ManageSiteMembershipAction` response before accepting `SiteApplication._process(...)` as successful.
