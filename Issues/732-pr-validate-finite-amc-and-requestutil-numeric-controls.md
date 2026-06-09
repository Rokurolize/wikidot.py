# PR Draft: Validate Finite AMC And Direct URL Numeric Controls

## Summary

`AjaxModuleConnectorConfig`, `AjaxModuleConnectorClient.request(...)`, and `RequestUtil.request(...)` already validate timeout, retry, backoff, and concurrency controls for wrong types, booleans, strings, negative values, zero positive-only values, and non-integer counts. One numeric edge remained at these higher-level request boundaries: Python `float("nan")`, `float("inf")`, and `-float("inf")` are still `float` values. `nan` bypasses normal comparison checks, and positive infinity is greater than zero, so local AMC and direct URL validators could accept non-finite request timeouts, retry intervals, backoff factors, and maximum backoff values.

This change converts numeric controls once, requires `math.isfinite(...)`, and then applies the existing range checks. Existing diagnostics are preserved: positive timeouts still raise `ValueError("request_timeout must be a positive number")`, and retry/backoff controls still raise `ValueError("<field> must be a non-negative number")`. Valid finite positive timeouts, valid finite retry controls, zero retry intervals/backoff caps/factors, retry behavior, status handling, header forwarding, request-body handling, and adjacent callers remain unchanged.

## Outcome

AMC and direct URL request callers no longer accept `NaN` or infinite numeric controls that can propagate into HTTP timeout setup, retry-loop sleeps, or backoff calculation. Callers now get deterministic wikidot.py-side validation at the same public request boundaries as the existing numeric-control checks.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using raw Ajax Module Connector requests, direct GET/POST URL batches, browser-free site probing, profile lookup, page/forum/private-message/member/application workflows, generated audits, migration tools, archival workflows, or moderation tools that may load numeric controls from Python objects, generated structures, JSON/YAML adapters, CLI parsing, spreadsheets, or test fixtures.

## Current Evidence

Local rollout-backed drafts repeatedly identify raw AMC and direct URL request helpers as practical infrastructure. [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md) validates raw AMC request numeric controls for ordinary malformed values. [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md) validates direct URL request numeric controls for ordinary malformed values. [520-pr-validate-amc-config-fields.md](520-pr-validate-amc-config-fields.md) validates `AjaxModuleConnectorConfig` construction fields. [731-pr-validate-finite-http-numeric-controls.md](731-pr-validate-finite-http-numeric-controls.md) validates non-finite values in lower-level `wikidot.util.http` helper arguments.

Those prior slices are not duplicates. Issues 392, 393, and 520 covered `None`, booleans, strings, negative values, zero positive-only values, and non-integer count values, but did not cover `NaN` or infinity. Issue 731 covered shared low-level HTTP helpers in `wikidot.util.http`, not the higher-level local validators in `wikidot.connector.ajax` and `wikidot.util.requestutil`.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md), [520-pr-validate-amc-config-fields.md](520-pr-validate-amc-config-fields.md), and [731-pr-validate-finite-http-numeric-controls.md](731-pr-validate-finite-http-numeric-controls.md).

## Changes

- Require finite values in `wikidot.connector.ajax._validate_positive_number_option(...)` after float conversion and before returning a request timeout control.
- Require finite values in `wikidot.connector.ajax._validate_non_negative_number_option(...)` after float conversion and before returning retry/backoff controls.
- Require finite values in `wikidot.util.requestutil._validate_positive_number_option(...)` after float conversion and before returning a direct URL request timeout control.
- Add non-finite constructor coverage for `AjaxModuleConnectorConfig.request_timeout`, `retry_interval`, `max_backoff`, and `backoff_factor`.
- Add non-finite request-time coverage for mutated raw AMC timeout/retry/backoff config values.
- Add non-finite request-time coverage for direct URL timeout/retry/backoff config values.
- Preserve existing messages, valid zero non-negative retry controls, valid finite positive timeouts, status handling, retry behavior, request body handling, header forwarding, and adjacent caller workflows.

## Type Of Change

