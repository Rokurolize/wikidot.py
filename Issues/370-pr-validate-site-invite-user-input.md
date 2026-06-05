# PR Draft: Validate Site.invite_user User Inputs

## Summary

`Site.invite_user(user, text)` documents `user` as a `User`, but malformed caller-provided values were not rejected at the public API boundary. A non-`User` value could pass text validation, run the login check, and then leak raw attribute errors such as `AttributeError: 'dict' object has no attribute 'id'` during `user_id` payload construction. A malformed `User` with `id=None`, `id=True`, or `name=None` could reach login and AMC work without any stable invitation-recipient validation failure.

This change validates the site invitation target user before login checks or AMC request construction. Invalid values now raise `ValueError("user must be a User")`, `ValueError("user.id must be an integer")`, or `ValueError("user.name must be a string")`. Valid invitations, invitation text validation, login-required behavior, action-status diagnostics, duplicate-invitation mappings, request payload shape, and successful no-return behavior remain unchanged.

## Outcome

Site invitation callers now get deterministic Python-side preflight validation for malformed invitation targets instead of login work, accidental invitation attempts, raw attribute errors, or action-status diagnostics built around invalid user metadata.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `Site.invite_user(...)` for site administration, member onboarding, moderation workflows, migration notifications, audit-driven membership operations, or generated invitation jobs.

## Current Evidence

