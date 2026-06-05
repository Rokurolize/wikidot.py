# PR Draft: Validate AMC Numeric Request Controls

## Summary

`AjaxModuleConnectorClient.request(...)` uses `AjaxModuleConnectorConfig` numeric controls for request timeout, retry attempts, backoff calculation, and concurrent request limits, but malformed caller-provided values were not rejected at the raw Ajax Module Connector request boundary. Values such as `request_timeout=None`, `request_timeout="1"`, `attempt_limit=0`, `attempt_limit=True`, `retry_interval="1"`, `max_backoff=-0.1`, `backoff_factor=True`, or `semaphore_limit=0` could reach request execution, raise later generic errors, or in the zero-semaphore case block non-empty request work instead of producing a stable wikidot.py-side diagnostic.

This change validates raw AMC request numeric controls before semaphore setup, site override validation, async client creation, or HTTP request execution. Invalid request timeouts now raise `ValueError("request_timeout must be a positive number")`. Invalid attempt and semaphore limits now raise `ValueError("<field> must be a positive integer")`. Invalid retry/backoff controls now raise `ValueError("<field> must be a non-negative number")`. Existing valid default request behavior, valid no-wait retry intervals, valid zero backoff controls, request body token preservation, site override validation, response parsing, retry policy, Issue 389 return-exceptions validation, Issue 391 shared HTTP retry validation, and wrapper-level behavior remain unchanged.

## Outcome

Raw AMC callers now get deterministic Python-side preflight validation for malformed numeric request controls instead of accidental request execution, implicit retry-loop shape changes, unrelated downstream errors, or zero-semaphore stalls.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using the raw Ajax Module Connector client directly or indirectly through site, page, forum, private-message, member, application, archival, generated-audit, migration, moderation, or browser-free automation workflows that may load AMC request controls from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables.

## Current Evidence

