# PR Draft: Validate Blank Login Credentials

## Summary

`HTTPAuthentication.login(client, username, password)` and `Client(username=..., password=...)` already reject malformed credential types and partial credential pairs, but empty strings and whitespace-only strings still passed validation. A direct auth call with blank credentials could reach the login POST path, and a `Client(...)` construction with blank credentials could initialize connector state and delegate to auth before the malformed secret input was detected.

This change rejects blank username and password strings at both public credential entry points. Direct auth calls raise `ValueError("username must not be empty")` or `ValueError("password must not be empty")` before HTTP request work or session-cookie mutation. `Client(...)` raises the same diagnostics before `AjaxModuleConnectorClient` setup, `HTTPAuthentication.login(...)`, or `User.from_name(...)` identity lookup. Valid non-empty credential strings, non-string diagnostics, partial credential-pair diagnostics, auth client/config/header validation, login success and failure mapping, returned session-cookie validation, logout behavior, and adjacent request/header workflows remain unchanged.

## Outcome

Blank login credentials now fail locally before any browser-free authentication setup or login request work, while ordinary non-empty string login attempts keep the existing server-authenticated flow.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who construct clients or call auth helpers from browser-free automation, sandbox setup scripts, environment-variable adapters, CI fixtures, local test harnesses, or credential bootstrap checks.

## Current Evidence

Authentication drafts [340-pr-login-session-cookie-validation.md](340-pr-login-session-cookie-validation.md), [513-pr-validate-login-credential-types.md](513-pr-validate-login-credential-types.md), [514-pr-validate-client-partial-credentials.md](514-pr-validate-client-partial-credentials.md), [524-pr-validate-auth-login-config-object.md](524-pr-validate-auth-login-config-object.md), [527-pr-validate-auth-header-object.md](527-pr-validate-auth-header-object.md), and [549-pr-validate-auth-client.md](549-pr-validate-auth-client.md) establish login, session-cookie, client-construction, config/header state, and direct auth client validation as practical browser-free infrastructure boundaries.

Issue 513 explicitly scoped credential validation to type checks and left empty-string rejection outside scope. Issue 514 explicitly scoped `Client(...)` credential validation to pair presence and type/content validation outside scope. This slice resolves that adjacent open content-boundary only for blank and whitespace-only strings; it does not attempt username syntax validation, password strength validation, credential correctness validation, live login policy changes, or account lockout policy changes.

No upstream issue was filed from this local workspace.

## Changes

- Reject blank and whitespace-only `username` / `password` values in the direct auth login text validator after the existing string-type check.
- Reject blank and whitespace-only `Client(...)` credential values in the constructor credential-pair preflight after the existing pair and type checks.
- Preserve valid non-empty string values exactly; the validators do not strip or normalize stored credentials.
- Add focused unit coverage proving direct auth blank credentials do not call `httpx.post(...)` and do not set `WIKIDOT_SESSION_ID`.
- Add focused unit coverage proving `Client(...)` blank credentials do not initialize `AjaxModuleConnectorClient`, call `HTTPAuthentication.login(...)`, or call `User.from_name(...)`.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `HTTPAuthentication.login(..., username="")` and whitespace-only variants must raise `ValueError("username must not be empty")` before HTTP request work or cookie mutation. |
| R2 | `HTTPAuthentication.login(..., password="")` and whitespace-only variants must raise `ValueError("password must not be empty")` before HTTP request work or cookie mutation. |
| R3 | `Client(username="", password="...")`, whitespace-only username variants, `Client(username="...", password="")`, and whitespace-only password variants must raise the same diagnostics before connector setup, auth delegation, or identity lookup. |
| R4 | Existing partial-pair, non-string credential, malformed auth client, config-object, header-object, and session-cookie diagnostics must remain unchanged. |
| R5 | Valid non-empty string login attempts, successful mocked login, invalid-credential response mapping, HTTP status failures, missing/blank returned-cookie handling, logout, and adjacent client/Ajax/RequestUtil workflows must remain unchanged. |
| R6 | Focused RED/GREEN, affected auth/client tests, adjacent workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Blank direct login usernames fail before request work. | `TestHTTPAuthentication.test_login_rejects_blank_credentials_before_request` failed RED for `""` and `"   "` username values with `DID NOT RAISE`, then passed GREEN after `_validate_login_text(...)` rejected blank strings. | Calling `httpx.post(...)`, setting `WIKIDOT_SESSION_ID`, accepting a blank username, stripping and continuing, or changing the non-string username diagnostic rejects this local completion claim. | Direct auth preflight | `src/wikidot/module/auth.py`, `tests/unit/test_auth.py` |
| R2 | Blank direct login passwords fail before request work. | The same auth test failed RED for `""` and `"   "` password values with `DID NOT RAISE`, then passed GREEN after the same validator rejected blank strings. | Calling `httpx.post(...)`, setting `WIKIDOT_SESSION_ID`, accepting a blank password, stripping and continuing, or changing the non-string password diagnostic rejects this local completion claim. | Direct auth preflight | `src/wikidot/module/auth.py`, `tests/unit/test_auth.py` |
| R3 | Blank `Client(...)` credentials fail before constructor side effects. | `TestClient.test_init_rejects_blank_credentials_before_client_setup` failed RED for 4 blank username/password cases with `DID NOT RAISE`, then passed GREEN after `_validate_client_credentials_pair(...)` rejected blank strings. | Constructing `AjaxModuleConnectorClient`, calling `HTTPAuthentication.login(...)`, calling `User.from_name(...)`, accepting blank credentials, or changing partial-pair/type diagnostics rejects this local completion claim. | Client constructor preflight | `src/wikidot/module/client.py`, `tests/unit/test_client.py` |
| R4 | Existing validation precedence and diagnostics remain stable. | Full auth and client test files passed after the fix, including partial credential pairs, malformed credential types, malformed auth clients, config objects, header objects, and returned cookie validation. | Checking blankness before type checks, replacing partial-pair diagnostics, weakening auth client/config/header validation, or changing returned-cookie errors rejects this local completion claim. | Auth/client validation order | `tests/unit/test_auth.py`, `tests/unit/test_client.py` |
| R5 | Existing login and adjacent request behavior remains green. | Auth passed 42 tests, client passed 45 tests, and adjacent auth/client/Ajax/RequestUtil coverage passed 249 tests. | Regressing valid mocked login, invalid-credential mapping, HTTP status mapping, missing/blank returned-cookie diagnostics, logout cleanup, client accessors, Ajax masking/header behavior, or RequestUtil behavior rejects this local completion claim. | Auth and adjacent workflows | `tests/unit` |
| R6 | Repository quality gates pass in the local dependency environment. | Full unit passed 2828 tests; full `ruff check`, `ruff format --check`, `mypy`, `pyright`, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | verification commands below |
| R7 | No live auth material or private state is needed to prove the behavior. | The regressions use synthetic placeholder credential strings and patched unit-level HTTP/auth constructors only; this draft contains no credentials, cookies, auth JSON, raw login response bodies, private usernames, raw rollout paths, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private account data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `d540c5b fix(auth): validate blank login credentials`.

