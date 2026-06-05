# PR Draft: Validate AMC Request Header Values

## Summary

`AjaxRequestHeader` owns the non-cookie AMC request-header fields `Content-Type`, `User-Agent`, and `Referer` as well as cookie state. Issues 398 and 399 hardened cookie names and values before they can be serialized into the outbound `Cookie` header, but explicit non-cookie header values still entered header state without validation.

This change validates caller-supplied `content_type`, `user_agent`, and `referer` values at construction time. Explicit values must be strings and must not contain `\r` or `\n`. Valid header values that naturally contain spaces or semicolons, such as `text/plain; charset=UTF-8` and `Custom Agent/1.0`, remain accepted. Default header values, cookie-name validation, cookie-value validation, default cookies, request-body token handling, authentication login/logout cookie behavior, AMC request behavior, and RequestUtil header forwarding remain unchanged.

## Outcome

Malformed non-cookie header values now fail deterministically before they can enter `AjaxRequestHeader` state or later be handed to the HTTP client. Valid custom header values keep their existing behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who construct AMC clients from generated code, JSON/YAML config, CLI flags, spreadsheets, environment variables, sandbox tooling, or other external input before making browser-free Wikidot requests.

## Current Evidence

Local rollout-backed drafts already exercise `AjaxRequestHeader` as shared header state for AMC token and authentication workflows. [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md) established that caller-managed `wikidot_token7` header cookies must be preserved and reflected in request bodies. [340-pr-login-session-cookie-validation.md](340-pr-login-session-cookie-validation.md) established that invalid `WIKIDOT_SESSION_ID` values should not become active client header state. [398-pr-validate-amc-cookie-names.md](398-pr-validate-amc-cookie-names.md) established that malformed cookie names should fail before header serialization. [399-pr-validate-amc-cookie-values.md](399-pr-validate-amc-cookie-values.md) established that malformed cookie values should fail before header serialization.

