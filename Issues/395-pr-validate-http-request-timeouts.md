# PR Draft: Validate HTTP Request Timeouts

## Summary

`sync_get_with_retry(...)`, `sync_post_with_retry(...)`, and `async_get_with_retry(...)` are the shared low-level HTTP helpers used by site probing, login, QuickModule, raw AMC initialization, and other browser-free Wikidot workflows. Their retry counts, retry intervals, backoff factors, and boolean controls were already validated, but malformed `timeout` values were still passed directly to `httpx`. Values such as `timeout=None`, `timeout=True`, `timeout="1"`, `timeout=0`, or `timeout=-0.1` could disable timeout behavior, be coerced through Python's bool/int relationship, issue HTTP requests before wikidot.py-side validation, or leave diagnostics to `httpx` behavior instead of the shared helper boundary.

This change validates `timeout` as a non-bool positive number before any HTTP request is issued in sync GET, sync POST, and async GET helpers. Existing boolean-control precedence, retry numeric validation, retryable 5xx handling, non-retryable 4xx behavior, timeout/network retry behavior, caller headers/data forwarding, QuickModule lookups, Auth login, Site probing, raw AMC initialization, and direct URL RequestUtil callers remain unchanged.

## Outcome

Shared HTTP helper callers now get deterministic Python-side timeout validation before request execution instead of accidental no-timeout operation, bool coercion, later `httpx` errors, or request work with malformed timeout configuration.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free site probing, login, QuickModule, raw AMC setup, direct URL reads, migration tools, generated audits, archival workflows, or moderation tools that may load timeout settings from JSON, YAML, CLI flags, spreadsheets, generated structures, environment variables, or mocked test clients.

## Current Evidence

Local rollout-backed drafts repeatedly identify the shared HTTP retry helpers as practical infrastructure. [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md) made QuickModule rely on `sync_get_with_retry(...)` retrying transient 5xx responses. [390-pr-validate-http-retry-boolean-controls.md](390-pr-validate-http-retry-boolean-controls.md) validates adjacent low-level boolean controls. [391-pr-validate-http-retry-numeric-controls.md](391-pr-validate-http-retry-numeric-controls.md) validates retry counts, retry intervals, max backoff, and backoff factor. [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md) and [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md) validate higher-level raw AMC and direct URL `request_timeout` config values.

Those prior slices are not duplicates. Issue 391 covers retry-loop numeric controls, not the per-request `timeout` passed to `httpx`. Issues 392 and 393 cover `AjaxModuleConnectorClient.request(...)` and `RequestUtil.request(...)` config boundaries, not direct callers of `wikidot.util.http`. This slice applies to the public low-level HTTP helper timeout argument itself.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [390-pr-validate-http-retry-boolean-controls.md](390-pr-validate-http-retry-boolean-controls.md), [391-pr-validate-http-retry-numeric-controls.md](391-pr-validate-http-retry-numeric-controls.md), [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), and [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md).

## Changes

- Validate `timeout` in `sync_get_with_retry(...)` as a non-bool positive number before `httpx.get(...)`.
- Validate `timeout` in `sync_post_with_retry(...)` as a non-bool positive number before `httpx.post(...)`.
- Validate `timeout` in `async_get_with_retry(...)` as a non-bool positive number before `httpx.AsyncClient(...)`.
- Preserve existing validation of `follow_redirects`, `raise_for_status`, `attempt_limit`, `retry_interval`, `max_backoff`, and `backoff_factor`.
- Preserve valid retry behavior, valid status handling, caller headers/data forwarding, and adjacent Auth/Ajax/QuickModule/Site/RequestUtil behavior.

## Type Of Change

