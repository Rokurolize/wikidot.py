# PR Draft: Validate HTTP Retry Numeric Controls

## Summary

`calculate_backoff(...)`, `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, and `async_get_with_retry(...)` documented retry counts, retry intervals, maximum backoff, and backoff factors as numeric controls, but malformed caller-provided values were not rejected at the shared HTTP retry boundary. Values such as `attempt_limit=0`, `attempt_limit="3"`, `retry_interval="1"`, `retry_interval=-0.1`, `max_backoff=-0.1`, or `backoff_factor=-0.1` could skip every request and raise the generic `RuntimeError("Unreachable")`, reach request execution before failing elsewhere, or create invalid backoff/sleep behavior instead of producing a stable wikidot.py-side diagnostic.

This change validates shared HTTP retry numeric controls before request execution and validates `calculate_backoff(...)` inputs before computing jitter. Invalid attempt counts now raise `ValueError("attempt_limit must be a positive integer")` or `ValueError("retry_count must be a positive integer")`. Invalid interval/backoff values now raise `ValueError("<field> must be a non-negative number")`. Existing valid retry behavior, valid zero retry intervals, 4xx/5xx status handling, timeout/network retries, boolean-control validation from Issue 390, caller headers/data forwarding, and adjacent Ajax/Auth/QuickModule/Site callers remain unchanged.

## Outcome

Shared HTTP retry callers now get deterministic Python-side preflight validation for malformed retry numeric controls instead of accidental no-op attempts, request execution with malformed configuration, or negative/non-numeric backoff behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `wikidot.util.http` directly or indirectly through QuickModule lookup, auth login, Ajax client SSL/site probing, site source visibility probing, direct read workflows, generated audits, migration tools, moderation tools, or browser-free automation that may load retry controls from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables.

## Current Evidence

Local rollout-backed drafts repeatedly identify retry-aware request behavior as practical infrastructure beneath browser-free Wikidot automation. [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md) made QuickModule rely on `sync_get_with_retry(...)` retrying transient 5xx responses before mapping a final 500 to `ValueError("Site is not found")`. [138-pr-reuse-requestutil-async-client.md](138-pr-reuse-requestutil-async-client.md) preserved direct URL retry behavior while improving request batching. [390-pr-validate-http-retry-boolean-controls.md](390-pr-validate-http-retry-boolean-controls.md) validated adjacent low-level HTTP boolean controls before request execution.

Those prior slices are not duplicates. They covered QuickModule retry semantics, RequestUtil batching, and HTTP retry boolean controls. They did not validate low-level retry numeric controls before `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, or `async_get_with_retry(...)` issue requests or before `calculate_backoff(...)` computes jitter. Higher-level retry-option validations such as [345-pr-validate-source-iterator-batch-sizes.md](345-pr-validate-source-iterator-batch-sizes.md), [346-pr-validate-publish-visibility-controls.md](346-pr-validate-publish-visibility-controls.md), and [139-pr-skip-empty-amc-retry-batches.md](139-pr-skip-empty-amc-retry-batches.md) validate different workflow-specific batch, visibility, or AMC retry controls, not the shared HTTP helper controls.

The current callers make this low-level surface concrete: `src/wikidot/connector/ajax.py` passes `AjaxModuleConnectorConfig` retry settings into `sync_get_with_retry(...)`; `src/wikidot/module/site.py` uses the same config for source visibility probing; `src/wikidot/util/quick_module.py` uses `sync_get_with_retry(...)` for QuickModule lookups; and `src/wikidot/module/auth.py` uses `sync_post_with_retry(...)` for login response handling.

No upstream issue was filed from this local workspace.

## Related Issue

