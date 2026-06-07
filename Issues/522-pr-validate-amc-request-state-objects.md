# PR Draft: Validate AMC Request State Objects

## Summary

`AjaxModuleConnectorClient.request(...)` validates caller request bodies, exception controls, site overrides, and numeric config fields before HTTP work, but the connector's public `config` and `header` attributes remain mutable after construction. A caller, generated fixture, or test double could directly replace `client.config` with a non-`AjaxModuleConnectorConfig` object, replace `client.header` with a non-`AjaxRequestHeader` object, or corrupt header state before calling `request(...)`.

Before this change, replaced config objects failed with incidental attribute errors such as `'dict' object has no attribute 'request_timeout'`. Replaced header objects failed inside the async request task with lower-level `.cookie` attribute errors. Malformed header state was worse under `return_exceptions=True`: local header validation errors could be returned as per-request exceptions rather than raised as request preflight failures.

This change validates request-time connector state before async task creation. `request(...)` now requires stored config state to be an `AjaxModuleConnectorConfig`, requires stored header state to be an `AjaxRequestHeader` for non-empty request batches, computes validated request headers once before the request tasks, and extracts the current `wikidot_token7` only after cookie state is confirmed to be a dictionary. Valid raw AMC requests, valid header token propagation, explicit body token precedence, empty request batches, return-exceptions handling for real request failures, retry behavior, response parsing, auth, RequestUtil, client, and site workflows remain unchanged.

## Outcome

Malformed mutable AMC connector state now fails deterministically at the raw request boundary instead of leaking lower-level attribute errors or being hidden by `return_exceptions=True`.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free clients, generated fixtures, raw AMC batches, login/session setup, mocked connectors, JSON/YAML adapters, continuation ledgers, local automation, or tests that may retain and mutate `AjaxModuleConnectorClient` instances.

## Current Evidence

Local rollout-backed drafts establish raw AMC request execution as a shared lower-level surface. [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md), [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), [401-pr-validate-amc-request-bodies.md](401-pr-validate-amc-request-bodies.md), and [517-pr-validate-requestutil-method-urls.md](517-pr-validate-requestutil-method-urls.md) covered direct request controls and request inputs. [515-pr-validate-amc-config-object.md](515-pr-validate-amc-config-object.md) covered constructor-time config objects, [520-pr-validate-amc-config-fields.md](520-pr-validate-amc-config-fields.md) covered config field construction, and [521-pr-validate-amc-header-serialization-state.md](521-pr-validate-amc-header-serialization-state.md) covered `AjaxRequestHeader.get_header(...)` serialization state.

Those prior slices are not duplicates. Issue 515 validates the `config` argument before it becomes stored connector state; this slice validates stored `client.config` after direct replacement. Issue 521 validates `AjaxRequestHeader.get_header(...)`; this slice makes `AjaxModuleConnectorClient.request(...)` run that header validation before async gather can convert local header errors into returned per-request exceptions. No upstream issue was filed from this local workspace.

## Changes

- Add request-time validation for stored `client.config` objects with `ValueError("config must be AjaxModuleConnectorConfig")`.
- Add request-time validation for stored `client.header` objects with `ValueError("header must be AjaxRequestHeader")` on non-empty raw AMC batches.
- Precompute validated request headers before async request task creation, so malformed mutable header state is raised as local preflight even when `return_exceptions=True`.
- Extract the header `wikidot_token7` value only after the cookie state is confirmed to be a dictionary.
- Preserve valid request headers, default token behavior, explicit request-body token precedence, empty batches, retry behavior, response parsing, and adjacent workflows.
- Add focused tests for mutated request config objects, mutated request header objects, and malformed header state under `return_exceptions=True`.

## Type Of Change

