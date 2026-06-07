# PR Draft: Validate Logging Level Inputs

## Summary

`Client(logging_level=...)` configures the package logger before Ajax module connector setup, authentication, user lookup, or accessor initialization. The public input is documented as a logging level string and now also accurately accepts integer logging constants, but malformed runtime values were previously validated only indirectly by Python's `logging` module. Non-string/non-integer values such as `None`, floats, lists, dictionaries, and arbitrary objects leaked incidental `TypeError` diagnostics, while booleans were accepted as integer levels because `bool` subclasses `int`.

This change adds wikidot.py-side validation in `setup_console_handler(...)`. Named string levels still normalize case-insensitively, integer levels still work, unsupported string levels keep the existing `ValueError("Invalid logging level: ...")` diagnostic, and malformed non-string/non-integer values now raise `ValueError("logging level must be a string or integer")`. Booleans are rejected as malformed levels. `Client(...)` now rejects malformed `logging_level` values before constructing `AjaxModuleConnectorClient`.

## Outcome

Logging configuration now fails deterministically at the library boundary for malformed caller input instead of accepting boolean levels or surfacing lower-level `logging` type errors.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators constructing clients from CLI flags, JSON/YAML config, generated fixtures, local automation, migration scripts, tests, or worker settings where logging levels may arrive as malformed runtime values rather than static literals.

## Current Evidence

Local rollout-backed drafts establish `Client(...)` as the shared entry point for browser-free workflows, authentication/session setup, direct page/user/site access, generated audits, and worker automation. Existing drafts [514-pr-validate-client-partial-credentials.md](514-pr-validate-client-partial-credentials.md), [515-pr-validate-amc-config-object.md](515-pr-validate-amc-config-object.md), [516-pr-validate-amc-cookie-container.md](516-pr-validate-amc-cookie-container.md), and [517-pr-validate-requestutil-method-urls.md](517-pr-validate-requestutil-method-urls.md) progressively harden constructor and low-level request preflight boundaries before deeper side effects start.

