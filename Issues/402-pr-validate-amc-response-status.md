# PR Draft: Validate AMC Response Status Field

## Summary

`AjaxModuleConnectorClient.request(...)` already retries non-JSON responses, non-dictionary JSON responses, empty dictionaries, and explicit `status: try_again` responses. A nonempty decoded dictionary without `status`, such as `{"body": ""}`, still returned as a successful raw AMC response, leaving callers to discover an unclassified Wikidot payload later or treat it as success.

This change validates the raw AMC response shape after JSON decoding and before status classification. A decoded nonempty dictionary must include `status`. Missing `status` now follows the same retry pattern as adjacent malformed AMC payloads and raises `ResponseDataException("AMC response is missing status field")` at the attempt limit. Existing `status: ok`, `status: try_again`, `status: no_permission`, non-`ok` status mapping, non-JSON handling, non-dictionary JSON handling, empty-response handling, request construction, token handling, header validation, numeric controls, and higher-level module-specific diagnostics remain unchanged.

## Outcome

Raw AMC responses that omit the required `status` field no longer pass through as successful `httpx.Response` objects. The lower-level connector now classifies the missing field consistently with other malformed AMC response data before returning to callers.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call `AjaxModuleConnectorClient.request(...)` directly or rely on raw AMC response processing through generated request batches, local migration tooling, sandbox probes, archival jobs, or moderation utilities.

## Current Evidence

Local rollout-backed drafts already establish raw AMC request execution as a shared lower-level surface. [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md) covered `return_exceptions`, [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md) covered raw AMC numeric execution controls, [398-pr-validate-amc-cookie-names.md](398-pr-validate-amc-cookie-names.md), [399-pr-validate-amc-cookie-values.md](399-pr-validate-amc-cookie-values.md), and [400-pr-validate-amc-header-values.md](400-pr-validate-amc-header-values.md) covered request-header state, and [401-pr-validate-amc-request-bodies.md](401-pr-validate-amc-request-bodies.md) covered raw request-body batch shape.

Those prior slices are not duplicates. They validate caller-provided request state and execution controls, not the decoded raw AMC response dictionary. Earlier module-level action-status drafts such as [248-pr-page-delete-action-status-context.md](248-pr-page-delete-action-status-context.md), [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), and [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md) reject missing action statuses with operation-specific context after higher-level workflows have their own response dictionaries. This slice keeps those diagnostics intact and hardens only the raw AMC connector boundary.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md), [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md), [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), [398-pr-validate-amc-cookie-names.md](398-pr-validate-amc-cookie-names.md), [399-pr-validate-amc-cookie-values.md](399-pr-validate-amc-cookie-values.md), [400-pr-validate-amc-header-values.md](400-pr-validate-amc-header-values.md), and [401-pr-validate-amc-request-bodies.md](401-pr-validate-amc-request-bodies.md).

## Changes

- Add a missing-`status` guard in `src/wikidot/connector/ajax.py` after decoded response dictionaries have been proven nonempty.
- Retry missing-`status` responses using the existing raw AMC backoff controls.
- Raise `ResponseDataException("AMC response is missing status field")` when the retry limit is exhausted.
- Keep the existing status-handling branch structure intact so `try_again`, `no_permission`, non-`ok`, and `ok` behavior remains unchanged.
- Add public-interface tests for retrying a missing-`status` response and for the retry-exhausted exception.

## Type Of Change

- Response validation
- Raw AMC connector hardening
- Retry behavior consistency
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `AjaxModuleConnectorClient.request(...)` must retry a nonempty decoded dictionary that lacks `status` before returning a raw response. |
| R2 | Missing-`status` raw AMC responses must raise `ResponseDataException("AMC response is missing status field")` once `attempt_limit` is exhausted. |
| R3 | Existing valid raw AMC behavior must remain unchanged, including `status: ok`, `status: try_again`, `status: no_permission`, other non-`ok` statuses, non-JSON responses, non-dictionary JSON responses, empty dictionaries, request construction, token defaults, explicit token preservation, site override validation, return-exceptions behavior, numeric controls, request-header validation, and request-body batch validation. |
| R4 | Diagnostics, docs, and tests must not expose raw response bodies, private payloads, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, adjacent AMC/ajax/site/RequestUtil/auth tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A first raw AMC response of `{"body": ""}` is retried, and a second response of `{"status": "ok", "body": ""}` is returned. | `TestAjaxModuleConnectorClientRequest.test_retry_on_missing_status_response` failed RED because only one request was issued, then passed GREEN after the missing-`status` guard. | Returning the first response, consuming only one mock request, fabricating `status`, or skipping retry rejects this local completion claim. | Raw AMC response parser | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | Repeated `{"body": ""}` responses with `attempt_limit=2` raise `ResponseDataException("AMC response is missing status field")`. | `TestAjaxModuleConnectorClientRequest.test_missing_status_response_max_retry` passed GREEN. | Raising `KeyError`, `WikidotStatusCodeException`, `ForbiddenException`, a generic exception, or including raw response JSON in the public error message rejects this local completion claim. | Raw AMC retry terminal path | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R3 | Existing adjacent behavior remains stable. | `TestAjaxModuleConnectorClientRequest` passed 61 tests; `tests/unit/test_amc_client.py tests/unit/test_ajax.py` passed 139 tests; `tests/unit/test_site.py tests/unit/test_requestutil.py tests/unit/test_auth.py` passed 243 tests; full unit passed 1433 tests. | Regressing successful raw AMC responses, `try_again`, `no_permission`, non-`ok` mapping, malformed JSON handling, empty response retrying, request bodies, headers, numeric controls, Site wrapper behavior, RequestUtil, or Auth rejects this local completion claim. | AMC/request utility workflows | affected unit suites |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic mocked JSON dictionaries and local assertions; the terminal exception message names only the missing field. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private site data, source text from real sites, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d536b7d fix(amc): validate response status field`.

- RED tracer: `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_retry_on_missing_status_response -q` failed before the fix because `client.request([{"moduleName": "Test"}])` returned after one POST from a decoded `{"body": ""}` response and left the second mocked `{"status": "ok", "body": ""}` response unconsumed.
- GREEN focused pair: `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_retry_on_missing_status_response tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_missing_status_response_max_retry -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest -q` passed 61 tests.
- `uv run --extra test pytest tests/unit/test_amc_client.py tests/unit/test_ajax.py -q` passed 139 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_requestutil.py tests/unit/test_auth.py -q` passed 243 tests.
- `uv run --extra test pytest tests/unit -q` passed 1433 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 81 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files.
- `git diff --check` passed before the code commit.

