# PR Draft: Validate SiteMember Action Users

## Summary

`SiteMember.to_moderator()`, `SiteMember.remove_moderator()`, `SiteMember.to_admin()`, and `SiteMember.remove_admin()` build `ManageSiteMembershipAction` requests from the stored `SiteMember.user`, but the role-change path did not validate that user object before authentication work or AMC payload construction. A non-user value could pass the login check and then leak raw attribute errors such as `AttributeError: 'dict' object has no attribute 'id'`. A malformed `User` with `id=None`, `id=True`, or `name=None` could reach AMC/status handling without a deterministic member-action validation failure.

This change validates the stored site-member action user before login checks or AMC requests. Invalid values now raise `ValueError("member.user must be an AbstractUser")`, `ValueError("member.user.id must be an integer")`, or `ValueError("member.user.name must be a string")`. Valid role changes, login-required behavior for valid users, action-status diagnostics, `already_*`/`not_already` mappings, role-cache invalidation, and member-list parsing remain unchanged.

## Outcome

Site member role-change callers now get deterministic Python-side preflight validation for malformed stored users instead of login work, accidental mutation attempts, raw attribute errors, or action-status diagnostics built around invalid user metadata.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.members`, `Site.admins`, `Site.moderators`, direct `SiteMember.get(site, group)` results, or stored `SiteMember` objects for browser-free site administration.

## Current Evidence

Local rollout evidence repeatedly treats site membership administration as a practical workflow surface. Existing drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md), and [372-pr-validate-site-member-lookup-user-id.md](372-pr-validate-site-member-lookup-user-id.md) establish member acquisition, parser diagnostics, role-change response validation, role-cache synchronization, and member lookup as practical surfaces.

Those prior slices are not duplicates. They covered member-list fetch retries, row scoping, pager scoping, response-body diagnostics, parsed member-user diagnostics, joined-at diagnostics, returned action-status validation, cache invalidation, and direct member lookup input validation. They did not validate the already-stored `SiteMember.user` object before role-change login checks, `user_id` payload construction, AMC submission, or user-based returned-status diagnostics. This slice follows the identity input-boundary pattern from [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md), [370-pr-validate-site-invite-user-input.md](370-pr-validate-site-invite-user-input.md), and [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md), but keeps the member field type as `AbstractUser` to match the dataclass contract.

## Related Issue

Builds directly on [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md) and [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `SiteMember.user` is an `AbstractUser` before login checks or site-member role-change requests.
- Validate `member.user.id` is a non-boolean integer before using it as the `user_id` payload field.
- Validate `member.user.name` is a string before it can appear in returned-status diagnostics or mapped role-change errors.
- Preserve successful `ManageSiteMembershipAction` payload shape, `toModerators`/`removeModerator`/`toAdmins`/`removeAdmin` event values, status validation, mapped target errors, and role-cache invalidation.
- Preserve member-list parsing, site-member lookup, site invitation, and site-application workflows.

## Type Of Change

- Input validation
- Public workflow behavior hardening
- Site member mutation preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Role-change methods must reject non-`AbstractUser` stored member-user values with `ValueError("member.user must be an AbstractUser")` before login checks or AMC requests. |
| R2 | Stored member users with `id=None` or boolean IDs must reject with `ValueError("member.user.id must be an integer")` before login checks or AMC requests. |
| R3 | Stored member users with non-string names must reject with `ValueError("member.user.name must be a string")` before login checks or AMC requests. |
| R4 | Valid role-change actions, login-required behavior for valid users, action-status diagnostics, target-error mappings, request payload shape, and role-cache invalidation must remain unchanged. |
| R5 | Adjacent site-member reads, member lookup, site invitation, site application, and user workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private member data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, affected site-member tests, adjacent site/application tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-`AbstractUser` stored member users fail before login or AMC request work. | `TestSiteMemberChangeGroup.test_change_group_rejects_non_user_before_login` failed RED before the fix with raw `AttributeError`, then passed GREEN after validation was added. | Calling `site.client.login_check()`, calling `site.amc_request(...)`, coercing dictionaries into users, or leaking attribute errors rejects this local completion claim. | Site member action-user preflight | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R2 | Stored member users without real integer IDs fail before login or AMC request work. | `TestSiteMemberChangeGroup.test_change_group_rejects_malformed_user_before_login` failed RED for `id=None` and `id=True` because malformed users reached AMC/status handling, then passed GREEN after ID validation was added. | Submitting `user_id=None`, submitting `user_id=True`, treating bool as an integer user ID, or attempting the role change rejects this local completion claim. | Site member action-user ID preflight | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R3 | Stored member users without string names fail before login or AMC request work. | `TestSiteMemberChangeGroup.test_change_group_rejects_malformed_user_before_login` failed RED for `name=None` because the malformed user reached AMC/status handling, then passed GREEN after name validation was added. | Building action-status diagnostics around `member.user.name=None`, calling login, calling AMC, or attempting the role change rejects this local completion claim. | Site member action-user diagnostic preflight | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R4 | Valid role-change mutations and existing diagnostics remain unchanged. | `tests/unit/test_site_member.py::TestSiteMemberChangeGroup` passed 19 tests, including successful promotion/demotion, cache invalidation, invalid events, login-required behavior, mapped target errors, missing returned status, and other-error reraising. | Regressing `ManageSiteMembershipAction`, event names, `user_id`, status validation, target-error mappings, cache invalidation, or valid login-required behavior rejects this local completion claim. | Site member role-change behavior | `tests/unit/test_site_member.py` |
| R5 | Adjacent site administration workflows remain green. | `tests/unit/test_site_member.py tests/unit/test_site.py tests/unit/test_site_application.py` passed 225 tests, and the full unit suite passed 1450 tests. | Regressing member-list parsing, member lookup, invitation behavior, application handling, page/site helpers, or user workflows rejects this local completion claim. | Site administration workflows | adjacent and full unit tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic users and mocked site/client objects. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw action responses, private member data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `f0efcef fix(site_member): validate member action users`.

- RED: `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_rejects_non_user_before_login tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_rejects_malformed_user_before_login -q` failed before the fix with 4 failures: the non-user member leaked `AttributeError: 'dict' object has no attribute 'id'`, and malformed `User` values reached AMC/status handling instead of raising `ValueError`.
- GREEN: `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_rejects_non_user_before_login tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_rejects_malformed_user_before_login -q` passed 4 tests.
- `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup -q` passed 19 tests.
- `uv run --extra test pytest tests/unit/test_site_member.py tests/unit/test_site.py tests/unit/test_site_application.py -q` passed 225 tests.
- `uv run ruff format src/wikidot/module/site_member.py tests/unit/test_site_member.py` reformatted 1 file and left 1 file unchanged.
- `uv run --extra test pytest tests/unit -q` passed 1450 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `SiteMember(site, {"id": 12345, "name": "TestUser"}, None).to_moderator()` raises `ValueError("member.user must be an AbstractUser")` before `site.client.login_check()` or `site.amc_request(...)`.
- `SiteMember(site, User(client, id=None, name="TestUser"), None).to_moderator()` raises `ValueError("member.user.id must be an integer")` before login or AMC work.
- `SiteMember(site, User(client, id=True, name="TestUser"), None).to_moderator()` raises `ValueError("member.user.id must be an integer")` before login or AMC work.
- `SiteMember(site, User(client, id=12345, name=None), None).to_moderator()` raises `ValueError("member.user.name must be a string")` before login or AMC work.
- Valid promotion and demotion calls still call `site.client.login_check()` and still submit `ManageSiteMembershipAction` with the existing event values, `user_id`, and `moduleName: ""`.
- Existing invalid-event behavior, login-required behavior for valid users, missing action-status diagnostics, mapped `already_*`/`not_already` target errors, other-error reraising, role-cache invalidation, member-list reads, member lookup, invitation workflows, and application workflows remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private member data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Site member role changes are membership mutation operations. The stored member user supplies the remote `user_id` and the human-readable diagnostic name for returned action-status failures, so malformed stored member-user values should fail deterministically before login or AMC work. The change is narrow: it keeps valid role-change behavior and existing response diagnostics unchanged while preventing accidental actions or misleading diagnostics from malformed caller-provided or manually constructed `SiteMember` objects.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established site member reads, role changes, role-change returned-status validation, cache invalidation, direct member lookup, site invitation, and site-application processing as practical workflows.
- The focused RED failures showed malformed stored member-user values crossing into login, payload construction, or status handling instead of failing at the mutation boundary.
- Existing site-member drafts covered acquisition-time parser diagnostics, response-body diagnostics, returned action-status validation, cache invalidation, and lookup inputs, but not malformed stored member-user preflight before role-change mutations.
- This slice only validates `SiteMember.user` before role-change mutation requests. It does not change member-list parsing, member lookup, invitation behavior, site-application behavior, client authentication, live Wikidot behavior, or user dataclass fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw action response bodies, private member data, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that construct `SiteMember` objects manually should pass a parsed `AbstractUser` with a concrete integer `id` and string `name` before calling role-change helpers.