Those prior slices are not duplicates. Issue 514 validates username/password pairing before logger setup. Issue 515 validates the Ajax module connector config object after logger setup. Issues 516 and 517 validate AMC header cookie containers and direct URL request inputs. None validates `logging_level` or `setup_console_handler(...)`.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_logging_level(...)` in `src/wikidot/common/logger.py`.
- Preserve case-insensitive named string level conversion such as `"debug"` to `logging.DEBUG`.
- Preserve integer logging levels such as `logging.ERROR`.
- Reject booleans and non-string/non-integer values with `ValueError("logging level must be a string or integer")`.
- Preserve unsupported string diagnostics as `ValueError("Invalid logging level: ...")`.
- Validate the logging level before replacing stream handlers or setting the logger level.
- Update `Client.__init__` typing and documentation to accept `str | int` logging levels.
- Add focused unit tests for direct logger setup and `Client(logging_level=...)` constructor preflight.

## Type Of Change

- Input validation
- Client constructor preflight hardening
- Logger utility behavior hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `setup_console_handler(logger, level)` must accept named string levels case-insensitively and set the expected logger integer level. |
| R2 | `setup_console_handler(logger, logging.ERROR)` and other integer levels must remain valid. |
| R3 | Unsupported string levels must continue to raise `ValueError("Invalid logging level: ...")`. |
| R4 | `None`, floats, arbitrary objects, lists, dictionaries, and booleans must raise `ValueError("logging level must be a string or integer")`. |
| R5 | `Client(logging_level=...)` must reject malformed logging levels before Ajax module connector setup. |
| R6 | Existing client construction, auth behavior, accessors, logger handler setup for valid levels, AMC behavior, and adjacent workflows must remain unchanged. |
| R7 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, logger/client tests, adjacent client/accessor/auth/AMC tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `"debug"` and `"INFO"` set logger levels to `logging.DEBUG` and `logging.INFO`. | `TestSetupConsoleHandler.test_accepts_named_string_and_integer_levels` passed after the guard. | Rejecting valid named strings, making level names case-sensitive, or setting a non-integer logger level rejects this local completion claim. | Logger setup | `src/wikidot/common/logger.py`, `tests/unit/test_logger.py` |
| R2 | Integer logging constants remain accepted. | The same direct logger test passed for `logging.ERROR`. | Rejecting valid integer levels or converting them through string-only logic rejects this local completion claim. | Logger setup | `tests/unit/test_logger.py` |
| R3 | Unknown strings keep the existing explicit invalid-level diagnostic. | `TestSetupConsoleHandler.test_rejects_unknown_string_level` passed for `"not-a-level"`. | Changing the unsupported string error message, accepting arbitrary string attributes, or leaking `logging` internals rejects this local completion claim. | String-level validation | `tests/unit/test_logger.py` |
| R4 | Malformed non-string/non-integer values and booleans fail with one stable wikidot.py-side `ValueError`. | `TestSetupConsoleHandler.test_rejects_malformed_level_values` failed RED for 7 malformed values with lower-level `TypeError` or `DID NOT RAISE`, then passed GREEN after validation was added. | Accepting booleans, leaking `TypeError`, mutating logger state as a substitute for validation, or coercing containers rejects this local completion claim. | Logger setup preflight | `tests/unit/test_logger.py` |
| R5 | Client construction rejects malformed `logging_level` values before Ajax connector construction. | `TestClient.test_init_rejects_malformed_logging_level_before_client_setup` failed RED for 7 malformed values with lower-level `TypeError` or `DID NOT RAISE`, then passed GREEN with `AjaxModuleConnectorClient` not called. | Constructing AMC, attempting login, creating accessors, or accepting booleans rejects this local completion claim. | Client constructor preflight | `src/wikidot/module/client.py`, `tests/unit/test_client.py` |
| R6 | Existing client/logger/AMC behavior remains green. | Logger/client tests passed 44 tests, adjacent logger/client/accessor/auth/AMC tests passed 196 tests, and full unit passed 2345 tests. | Regressing unauthenticated client setup, authenticated client setup, context manager cleanup, accessors, auth, AMC behavior, or valid logger levels rejects this local completion claim. | Adjacent workflows | `tests/unit` |
| R7 | No private material or live action is needed to prove the behavior. | All regressions use synthetic logging-level values and mocks; the draft contains no raw credentials, cookies, auth JSON, rollout paths, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, logger/client and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `8b87c6c fix(logger): validate console level inputs`.

- RED logger/client tests: `uv run pytest tests/unit/test_logger.py tests/unit/test_client.py::TestClient::test_init_rejects_malformed_logging_level_before_client_setup -q` failed 14 malformed cases before the fix with `logging` `TypeError` and boolean `DID NOT RAISE` failures.
- GREEN focused tests: the same focused command passed 18 tests after logging-level validation was added.
- `uv run ruff format src/wikidot/common/logger.py src/wikidot/module/client.py tests/unit/test_logger.py tests/unit/test_client.py` left 4 files unchanged.
- `uv run pytest tests/unit/test_logger.py tests/unit/test_client.py -q` passed 44 tests.
- `uv run ruff check src/wikidot/common/logger.py src/wikidot/module/client.py tests/unit/test_logger.py tests/unit/test_client.py` passed.
- `uv run ruff format --check src/wikidot/common/logger.py src/wikidot/module/client.py tests/unit/test_logger.py tests/unit/test_client.py` passed with 4 files already formatted.
- `uv run pytest tests/unit/test_logger.py tests/unit/test_client.py tests/unit/test_client_accessors.py tests/unit/test_auth.py tests/unit/test_amc_client.py -q` passed 196 tests.
- `uv run mypy src/wikidot/common/logger.py src/wikidot/module/client.py tests/unit/test_logger.py tests/unit/test_client.py` passed with no issues in 4 source files.
- `uv run pyright src/wikidot/common/logger.py src/wikidot/module/client.py tests/unit/test_logger.py tests/unit/test_client.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2345 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `setup_console_handler(logger, "debug")` sets `logger.level == logging.DEBUG`.
- `setup_console_handler(logger, "INFO")` sets `logger.level == logging.INFO`.
- `setup_console_handler(logger, logging.ERROR)` remains valid.
- `setup_console_handler(logger, "not-a-level")` raises `ValueError("Invalid logging level: not-a-level")`.
- `setup_console_handler(logger, None)`, `True`, `False`, `1.5`, `object()`, `[]`, and `{}` raise `ValueError("logging level must be a string or integer")`.
- `Client(logging_level=None)`, `True`, `False`, `1.5`, `object()`, `[]`, and `{}` raise the same validation error before `AjaxModuleConnectorClient` is called.
- Existing default `Client()` construction, valid client logging setup, authenticated client construction, accessors, auth, and AMC behavior remain unchanged.
- The new tests use synthetic logging-level values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Rejecting `True` or `False` tightens behavior for callers that accidentally relied on Python's `bool`-as-`int` behavior. Mitigation: booleans are not meaningful logging levels; callers should pass named strings such as `"INFO"` or integer logging constants such as `logging.INFO`.
- Risk: Accepting arbitrary integers preserves Python logging semantics, including unusual integer values. Mitigation: this slice deliberately avoids redefining logging's integer-level model and only rejects values outside the documented `str | int` boundary.
- Risk: This could be confused with partial credential validation. Mitigation: Issue 514 validates credentials before logger setup; this slice validates `logging_level` during logger setup and before AMC construction.
- Risk: This could be confused with Ajax connector config validation. Mitigation: Issue 515 validates `amc_config` after logger setup; this slice validates logger configuration itself.

## Out Of Scope

Changing logging formatter text, logger names, handler class selection, handler deduplication rules, accepting structural level objects, validating integer ranges, changing Python logging semantics, AMC config validation, credential validation, authentication behavior, live Wikidot behavior, and top-level logging policy are outside this slice.

## Why This Matters

`Client(...)` is the normal entry point for automated wikidot.py workflows, and `logging_level` is likely to come from configuration in those workflows. A malformed config value should fail as a clear wikidot.py input error before request clients, auth, or accessors are initialized.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used `Client(...)` as the root object for page, user, site, auth, and request workflows.
- Existing constructor hardening covered partial credentials and Ajax connector config objects, but did not validate the logger level boundary.
- The focused RED failures showed malformed logging levels either leaking Python `logging` `TypeError` diagnostics or being accepted as boolean integer levels.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