- Input validation
- Public request-boundary behavior hardening
- AMC and direct URL retry/timeout preflight safety
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `AjaxModuleConnectorConfig(...)` must reject `NaN`, positive infinity, and negative infinity for `request_timeout` with `ValueError("request_timeout must be a positive number")`. |
| R2 | `AjaxModuleConnectorConfig(...)` must reject `NaN`, positive infinity, and negative infinity for `retry_interval`, `max_backoff`, and `backoff_factor` with `ValueError("<field> must be a non-negative number")`. |
| R3 | `AjaxModuleConnectorClient.request(...)` must reject mutated non-finite `request_timeout`, `retry_interval`, `max_backoff`, and `backoff_factor` config values before issuing HTTP requests. |
| R4 | `RequestUtil.request(...)` must reject mutated non-finite `request_timeout`, `retry_interval`, `max_backoff`, and `backoff_factor` config values before issuing GET/POST requests. |
| R5 | Existing validation messages and malformed-value categories from Issues 392, 393, and 520 must remain unchanged. |
| R6 | Valid finite AMC and direct URL behavior must remain unchanged, including zero retry intervals/backoff caps/factors, positive finite timeouts, 4xx no-retry behavior, 5xx retries, timeout/network retries, raw AMC response handling, direct URL header forwarding, and `return_exceptions` behavior. |
| R7 | Adjacent HTTP, Ajax, Auth, Client, QuickModule, and Site workflows must remain green with valid finite configuration. |
| R8 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, affected AMC and RequestUtil tests, adjacent tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-finite AMC timeouts fail during config construction. | Focused RED failed `NaN` and positive infinity constructor cases with `DID NOT RAISE`; focused GREEN passed after `math.isfinite(...)` was added. | Accepting `NaN` or infinity, raising an unrelated later `httpx` error, or changing existing timeout diagnostics rejects this local completion claim. | AMC config construction | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | Non-finite AMC retry/backoff controls fail during config construction. | Focused RED failed new `NaN` and positive infinity constructor cases for `retry_interval`, `max_backoff`, and `backoff_factor`; focused GREEN passed after the finite check. | Returning a config with non-finite retry/backoff controls or changing existing diagnostics rejects this local completion claim. | AMC config construction | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R3 | Mutated non-finite AMC request controls fail before request setup. | Focused GREEN covered raw AMC request-time timeout and retry/backoff validation and asserts no requests are issued. | Issuing a POST, sleeping on `nan` or infinite backoff, passing non-finite timeout to `httpx`, or raising an unrelated later error rejects this local completion claim. | Raw AMC request preflight | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R4 | Mutated non-finite direct URL controls fail before request setup. | Focused RED for RequestUtil timeout allowed `NaN`/infinity through to unmatched HTTP attempts; focused GREEN passed after the local timeout validator required finite values. Retry/backoff non-finite cases pass through the shared helper fixed in Issue 731 and are covered at the direct URL boundary. | Issuing GET/POST requests, opening an async client with malformed timeout, sleeping on non-finite backoff, or raising an unrelated later error rejects this local completion claim. | Direct URL request preflight | `src/wikidot/util/requestutil.py`, `tests/unit/test_requestutil.py` |
| R5 | Existing malformed-value diagnostics remain stable. | The expanded parameter tables include the previous invalid values and still match the same messages. | Changing `None`, booleans, strings, negative retry controls, zero timeout, negative timeout, or non-integer count diagnostics rejects this local completion claim. | Validator compatibility | affected unit tests |
| R6 | Valid AMC and direct URL behavior remains stable. | `tests/unit/test_amc_client.py tests/unit/test_requestutil.py` passed 394 tests after the finite checks. | Regressing valid zero retry controls, positive finite timeouts, response parsing, status classification, timeout/network retries, `return_exceptions`, headers, or body handling rejects this local completion claim. | Request behavior | affected unit suites |
| R7 | Adjacent callers remain green. | Adjacent Ajax/Auth/Client/HTTP/QuickModule/Site tests passed 763 tests, and full unit passed 3696 tests. | Regressing login handling, Ajax helpers, client setup, shared HTTP retry helpers, QuickModule lookup, site probing, raw AMC, or direct URL reads rejects this local completion claim. | Adjacent workflows | affected unit suites |
| R8 | No live site state or private material is needed. | All regressions use unit-level synthetic values, mocks, and `pytest-httpx` request assertions. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, affected tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `cecc882 fix(http): validate finite request numeric controls`.

