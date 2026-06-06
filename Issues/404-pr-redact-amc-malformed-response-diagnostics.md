# PR Draft: Redact AMC Malformed Response Diagnostics

## Summary

`AjaxModuleConnectorClient.request(...)` already masks sensitive request-body fields in terminal AMC logs, but two malformed response terminal paths still embedded raw response data. Repeated non-JSON responses raised `ResponseDataException` with `response.text`, and repeated non-dictionary JSON responses raised `ResponseDataException` with the decoded payload `repr`. The same raw values also appeared in error logs.

This change keeps the existing retry behavior for non-JSON and non-dictionary JSON responses, but makes the final diagnostics compact. Non-JSON terminal failures now raise `ResponseDataException("AMC responded with non-JSON data")`. Non-dictionary JSON terminal failures now raise `ResponseDataException("AMC responded with invalid JSON data type: <type>")`. Existing successful responses, transient malformed response retrying, empty-dictionary handling, missing `status`, non-string `status`, `try_again`, `no_permission`, other string non-`ok` statuses, request construction, token handling, header validation, numeric controls, request-body validation, and higher-level module-specific diagnostics remain unchanged.

## Outcome

Malformed raw AMC responses no longer force operators to retain page source, private generated HTML, or arbitrary decoded JSON payloads in exception text or error logs to triage a connector failure. The diagnostics still identify the response class and, for decoded non-dictionary JSON, the observed top-level type.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call `AjaxModuleConnectorClient.request(...)` directly or rely on raw AMC request processing through local migration tooling, sandbox probes, archival jobs, moderation utilities, source fetches, or generated request batches.

## Current Evidence

Local rollout-backed drafts establish raw AMC request execution as a shared lower-level surface. [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md), [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md), and [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md) covered request-side secret handling. [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md), [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), [398-pr-validate-amc-cookie-names.md](398-pr-validate-amc-cookie-names.md), [399-pr-validate-amc-cookie-values.md](399-pr-validate-amc-cookie-values.md), [400-pr-validate-amc-header-values.md](400-pr-validate-amc-header-values.md), [401-pr-validate-amc-request-bodies.md](401-pr-validate-amc-request-bodies.md), [402-pr-validate-amc-response-status.md](402-pr-validate-amc-response-status.md), and [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) covered adjacent raw AMC input and response-shape validation.

Those prior slices are not duplicates. They either mask request-side data, validate request controls, or validate decoded response `status` shape. They did not remove raw response text from the non-JSON terminal path or raw decoded payload `repr` from the non-dictionary JSON terminal path.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md), [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md), [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), [401-pr-validate-amc-request-bodies.md](401-pr-validate-amc-request-bodies.md), [402-pr-validate-amc-response-status.md](402-pr-validate-amc-response-status.md), and [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md).

## Changes

- Remove raw `response.text` from terminal non-JSON AMC exceptions and error logs.
- Remove raw decoded non-dictionary JSON payload `repr` from terminal invalid JSON exceptions and error logs.
- Preserve a compact observed top-level type for decoded non-dictionary JSON responses.
- Keep existing retry/backoff behavior and masked request-body logging.
- Add public-interface tests proving synthetic private response content does not appear in terminal exceptions or captured error logs.

## Type Of Change

- Response diagnostic hardening
- Privacy/logging improvement
- Raw AMC connector hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Repeated non-JSON AMC responses must keep retrying until `attempt_limit` and then raise a compact `ResponseDataException` that does not include raw `response.text`. |
| R2 | Repeated decoded non-dictionary JSON AMC responses must keep retrying until `attempt_limit` and then raise a compact `ResponseDataException` that does not include raw decoded payload content. |
| R3 | Terminal error logs for R1 and R2 must not include raw response text or raw decoded payload content. |
| R4 | Existing valid and adjacent malformed raw AMC behavior must remain unchanged, including successful `status: ok`, `try_again`, `no_permission`, other string non-`ok` statuses, empty dictionaries, missing `status`, non-string `status`, request construction, token defaults, explicit token preservation, site override validation, return-exceptions behavior, numeric controls, request-header validation, and request-body batch validation. |
| R5 | Diagnostics, docs, and tests must not expose raw response bodies, private payloads, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent AMC/ajax/site/RequestUtil/auth tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Repeated text response `PRIVATE_AMC_BODY_SHOULD_NOT_LEAK` raises a `ResponseDataException` whose string omits that value. | `TestAjaxModuleConnectorClientRequest.test_non_json_response_max_retry_does_not_expose_body` failed RED because the old exception embedded the raw text, then passed GREEN after the diagnostic redaction. | Including `response.text`, page source, generated HTML, credentials, private site content, or local rollout paths rejects this local completion claim. | Raw AMC non-JSON terminal path | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | Repeated list-valued JSON response `["PRIVATE_AMC_JSON_PAYLOAD_SHOULD_NOT_LEAK"]` raises a `ResponseDataException` whose string omits that value while preserving `actual=list`-equivalent type context as `type: list`. | `TestAjaxModuleConnectorClientRequest.test_non_dict_json_response_max_retry_does_not_expose_payload` failed RED because the old exception embedded the decoded list `repr`, then passed GREEN after the diagnostic redaction. | Including raw decoded JSON, generated HTML, credentials, private content, or local rollout paths rejects this local completion claim. | Raw AMC non-dict JSON terminal path | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R3 | Captured terminal error logs for R1 and R2 omit the synthetic private sentinels. | Both focused tests assert the sentinel is absent from `caplog.text`. | Logging raw response text, raw decoded JSON, credentials, cookies, private site content, or raw local paths rejects this local completion claim. | AMC error logging | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R4 | Existing adjacent behavior remains stable. | `TestAjaxModuleConnectorClientRequest` passed 65 tests; `tests/unit/test_amc_client.py tests/unit/test_ajax.py` passed 143 tests; `tests/unit/test_site.py tests/unit/test_requestutil.py tests/unit/test_auth.py` passed 243 tests; full unit passed 1437 tests. | Regressing successful raw AMC responses, malformed response retrying, `try_again`, `no_permission`, string non-`ok` mapping, empty-response retrying, missing-status handling, non-string status handling, request bodies, headers, numeric controls, Site wrapper behavior, RequestUtil, or Auth rejects this local completion claim. | AMC/request utility workflows | affected unit suites |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic mocked responses and local assertions over exception/log text. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private site data, source text from real sites, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `b79d6ed fix(amc): redact malformed response diagnostics`.