- Input/state validation
- Raw AMC request preflight hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `AjaxModuleConnectorClient.request(...)` must reject directly replaced non-`AjaxModuleConnectorConfig` `client.config` state before HTTP work. |
| R2 | `request(...)` must reject directly replaced non-`AjaxRequestHeader` `client.header` state before async task creation for non-empty request batches. |
| R3 | `request(..., return_exceptions=True)` must still raise malformed local header state instead of returning it as a per-request exception. |
| R4 | Existing valid raw AMC request behavior must remain unchanged, including default header token propagation and explicit body token precedence. |
| R5 | Existing AMC, client, auth, RequestUtil, and site workflows must remain green. |
| R6 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, AMC tests, adjacent tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Directly replacing `client.config` with `None`, arbitrary objects, dictionaries, strings, or booleans raises `ValueError("config must be AjaxModuleConnectorConfig")` and sends no requests. | `test_request_rejects_mutated_config_object_before_request` failed RED with lower-level `AttributeError` diagnostics, then passed GREEN. | Reading `.request_timeout` on malformed config state, issuing HTTP requests, or silently defaulting replaced state rejects this local completion claim. | Raw AMC request preflight | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | Directly replacing `client.header` with `None`, arbitrary objects, dictionaries, strings, or booleans raises `ValueError("header must be AjaxRequestHeader")` and sends no requests. | `test_request_rejects_mutated_header_object_before_request` failed RED with async-task `.cookie` `AttributeError`, then passed GREEN. | Letting header replacement reach `asyncio.gather(...)`, returning attribute errors, or issuing HTTP requests rejects this local completion claim. | Raw AMC request preflight | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R3 | Mutated scalar header state, non-dict cookie state, and malformed cookie names raise their existing local header diagnostics even under `return_exceptions=True`. | `test_request_rejects_mutated_header_state_before_returning_exceptions` failed RED with `DID NOT RAISE`, then passed GREEN. | Returning local validation failures as tuple entries, hiding malformed header state behind exception-returning mode, or issuing HTTP requests rejects this local completion claim. | Header/request-state boundary | `tests/unit/test_amc_client.py` |
| R4 | Valid raw AMC request behavior remains stable. | Existing AMC tests for success, multiple requests, token defaults, explicit token preservation, retry, response parsing, and exception-returning behavior passed inside the 207-test AMC suite. | Changing request bodies, token precedence, headers, retry behavior, response status handling, or valid `return_exceptions=True` behavior rejects this local completion claim. | Raw AMC request behavior | `tests/unit/test_amc_client.py` |
| R5 | Existing adjacent workflows remain green. | Adjacent AMC/client/auth/RequestUtil/site suites passed 598 tests, and full unit passed 2443 tests. | Regressing client construction, auth login/logout cookie state, RequestUtil forwarding, site workflows, or raw AMC wrappers rejects this local completion claim. | AMC and adjacent workflows | `tests/unit` |
| R6 | No private material or live action is needed to prove the behavior. | All regressions use synthetic state objects and local unit tests; the draft contains no raw credentials, cookies, auth JSON, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `8b65a66 fix(amc): validate request state objects`.

- RED request-state tests: `uv run pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_mutated_config_object_before_request tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_mutated_header_object_before_request tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_mutated_header_state_before_returning_exceptions -q` failed 13 cases before the fix: 5 malformed config replacements with `AttributeError`, 5 malformed header replacements with async-task `.cookie` `AttributeError`, and 3 malformed header-state cases with `DID NOT RAISE`.
- GREEN focused tests: the same focused command passed 13 tests after request-state preflight was added.
- `uv run ruff format src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed with 2 files left unchanged.
- `uv run pytest tests/unit/test_amc_client.py -q` passed 207 tests.
- `uv run ruff check src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed.
- `uv run ruff format --check src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit/test_amc_client.py tests/unit/test_client.py tests/unit/test_auth.py tests/unit/test_requestutil.py tests/unit/test_site.py -q` passed 598 tests.
- `uv run pytest tests/unit -q` passed 2443 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `client.config = object()` and other non-config replacements cause `client.request([{"moduleName": "Test"}])` to raise `ValueError("config must be AjaxModuleConnectorConfig")` before any request is sent.
- `client.header = object()` and other non-header replacements cause non-empty raw AMC requests to raise `ValueError("header must be AjaxRequestHeader")` before async tasks are created.
- Malformed `AjaxRequestHeader` state still raises its existing local diagnostics when `client.request(..., return_exceptions=True)` is called, rather than being returned as a per-request exception.
- Valid raw AMC requests still send the same endpoint, headers, request body token, and explicit token values.
- Existing AMC, auth, client, RequestUtil, and site tests remain green.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This could be confused with constructor-time config validation. Mitigation: Issue 515 covers the constructor argument; this slice covers public mutable connector state after construction.
- Risk: This could be confused with header serialization validation. Mitigation: Issue 521 covers `AjaxRequestHeader.get_header(...)`; this slice ensures the raw AMC request boundary calls that validation before async exception-returning mode can hide local input errors.
- Risk: Precomputing headers once per `request(...)` call could be seen as a behavior change. Mitigation: `request(...)` is synchronous from the caller's perspective, valid header/token behavior remains covered, and per-attempt header recomputation was only exposing mutable state races and lower-level diagnostics.
- Risk: Rejecting mutated state may expose tests or generated fixtures that directly replace connector internals. Mitigation: callers should replace config/header state only with valid `AjaxModuleConnectorConfig` and `AjaxRequestHeader` objects, or use the existing mutation APIs.

## Out Of Scope

Making connector state immutable, changing `AjaxRequestHeader` storage, changing empty-batch config validation, accepting non-dataclass config mappings, changing retry timing, changing `return_exceptions` behavior for real HTTP/AMC failures, changing auth login/logout behavior, live Wikidot behavior, and upstream Issue/PR creation are outside this slice.

## Why This Matters

`AjaxModuleConnectorClient.request(...)` is the shared raw request executor beneath browser-free Wikidot operations. Request-time mutable state should fail with wikidot.py-side diagnostics before async task execution, not as incidental Python attribute errors or returned local validation exceptions.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used raw AMC batches, login/session setup, request headers, retry controls, generated fixtures, and direct request utilities that depend on `AjaxModuleConnectorClient.request(...)`.
- Existing drafts covered constructor config objects, config fields, request bodies, request controls, header field validation, and header serialization, but did not validate direct replacement of stored request-state objects at the raw AMC request boundary.
- The focused RED failures showed malformed direct mutations reaching attribute errors or being hidden by `return_exceptions=True`. The GREEN regression covers those values before request tasks or HTTP work can run.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
