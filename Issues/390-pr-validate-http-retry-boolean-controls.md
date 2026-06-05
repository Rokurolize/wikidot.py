# PR Draft: Validate HTTP Retry Boolean Controls

## Summary

`sync_get_with_retry(..., follow_redirects=..., raise_for_status=...)`, `sync_post_with_retry(..., raise_for_status=...)`, and `async_get_with_retry(..., follow_redirects=...)` documented those controls as booleans, but malformed caller-provided values were passed into the shared HTTP retry helpers. Falsy malformed values such as `None` and `0` could act like disabled controls, while truthy malformed values such as `"false"` and `1` could act like enabled controls or reach `httpx` before callers received a stable wikidot.py-side diagnostic.

This change validates the shared HTTP helper boolean controls before any HTTP request, retry loop, backoff, or `httpx` call. Malformed values now raise `ValueError("follow_redirects must be a boolean")` or `ValueError("raise_for_status must be a boolean")`. Existing valid default behavior, valid `False` controls, 4xx/5xx status handling, timeout/network retries, caller headers/data forwarding, and adjacent QuickModule/Auth/Ajax/Site callers remain unchanged.

## Outcome

Shared HTTP retry callers now get deterministic Python-side preflight validation for malformed redirect and status-handling controls instead of accidental truthiness changing redirect/status behavior or allowing malformed configuration to reach the network layer.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `wikidot.util.http` directly or indirectly through QuickModule lookup, auth login, Ajax client SSL/site probing, site source visibility probing, direct read workflows, generated audits, migration tools, moderation tools, or browser-free automation that may load request controls from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables.

## Current Evidence

Local rollout-backed drafts repeatedly identify the shared HTTP retry helpers as practical infrastructure beneath browser-free Wikidot automation. [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md) made QuickModule rely on `sync_get_with_retry(..., raise_for_status=False)` so transient 5xx responses can be retried before QuickModule maps a final 500 to `ValueError("Site is not found")`. [138-pr-reuse-requestutil-async-client.md](138-pr-reuse-requestutil-async-client.md) preserved direct URL retry behavior while improving request batching. [387-pr-validate-site-amc-return-exceptions-flag.md](387-pr-validate-site-amc-return-exceptions-flag.md), [388-pr-validate-requestutil-return-exceptions-flag.md](388-pr-validate-requestutil-return-exceptions-flag.md), and [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md) validate nearby boolean exception controls before branchy request execution paths.

