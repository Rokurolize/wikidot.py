# PR Draft: Validate SiteApplication Applicant Inputs

## Summary

`SiteApplication.accept()` and `SiteApplication.decline()` build a `ManageSiteMembershipAction` request from the stored `SiteApplication.user`, but the process path did not validate that applicant object before authentication work or AMC payload construction. A non-user value could pass through the login check and then leak raw attribute errors such as `AttributeError: 'dict' object has no attribute 'id'`. A malformed `User` with `id=None`, `id=True`, or `name=None` could reach AMC/status handling without a deterministic applicant validation failure.

This change validates the stored application applicant before login checks or AMC request construction. Invalid values now raise `ValueError("application.user must be an AbstractUser")`, `ValueError("application.user.id must be an integer")`, or `ValueError("application.user.name must be a string")`. Valid accept/decline actions, login-required behavior for valid applicants, action-status diagnostics, `no_application` mapping, member-cache invalidation on successful accept, and decline cache preservation remain unchanged.

## Outcome

Site application mutation callers now get deterministic Python-side preflight validation for malformed applicants instead of login work, accidental mutation attempts, raw attribute errors, or action-status diagnostics built around invalid user metadata.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using site-application moderation workflows, membership approval jobs, generated admin tools, or audit-driven site administration scripts.

## Current Evidence

