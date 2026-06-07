# PR Draft: Validate Ajax Module Connector Config Fields

## Summary

`AjaxModuleConnectorConfig(...)` is the public dataclass used to carry Ajax Module Connector timeout, retry, backoff, concurrency, and retry-batch defaults through raw AMC, direct URL, auth, site, page, and private-message workflows. Field values were validated only later at request helper boundaries. Direct construction still accepted malformed values such as `request_timeout=None`, `attempt_limit=True`, `retry_interval="1"`, `semaphore_limit=0`, `retry_batch_size=1.5`, or `retry_max_retries=False`, leaving an invalid config object available for storage, mocks, generated configuration, and downstream helper calls.

This change validates all documented config fields during dataclass construction. Positive number, positive integer, non-negative number, and non-negative retry-count rules now fail immediately with stable `ValueError` diagnostics. Existing request-time validation remains in place for config objects mutated after construction, so raw AMC and RequestUtil still reject malformed mutable state before network work.

## Outcome

Malformed Ajax Module Connector config field values now fail at the configuration boundary instead of creating an invalid object that fails later in request, site retry, direct URL, auth, page, or private-message paths.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build `AjaxModuleConnectorConfig` from JSON, YAML, CLI flags, spreadsheets, environment variables, generated fixtures, mocked clients, browser-free automation, sandbox scripts, archival jobs, or local CI fixtures.

## Current Evidence

Local rollout-backed drafts repeatedly identify browser-free clients, raw AMC request execution, direct URL batches, site retry batches, ListPages/page-source workflows, private-message retry batches, auth setup, generated configuration, and mocked clients as practical surfaces. Existing drafts [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md), [394-pr-validate-site-amc-retry-controls.md](394-pr-validate-site-amc-retry-controls.md), [395-pr-validate-http-request-timeouts.md](395-pr-validate-http-request-timeouts.md), [396-pr-validate-listpages-retry-control.md](396-pr-validate-listpages-retry-control.md), [397-pr-validate-private-message-retry-controls.md](397-pr-validate-private-message-retry-controls.md), and [515-pr-validate-amc-config-object.md](515-pr-validate-amc-config-object.md) show that config-driven retry and timeout behavior is already a practical safety surface.

Those prior slices are not duplicates. Issues 392 and 393 validate config-derived request fields when raw AMC or RequestUtil starts work, not when the config object is created. Issue 394 validates site-level retry defaults before `Site.amc_request_with_retry(...)` issues work. Issues 396 and 397 validate narrower downstream retry controls. Issue 515 validates that the constructor receives an `AjaxModuleConnectorConfig` object rather than an arbitrary container, and explicitly left field values for a later slice. This change closes that field-construction gap while keeping request-time guards for mutated config objects.

No upstream issue was filed from this local workspace.

## Changes

- Add `AjaxModuleConnectorConfig.__post_init__(...)` validation for every config field.
- Validate `request_timeout` as a non-bool positive number.
- Validate `attempt_limit`, `semaphore_limit`, and `retry_batch_size` as non-bool positive integers.
- Validate `retry_interval`, `max_backoff`, and `backoff_factor` as non-bool non-negative numbers.
- Validate `retry_max_retries` as a non-bool non-negative integer.
- Preserve valid defaults and valid custom config values, including zero retry/backoff intervals where already supported.
- Keep raw AMC and RequestUtil request-time validation for config objects mutated after construction.

## Type Of Change

