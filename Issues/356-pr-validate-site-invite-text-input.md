# PR Draft: Validate Site.invite_user Text Input Before Login

## Summary

`Site.invite_user(user, text)` documents `text` as a string invitation message, but malformed non-string values were not rejected at the public API boundary. Because the method used `@login_required`, invalid values reached the login check before any stable input validation, and after login they could be placed into the `ManageSiteMembershipAction` invitation payload.

This change validates `text` before login checks, invitation request construction, AMC submission, returned action-status parsing, or invite-success acceptance. Invalid values now raise `ValueError("text must be a string")`. Valid invitations, login-required behavior, action-status diagnostics, and request payload shape remain unchanged.

## Outcome

Browser-free site membership invitation callers now get deterministic Python-side preflight validation for malformed invitation messages instead of login work, remote invitation attempts, or downstream action-status errors.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `Site.invite_user(...)` for site administration, member onboarding, moderation workflows, migration notifications, or audit-driven membership operations.

## Current Evidence

Local rollout evidence repeatedly treats site membership and administration as practical workflow surfaces. Existing drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), and [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md) establish site membership reads, pending applications, invitation actions, permission changes, and action-status validation as practical surfaces.

Those prior slices are not duplicates. They covered membership/application reads, parser and response-body diagnostics, returned invitation action-status validation, member group action-status validation, and application accept/decline action-status validation. They did not validate public invitation `text` inputs before login checks or request construction. This slice follows the input-boundary pattern from [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), and [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), but applies it to site membership invitations.

## Related Issue

Builds directly on [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), and [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `Site.invite_user(text=...)` before login checks or membership invitation action requests.
- Move the login check inside `Site.invite_user(...)` after validation so valid invitations keep the same login-required behavior while invalid text fails earlier.
- Reuse the existing page text-field validator already used by site page create/publish helpers.
- Preserve successful `ManageSiteMembershipAction` payload shape, `event: "inviteMember"`, `user_id`, `text`, returned action-status validation, `already_invited` and `already_member` mappings, explicit other-error reraising, and no-return successful invitations.

## Type Of Change

- Input validation
- Public API behavior hardening
- Site membership invitation preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.invite_user(..., text=...)` must reject non-string text values with `ValueError("text must be a string")` before login checks or AMC requests. |
| R2 | Valid invitations must keep the existing login-required behavior and request payload shape. |
| R3 | Existing missing action-status diagnostics and non-`ok` status mappings must remain unchanged for valid text inputs. |
| R4 | Adjacent site member and site application workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent site/member/application tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-string invitation messages fail before side effects. | `TestSiteInviteUser.test_invite_user_rejects_non_string_text_before_login` failed RED before the fix because the invalid value did not raise `ValueError`, then passed GREEN after validation was added. | Calling `login_check()`, calling `amc_client.request(...)`, accepting the malformed payload, or leaking action-status exceptions rejects this local completion claim. | Site invitation preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Valid invitation behavior remains unchanged. | Focused GREEN included `test_invite_user_success` and `test_invite_user_not_logged_in`; adjacent site/member/application tests passed 71 tests. | Losing the login-required exception for valid inputs, changing `ManageSiteMembershipAction`, changing `event=inviteMember`, changing `user_id`, changing `text`, changing `moduleName=Empty`, or returning a new value rejects this local completion claim. | Site invitation behavior | `tests/unit/test_site.py` |
| R3 | Existing invitation response diagnostics remain unchanged. | Focused GREEN included missing action-status handling; adjacent invitation tests covered `already_invited`, `already_member`, and other error reraising. | Accepting missing status, changing site/user/event/field context, swallowing non-`ok` statuses, or reclassifying non-`ok` statuses as `ValueError` rejects this local completion claim. | Site invitation response boundary | `tests/unit/test_site.py` |
| R4 | Site member and site application workflows remain green. | `TestSiteInviteUser`, `tests/unit/test_site_member.py`, and `tests/unit/test_site_application.py` passed 71 tests; the full unit suite passed 964 tests. | Regressing member-list reads, member role changes, application list parsing, application accept/decline actions, or site invite action-status handling rejects this local completion claim. | Site administration workflows | affected site/member/application tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw action responses, invitation text from real sites, private member data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent site/member/application tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `a939e33 fix(site): validate invite text input`.

- Environment note: direct system `PYTHONPATH=src pytest ...` could not collect `tests/unit/test_site.py` because `pytest_httpx` was not installed in the system interpreter, so behavior verification used the repository virtualenv.
- RED: `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_rejects_non_string_text_before_login` failed before the fix because invalid `text` did not raise `ValueError`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_rejects_non_string_text_before_login tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_success tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_not_logged_in tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_missing_action_status_includes_site_user_event_and_field_context` passed 4 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteInviteUser tests/unit/test_site_member.py tests/unit/test_site_application.py` passed 71 tests.
- `ruff format src/wikidot/module/site.py tests/unit/test_site.py` left 2 files unchanged.
- `ruff check src/wikidot/module/site.py tests/unit/test_site.py` passed.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `.venv/bin/python -m pytest -q tests/unit` passed 964 tests.
- `ruff check .` passed.
- `ruff format --check .` passed with 81 files already formatted.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `site.invite_user(user, text=3)` raises `ValueError("text must be a string")` before calling `site.client.login_check()` or `site.client.amc_client.request(...)`.
- Valid invitations still call `site.client.login_check()` and still submit `ManageSiteMembershipAction` with `event: "inviteMember"`, `user_id`, `text`, and `moduleName: "Empty"`.
- Logged-out valid invitations still raise `LoginRequiredException`.
- Missing returned invitation action status still raises contextual `NoElementException`.
- `already_invited` still maps to `TargetErrorException`.
- `already_member` still maps to `TargetErrorException`.
- Other non-`ok` invitation statuses still reraises `WikidotStatusCodeException`.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Site invitations are non-retried membership mutation actions. Runtime validation should reject malformed invitation messages before login checks or request construction, so caller configuration errors cannot trigger remote invitation work or confusing downstream action-status failures. The change is narrow: it keeps valid invitation semantics and existing action-status diagnostics unchanged.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established site membership reads, site application reads/actions, invitation action-status validation, member permission-change validation, and response-body diagnostics as practical surfaces.
- The focused RED failure showed malformed invite text crossing the public call boundary without a stable validation failure.
- Existing site invitation drafts covered returned action-status validation, but not malformed public `Site.invite_user(text=...)` inputs.
- This slice only validates site invitation text inputs. It does not change member-list parsing, site application parsing, site application accept/decline actions, member permission changes, returned invitation action-status validation, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw action response bodies, real invitation messages, private member data, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that load invitation messages from JSON, YAML, CLI flags, generated structures, spreadsheets, or environment variables should normalize them to strings before calling `Site.invite_user(...)`.
