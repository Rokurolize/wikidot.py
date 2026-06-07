# PR Draft: Validate Client Partial Credentials

## Summary

`Client(username=..., password=...)` supports optional authentication, but partial credential pairs were silently treated as unauthenticated clients. Supplying only `username` or only `password` skipped `HTTPAuthentication.login(...)`, left `is_logged_in=False`, `username=None`, and `me=None`, and still initialized the Ajax module connector client and accessors. This can hide JSON, YAML, environment, or generated-config mistakes and later fail as `LoginRequiredException` on authenticated workflows rather than at the constructor boundary.

This change validates the credential pair before logger setup, Ajax module connector setup, login, user lookup, or accessor initialization. `Client(username="...", password=None)` and `Client(username=None, password="...")` now raise `ValueError("username and password must be provided together")`. `Client()` remains valid for unauthenticated use, and `Client(username=..., password=...)` still delegates to `HTTPAuthentication.login(...)` and `User.from_name(...)`.

## Outcome

Partial credentials now fail locally before client setup, while no-credential and full-credential construction remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who construct `Client(...)` from browser-free automation, sandbox setup scripts, account bootstrap checks, CI fixtures, environment adapters, or generated local configuration.

## Current Evidence

Authentication draft [513-pr-validate-login-credential-types.md](513-pr-validate-login-credential-types.md) validates malformed credential types once `HTTPAuthentication.login(...)` is called, but it explicitly leaves client partial-credential behavior out of scope. Session and diagnostic drafts such as [340-pr-login-session-cookie-validation.md](340-pr-login-session-cookie-validation.md), [341-pr-mask-client-string-username.md](341-pr-mask-client-string-username.md), and [479-pr-validate-client-accessor-parents.md](479-pr-validate-client-accessor-parents.md) establish login/session state, diagnostic privacy, and client accessor parent integrity as practical safety surfaces, but they do not cover the constructor's optional credential pair boundary.

Input-boundary drafts such as [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), [359-pr-validate-site-lookup-unix-names.md](359-pr-validate-site-lookup-unix-names.md), and [497-pr-validate-quickmodule-request-arguments.md](497-pr-validate-quickmodule-request-arguments.md) establish the local pattern that documented public inputs should fail before setup work, request construction, or state mutation.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 513. Issue 513 validates credential value types once both credentials are provided and the login helper is called; this slice validates pair presence in `Client.__init__(...)` before `HTTPAuthentication.login(...)`.

This is not a duplicate of Issue 340. Issue 340 validates a returned `WIKIDOT_SESSION_ID` cookie after a login response; this slice validates whether the constructor received both credential fields or neither credential field.

This is not a duplicate of Issue 341. Issue 341 masks logged-in usernames in `str(client)` diagnostics; this slice prevents accidental unauthenticated clients from partial credential configuration.

This is not a duplicate of Issue 479. Issue 479 validates accessor parent clients; this slice validates the credential pair before accessors are initialized.

No upstream issue was filed from this local workspace.

## Changes

- Add a small `_validate_client_credentials_pair(...)` helper.
- Call the helper at the start of `Client.__init__(...)`.
- Preserve unauthenticated `Client()` construction and full-credential login construction.
- Add parameterized constructor tests for only `username` and only `password`.
- Assert malformed partial credentials do not initialize the Ajax module connector client, call `HTTPAuthentication.login(...)`, or call `User.from_name(...)`.

## Type Of Change

