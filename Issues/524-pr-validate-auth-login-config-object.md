# PR Draft: Validate Auth Login Config Object State

## Summary

`HTTPAuthentication.login(client, username, password)` validates login credential types and delegates retry controls to the shared HTTP helper, but it still assumed `client.amc_client.config` was an `AjaxModuleConnectorConfig` object once valid credentials reached login request setup. A caller, generated fixture, or test double could replace `client.amc_client.config` with `None`, an arbitrary object, a dictionary, a string, or a boolean, and login would fail with incidental attribute errors such as `'dict' object has no attribute 'request_timeout'` after header serialization had already run.

This change validates the stored config object before reading timeout, retry, and backoff fields. Login now rejects replaced config state with `ValueError("config must be AjaxModuleConnectorConfig")` before serializing headers, issuing HTTP requests, or mutating session cookies. Valid login success and failure handling, credential validation, session-cookie validation, logout behavior, raw AMC requests, RequestUtil, client construction, and site workflows remain unchanged.

## Outcome

Auth login callers now get deterministic config-object validation at the login request boundary instead of lower-level attribute errors when nested AMC config state is replaced.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free login, mocked clients, generated local fixtures, JSON/YAML adapters, account bootstrap scripts, migration tools, moderation tools, archival workflows, or local CI fixtures that may replace nested client state.

## Current Evidence

Local rollout-backed drafts establish auth login and AMC config state as practical shared infrastructure. [513-pr-validate-login-credential-types.md](513-pr-validate-login-credential-types.md) covered login credential types, [340-pr-login-session-cookie-validation.md](340-pr-login-session-cookie-validation.md) covered returned session-cookie value validation, [390-pr-validate-http-retry-boolean-controls.md](390-pr-validate-http-retry-boolean-controls.md) covered shared HTTP retry controls, [515-pr-validate-amc-config-object.md](515-pr-validate-amc-config-object.md) covered constructor-time AMC config object inputs, [520-pr-validate-amc-config-fields.md](520-pr-validate-amc-config-fields.md) covered config field construction, [522-pr-validate-amc-request-state-objects.md](522-pr-validate-amc-request-state-objects.md) covered raw `AjaxModuleConnectorClient.request(...)` stored request-state objects, and [523-pr-validate-requestutil-config-object.md](523-pr-validate-requestutil-config-object.md) covered direct URL `RequestUtil.request(...)` config object state.

Those prior slices are not duplicates. Issue 513 validates username/password objects before login request work. Issue 340 validates the returned session cookie after a login response. Issues 515 and 520 validate AMC construction surfaces. Issue 522 validates the raw AMC request boundary. Issue 523 validates the direct URL RequestUtil boundary. This slice validates the auth login boundary after callers or fixtures replace `client.amc_client.config` before the login POST is prepared. No upstream issue was filed from this local workspace.

## Changes

- Import `AjaxModuleConnectorConfig` into `src/wikidot/module/auth.py`.
- Add `_validate_login_config_object(...)` to reject non-`AjaxModuleConnectorConfig` state with `ValueError("config must be AjaxModuleConnectorConfig")`.
- Run config-object validation before login header serialization, timeout/retry field access, HTTP POST setup, or session-cookie mutation.
- Preserve the existing login credential validation, HTTP status handling, invalid-credential response handling, session-cookie validation, and logout behavior.
- Add focused tests for replaced login config objects before request setup.

## Type Of Change

- Input/state validation
- Auth login preflight hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `HTTPAuthentication.login(...)` must reject replaced non-`AjaxModuleConnectorConfig` `client.amc_client.config` state before preparing the login request. |
| R2 | The rejection must use `ValueError("config must be AjaxModuleConnectorConfig")` rather than incidental attribute errors or field-level timeout diagnostics. |
| R3 | Invalid config replacements must not serialize headers, issue HTTP requests, or mutate session cookies. |
| R4 | Existing valid login success, invalid credentials, HTTP error, missing-cookie, blank-cookie, credential-type, and logout behavior must remain unchanged. |
| R5 | Existing auth, client, AMC, RequestUtil, site, and full unit workflows must remain green. |
| R6 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, auth tests, adjacent tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Directly replacing `client.amc_client.config` with `None`, arbitrary objects, dictionaries, strings, or booleans raises before the login request is prepared. | `test_login_rejects_invalid_config_object_before_request` failed RED for five malformed replacements with old attribute errors, then passed GREEN. | Reading `.request_timeout` on malformed config state, preparing a login POST, or silently defaulting replaced state rejects this local completion claim. | Auth login preflight | `src/wikidot/module/auth.py`, `tests/unit/test_auth.py` |
| R2 | The raised error is `ValueError("config must be AjaxModuleConnectorConfig")`. | The focused GREEN test asserts that exact diagnostic for five malformed config replacements. | Returning `AttributeError`, `request_timeout must be a positive number`, HTTPX-level errors, or session-creation errors rejects this local completion claim. | Config object diagnostics | `tests/unit/test_auth.py` |
| R3 | Invalid config replacements do not serialize headers, send HTTP requests, or set session cookies. | The focused GREEN test asserts `httpx.post`, `header.get_header`, and `header.set_cookie` are not called. | Calling `get_header`, issuing an HTTP request, setting `WIKIDOT_SESSION_ID`, or mutating cookies under invalid config state rejects this local completion claim. | Login side effects | `tests/unit/test_auth.py` |
| R4 | Existing login and logout behavior remains stable. | `uv run pytest tests/unit/test_auth.py -q` passed 18 tests. | Regressing valid login, invalid credentials, HTTP status handling, missing cookies, blank cookies, credential type checks, logout request, or cookie deletion rejects this local completion claim. | Auth workflows | `tests/unit/test_auth.py` |
| R5 | Existing adjacent workflows remain green. | Adjacent auth/client/AMC/RequestUtil/site suites passed 613 tests, and full unit passed 2458 tests. | Regressing client construction, raw AMC request validation, direct URL requests, site workflows, or auth behavior rejects this local completion claim. | Auth and adjacent workflows | `tests/unit` |
| R6 | No private material or live action is needed to prove the behavior. | All regressions use synthetic config replacements and local unit tests; the draft contains no raw credentials, cookies, auth JSON, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `0a8a05e fix(auth): validate login config object state`.

