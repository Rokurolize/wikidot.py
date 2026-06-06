# PR Draft: Use Merged AMC Request Body In Terminal try_again Diagnostics

## Summary

`AjaxModuleConnectorClient.request(...)` merges caller request bodies with default AMC fields before sending, including the default `wikidot_token7`. Most terminal AMC diagnostics already log a masked view of this merged request body. The terminal `try_again` exhausted-retry branch instead logged the pre-merge body, so diagnostics omitted the token field entirely rather than showing the same masked default token context as other terminal branches.

This change makes terminal `try_again` diagnostics use the same merged masked request-body representation as the other terminal status/error logs. Request construction, outgoing payloads, retry timing, retry count handling, `ok`, `no_permission`, unknown status handling, malformed response validation, token preservation, and existing masking policy are unchanged.

## Outcome

When an AMC response keeps returning `{"status": "try_again"}` until the configured attempt limit is exhausted, the terminal error log now shows the merged request body with structural fields preserved and `wikidot_token7` masked as `***MASKED***`.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who diagnose browser-free AMC workflows, generated request batches, retry failures, page publishing, forum writes, private messages, invitations, and other module operations through raw AMC logs.

## Current Evidence

Local rollout-backed drafts established raw AMC request execution as shared infrastructure for token handling, request batching, retry control, Site wrapper delegation, RequestUtil delegation, browser-free publishing, forum workflows, private messages, invitations, and generated AMC request batches. Recent local AMC hardening covered explicit caller token preservation, request-body batch validation, response-status field/type validation, malformed-response diagnostic redaction, and request-side user-content redaction.