- Input validation
- Client constructor preflight hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Client(username="test-user", password=None)` must raise `ValueError("username and password must be provided together")` before client setup. |
| R2 | `Client(username=None, password="test-password")` must raise `ValueError("username and password must be provided together")` before client setup. |
| R3 | Malformed partial credentials must not call `AjaxModuleConnectorClient`, `HTTPAuthentication.login(...)`, or `User.from_name(...)`. |
| R4 | `Client()` must remain valid for unauthenticated use; `Client(username=..., password=...)` must still delegate to login and user lookup; context manager cleanup, `close()`, `login_check()`, string diagnostics, and accessors must remain unchanged. |
| R5 | This slice must not validate credential content, reject empty strings, change login credential type validation, log raw credentials, require live Wikidot actions, credentials, cookies, auth JSON, raw response bodies, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, client tests, adjacent auth/client/Ajax/request utility tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Username-only construction fails with a stable pair-validation `ValueError` before client setup. | `TestClient.test_init_rejects_partial_credentials_before_client_setup` failed RED for `("test-user", None)` because no `ValueError` was raised, then passed GREEN after validation was added. | Accepting username-only construction, silently treating it as unauthenticated, initializing the Ajax module connector client, or calling login/user lookup rejects this local completion claim. | Client constructor preflight | `src/wikidot/module/client.py`, `tests/unit/test_client.py` |
| R2 | Password-only construction fails with a stable pair-validation `ValueError` before client setup. | The same parameterized test failed RED for `(None, "test-password")` because no `ValueError` was raised, then passed GREEN after validation was added. | Accepting password-only construction, silently treating it as unauthenticated, initializing the Ajax module connector client, or calling login/user lookup rejects this local completion claim. | Client constructor preflight | `src/wikidot/module/client.py`, `tests/unit/test_client.py` |
| R3 | Invalid partial credentials do not initialize connector, login, or user lookup work. | The GREEN test asserts patched `AjaxModuleConnectorClient`, `HTTPAuthentication.login(...)`, and `User.from_name(...)` are not called for either malformed partial pair. | Calling connector setup, login, user lookup, accessor setup, or logging credential values rejects this local completion claim. | Constructor side effects | `tests/unit/test_client.py` |
| R4 | Existing client and adjacent auth/request workflows remain green. | `tests/unit/test_client.py` passed 26 tests, adjacent auth/client/Ajax/request utility tests passed 159 tests, and full unit passed 2307 tests. | Regressing no-credential construction, valid full-credential construction, context manager cleanup, `close()`, `login_check()`, string diagnostics, accessors, Ajax masking/header behavior, auth login behavior, or RequestUtil behavior rejects this local completion claim. | Client and adjacent workflows | `tests/unit` |
| R5 | No private material or live action is needed to prove the behavior. | All regressions use synthetic credential strings and patched local constructors/helpers; the draft contains no raw credentials, cookies, auth JSON, or response bodies. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, raw login response bodies, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, client tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `a4724d6 fix(client): reject partial credentials`.

- RED partial-credential tests: `uv run pytest tests/unit/test_client.py::TestClient::test_init_rejects_partial_credentials_before_client_setup -q` failed 2 malformed partial credential cases before the fix with `DID NOT RAISE`.
- GREEN partial-credential tests: the same focused command passed 2 tests after credential pair validation was added.
- `uv run pytest tests/unit/test_client.py -q` passed 26 tests.
- `uv run pytest tests/unit/test_auth.py tests/unit/test_client.py tests/unit/test_ajax.py tests/unit/test_requestutil.py -q` passed 159 tests.
- `uv run ruff format src/wikidot/module/client.py tests/unit/test_client.py` left 2 files unchanged.
- `uv run ruff format --check src/wikidot/module/client.py tests/unit/test_client.py` passed with 2 files already formatted.
- `uv run ruff check src/wikidot/module/client.py tests/unit/test_client.py` passed.
- `uv run mypy src/wikidot/module/client.py tests/unit/test_client.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/client.py tests/unit/test_client.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2307 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Client(username="test-user", password=None)` raises `ValueError("username and password must be provided together")` before client setup.
- `Client(username=None, password="test-password")` raises `ValueError("username and password must be provided together")` before client setup.
- Malformed partial credentials do not initialize `AjaxModuleConnectorClient`, call `HTTPAuthentication.login(...)`, or call `User.from_name(...)`.
- `Client()` remains valid and unauthenticated.
- `Client(username="test-user", password="test-password")` still logs in and caches the authenticated username/user object.
- Existing context manager cleanup, `close()`, `login_check()`, string diagnostics, accessors, Ajax masking/header behavior, auth login behavior, and RequestUtil behavior remain green.
- The new tests use unit-level synthetic credentials only and do not require live Wikidot, real credentials, cookies, auth JSON, raw response bodies, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This tightens behavior for callers that intentionally passed `username` alone as metadata. Mitigation: `Client.username` represents logged-in identity and is already cleared for unauthenticated clients; unauthenticated metadata should not be passed through credential arguments.
- Risk: This could be confused with Issue 513 credential type validation. Mitigation: this slice only checks that both credential fields are present or absent; type and content validation remain at the login helper/server boundary.
- Risk: The guard could change valid login behavior. Mitigation: no-credential construction, full-credential construction, client tests, adjacent auth/client/Ajax/request utility tests, and full unit tests remain green.
- Risk: Tests could accidentally expose real credentials. Mitigation: all test values are synthetic and the regression patches constructor/login/user-lookup dependencies.

## Out Of Scope

Live login attempts, credential correctness, credential type/content validation beyond pair presence, empty-string rejection, password policy, request retry changes, cookie/header validation, logging changes, and storing username metadata on unauthenticated clients are outside this slice.

## Why This Matters

Configuration-driven browser-free workflows can accidentally supply only one secret. Failing at the constructor boundary prevents silent unauthenticated state that later errors as login-required workflow behavior rather than as the real credential-configuration problem.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used authenticated browser-free workflows, client initialization, login/session setup, logout cleanup, session-cookie validation, Ajax masking, and request-header state as practical operational surfaces.
- Existing local drafts covered returned session-cookie validation, request-header validation, cookie-name/value validation, client string masking, accessor parent integrity, and login credential types, but did not cover partial credential pairs at `Client.__init__(...)`.
- The focused RED failures showed partial credentials silently created unauthenticated clients before the fix. The GREEN regression covers both partial pairs before Ajax module connector setup, login, or user lookup can run.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private content, and private site data out of upstream discussion.