- RED config-object tests: `uv run pytest tests/unit/test_auth.py::TestHTTPAuthentication::test_login_rejects_invalid_config_object_before_request -q` failed 5 cases before the fix because `None`, arbitrary objects, dictionaries, strings, and booleans raised `AttributeError` while reading `request_timeout`.
- GREEN focused tests: the same focused command passed 5 tests after config-object preflight was added.
- `uv run ruff format src/wikidot/module/auth.py tests/unit/test_auth.py` passed with 2 files left unchanged.
- `uv run pytest tests/unit/test_auth.py -q` passed 18 tests.
- `uv run ruff check src/wikidot/module/auth.py tests/unit/test_auth.py` passed.
- `uv run ruff format --check src/wikidot/module/auth.py tests/unit/test_auth.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/module/auth.py tests/unit/test_auth.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/auth.py tests/unit/test_auth.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit/test_auth.py tests/unit/test_client.py tests/unit/test_amc_client.py tests/unit/test_requestutil.py tests/unit/test_site.py -q` passed 613 tests.
- `uv run pytest tests/unit -q` passed 2458 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `HTTPAuthentication.login(client, "test-user", "test-password")` raises `ValueError("config must be AjaxModuleConnectorConfig")` when `client.amc_client.config` is `None`, `object()`, `{}`, `"config"`, or `True`.
- Those malformed config replacements do not serialize request headers, send HTTP requests, or set `WIKIDOT_SESSION_ID`.
- Existing non-string username/password validation still runs before config validation and sends no request.
- Valid login success, invalid-credential response handling, HTTP error handling, missing-cookie handling, blank-cookie handling, logout request, and logout cookie deletion remain unchanged.
- Raw AMC requests, direct URL RequestUtil requests, client construction, and site workflows remain unchanged.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This could be confused with login credential validation. Mitigation: Issue 513 covers username/password objects; this slice covers nested AMC config state after valid credentials pass.
- Risk: This could be confused with returned session-cookie validation. Mitigation: Issue 340 covers post-response cookie validation; this slice runs before any login request is sent.
- Risk: This could be confused with AMC constructor config validation. Mitigation: Issues 515 and 520 cover constructor inputs and field construction; this slice covers auth request-time nested state after replacement.
- Risk: This could be confused with raw AMC or RequestUtil request-state validation. Mitigation: Issues 522 and 523 cover other request boundaries; this slice covers the auth login POST path.
- Risk: Rejecting replaced config objects may expose mocks that used bare dictionaries or generic objects. Mitigation: login needs configured timeout, retry interval, max backoff, and backoff factor values; mocks should use a real `AjaxModuleConnectorConfig` or a full client fixture.

## Out Of Scope

Changing config immutability, accepting mapping-based config objects, changing numeric timeout/retry/backoff validation, validating auth header object state, changing login retry limits, changing response parsing, changing session-cookie policy, changing logout behavior, changing raw AMC request behavior, changing RequestUtil behavior, live Wikidot behavior, and upstream Issue/PR creation are outside this slice.

## Why This Matters

`HTTPAuthentication.login(...)` is the browser-free session creation path. When nested client state is malformed, the login boundary should identify the malformed config object before request header serialization, retry setup, or HTTP machinery starts.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used browser-free clients, account bootstrap flows, mocked client objects, generated fixtures, raw AMC clients, and nested client state that depends on `client.amc_client.config`.
- Existing drafts covered login credentials, returned session cookies, shared HTTP retry controls, AMC constructor config validation, AMC config field construction, raw AMC request-state validation, and direct URL RequestUtil config-object validation, but did not validate replaced config objects at the auth login boundary.
- The focused RED failures showed replaced config objects surfacing as attribute errors after header serialization had already been evaluated. The GREEN regression covers those replacements before headers, requests, or session-cookie mutation can run.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