Those prior slices are not duplicates. [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md) preserves caller-supplied token values in outgoing request bodies. [402-pr-validate-amc-response-status.md](402-pr-validate-amc-response-status.md) and [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) validate decoded response status shape. [404-pr-redact-amc-malformed-response-diagnostics.md](404-pr-redact-amc-malformed-response-diagnostics.md) avoids raw malformed response logging. [405-pr-redact-amc-user-content-request-logs.md](405-pr-redact-amc-user-content-request-logs.md) expands request-log redaction policy. None of those made the terminal `try_again` exhausted-retry log use the already-merged request body.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md), [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [401-pr-validate-amc-request-bodies.md](401-pr-validate-amc-request-bodies.md), [402-pr-validate-amc-response-status.md](402-pr-validate-amc-response-status.md), [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md), [404-pr-redact-amc-malformed-response-diagnostics.md](404-pr-redact-amc-malformed-response-diagnostics.md), and [405-pr-redact-amc-user-content-request-logs.md](405-pr-redact-amc-user-content-request-logs.md).

## Changes

- Change the terminal `try_again` exhausted-retry log in `AjaxModuleConnectorClient.request(...)` from the pre-merge request body to the existing merged `request_body`.
- Preserve the same recursive `_mask_sensitive_data(...)` masking used by other terminal request-body diagnostics.
- Reuse the already-validated response `status` value for status classification, avoiding the redundant post-validation `"status" in _response_body` wrapper.
- Add a public raw AMC regression proving terminal `try_again` diagnostics include the default token key while masking its value.

## Type Of Change

- Diagnostic consistency fix
- Raw AMC connector hardening
- Privacy/logging behavior preservation
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Terminal `try_again` exhausted-retry logs must use the merged AMC request body, not the pre-merge caller body. |
| R2 | The diagnostic must preserve structural fields such as `moduleName` while masking `wikidot_token7` through the existing recursive masker. |
| R3 | Retry timing, retry count handling, exception type, exception status, outgoing request payloads, default token insertion, explicit token preservation, and successful retry behavior must remain unchanged. |
| R4 | `ok`, `no_permission`, unknown non-ok status handling, missing-status validation, non-string-status validation, malformed-response diagnostics, and request-body validation must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not expose real tokens, credentials, cookies, auth JSON, private site data, raw rollout paths, live Wikidot state, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, AMC/ajax tests, adjacent tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A terminal `try_again` log at `attempt_limit=1` includes the merged default `wikidot_token7` key instead of only the caller body. | `TestAjaxModuleConnectorClientRequest.test_try_again_max_retry_log_uses_merged_request_body` failed RED because `caplog.text` only contained `{'moduleName': 'Test'}`, then passed GREEN after the diagnostic switched to `request_body`. | A terminal `try_again` log without the default token key rejects this local completion claim. | Raw AMC exhausted-retry diagnostics | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | The same log still includes `moduleName` and masks the token value as `***MASKED***`. | The public regression asserts `moduleName`, `wikidot_token7`, and `***MASKED***` in captured error logs. | Removing structural context or logging an unmasked token rejects this local completion claim. | AMC request-log masking | `tests/unit/test_amc_client.py` |
| R3 | The exhausted-retry path still raises `WikidotStatusCodeException` with `try_again`, and non-terminal retry mechanics remain covered by existing AMC tests. | `uv run pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest -q` passed 67 tests after the change. | Changing retry count, backoff, exception type, exception status, outgoing request body, default token behavior, or explicit token preservation rejects this local completion claim. | Raw AMC retry/status behavior | `tests/unit/test_amc_client.py` |
| R4 | Existing status branches and malformed-response validation remain stable. | `uv run pytest tests/unit/test_amc_client.py tests/unit/test_ajax.py -q` passed 146 tests, and the full unit suite passed 1440 tests. | Regressing `ok`, `no_permission`, unknown status, missing status, non-string status, malformed response, request-body validation, or recursive masking rejects this local completion claim. | Raw AMC request/response classification | `tests/unit/test_amc_client.py`, `tests/unit/test_ajax.py` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic values and mocked HTTP responses only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private site data, or real tokens rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, AMC/ajax and adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `e141515 fix(amc): use merged body in try-again logs`.

- RED tracer: `uv run pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_try_again_max_retry_log_uses_merged_request_body -q` failed before the fix because the captured terminal `try_again` error log was `AMC is respond status: "try_again" -> {'moduleName': 'Test'}` and did not include `wikidot_token7`.
- GREEN tracer: `uv run pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_try_again_max_retry_log_uses_merged_request_body -q` passed 1 test.
- Focused request class: `uv run pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest -q` passed 67 tests.
- Focused AMC/ajax pair: `uv run pytest tests/unit/test_amc_client.py tests/unit/test_ajax.py -q` passed 146 tests.
- Post-format focused AMC/ajax pair: `uv run pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest tests/unit/test_ajax.py -q` passed 100 tests.
- Adjacent wrappers: `uv run pytest tests/unit/test_site.py tests/unit/test_requestutil.py tests/unit/test_auth.py -q` passed 243 tests.
- Full unit: `uv run pytest tests/unit -q` passed 1440 tests after formatting.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 81 files already formatted after applying `uv run ruff format src/wikidot/connector/ajax.py`.
- `uv run mypy src` passed with no issues in 36 source files.
- `git diff --check` passed before the code commit.

Not run successfully: `command -v pyright` exited nonzero because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- Terminal `try_again` exhausted-retry diagnostics show the merged AMC request body.
- The default `wikidot_token7` key appears in the diagnostic and its value is masked.
- Structural fields such as `moduleName` remain visible.
- The exhausted-retry exception remains `WikidotStatusCodeException` with status `try_again`.
- Existing retry mechanics, response status classification, malformed-response validation, request-body validation, outgoing payload construction, and request-log redaction policy remain unchanged.
- The new test uses unit-level code only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Logging the merged request body could expose default fields that were not visible in this one branch before. Mitigation: the value is passed through the existing recursive masker, and the regression asserts `wikidot_token7` is present only with a masked value.
- Risk: Flattening the already-validated status branch could unintentionally change response classification. Mitigation: missing status and non-string status validation still happen before `status = _response_body["status"]`, and the focused AMC request class plus full unit suite remained green.
- Risk: This is a diagnostic consistency fix, not a new retry feature. Mitigation: the acceptance criteria explicitly reject retry timing, attempt-limit, exception, or outgoing-payload changes.

## Dependencies

- Existing `AjaxModuleConnectorClient.request(...)` remains the source of truth for raw Ajax Module Connector request execution.
- Existing request-body merging remains the source of truth for outgoing payloads and default `wikidot_token7` insertion.
- Existing `_mask_sensitive_data(...)` remains the source of truth for request-side diagnostic masking.
- Existing response status validation remains the source of truth for missing and non-string status rejection before status classification.
- Existing Site, RequestUtil, auth, page, forum, and private-message wrappers continue to own higher-level behavior and validation.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-body field-type checks, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered terminal `try_again` request-body diagnostic path.

## Upstream-Safe Motivation

AMC retry failures are easier to diagnose when every terminal branch reports the same masked merged request-body shape. The terminal `try_again` path was the outlier: it logged the caller body before the default token field was merged. Aligning it with the other terminal paths keeps diagnostics consistent without changing request behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established raw AMC request execution as shared infrastructure for token handling, site wrapper delegation, request utilities, source fetches, browser-free publishing, forum workflows, private messages, invitations, retry diagnostics, and generated request batches.
- Existing drafts covered recursive explicit-secret masking, caller token preservation, page lock-secret masking, return-exceptions validation, numeric request controls, request-body batch validation, response-status field validation, response-status type validation, malformed-response diagnostic redaction, and request-side user-content redaction. They did not cover the terminal `try_again` pre-merge request-body diagnostic.
- This slice only changes a terminal diagnostic representation and a redundant branch wrapper after validation. It does not change outgoing request bodies, token defaults, token masking, login credentials, session-cookie validation, logout cleanup, retry control validation, URL routing, RequestUtil behavior, Site wrapper behavior, module-specific action-status diagnostics, module-specific response-body diagnostics, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, real token values, page source text from real sites, and private message contents out of upstream discussion.
