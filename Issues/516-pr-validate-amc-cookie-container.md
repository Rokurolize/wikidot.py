# PR Draft: Validate AMC Header Cookie Container

## Summary

`AjaxRequestHeader(cookie=...)` documents `cookie` as a dictionary, but malformed caller-provided cookie containers were not rejected at the header boundary. Values such as lists, strings, booleans, and arbitrary objects reached `cookie.items()` and failed with incidental `AttributeError` diagnostics instead of a stable wikidot.py-side validation error.

This change validates the initial cookie container before iterating over cookie names and values. `cookie=None` still adds no caller cookies, valid dictionaries still merge into the default `wikidot_token7` header cookie state, malformed containers now raise `ValueError("cookie must be a dictionary")`, and existing cookie-name, cookie-value, non-cookie header, token, login/logout, AMC request, and RequestUtil behavior remain unchanged.

## Outcome

Malformed initial AMC header cookie containers now fail deterministically at construction, while valid default and dictionary cookie initialization remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who construct `AjaxRequestHeader(...)` directly or indirectly through browser-free clients, Ajax module connector setup, token/session handling, request utilities, tests, generated configuration, or local fixtures.

## Current Evidence

Header/request-state drafts [398-pr-validate-amc-cookie-names.md](398-pr-validate-amc-cookie-names.md), [399-pr-validate-amc-cookie-values.md](399-pr-validate-amc-cookie-values.md), and [400-pr-validate-amc-header-values.md](400-pr-validate-amc-header-values.md) establish `AjaxRequestHeader` as a practical safety boundary. They validate malformed cookie names, malformed cookie values, and malformed explicit non-cookie header values before unsafe header state can be serialized.

Those prior slices do not validate the `cookie` container itself. A generated config or fixture that passes a list, string, boolean, or arbitrary object still fails as a Python `.items()` attribute error rather than as a documented request-header input validation error.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 398. Issue 398 validates keys inside a cookie dictionary; this slice validates that the initial cookie container is a dictionary before keys are inspected.

This is not a duplicate of Issue 399. Issue 399 validates cookie values after a cookie mapping is available; this slice prevents non-mapping containers from reaching `.items()`.

This is not a duplicate of Issue 400. Issue 400 validates explicit non-cookie header fields; this slice validates the cookie mapping container.

