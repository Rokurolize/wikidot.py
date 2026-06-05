# PR Draft: Validate AMC Header Cookie Names

## Summary

`AjaxRequestHeader` stores AMC request cookies and serializes them into the outbound `Cookie` header. Before this change, callers could construct or set a cookie with an empty name, whitespace, `=`, `;`, or line breaks, and that malformed name would remain in header state until `get_header(...)` serialized an ambiguous or invalid Cookie header.

This change validates cookie names at the mutation boundary. `AjaxRequestHeader(cookie=...)`, `set_cookie(...)`, and `delete_cookie(...)` now require a string cookie name that is non-empty and contains no whitespace, `=`, or `;`. Cookie values remain unchanged, including existing integer `wikidot_token7` usage. Default cookies, valid custom cookies, missing-cookie deletion no-op behavior, request-body token defaults, explicit caller token preservation, authentication cookie storage, and request utilities remain unchanged.

## Outcome

Malformed cookie names now fail deterministically before they can enter `AjaxRequestHeader.cookie` or later produce malformed request headers. Valid token and session-cookie workflows keep their existing behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who manage browser-free AMC calls, public source fetches, login/session setup, sandbox scripts, generated clients, or configuration-driven tooling that may construct AMC headers from JSON, YAML, CLI flags, spreadsheets, environment variables, or generated structures.

## Current Evidence

Local rollout-backed drafts already exercise `AjaxRequestHeader` as the shared header state for AMC token and authentication workflows. [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md) established that caller-managed `wikidot_token7` header cookies must be preserved and reflected in request bodies. [340-pr-login-session-cookie-validation.md](340-pr-login-session-cookie-validation.md) established that invalid `WIKIDOT_SESSION_ID` values should not become active client header state. [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md), and [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md) show adjacent AMC request-boundary and sensitive-data concerns.

