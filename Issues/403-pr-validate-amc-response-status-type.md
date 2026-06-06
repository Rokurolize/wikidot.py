# PR Draft: Validate AMC Response Status Type

## Summary

`AjaxModuleConnectorClient.request(...)` now requires decoded raw AMC response dictionaries to include `status`, but the current status-classification branch still accepts any present value. A response like `{"status": 123, "body": ""}` is classified as a Wikidot status-code error, raises `WikidotStatusCodeException`, and stores a non-string `status_code` even though the exception contract documents Wikidot status codes as strings.

This change validates the raw AMC response `status` value after presence has been confirmed and before the existing status classification runs. Non-string `status` values now follow the same retry pattern as adjacent malformed AMC payloads and raise `ResponseDataException("AMC response status must be a string")` at the attempt limit. Existing `status: ok`, `status: try_again`, `status: no_permission`, other string non-`ok` statuses, missing-status handling, non-JSON handling, non-dictionary JSON handling, empty-response handling, request construction, token handling, header validation, numeric controls, request-body validation, and higher-level module-specific diagnostics remain unchanged.

## Outcome

Raw AMC responses with non-string `status` values no longer enter `WikidotStatusCodeException` as bogus Wikidot status codes. The lower-level connector now classifies malformed status values consistently with malformed response data before returning or raising status-specific exceptions.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call `AjaxModuleConnectorClient.request(...)` directly or rely on raw AMC response processing through generated request batches, local migration tooling, sandbox probes, archival jobs, or moderation utilities.

## Current Evidence

Local rollout-backed drafts establish raw AMC request execution as a shared lower-level surface. [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md) covered `return_exceptions`, [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md) covered raw AMC numeric execution controls, [398-pr-validate-amc-cookie-names.md](398-pr-validate-amc-cookie-names.md), [399-pr-validate-amc-cookie-values.md](399-pr-validate-amc-cookie-values.md), and [400-pr-validate-amc-header-values.md](400-pr-validate-amc-header-values.md) covered request-header state, [401-pr-validate-amc-request-bodies.md](401-pr-validate-amc-request-bodies.md) covered raw request-body batch shape, and [402-pr-validate-amc-response-status.md](402-pr-validate-amc-response-status.md) covered missing response `status`.

Those prior slices are not duplicates. Issue 402 requires `status` to be present, but explicitly left status type and vocabulary validation for a future slice. Earlier module-level action-status drafts such as [248-pr-page-delete-action-status-context.md](248-pr-page-delete-action-status-context.md), [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), and [254-pr-private-message-send-action-status-context.md](254-pr-private-message-send-action-status-context.md) reject missing action statuses with operation-specific context after higher-level workflows have their own response dictionaries. This slice keeps those diagnostics intact and hardens only the raw AMC connector status-value boundary.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md), [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md), [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), [398-pr-validate-amc-cookie-names.md](398-pr-validate-amc-cookie-names.md), [399-pr-validate-amc-cookie-values.md](399-pr-validate-amc-cookie-values.md), [400-pr-validate-amc-header-values.md](400-pr-validate-amc-header-values.md), [401-pr-validate-amc-request-bodies.md](401-pr-validate-amc-request-bodies.md), and [402-pr-validate-amc-response-status.md](402-pr-validate-amc-response-status.md).

## Changes

- Add a non-string `status` guard in `src/wikidot/connector/ajax.py` after decoded response dictionaries have been proven nonempty and status-bearing.
- Retry non-string `status` responses using the existing raw AMC backoff controls.
- Raise `ResponseDataException("AMC response status must be a string")` when the retry limit is exhausted.
- Keep the existing string status-handling branch intact so `try_again`, `no_permission`, string non-`ok`, and `ok` behavior remains unchanged.
- Add public-interface tests for retrying a non-string `status` response and for the retry-exhausted exception.

## Type Of Change

- Response validation
- Raw AMC connector hardening
- Retry behavior consistency
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `AjaxModuleConnectorClient.request(...)` must retry a nonempty decoded dictionary whose present `status` value is not a string before returning a raw response or raising a Wikidot status-code exception. |
| R2 | Non-string raw AMC `status` values must raise `ResponseDataException("AMC response status must be a string")` once `attempt_limit` is exhausted. |
| R3 | Existing valid raw AMC behavior must remain unchanged, including `status: ok`, `status: try_again`, `status: no_permission`, other string non-`ok` statuses, missing `status`, non-JSON responses, non-dictionary JSON responses, empty dictionaries, request construction, token defaults, explicit token preservation, site override validation, return-exceptions behavior, numeric controls, request-header validation, and request-body batch validation. |
| R4 | Diagnostics, docs, and tests must not expose raw response bodies, private payloads, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, adjacent AMC/ajax/site/RequestUtil/auth tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A first raw AMC response of `{"status": 123, "body": ""}` is retried, and a second response of `{"status": "ok", "body": ""}` is returned. | `TestAjaxModuleConnectorClientRequest.test_retry_on_non_string_status_response` failed RED with immediate `WikidotStatusCodeException`, then passed GREEN after the non-string status guard. | Returning the first response, raising `WikidotStatusCodeException`, consuming only one mock request, coercing `123` to `"123"`, fabricating `status`, or skipping retry rejects this local completion claim. | Raw AMC response parser | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | Repeated `{"status": 123, "body": ""}` responses with `attempt_limit=2` raise `ResponseDataException("AMC response status must be a string")`. | `TestAjaxModuleConnectorClientRequest.test_non_string_status_response_max_retry` passed GREEN. | Raising `KeyError`, `WikidotStatusCodeException`, `ForbiddenException`, a generic exception, coercing the value, or including raw response JSON in the public error message rejects this local completion claim. | Raw AMC retry terminal path | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R3 | Existing adjacent behavior remains stable. | `TestAjaxModuleConnectorClientRequest` passed 63 tests; `tests/unit/test_amc_client.py tests/unit/test_ajax.py` passed 141 tests; `tests/unit/test_site.py tests/unit/test_requestutil.py tests/unit/test_auth.py` passed 243 tests; full unit passed 1435 tests. | Regressing successful raw AMC responses, `try_again`, `no_permission`, string non-`ok` mapping, missing-status handling, malformed JSON handling, empty response retrying, request bodies, headers, numeric controls, Site wrapper behavior, RequestUtil, or Auth rejects this local completion claim. | AMC/request utility workflows | affected unit suites |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic mocked JSON dictionaries and local assertions; the terminal exception message names only the malformed field. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private site data, source text from real sites, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `3105879 fix(amc): validate response status type`.

