# PR Draft: Validate Site.invite_user Action Status Before Accepting Invitation Success

## Summary

`Site.invite_user(...)` sends Wikidot's `inviteMember` action through `ManageSiteMembershipAction`. The method already maps explicit `already_invited` and `already_member` statuses to `TargetErrorException`, but it previously accepted a decoded action response without `status` as success because the lower-level AMC connector only raises for non-`ok` statuses when the `status` field is present.

This follow-up validates the returned `inviteMember` action status inside `Site.invite_user(...)`. A missing `status` raises `NoElementException` with site, user, user ID, event, and field context. Explicit non-`ok` statuses still flow through `WikidotStatusCodeException`, preserving the existing `already_invited` and `already_member` user-facing mappings. Successful `status: ok` invitations and request payload construction remain unchanged.

## Related Issue

Builds on the membership and action-status hardening drafts around [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md), [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), and [252-pr-forum-category-create-thread-action-status-context.md](252-pr-forum-category-create-thread-action-status-context.md). Those drafts established site membership workflows and non-retried action responses as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Validate the returned `inviteMember` action response before treating `Site.invite_user(...)` as successful.
- Convert a missing invitation action `status` into `NoElementException` with site unix name, user name, user ID, event, and field context.
- Preserve explicit non-`ok` status handling through `WikidotStatusCodeException`.
- Preserve the existing `already_invited` and `already_member` mappings to `TargetErrorException`.
- Add a focused public-interface regression for malformed site invitation responses.
- Preserve login checks, request payload construction, successful invitation behavior, and other status re-raise behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Site membership invitation action response validation
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A site invitation response missing `status` fails with contextual `NoElementException`. | `TestSiteInviteUser.test_invite_user_missing_action_status_includes_site_user_event_and_field_context` returns `{}` from the invite action response and asserts `NoElementException`. | Treating the response as successful, raising a raw `KeyError`, or omitting invite context rejects this local completion claim. |
| The malformed action-status message identifies site, user, user ID, event, and missing field. | The focused regression asserts `Site invitation action response is malformed for site: test, user: test-user (id=12345, event=inviteMember, field=status)`. | Omitting site unix name, user name, user ID, event, or field context makes the failure ambiguous and rejects this local completion claim. |
| Explicit duplicate-invitation statuses keep the existing user-facing mappings. | `TestSiteInviteUser` still covers `already_invited` and `already_member` as `TargetErrorException`. | Converting those statuses into generic `WikidotStatusCodeException` or `NoElementException` rejects this local completion claim. |
| Successful invite behavior remains unchanged. | `TestSiteInviteUser.test_invite_user_success` passes and still asserts `ManageSiteMembershipAction`, `inviteMember`, and `user_id` payload fields. | Regressions in login checks, request payload shape, user ID submission, or successful no-return behavior reject this local completion claim. |
| Adjacent membership workflows remain unchanged. | `uv run --extra test pytest tests/unit/test_site.py::TestSiteInviteUser tests/unit/test_site_member.py tests/unit/test_site_application.py -q` passed 56 tests. | Regressions in member permission changes, application accept/decline, membership parsing, or invitation status mapping reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `578f334 fix(site): guard invite action status`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_missing_action_status_includes_site_user_event_and_field_context -q` failed before the fix with `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>`.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_missing_action_status_includes_site_user_event_and_field_context -q` passed.
- `uv run --extra test pytest tests/unit/test_site.py::TestSiteInviteUser -q` passed 6 tests.
- `uv run --extra test pytest tests/unit/test_site.py -q` passed 75 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSiteInviteUser tests/unit/test_site_member.py tests/unit/test_site_application.py -q` passed 56 tests.
- `uv run --extra test pytest tests/unit -q` passed 803 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Site.invite_user(...)` raises `NoElementException` when the returned `inviteMember` action response lacks `status`.
- The malformed-response message includes site `unix_name`, user name, user ID, action event, and missing field.
- Explicit non-`ok` invitation-action statuses are not treated as successful invitations.
- Existing `already_invited` and `already_member` statuses still raise `TargetErrorException`.
- Successful invitation paths keep the existing login check, request payload shape, user ID submission, invitation text submission, and no-return behavior.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Site invitations are a non-retried membership mutation workflow. Callers should not accept an unclassified Wikidot response as a successful invitation merely because the response object decoded without crashing. Validating the returned action status makes the invitation boundary consistent with the nearby forum mutation action guards and gives operators a compact site/user/event signal when Wikidot omits the required status field.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established membership reads, application actions, and site membership parsing as practical local surfaces.
- Issues 250 through 252 established the adjacent action-status pattern for non-retried forum mutation helpers.
- This slice intentionally targets only `Site.invite_user(...)`; site member permission changes, site application accept/decline, and private-message send actions remain separate action boundaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, invitation text from real sites, page source text, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not retry site invitation writes, change request construction, add per-action result objects, change member lookup behavior, touch site member permission mutation helpers, touch site application accept/decline helpers, touch private-message send behavior, or modify live Wikidot behavior. It only validates the returned `inviteMember` action response before accepting `Site.invite_user(...)` as successful.
