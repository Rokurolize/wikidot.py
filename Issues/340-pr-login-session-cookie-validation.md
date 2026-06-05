# PR Draft: Reject Empty Login Session Cookies

## Summary

`HTTPAuthentication.login(...)` validates the HTTP status, credential-mismatch text, and presence of the `WIKIDOT_SESSION_ID` cookie before storing that cookie on the AMC request header. One authentication boundary remained under-validated: a response that included the cookie key with an empty or whitespace-only value was accepted and installed as the active session cookie.

This change rejects blank `WIKIDOT_SESSION_ID` values with `SessionCreateException("Login attempt is failed because WIKIDOT_SESSION_ID cookie is empty")` before mutating the client header. Valid non-empty session cookies continue to be stored unchanged.

## Outcome

Login no longer converts a structurally present but unusable session cookie into authenticated client state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who rely on `Client(username=..., password=...)` or `HTTPAuthentication.login(...)` before running authenticated page, forum, membership, private-message, or sandbox workflows.

## Current Evidence

Local rollout evidence repeatedly uses wikidot.py as a login reference for Wikidot sandbox and SPECA/FTML oracle work. Those workflows depend on reliable session establishment before any authenticated action can be trusted. The existing login tests already covered successful login, invalid credentials, HTTP errors, and a missing session-cookie key, but not a present empty session-cookie value.

## Related Issue

Builds on the existing sensitive-cookie handling in [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), which treats `WIKIDOT_SESSION_ID` as secret material in diagnostics, and on authenticated action-boundary drafts such as [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), which established that authenticated operations should fail before unnecessary downstream work.

No upstream issue was filed from this local workspace.

## Changes

- Validate that `WIKIDOT_SESSION_ID` is non-empty after stripping whitespace.
- Raise `SessionCreateException` before calling `set_cookie(...)` when the cookie value is blank.
- Preserve existing missing-cookie, invalid-credential, HTTP-status, successful login, and logout behavior.
- Add a focused unit regression proving blank session cookies are rejected without mutating the AMC header.

## Type Of Change

- Authentication-boundary validation fix
- State-mutation guard
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A login response without `WIKIDOT_SESSION_ID` must keep raising the existing invalid-cookie `SessionCreateException`. |
| R2 | A login response with a blank or whitespace-only `WIKIDOT_SESSION_ID` must raise `SessionCreateException` before storing the cookie. |
| R3 | A valid non-empty `WIKIDOT_SESSION_ID` must still be stored on the AMC header unchanged. |
| R4 | The new diagnostic must not include username, password, session-cookie value, raw response body text, local rollout paths, account material, cookies, or auth JSON. |
| R5 | Focused, auth, adjacent connector/client, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Missing session-cookie keys still raise the existing `"invalid cookies"` failure. | Existing `test_login_no_session_cookie` stayed green in the auth suite. | Rewording or weakening the missing-cookie guard rejects this local completion claim. | Login cookie boundary | `tests/unit/test_auth.py` |
| R2 | Whitespace-only `WIKIDOT_SESSION_ID` raises `"WIKIDOT_SESSION_ID cookie is empty"` and does not call `set_cookie(...)`. | `TestHTTPAuthentication.test_login_blank_session_cookie_fails_without_setting_cookie` uses a mocked login response with `"   "`. | Installing a blank cookie, returning success, or leaking a lower-level error rejects this local completion claim. | Login state mutation guard | `src/wikidot/module/auth.py`, `tests/unit/test_auth.py` |
| R3 | Successful login still stores the valid session ID exactly as before. | Existing `test_login_success` stayed green. | Trimming or otherwise rewriting valid non-empty session cookies without a separate requirement rejects this local completion claim. | AMC request header | `tests/unit/test_auth.py` |
| R4 | The exception text is compact and contains no sensitive fields or raw payloads. | The new message names only the cookie field and emptiness condition. | Including username, password, the cookie value, raw response text, local account names, rollout paths, cookies, or auth JSON rejects this local completion claim. | Diagnostic privacy | `src/wikidot/module/auth.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, auth passed 7 tests, adjacent connector/client passed 73 tests, full unit passed 915 tests, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `b12a344 fix(auth): reject empty session cookies`.

- RED: `uv run --extra test pytest tests/unit/test_auth.py::TestHTTPAuthentication::test_login_blank_session_cookie_fails_without_setting_cookie -q` failed before the fix because no `SessionCreateException` was raised.
- GREEN: `uv run --extra test pytest tests/unit/test_auth.py::TestHTTPAuthentication::test_login_blank_session_cookie_fails_without_setting_cookie -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_auth.py -q` passed 7 tests.
- `uv run --extra test pytest tests/unit/test_auth.py tests/unit/test_client.py tests/unit/test_ajax.py tests/unit/test_amc_client.py -q` passed 73 tests.
- `uv run --extra test pytest tests/unit -q` passed 915 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- Missing session cookies keep the existing invalid-cookie behavior.
- Blank or whitespace-only session cookies are rejected before the client header is mutated.
- Valid session cookies continue to be stored unchanged.
- Logout behavior remains unchanged.
- The new exception text does not include username, password, session-cookie value, raw response body text, local rollout paths, local account names, sandbox details, credentials, cookies, auth JSON, or private site data.
- No live Wikidot action, upstream Issue, upstream PR, push, real login response body, credentials, cookies, auth JSON, or account material is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Authentication should not succeed on a response that only appears to contain a session cookie. Treating an empty session cookie as authenticated state can make later failures look like page, forum, or permission problems instead of a login/session-establishment problem. Rejecting the blank value at login keeps downstream authenticated workflows clearer without changing valid login behavior.

## Local Evidence, Not For Upstream Paste

- Local sandbox and oracle workflows repeatedly use wikidot.py as the login reference before authenticated Wikidot probes.
- The focused RED failure showed the current login path accepting a whitespace-only session cookie and calling `set_cookie(...)`.
- This slice only validates the session-cookie value before header mutation; it does not perform a live login, alter credentials handling, change retry policy, change request payloads, or inspect real response bodies.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, and private site data out of upstream discussion.

## Additional Notes

This slice intentionally does not add session-refresh behavior, parse additional login response fields, change the credential-mismatch text check, change login retry limits, trim stored non-empty cookie values, or alter logout. It only prevents blank `WIKIDOT_SESSION_ID` values from becoming client state.
