# PR Draft: Validate AMC Header Serialization State

## Summary

`AjaxRequestHeader` validates explicit constructor and setter inputs, but its public attributes remain mutable. A caller or fixture could directly assign malformed `content_type`, `user_agent`, `referer`, or `cookie` state after construction, and `get_header(...)` would serialize that corrupted state into the outbound HTTP headers. Malformed scalar headers with line breaks or non-string values were returned unchanged, malformed cookie names and values were serialized into ambiguous `Cookie` text, and non-dictionary `cookie` state failed with incidental `.items()` `AttributeError`.

This change revalidates header state at serialization time. `get_header(...)` now rejects malformed scalar header values, malformed cookie containers, malformed cookie names, and malformed cookie values before returning the header dictionary. Valid default headers, valid custom headers, valid cookie dictionaries, integer `wikidot_token7` values, opaque values containing `=`, login/logout cookie state, raw AMC request behavior, and RequestUtil forwarding remain unchanged.

## Outcome

Directly mutated AMC header state now fails deterministically at `get_header(...)` instead of producing malformed HTTP headers or lower-level Python attribute errors.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free clients, login/session setup, raw AMC requests, direct URL batches, generated fixtures, mocked clients, JSON/YAML adapters, or local test utilities that may inspect or mutate `AjaxRequestHeader` objects.

## Current Evidence

Header/request-state drafts [398-pr-validate-amc-cookie-names.md](398-pr-validate-amc-cookie-names.md), [399-pr-validate-amc-cookie-values.md](399-pr-validate-amc-cookie-values.md), [400-pr-validate-amc-header-values.md](400-pr-validate-amc-header-values.md), and [516-pr-validate-amc-cookie-container.md](516-pr-validate-amc-cookie-container.md) establish `AjaxRequestHeader` as a practical safety boundary. They validate initial and setter inputs before unsafe state is stored, but they do not protect the final serialization boundary after public attributes or the public cookie dictionary are mutated directly.

Those prior slices are not duplicates. Issues 398 and 399 validate cookie keys and values when callers use the constructor or `set_cookie(...)`. Issue 400 validates explicit scalar header constructor inputs. Issue 516 validates the initial `cookie` container. This slice validates the state that `get_header(...)` is about to serialize, which also covers direct test/fixture/config mutation that bypasses those earlier boundaries.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `content_type`, `user_agent`, and `referer` in `AjaxRequestHeader.get_header(...)`.
- Reject non-dictionary `self.cookie` state with `ValueError("cookie must be a dictionary")` before `.items()` is used.
- Revalidate every cookie name and value while serializing the `Cookie` header.
- Preserve default header behavior and valid serialized cookie output.
- Add focused tests for directly mutated scalar header fields, cookie containers, cookie names, and cookie values.

## Type Of Change

- Input/state validation
- AMC request-header serialization hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `get_header(...)` must reject directly mutated scalar header values with the same diagnostics as constructor validation. |
| R2 | `get_header(...)` must reject directly mutated non-dictionary `cookie` state with `ValueError("cookie must be a dictionary")` instead of `.items()` errors. |
| R3 | `get_header(...)` must reject directly mutated malformed cookie names before serializing the `Cookie` header. |
| R4 | `get_header(...)` must reject directly mutated malformed cookie values before serializing the `Cookie` header. |
| R5 | Existing valid default/custom header behavior, valid cookie serialization, integer token support, and `=` inside opaque values must remain unchanged. |
| R6 | Existing raw AMC, client, auth, RequestUtil, and site workflows must remain green. |
| R7 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, AMC tests, adjacent tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Mutated `content_type`, `user_agent`, or `referer` values containing `\n`/`\r` raise `ValueError("<field> must not contain line breaks")`, and non-string values raise `TypeError("<field> must be str")`. | `test_get_header_rejects_mutated_header_line_breaks` and `test_get_header_rejects_mutated_non_string_header_values` failed RED with `DID NOT RAISE`, then passed GREEN. | Returning malformed scalar headers, accepting non-strings, or producing HTTPX-level header errors rejects this local completion claim. | Header serialization | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | Mutated `cookie=None`, list, string, boolean, or arbitrary object state raises `ValueError("cookie must be a dictionary")`. | `test_get_header_rejects_mutated_non_dict_cookie_state` failed RED with `.items()` `AttributeError`, then passed GREEN. | Calling `.items()` on a non-dict, silently treating non-dicts as empty cookies, or serializing arbitrary objects rejects this local completion claim. | Cookie serialization | `tests/unit/test_amc_client.py` |
| R3 | Mutated cookie names that are empty, contain whitespace, `=`, `;`, line breaks, or are non-strings fail before serialization. | `test_get_header_rejects_mutated_cookie_names` and `test_get_header_rejects_mutated_non_string_cookie_name` failed RED with `DID NOT RAISE`, then passed GREEN. | Returning `Cookie` text with malformed names or coercing non-string keys rejects this local completion claim. | Cookie serialization | `tests/unit/test_amc_client.py` |
| R4 | Mutated cookie values containing whitespace, `;`, line breaks, or tabs fail before serialization. | `test_get_header_rejects_mutated_cookie_values` failed RED with `DID NOT RAISE`, then passed GREEN. | Returning ambiguous `Cookie` text with malformed values rejects this local completion claim. | Cookie serialization | `tests/unit/test_amc_client.py` |
| R5 | Valid header serialization remains stable. | Existing `TestAjaxRequestHeader` default/custom/get-header/token tests passed inside the 194-test AMC suite. | Changing default headers, dropping `wikidot_token7`, coercing stored integer token state, or rejecting `=` in valid cookie values rejects this local completion claim. | Valid header behavior | `tests/unit/test_amc_client.py` |
| R6 | Existing adjacent workflows remain green. | Adjacent AMC/client/auth/RequestUtil/site suites passed 585 tests, and full unit passed 2430 tests. | Regressing raw AMC request execution, auth login/logout cookie state, RequestUtil forwarding, client construction, or site workflows rejects this local completion claim. | AMC and adjacent workflows | `tests/unit` |
| R7 | No private material or live action is needed to prove the behavior. | All regressions use synthetic mutated values and local unit tests; the draft contains no raw credentials, cookies, auth JSON, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `bfee861 fix(amc): validate header serialization state`.