This is not a duplicate of Issue 515. Issue 515 validates the Ajax module connector config object; this slice validates the `AjaxRequestHeader(cookie=...)` object.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_cookie_dict(...)` in `src/wikidot/connector/ajax.py`.
- Treat `cookie=None` as an empty caller cookie mapping.
- Reject non-dictionary cookie containers with `ValueError("cookie must be a dictionary")`.
- Preserve existing cookie-name and cookie-value validation for dictionary entries.
- Add parameterized header-constructor tests for list, string, boolean, and arbitrary object cookie containers.

## Type Of Change

- Input validation
- AMC request-header preflight hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `AjaxRequestHeader(cookie=[])` must raise `ValueError("cookie must be a dictionary")` before iterating over cookie entries. |
| R2 | String, boolean, and arbitrary object cookie containers must raise the same `ValueError`. |
| R3 | `cookie=None` must preserve default header-cookie behavior, including the default `wikidot_token7` value. |
| R4 | Valid dictionary cookies must still merge with default cookies and continue to use existing cookie-name and cookie-value validators. |
| R5 | Existing cookie-name validation, cookie-value validation, non-cookie header validation, token preservation, login/logout cookie behavior, AMC request behavior, client construction, auth behavior, direct URL request behavior, and site workflows must remain unchanged. |
| R6 | This slice must not coerce non-dict containers, validate cookie values more strictly than before, remove integer token support, require live Wikidot actions, credentials, cookies, auth JSON, raw response bodies, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, AMC tests, adjacent AMC/client/auth/request utility/site tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | List cookie containers fail with a stable cookie-container `ValueError`. | `TestAjaxRequestHeader.test_custom_cookie_rejects_non_dict_cookie_container` failed RED for `[]` with `AttributeError: 'list' object has no attribute 'items'`, then passed GREEN after validation was added. | Accepting lists, iterating arbitrary list data, or raising only via `.items()` rejects this local completion claim. | AMC request header construction | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | String, boolean, and arbitrary object cookie containers fail with the same diagnostic. | The same parameterized test failed RED for `"cookie"`, `True`, and `object()` with `.items()` `AttributeError`, then passed GREEN after validation was added. | Accepting strings, booleans, arbitrary objects, or treating them as iterable cookie data rejects this local completion claim. | AMC request header construction | `tests/unit/test_amc_client.py` |
| R3 | Default cookie behavior remains stable. | Existing `test_default_values`, `test_get_header`, and related header tests passed after the guard. | Removing the default `wikidot_token7`, changing default header fields, or requiring a caller cookie dictionary rejects this local completion claim. | Default header state | `tests/unit/test_amc_client.py` |
| R4 | Valid cookie dictionaries still use existing entry validators. | Existing invalid cookie-name and cookie-value tests passed, and valid custom cookie tests passed. | Bypassing key/value validators, rejecting valid dictionaries, or changing accepted integer token values rejects this local completion claim. | Header cookie entries | `tests/unit/test_amc_client.py` |
| R5 | Existing request and adjacent workflows remain green. | AMC tests passed 121 tests, adjacent AMC/client/auth/request utility/site tests passed 493 tests, and full unit passed 2315 tests. | Regressing cookie-name validation, cookie-value validation, non-cookie header validation, token behavior, login/logout cookie state, AMC request behavior, client construction, auth behavior, direct URL behavior, or site workflows rejects this local completion claim. | AMC and adjacent workflows | `tests/unit` |
| R6 | No private material or live action is needed to prove the behavior. | All regressions use synthetic cookie container values and local header construction; the draft contains no raw credentials, cookies, auth JSON, or response bodies. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, AMC tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `443097d fix(amc): validate header cookie container`.

- RED cookie-container tests: `uv run pytest tests/unit/test_amc_client.py::TestAjaxRequestHeader::test_custom_cookie_rejects_non_dict_cookie_container -q` failed 4 malformed cookie container cases before the fix with `.items()` `AttributeError`.
- GREEN cookie-container tests: the same focused command passed 4 tests after cookie container validation was added.
- `uv run ruff format src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` reformatted 1 file and left 1 file unchanged.
- `uv run pytest tests/unit/test_amc_client.py -q` passed 121 tests.
- `uv run pytest tests/unit/test_amc_client.py tests/unit/test_client.py tests/unit/test_auth.py tests/unit/test_requestutil.py tests/unit/test_site.py -q` passed 493 tests.
- `uv run ruff check src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed.
- `uv run ruff format --check src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2315 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `AjaxRequestHeader(cookie=[])` raises `ValueError("cookie must be a dictionary")`.
- `AjaxRequestHeader(cookie="cookie")`, `cookie=True`, and `cookie=object()` raise the same validation error.
- Malformed cookie containers fail before `.items()` is called.
- `AjaxRequestHeader()` and `AjaxRequestHeader(cookie=None)` preserve default header-cookie behavior.
- `AjaxRequestHeader(cookie={"session": "abc123"})` remains valid and still keeps `wikidot_token7`.
- Existing invalid cookie-name and cookie-value cases keep their existing diagnostics.
- The new tests use synthetic cookie containers only and do not require live Wikidot, real credentials, cookies, auth JSON, raw response bodies, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This tightens behavior for callers that accidentally pass list-of-pairs or another mapping-like wrapper. Mitigation: the public parameter is documented as `dict | None`; callers should normalize generated config before header construction.
- Risk: This could be confused with cookie-name or cookie-value validation. Mitigation: this slice only validates the container type; entry keys and values still use the existing validators.
- Risk: The guard could alter valid header behavior. Mitigation: default header tests, valid custom cookie tests, AMC tests, adjacent tests, and full unit tests remain green.
- Risk: Tests could accidentally expose real cookie values. Mitigation: all test inputs are synthetic and no live request is required.

## Out Of Scope

Cookie-name validation, cookie-value validation, non-cookie header validation, token preservation, token masking, login credential validation, session-cookie value validation, logout cleanup, retry controls, URL routing, request bodies, response parsing, live Wikidot behavior, and accepting non-dict structural mapping objects are outside this slice.

## Why This Matters

Header cookie state carries request and session context. Generated config and local fixtures can accidentally pass the wrong container shape; a deterministic constructor error is clearer than storing default header state and then surfacing an incidental Python attribute error unrelated to wikidot.py's public API.

## Rollout-Backed Notes

- Local rollout-backed work established `AjaxRequestHeader` as shared state for `wikidot_token7`, `WIKIDOT_SESSION_ID`, login/session setup, public source fetches, and AMC request execution.
- Existing drafts covered sensitive-log masking, token value preservation, login session-cookie value validation, raw AMC flag validation, raw AMC numeric controls, cookie-name validation, cookie-value validation, non-cookie header validation, request body validation, and connector config-object validation, but did not validate the initial cookie container itself.
- The focused RED failures showed malformed cookie containers reaching `.items()` before the fix. The GREEN regression covers those values before cookie entry validation or header serialization can run.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
