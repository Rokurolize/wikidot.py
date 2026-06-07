# PR Draft: Validate Authentication Client Input

## Summary

`HTTPAuthentication.login(client, username, password)` and `HTTPAuthentication.logout(client)` are the direct browser-free authentication helpers behind `Client(...)` login and context/close cleanup. Earlier local slices validated login credential types, client partial credentials, auth login config-object state, auth header-object state, session-cookie values, and client accessor parent state. One adjacent public auth-input gap remained: direct calls such as `HTTPAuthentication.login(None, "test-user", "test-password")` or `HTTPAuthentication.logout(None)`, booleans, strings, dictionaries, or arbitrary objects reached `client.amc_client.config` or `client.amc_client.header` and leaked raw `AttributeError`.

This change validates the caller-provided `client` object after login credential validation, but before login config access, header access, HTTP request setup, session-cookie mutation, logout AMC request work, or logout cookie deletion. Malformed direct auth clients now raise `ValueError("client must be a Client")` deterministically, while existing credential validation precedence, config-object validation, header-object validation, login success/failure handling, session-cookie diagnostics, logout error suppression, and adjacent client/request/site workflows remain unchanged.

## Outcome

Direct authentication callers now get deterministic client validation before nested auth state reads or request work instead of incidental attribute errors from malformed client-like values.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call auth helpers directly, construct clients from generated configuration, run browser-free authenticated workflows, or use local fixtures where malformed authentication clients should fail before network or cookie side effects.

## Current Evidence

Local rollout-backed drafts repeatedly identify authentication, session setup, cookie/header state, and client construction as practical workflow surfaces. Existing drafts [340-pr-login-session-cookie-validation.md](340-pr-login-session-cookie-validation.md), [513-pr-validate-login-credential-types.md](513-pr-validate-login-credential-types.md), [514-pr-validate-client-partial-credentials.md](514-pr-validate-client-partial-credentials.md), [515-pr-validate-amc-config-object.md](515-pr-validate-amc-config-object.md), [520-pr-validate-amc-config-fields.md](520-pr-validate-amc-config-fields.md), [522-pr-validate-amc-request-state-objects.md](522-pr-validate-amc-request-state-objects.md), [524-pr-validate-auth-login-config-object.md](524-pr-validate-auth-login-config-object.md), [527-pr-validate-auth-header-object.md](527-pr-validate-auth-header-object.md), and [548-pr-validate-site-lookup-client.md](548-pr-validate-site-lookup-client.md) establish auth login, logout cleanup, session cookies, nested AMC state, and direct client validation as active operational boundaries.

This is not a duplicate of Issue 513. Issue 513 validates `username` and `password` values once `HTTPAuthentication.login(...)` is called. This slice preserves that precedence and validates the separate caller-provided `client` object only after credentials are known valid.

This is not a duplicate of Issue 524. Issue 524 validates replaced `client.amc_client.config` state after a usable client reaches login request setup. This slice validates the parent client object before `amc_client` or `config` is read.

This is not a duplicate of Issue 527. Issue 527 validates replaced `client.amc_client.header` state before login/logout header work. This slice validates the parent client object before `amc_client` or `header` is read.

This is not a duplicate of Issue 514 or Issue 479. Issue 514 validates `Client(...)` constructor credential-pair presence, and Issue 479 validates client accessor constructors. This slice covers direct static auth helper calls.

No upstream issue was filed from this local workspace.

## Changes

- Add focused regressions for malformed direct `HTTPAuthentication.login(client=...)` and `HTTPAuthentication.logout(client=...)` inputs.
- Add `_validate_auth_client(...)` and call it before auth nested state access.
- Update the auth test fixture to use an uninitialized real `Client` with synthetic AMC state so direct auth tests exercise the stricter public boundary without constructor side effects.
- Preserve login credential validation, config-object validation, header-object validation, login response diagnostics, session-cookie mutation, logout error suppression, and adjacent workflows.