- Input validation
- Public helper behavior hardening
- Low-level HTTP request preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `sync_get_with_retry(..., timeout=...)` must reject malformed timeout values with `ValueError("timeout must be a positive number")` before issuing an HTTP request. |
| R2 | `sync_post_with_retry(..., timeout=...)` must reject malformed timeout values with `ValueError("timeout must be a positive number")` before issuing an HTTP request. |
| R3 | `async_get_with_retry(..., timeout=...)` must reject malformed timeout values with `ValueError("timeout must be a positive number")` before opening an async client or issuing an HTTP request. |
| R4 | Existing retry, boolean-control, status, timeout/network retry, header, data, and adjacent caller behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, affected HTTP tests, adjacent tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `timeout=None`, `True`, `"1"`, `0`, and `-0.1` fail before sync GET request work. | `TestSyncGetWithRetry.test_rejects_invalid_timeout_before_request` passed GREEN and asserts `httpx_mock.get_requests() == []`. | Issuing a GET request, accepting booleans or strings, disabling timeout with `None`, treating `0` as valid, or raising an unrelated `httpx` error rejects this local completion claim. | Shared HTTP GET helper | `src/wikidot/util/http.py`, `tests/unit/test_http.py` |
| R2 | `timeout=None`, `True`, `"1"`, `0`, and `-0.1` fail before sync POST request work. | `TestSyncPostWithRetry.test_rejects_invalid_timeout_before_request` passed GREEN and asserts no requests are issued. | Issuing a POST request, accepting booleans or strings, disabling timeout with `None`, treating `0` as valid, or raising an unrelated `httpx` error rejects this local completion claim. | Shared HTTP POST helper | `src/wikidot/util/http.py`, `tests/unit/test_http.py` |
| R3 | `timeout=None`, `True`, `"1"`, `0`, and `-0.1` fail before async GET request work. | `TestAsyncGetWithRetry.test_rejects_invalid_timeout_before_request` passed GREEN and asserts no requests are issued. | Opening an async client, issuing a GET request, accepting booleans or strings, disabling timeout with `None`, treating `0` as valid, or raising an unrelated `httpx` error rejects this local completion claim. | Shared async HTTP GET helper | `src/wikidot/util/http.py`, `tests/unit/test_http.py` |
| R4 | Valid retry and adjacent caller behavior remains stable. | `tests/unit/test_http.py` passed 130 tests; adjacent Auth/Ajax/AMC/QuickModule/Site/RequestUtil tests passed 372 tests; full unit passed 1373 tests. | Regressing retryable 5xx handling, 4xx handling, timeout/network retries, boolean-control validation, retry numeric validation, headers/data forwarding, QuickModule, Auth, Site, raw AMC, or RequestUtil behavior rejects this local completion claim. | Shared HTTP workflows | affected unit suites |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic values, mocks, and `pytest-httpx` request assertions. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, affected tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `a418f19 fix(http): validate request timeouts`.

