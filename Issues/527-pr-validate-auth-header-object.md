# PR Draft: Validate Auth Header Object State

## Summary

`HTTPAuthentication.login(...)` and `HTTPAuthentication.logout(...)` already validate login credential types and login config object state, and raw AMC requests validate stored connector header state. The auth helper itself still assumed `client.amc_client.header` was an `AjaxRequestHeader` object before login header serialization, session-cookie mutation, or logout cookie deletion. A caller, generated fixture, or test double could replace `client.amc_client.header` with `None`, an arbitrary object, a dictionary, a string, or a boolean, and auth would fail with incidental attribute errors such as `'dict' object has no attribute 'get_header'` or `'dict' object has no attribute 'delete_cookie'`.

This change validates the stored auth header object before login request setup and before logout request/cookie mutation. Replaced header state now raises `ValueError("header must be AjaxRequestHeader")`. Valid login success/failure handling, config-object validation, blank-cookie validation, logout request suppression, session-cookie set/delete calls, raw AMC request-state validation, RequestUtil, client construction, and site workflows remain unchanged.

## Outcome

Auth callers now get deterministic header-object validation at the auth boundary instead of lower-level attribute errors when nested AMC header state is replaced.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free login/logout workflows, account bootstrap scripts, generated local fixtures, JSON/YAML adapters, migration tools, moderation tools, archival workflows, or local CI fixtures that may replace nested client state.

## Current Evidence

Local rollout-backed drafts establish authentication, request headers, and AMC mutable state as practical shared infrastructure. [340-pr-login-session-cookie-validation.md](340-pr-login-session-cookie-validation.md) covered returned login session-cookie values, [400-pr-validate-amc-header-values.md](400-pr-validate-amc-header-values.md) covered request-header field values, [521-pr-validate-amc-header-serialization-state.md](521-pr-validate-amc-header-serialization-state.md) covered `AjaxRequestHeader.get_header(...)` serialization state, [522-pr-validate-amc-request-state-objects.md](522-pr-validate-amc-request-state-objects.md) covered raw `AjaxModuleConnectorClient.request(...)` stored header objects, [513-pr-validate-login-credential-types.md](513-pr-validate-login-credential-types.md) covered auth credential types, and [524-pr-validate-auth-login-config-object.md](524-pr-validate-auth-login-config-object.md) covered auth login config-object state.

Those prior slices are not duplicates. Issue 521 validates header contents once a real `AjaxRequestHeader` is asked to serialize itself. Issue 522 validates raw AMC request-time stored header objects before async request work. Issue 524 validates the auth login config object before timeout/retry reads. This slice validates the auth helper's own stored header object before login header serialization, login session-cookie mutation, or logout cookie deletion. No upstream issue was filed from this local workspace.

## Changes

- Import `AjaxRequestHeader` into `src/wikidot/module/auth.py`.
- Add an auth-local header object validator that rejects non-`AjaxRequestHeader` state with `ValueError("header must be AjaxRequestHeader")`.
- Validate the header object before login request setup and reuse the validated header for `get_header(...)` and `set_cookie(...)`.
- Validate the header object before logout request work and reuse the validated header for `delete_cookie(...)`.
- Convert auth unit fixtures to use a real `AjaxRequestHeader` object with mocked methods for valid call assertions.
- Add focused tests for replaced login/logout header objects before request or cookie mutation work.

## Type Of Change

- Input/state validation
- Auth preflight hardening
- Test fixture correction
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `HTTPAuthentication.login(...)` must reject replaced non-`AjaxRequestHeader` `client.amc_client.header` state before login request setup. |
| R2 | `HTTPAuthentication.logout(...)` must reject replaced non-`AjaxRequestHeader` `client.amc_client.header` state before logout request work or cookie deletion. |
| R3 | The rejection must use `ValueError("header must be AjaxRequestHeader")` rather than incidental attribute errors. |
| R4 | Invalid login header replacements must not issue HTTP POSTs, and invalid logout header replacements must not call `client.amc_client.request`. |
| R5 | Existing valid auth, client, AMC, RequestUtil, site, and full unit workflows must remain unchanged. |
| R6 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, auth tests, adjacent tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Directly replacing `client.amc_client.header` with `None`, arbitrary objects, dictionaries, strings, or booleans raises before login header serialization. | `test_login_rejects_invalid_header_object_before_request` failed RED for five malformed replacements with old attribute errors, then passed GREEN. | Reading `.get_header()` on malformed header state, preparing the login POST, or silently defaulting replaced header state rejects this local completion claim. | Auth login preflight | `src/wikidot/module/auth.py`, `tests/unit/test_auth.py` |
| R2 | The same replacements raise before logout request work or cookie deletion. | `test_logout_rejects_invalid_header_object_before_mutation` failed RED for five malformed replacements with old attribute errors, then passed GREEN. | Calling `client.amc_client.request`, reading `.delete_cookie()` on malformed header state, or silently skipping the malformed header rejects this local completion claim. | Auth logout preflight | `src/wikidot/module/auth.py`, `tests/unit/test_auth.py` |
| R3 | The raised error is `ValueError("header must be AjaxRequestHeader")`. | The focused GREEN tests assert that diagnostic for ten malformed header replacements across login and logout. | Returning `AttributeError`, raw AMC diagnostics, or cookie/header serialization diagnostics rejects this local completion claim. | Auth header diagnostics | `tests/unit/test_auth.py` |
| R4 | Invalid login headers send no HTTP requests, and invalid logout headers call no AMC request. | The focused GREEN tests assert patched `httpx.post` is not called for login and `mock_client.amc_client.request` is not called for logout. | Sending a login POST, sending a logout AMC request, or mutating cookies under invalid header state rejects this local completion claim. | Auth side effects | `tests/unit/test_auth.py` |
| R5 | Existing auth and adjacent workflows remain green. | `uv run pytest tests/unit/test_auth.py -q` passed 28 tests; adjacent auth/client/AMC/RequestUtil/site suites passed 633 tests; full unit passed 2478 tests. | Regressing valid login, invalid credential handling, HTTP status handling, missing/blank cookie diagnostics, logout suppression, client construction, raw AMC request validation, direct URL RequestUtil, or site workflows rejects this local completion claim. | Auth and adjacent workflows | `tests/unit` |
| R6 | No private material or live action is needed to prove the behavior. | All regressions use synthetic header replacements and local unit tests; the draft contains no raw credentials, cookies, auth JSON, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `5d42f59 fix(auth): validate header object state`.