## Type Of Change

- Input validation
- Public authentication-boundary hardening
- Login/logout preflight
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `HTTPAuthentication.login(None, "test-user", "test-password")`, `True`, `"test-client"`, `{"username": "test-user"}`, and `object()` must raise `ValueError("client must be a Client")` before config/header access or HTTP requests. |
| R2 | `HTTPAuthentication.logout(...)` must reject the same malformed clients before header access, logout AMC request work, or session-cookie deletion. |
| R3 | Existing malformed login credential validation must remain earlier than client validation and request work. |
| R4 | Existing config-object and header-object state validation must remain separate valid-client preflights. |
| R5 | Valid login success/failure handling, missing/blank session-cookie diagnostics, logout success, logout error suppression, and adjacent auth/client/AMC/RequestUtil/site workflows must remain unchanged. |
| R6 | Auth, adjacent workflow, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct login clients fail at the public auth boundary. | `TestHTTPAuthentication.test_login_rejects_malformed_client_before_config` failed RED for all 5 malformed values with raw `AttributeError`, then passed GREEN after validation was added. | Reaching `client.amc_client.config`, accepting client-like dictionaries, preparing HTTP requests, serializing headers, or leaking raw attribute errors rejects this local completion claim. | `HTTPAuthentication.login(...)` | `src/wikidot/module/auth.py`, `tests/unit/test_auth.py` |
| R2 | Malformed direct logout clients fail before logout state access or mutation. | `TestHTTPAuthentication.test_logout_rejects_malformed_client_before_header` failed RED for all 5 malformed values with raw `AttributeError`, then passed GREEN after validation was added. | Reaching `client.amc_client.header`, suppressing the wrong error, issuing logout requests, deleting cookies, or leaking raw attribute errors rejects this local completion claim. | `HTTPAuthentication.logout(...)` | `src/wikidot/module/auth.py`, `tests/unit/test_auth.py` |
| R3 | Existing credential validation remains the first login preflight. | Focused GREEN included `test_login_rejects_non_string_credentials_before_request` for six malformed credential cases. | Shifting malformed credentials into client validation, config reads, header reads, HTTP POST, or cookie mutation rejects this local completion claim. | Login credentials | `tests/unit/test_auth.py` |
| R4 | Nested config/header state validation remains separate after valid client validation. | Focused GREEN included invalid config-object and invalid header-object tests for login, plus invalid header-object tests for logout. | Treating malformed config/header state as malformed client state, reading their fields before validation, or issuing requests rejects this local completion claim. | Auth nested state | `src/wikidot/module/auth.py`, `tests/unit/test_auth.py` |
| R5 | Existing auth behavior remains stable. | Focused auth tests passed 38 tests, the full auth file passed 38 tests, and adjacent client/Ajax/AMC/RequestUtil/site tests passed 674 tests. | Regressing login success, invalid credential mapping, HTTP status mapping, missing/blank cookie diagnostics, cookie set/delete calls, logout request suppression, client construction, raw AMC requests, RequestUtil behavior, or site workflows rejects this local completion claim. | Auth and adjacent workflows | `tests/unit` |
| R6 | Existing repository quality gates remain green. | Full unit tests passed 2608 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live auth material or private state is needed to prove the behavior. | All regressions use unit-level synthetic state; this draft contains no credentials, cookies, auth JSON, raw account data, private response bodies, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private usernames, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `b4d517b fix(auth): validate auth client`.