- RED focused pair: `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_non_json_response_max_retry_does_not_expose_body tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_non_dict_json_response_max_retry_does_not_expose_payload -q` failed before the fix because both `ResponseDataException` strings and captured `wikidot` error logs included the synthetic private response values.
- GREEN focused pair: `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_non_json_response_max_retry_does_not_expose_body tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_non_dict_json_response_max_retry_does_not_expose_payload -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest -q` passed 65 tests.
- `uv run --extra test pytest tests/unit/test_amc_client.py tests/unit/test_ajax.py -q` passed 143 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_requestutil.py tests/unit/test_auth.py -q` passed 243 tests.
- `uv run --extra test pytest tests/unit -q` passed 1437 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 81 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files.
- `git diff --check` passed before the code commit.

Not run successfully: `pyright --version` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- Non-JSON AMC response retry exhaustion raises a compact `ResponseDataException` without raw response text.
- Non-dictionary JSON AMC response retry exhaustion raises a compact `ResponseDataException` without raw decoded payload content.
- Terminal error logs for those response classes do not include raw response text or raw decoded payload content.
- Successful `status: ok`, retrying `status: try_again`, forbidden `status: no_permission`, other string non-`ok` statuses, missing `status`, non-string `status`, empty dictionaries, and transient malformed response retrying keep their existing behavior.
- Valid request bodies, empty request batches, explicit request-body `wikidot_token7`, header-cookie token defaults, site override validation, return-exceptions behavior, numeric-control validation, cookie validation, header-value validation, request-body batch validation, Site wrapper delegation, RequestUtil, and auth behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Removing raw response content could reduce immediate debugging detail. Mitigation: the connector still reports the response class, preserves the decoded top-level type for non-dictionary JSON, and logs the masked request body for routing without retaining private content.
- Risk: The lower-level redaction could be confused with module-specific body diagnostics. Mitigation: higher-level modules still own contextual `body` and parser diagnostics after valid raw AMC responses; this slice applies only to raw connector malformed-response terminal paths.
- Risk: Retry behavior could hide a persistent malformed response until the attempt limit. Mitigation: this preserves the existing retry pattern and only changes terminal diagnostic content.

## Dependencies

- Existing `AjaxModuleConnectorClient.request(...)` remains the source of truth for raw Ajax Module Connector request execution.
- Existing `_calculate_backoff(...)` and validated `AjaxModuleConnectorConfig` values remain the source of truth for raw AMC retry timing.
- Existing `_mask_sensitive_data(...)` remains the source of truth for request-side log masking.
- Existing status-handling branches continue to own successful, retry, forbidden, and other string status behavior.
- The diagnostic change is local to `src/wikidot/connector/ajax.py` and does not alter URL routing, request body field semantics, retry control validation, RequestUtil host filtering, module-specific action-status validators, module-specific response-body validators, or live Wikidot behavior.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-body field-type checks, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered raw AMC malformed-response diagnostic path.

## Upstream-Safe Motivation

Raw AMC request execution is shared by many browser-free Wikidot workflows. When Wikidot or an intermediary returns malformed response data, operators need to know the response class without storing private page source, generated module HTML, or arbitrary decoded JSON payloads in exception text and logs. Compact terminal diagnostics keep the existing strict failure behavior while reducing accidental data retention.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established raw AMC request execution as shared infrastructure for `wikidot_token7` handling, site wrapper delegation, request utilities, login/session setup, public source fetches, and many module workflows.
- Existing drafts covered sensitive request-body masking, token value preservation, return-exceptions validation, numeric request controls, cookie-name validation, cookie-value validation, explicit request-header value validation, request-body batch validation, missing response status validation, and response status type validation. They did not redact terminal malformed response content from the raw connector's non-JSON and non-dictionary JSON paths.
- This slice only changes terminal diagnostics for two malformed response classes. It does not change token defaults, token masking, login credentials, session-cookie validation, logout cleanup, retry control validation, URL routing, request-body field semantics, RequestUtil behavior, Site wrapper behavior, module-specific action-status diagnostics, module-specific response-body diagnostics, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The decoded non-dictionary JSON terminal path intentionally reports only the top-level Python type name. Future slices can evaluate structured length diagnostics separately if rollout evidence shows type alone is insufficient.