Builds directly on [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [138-pr-reuse-requestutil-async-client.md](138-pr-reuse-requestutil-async-client.md), [345-pr-validate-source-iterator-batch-sizes.md](345-pr-validate-source-iterator-batch-sizes.md), [346-pr-validate-publish-visibility-controls.md](346-pr-validate-publish-visibility-controls.md), [390-pr-validate-http-retry-boolean-controls.md](390-pr-validate-http-retry-boolean-controls.md), and [139-pr-skip-empty-amc-retry-batches.md](139-pr-skip-empty-amc-retry-batches.md).

## Changes

- Validate `retry_count` in `calculate_backoff(...)` as a non-bool positive integer.
- Validate `base_interval`, `backoff_factor`, and `max_backoff` in `calculate_backoff(...)` as non-bool non-negative numbers.
- Validate `attempt_limit` in `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, and `async_get_with_retry(...)` as a non-bool positive integer before request execution.
- Validate `retry_interval`, `max_backoff`, and `backoff_factor` in the shared HTTP retry helpers as non-bool non-negative numbers before request execution.
- Preserve valid zero retry intervals and zero max/backoff factors as explicit no-wait/no-growth controls.
- Preserve Issue 390 boolean-control validation, status handling, timeout/network retry behavior, caller headers/data forwarding, and adjacent Ajax/Auth/QuickModule/Site behavior.
- Update auth tests to provide a real `AjaxModuleConnectorConfig` on mocked clients instead of accidentally relying on `MagicMock` retry config fields.

## Type Of Change

- Input validation
- Public helper behavior hardening
- Shared HTTP retry preflight safety
- Test fixture correctness
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `calculate_backoff(retry_count=...)` must reject `None`, booleans, strings, non-positive integers, and floats with `ValueError("retry_count must be a positive integer")` before computing backoff. |
| R2 | `calculate_backoff(base_interval=..., backoff_factor=..., max_backoff=...)` must reject `None`, booleans, strings, and negative numeric values with `ValueError("<field> must be a non-negative number")` before computing backoff. |
| R3 | `sync_get_with_retry(..., attempt_limit=...)`, `sync_post_with_retry(..., attempt_limit=...)`, and `async_get_with_retry(..., attempt_limit=...)` must reject malformed attempt limits before issuing an HTTP request. |
| R4 | `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, and `async_get_with_retry(...)` must reject malformed `retry_interval`, `max_backoff`, and `backoff_factor` values before issuing an HTTP request. |
| R5 | Valid retry behavior must remain unchanged for sync GET, sync POST, and async GET, including valid zero retry intervals, 4xx no-retry behavior, 5xx retry behavior, timeout/network retries, and valid `raise_for_status=False` 4xx-return/5xx-retry semantics. |
| R6 | Adjacent Ajax, auth, QuickModule, and site callers that pass valid retry controls must remain green. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED evidence must be recorded, focused GREEN must pass, and affected HTTP tests, auth tests, adjacent tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed backoff retry counts fail before jitter computation. | `TestCalculateBackoff.test_rejects_invalid_retry_count` passed GREEN after validation was added; the pre-fix RED selection showed these invalid inputs were not preflighted. | Returning a computed backoff for `retry_count=0`, accepting `True`, accepting strings, or raising an unrelated arithmetic error rejects this local completion claim. | Backoff helper | `src/wikidot/util/http.py`, `tests/unit/test_http.py` |
| R2 | Malformed backoff interval/factor/cap values fail before jitter computation. | `TestCalculateBackoff.test_rejects_invalid_numeric_backoff_options` passed GREEN after validation was added; the pre-fix RED selection showed invalid values were not consistently preflighted. | Accepting negative intervals, accepting strings, accepting booleans, producing negative sleeps, or raising an unrelated arithmetic error rejects this local completion claim. | Backoff helper | `src/wikidot/util/http.py`, `tests/unit/test_http.py` |
| R3 | Malformed attempt limits fail before request setup for all public HTTP retry helpers. | `test_rejects_invalid_attempt_limit_before_request` passed GREEN for sync GET, sync POST, and async GET, and asserts `httpx_mock.get_requests() == []`. | Treating `True` as one attempt, treating `0` as an empty retry loop, issuing a GET/POST, opening an async client, or raising `RuntimeError("Unreachable")` rejects this local completion claim. | HTTP retry preflight | `src/wikidot/util/http.py`, `tests/unit/test_http.py` |
| R4 | Malformed interval/backoff controls fail before request setup for all public HTTP retry helpers. | `test_rejects_invalid_numeric_retry_options_before_request` passed GREEN for sync GET, sync POST, and async GET, and asserts `httpx_mock.get_requests() == []`. | Issuing a request, coercing strings, accepting booleans, creating negative sleep values, or raising an unrelated later error rejects this local completion claim. | HTTP retry preflight | `src/wikidot/util/http.py`, `tests/unit/test_http.py` |
| R5 | Valid retry behavior remains stable. | Existing success, 4xx, 5xx, timeout, network, and `raise_for_status=False` tests in `tests/unit/test_http.py` passed after validation was added. | Regressing valid no-wait intervals, retry counts, status classification, timeout/network retry, or valid `False` status behavior rejects this local completion claim. | HTTP retry behavior | `tests/unit/test_http.py` |
| R6 | Adjacent callers remain green with real numeric retry config. | `tests/unit/test_auth.py` passed 7 tests; `tests/unit/test_http.py tests/unit/test_ajax.py tests/unit/test_auth.py tests/unit/test_quick_module.py tests/unit/test_site.py` passed 291 tests; full unit passed 1226 tests. | Regressing auth login response handling, QuickModule lookup mapping, Ajax site/SSL probing, site source visibility probing, or test clients with realistic config rejects this local completion claim. | Shared caller workflows | affected HTTP/Ajax/Auth/QuickModule/Site tests |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic values, mocks, and `pytest-httpx` request assertions. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, affected tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `e35b75d fix(http): validate retry numeric controls`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_http.py::TestCalculateBackoff::test_rejects_invalid_retry_count tests/unit/test_http.py::TestCalculateBackoff::test_rejects_invalid_numeric_backoff_options tests/unit/test_http.py::TestSyncGetWithRetry::test_rejects_invalid_attempt_limit_before_request tests/unit/test_http.py::TestSyncGetWithRetry::test_rejects_invalid_numeric_retry_options_before_request tests/unit/test_http.py::TestSyncPostWithRetry::test_rejects_invalid_attempt_limit_before_request tests/unit/test_http.py::TestSyncPostWithRetry::test_rejects_invalid_numeric_retry_options_before_request tests/unit/test_http.py::TestAsyncGetWithRetry::test_rejects_invalid_attempt_limit_before_request tests/unit/test_http.py::TestAsyncGetWithRetry::test_rejects_invalid_numeric_retry_options_before_request` failed before the fix; it was stopped after reaching the malformed request/retry paths because invalid controls were not preflighted.
- GREEN: the same focused selection passed 72 tests after adding numeric preflight.
- `.venv/bin/python -m pytest -q tests/unit/test_http.py` passed 115 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_auth.py` passed 7 tests after mocked clients were given real retry config values.
- `.venv/bin/python -m pytest -q tests/unit/test_http.py tests/unit/test_ajax.py tests/unit/test_auth.py tests/unit/test_quick_module.py tests/unit/test_site.py` passed 291 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1226 tests.
- `.venv/bin/ruff check src/wikidot/util/http.py tests/unit/test_http.py tests/unit/test_auth.py` passed.
- `.venv/bin/ruff format --check src/wikidot/util/http.py tests/unit/test_http.py tests/unit/test_auth.py` passed with 3 files already formatted.
- `.venv/bin/mypy src/wikidot/util/http.py tests/unit/test_http.py tests/unit/test_auth.py` passed with no issues in 3 source files.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy .` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `calculate_backoff(None, 1.0, 2.0, 60.0)`, `retry_count=True`, `retry_count="1"`, `retry_count=0`, `retry_count=-1`, and `retry_count=1.5` raise `ValueError("retry_count must be a positive integer")`.
- `calculate_backoff(1, base_interval=None, ...)`, `base_interval=True`, `base_interval="1"`, and `base_interval=-0.1` raise `ValueError("base_interval must be a non-negative number")`.
- `calculate_backoff(1, ..., backoff_factor=None)`, `backoff_factor=True`, `backoff_factor="1"`, and `backoff_factor=-0.1` raise `ValueError("backoff_factor must be a non-negative number")`.
- `calculate_backoff(1, ..., max_backoff=None)`, `max_backoff=True`, `max_backoff="1"`, and `max_backoff=-0.1` raise `ValueError("max_backoff must be a non-negative number")`.
- `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, and `async_get_with_retry(...)` reject malformed `attempt_limit`, `retry_interval`, `max_backoff`, and `backoff_factor` controls before HTTP requests are issued.
- Valid default retry behavior, valid no-wait `retry_interval=0`, valid `raise_for_status=False`, and valid `follow_redirects` behavior remain unchanged.
- Existing Ajax, auth, QuickModule, and site callers that pass valid retry controls remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `True` as an attempt limit tightens behavior for callers that accidentally relied on Python's `bool` subclassing `int`. Mitigation: retry counts are documented as integers, and treating `True` as one attempt hides configuration parsing mistakes.
- Risk: Rejecting strings can expose CLI, environment, JSON, YAML, spreadsheet, or generated-structure parsing bugs. Mitigation: text configuration should parse numeric retry controls into real integers/floats before calling the HTTP retry helpers.
- Risk: Rejecting negative intervals may break callers that accidentally passed negative sleep/backoff controls. Mitigation: negative intervals can produce invalid sleep behavior and are not meaningful retry controls.
- Risk: This could be confused with Issue 390. Mitigation: Issue 390 covered boolean controls; this slice covers numeric retry/backoff controls.
- Risk: This could be confused with higher-level source iterator, publish visibility, or AMC retry option validation. Mitigation: those slices cover workflow-specific controls; this slice applies only to shared low-level HTTP retry helpers and `calculate_backoff(...)`.

## Dependencies

- Existing `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, `async_get_with_retry(...)`, and `calculate_backoff(...)` remain the source of truth for shared low-level HTTP retry behavior.
- Existing Ajax, auth, QuickModule, RequestUtil, and site workflows continue to use their current wrappers and retry helpers.
- The validation is local to `src/wikidot/util/http.py` and does not affect request URL construction, headers, form data, response parsing, higher-level exception conversion, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered HTTP retry numeric-control validation path.

## Upstream-Safe Motivation

`wikidot.util.http` is a low-level request utility under multiple practical Wikidot workflows. Since retry counts, retry intervals, maximum backoff, and backoff factors control request repetition and sleep behavior, malformed strings, booleans, non-positive attempt counts, and negative backoff controls should fail deterministically before request execution rather than silently changing retry behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established shared HTTP retry behavior as practical infrastructure for QuickModule lookup, auth, site probing, direct URL reads, and browser-free automation.
- Existing drafts covered QuickModule retry semantics, RequestUtil batching, source iterator retry controls, publish visibility retry controls, AMC retry batch controls, and HTTP retry boolean controls; they did not validate caller-provided low-level HTTP retry numeric controls.
- This slice only validates retry numeric inputs for `calculate_backoff(...)`, `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, and `async_get_with_retry(...)`. It does not change retry policy, status classification, response parsing, headers, auth behavior, Ajax behavior, RequestUtil behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or user names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed retry numeric controls instead of coercing them. Callers that load these controls from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should resolve them into real integers or floats before calling the shared HTTP retry helpers.