Those prior slices are not duplicates. Issue 050 preserves cookie token values and request-body token precedence, not cookie names. Issue 340 validates the login session-cookie value returned by Wikidot, not the local header cookie-name mutation boundary. Issues 389 and 392 validate raw AMC flags and numeric controls, not header cookie-name serialization.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md), [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [340-pr-login-session-cookie-validation.md](340-pr-login-session-cookie-validation.md), [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md), and [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md).

## Changes

- Add one `_validate_cookie_name(...)` helper in `src/wikidot/connector/ajax.py`.
- Validate custom cookie names passed to `AjaxRequestHeader(cookie=...)`.
- Validate cookie names passed to `AjaxRequestHeader.set_cookie(...)` before mutating header state.
- Validate cookie names passed to `AjaxRequestHeader.delete_cookie(...)` while preserving no-op deletion for valid missing names.
- Preserve cookie values unchanged, including integer `wikidot_token7`.
- Preserve default header fields, default cookies, valid custom cookies, request-body token handling, authentication login/logout cookie behavior, and RequestUtil header forwarding.

## Type Of Change

- Input validation
- AMC request-header hardening
- Authentication/token boundary clarification
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `AjaxRequestHeader(cookie=...)` must reject invalid cookie names before they enter header state. |
| R2 | `AjaxRequestHeader.set_cookie(...)` must reject invalid cookie names before mutating header state. |
| R3 | `AjaxRequestHeader.delete_cookie(...)` must reject invalid cookie names, while valid missing cookie names remain a no-op. |
| R4 | Cookie names must be strings, non-empty, and contain no whitespace, `=`, or `;`. |
| R5 | Existing valid cookie values, default `wikidot_token7`, explicit caller token preservation, login session-cookie storage, logout cookie deletion, AMC request behavior, and RequestUtil header forwarding must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent AMC/auth/RequestUtil/ajax tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Initial cookies named `""`, `" "`, `"bad name"`, `"bad=name"`, `"bad;name"`, and `"bad\nname"` raise `ValueError("cookie name must be a non-empty string without whitespace, '=' or ';'")`. | `TestAjaxRequestHeader.test_custom_cookie_rejects_invalid_cookie_names` passed GREEN for all six values. | Accepting any malformed initial cookie name, storing it in `header.cookie`, or delaying failure until `get_header(...)` rejects this local completion claim. | AMC request header state | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | `set_cookie(...)` rejects the same malformed names and leaves `header.cookie` unchanged. | `TestAjaxRequestHeader.test_set_cookie_rejects_invalid_cookie_names_without_mutating_header` passed GREEN for all six values. | Mutating `header.cookie`, accepting ambiguous header separators, accepting line breaks, or raising only after serialization rejects this local completion claim. | AMC request header mutation | `tests/unit/test_amc_client.py` |
| R3 | `delete_cookie(...)` rejects malformed names, but `delete_cookie("missing")` remains a no-op. | `TestAjaxRequestHeader.test_delete_cookie_rejects_invalid_cookie_names` and `test_delete_missing_cookie_is_noop` passed GREEN. | Treating valid missing names as errors, accepting malformed names, or altering default cookies rejects this local completion claim. | AMC request header mutation | `tests/unit/test_amc_client.py` |
| R4 | Non-string cookie names raise `TypeError("cookie name must be str")`. | `TestAjaxRequestHeader.test_set_cookie_rejects_non_string_cookie_name` passed GREEN. | Coercing integers or other objects into cookie-name strings rejects this local completion claim. | AMC request header mutation | `tests/unit/test_amc_client.py` |
| R5 | Existing valid adjacent behavior remains stable. | `tests/unit/test_amc_client.py` passed 82 tests; adjacent auth, RequestUtil, and ajax tests passed 126 tests; full unit passed 1408 tests. | Breaking default cookies, valid custom cookies, integer `wikidot_token7`, request-body token defaults, explicit caller token preservation, login session-cookie storage, logout deletion, AMC requests, or RequestUtil header forwarding rejects this local completion claim. | AMC/auth/request utility workflows | affected unit suites |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic cookie names, mocks, and local assertions. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private site data, source text from real sites, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `b545e14 fix(amc): validate cookie names`.

- RED tracer: `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxRequestHeader::test_set_cookie_rejects_invalid_cookie_names_without_mutating_header -q` failed 6 tests before the fix because `set_cookie(...)` accepted every malformed name and did not raise `ValueError`.
- GREEN tracer: `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxRequestHeader -q` passed 21 tests after adding cookie-name validation.
- `uv run --extra test pytest tests/unit/test_amc_client.py -q` passed 82 tests.
- `uv run --extra test pytest tests/unit/test_auth.py tests/unit/test_requestutil.py tests/unit/test_ajax.py -q` passed 126 tests.
- `uv run --extra test pytest tests/unit -q` passed 1408 tests.
- `git diff --check` passed before the code commit.

## Acceptance Criteria

- `AjaxRequestHeader(cookie={name: "value"})` rejects empty, whitespace-containing, `=`, `;`, and newline-containing cookie names with `ValueError` before mutating header state.
- `AjaxRequestHeader().set_cookie(name, "value")` rejects the same malformed names before mutating header state.
- `AjaxRequestHeader().set_cookie(123, "value")` raises `TypeError("cookie name must be str")`.
- `AjaxRequestHeader().delete_cookie(name)` rejects malformed names, while `delete_cookie("missing")` remains a no-op.
- Valid cookie values are preserved unchanged, including integer `wikidot_token7` values.
- Existing default headers, valid custom cookies, request-body token handling, authentication session-cookie behavior, logout cleanup, AMC request behavior, and RequestUtil header forwarding remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting malformed names can expose generated-client or configuration bugs earlier than before. Mitigation: cookie names are header syntax, not arbitrary payload data; early rejection prevents ambiguous header serialization.
- Risk: Rejecting non-string names could surprise callers that relied on implicit coercion. Mitigation: cookie names are protocol field names and should be normalized by the caller before header mutation.
- Risk: This change could be confused with Issue 050. Mitigation: Issue 050 preserves token values and request-body precedence; this slice validates cookie names before values enter header state.
- Risk: This change could be confused with Issue 340. Mitigation: Issue 340 validates the returned `WIKIDOT_SESSION_ID` value; this slice validates local header cookie-name keys.
- Risk: This change could be confused with Issue 392. Mitigation: Issue 392 validates AMC numeric request controls; this slice covers request-header cookie-name serialization.

## Dependencies

- Existing `AjaxRequestHeader.cookie` remains the source of truth for AMC header cookies.
- Existing request-body token logic remains the source of truth for `wikidot_token7` body defaults and explicit caller token preservation.
- Existing authentication login/logout logic remains the source of truth for setting and deleting `WIKIDOT_SESSION_ID`.
- The validation is local to `src/wikidot/connector/ajax.py` and does not alter URL routing, retry policy, response parsing, request body construction, RequestUtil host filtering, or live Wikidot behavior.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-body field-type checks, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered AMC cookie-name path.

## Upstream-Safe Motivation

AMC request headers carry session and anti-CSRF token state. Cookie names containing whitespace, separators, or line breaks cannot be represented unambiguously by the simple `name=value;` serializer and should fail before entering request-header state.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established `AjaxRequestHeader` as the shared state for `wikidot_token7`, `WIKIDOT_SESSION_ID`, login/session setup, public source fetches, and AMC request execution.
- Existing drafts covered sensitive-log masking, token value preservation, login session-cookie value validation, raw AMC flag validation, and raw AMC numeric controls; they did not validate cookie-name keys before header serialization.
- This slice only validates cookie names. It does not change cookie values, token defaults, token masking, login credentials, session-cookie value validation, logout cleanup, retry controls, URL routing, request bodies, response parsing, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The validation intentionally preserves non-string cookie values because the existing AMC token path uses integer `wikidot_token7` values and request serialization already stringifies values.
