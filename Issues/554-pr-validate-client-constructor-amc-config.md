# PR Draft: Validate Client Constructor AMC Config

## Summary

`AjaxModuleConnectorClient(..., config=...)` already validates raw connector config objects, but `Client(amc_config=...)` still accepted malformed values until the lower-level connector was constructed. In tests or generated setup code where the connector is patched, malformed values such as `Client(amc_config=True)`, `Client(amc_config="config")`, `Client(amc_config={})`, and `Client(amc_config=object())` could proceed through client setup instead of failing at the public client constructor boundary.

This change adds a client-side `amc_config` preflight before logger setup and AMC client construction. `None` remains valid, real `AjaxModuleConnectorConfig` instances pass through unchanged, and malformed values now raise `ValueError("config must be AjaxModuleConnectorConfig")` before connector setup, login, user lookup, or accessor initialization.

## Outcome

Malformed AMC config values now fail at the `Client(...)` constructor boundary before any client setup side effects.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators constructing clients from environment adapters, JSON/YAML configuration, local fixtures, sandbox bootstrap code, generated connector config, or CI tests where malformed config objects should fail before setup work.

## Current Evidence

Existing draft [515-pr-validate-amc-config-object.md](515-pr-validate-amc-config-object.md) validates `AjaxModuleConnectorClient(..., config=...)` directly. That lower-level guard remains necessary, but it does not prove the public `Client(amc_config=...)` constructor owns its own preflight before logger setup and connector construction. Recent client constructor drafts [514-pr-validate-client-partial-credentials.md](514-pr-validate-client-partial-credentials.md) and [553-pr-validate-client-constructor-credentials.md](553-pr-validate-client-constructor-credentials.md) establish `Client(...)` as an active constructor validation surface.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_client_amc_config(...)` to reject non-`AjaxModuleConnectorConfig` objects when `amc_config` is present.
- Run the AMC config preflight before logger setup and connector construction.
- Add constructor regressions for malformed `amc_config` values and assert no AMC setup, login, or user lookup occurs.
- Preserve `amc_config=None`, valid custom config objects, unauthenticated construction, valid authenticated construction, login-check behavior, accessor initialization, and adjacent auth/connector behavior.

## Type Of Change

- Input validation
- Constructor preflight
- Client setup hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Client(amc_config=True)`, `"config"`, `{}`, and `object()` must raise `ValueError("config must be AjaxModuleConnectorConfig")` before client setup. |
| R2 | `Client(amc_config=None)` and valid `AjaxModuleConnectorConfig` objects must remain valid constructor input. |
| R3 | Existing credential pair/type validation must keep its current precedence and diagnostics. |
| R4 | Valid `Client()`, valid string credential construction, context manager cleanup, login checks, and accessors must remain unchanged. |
| R5 | Client/auth adjacent tests, broader connector/request/site/user tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed AMC config values fail before setup. | `TestClient.test_init_rejects_malformed_amc_config_before_client_setup` failed RED for 4 malformed values with `DID NOT RAISE`, then passed GREEN after constructor validation was added. | Initializing `AjaxModuleConnectorClient`, calling `HTTPAuthentication.login`, calling `User.from_name`, coercing values, or silently storing malformed config objects rejects this local completion claim. | `Client(...)` constructor | `src/wikidot/module/client.py`, `tests/unit/test_client.py` |
| R2 | Missing and valid config values remain accepted. | Existing client construction tests passed in the focused client/auth run, adjacent 789-test run, and full unit run. | Rejecting `None`, copying or replacing a valid custom config object, or changing downstream connector config behavior rejects this local completion claim. | Constructor AMC config preflight | `tests/unit/test_client.py`, `tests/unit/test_amc_client.py` |
| R3 | Credential validation remains stable. | Existing partial credential and malformed credential tests passed inside the 41-test client suite and 79-test client/auth run. | Reporting config errors for credential failures, changing partial-pair precedence, or allowing malformed credentials to reach setup rejects this local completion claim. | Constructor credential preflight | `tests/unit/test_client.py` |
| R4 | Existing client/auth/connector behavior remains stable. | Focused AMC config tests passed 4 tests, client/auth tests passed 79 tests, adjacent client/auth/Ajax/AMC/RequestUtil/site/user tests passed 789 tests, and full unit passed 2636 tests. | Regressing unauthenticated construction, valid authenticated construction, context cleanup, login checks, accessor delegation, auth login/logout behavior, RequestUtil behavior, connector config validation, site lookup, or user lookup rejects this local completion claim. | Client and adjacent workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | All regressions use synthetic config values and patched constructor collaborators; this draft contains no credentials, cookies, auth JSON, raw account data, private response bodies, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private usernames, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `be9c779 fix(client): validate constructor amc config`.

- RED AMC config constructor: `uv run pytest tests/unit/test_client.py::TestClient::test_init_rejects_malformed_amc_config_before_client_setup -q` failed 4 tests before the fix with `DID NOT RAISE` because the patched connector let malformed values pass through constructor setup.
- GREEN focused: the same focused command passed 4 tests.
- `uv run pytest tests/unit/test_client.py tests/unit/test_auth.py -q` passed 79 tests.
- `uv run pytest tests/unit/test_client.py tests/unit/test_auth.py tests/unit/test_ajax.py tests/unit/test_amc_client.py tests/unit/test_requestutil.py tests/unit/test_site.py tests/unit/test_user.py -q` passed 789 tests.
- `uv run pytest tests/unit -q` passed 2636 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Client(...)` rejects non-`AjaxModuleConnectorConfig` present `amc_config` values before logger setup, AMC setup, login, user lookup, or accessor initialization.
- `amc_config=None` and valid `AjaxModuleConnectorConfig` objects remain valid.
- Existing missing half-pair and credential type validation remain intact and keep their current diagnostics.
- Direct `AjaxModuleConnectorClient(..., config=...)` validation remains intact for callers that bypass `Client(...)`.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Constructor config validation could be confused with direct connector validation. Mitigation: Issue 515 still covers `AjaxModuleConnectorClient(..., config=...)`; this slice covers `Client(amc_config=...)` before setup.
- Risk: Valid default config construction could be rejected. Mitigation: `None` remains valid and existing `Client()` construction tests remain green.
- Risk: This could accidentally change auth setup behavior. Mitigation: credential, auth, connector, RequestUtil, site, and user adjacent tests remain green.

## Dependencies

- Existing direct connector config validation remains responsible for direct `AjaxModuleConnectorClient(...)` calls.
- Existing client credential validation remains the first credential preflight.
- Existing logger setup, AMC construction, login, user lookup, and accessor initialization remain unchanged after valid constructor preflight.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`Client(...)` is the main browser-free entry point for wikidot.py workflows. Validating its connector config object before setup gives generated config loaders and tests deterministic constructor errors for malformed values without changing direct connector behavior, valid client setup, logout cleanup, or live Wikidot semantics for valid config objects.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed malformed constructor AMC config values passing through patched setup without any `ValueError`.
- This slice only validates present `amc_config` objects in `Client(...)`. It does not change config field validation, retry timing, request construction, credential correctness, login retry behavior, session-cookie validation, accessors, direct connector calls, live site behavior, or authentication semantics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, and live Wikidot account details out of upstream discussion.