- RED: `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorConfig::test_rejects_invalid_request_timeout tests/unit/test_amc_client.py::TestAjaxModuleConnectorConfig::test_rejects_invalid_non_negative_number_fields tests/unit/test_requestutil.py::TestRequestUtilConfigValidation::test_rejects_invalid_request_timeout_before_request -q` failed before the fix with 12 failing non-finite cases and 4 RequestUtil teardown errors caused by unmatched HTTP attempts.
- GREEN focused: `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorConfig::test_rejects_invalid_request_timeout tests/unit/test_amc_client.py::TestAjaxModuleConnectorConfig::test_rejects_invalid_non_negative_number_fields tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_invalid_positive_timeout_config_before_request tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_invalid_retry_number_config_before_request tests/unit/test_requestutil.py::TestRequestUtilConfigValidation::test_rejects_invalid_request_timeout_before_request tests/unit/test_requestutil.py::TestRequestUtilConfigValidation::test_rejects_invalid_retry_number_config_before_request -q` passed 120 tests.
- `uv run --extra test pytest tests/unit/test_amc_client.py tests/unit/test_requestutil.py -q` passed 394 tests.
- `uv run --extra test pytest tests/unit/test_ajax.py tests/unit/test_auth.py tests/unit/test_client.py tests/unit/test_http.py tests/unit/test_quick_module.py tests/unit/test_site.py -q` passed 763 tests.
- `uv run --extra test pytest tests/unit -q` passed 3696 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `AjaxModuleConnectorConfig(request_timeout=float("nan"))`, `float("inf")`, and `-float("inf")` raise `ValueError("request_timeout must be a positive number")`.
- `AjaxModuleConnectorConfig(retry_interval=float("nan"))`, `max_backoff=float("inf")`, and `backoff_factor=-float("inf")` raise `ValueError("<field> must be a non-negative number")` for the corresponding field.
- `AjaxModuleConnectorClient.request(...)` rejects mutated non-finite `request_timeout`, `retry_interval`, `max_backoff`, and `backoff_factor` before issuing HTTP requests.
- `RequestUtil.request(...)` rejects mutated non-finite `request_timeout`, `retry_interval`, `max_backoff`, and `backoff_factor` before issuing GET/POST requests.
- Existing malformed-value messages from Issues 392, 393, and 520 remain stable.
- Valid finite AMC and direct URL retry/timeout behavior remains green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A caller intentionally used `float("inf")` as a request timeout or retry control. Mitigation: these fields control concrete HTTP timeout and sleep/backoff behavior; unbounded wait semantics should be explicit at a higher level, not represented by non-finite numeric values inside request retry code.
- Risk: Rejecting `NaN` exposes configuration parsing bugs from generated data or test fixtures. Mitigation: `NaN` cannot produce meaningful timeout or backoff behavior; callers should normalize configuration before constructing AMC or direct URL request config.
- Risk: The slice could be confused with Issues 392, 393, or 520. Mitigation: those drafts covered type and ordinary range validation; this follow-up covers IEEE non-finite floats that passed the existing validators.
- Risk: The slice could be confused with Issue 731. Mitigation: Issue 731 covered shared `wikidot.util.http` helpers; this slice covers the higher-level local validators in AMC and direct URL request code.
- Risk: Finite checks could accidentally change valid zero retry controls. Mitigation: `_validate_non_negative_number_option(...)` still accepts finite zero values, and full affected request tests remain green.

## Dependencies

- Existing `AjaxModuleConnectorConfig`, `AjaxModuleConnectorClient.request(...)`, and `RequestUtil.request(...)` remain the source of truth for their respective higher-level request boundaries.
- Existing lower-level `wikidot.util.http` finite validation from Issue 731 remains separate and unchanged.
- Existing site, page, forum, private-message, member, application, profile lookup, and direct URL workflows continue to use their current wrappers.
- The validation does not affect URL construction, headers, form data, response parsing, higher-level exception conversion, retry policy, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-shape validation, result ergonomics, action/read boundaries, or measured complexity candidates outside this now-covered higher-level finite numeric-control validation.

## Upstream-Safe Motivation

AMC and direct URL request helpers sit below multiple browser-free workflows. Since retry intervals, backoff factors, maximum backoff values, and request timeouts control wait behavior, wikidot.py should reject `NaN` and infinite values at the request boundary instead of allowing non-finite timeout or sleep state to propagate into retry execution.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established AMC and direct URL request helpers as practical infrastructure through site probing, raw AMC requests, profile lookups, QuickModule lookups, direct URL reads, and adjacent retry-control validation.
- Existing drafts covered type and ordinary range validation for AMC config/request controls, direct URL controls, and lower-level HTTP helper finite checks; they did not cover higher-level AMC and RequestUtil non-finite float handling together.
- This slice only validates finite numeric controls for `AjaxModuleConnectorConfig`, `AjaxModuleConnectorClient.request(...)`, and `RequestUtil.request(...)`. It does not change retry policy, status classification, response parsing, headers, auth behavior, Ajax behavior, site behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or user names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
