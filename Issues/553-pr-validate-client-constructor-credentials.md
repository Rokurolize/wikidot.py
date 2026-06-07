# PR Draft: Validate Client Constructor Credential Types

## Summary

`Client(username=..., password=...)` already rejects partial credential pairs before client setup, and `HTTPAuthentication.login(...)` rejects non-string credential values once login is called. One constructor-boundary gap remained: when both credential fields were present but malformed, such as `Client(username=123, password="test-password")` or `Client(username="test-user", password=True)`, the constructor could proceed through logging setup, Ajax module connector construction, patched login, user lookup, and accessor initialization instead of failing at constructor preflight.

This change extends the existing credential-pair preflight so `Client(...)` rejects non-string `username` and `password` values before logger setup, AMC client construction, login, user lookup, or accessor initialization. The existing partial-pair diagnostic remains first, valid unauthenticated construction remains valid, and valid string credential construction still delegates to the authentication helper and user lookup.

## Outcome

Malformed credential values now fail at the `Client(...)` constructor boundary before any client setup side effects.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators constructing clients from environment adapters, JSON/YAML configuration, local fixtures, sandbox bootstrap code, generated credentials, or CI tests where malformed credential types should fail before setup or login work.

## Current Evidence

Existing drafts [513-pr-validate-login-credential-types.md](513-pr-validate-login-credential-types.md) and [514-pr-validate-client-partial-credentials.md](514-pr-validate-client-partial-credentials.md) establish authentication credential preflight as a practical surface. Issue 513 validates direct `HTTPAuthentication.login(...)` credential values after a caller has already reached the auth helper. Issue 514 validates missing half-pairs in `Client(...)`. This slice covers the remaining constructor-specific type boundary when both values are present but malformed.

No upstream issue was filed from this local workspace.

## Changes

- Extend `_validate_client_credentials_pair(...)` to reject non-string `username` and `password` values when present.
- Add constructor regressions for malformed credential types and assert no AMC setup, login, or user lookup occurs.
- Preserve partial credential rejection, unauthenticated construction, valid authenticated construction, login-check behavior, accessor initialization, and adjacent auth behavior.

## Type Of Change

- Input validation
- Constructor preflight
- Authentication setup hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Client(username=123, password="test-password")` and `Client(username=True, password="test-password")` must raise `ValueError("username must be a string")` before client setup. |
| R2 | `Client(username="test-user", password=123)` and `Client(username="test-user", password=True)` must raise `ValueError("password must be a string")` before client setup. |
| R3 | Existing partial credential pairs must still raise `ValueError("username and password must be provided together")` before type validation or client setup. |
| R4 | Valid `Client()`, valid string credential construction, context manager cleanup, login checks, and accessors must remain unchanged. |
| R5 | Client/auth adjacent tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed username values fail before setup. | `TestClient.test_init_rejects_malformed_credentials_before_client_setup` failed RED for username cases with `DID NOT RAISE`, then passed GREEN after constructor validation was added. | Initializing `AjaxModuleConnectorClient`, calling `HTTPAuthentication.login`, calling `User.from_name`, coercing values, or silently storing malformed usernames rejects this local completion claim. | `Client(...)` constructor | `src/wikidot/module/client.py`, `tests/unit/test_client.py` |
| R2 | Malformed password values fail before setup. | The same focused test failed RED for password cases with `DID NOT RAISE`, then passed GREEN after constructor validation was added. | Initializing `AjaxModuleConnectorClient`, calling `HTTPAuthentication.login`, calling `User.from_name`, coercing values, or silently storing malformed passwords rejects this local completion claim. | `Client(...)` constructor | `src/wikidot/module/client.py`, `tests/unit/test_client.py` |
| R3 | Missing half-pairs keep the existing pair diagnostic and precedence. | Existing partial credential tests passed inside the 37-test client suite and 75-test client/auth run. | Reporting username/password type errors for `None` half-pairs, setting up a client, or calling login/user lookup rejects this local completion claim. | Constructor credential pair preflight | `tests/unit/test_client.py` |
| R4 | Existing client/auth behavior remains stable. | Focused constructor credential tests passed 4 tests, client/auth tests passed 75 tests, adjacent client/auth/Ajax/AMC/RequestUtil/site/user tests passed 785 tests, and full unit passed 2632 tests. | Regressing unauthenticated construction, valid authenticated construction, context cleanup, login checks, accessor delegation, auth login/logout behavior, RequestUtil behavior, site lookup, or user lookup rejects this local completion claim. | Client and adjacent auth workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | All regressions use synthetic credential values and patched constructor collaborators; this draft contains no credentials, cookies, auth JSON, raw account data, private response bodies, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private usernames, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `e84487b fix(client): validate constructor credentials`.

- RED credential constructor: `uv run pytest tests/unit/test_client.py::TestClient::test_init_rejects_malformed_credentials_before_client_setup -q` failed 4 tests before the fix with `DID NOT RAISE` because patched auth let malformed values pass through constructor setup.
- GREEN focused: the same focused command passed 4 tests.
- `uv run pytest tests/unit/test_client.py tests/unit/test_auth.py -q` passed 75 tests.
- `uv run pytest tests/unit/test_client.py tests/unit/test_auth.py tests/unit/test_ajax.py tests/unit/test_amc_client.py tests/unit/test_requestutil.py tests/unit/test_site.py tests/unit/test_user.py -q` passed 785 tests.
- `uv run pytest tests/unit -q` passed 2632 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy .` passed with no issues in 87 source files.
- `uv run pyright .` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Client(...)` rejects non-string present username/password values before logger setup, AMC setup, login, user lookup, or accessor initialization.
- Existing missing half-pair validation remains earlier and keeps its current diagnostic.
- Valid unauthenticated and authenticated client construction remain unchanged.
- Direct `HTTPAuthentication.login(...)` credential validation remains intact for callers that bypass `Client(...)`.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Constructor credential type validation could be confused with direct auth validation. Mitigation: Issue 513 still covers `HTTPAuthentication.login(...)`; this slice covers `Client(...)` before setup.
- Risk: Partial-pair validation precedence could change. Mitigation: the pair mismatch check still runs first, and existing partial credential tests remain green.
- Risk: This could accidentally reject valid unauthenticated construction. Mitigation: `None`/`None` remains valid and existing constructor tests remain green.

## Dependencies

- Existing direct auth credential validation remains responsible for direct `HTTPAuthentication.login(...)` calls.
- Existing client partial-pair validation remains the first constructor credential preflight.
- Existing logger setup, AMC construction, login, user lookup, and accessor initialization remain unchanged after valid credential preflight.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`Client(...)` is the main browser-free entry point for wikidot.py workflows. Validating credential types before client setup gives generated config loaders and tests deterministic constructor errors for malformed values without changing direct auth helper behavior, valid login behavior, logout cleanup, or live Wikidot semantics for valid string credentials.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed malformed constructor credentials passing through patched setup without any `ValueError`.
- This slice only validates present credential types in `Client(...)`. It does not change credential correctness, password policy, login retry behavior, session-cookie validation, accessors, direct auth calls, live site behavior, or authentication semantics for valid string credentials.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, and live Wikidot account details out of upstream discussion.
