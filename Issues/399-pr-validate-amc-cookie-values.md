# PR Draft: Validate AMC Header Cookie Values

## Summary

`AjaxRequestHeader` serializes stored cookie state into the outbound AMC `Cookie` header with a simple `name=value;` join. Issue 398 validated cookie names before they enter header state, but cookie values containing whitespace, `;`, or line breaks could still be accepted and later serialized into ambiguous or invalid headers.

This change validates the string representation of cookie values at the same mutation boundary. `AjaxRequestHeader(cookie=...)` and `set_cookie(...)` now reject values whose serialized form contains whitespace or `;`, while preserving the original value object for valid inputs. Existing integer `wikidot_token7` values, `=` inside opaque values, valid custom cookies, default cookies, missing-cookie deletion, explicit caller token preservation, login session-cookie storage, logout cleanup, AMC request behavior, and RequestUtil header forwarding remain unchanged.

## Outcome

Malformed cookie values now fail deterministically before they can enter `AjaxRequestHeader.cookie` or later produce malformed request headers. Valid token and session-cookie workflows keep their existing behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who manage browser-free AMC calls, public source fetches, login/session setup, sandbox scripts, generated clients, or configuration-driven tooling that may construct AMC headers from JSON, YAML, CLI flags, spreadsheets, environment variables, or generated structures.

## Current Evidence

Local rollout-backed drafts already exercise `AjaxRequestHeader` as shared header state for AMC token and authentication workflows. [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md) established that caller-managed `wikidot_token7` header cookies must be preserved and reflected in request bodies. [340-pr-login-session-cookie-validation.md](340-pr-login-session-cookie-validation.md) established that invalid `WIKIDOT_SESSION_ID` values should not become active client header state. [398-pr-validate-amc-cookie-names.md](398-pr-validate-amc-cookie-names.md) established that malformed cookie names should fail before header serialization.

