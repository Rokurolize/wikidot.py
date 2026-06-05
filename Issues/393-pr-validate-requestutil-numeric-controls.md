# PR Draft: Validate RequestUtil Numeric Request Controls

## Summary

`RequestUtil.request(client, method, urls, ...)` is the direct URL GET/POST batch helper used by profile lookups, direct page probes, and other retry-aware read paths, but malformed numeric settings from `client.amc_client.config` were not rejected at this boundary. Values such as `request_timeout=None`, `request_timeout="1"`, `attempt_limit=0`, `attempt_limit=True`, `retry_interval="1"`, `max_backoff=-0.1`, `backoff_factor=True`, or `semaphore_limit=0` could reach async client setup, request execution, retry loops, backoff calculation, or zero-semaphore blocking instead of producing a stable wikidot.py-side diagnostic before any HTTP work.

This change validates the non-empty `RequestUtil.request(...)` config values after method, `return_exceptions`, and empty-URL handling, but before semaphore setup, header preparation, `httpx.AsyncClient` creation, or GET/POST execution. Invalid request timeouts now raise `ValueError("request_timeout must be a positive number")`. Invalid attempt and semaphore limits now raise `ValueError("<field> must be a positive integer")`. Invalid retry/backoff controls now raise `ValueError("<field> must be a non-negative number")`. Existing invalid-method precedence, Issue 388 return-exceptions validation, empty URL no-op behavior, valid no-wait retry intervals, valid zero backoff controls, header forwarding, retry behavior, return-exceptions behavior, and adjacent HTTP/Ajax/Site behavior remain unchanged.

## Outcome

Direct URL batch callers now get deterministic Python-side preflight validation for malformed numeric request controls instead of accidental GET/POST execution, unrelated `httpx` failures, hidden retry-loop shape changes, or zero-semaphore stalls.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using direct GET/POST URL batches through profile lookup, direct page-ID probing, generated audits, migration tools, moderation tools, archival workflows, or browser-free automation that may load request controls from JSON, YAML, CLI flags, spreadsheets, generated structures, environment variables, or mocked test clients.

## Current Evidence

Local rollout-backed drafts repeatedly identify direct URL request behavior as practical infrastructure. [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md) made empty direct URL batches no-op before config access. [138-pr-reuse-requestutil-async-client.md](138-pr-reuse-requestutil-async-client.md) preserved direct URL retry behavior while reducing client churn. [388-pr-validate-requestutil-return-exceptions-flag.md](388-pr-validate-requestutil-return-exceptions-flag.md) validates `RequestUtil.request(..., return_exceptions=...)` before empty URL handling or config access. [391-pr-validate-http-retry-numeric-controls.md](391-pr-validate-http-retry-numeric-controls.md) validates shared `wikidot.util.http` helper numeric controls. [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md) validates raw AMC request numeric controls.

Those prior slices are not duplicates. Issue 388 validates the direct URL exception-handling flag, not numeric timeout/retry/concurrency controls. Issue 391 validates the public low-level HTTP retry helper arguments, not the `client.amc_client.config` values read by `RequestUtil.request(...)`. Issue 392 validates `AjaxModuleConnectorClient.request(...)`, not direct URL GET/POST batches. This slice applies to non-empty `RequestUtil.request(...)` calls and preserves the empty-URL no-config contract from Issue 137.

No upstream issue was filed from this local workspace.

## Related Issue

Builds directly on [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md), [138-pr-reuse-requestutil-async-client.md](138-pr-reuse-requestutil-async-client.md), [388-pr-validate-requestutil-return-exceptions-flag.md](388-pr-validate-requestutil-return-exceptions-flag.md), [391-pr-validate-http-retry-numeric-controls.md](391-pr-validate-http-retry-numeric-controls.md), and [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md).

## Changes

- Validate `request_timeout` as a non-bool positive number before direct URL request execution.
- Validate `attempt_limit` and `semaphore_limit` as non-bool positive integers before retry loops or semaphore setup.
- Validate `retry_interval`, `max_backoff`, and `backoff_factor` as non-bool non-negative numbers before request execution.
- Use validated local config values inside GET/POST retry loops instead of repeatedly reading mutable config fields mid-request.
- Preserve method validation before all other checks.
- Preserve Issue 388 `return_exceptions` validation before the empty-URL shortcut.
- Preserve empty URL no-op behavior without requiring `client.amc_client.config`.
- Preserve valid zero retry intervals and zero backoff controls as explicit no-wait/no-growth controls.
- Preserve header forwarding, non-Wikidot header suppression, retryable 5xx behavior, non-retryable 4xx behavior, timeout/network retry behavior, and `return_exceptions=True` behavior.

## Type Of Change