Those prior slices are not duplicates. They covered QuickModule retry semantics, RequestUtil batching, and `return_exceptions` controls for site AMC, direct URL, and raw AMC boundaries. They did not validate low-level HTTP helper controls before `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, or `async_get_with_retry(...)` issue requests or branch on status handling.

The current callers make this low-level surface concrete: `src/wikidot/connector/ajax.py` uses `sync_get_with_retry(..., follow_redirects=False, raise_for_status=False)` while probing site existence and SSL support; `src/wikidot/module/site.py` uses `sync_get_with_retry(..., follow_redirects=True, raise_for_status=False)` for source visibility probing; `src/wikidot/util/quick_module.py` uses `sync_get_with_retry(..., raise_for_status=False)` for QuickModule lookups; and `src/wikidot/module/auth.py` uses `sync_post_with_retry(..., raise_for_status=False)` for login response handling.

No upstream issue was filed from this local workspace.

## Related Issue

Builds directly on [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [138-pr-reuse-requestutil-async-client.md](138-pr-reuse-requestutil-async-client.md), [387-pr-validate-site-amc-return-exceptions-flag.md](387-pr-validate-site-amc-return-exceptions-flag.md), [388-pr-validate-requestutil-return-exceptions-flag.md](388-pr-validate-requestutil-return-exceptions-flag.md), and [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md).

## Changes

- Validate `follow_redirects` in `sync_get_with_retry(...)` before request execution.
- Validate `raise_for_status` in `sync_get_with_retry(...)` before request execution.
- Validate `raise_for_status` in `sync_post_with_retry(...)` before request execution.
- Validate `follow_redirects` in `async_get_with_retry(...)` before request execution.
- Reject malformed controls with stable `ValueError("<field> must be a boolean")` diagnostics.
- Preserve valid `raise_for_status=False` behavior where 4xx responses are returned and retryable 5xx responses still retry.
- Preserve existing timeout, network, status, redirect, header, data, and adjacent caller behavior.

## Type Of Change

- Input validation
- Public helper behavior hardening
- Shared HTTP retry preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `sync_get_with_retry(..., follow_redirects=...)` must reject `None`, strings, integers, and other non-bool values with `ValueError("follow_redirects must be a boolean")` before issuing an HTTP request. |
| R2 | `sync_get_with_retry(..., raise_for_status=...)` must reject `None`, strings, integers, and other non-bool values with `ValueError("raise_for_status must be a boolean")` before issuing an HTTP request. |
| R3 | `sync_post_with_retry(..., raise_for_status=...)` must reject `None`, strings, integers, and other non-bool values with `ValueError("raise_for_status must be a boolean")` before issuing an HTTP request. |
| R4 | `async_get_with_retry(..., follow_redirects=...)` must reject `None`, strings, integers, and other non-bool values with `ValueError("follow_redirects must be a boolean")` before opening an async client or issuing an HTTP request. |
| R5 | Valid `raise_for_status=False` behavior must remain unchanged for sync GET and sync POST: non-retryable 4xx responses are returned, while retryable 5xx responses still retry before returning a successful later response or final response. |
| R6 | Adjacent Ajax, auth, QuickModule, and site callers that pass valid boolean controls must remain green. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, affected HTTP tests, adjacent tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed sync GET redirect controls fail before request setup. | `TestSyncGetWithRetry.test_rejects_non_bool_follow_redirects_before_request` failed RED for `None`, `"false"`, `0`, and `1` because malformed controls did not raise, then passed GREEN after validation was added. | Treating `"false"` or `1` as truthy, treating `None` or `0` as falsy, issuing a request, entering retry/backoff behavior, or raising an unrelated later error rejects this local completion claim. | Sync GET retry preflight | `src/wikidot/util/http.py`, `tests/unit/test_http.py` |
| R2 | Malformed sync GET status controls fail before request setup. | `TestSyncGetWithRetry.test_rejects_non_bool_raise_for_status_before_request` failed RED for `None`, `"false"`, `0`, and `1` because malformed controls did not raise, then passed GREEN after validation was added. | Coercing malformed values, issuing a request, reaching `response.raise_for_status()`, entering retry/backoff behavior, or raising an unrelated later error rejects this local completion claim. | Sync GET retry preflight | `src/wikidot/util/http.py`, `tests/unit/test_http.py` |
| R3 | Malformed sync POST status controls fail before request setup. | `TestSyncPostWithRetry.test_rejects_non_bool_raise_for_status_before_request` failed RED for `None`, `"false"`, `0`, and `1` because malformed controls did not raise, then passed GREEN after validation was added. | Coercing malformed values, issuing a POST, reaching status handling, entering retry/backoff behavior, or raising an unrelated later error rejects this local completion claim. | Sync POST retry preflight | `src/wikidot/util/http.py`, `tests/unit/test_http.py` |
| R4 | Malformed async GET redirect controls fail before async request setup. | `TestAsyncGetWithRetry.test_rejects_non_bool_follow_redirects_before_request` failed RED for `None`, `"false"`, `0`, and `1` because malformed controls did not raise, then passed GREEN after validation was added. | Opening `httpx.AsyncClient`, issuing a request, coercing malformed values, entering retry/backoff behavior, or raising an unrelated later error rejects this local completion claim. | Async GET retry preflight | `src/wikidot/util/http.py`, `tests/unit/test_http.py` |
| R5 | Valid `raise_for_status=False` semantics are preserved. | Focused GREEN included `test_raise_for_status_false` and `test_raise_for_status_false_retries_5xx` for sync GET and sync POST. | Returning 5xx without retry when a later success is available, raising on non-retryable 4xx despite `False`, or rejecting valid `False` rejects this local completion claim. | HTTP status handling | `tests/unit/test_http.py` |
| R6 | Adjacent callers remain green with valid boolean controls. | `tests/unit/test_http.py tests/unit/test_ajax.py tests/unit/test_auth.py tests/unit/test_quick_module.py tests/unit/test_site.py` passed 219 tests, and full unit tests passed 1154 tests. | Regressing Ajax site/SSL probing, auth login response handling, QuickModule lookup mapping, site source visibility probing, or direct helper retry behavior rejects this local completion claim. | Shared caller workflows | affected HTTP/Ajax/Auth/QuickModule/Site tests |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic values and `pytest-httpx` request assertions. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `de9fb46 fix(http): validate retry boolean controls`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_http.py::TestSyncGetWithRetry::test_rejects_non_bool_follow_redirects_before_request tests/unit/test_http.py::TestSyncGetWithRetry::test_rejects_non_bool_raise_for_status_before_request tests/unit/test_http.py::TestSyncPostWithRetry::test_rejects_non_bool_raise_for_status_before_request tests/unit/test_http.py::TestAsyncGetWithRetry::test_rejects_non_bool_follow_redirects_before_request` failed 16 selected tests before the fix because malformed boolean controls were accepted and requests were reached instead of raising.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_http.py::TestSyncGetWithRetry::test_rejects_non_bool_follow_redirects_before_request tests/unit/test_http.py::TestSyncGetWithRetry::test_rejects_non_bool_raise_for_status_before_request tests/unit/test_http.py::TestSyncGetWithRetry::test_raise_for_status_false tests/unit/test_http.py::TestSyncGetWithRetry::test_raise_for_status_false_retries_5xx tests/unit/test_http.py::TestSyncPostWithRetry::test_rejects_non_bool_raise_for_status_before_request tests/unit/test_http.py::TestSyncPostWithRetry::test_raise_for_status_false tests/unit/test_http.py::TestSyncPostWithRetry::test_raise_for_status_false_retries_5xx tests/unit/test_http.py::TestAsyncGetWithRetry::test_rejects_non_bool_follow_redirects_before_request` passed 20 tests after adding boolean preflight.
- `.venv/bin/python -m pytest -q tests/unit/test_http.py` passed 43 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_http.py tests/unit/test_ajax.py tests/unit/test_auth.py tests/unit/test_quick_module.py tests/unit/test_site.py` passed 219 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1154 tests.
- `.venv/bin/ruff check src/wikidot/util/http.py tests/unit/test_http.py` passed.
- `.venv/bin/ruff format --check src/wikidot/util/http.py tests/unit/test_http.py` passed with 2 files already formatted.
- `.venv/bin/mypy src/wikidot/util/http.py tests/unit/test_http.py` passed with no issues in 2 source files.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy .` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `sync_get_with_retry("https://example.com/test", follow_redirects=None)`, `follow_redirects="false"`, `follow_redirects=0`, and `follow_redirects=1` raise `ValueError("follow_redirects must be a boolean")` before HTTP requests are issued.
- `sync_get_with_retry("https://example.com/test", raise_for_status=None)`, `raise_for_status="false"`, `raise_for_status=0`, and `raise_for_status=1` raise `ValueError("raise_for_status must be a boolean")` before HTTP requests are issued.
- `sync_post_with_retry("https://example.com/test", raise_for_status=None)`, `raise_for_status="false"`, `raise_for_status=0`, and `raise_for_status=1` raise `ValueError("raise_for_status must be a boolean")` before HTTP requests are issued.
- `async_get_with_retry("https://example.com/test", follow_redirects=None)`, `follow_redirects="false"`, `follow_redirects=0`, and `follow_redirects=1` raise `ValueError("follow_redirects must be a boolean")` before opening an async client or issuing HTTP requests.
- Valid default and `True` behavior still raises on non-retryable 4xx and final retryable 5xx responses.
- Valid `raise_for_status=False` behavior still returns non-retryable 4xx responses and still retries retryable 5xx responses.
- Valid `follow_redirects=False` and `follow_redirects=True` values still pass through to `httpx` for sync and async GET.
- Existing Ajax, auth, QuickModule, and site callers that pass valid boolean controls remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `0` or `1` tightens behavior for callers that previously used integers as booleans. Mitigation: the documented API type is `bool`; accepting integer controls can hide configuration parsing mistakes and change redirect/status behavior.
- Risk: Rejecting strings can expose CLI, environment, JSON, YAML, spreadsheet, or generated-structure parsing bugs. Mitigation: text configuration should parse `"true"`/`"false"` into real booleans before calling the HTTP retry helpers.
- Risk: The change could be confused with `return_exceptions` validation. Mitigation: Issues 387, 388, and 389 covered exception-return controls; this slice applies only to low-level HTTP redirect/status controls.
- Risk: The change could accidentally change valid `raise_for_status=False` retry semantics. Mitigation: focused GREEN explicitly includes both 4xx-return and 5xx-retry behavior for sync GET and sync POST.

## Dependencies

- Existing `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, and `async_get_with_retry(...)` remain the source of truth for shared low-level HTTP retry behavior.
- Existing Ajax, auth, QuickModule, RequestUtil, and site workflows continue to use their current wrappers and retry helpers.
- The validation is local to `src/wikidot/util/http.py` and does not affect request URL construction, headers, form data, retry timing, response parsing, higher-level exception conversion, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered HTTP retry boolean-control validation path.

## Upstream-Safe Motivation

`wikidot.util.http` is a low-level request utility under multiple practical Wikidot workflows. Since `follow_redirects` and `raise_for_status` control network behavior and status handling, malformed truthy strings and integer stand-ins should fail deterministically before request execution rather than silently changing redirect/status behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established shared HTTP retry behavior as practical infrastructure for QuickModule lookup, auth, site probing, direct URL reads, and browser-free automation.
- Existing drafts covered QuickModule retry semantics, RequestUtil batching, and nearby `return_exceptions` controls; they did not validate caller-provided low-level HTTP redirect/status controls.
- This slice only validates `follow_redirects` and `raise_for_status` inputs for `sync_get_with_retry(...)`, `sync_post_with_retry(...)`, and `async_get_with_retry(...)`. It does not change retry policy, status classification, response parsing, headers, auth behavior, Ajax behavior, RequestUtil behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or user names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed redirect/status controls instead of coercing them. Callers that load these controls from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should resolve them into real booleans before calling the shared HTTP retry helpers.