- RED login client: `uv run pytest tests/unit/test_auth.py::TestHTTPAuthentication::test_login_rejects_malformed_client_before_config -q` failed 5 tests before the fix because malformed clients reached `client.amc_client.config` and leaked raw `AttributeError`.
- RED logout client: `uv run pytest tests/unit/test_auth.py::TestHTTPAuthentication::test_logout_rejects_malformed_client_before_header -q` failed 5 tests before the logout fix because malformed clients reached `client.amc_client.header` and leaked raw `AttributeError`.
- GREEN focused: `uv run pytest tests/unit/test_auth.py::TestHTTPAuthentication::test_login_rejects_malformed_client_before_config tests/unit/test_auth.py::TestHTTPAuthentication::test_logout_rejects_malformed_client_before_header tests/unit/test_auth.py::TestHTTPAuthentication::test_login_rejects_non_string_credentials_before_request tests/unit/test_auth.py::TestHTTPAuthentication::test_login_rejects_invalid_config_object_before_request tests/unit/test_auth.py::TestHTTPAuthentication::test_login_rejects_invalid_header_object_before_request tests/unit/test_auth.py::TestHTTPAuthentication::test_login_success tests/unit/test_auth.py::TestHTTPAuthentication::test_login_invalid_credentials tests/unit/test_auth.py::TestHTTPAuthentication::test_login_http_error tests/unit/test_auth.py::TestHTTPAuthentication::test_login_no_session_cookie tests/unit/test_auth.py::TestHTTPAuthentication::test_login_blank_session_cookie_fails_without_setting_cookie tests/unit/test_auth.py::TestHTTPAuthentication::test_logout tests/unit/test_auth.py::TestHTTPAuthentication::test_logout_rejects_invalid_header_object_before_mutation tests/unit/test_auth.py::TestHTTPAuthentication::test_logout_suppresses_errors -q` passed 38 tests.
- `uv run pytest tests/unit/test_auth.py -q` passed 38 tests.
- `uv run pytest tests/unit/test_client.py tests/unit/test_ajax.py tests/unit/test_amc_client.py tests/unit/test_requestutil.py tests/unit/test_site.py -q` passed 674 tests.
- `uv run pytest tests/unit -q` passed 2608 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy .` passed with no issues in 87 source files.
- `uv run pyright .` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Malformed direct `HTTPAuthentication.login(client=...)` inputs raise `ValueError("client must be a Client")`.
- Malformed direct `HTTPAuthentication.logout(client=...)` inputs raise `ValueError("client must be a Client")`.
- Existing malformed credential validation remains an earlier login preflight.
- Existing config-object and header-object validation remain separate valid-client preflights.
- Valid login, login failure diagnostics, session-cookie mutation, logout success, logout error suppression, and adjacent workflows remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Client validation could accidentally change credential validation precedence. Mitigation: login client validation runs after existing username/password validation, and focused GREEN includes malformed credential tests.
- Risk: This could be confused with auth config/header validation. Mitigation: Issues 524 and 527 cover nested state after a valid client exists; this draft covers the parent client object before `amc_client` is read.
- Risk: Auth tests need a stricter client-shaped fixture. Mitigation: the test helper uses `object.__new__(Client)` with synthetic AMC state to pass the public type boundary without running constructor/login side effects.

## Dependencies

- Existing `Client` remains the canonical parent type for direct authentication helpers.
- Existing login credential validators remain responsible for username/password inputs before client validation.
- Existing config/header validators remain responsible for nested state after a valid client is supplied.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`HTTPAuthentication.login(...)` and `HTTPAuthentication.logout(...)` are direct session lifecycle entry points for browser-free workflows. Validating the supplied client object before nested state reads and request/cookie work gives generated callers and tests deterministic errors for malformed inputs without changing credential validation, login behavior, logout cleanup, nested config/header validation, or live Wikidot semantics for valid clients.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed malformed direct `client` arguments crossing the public static auth boundaries and leaking `AttributeError` from `client.amc_client.config` or `client.amc_client.header`.
- This slice only validates the `HTTPAuthentication.login(...)` and `HTTPAuthentication.logout(...)` caller-provided parent client. It does not change credential policy, retry policy, HTTP helper behavior, session-cookie validation, header serialization, cookie mutation semantics, client construction, live site behavior, or authentication semantics for valid clients.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, and live Wikidot account details out of upstream discussion.