- Input validation
- Public helper behavior hardening
- Direct URL request preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `RequestUtil.request(...)` must reject malformed `request_timeout` values with `ValueError("request_timeout must be a positive number")` before GET/POST requests are issued. |
| R2 | `RequestUtil.request(...)` must reject malformed `attempt_limit` and `semaphore_limit` values with `ValueError("<field> must be a positive integer")` before retry loops, semaphore setup, or HTTP requests can start. |
| R3 | `RequestUtil.request(...)` must reject malformed `retry_interval`, `max_backoff`, and `backoff_factor` values with `ValueError("<field> must be a non-negative number")` before GET/POST requests are issued. |
| R4 | Existing method, `return_exceptions`, and empty URL precedence must remain unchanged. |
| R5 | Valid direct URL GET/POST behavior must remain unchanged, including successful requests, Wikidot header forwarding, non-Wikidot header suppression, retryable 5xx handling, non-retryable 4xx handling, timeout retry, and `return_exceptions=True`. |
| R6 | Adjacent HTTP, Ajax, raw AMC, and Site wrapper behavior must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, affected RequestUtil tests, adjacent tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed request timeouts fail before direct URL request execution. | `test_rejects_invalid_request_timeout_before_request` passed GREEN for GET and POST and asserts `httpx_mock.get_requests() == []`. | Issuing GET/POST requests, accepting booleans or strings, treating `0` as a valid timeout, or raising an unrelated `httpx` error rejects this local completion claim. | Direct URL preflight | `src/wikidot/util/requestutil.py`, `tests/unit/test_requestutil.py` |
| R2 | Malformed attempt and semaphore limits fail before retry/semaphore/request setup. | `test_rejects_invalid_positive_integer_config_before_request` passed GREEN for GET and POST and asserts no requests are issued. | Treating `True` as one attempt, treating `0` as an empty retry loop, creating `asyncio.Semaphore(0)` for a non-empty URL batch, issuing a request, or raising an unrelated later error rejects this local completion claim. | Direct URL preflight | `src/wikidot/util/requestutil.py`, `tests/unit/test_requestutil.py` |
| R3 | Malformed retry/backoff controls fail before request setup. | `test_rejects_invalid_retry_number_config_before_request` passed GREEN for GET and POST and asserts no requests are issued. | Coercing strings, accepting booleans, accepting negative sleeps, issuing a request before validation, or relying on later `calculate_backoff(...)` failure rejects this local completion claim. | Direct URL preflight | `src/wikidot/util/requestutil.py`, `tests/unit/test_requestutil.py` |
| R4 | Method, exception-control, and empty URL precedence remains stable. | Existing empty URL and invalid-method tests in `tests/unit/test_requestutil.py` passed after validation was added. | Reading client config for empty URLs, accepting malformed `return_exceptions`, changing invalid-method error precedence, or requiring a configured client for `[]` rejects this local completion claim. | Direct URL public boundary | `tests/unit/test_requestutil.py` |
| R5 | Valid GET/POST behavior remains stable. | `tests/unit/test_requestutil.py` passed 87 tests after validation was added. | Regressing success, header forwarding/suppression, retryable 5xx, non-retryable 4xx, timeout retry, return-exceptions behavior, or one-client-per-batch behavior rejects this local completion claim. | Direct URL behavior | `tests/unit/test_requestutil.py` |
| R6 | Adjacent request wrappers remain green. | `tests/unit/test_http.py tests/unit/test_ajax.py tests/unit/test_amc_client.py tests/unit/test_site.py` passed 339 tests after validation was added. | Regressing shared HTTP retry validation, raw AMC request validation, Ajax helpers, or Site wrappers rejects this local completion claim. | Adjacent workflows | affected HTTP/Ajax/AMC/Site tests |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic values, mocks, and `pytest-httpx` request assertions. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, affected tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `c99c6cb fix(requestutil): validate numeric request controls`.