Those prior slices are not duplicates. Issue 050 preserves token values and request-body token precedence, not value syntax safety. Issue 340 validates blank login session-cookie values returned by Wikidot, not caller-managed generic header cookie values. Issue 398 validates cookie-name keys, not cookie-value serialization.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md), [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [340-pr-login-session-cookie-validation.md](340-pr-login-session-cookie-validation.md), [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md), [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), and [398-pr-validate-amc-cookie-names.md](398-pr-validate-amc-cookie-names.md).

## Changes

- Add one `_validate_cookie_value(...)` helper in `src/wikidot/connector/ajax.py`.
- Validate custom cookie values passed to `AjaxRequestHeader(cookie=...)`.
- Validate cookie values passed to `AjaxRequestHeader.set_cookie(...)` before mutating header state.
- Preserve original valid value objects instead of coercing stored values to strings.
- Preserve integer `wikidot_token7` values and `=` inside valid opaque values.
- Preserve cookie-name validation, default header fields, default cookies, valid custom cookies, request-body token handling, authentication login/logout cookie behavior, and RequestUtil header forwarding.

## Type Of Change

- Input validation
- AMC request-header hardening
- Authentication/token boundary clarification
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `AjaxRequestHeader(cookie=...)` must reject cookie values whose serialized form contains whitespace or `;` before they enter header state. |
| R2 | `AjaxRequestHeader.set_cookie(...)` must reject cookie values whose serialized form contains whitespace or `;` before mutating header state. |
| R3 | Valid cookie values must remain stored unchanged, including integer `wikidot_token7` values and opaque strings containing `=`. |
| R4 | Existing cookie-name validation, default `wikidot_token7`, explicit caller token preservation, login session-cookie storage, logout cookie deletion, AMC request behavior, and RequestUtil header forwarding must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent AMC/auth/RequestUtil/ajax tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Initial cookie values `"bad value"`, `"bad;value"`, `"bad\nvalue"`, and `"bad\tvalue"` raise `ValueError("cookie value must serialize without whitespace or ';'")`. | `TestAjaxRequestHeader.test_custom_cookie_rejects_invalid_cookie_values` passed GREEN for all four values. | Accepting any malformed initial cookie value, storing it in `header.cookie`, or delaying failure until `get_header(...)` rejects this local completion claim. | AMC request header state | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | `set_cookie(...)` rejects the same malformed values and leaves `header.cookie` unchanged. | `TestAjaxRequestHeader.test_set_cookie_rejects_invalid_cookie_values_without_mutating_header` passed GREEN for all four values. | Mutating `header.cookie`, accepting ambiguous cookie separators, accepting line breaks, or raising only after serialization rejects this local completion claim. | AMC request header mutation | `tests/unit/test_amc_client.py` |
| R3 | Valid integer and `=`-containing values remain accepted and stored unchanged. | `TestAjaxRequestHeader.test_set_cookie_preserves_integer_and_equals_values` passed GREEN and asserts `987654` remains an integer value while `session=abc=def` serializes correctly. | String-coercing stored integer tokens, rejecting `=` in values, or changing header token serialization rejects this local completion claim. | AMC token/header state | `tests/unit/test_amc_client.py` |
| R4 | Existing valid adjacent behavior remains stable. | `tests/unit/test_amc_client.py` passed 91 tests; adjacent auth, RequestUtil, and ajax tests passed 126 tests; full unit passed 1417 tests. | Breaking cookie-name validation, default cookies, valid custom cookies, integer `wikidot_token7`, request-body token defaults, explicit caller token preservation, login session-cookie storage, logout deletion, AMC requests, or RequestUtil header forwarding rejects this local completion claim. | AMC/auth/request utility workflows | affected unit suites |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic cookie values, mocks, and local assertions. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private site data, source text from real sites, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `37189c5 fix(amc): validate cookie values`.

- RED tracer: `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxRequestHeader::test_set_cookie_rejects_invalid_cookie_values_without_mutating_header -q` failed 4 tests before the fix because `set_cookie(...)` accepted every malformed value and did not raise `ValueError`.
- GREEN tracer: `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxRequestHeader -q` passed 30 tests after adding cookie-value validation.
- `uv run --extra test pytest tests/unit/test_amc_client.py -q` passed 91 tests.
- `uv run --extra test pytest tests/unit/test_auth.py tests/unit/test_requestutil.py tests/unit/test_ajax.py -q` passed 126 tests.
- `uv run --extra test pytest tests/unit -q` passed 1417 tests.
- `uv run --extra test ruff check src tests` passed.
- `uv run --extra test ruff format --check src tests` passed with 81 files already formatted.
- `uv run --extra test mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed before the code commit.

Not run successfully: `pyright src tests` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `AjaxRequestHeader(cookie={"session": value})` rejects whitespace, `;`, and newline/tab-containing values with `ValueError` before mutating header state.
- `AjaxRequestHeader().set_cookie("session", value)` rejects the same malformed values before mutating header state.
- `AjaxRequestHeader().set_cookie("wikidot_token7", 987654)` preserves the integer token value and serializes it as `wikidot_token7=987654`.
- `AjaxRequestHeader().set_cookie("session", "abc=def")` accepts `=` inside the opaque value and serializes it as `session=abc=def`.
- Existing cookie-name validation, default headers, valid custom cookies, request-body token handling, authentication session-cookie behavior, logout cleanup, AMC request behavior, and RequestUtil header forwarding remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting whitespace or semicolon values can expose generated-client or configuration bugs earlier than before. Mitigation: `AjaxRequestHeader` uses an unquoted `name=value;` serializer, so those characters cannot be represented unambiguously without changing serialization strategy.
- Risk: Rejecting whitespace could surprise callers that attempted to pass already-rendered cookie fragments. Mitigation: callers should pass individual cookie values, not serialized header fragments.
- Risk: Rejecting semicolons could affect callers using multi-cookie fragments as a single value. Mitigation: multi-cookie state should be represented as separate `set_cookie(...)` calls so request-body token defaults and sensitive-key masking remain predictable.
- Risk: This change could be confused with Issue 398. Mitigation: Issue 398 validates cookie-name keys; this slice validates cookie-value serialization only.
- Risk: This change could be confused with Issue 340. Mitigation: Issue 340 validates blank `WIKIDOT_SESSION_ID` values returned by login; this slice validates generic caller-managed header cookie values while preserving the auth-specific blank-cookie check.

## Dependencies

- Existing `AjaxRequestHeader.cookie` remains the source of truth for AMC header cookies.
- Existing request-body token logic remains the source of truth for `wikidot_token7` body defaults and explicit caller token preservation.
- Existing authentication login/logout logic remains the source of truth for setting and deleting `WIKIDOT_SESSION_ID`.
- The validation is local to `src/wikidot/connector/ajax.py` and does not alter URL routing, retry policy, response parsing, request body construction, RequestUtil host filtering, or live Wikidot behavior.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-body field-type checks, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered AMC cookie-value path.

## Upstream-Safe Motivation

AMC request headers carry session and anti-CSRF token state. Since `AjaxRequestHeader` serializes cookies with a simple unquoted `name=value;` join, values containing whitespace, semicolon separators, or line breaks should fail before entering request-header state.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established `AjaxRequestHeader` as the shared state for `wikidot_token7`, `WIKIDOT_SESSION_ID`, login/session setup, public source fetches, and AMC request execution.
- Existing drafts covered sensitive-log masking, token value preservation, login session-cookie value validation, raw AMC flag validation, raw AMC numeric controls, and cookie-name validation; they did not validate cookie values before header serialization.
- This slice only validates cookie-value serialization safety. It does not change cookie names, token defaults, token masking, login credentials, session-cookie value validation, logout cleanup, retry controls, URL routing, request bodies, response parsing, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The validation intentionally checks `str(value)` but stores the original value object. This preserves existing integer token behavior while preventing values whose serialized representation would break the simple Cookie header format.
