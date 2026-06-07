# PR Draft: Validate Login Credential Types

## Summary

`HTTPAuthentication.login(client, username, password)` documents `username` and `password` as strings, but malformed caller-provided values could reach login request construction and successful mocked login handling. Non-string usernames and passwords such as `None`, integers, and booleans were accepted into the request `data` payload instead of failing at the authentication boundary.

This change validates login credential types before reading client retry configuration, building headers, issuing the HTTP POST, inspecting returned cookies, or mutating the client's `WIKIDOT_SESSION_ID` header state. Invalid values now raise `ValueError("username must be a string")` or `ValueError("password must be a string")`. Valid string credentials, retry settings, HTTP status handling, invalid-credential response handling, session-cookie validation, cookie storage, logout behavior, and adjacent client/Ajax/request utility workflows remain unchanged.

## Outcome

Malformed login credential values now fail locally before request work or cookie mutation, while ordinary string login attempts continue through the existing retry-aware login flow.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who construct `Client(username=..., password=...)` or call `HTTPAuthentication.login(...)` from browser-free automation, sandbox setup scripts, account bootstrap checks, CI fixtures, or local test harnesses.

## Current Evidence

Authentication drafts [340-pr-login-session-cookie-validation.md](340-pr-login-session-cookie-validation.md) and header/request-state drafts [398-pr-validate-amc-cookie-names.md](398-pr-validate-amc-cookie-names.md), [399-pr-validate-amc-cookie-values.md](399-pr-validate-amc-cookie-values.md), and [400-pr-validate-amc-header-values.md](400-pr-validate-amc-header-values.md) establish login/session and request-header state as practical safety boundaries. They validate returned session-cookie and header state, not caller-provided login credential types.

Input-boundary drafts such as [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), [359-pr-validate-site-lookup-unix-names.md](359-pr-validate-site-lookup-unix-names.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), and [497-pr-validate-quickmodule-request-arguments.md](497-pr-validate-quickmodule-request-arguments.md) establish the local pattern that documented public inputs should fail before request construction or side effects.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 340. Issue 340 validates a returned `WIKIDOT_SESSION_ID` cookie after a login response; this slice validates caller-provided `username` and `password` values before the login request is made.

This is not a duplicate of Issues 398, 399, or 400. Those slices validate cookie/header fields in shared request-header state; this slice validates login credentials before those headers are read or mutated.

This is not a duplicate of page/forum/private-message input validation slices. Those cover workflow-specific public inputs before page/forum/PM request construction; this slice applies the same boundary principle to the authentication login helper.

No upstream issue was filed from this local workspace.

## Changes

- Add a small authentication-boundary text validator for login fields.
- Validate `username` and `password` at the start of `HTTPAuthentication.login(...)`.
- Preserve valid string login attempts and existing login failure diagnostics.
- Add parameterized auth tests for malformed username and password values.
- Assert malformed credentials do not call `httpx.post(...)` and do not set the session cookie.

## Type Of Change

- Input validation
- Authentication request preflight hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `HTTPAuthentication.login(..., username=...)` must reject non-string usernames with `ValueError("username must be a string")` before request work. |
| R2 | `HTTPAuthentication.login(..., password=...)` must reject non-string passwords with `ValueError("password must be a string")` before request work. |
| R3 | Malformed credential rejection must not call `httpx.post(...)` or mutate the `WIKIDOT_SESSION_ID` cookie. |
| R4 | Valid login success, invalid credential response handling, HTTP status failures, missing/blank session-cookie failures, logout behavior, and adjacent client/Ajax/request utility workflows must remain unchanged. |
| R5 | This slice must not validate credential content, reject empty strings, log raw credentials, require live Wikidot actions, credentials, cookies, auth JSON, raw response bodies, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, auth tests, adjacent auth/client/Ajax/request utility tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-string usernames fail with stable `ValueError` before login request work. | `TestHTTPAuthentication.test_login_rejects_non_string_credentials_before_request` failed RED for `None`, `123`, and `True` username values because no `ValueError` was raised, then passed GREEN after validation was added. | Accepting non-string usernames, coercing them to strings, reading request config first, or issuing HTTP POST rejects this local completion claim. | Login preflight | `src/wikidot/module/auth.py`, `tests/unit/test_auth.py` |
| R2 | Non-string passwords fail with stable `ValueError` before login request work. | The same parameterized test failed RED for `None`, `123`, and `True` password values because no `ValueError` was raised, then passed GREEN after validation was added. | Accepting non-string passwords, coercing them to strings, reading request config first, or issuing HTTP POST rejects this local completion claim. | Login preflight | `src/wikidot/module/auth.py`, `tests/unit/test_auth.py` |
| R3 | Invalid credential values do not issue requests or set cookies. | The GREEN test asserts patched `httpx.post` is not called and `set_cookie` is not called for every malformed credential case. | Calling the HTTP POST, setting `WIKIDOT_SESSION_ID`, deleting cookies, or logging credential values rejects this local completion claim. | Authentication side effects | `tests/unit/test_auth.py` |
| R4 | Existing auth and adjacent request workflows remain green. | `tests/unit/test_auth.py` passed 13 tests, adjacent auth/client/Ajax/request utility tests passed 157 tests, and full unit passed 2305 tests. | Regressing valid login, invalid credential response mapping, HTTP status mapping, missing/blank cookie diagnostics, logout cleanup, client initialization/accessors, Ajax masking/header behavior, or RequestUtil behavior rejects this local completion claim. | Auth and adjacent workflows | `tests/unit` |
| R5 | No private material or live action is needed to prove the behavior. | All regressions use synthetic credential values and patched local HTTP responses; the draft contains no raw credentials, cookies, auth JSON, or response bodies. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, raw login response bodies, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, auth tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `42f0a0e fix(auth): validate login credentials`.