- RED header-object tests: `uv run pytest tests/unit/test_auth.py::TestHTTPAuthentication::test_login_rejects_invalid_header_object_before_request tests/unit/test_auth.py::TestHTTPAuthentication::test_logout_rejects_invalid_header_object_before_mutation -q` failed 10 cases before the fix because login replacements raised `AttributeError` while reading `get_header` and logout replacements raised `AttributeError` while reading `delete_cookie`.
- GREEN focused tests: the same focused command passed 10 tests after auth header-object preflight was added.
- `uv run pytest tests/unit/test_auth.py -q` passed 28 tests.
- `uv run ruff format src/wikidot/module/auth.py tests/unit/test_auth.py` passed with 2 files left unchanged.
- `uv run pytest tests/unit/test_auth.py tests/unit/test_client.py tests/unit/test_amc_client.py tests/unit/test_requestutil.py tests/unit/test_site.py -q` passed 633 tests.
- `uv run ruff check src/wikidot/module/auth.py tests/unit/test_auth.py` passed.
- `uv run ruff format --check src/wikidot/module/auth.py tests/unit/test_auth.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/module/auth.py tests/unit/test_auth.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/auth.py tests/unit/test_auth.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2478 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `HTTPAuthentication.login(client, "test-user", "test-password")` raises `ValueError("header must be AjaxRequestHeader")` when `client.amc_client.header` is `None`, `object()`, `{}`, `"header"`, or `True`.
- Those malformed login header replacements send no HTTP POST.
- `HTTPAuthentication.logout(client)` raises `ValueError("header must be AjaxRequestHeader")` for the same replacements before logout AMC request work or cookie deletion.
- Valid login success, login credential validation, invalid credential handling, HTTP status handling, missing/blank session-cookie diagnostics, logout request suppression, and session-cookie set/delete calls remain unchanged.
- Raw AMC request-state validation, RequestUtil behavior, client construction, site lookup, and site AMC retry behavior remain unchanged.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with AMC header serialization validation. Mitigation: Issue 521 covers malformed state inside a real `AjaxRequestHeader`; this slice covers the auth helper receiving a replaced non-header object.
- Risk: This could be confused with raw AMC request-state validation. Mitigation: Issue 522 covers `AjaxModuleConnectorClient.request(...)`; this slice covers login/logout before auth reads or mutates header state.
- Risk: This could be confused with auth config-object validation. Mitigation: Issue 524 covers config state before timeout/retry reads; this slice covers the separate header object used for request headers and session-cookie mutation.
- Risk: Valid tests that used bare MagicMock header state may fail. Mitigation: valid auth tests now use a real `AjaxRequestHeader` instance with mocked methods, preserving assertions while matching runtime object shape.

## Out Of Scope

Changing header immutability, accepting mapping-based header objects, changing cookie-name/value validation, changing login retry policy, changing credential validation, changing session-cookie value validation, changing raw AMC request behavior, changing RequestUtil behavior, changing live Wikidot behavior, and upstream Issue/PR creation are outside this slice.

## Why This Matters

Authentication is the entry point for browser-free write and private-dashboard workflows. When nested header state is malformed, login/logout should fail at the auth boundary before request setup or cookie mutation, not through incidental attribute errors.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used authenticated browser-free workflows, login/session setup, logout cleanup, Ajax header state, request utilities, and generated fixtures.
- Existing drafts covered credential types, session-cookie values, header value/serialization state, raw AMC request-state objects, and auth login config-object state, but did not validate replaced auth header objects at the login/logout boundary.
- The focused RED failures showed replaced header objects surfacing as attribute errors while auth prepared login headers or deleted logout cookies. The GREEN regression covers those replacements before request or cookie mutation work can run.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