- RED tracer: `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_retry_on_non_string_status_response -q` failed before the fix because `client.request([{"moduleName": "Test"}])` classified decoded `{"status": 123, "body": ""}` as `WikidotStatusCodeException` and left the second mocked `{"status": "ok", "body": ""}` response unconsumed.
- GREEN focused pair: `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_retry_on_non_string_status_response tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_non_string_status_response_max_retry -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest -q` passed 63 tests.
- `uv run --extra test pytest tests/unit/test_amc_client.py tests/unit/test_ajax.py -q` passed 141 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_requestutil.py tests/unit/test_auth.py -q` passed 243 tests.
- `uv run --extra test pytest tests/unit -q` passed 1435 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 81 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files.
- `git diff --check` passed before the code commit.

Not run successfully: `pyright --version` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- A nonempty raw AMC response dictionary with a non-string `status` is retried instead of returned or classified as a Wikidot status-code exception.
- Retry exhaustion for non-string `status` raises `ResponseDataException("AMC response status must be a string")`.
- Successful `status: ok`, retrying `status: try_again`, forbidden `status: no_permission`, and other string non-`ok` statuses keep their existing behavior.
- Missing `status`, non-JSON responses, non-dictionary JSON responses, and empty dictionaries keep their existing retry and terminal-error behavior.
- Valid request bodies, empty request batches, explicit request-body `wikidot_token7`, header-cookie token defaults, site override validation, return-exceptions behavior, numeric-control validation, cookie validation, header-value validation, request-body batch validation, Site wrapper delegation, RequestUtil, and auth behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Some raw callers may have intentionally relied on non-string status values flowing through `WikidotStatusCodeException`. Mitigation: `WikidotStatusCodeException.status_code` is documented as a string Wikidot code, so non-string decoded JSON values are malformed response data rather than valid Wikidot status codes.
- Risk: The lower-level guard could be confused with module-specific action-status diagnostics. Mitigation: higher-level modules still own their contextual action validators; this slice applies only to raw connector responses before returning an `httpx.Response` or raising status-specific exceptions.
- Risk: Retry behavior could hide a persistent malformed response until the attempt limit. Mitigation: this matches the existing non-JSON, non-dictionary, empty-dictionary, missing-status, and `try_again` response patterns and preserves caller-configured retry limits.
- Risk: Diagnostics could leak response content. Mitigation: the public terminal exception names only the malformed field, and logs use the existing masked request-body helper rather than embedding raw response JSON.

## Dependencies

- Existing `AjaxModuleConnectorClient.request(...)` remains the source of truth for raw Ajax Module Connector request execution.
- Existing `_calculate_backoff(...)` and validated `AjaxModuleConnectorConfig` values remain the source of truth for raw AMC retry timing.
- Existing `AjaxRequestHeader.cookie` remains the source of truth for default `wikidot_token7` header-cookie values.
- Existing request-body merging remains the source of truth for explicit caller token preservation.
- Existing Site and RequestUtil wrappers continue to own their higher-level delegation behavior.
- The validation is local to `src/wikidot/connector/ajax.py` and does not alter URL routing, request body field semantics, retry control validation, RequestUtil host filtering, module-specific action-status validators, or live Wikidot behavior.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-body field-type checks, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered raw AMC response-status type path.

## Upstream-Safe Motivation

Raw AMC request execution is a shared lower-level workflow for browser-free Wikidot operations. Since Wikidot status handling determines whether callers should proceed, retry, or raise a mapped exception, only string status codes should flow into Wikidot status-code exceptions. A decoded response with a present but non-string `status` is malformed response data and should be retried before surfacing a compact response-data diagnostic.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established raw AMC request execution as shared infrastructure for `wikidot_token7` handling, site wrapper delegation, request utilities, login/session setup, public source fetches, and many module workflows.
- Existing drafts covered sensitive-log masking, token value preservation, return-exceptions validation, numeric request controls, cookie-name validation, cookie-value validation, explicit request-header value validation, request-body batch validation, and missing response status validation; they did not validate non-string decoded raw AMC response statuses.
- This slice only validates the raw response dictionary's `status` type. It does not change token defaults, token masking, login credentials, session-cookie validation, logout cleanup, retry control validation, URL routing, request-body field semantics, RequestUtil behavior, Site wrapper behavior, module-specific action-status diagnostics, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The validation intentionally does not validate the vocabulary of string `status` values beyond the existing status-handling logic. Unknown string statuses continue to flow through `WikidotStatusCodeException`, and future slices can evaluate status-vocabulary validation separately if rollout evidence supports it.