- RED: `timeout 8s .venv/bin/python -m pytest -q tests/unit/test_requestutil.py::TestRequestUtilConfigValidation::test_rejects_invalid_request_timeout_before_request` failed 2 tests and 2 teardown checks before the fix because malformed timeout config still issued five unmatched GETs or POSTs per method.
- GREEN tracer: `.venv/bin/python -m pytest -q tests/unit/test_requestutil.py::TestRequestUtilConfigValidation::test_rejects_invalid_request_timeout_before_request` passed 2 tests after adding preflight.
- Focused GREEN: `timeout 15s .venv/bin/python -m pytest -q tests/unit/test_requestutil.py::TestRequestUtilConfigValidation` passed 60 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_requestutil.py` passed 87 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_http.py tests/unit/test_ajax.py tests/unit/test_amc_client.py tests/unit/test_site.py` passed 339 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1334 tests.
- `.venv/bin/python -m ruff check src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed.
- `.venv/bin/python -m ruff format --check src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed with 2 files already formatted.
- `.venv/bin/python -m mypy src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed with no issues in 2 source files.
- `.venv/bin/python -m ruff check .` passed.
- `.venv/bin/python -m ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/python -m mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `RequestUtil.request(client, "GET", ["https://example.com/test"])` and POST equivalents reject `request_timeout=None`, `request_timeout=True`, `request_timeout="1"`, `request_timeout=0`, and `request_timeout=-0.1` with `ValueError("request_timeout must be a positive number")` before issuing HTTP requests.
- `attempt_limit=None`, `attempt_limit=True`, `attempt_limit="1"`, `attempt_limit=0`, `attempt_limit=-1`, and `attempt_limit=1.5` raise `ValueError("attempt_limit must be a positive integer")` before issuing HTTP requests.
- `semaphore_limit=None`, `semaphore_limit=True`, `semaphore_limit="1"`, `semaphore_limit=0`, `semaphore_limit=-1`, and `semaphore_limit=1.5` raise `ValueError("semaphore_limit must be a positive integer")` before semaphore setup can block a non-empty URL batch.
- `retry_interval`, `max_backoff`, and `backoff_factor` reject `None`, booleans, strings, and negative numbers with `ValueError("<field> must be a non-negative number")` before issuing HTTP requests.
- Valid `retry_interval=0`, `max_backoff=0`, and `backoff_factor=0` remain accepted.
- `RequestUtil.request(object(), "GET", [])` and `RequestUtil.request(object(), "POST", [])` still return `[]` without requiring client config.
- Invalid method validation and malformed `return_exceptions` validation remain unchanged.
- Valid GET/POST success, Wikidot header forwarding, non-Wikidot header suppression, retryable 5xx handling, non-retryable 4xx handling, timeout retry, and `return_exceptions=True` behavior remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting booleans as numeric controls tightens behavior for callers that accidentally relied on Python's `bool` subclassing `int`. Mitigation: these fields are numeric retry, timeout, and concurrency controls; accepting booleans hides configuration parsing mistakes.
- Risk: Rejecting strings can expose CLI, environment, JSON, YAML, spreadsheet, or generated-structure parsing bugs. Mitigation: text configuration should parse numeric controls into real integers or floats before constructing direct URL request batches.
- Risk: Rejecting `semaphore_limit=0` changes an accidental zero-capacity concurrency setting into an explicit error. Mitigation: a zero-capacity semaphore cannot make progress for non-empty GET/POST batches.
- Risk: The change could be confused with Issue 388. Mitigation: Issue 388 covered the boolean exception-returning control; this slice covers numeric timeout/retry/backoff/concurrency controls.
- Risk: The change could be confused with Issue 391 or Issue 392. Mitigation: Issue 391 covered shared `wikidot.util.http` helpers, and Issue 392 covered raw AMC request execution; this slice applies to direct URL `RequestUtil.request(...)`.

## Dependencies

- Existing `RequestUtil.request(...)` remains the source of truth for direct GET/POST URL batch execution.
- Existing site, page, user, and other direct URL workflows continue to use their current wrappers and retry helpers.
- Existing `wikidot.util.http`, `AjaxModuleConnectorClient.request(...)`, and Site AMC validation remains separate and unchanged.
- The validation is local to `src/wikidot/util/requestutil.py` and does not affect URL construction, request method selection, response parsing, higher-level wrapper behavior, raw AMC behavior, shared HTTP helper behavior, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, site-level AMC retry-default validation, or complexity candidates outside this now-covered RequestUtil numeric-control path.

## Upstream-Safe Motivation

`RequestUtil.request(...)` is the lower-level direct URL batch executor beneath multiple Wikidot workflows. Since timeout, retry count, backoff, and concurrency controls determine whether request work starts, repeats, sleeps, or blocks, malformed strings, booleans, non-positive counts, negative backoff values, and zero concurrency should fail deterministically before request setup.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established `RequestUtil.request(...)` as practical infrastructure through profile lookup, direct page probing, empty URL batching, and retry-aware direct URL reads.
- Existing RequestUtil drafts covered empty URL no-ops, AsyncClient reuse, and the exception-returning flag; they did not validate caller-provided numeric request controls.
- This slice only validates direct URL request timeout, attempt, retry/backoff, and semaphore inputs. It does not change URL selection, request method validation, header forwarding policy, retry policy, response parsing, raw AMC request behavior, site wrapper behavior, shared HTTP helper behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or user names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed numeric controls instead of coercing them. Callers that load these controls from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should resolve them into real integers or floats before calling `RequestUtil.request(...)`.