- RED: `uv run pytest tests/unit/test_auth.py::TestHTTPAuthentication::test_login_rejects_blank_credentials_before_request tests/unit/test_client.py::TestClient::test_init_rejects_blank_credentials_before_client_setup -q` failed 8 blank direct-auth and `Client(...)` credential cases with `DID NOT RAISE`.
- GREEN focused: the same command passed 8 tests after direct auth and client constructor blank-credential validation was added.
- Auth coverage: `uv run pytest tests/unit/test_auth.py -q` passed 42 tests.
- Client coverage: `uv run pytest tests/unit/test_client.py -q` passed 45 tests.
- Adjacent coverage: `uv run pytest tests/unit/test_auth.py tests/unit/test_client.py tests/unit/test_ajax.py tests/unit/test_requestutil.py -q` passed 249 tests.
- `uv run ruff format src/wikidot/module/auth.py src/wikidot/module/client.py tests/unit/test_auth.py tests/unit/test_client.py` left 4 files unchanged.
- `uv run pytest tests/unit -q` passed 2828 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `HTTPAuthentication.login(client, "", "test-password")` and whitespace-only username variants raise `ValueError("username must not be empty")` before `httpx.post(...)` and before `WIKIDOT_SESSION_ID` mutation.
- `HTTPAuthentication.login(client, "test-user", "")` and whitespace-only password variants raise `ValueError("password must not be empty")` before `httpx.post(...)` and before `WIKIDOT_SESSION_ID` mutation.
- `Client(username="", password="test-password")` and whitespace-only username variants raise `ValueError("username must not be empty")` before connector setup, login delegation, or identity lookup.
- `Client(username="test-user", password="")` and whitespace-only password variants raise `ValueError("password must not be empty")` before connector setup, login delegation, or identity lookup.
- Non-string username/password values still raise the existing `"... must be a string"` diagnostics, and partial credential pairs still raise `ValueError("username and password must be provided together")`.
- Valid non-empty string credentials keep the existing mocked login path, session-cookie storage, client logged-in state, username storage, and `User.from_name(...)` identity lookup behavior.
- Existing invalid credential response detection, HTTP status failure handling, missing returned-cookie handling, blank returned-cookie handling, logout request/cookie deletion behavior, adjacent client accessors, Ajax masking/header behavior, RequestUtil behavior, live Wikidot semantics, upstream Issues, upstream PRs, pushes, credentials, cookies, auth JSON, and raw response bodies remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

Browser-free authentication often loads credentials from environment variables, files, generated configs, or CI secret adapters. Blank strings usually mean "missing secret" at those boundaries, not a useful login attempt. Failing before request setup avoids avoidable login POSTs and keeps unit-level diagnostics deterministic without inspecting live accounts or logging raw credential values.

## Local Evidence, Not For Upstream Paste

- Issue 513 covered non-string direct login credentials and explicitly left empty-string rejection for a separate decision.
- Issue 514 covered `Client(...)` partial credential pairs and explicitly left empty-string rejection outside that slice.
- The focused RED run showed direct auth and client construction accepted empty and whitespace-only credential strings.
- This slice only validates blank credential strings. It does not validate username syntax, password correctness, password strength, live account policy, login retry limits, returned-cookie names beyond existing checks, request-header/cookie validators, or valid non-empty credential semantics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private account data, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The new validators deliberately do not strip, normalize, or store modified non-empty credentials. They only reject strings whose stripped form is empty, preserving existing request payload behavior for all non-empty string inputs.