- RED serialization-state tests: `uv run pytest tests/unit/test_amc_client.py::TestAjaxRequestHeader::test_get_header_rejects_mutated_header_line_breaks tests/unit/test_amc_client.py::TestAjaxRequestHeader::test_get_header_rejects_mutated_non_string_header_values tests/unit/test_amc_client.py::TestAjaxRequestHeader::test_get_header_rejects_mutated_non_dict_cookie_state tests/unit/test_amc_client.py::TestAjaxRequestHeader::test_get_header_rejects_mutated_cookie_names tests/unit/test_amc_client.py::TestAjaxRequestHeader::test_get_header_rejects_mutated_non_string_cookie_name tests/unit/test_amc_client.py::TestAjaxRequestHeader::test_get_header_rejects_mutated_cookie_values -q` failed 25 cases before the fix: 20 with `DID NOT RAISE` and 5 non-dict cookie states with `.items()` `AttributeError`.
- GREEN focused tests: the same focused command passed 25 tests after serialization preflight was added.
- `uv run ruff format src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` reformatted 1 file and left 1 file unchanged.
- `uv run pytest tests/unit/test_amc_client.py -q` passed 194 tests.
- `uv run ruff check src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed.
- `uv run ruff format --check src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit/test_amc_client.py tests/unit/test_client.py tests/unit/test_auth.py tests/unit/test_requestutil.py tests/unit/test_site.py -q` passed 585 tests.
- `uv run pytest tests/unit -q` passed 2430 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Directly assigning `header.content_type`, `header.user_agent`, or `header.referer` to values containing `\n` or `\r` causes `get_header(...)` to raise `ValueError("<field> must not contain line breaks")`.
- Directly assigning those scalar header fields to non-string values causes `get_header(...)` to raise `TypeError("<field> must be str")`.
- Directly assigning `header.cookie` to `None`, a list, a string, a boolean, or an arbitrary object causes `get_header(...)` to raise `ValueError("cookie must be a dictionary")`.
- Directly adding malformed cookie names or values to `header.cookie` causes `get_header(...)` to raise the same cookie-name or cookie-value diagnostics as constructor/setter validation.
- Valid `get_header(...)` output remains unchanged for default headers, valid custom headers, valid custom cookies, integer `wikidot_token7` values, and values containing `=`.
- Existing raw AMC, auth, client, RequestUtil, and site tests remain green.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This adds validation to `get_header(...)` even though earlier fixes validate normal mutation APIs. Mitigation: `AjaxRequestHeader` exposes mutable public attributes and a mutable dictionary, so serialization is the last reliable boundary before HTTP request setup.
- Risk: Rejecting mutated state may expose tests or generated fixtures that were directly modifying header internals. Mitigation: those fixtures should use `set_cookie(...)` or assign valid scalar strings; malformed header state cannot be sent safely.
- Risk: This could be confused with Issues 398, 399, 400, or 516. Mitigation: those slices validate constructor/setter inputs; this slice validates the final serialized state after direct mutation.
- Risk: Revalidating values during serialization could be seen as duplicated work. Mitigation: the cost is negligible compared with HTTP request setup and protects a public mutable object from unsafe state.

## Out Of Scope

Making `AjaxRequestHeader` immutable, replacing the public `cookie` dictionary with a private mapping, changing cookie serialization strategy, accepting quoted cookie values, altering token defaults, changing auth login/logout behavior, changing retry behavior, changing RequestUtil forwarding, live Wikidot behavior, and upstream Issue/PR creation are outside this slice.

## Why This Matters

`get_header(...)` is the final boundary before header state is handed to the HTTP client. Revalidating mutable public state there keeps generated fixtures, mocked clients, and direct local automation from turning invalid in-memory state into malformed request headers.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used browser-free AMC clients, login/session setup, token forwarding, generated fixtures, and direct request utilities that depend on `AjaxRequestHeader.get_header(...)`.
- Existing drafts covered cookie-name validation, cookie-value validation, scalar header constructor validation, and initial cookie-container validation, but did not validate directly mutated header state at serialization.
- The focused RED failures showed malformed direct mutations either serialized without error or failed as `.items()` attribute errors. The GREEN regression covers those mutations before header dictionaries are returned.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