Local rollout evidence repeatedly treats site applications and membership administration as practical workflow surfaces. Existing drafts [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [271-pr-site-application-accept-member-cache-invalidation.md](271-pr-site-application-accept-member-cache-invalidation.md), [308-pr-site-application-user-context.md](308-pr-site-application-user-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), and [370-pr-validate-site-invite-user-input.md](370-pr-validate-site-invite-user-input.md) establish application listing, applicant parsing, accept/decline mutation, response diagnostics, cache synchronization, and adjacent membership input validation as practical surfaces.

Those prior slices are not duplicates. They covered application-list fetch retries, application body parsing, application response-body diagnostics, applicant parser diagnostics during acquisition, accept/decline returned action-status validation, accept cache invalidation, and invitation target validation. They did not validate the already-stored `SiteApplication.user` object before accept/decline login checks, `user_id` payload construction, AMC submission, or user-based action diagnostics. This slice follows the identity input-boundary pattern from [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md) and [370-pr-validate-site-invite-user-input.md](370-pr-validate-site-invite-user-input.md), but keeps the application field type as `AbstractUser` to match the dataclass contract.

## Related Issue

Builds directly on [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [271-pr-site-application-accept-member-cache-invalidation.md](271-pr-site-application-accept-member-cache-invalidation.md), [308-pr-site-application-user-context.md](308-pr-site-application-user-context.md), and [370-pr-validate-site-invite-user-input.md](370-pr-validate-site-invite-user-input.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `SiteApplication.user` is an `AbstractUser` before login checks or site-application mutation requests.
- Validate `application.user.id` is a non-boolean integer before using it as the `user_id` payload field.
- Validate `application.user.name` is a string before it can appear in action-status diagnostics or `no_application` context.
- Preserve successful `ManageSiteMembershipAction` payload shape, `event: "acceptApplication"`, `type: "accept"`/`"decline"`, status validation, and `no_application` handling.
- Preserve successful accept cache invalidation for `site._members` and decline cache preservation.

## Type Of Change

- Input validation
- Public workflow behavior hardening
- Site application mutation preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteApplication.accept()` and `SiteApplication.decline()` must reject non-`AbstractUser` applicant values with `ValueError("application.user must be an AbstractUser")` before login checks or AMC requests. |
| R2 | Applicant values with `id=None` or boolean IDs must reject with `ValueError("application.user.id must be an integer")` before login checks or AMC requests. |
| R3 | Applicant values with non-string names must reject with `ValueError("application.user.name must be a string")` before login checks or AMC requests. |
| R4 | Valid accept/decline actions, login-required behavior for valid applicants, action-status diagnostics, `no_application` mapping, request payload shape, accept member-cache invalidation, and decline cache preservation must remain unchanged. |
| R5 | Adjacent site invitation, site member, and user workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private member data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, affected site-application tests, adjacent site/application/user tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-`AbstractUser` applicants fail before login or AMC request work. | `TestSiteApplicationProcess.test_accept_rejects_non_user_before_login` failed RED before the fix with raw `AttributeError`, then passed GREEN after validation was added. | Calling `site.client.login_check()`, calling `site.amc_request(...)`, coercing dicts/mocks into applicants, or leaking attribute errors rejects this local completion claim. | Site application applicant preflight | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R2 | Applicants without a real integer ID fail before login or AMC request work. | `TestSiteApplicationProcess.test_accept_rejects_malformed_user_before_login` failed RED for `id=None` and `id=True` because malformed users reached AMC/status handling, then passed GREEN after ID validation was added. | Submitting `user_id=None`, submitting `user_id=True`, treating bool as an integer user ID, or accepting/declining the application rejects this local completion claim. | Site application applicant ID preflight | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R3 | Applicants without a string name fail before login or AMC request work. | `TestSiteApplicationProcess.test_accept_rejects_malformed_user_before_login` failed RED for `name=None` because the malformed user reached AMC/status handling, then passed GREEN after name validation was added. | Building action-status diagnostics around `application.user.name=None`, calling login, calling AMC, or accepting/declining the application rejects this local completion claim. | Site application applicant diagnostic preflight | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R4 | Valid application mutations and existing diagnostics remain unchanged. | `tests/unit/test_site_application.py` passed 30 tests, including successful accept/decline, invalid actions, login-required behavior, missing returned status, non-ok returned status, `no_application`, other-error reraising, accept cache invalidation, and decline cache preservation. | Regressing `ManageSiteMembershipAction`, `event=acceptApplication`, `type=accept/decline`, `user_id`, status validation, `no_application`, accept cache invalidation, decline cache behavior, or valid login-required behavior rejects this local completion claim. | Site application mutation behavior | `tests/unit/test_site_application.py` |
| R5 | Adjacent site administration and user workflows remain green. | `tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_user.py` passed 157 tests, and the full unit suite passed 1050 tests. | Regressing invitation behavior, member workflows, user profile lookup, application list parsing, or application mutation handling rejects this local completion claim. | Site administration workflows | adjacent and full unit tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic users and mocked site/client objects. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw action responses, private member data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `2a186cd fix(site_application): validate application user input`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_rejects_non_user_before_login tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_rejects_malformed_user_before_login` failed before the fix with 4 failures: the non-user applicant leaked `AttributeError: 'dict' object has no attribute 'id'`, and malformed `User` values reached AMC/status handling instead of raising `ValueError`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_rejects_non_user_before_login tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_rejects_malformed_user_before_login` passed 4 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_site_application.py` passed 30 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_user.py` passed 157 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1050 tests.
- `.venv/bin/ruff check src/wikidot/module/site_application.py tests/unit/test_site_application.py` passed.
- `.venv/bin/ruff format --check src/wikidot/module/site_application.py tests/unit/test_site_application.py` passed with 2 files already formatted.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `SiteApplication(site, {"id": 12345, "name": "test-user"}, "").accept()` raises `ValueError("application.user must be an AbstractUser")` before `site.client.login_check()` or `site.amc_request(...)`.
- `SiteApplication(site, User(client, id=None, name="test-user"), "").accept()` raises `ValueError("application.user.id must be an integer")` before login or AMC work.
- `SiteApplication(site, User(client, id=True, name="test-user"), "").accept()` raises `ValueError("application.user.id must be an integer")` before login or AMC work.
- `SiteApplication(site, User(client, id=12345, name=None), "").accept()` raises `ValueError("application.user.name must be a string")` before login or AMC work.
- Valid accept/decline actions still call `site.client.login_check()` and still submit `ManageSiteMembershipAction` with `event: "acceptApplication"`, `user_id`, `type`, notification text, and `moduleName: "Empty"`.
- Existing invalid-action behavior, login-required behavior for valid applicants, missing action-status diagnostics, non-ok status handling, `no_application` mapping, other-error reraising, accept member-cache invalidation, decline cache preservation, site invitation workflows, site member workflows, and user workflows remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private member data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Site application accept/decline actions are membership mutation operations. The applicant supplies the remote `user_id` and the human-readable diagnostic name for returned action-status failures, so malformed stored applicant values should fail deterministically before login or AMC work. The change is narrow: it keeps valid application moderation behavior and existing response diagnostics unchanged while preventing accidental actions or misleading diagnostics from malformed caller-provided or manually constructed `SiteApplication` objects.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established site application reads, accept/decline actions, action-status validation, cache invalidation, applicant parser diagnostics, and adjacent site invitation validation as practical workflows.
- The focused RED failures showed malformed application applicant values crossing into login, payload construction, or status handling instead of failing at the mutation boundary.
- Existing site application drafts covered acquisition-time parser diagnostics, response-body diagnostics, action-status validation, and cache invalidation, but not malformed stored applicant preflight before accept/decline mutations.
- This slice only validates `SiteApplication.user` before accept/decline mutation requests. It does not change application list parsing, invitation behavior, member permission changes, client authentication, live Wikidot behavior, or user dataclass fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw action response bodies, real application messages, private member data, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that construct `SiteApplication` objects manually should pass a parsed `AbstractUser` with a concrete integer `id` and string `name` before calling `accept()` or `decline()`.