- RED tracer: `timeout 8s .venv/bin/python -m pytest -q tests/unit/test_http.py::TestSyncGetWithRetry::test_rejects_invalid_timeout_before_request` failed 5 tests before the fix when the tracer registered a mock response, proving malformed sync GET timeouts reached HTTP request execution instead of raising `ValueError`.
- GREEN tracer: `.venv/bin/python -m pytest -q tests/unit/test_http.py::TestSyncGetWithRetry::test_rejects_invalid_timeout_before_request` passed 5 tests after adding preflight.
- Focused GREEN: `timeout 12s .venv/bin/python -m pytest -q tests/unit/test_http.py::TestSyncGetWithRetry::test_rejects_invalid_timeout_before_request tests/unit/test_http.py::TestSyncPostWithRetry::test_rejects_invalid_timeout_before_request tests/unit/test_http.py::TestAsyncGetWithRetry::test_rejects_invalid_timeout_before_request` passed 15 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_http.py` passed 130 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_auth.py tests/unit/test_ajax.py tests/unit/test_amc_client.py tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_requestutil.py` passed 372 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1373 tests.
- `.venv/bin/python -m ruff check src/wikidot/util/http.py tests/unit/test_http.py` passed.
- `.venv/bin/python -m ruff format --check src/wikidot/util/http.py tests/unit/test_http.py` passed with 2 files already formatted.
- `.venv/bin/python -m mypy src/wikidot/util/http.py tests/unit/test_http.py` passed with no issues in 2 source files.
- `.venv/bin/python -m ruff check .` passed.
- `.venv/bin/python -m ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/python -m mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `sync_get_with_retry("https://example.com/test", timeout=None)`, `timeout=True`, `timeout="1"`, `timeout=0`, and `timeout=-0.1` raise `ValueError("timeout must be a positive number")` before HTTP requests are issued.
- `sync_post_with_retry("https://example.com/test", timeout=None)`, `timeout=True`, `timeout="1"`, `timeout=0`, and `timeout=-0.1` raise `ValueError("timeout must be a positive number")` before HTTP requests are issued.
- `async_get_with_retry("https://example.com/test", timeout=None)`, `timeout=True`, `timeout="1"`, `timeout=0`, and `timeout=-0.1` raise `ValueError("timeout must be a positive number")` before opening an async client or issuing HTTP requests.
- Valid positive integer and float timeout values remain accepted.
- Existing follow-redirect, raise-for-status, retry numeric, 4xx/5xx, timeout/network retry, header forwarding, POST data, QuickModule, Auth, Site, raw AMC, and RequestUtil behavior remains green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `timeout=None` changes behavior for callers that intentionally disabled timeouts. Mitigation: the public helper annotation is numeric, higher-level wikidot.py config names this as a request timeout, and browser-free automation should not silently disable timeouts through malformed config.
- Risk: Rejecting booleans tightens behavior for callers that accidentally relied on Python's `bool` subclassing `int`. Mitigation: `True` and `False` are configuration mistakes for a request timeout and should not become one second or zero seconds.
- Risk: Rejecting strings can expose CLI, environment, JSON, YAML, spreadsheet, or generated-structure parsing bugs. Mitigation: textual configuration should parse timeout controls into real positive integers or floats before calling shared HTTP helpers.
- Risk: This change could be confused with Issue 391. Mitigation: Issue 391 covered retry-loop numeric controls; this slice covers the per-request `timeout` argument.
- Risk: This change could be confused with Issues 392 or 393. Mitigation: those slices covered raw AMC and direct URL RequestUtil config timeouts; this slice applies to direct uses of `wikidot.util.http`.

## Dependencies

- Existing `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, `async_get_with_retry(...)`, and `calculate_backoff(...)` remain the source of truth for shared low-level HTTP retry behavior.
- Existing Auth, Ajax, QuickModule, Site, RequestUtil, and raw AMC callers continue to use their current wrappers and config sources.
- The validation is local to `src/wikidot/util/http.py` and does not affect URL construction, response parsing, raw AMC request execution, direct URL RequestUtil execution, site-level AMC retry behavior, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-body field-type checks, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered shared HTTP timeout path.

## Upstream-Safe Motivation

The shared HTTP helpers sit below multiple Wikidot workflows. Since timeout settings determine whether request work can wait indefinitely, malformed `None`, strings, booleans, zero, and negative values should fail deterministically before `httpx` request setup.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established shared HTTP helpers as practical infrastructure through QuickModule lookup retrying, site probing, raw AMC initialization, Auth login, RequestUtil direct URL reads, and adjacent retry-control validation.
- Existing shared HTTP drafts covered boolean controls and retry-loop numeric controls; they did not validate the direct `timeout` argument.
- This slice only validates shared HTTP helper request timeouts. It does not change retry policy, status classification, response parsing, headers, auth behavior, Ajax behavior, RequestUtil behavior, site-level AMC retry behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or user names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed timeout controls instead of coercing them. Callers that load timeout values from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should resolve them into real positive integers or floats before calling the shared HTTP helpers.
