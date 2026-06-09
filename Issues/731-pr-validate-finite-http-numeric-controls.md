# PR Draft: Validate Finite HTTP Numeric Controls

## Summary

`calculate_backoff(...)`, `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, and `async_get_with_retry(...)` already validate shared HTTP retry and timeout controls for wrong types, booleans, strings, negative values, zero timeouts, and non-positive attempt counts. One numeric edge remained: Python `float("nan")`, `float("inf")`, and `-float("inf")` are still `float` values. `nan` bypasses normal comparison checks, and positive infinity is greater than zero, so the shared validators could accept non-finite retry intervals, backoff factors, maximum backoff values, and request timeouts.

This change converts numeric controls once, requires `math.isfinite(...)`, and then applies the existing range checks. Existing diagnostics are preserved: retry/backoff controls still raise `ValueError("<field> must be a non-negative number")`, and timeouts still raise `ValueError("timeout must be a positive number")`. Valid finite positive timeouts, valid finite retry controls, zero retry intervals/backoff caps/factors, retry behavior, status handling, and adjacent callers remain unchanged.

## Outcome

Shared HTTP helpers no longer accept `NaN` or infinite numeric controls that can produce `nan` backoff values, unbounded or invalid sleep behavior, or non-finite request timeout configuration. Callers now get deterministic wikidot.py-side validation at the same public helper boundary as the existing retry and timeout checks.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free site probing, login, QuickModule lookup, raw AMC setup, direct URL reads, migration tools, generated audits, archival workflows, or moderation tools that may load numeric controls from Python objects, generated structures, JSON/YAML adapters, CLI parsing, spreadsheets, or test fixtures.

## Current Evidence

Local rollout-backed drafts repeatedly identify the shared HTTP helpers as practical infrastructure. [391-pr-validate-http-retry-numeric-controls.md](391-pr-validate-http-retry-numeric-controls.md) validates retry counts, retry intervals, maximum backoff, and backoff factors for type and basic range. [395-pr-validate-http-request-timeouts.md](395-pr-validate-http-request-timeouts.md) validates shared helper request timeouts for type and positive range. [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md) and [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md) validate higher-level raw AMC and direct URL numeric config boundaries. [636-pr-validate-page-rating-percent-range.md](636-pr-validate-page-rating-percent-range.md) separately shows that finite numeric validation is already appropriate for semantically bounded generated state.

Those prior slices are not duplicates. Issue 391 covered `None`, booleans, strings, negative retry/backoff values, and invalid retry counts, but did not cover non-finite floats. Issue 395 covered malformed timeouts such as `None`, booleans, strings, zero, and negative values, but did not cover `NaN` or infinity. Issues 392 and 393 cover higher-level config entry points, not the shared `wikidot.util.http` helper validators. Issue 636 covers page rating percentages, not HTTP request controls.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [391-pr-validate-http-retry-numeric-controls.md](391-pr-validate-http-retry-numeric-controls.md), [395-pr-validate-http-request-timeouts.md](395-pr-validate-http-request-timeouts.md), [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md), and [636-pr-validate-page-rating-percent-range.md](636-pr-validate-page-rating-percent-range.md).

## Changes

- Require finite values in `_validate_non_negative_number_option(...)` after float conversion and before returning a retry/backoff control.
- Require finite values in `_validate_positive_number_option(...)` after float conversion and before returning a timeout control.
- Add non-finite cases to `calculate_backoff(...)` numeric backoff validation coverage.
- Add non-finite timeout validation coverage for sync GET, sync POST, and async GET helpers.
- Add non-finite retry numeric validation coverage for sync GET, sync POST, and async GET helpers.
- Preserve existing messages, valid zero non-negative retry controls, valid finite positive timeouts, status handling, retry behavior, caller headers/data forwarding, and adjacent Auth/Ajax/AMC/QuickModule/Site/RequestUtil workflows.

## Type Of Change

- Input validation
- Public helper behavior hardening
- Shared HTTP retry/timeout preflight safety
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `calculate_backoff(...)` must reject `NaN`, positive infinity, and negative infinity for `base_interval`, `backoff_factor`, and `max_backoff` with `ValueError("<field> must be a non-negative number")`. |
| R2 | `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, and `async_get_with_retry(...)` must reject `NaN`, positive infinity, and negative infinity for `retry_interval`, `backoff_factor`, and `max_backoff` before issuing an HTTP request. |
| R3 | `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, and `async_get_with_retry(...)` must reject `NaN`, positive infinity, and negative infinity for `timeout` before issuing an HTTP request or opening an async client. |
| R4 | Existing validation messages and malformed-value categories from Issues 391 and 395 must remain unchanged. |
| R5 | Valid finite retry behavior must remain unchanged, including zero retry intervals/backoff caps/factors, positive finite timeouts, 4xx no-retry behavior, 5xx retries, timeout/network retries, and `raise_for_status=False` behavior. |
| R6 | Adjacent Auth, Ajax, AMC, QuickModule, Site, and RequestUtil callers must remain green with valid finite configuration. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, affected HTTP tests, adjacent tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-finite backoff inputs fail before jitter/backoff calculation. | `TestCalculateBackoff.test_rejects_invalid_numeric_backoff_options` failed RED for six new `NaN`/`inf` cases with `DID NOT RAISE`, then passed GREEN after the shared validator required `math.isfinite(...)`. | Returning `nan`, returning infinity, computing jitter from non-finite values, or raising an unrelated arithmetic/sleep error rejects this local completion claim. | Backoff helper | `src/wikidot/util/http.py`, `tests/unit/test_http.py` |
| R2 | Non-finite retry-loop numeric controls fail before request setup. | Focused GREEN covered sync GET, sync POST, and async GET retry numeric validation and asserts no requests are issued. | Issuing a GET/POST, opening an async client with malformed retry controls, sleeping on `nan`/infinite backoff, or raising an unrelated later error rejects this local completion claim. | HTTP retry preflight | `src/wikidot/util/http.py`, `tests/unit/test_http.py` |
| R3 | Non-finite timeouts fail before request setup. | Focused GREEN covered sync GET, sync POST, and async GET timeout validation and asserts no requests are issued. | Passing `NaN` or infinity to `httpx`, issuing a request, opening an async client, or changing timeout diagnostics rejects this local completion claim. | HTTP timeout preflight | `src/wikidot/util/http.py`, `tests/unit/test_http.py` |
| R4 | Existing malformed-value diagnostics remain stable. | The expanded parameter tables include the previous invalid values and still match the same messages. | Changing `None`, booleans, strings, negative retry controls, zero timeout, or negative timeout diagnostics rejects this local completion claim. | Shared validator compatibility | `tests/unit/test_http.py` |
| R5 | Valid HTTP retry behavior remains stable. | `tests/unit/test_http.py` passed 175 tests after the finite checks. | Regressing valid zero retry controls, positive finite timeouts, status classification, timeout/network retries, `raise_for_status=False`, headers, or POST data rejects this local completion claim. | HTTP helper behavior | `tests/unit/test_http.py` |
| R6 | Adjacent callers remain green. | Adjacent Auth/Ajax/AMC/QuickModule/Site/RequestUtil tests passed 887 tests. | Regressing login response handling, Ajax site/SSL probing, raw AMC requests, QuickModule lookups, site probing, or direct URL reads rejects this local completion claim. | Shared caller workflows | affected unit suites |
| R7 | No live site state or private material is needed. | All regressions use unit-level synthetic values, mocks, and `pytest-httpx` request assertions. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, full HTTP, adjacent, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `422be1a fix(http): validate finite numeric controls`.

- RED: `uv run --extra test pytest tests/unit/test_http.py::TestCalculateBackoff::test_rejects_invalid_numeric_backoff_options -q` failed before the helper fix with 6 new `NaN`/`inf` cases reporting `DID NOT RAISE`; the existing invalid values still passed.
- GREEN focused: `uv run --extra test pytest tests/unit/test_http.py::TestCalculateBackoff::test_rejects_invalid_numeric_backoff_options tests/unit/test_http.py::TestSyncGetWithRetry::test_rejects_invalid_timeout_before_request tests/unit/test_http.py::TestSyncGetWithRetry::test_rejects_invalid_numeric_retry_options_before_request tests/unit/test_http.py::TestSyncPostWithRetry::test_rejects_invalid_timeout_before_request tests/unit/test_http.py::TestSyncPostWithRetry::test_rejects_invalid_numeric_retry_options_before_request tests/unit/test_http.py::TestAsyncGetWithRetry::test_rejects_invalid_timeout_before_request tests/unit/test_http.py::TestAsyncGetWithRetry::test_rejects_invalid_numeric_retry_options_before_request -q` passed 108 tests.
- `uv run --extra test pytest tests/unit/test_http.py -q` passed 175 tests.
- `uv run --extra test pytest tests/unit/test_auth.py tests/unit/test_ajax.py tests/unit/test_amc_client.py tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_requestutil.py -q` passed 887 tests.
- `uv run ruff check src/wikidot/util/http.py tests/unit/test_http.py` passed.
- `uv run ruff format --check src/wikidot/util/http.py tests/unit/test_http.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/util/http.py tests/unit/test_http.py` passed with no issues in 2 source files.
- `uv run --extra test pytest tests/unit -q` passed 3648 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `calculate_backoff(1, base_interval=float("nan"), ...)`, `base_interval=float("inf")`, and `base_interval=-float("inf")` raise `ValueError("base_interval must be a non-negative number")`.
- `calculate_backoff(1, ..., backoff_factor=float("nan"))`, `float("inf")`, and `-float("inf")` raise `ValueError("backoff_factor must be a non-negative number")`.
- `calculate_backoff(1, ..., max_backoff=float("nan"))`, `float("inf")`, and `-float("inf")` raise `ValueError("max_backoff must be a non-negative number")`.
- `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, and `async_get_with_retry(...)` reject non-finite `retry_interval`, `max_backoff`, and `backoff_factor` controls before HTTP requests are issued.
- `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, and `async_get_with_retry(...)` reject non-finite `timeout` values before HTTP requests are issued.
- Existing malformed-value messages from Issues 391 and 395 remain stable.
- Valid finite HTTP retry and timeout behavior remains green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A caller intentionally used `float("inf")` as a request timeout or retry control. Mitigation: these helpers describe finite request timeout and sleep/backoff controls; unbounded wait semantics should be explicit at a higher level, not represented by non-finite numeric values inside retry code.
- Risk: Rejecting `NaN` exposes configuration parsing bugs from generated data or test fixtures. Mitigation: `NaN` cannot produce meaningful timeout or backoff behavior; callers should normalize configuration before calling shared HTTP helpers.
- Risk: The slice could be confused with Issue 391 or Issue 395. Mitigation: those drafts covered type and ordinary range validation; this follow-up covers IEEE non-finite floats that passed the existing validators.
- Risk: Finite checks could accidentally change valid zero retry controls. Mitigation: `_validate_non_negative_number_option(...)` still accepts finite zero values, and full HTTP retry tests remain green.

## Dependencies

- Existing `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, `async_get_with_retry(...)`, and `calculate_backoff(...)` remain the source of truth for shared low-level HTTP retry behavior.
- Existing Auth, Ajax, AMC, QuickModule, Site, and RequestUtil callers continue to use their current wrappers and config sources.
- The validation is local to `src/wikidot/util/http.py` and does not affect URL construction, headers, form data, response parsing, higher-level exception conversion, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-shape validation, result ergonomics, action/read boundaries, or measured complexity candidates outside this now-covered shared HTTP numeric-control finite validation.

## Upstream-Safe Motivation

The shared HTTP helpers sit below multiple browser-free workflows. Since retry intervals, backoff factors, maximum backoff, and request timeouts control wait behavior, wikidot.py should reject `NaN` and infinite values at the helper boundary instead of allowing non-finite sleep or timeout state to propagate into retry execution.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established shared HTTP helpers as practical infrastructure through QuickModule lookup retrying, site probing, raw AMC initialization, Auth login, RequestUtil direct URL reads, and adjacent retry-control validation.
- Existing drafts covered type and ordinary range validation for retry controls and timeouts; they did not cover non-finite Python float values.
- This slice only validates finite numeric controls for `calculate_backoff(...)`, `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, and `async_get_with_retry(...)`. It does not change retry policy, status classification, response parsing, headers, auth behavior, Ajax behavior, RequestUtil behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or user names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