Local rollout-backed drafts repeatedly identify raw AMC request behavior as a practical shared surface. Existing drafts [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md), [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [139-pr-skip-empty-amc-retry-batches.md](139-pr-skip-empty-amc-retry-batches.md), [140-pr-skip-empty-site-amc-request-batches.md](140-pr-skip-empty-site-amc-request-batches.md), [387-pr-validate-site-amc-return-exceptions-flag.md](387-pr-validate-site-amc-return-exceptions-flag.md), [388-pr-validate-requestutil-return-exceptions-flag.md](388-pr-validate-requestutil-return-exceptions-flag.md), [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md), [390-pr-validate-http-retry-boolean-controls.md](390-pr-validate-http-retry-boolean-controls.md), and [391-pr-validate-http-retry-numeric-controls.md](391-pr-validate-http-retry-numeric-controls.md) cover AMC logging, token preservation, empty batches, wrapper/direct-URL boolean controls, raw AMC exception mode, and shared HTTP retry controls.

Those prior slices are not duplicates. Issue 389 validates `return_exceptions` before raw AMC request setup, but does not validate retry, timeout, or concurrency numeric controls. Issue 391 validates `wikidot.util.http` retry helper numeric controls, but explicitly leaves Ajax request execution unchanged. Issue 139 validates empty site-level AMC retry batches and explicit `batch_size`/`max_retries` options, not `AjaxModuleConnectorClient.request(...)` config values. This slice applies to raw AMC request execution and its local `_calculate_backoff(...)` helper.

No upstream issue was filed from this local workspace.

## Related Issue

Builds directly on [139-pr-skip-empty-amc-retry-batches.md](139-pr-skip-empty-amc-retry-batches.md), [140-pr-skip-empty-site-amc-request-batches.md](140-pr-skip-empty-site-amc-request-batches.md), [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md), [390-pr-validate-http-retry-boolean-controls.md](390-pr-validate-http-retry-boolean-controls.md), and [391-pr-validate-http-retry-numeric-controls.md](391-pr-validate-http-retry-numeric-controls.md).

## Changes

- Validate `request_timeout` in `AjaxModuleConnectorClient.request(...)` as a non-bool positive number before request execution.
- Validate `attempt_limit` and `semaphore_limit` as non-bool positive integers before request execution.
- Validate `retry_interval`, `max_backoff`, and `backoff_factor` as non-bool non-negative numbers before request execution.
- Validate raw AMC `_calculate_backoff(...)` retry counts and numeric backoff inputs before jitter computation.
- Use validated local config values inside the raw AMC request loop instead of repeatedly reading mutable `self.config` fields mid-request.
- Preserve valid zero retry intervals and zero backoff controls as explicit no-wait/no-growth controls.
- Preserve valid default request behavior, valid `return_exceptions` behavior, body token preservation, site override validation, retry policy, response parsing, status handling, and wrapper-level behavior.

## Type Of Change

- Input validation
- Public API behavior hardening
- Raw Ajax Module Connector numeric-control preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `AjaxModuleConnectorClient.request(...)` must reject malformed `request_timeout` values with `ValueError("request_timeout must be a positive number")` before HTTP requests are issued. |
| R2 | `AjaxModuleConnectorClient.request(...)` must reject malformed `attempt_limit` and `semaphore_limit` values with `ValueError("<field> must be a positive integer")` before semaphore setup can block or request work can start. |
| R3 | `AjaxModuleConnectorClient.request(...)` must reject malformed `retry_interval`, `max_backoff`, and `backoff_factor` values with `ValueError("<field> must be a non-negative number")` before HTTP requests are issued. |
| R4 | Raw AMC `_calculate_backoff(...)` must reject malformed retry counts and backoff controls before computing jitter. |
| R5 | Valid default raw AMC request behavior must remain unchanged, including retries, response parsing, Wikidot status handling, HTTP error handling, and exception-returning mode. |
| R6 | Existing raw AMC body handling and routing must remain unchanged, including caller body immutability, explicit `wikidot_token7` preservation, header-cookie token defaults, site override validation, and custom site routing. |
| R7 | Adjacent Ajax connector, site wrapper, RequestUtil, and shared HTTP retry behavior must remain unchanged. |
| R8 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, affected AMC tests, adjacent tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed request timeouts fail before raw AMC request execution. | `test_request_rejects_invalid_positive_timeout_config_before_request` passed GREEN and asserts `httpx_mock.get_requests() == []`. | Issuing a POST, retrying an unmatched POST, accepting booleans or strings, treating `0` as a valid timeout, or raising `AMCHttpStatusCodeException` rejects this local completion claim. | Raw AMC preflight | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | Malformed attempt and semaphore limits fail before semaphore/request setup. | `test_request_rejects_invalid_positive_integer_config_before_request` passed GREEN and asserts no requests are issued. | Treating `True` as one attempt, treating `0` as an empty retry loop, creating `asyncio.Semaphore(0)` for a non-empty request, issuing a POST, or raising an unrelated later error rejects this local completion claim. | Raw AMC preflight | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R3 | Malformed retry/backoff controls fail before request setup. | `test_request_rejects_invalid_retry_number_config_before_request` passed GREEN and asserts no requests are issued. | Coercing strings, accepting booleans, accepting negative sleeps, issuing a POST, or raising an unrelated arithmetic/sleep error rejects this local completion claim. | Raw AMC preflight | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R4 | Raw AMC backoff helper validates its own direct inputs. | `TestCalculateBackoff.test_rejects_invalid_retry_count` and `test_rejects_invalid_numeric_backoff_options` passed GREEN. | Returning a computed backoff for invalid retry counts, accepting strings or booleans, producing negative jitter ranges, or raising unrelated arithmetic errors rejects this local completion claim. | Raw AMC backoff helper | `src/wikidot/connector/ajax.py`, `tests/unit/test_ajax.py` |
| R5 | Valid raw AMC behavior remains stable. | `tests/unit/test_amc_client.py` passed 67 tests and full unit passed 1274 tests. | Regressing retry count, try-again handling, JSON validation, empty-response handling, HTTP status handling, exception mode, or response tuple shape rejects this local completion claim. | Raw AMC request behavior | `tests/unit/test_amc_client.py` |
| R6 | Request body and routing behavior remains stable. | Existing body mutation, explicit token, header token, site override, and custom-site tests in `tests/unit/test_amc_client.py` passed after validation was added. | Mutating caller dictionaries, overwriting explicit tokens, losing header-cookie defaults, accepting invalid site overrides, or misrouting custom site requests rejects this local completion claim. | Request preparation and routing | `tests/unit/test_amc_client.py` |
| R7 | Adjacent wrappers remain green. | `tests/unit/test_site.py tests/unit/test_requestutil.py tests/unit/test_http.py` passed 267 tests after validation was added. | Regressing site wrappers, RequestUtil direct URL behavior, or shared HTTP retry validation rejects this local completion claim. | Adjacent workflows | affected site/requestutil/http tests |
| R8 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic values, mocks, and `pytest-httpx` request assertions. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, affected tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `f99bffe fix(ajax): validate amc numeric controls`.

- RED: `timeout 8s .venv/bin/python -m pytest -q tests/unit/test_ajax.py::TestCalculateBackoff::test_rejects_invalid_retry_count tests/unit/test_ajax.py::TestCalculateBackoff::test_rejects_invalid_numeric_backoff_options tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_invalid_positive_integer_config_before_request tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_invalid_positive_timeout_config_before_request tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_invalid_retry_number_config_before_request tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_accepts_zero_backoff_controls` exited `124` before the fix after showing the new backoff tests failing and the AMC numeric tests entering the unvalidated request/semaphore path.
- RED detail: `timeout 8s .venv/bin/python -m pytest -q tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_invalid_positive_timeout_config_before_request` failed 5 tests and 5 teardown checks before the fix because malformed timeout values still issued unmatched POST requests.
- GREEN: the full focused selection above passed 48 tests after adding numeric preflight.
- `.venv/bin/python -m pytest -q tests/unit/test_ajax.py` passed 32 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_amc_client.py` passed 67 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_site.py tests/unit/test_requestutil.py tests/unit/test_http.py` passed 267 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1274 tests.
- `.venv/bin/python -m ruff check .` passed.
- `.venv/bin/python -m ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/python -m mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `AjaxModuleConnectorClient(site_name="www", config=AjaxModuleConnectorConfig(request_timeout=None)).request([...])`, `request_timeout=True`, `request_timeout="1"`, `request_timeout=0`, and `request_timeout=-0.1` raise `ValueError("request_timeout must be a positive number")` before HTTP requests are issued.
- `attempt_limit=None`, `attempt_limit=True`, `attempt_limit="1"`, `attempt_limit=0`, `attempt_limit=-1`, and `attempt_limit=1.5` raise `ValueError("attempt_limit must be a positive integer")` before HTTP requests are issued.
- `semaphore_limit=None`, `semaphore_limit=True`, `semaphore_limit="1"`, `semaphore_limit=0`, `semaphore_limit=-1`, and `semaphore_limit=1.5` raise `ValueError("semaphore_limit must be a positive integer")` before semaphore setup can block a non-empty request.
- `retry_interval`, `max_backoff`, and `backoff_factor` reject `None`, booleans, strings, and negative numbers with `ValueError("<field> must be a non-negative number")` before HTTP requests are issued.
- Raw AMC `_calculate_backoff(...)` rejects malformed `retry_count`, `base_interval`, `backoff_factor`, and `max_backoff` inputs before computing jitter.
- Valid default AMC requests, valid `retry_interval=0`, valid `max_backoff=0`, valid `backoff_factor=0`, valid `return_exceptions=True`, valid site overrides, token handling, retry behavior, response parsing, and status handling remain unchanged.
- Existing `Site.amc_request(...)`, `Site.amc_request_with_retry(...)`, `RequestUtil.request(...)`, and shared HTTP retry helper behavior remains unchanged; those surfaces keep their own validation coverage.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting booleans as numeric controls tightens behavior for callers that accidentally relied on Python's `bool` subclassing `int`. Mitigation: these fields are documented as numeric controls; accepting booleans hides configuration parsing mistakes and can change retry/concurrency behavior.
- Risk: Rejecting strings can expose CLI, environment, JSON, YAML, spreadsheet, or generated-structure parsing bugs. Mitigation: text configuration should parse numeric controls into real integers or floats before constructing raw AMC requests.
- Risk: Rejecting `semaphore_limit=0` changes an accidental deadlock-like configuration into an explicit error. Mitigation: a zero-capacity semaphore cannot make progress for non-empty AMC request batches.
- Risk: The change could be confused with Issue 389. Mitigation: Issue 389 covered the boolean exception-returning control; this slice covers numeric timeout/retry/backoff/concurrency controls.
- Risk: The change could be confused with Issue 391. Mitigation: Issue 391 covered shared `wikidot.util.http` retry helpers; this slice applies to raw AMC request execution and raw AMC backoff.

## Dependencies

- Existing `AjaxModuleConnectorClient.request(...)` remains the source of truth for raw Ajax Module Connector request execution.
- Existing site, page, forum, private-message, member, and application workflows continue to use their current wrappers and retry helpers.
- Existing `Site.amc_request(...)`, `Site.amc_request_with_retry(...)`, `RequestUtil.request(...)`, and `wikidot.util.http` validation remains separate and unchanged.
- The validation is local to `src/wikidot/connector/ajax.py` and does not affect request body construction, request URLs, response parsing, higher-level wrapper behavior, direct URL request behavior, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, RequestUtil config-default validation, site-level AMC retry-default validation, or complexity candidates outside this now-covered raw AMC numeric-control path.

## Upstream-Safe Motivation

`AjaxModuleConnectorClient.request(...)` is the lower-level batch executor beneath many Wikidot AMC workflows. Since timeout, retry count, backoff, and concurrency controls determine whether request work starts, repeats, sleeps, or blocks, malformed strings, booleans, non-positive counts, negative backoff values, and zero concurrency should fail deterministically before request setup.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established raw AMC request behavior as a practical shared surface through page, forum, private-message, member, application, and site workflows.
- Existing AMC drafts covered token preservation, sensitive log masking, empty batches, wrapper/direct-URL exception controls, raw AMC exception controls, and shared HTTP retry controls; they did not validate caller-provided raw AMC numeric request controls.
- This slice only validates raw AMC request timeout, attempt, retry/backoff, semaphore, and backoff-helper inputs. It does not change request body construction, request URL construction, retry policy, response parsing, logging, site wrapper behavior, RequestUtil behavior, shared HTTP helper behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or user names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed numeric controls instead of coercing them. Callers that load these controls from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should resolve them into real integers or floats before calling `AjaxModuleConnectorClient.request(...)`.
