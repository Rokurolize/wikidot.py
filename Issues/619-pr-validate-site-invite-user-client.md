# PR Draft: Validate Site Invite User Client

## Summary

`Site.invite_user(user, text)` already validates invitation text and, through Issue 370, validates that the invitation target is a well-formed `User` with a usable ID and name. One adjacent mutation-boundary gap remained: a valid `User` object from a different `Client` context could still be passed to a `Site` and progress into login, AMC request construction, and action-status handling under the site's client.

This change validates invitation target/client coherence after existing text and user-shape checks but before `site.client.login_check()` or `ManageSiteMembershipAction` request construction. Mismatched invitation targets now raise `ValueError("user must belong to the site")`. Valid same-client invitations, malformed text precedence, malformed user-shape precedence, request payload shape, login-required behavior for valid users, returned invitation action-status diagnostics, duplicate-invitation mappings, and adjacent membership workflows remain unchanged.

## Outcome

Site invitation calls can no longer submit a `user_id` from a user object retained under a different client context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `Site.invite_user(...)` for site administration, member onboarding, moderation workflows, migration notifications, audit-driven membership operations, generated invitation jobs, or browser-free membership tooling.

## Current Evidence

Local rollout-backed drafts repeatedly identify site membership and administration actions as practical workflow surfaces. Existing drafts [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [356-pr-validate-site-invite-text-input.md](356-pr-validate-site-invite-text-input.md), [370-pr-validate-site-invite-user-input.md](370-pr-validate-site-invite-user-input.md), [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md), [605-pr-validate-site-member-user-client.md](605-pr-validate-site-member-user-client.md), [606-pr-validate-site-application-user-client.md](606-pr-validate-site-application-user-client.md), and [614-pr-validate-private-message-send-recipient-client.md](614-pr-validate-private-message-send-recipient-client.md) establish membership mutations, invitation inputs, application/member user-client coherence, and adjacent recipient/client preflights as active operational boundaries.

This is not a duplicate of Issue 370. Issue 370 validates malformed invitation target shape: non-`User` values, malformed `user.id`, and malformed `user.name`. This slice validates a well-formed `User` whose retained `user.client` differs from `site.client`.

This is not a duplicate of Issues 605 or 606. Those validate stored `SiteMember.user` and `SiteApplication.user` coherence in member/application records and actions. This slice validates the direct `Site.invite_user(...)` recipient before an invitation mutation can be sent.

This is not a duplicate of Issue 614. Issue 614 validates private-message send recipient/client coherence. This slice applies the same direct mutation-boundary principle to site membership invitations and preserves the existing site invitation payload and action-status behavior.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_site_invitation_user_site(...)`.
- Reject `Site.invite_user(site_client, User(client=other_client, ...), text)` with `ValueError("user must belong to the site")`.
- Run the new coherence check after existing text and user-shape validation and before login or AMC request work.
- Add a focused RED/GREEN regression proving a different-client `User` is rejected before `login_check()` and request construction.
- Preserve valid invitations, malformed text/user precedence, returned action-status diagnostics, duplicate-invitation mappings, and adjacent member/application/user workflows.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `site.invite_user(User(client=other_client, id=12345, name="test-user"), "Welcome")` must raise `ValueError("user must belong to the site")` when `other_client is not site.client`. |
| R2 | The mismatch check must run before `site.client.login_check()`, `site.amc_request(...)`, or `site.client.amc_client.request(...)`. |
| R3 | Existing malformed text and malformed user-shape diagnostics must keep their current precedence. |
| R4 | Valid same-client invitations must keep the same `ManageSiteMembershipAction` payload and returned action-status behavior. |
| R5 | Site invitation, site member, site application, user lookup, and adjacent site workflows must remain green. |
| R6 | Full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Different-client invite targets fail at the public mutation boundary. | `TestSiteInviteUser.test_invite_user_rejects_user_from_different_client_before_login` failed RED with `DID NOT RAISE`, then passed GREEN after `Site.invite_user(...)` called the user/client coherence preflight. | Accepting the different-client user, submitting its ID, or deferring the mismatch to action-status handling rejects this local completion claim. | `Site.invite_user(...)` | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | The failure happens before side effects. | The regression asserts the site's `login_check()` and AMC request mock are not called. | Reaching login, reaching AMC request construction, or relying on a returned response to detect the mismatch rejects this local completion claim. | Invitation preflight ordering | `tests/unit/test_site.py` |
| R3 | Existing malformed input precedence remains stable. | `TestSiteInviteUser` passed 12 tests, including non-string text, non-`User` targets, malformed target IDs, and malformed target names. | Changing `ValueError("text must be a string")`, `ValueError("user must be a User")`, `ValueError("user.id must be an integer")`, or `ValueError("user.name must be a string")` rejects this local completion claim. | Input validation precedence | `tests/unit/test_site.py` |
| R4 | Valid invitations and response diagnostics remain unchanged. | `TestSiteInviteUser` passed success, missing-status, already-invited, already-member, login-required, and other-error tests. | Changing action, event, user_id, text, moduleName, returned status diagnostics, duplicate mappings, or other-error reraising rejects this local completion claim. | Site invitation behavior | `tests/unit/test_site.py` |
| R5 | Adjacent membership and user workflows remain green. | `uv run pytest tests/unit/test_site.py::TestSiteInviteUser tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py -q` passed 213 tests. | Regressing member reads/actions, application reads/actions, user records, user lookup, or invitation behavior rejects this local completion claim. | Site administration workflows | `tests/unit` |
| R6 | Repository quality gates remain green. | Full unit coverage passed 2778 tests; full ruff check, full format check, mypy, pyright, and `git diff --check` passed. | Any unreported test, lint, format, type, or whitespace failure rejects this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live auth material or private state is needed to prove the behavior. | The regression uses synthetic `Site`, `Client`, and `User` objects; this draft contains no credentials, cookies, auth JSON, raw response bodies, private usernames, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private membership data, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `8cf16fa fix(site): validate invite user client`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_rejects_user_from_different_client_before_login -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused: the same command passed after the invitation user/client preflight was added.
- Invitation coverage: `uv run pytest tests/unit/test_site.py::TestSiteInviteUser -q` passed 12 tests.
- Adjacent site administration coverage: `uv run pytest tests/unit/test_site.py::TestSiteInviteUser tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py -q` passed 213 tests.
- `uv run pytest tests/unit -q` passed 2778 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `site.invite_user(User(client=other_client, id=12345, name="test-user"), "Welcome")` raises `ValueError("user must belong to the site")` before login or AMC request work.
- `site.invite_user(User(client=site.client, id=12345, name="test-user"), "Welcome")` remains valid and submits the same invitation payload.
- Existing non-string text still raises `ValueError("text must be a string")`.
- Existing non-`User` targets still raise `ValueError("user must be a User")`.
- Existing malformed user IDs and names still raise `ValueError("user.id must be an integer")` or `ValueError("user.name must be a string")`.
- Existing invitation success, missing action-status diagnostics, already-invited mapping, already-member mapping, login-required behavior, other-error reraising, site member workflows, site application workflows, and user workflows remain green.
- The new tests use unit-level synthetic state only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Site invitations are direct membership mutation actions. The target `User` supplies both the remote `user_id` and human-readable diagnostic name while the `Site` supplies the authenticated client and action route. Requiring the invite target to belong to the same client context prevents generated fixtures, cached user objects, mixed-client scripts, or rehydrated records from issuing invitations with an incoherent object graph, without changing valid same-client invitations or returned response handling.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed a valid `User` from another `Client` object could be accepted by `Site.invite_user(...)` and reach the existing success path.
- Existing local drafts covered invitation text validation, malformed invitation target validation, invitation action-status diagnostics, site member/application user-client coherence, private-message send recipient/client coherence, and user record-client validation, but did not cover direct invitation target/client coherence.
- This slice only validates direct `Site.invite_user(...)` target/client coherence. It does not change member-list parsing, site application parsing, site application accept/decline actions, member permission changes, returned invitation action-status validation, text validation, malformed target-shape validation, client authentication, live Wikidot behavior, or user dataclass fields for valid users.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw action response bodies, real invitation messages, private member data, private-message content, and private site data out of upstream discussion.

## Additional Notes

The check intentionally compares retained client object identity. A site invitation should be issued through the same client context that produced or owns the target user object, matching neighboring membership and private-message send coherence rules.