- Input validation
- Configuration boundary hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `AjaxModuleConnectorConfig(request_timeout=...)` must reject malformed timeout values with `ValueError("request_timeout must be a positive number")`. |
| R2 | `attempt_limit`, `semaphore_limit`, and `retry_batch_size` must reject malformed values with `ValueError("<field> must be a positive integer")`. |
| R3 | `retry_interval`, `max_backoff`, and `backoff_factor` must reject malformed values with `ValueError("<field> must be a non-negative number")`. |
| R4 | `retry_max_retries` must reject malformed values with `ValueError("retry_max_retries must be a non-negative integer")`. |
| R5 | Valid default and custom config construction must remain unchanged, including `retry_batch_size` and `retry_max_retries` defaults. |
| R6 | Existing request-time validation for mutable config objects must remain green for raw AMC and RequestUtil callers. |
| R7 | Existing auth, client, site, page, and private-message workflows that use valid config values must remain green. |
| R8 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, affected AMC and RequestUtil tests, adjacent tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None`, booleans, strings, zero, and negative timeouts fail at config construction. | `TestAjaxModuleConnectorConfig.test_rejects_invalid_request_timeout` failed RED for 6 malformed values with `DID NOT RAISE`, then passed GREEN after `__post_init__` validation was added. | Constructing an invalid timeout config, accepting booleans, coercing strings, or deferring the error until request work rejects this local completion claim. | AMC config construction | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | Positive-integer fields reject `None`, booleans, strings, zero, negative integers, and floats during construction. | `test_rejects_invalid_positive_integer_fields` failed RED for 21 malformed field/value cases, then passed GREEN. | Accepting `True` as `1`, accepting `False` as `0`, accepting floats or strings, or creating a zero semaphore/batch config rejects this local completion claim. | AMC config construction | `tests/unit/test_amc_client.py` |
| R3 | Non-negative number fields reject `None`, booleans, strings, and negative numbers during construction. | `test_rejects_invalid_non_negative_number_fields` failed RED for 15 malformed field/value cases, then passed GREEN. | Accepting `False` as a no-wait value, accepting strings, or storing negative sleep/backoff controls rejects this local completion claim. | AMC config construction | `tests/unit/test_amc_client.py` |
| R4 | `retry_max_retries` rejects malformed non-integer retry counts during construction. | `test_rejects_invalid_retry_max_retries` failed RED for 6 malformed values, then passed GREEN. | Treating booleans as retry counts, accepting strings/floats, or storing negative retry counts rejects this local completion claim. | AMC config construction | `tests/unit/test_amc_client.py` |
| R5 | Valid defaults and valid custom config values remain stable. | `TestAjaxModuleConnectorConfig.test_default_values` and `test_custom_values` passed after adding assertions for `retry_batch_size` and `retry_max_retries`. | Changing defaults, dropping custom retry defaults, or mutating valid values rejects this local completion claim. | AMC config construction | `tests/unit/test_amc_client.py` |
| R6 | Mutated config objects are still rejected at request-time boundaries before network work. | AMC and RequestUtil config-validation tests were adjusted to mutate a valid config after construction; focused AMC passed 169 tests and RequestUtil passed 99 tests. | Removing request-time guards, issuing HTTP work for mutated invalid config values, or requiring invalid construction to test mutable state rejects this local completion claim. | Raw AMC and RequestUtil preflight | `tests/unit/test_amc_client.py`, `tests/unit/test_requestutil.py` |
| R7 | Valid adjacent workflows remain green. | Adjacent AMC/RequestUtil/client/auth/site/page/private-message suites passed 922 tests, and full unit passed 2405 tests. | Regressing valid config use in auth, client construction, site retry batches, page workflows, or private-message workflows rejects this local completion claim. | Valid downstream workflows | `tests/unit` |
| R8 | No private material or live action is needed to prove the behavior. | All regressions use synthetic malformed values and local unit tests; the draft contains no raw credentials, cookies, auth JSON, rollout paths, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `b030374 fix(amc): validate config field construction`.

- RED config-constructor tests: `uv run pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorConfig::test_rejects_invalid_request_timeout tests/unit/test_amc_client.py::TestAjaxModuleConnectorConfig::test_rejects_invalid_positive_integer_fields tests/unit/test_amc_client.py::TestAjaxModuleConnectorConfig::test_rejects_invalid_non_negative_number_fields tests/unit/test_amc_client.py::TestAjaxModuleConnectorConfig::test_rejects_invalid_retry_max_retries -q` failed 48 malformed field/value cases before the fix with `DID NOT RAISE`.
- GREEN focused tests: the same focused command passed 48 tests after constructor validation was added.
- `uv run pytest tests/unit/test_amc_client.py -q` passed 169 tests.
- `uv run pytest tests/unit/test_requestutil.py -q` passed 99 tests.
- `uv run ruff format src/wikidot/connector/ajax.py tests/unit/test_amc_client.py tests/unit/test_requestutil.py` left 3 files unchanged.
- `uv run ruff check src/wikidot/connector/ajax.py tests/unit/test_amc_client.py tests/unit/test_requestutil.py` passed.
- `uv run ruff format --check src/wikidot/connector/ajax.py tests/unit/test_amc_client.py tests/unit/test_requestutil.py` passed with 3 files already formatted.
- `uv run mypy src/wikidot/connector/ajax.py tests/unit/test_amc_client.py tests/unit/test_requestutil.py` passed with no issues in 3 source files.
- `uv run pyright src/wikidot/connector/ajax.py tests/unit/test_amc_client.py tests/unit/test_requestutil.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit/test_amc_client.py tests/unit/test_requestutil.py tests/unit/test_client.py tests/unit/test_auth.py tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_private_message.py -q` passed 922 tests.
- `uv run pytest tests/unit -q` passed 2405 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `AjaxModuleConnectorConfig(request_timeout=None)`, `True`, `False`, `"1"`, `0`, and `-0.1` raise `ValueError("request_timeout must be a positive number")`.
- `AjaxModuleConnectorConfig(attempt_limit=...)`, `semaphore_limit=...`, and `retry_batch_size=...` reject `None`, booleans, strings, zero, negative integers, and floats with `ValueError("<field> must be a positive integer")`.
- `AjaxModuleConnectorConfig(retry_interval=...)`, `max_backoff=...`, and `backoff_factor=...` reject `None`, booleans, strings, and negative numbers with `ValueError("<field> must be a non-negative number")`.
- `AjaxModuleConnectorConfig(retry_max_retries=None)`, booleans, strings, negative integers, and floats raise `ValueError("retry_max_retries must be a non-negative integer")`.
- Valid default config construction still yields `request_timeout=20`, `attempt_limit=5`, `retry_interval=1.0`, `max_backoff=60.0`, `backoff_factor=2.0`, `semaphore_limit=10`, `retry_batch_size=50`, and `retry_max_retries=3`.
- Valid custom config construction still preserves caller-provided values.
- Raw AMC and RequestUtil still reject invalid config values if a valid config object is mutated after construction.
- Existing auth, client, site, page, private-message, raw AMC, direct URL RequestUtil, and shared helper tests remain green.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This tightens behavior for callers that intentionally constructed invalid configs and relied on later helper errors. Mitigation: the config object is the configuration boundary; invalid field values should fail before being stored or passed across modules.
- Risk: Rejecting booleans tightens behavior for callers that accidentally relied on Python's `bool` subclassing `int`. Mitigation: booleans are configuration parsing mistakes for numeric retry, timeout, and batch controls.
- Risk: Rejecting strings exposes text-based config parsing bugs. Mitigation: JSON/YAML/CLI/environment adapters should parse text into real numbers before constructing `AjaxModuleConnectorConfig`.
- Risk: Constructor validation could be confused with request-time validation. Mitigation: request-time guards remain for mutated config objects, and tests cover those mutable-state paths.
- Risk: Constructor validation could be confused with Issue 515. Mitigation: Issue 515 validates the config object type; this slice validates the fields inside a real config object.

## Out Of Scope

Changing retry defaults, changing request-time retry behavior, accepting structural duck-typed config containers, making the config dataclass frozen, validating later attribute mutation immediately, changing site/page/private-message retry policies, changing timeout semantics, changing live Wikidot behavior, and upstream Issue/PR creation are outside this slice.

## Why This Matters

`AjaxModuleConnectorConfig` is often the first object created after parsing timeout and retry settings. Failing at construction gives operators one local diagnostic before invalid state can move through raw AMC, RequestUtil, auth, site, page, and private-message code.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used browser-free clients, raw AMC batches, direct URL batches, site retry helpers, page/ListPages flows, private-message retries, generated fixtures, and mocked configs.
- Existing drafts covered request-time numeric guards, site retry defaults, direct URL guards, downstream retry controls, HTTP helper validation, and config-object type validation, but did not validate `AjaxModuleConnectorConfig` fields at construction.
- The focused RED failures showed invalid field values could be stored directly in a config object; the GREEN regression rejects those values before the object exists.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
