# PR Draft: Validate SiteMember Permission Change Action Status Before Accepting Success

## Summary

`SiteMember.to_moderator()`, `remove_moderator()`, `to_admin()`, and `remove_admin()` route through `SiteMember._change_group(...)`, which sends Wikidot's `ManageSiteMembershipAction` permission-change events. The method already maps explicit `not_already`, `already_admin`, and `already_moderator` statuses to `TargetErrorException`, but it previously accepted a decoded action response without `status` as success because the lower-level AMC connector only raises for non-`ok` statuses when the `status` field is present.

This follow-up validates the returned member permission-change action status inside `SiteMember._change_group(...)`. A missing `status` raises `NoElementException` with site, user, user ID, event, and field context. Explicit non-`ok` statuses still flow through `WikidotStatusCodeException`, preserving the existing `TargetErrorException` mappings. Successful `status: ok` permission changes and request payload construction remain unchanged.

## Related Issue

Builds on the membership workflow drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), and [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md). Those drafts established membership reads, invitations, and adjacent non-retried mutation actions as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Validate the returned site member permission-change action response before treating group changes as successful.
- Convert a missing member action `status` into `NoElementException` with site unix name, user name, user ID, event, and field context.
- Preserve explicit non-`ok` status handling through `WikidotStatusCodeException`.
- Preserve the existing `not_already`, `already_admin`, and `already_moderator` mappings to `TargetErrorException`.
- Add a focused public-interface regression through `SiteMember.to_moderator(...)`.
- Preserve login checks, request payload construction, user ID submission, successful no-return behavior, and the four permission-change wrapper methods.

## Type Of Change

- Bug fix / diagnostics improvement
- Site member permission-change action response validation
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A site member permission-change response missing `status` fails with contextual `NoElementException`. | `TestSiteMemberChangeGroup.test_change_group_missing_action_status_includes_site_user_event_and_field_context` returns `{}` from the `toModerators` action response and asserts `NoElementException`. | Treating the response as successful, raising a raw `KeyError`, or omitting member context rejects this local completion claim. |
| The malformed action-status message identifies site, user, user ID, event, and missing field. | The focused regression asserts `Site member action response is malformed for site: test-site, user: TestUser (id=12345, event=toModerators, field=status)`. | Omitting site unix name, user name, user ID, event, or field context makes the failure ambiguous and rejects this local completion claim. |
| Existing permission status mappings remain unchanged. | `TestSiteMemberChangeGroup` still covers `not_already`, `already_admin`, and `already_moderator` as `TargetErrorException`. | Converting those statuses into generic `WikidotStatusCodeException` or `NoElementException` rejects this local completion claim. |
| Successful permission-change behavior remains unchanged. | `TestSiteMemberChangeGroup` passes with `status: ok` for `to_moderator()`, `remove_moderator()`, `to_admin()`, and `remove_admin()` and still asserts event and user ID payload fields. | Regressions in login checks, request payload shape, event names, user ID submission, or successful no-return behavior reject this local completion claim. |
| Adjacent membership workflows remain unchanged. | `uv run --extra test pytest tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_site.py::TestSiteInviteUser -q` passed 57 tests. | Regressions in member reads, application parsing/actions, or invitation status handling reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `f31b977 fix(site_member): guard change group action status`.

- RED: `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_missing_action_status_includes_site_user_event_and_field_context -q` failed before the fix with `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>`.
- GREEN: `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_missing_action_status_includes_site_user_event_and_field_context -q` passed.
- `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup -q` passed 11 tests.
- `uv run --extra test pytest tests/unit/test_site_member.py -q` passed 31 tests.
- `uv run --extra test pytest tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_site.py::TestSiteInviteUser -q` passed 57 tests.
- `uv run --extra test pytest tests/unit -q` passed 806 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `SiteMember.to_moderator(...)` raises `NoElementException` when the returned permission-change action response lacks `status`.
- The malformed-response message includes site `unix_name`, user name, user ID, action event, and missing field.
- Explicit non-`ok` member-action statuses are not treated as successful permission changes.
- Existing `not_already`, `already_admin`, and `already_moderator` statuses still raise `TargetErrorException`.
- Successful permission-change paths keep the existing login check, request payload shape, event names, user ID submission, and no-return behavior.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Site member permission changes are non-retried membership mutation workflows. Callers should not accept an unclassified Wikidot response as a successful role change merely because the response object decoded without crashing. Validating the returned action status makes member permission changes consistent with invitations and nearby action-status guards, and gives operators a compact site/user/event signal when Wikidot omits the required status field.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established member-list reads, site application reads/actions, and site invitation writes as practical local surfaces.
- Issues 250 through 254 established the adjacent action-status pattern for non-retried forum, membership, and private-message mutation helpers.
- This slice intentionally targets only `SiteMember._change_group(...)`; site application accept/decline actions remain a separate action boundary.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, private member names from real sites, page source text, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not retry site member permission changes, change request construction, add per-action result objects, change member-list parsing, touch site invitations, touch site application accept/decline helpers, touch private-message send behavior, or modify live Wikidot behavior. It only validates the returned `ManageSiteMembershipAction` permission-change response before accepting `SiteMember._change_group(...)` as successful.