Local rollout evidence repeatedly treats site membership and administration as practical workflow surfaces. Existing drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md), [271-pr-site-application-accept-member-cache-invalidation.md](271-pr-site-application-accept-member-cache-invalidation.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [356-pr-validate-site-invite-text-input.md](356-pr-validate-site-invite-text-input.md), and [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md) establish site membership reads, pending applications, invitation actions, permission changes, cache synchronization, and membership input validation as practical surfaces.

Those prior slices are not duplicates. They covered membership/application reads, parser and response-body diagnostics, returned invitation action-status validation, member group action-status validation, application accept/decline action-status validation, role/member cache invalidation, invitation `text` validation, and member lookup username validation. They did not validate the public `Site.invite_user(user=...)` argument before login checks, `user_id` payload construction, AMC submission, or user-based invitation diagnostics. This slice follows the recipient identity input-boundary pattern from [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md), but applies it to site membership invitations.

## Related Issue

Builds directly on [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), [356-pr-validate-site-invite-text-input.md](356-pr-validate-site-invite-text-input.md), and [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `user` is a `User` before login checks or membership invitation action requests.
- Validate `user.id` is a non-boolean integer before using it as the `user_id` payload field.
- Validate `user.name` is a string before it can appear in returned invitation action-status diagnostics and duplicate-invitation mappings.
- Keep `text` preflight validation before login checks.
- Preserve successful `ManageSiteMembershipAction` payload shape, `event: "inviteMember"`, `user_id`, `text`, `moduleName: "Empty"`, returned action-status validation, `already_invited` and `already_member` mappings, explicit other-error reraising, and no-return successful invitations.

## Type Of Change

- Input validation
- Public API behavior hardening
- Site membership invitation preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.invite_user(user=...)` must reject non-`User` values with `ValueError("user must be a User")` before login checks or AMC requests. |
| R2 | `Site.invite_user(user=User(id=None or bool, ...))` must reject invalid invitation target IDs with `ValueError("user.id must be an integer")` before login checks or AMC requests. |
| R3 | `Site.invite_user(user=User(name=None, ...))` must reject invalid invitation target names with `ValueError("user.name must be a string")` before login checks or AMC requests. |
| R4 | Valid invitations, invitation text validation, login-required behavior, action-status diagnostics, duplicate-invitation mappings, and request payload shape must remain unchanged. |
| R5 | Adjacent site member, site application, and user workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private member data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent site/member/application/user tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-`User` invitation targets fail before login or AMC request work. | `TestSiteInviteUser.test_invite_user_rejects_non_user_before_login` failed RED before the fix with raw `AttributeError`, then passed GREEN after validation was added. | Calling `site.client.login_check()`, calling `site.client.amc_client.request(...)`, coercing dicts/mocks into invite targets, or leaking attribute errors rejects this local completion claim. | Site invitation preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | `User` invite targets without a real integer ID fail before login or AMC request work. | `TestSiteInviteUser.test_invite_user_rejects_malformed_user_before_login` failed RED for `id=None` and `id=True` because the malformed users did not raise `ValueError`, then passed GREEN after ID validation was added. | Submitting `user_id=None`, submitting `user_id=True`, treating bool as an integer user ID, or accepting the invitation call rejects this local completion claim. | Invitation target ID preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | `User` invite targets without a string name fail before login or AMC request work. | `TestSiteInviteUser.test_invite_user_rejects_malformed_user_before_login` failed RED for `name=None` because the malformed user did not raise `ValueError`, then passed GREEN after name validation was added. | Building action-status diagnostics or duplicate-invitation messages around `user.name=None`, calling login, calling AMC, or accepting the invitation call rejects this local completion claim. | Invitation target diagnostic preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R4 | Valid invitations and existing invitation diagnostics remain unchanged. | `TestSiteInviteUser` passed 11 tests, including successful invitations, text validation, login-required behavior, missing returned status, duplicate-invitation mappings, and other-error reraising. | Regressing `text` validation, `ManageSiteMembershipAction`, `event=inviteMember`, `user_id`, `text`, `moduleName=Empty`, missing-status diagnostics, `already_invited`, `already_member`, or other status handling rejects this local completion claim. | Site invitation behavior | `tests/unit/test_site.py` |
| R5 | Adjacent site administration and user workflows remain green. | `tests/unit/test_site.py::TestSiteInviteUser tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py` passed 94 tests, and the full unit suite passed 1046 tests. | Regressing member-list reads, member role changes, application list parsing, application accept/decline actions, user profile lookup, or invitation action-status handling rejects this local completion claim. | Site administration workflows | adjacent site/member/application/user tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic users and no live membership state. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw action responses, real invitation messages, private member data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `b044baa fix(site): validate invite user input`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_rejects_non_user_before_login tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_rejects_malformed_user_before_login` failed before the fix with 4 failures: the non-`User` target leaked `AttributeError: 'dict' object has no attribute 'id'`, and malformed `User` values did not raise `ValueError`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_rejects_non_user_before_login tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_rejects_malformed_user_before_login` passed 4 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteInviteUser` passed 11 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteInviteUser tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py` passed 94 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1046 tests.
- `.venv/bin/ruff check src/wikidot/module/site.py tests/unit/test_site.py` passed.
- `.venv/bin/ruff format --check src/wikidot/module/site.py tests/unit/test_site.py` passed with 2 files already formatted.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `site.invite_user({"id": 12345, "name": "test-user"}, "Welcome")` raises `ValueError("user must be a User")` before `site.client.login_check()` or `site.client.amc_client.request(...)`.
- `site.invite_user(User(client, id=None, name="test-user"), "Welcome")` raises `ValueError("user.id must be an integer")` before login or AMC work.
- `site.invite_user(User(client, id=True, name="test-user"), "Welcome")` raises `ValueError("user.id must be an integer")` before login or AMC work.
- `site.invite_user(User(client, id=12345, name=None), "Welcome")` raises `ValueError("user.name must be a string")` before login or AMC work.
- Valid invitations still call `site.client.login_check()` and still submit `ManageSiteMembershipAction` with `event: "inviteMember"`, `user_id`, `text`, and `moduleName: "Empty"`.
- Existing `text` validation, login-required behavior, missing action-status diagnostics, duplicate-invitation mappings, other-error reraising, site member workflows, site application workflows, and user workflows remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private member data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Site invitations are non-retried membership mutation actions. The target user supplies the remote `user_id` and the human-readable diagnostic name for returned action-status failures and duplicate-invitation mappings, so malformed target inputs should fail deterministically before login or AMC work. The change is narrow: it keeps valid invitation behavior and existing invitation response diagnostics unchanged while preventing accidental invitations or misleading diagnostics from malformed caller-provided user values.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established site membership reads, site application reads/actions, invitation action-status validation, member permission-change validation, cache invalidation, and invitation text validation as practical workflows.
- The focused RED failures showed malformed invitation target values crossing into login, payload construction, or successful request handling instead of failing at the public call boundary.
- Existing site invitation drafts covered returned action-status validation and invitation text validation, but not malformed public `user` input preflight.
- This slice only validates `Site.invite_user(user=...)`. It does not change member-list parsing, site application parsing, site application accept/decline actions, member permission changes, returned invitation action-status validation, text validation, client authentication, live Wikidot behavior, or user dataclass fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw action response bodies, real invitation messages, private member data, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that load invitation target IDs or names from JSON, YAML, CLI flags, generated structures, spreadsheets, or environment variables should resolve them into a real `User` object before calling wikidot.py site invitation helpers.