- RED credential tests: `uv run pytest tests/unit/test_auth.py::TestHTTPAuthentication::test_login_rejects_non_string_credentials_before_request -q` failed 6 malformed credential cases before the fix with `DID NOT RAISE`.
- GREEN credential tests: the same focused command passed 6 tests after credential type validation was added.
- `uv run pytest tests/unit/test_auth.py -q` passed 13 tests.
- `uv run pytest tests/unit/test_auth.py tests/unit/test_client.py tests/unit/test_ajax.py tests/unit/test_requestutil.py -q` passed 157 tests.
- `uv run ruff format src/wikidot/module/auth.py tests/unit/test_auth.py` reformatted the test file and left the source file unchanged.
- `uv run ruff format --check src/wikidot/module/auth.py tests/unit/test_auth.py` passed with 2 files already formatted.
- `uv run ruff check src/wikidot/module/auth.py tests/unit/test_auth.py` passed.
- `uv run mypy src/wikidot/module/auth.py tests/unit/test_auth.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/auth.py tests/unit/test_auth.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2305 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `HTTPAuthentication.login(client, None, "password")`, `123`, and `True` for `username` raise `ValueError("username must be a string")` before request work or cookie mutation.
- `HTTPAuthentication.login(client, "username", None)`, `123`, and `True` for `password` raise `ValueError("password must be a string")` before request work or cookie mutation.
- Valid string login attempts still call the existing retry-aware POST path and store a non-blank `WIKIDOT_SESSION_ID` cookie on success.
- Existing invalid username/password response detection still raises `SessionCreateException("Login attempt is failed due to invalid username or password")`.
- Existing HTTP status, missing session-cookie, blank session-cookie, and logout tests remain green.
- The new tests use unit-level synthetic credentials only and do not require live Wikidot, real credentials, cookies, auth JSON, raw response bodies, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Credential validation could be confused with credential content policy. Mitigation: this slice validates type only and intentionally does not reject empty strings or credential-like values; server-side login response handling remains authoritative for credential correctness.
- Risk: Tests could accidentally expose real credentials. Mitigation: all test values are synthetic and the regression patches the HTTP POST path.
- Risk: The guard could change valid login behavior. Mitigation: existing success, invalid credential, HTTP status, missing-cookie, blank-cookie, logout, and adjacent client/Ajax/request utility tests remain green.

## Out Of Scope

- Live login attempts, credential correctness, password strength, username syntax, empty-string rejection, account lockout policy changes, retry limit changes, logging changes, cookie-name/value validation, request-header validation, and client partial-credential behavior are outside this slice.

## Why This Matters

Authentication is the entry point for browser-free write and private-dashboard workflows. Type-invalid credential values should fail before request setup or cookie mutation so scripts that load credentials from JSON, YAML, environment adapters, generated config, or test fixtures get deterministic local diagnostics instead of sending malformed login payloads or silently creating authenticated-looking test state from bad input.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used authenticated browser-free workflows, client initialization, login/session setup, logout cleanup, session-cookie validation, Ajax masking, and request-header state as practical operational surfaces.
- Existing local drafts covered returned session-cookie validation, request-header validation, cookie-name/value validation, sensitive-log masking, and many workflow-specific input preflights, but did not cover malformed login credential types before the login POST path.
- The focused RED failures showed malformed credential values reaching successful mocked login behavior before the fix. The GREEN regression covers both fields before any patched HTTP POST or cookie mutation can run.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private content, and private site data out of upstream discussion.