Not run successfully: `pyright --version` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- A nonempty raw AMC response dictionary without `status` is retried instead of returned.
- Retry exhaustion for missing `status` raises `ResponseDataException("AMC response is missing status field")`.
- Successful `status: ok`, retrying `status: try_again`, forbidden `status: no_permission`, and other non-`ok` statuses keep their existing behavior.
- Non-JSON responses, non-dictionary JSON responses, and empty dictionaries keep their existing retry and terminal-error behavior.
- Valid request bodies, empty request batches, explicit request-body `wikidot_token7`, header-cookie token defaults, site override validation, return-exceptions behavior, numeric-control validation, cookie validation, header-value validation, request-body batch validation, Site wrapper delegation, RequestUtil, and auth behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Some raw callers may have intentionally used `AjaxModuleConnectorClient.request(...)` for nonstandard decoded dictionaries without `status`. Mitigation: this client is the Ajax Module Connector path, and adjacent response validation already treats malformed AMC payloads as retryable response-data failures.
- Risk: The lower-level guard could be confused with module-specific action-status diagnostics. Mitigation: higher-level modules still own their contextual action validators; this slice applies only to raw connector responses before returning an `httpx.Response`.
- Risk: Retry behavior could hide a persistent malformed response until the attempt limit. Mitigation: this matches the existing non-JSON, non-dictionary, empty-dictionary, and `try_again` response patterns and preserves caller-configured retry limits.
- Risk: Diagnostics could leak response content. Mitigation: the public terminal exception names only the missing field, and logs use the existing masked request-body helper rather than embedding raw response JSON.

## Dependencies

- Existing `AjaxModuleConnectorClient.request(...)` remains the source of truth for raw Ajax Module Connector request execution.
- Existing `_calculate_backoff(...)` and validated `AjaxModuleConnectorConfig` values remain the source of truth for raw AMC retry timing.
- Existing `AjaxRequestHeader.cookie` remains the source of truth for default `wikidot_token7` header-cookie values.
- Existing request-body merging remains the source of truth for explicit caller token preservation.
- Existing Site and RequestUtil wrappers continue to own their higher-level delegation behavior.
- The validation is local to `src/wikidot/connector/ajax.py` and does not alter URL routing, request body field semantics, retry control validation, RequestUtil host filtering, module-specific action-status validators, or live Wikidot behavior.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-body field-type checks, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered raw AMC response-status field path.

## Upstream-Safe Motivation

Raw AMC request execution is a shared lower-level workflow for browser-free Wikidot operations. Since Wikidot's Ajax Module Connector status handling determines whether callers should proceed, retry, or raise a mapped exception, a decoded response dictionary without `status` should not be returned as if it were a classified success. The fix is intentionally narrow: it retries and then reports only the missing status field while preserving existing status values and higher-level operation-specific diagnostics.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established raw AMC request execution as shared infrastructure for `wikidot_token7` handling, site wrapper delegation, request utilities, login/session setup, public source fetches, and many module workflows.
- Existing drafts covered sensitive-log masking, token value preservation, return-exceptions validation, numeric request controls, cookie-name validation, cookie-value validation, explicit request-header value validation, and request-body batch validation; they did not validate nonempty decoded raw AMC responses that omit `status`.
- This slice only validates the raw response dictionary's `status` presence. It does not change token defaults, token masking, login credentials, session-cookie validation, logout cleanup, retry control validation, URL routing, request-body field semantics, RequestUtil behavior, Site wrapper behavior, module-specific action-status diagnostics, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The validation intentionally does not validate the type or vocabulary of `status` beyond the existing status-handling logic. Non-`ok` values continue to flow through `WikidotStatusCodeException`, and future slices can evaluate field-type validation separately if rollout evidence supports it.