Those prior slices are not duplicates. Issue 050 preserves token values and request-body token precedence. Issue 340 validates a login-returned session-cookie value. Issue 398 validates cookie-name keys. Issue 399 validates cookie-value serialization. This slice validates the explicit non-cookie header fields that `AjaxRequestHeader.get_header()` returns as `Content-Type`, `User-Agent`, and `Referer`.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md), [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [340-pr-login-session-cookie-validation.md](340-pr-login-session-cookie-validation.md), [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md), [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), [398-pr-validate-amc-cookie-names.md](398-pr-validate-amc-cookie-names.md), and [399-pr-validate-amc-cookie-values.md](399-pr-validate-amc-cookie-values.md).

## Changes

- Add one `_validate_header_value(...)` helper in `src/wikidot/connector/ajax.py`.
- Validate explicit `content_type`, `user_agent`, and `referer` constructor values before storing them.
- Reject non-string explicit header values with `TypeError("<field> must be str")`.
- Reject CR/LF-containing explicit header values with `ValueError("<field> must not contain line breaks")`.
- Preserve valid spaces and semicolons in normal header fields.
- Preserve cookie-name validation, cookie-value validation, default headers, default cookies, token handling, authentication cookie behavior, AMC request behavior, and RequestUtil header forwarding.

## Type Of Change

- Input validation
- AMC request-header hardening
- Constructor boundary clarification
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Explicit `content_type`, `user_agent`, and `referer` values must reject `\r` and `\n` before they enter `AjaxRequestHeader` state. |
| R2 | Explicit `content_type`, `user_agent`, and `referer` values must reject non-string inputs before they enter `AjaxRequestHeader` state. |
| R3 | Valid custom header values must remain accepted, including spaces in `User-Agent` and semicolons in `Content-Type`. |
| R4 | Existing cookie-name validation, cookie-value validation, default `wikidot_token7`, explicit caller token preservation, login session-cookie storage, logout cookie deletion, AMC request behavior, and RequestUtil header forwarding must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent AMC/auth/RequestUtil/ajax tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `AjaxRequestHeader(content_type=value)`, `AjaxRequestHeader(user_agent=value)`, and `AjaxRequestHeader(referer=value)` reject `"bad\nvalue"` and `"bad\rvalue"` with `ValueError("<field> must not contain line breaks")`. | `TestAjaxRequestHeader.test_custom_header_values_reject_line_breaks` passed GREEN for all six field/value combinations. | Accepting CR/LF values, storing them in header state, or delaying failure until `get_header(...)` or HTTP send time rejects this local completion claim. | AMC request header state | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | The same three explicit fields reject non-string values with `TypeError("<field> must be str")`. | `TestAjaxRequestHeader.test_custom_header_values_reject_non_strings` passed GREEN for all three fields. | Coercing integers or other objects into non-cookie header strings rejects this local completion claim. | AMC request header state | `tests/unit/test_amc_client.py` |
| R3 | Valid values with ordinary header syntax remain accepted. | `TestAjaxRequestHeader.test_custom_values` passed with `content_type="text/plain; charset=UTF-8"` and `user_agent="Custom Agent/1.0"`. | Rejecting spaces in `User-Agent`, rejecting `;` in `Content-Type`, changing stored valid values, or URL-validating `referer` beyond the requested boundary rejects this local completion claim. | AMC request header state | `tests/unit/test_amc_client.py` |
| R4 | Existing valid adjacent behavior remains stable. | `tests/unit/test_amc_client.py` passed 100 tests; adjacent auth, RequestUtil, and ajax tests passed 126 tests; full unit passed 1426 tests. | Breaking cookie-name validation, cookie-value validation, default cookies, valid custom cookies, integer `wikidot_token7`, request-body token defaults, explicit caller token preservation, login session-cookie storage, logout deletion, AMC requests, or RequestUtil header forwarding rejects this local completion claim. | AMC/auth/request utility workflows | affected unit suites |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic header values, mocks, and local assertions. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private site data, source text from real sites, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `eb9de8f fix(amc): validate request header values`.

- RED tracer: `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxRequestHeader::test_custom_header_values_reject_line_breaks -q` failed 6 tests before the fix because explicit header fields accepted CR/LF values and did not raise `ValueError`.
- GREEN tracer: `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxRequestHeader::test_custom_header_values_reject_line_breaks -q` passed 6 tests after adding header-value validation.
- `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxRequestHeader::test_custom_header_values_reject_non_strings -q` passed 3 tests.
- `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxRequestHeader -q` passed 39 tests.
- `uv run --extra test pytest tests/unit/test_amc_client.py -q` passed 100 tests.
- `uv run --extra test pytest tests/unit/test_auth.py tests/unit/test_requestutil.py tests/unit/test_ajax.py -q` passed 126 tests.
- `uv run --extra test pytest tests/unit -q` passed 1426 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 81 files already formatted after running formatter once on `src/wikidot/connector/ajax.py`.
- `uv run mypy src` passed with no issues in 36 source files.
- `git diff --check` passed before the code commit.

Not run successfully: `pyright --version` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `AjaxRequestHeader(content_type="bad\nvalue")`, `AjaxRequestHeader(user_agent="bad\nvalue")`, and `AjaxRequestHeader(referer="bad\nvalue")` reject the values with `ValueError` before header state is created.
- The same fields reject `\r` line breaks with `ValueError` before header state is created.
- The same fields reject non-string explicit values with `TypeError`.
- `AjaxRequestHeader(content_type="text/plain; charset=UTF-8", user_agent="Custom Agent/1.0", referer="https://example.com/")` remains accepted and stores those exact values.
- Existing cookie-name validation, cookie-value validation, default headers, valid custom cookies, request-body token handling, authentication session-cookie behavior, logout cleanup, AMC request behavior, and RequestUtil header forwarding remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting CR/LF values can expose generated-client or configuration bugs earlier than before. Mitigation: explicit header values containing line breaks cannot be represented as safe single header-field values, so early failure is clearer than delayed HTTP-client failure.
- Risk: Over-validating could reject legitimate user agents or content types. Mitigation: this slice intentionally permits spaces and semicolons and does not parse or normalize field-specific syntax.
- Risk: `referer` could be interpreted as a URL-validation target. Mitigation: this slice only validates the shared header-field value boundary and does not enforce URL grammar, scheme policy, or host policy.
- Risk: This change could be confused with Issue 398 or 399. Mitigation: Issues 398 and 399 validate the serialized `Cookie` header components; this slice validates the separate `Content-Type`, `User-Agent`, and `Referer` values.
- Risk: This change could be confused with RequestUtil host filtering. Mitigation: no request URL, site name, redirect, host validation, retry, or RequestUtil behavior changes in this slice.

## Dependencies

- Existing `AjaxRequestHeader` remains the source of truth for AMC request headers.
- Existing `AjaxRequestHeader.cookie` remains the source of truth for AMC header cookies.
- Existing request-body token logic remains the source of truth for `wikidot_token7` body defaults and explicit caller token preservation.
- Existing authentication login/logout logic remains the source of truth for setting and deleting `WIKIDOT_SESSION_ID`.
- The validation is local to `src/wikidot/connector/ajax.py` and does not alter URL routing, retry policy, response parsing, request body construction, RequestUtil host filtering, or live Wikidot behavior.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-body field-type checks, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered AMC header-value path.

## Upstream-Safe Motivation

AMC request headers carry session and request-context state. Since `AjaxRequestHeader` stores explicit `Content-Type`, `User-Agent`, and `Referer` values and returns them directly from `get_header()`, CR/LF-containing values should fail before entering header state. The fix is intentionally narrow: it rejects line breaks and non-string explicit values while preserving valid spaces, semicolons, defaults, cookies, token behavior, and existing request flows.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established `AjaxRequestHeader` as the shared state for `wikidot_token7`, `WIKIDOT_SESSION_ID`, login/session setup, public source fetches, and AMC request execution.
- Existing drafts covered sensitive-log masking, token value preservation, login session-cookie value validation, raw AMC flag validation, raw AMC numeric controls, cookie-name validation, and cookie-value validation; they did not validate explicit non-cookie request-header values before header construction.
- This slice only validates `content_type`, `user_agent`, and `referer` constructor values. It does not change cookie names, cookie values, token defaults, token masking, login credentials, session-cookie value validation, logout cleanup, retry controls, URL routing, request bodies, response parsing, RequestUtil behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The validation intentionally avoids field-specific parsing. A future upstream discussion can decide whether `referer` should receive URL grammar validation, but that would be a separate behavior change from preventing malformed header-field values.
