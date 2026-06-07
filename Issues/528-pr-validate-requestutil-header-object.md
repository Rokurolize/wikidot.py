# PR Draft: Validate RequestUtil Header Object State

## Summary

`RequestUtil.request(...)` already validates direct URL methods, URL batches, exception-returning controls, config-object state, and numeric config fields before GET/POST work. It still treated malformed nested `client.amc_client.header` state as optional header absence. A caller, generated fixture, or test double could replace `client.amc_client.header` with `None`, an arbitrary object, a dictionary, a string, or a boolean, and non-empty direct URL requests would proceed without client Wikidot headers instead of failing at the request boundary.

This change validates the stored RequestUtil header object before direct URL request setup. Replaced header state now raises `ValueError("header must be AjaxRequestHeader")` before any direct GET/POST request is sent. Valid empty URL batches, method/URL validation, return-exceptions validation, config-object validation, numeric config validation, Wikidot-only header forwarding, non-Wikidot header suppression, retry behavior, one-client-per-batch behavior, raw AMC requests, auth login/logout, client construction, page/user/site workflows, and full static gates remain unchanged.

## Outcome

Direct URL request callers now get deterministic header-object validation at the RequestUtil boundary instead of silently dropping stored client headers and continuing with an unauthenticated or context-free request.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using direct URL GET/POST batches, profile lookups, page-ID probes, browser-free authenticated reads, generated local fixtures, JSON/YAML adapters, migration tools, archival workflows, and local CI fixtures that may replace nested client state.

## Current Evidence

Local rollout-backed drafts establish `RequestUtil.request(...)`, authentication, request headers, and AMC mutable state as practical shared infrastructure. [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md) covered empty direct URL batches, [138-pr-reuse-requestutil-async-client.md](138-pr-reuse-requestutil-async-client.md) covered per-batch async-client reuse, [388-pr-validate-requestutil-return-exceptions-flag.md](388-pr-validate-requestutil-return-exceptions-flag.md) covered direct URL exception controls, [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md) covered direct URL numeric config fields, [517-pr-validate-requestutil-method-urls.md](517-pr-validate-requestutil-method-urls.md) covered method and URL inputs, [523-pr-validate-requestutil-config-object.md](523-pr-validate-requestutil-config-object.md) covered direct URL config-object state, [521-pr-validate-amc-header-serialization-state.md](521-pr-validate-amc-header-serialization-state.md) covered `AjaxRequestHeader.get_header(...)` serialization state, [522-pr-validate-amc-request-state-objects.md](522-pr-validate-amc-request-state-objects.md) covered raw AMC request-time stored header objects, and [527-pr-validate-auth-header-object.md](527-pr-validate-auth-header-object.md) covered auth login/logout header-object state.

Those prior slices are not duplicates. Issue 521 validates header contents once a real `AjaxRequestHeader` is asked to serialize itself. Issue 522 validates raw `AjaxModuleConnectorClient.request(...)` stored header objects. Issue 523 validates the RequestUtil config object before timeout/retry reads. Issue 527 validates auth login/logout before auth reads or mutates header state. This slice validates the direct URL RequestUtil helper's own stored header object before GET/POST header preparation or HTTP work. No upstream issue was filed from this local workspace.

## Changes

- Import `AjaxRequestHeader` into `src/wikidot/util/requestutil.py`.
- Add a RequestUtil-local header object validator that rejects non-`AjaxRequestHeader` state with `ValueError("header must be AjaxRequestHeader")`.
- Validate the header object before direct URL request header preparation and reuse the validated header for `get_header(...)`.
- Keep the existing Wikidot hostname gate so client headers are forwarded only to Wikidot hosts and suppressed for non-Wikidot hosts.
- Convert RequestUtil unit fixtures to use a real `AjaxRequestHeader` object with mocked `get_header(...)` for valid header-forwarding assertions.
- Add focused tests for replaced direct URL header objects before GET/POST request work.

## Type Of Change

- Input/state validation
- Direct URL request preflight hardening
- Test fixture correction
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `RequestUtil.request(...)` must reject replaced non-`AjaxRequestHeader` `client.amc_client.header` state before any non-empty direct GET/POST request is sent. |
| R2 | The rejection must use `ValueError("header must be AjaxRequestHeader")` rather than silently treating malformed state as absent headers. |
| R3 | Invalid header replacements must not issue HTTP requests. |
| R4 | Valid direct URL header forwarding must remain Wikidot-host-only, and non-Wikidot URLs must still omit client cookies. |
| R5 | Existing empty batches, method/URL validation, return-exceptions validation, config-object validation, numeric config validation, retry behavior, one-client-per-batch behavior, raw AMC requests, auth, client, page, user, and site workflows must remain unchanged. |
| R6 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, RequestUtil tests, adjacent tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Directly replacing `client.amc_client.header` with `None`, arbitrary objects, dictionaries, strings, or booleans raises before direct URL GET/POST work. | `test_rejects_invalid_header_object_before_request` failed RED for ten malformed replacements across GET and POST, then passed GREEN. | Silently treating malformed header state as absent headers, reaching request setup, or issuing HTTP requests rejects this local completion claim. | RequestUtil direct URL preflight | `src/wikidot/util/requestutil.py`, `tests/unit/test_requestutil.py` |
| R2 | The raised error is `ValueError("header must be AjaxRequestHeader")`. | The focused GREEN tests assert that diagnostic for ten malformed header replacements. | Returning raw AMC diagnostics, auth diagnostics, `AttributeError`, or no error rejects this local completion claim. | RequestUtil header diagnostics | `tests/unit/test_requestutil.py` |
| R3 | Invalid header replacements send no direct URL HTTP requests. | The focused GREEN tests assert `httpx_mock.get_requests() == []`. | Sending GET/POST requests, even without headers, rejects this local completion claim. | RequestUtil side effects | `tests/unit/test_requestutil.py` |
| R4 | Valid client headers still attach only to Wikidot hosts. | Existing GET/POST header-forwarding tests passed inside the 119-test RequestUtil suite. | Forwarding cookies to non-Wikidot hosts, dropping cookies for Wikidot hosts, changing hostname matching, or changing header stringification rejects this local completion claim. | Direct URL header forwarding | `tests/unit/test_requestutil.py` |
| R5 | Existing RequestUtil and adjacent workflows remain green. | RequestUtil passed 119 tests; adjacent RequestUtil/user/page/client/site/AMC/auth suites passed 947 tests; full unit passed 2488 tests. | Regressing empty batches, direct GET/POST success, retryable 5xx, non-retryable 4xx, timeout retry, return-exceptions, one-client-per-batch behavior, profile lookup, page-ID probing, client construction, site lookup, raw AMC requests, or auth login/logout rejects this local completion claim. | Direct URL and adjacent workflows | `tests/unit` |
| R6 | No private material or live action is needed to prove the behavior. | All regressions use synthetic header replacements and local unit tests; the draft contains no raw credentials, cookies, auth JSON, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `68546b4 fix(requestutil): validate header object state`.

- RED header-object tests: `uv run pytest tests/unit/test_requestutil.py::TestRequestUtilConfigValidation::test_rejects_invalid_header_object_before_request -q` failed 10 cases before the fix with `DID NOT RAISE` after mocked GET/POST responses were registered, proving direct URL requests continued instead of rejecting replaced header state.
- GREEN focused tests: the same focused command passed 10 tests after RequestUtil header-object preflight was added.
- `uv run pytest tests/unit/test_requestutil.py -q` passed 119 tests.
- `uv run ruff format src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed with 2 files left unchanged.
- `uv run ruff check src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed.
- `uv run ruff format --check src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit/test_requestutil.py tests/unit/test_user.py tests/unit/test_page.py tests/unit/test_client.py tests/unit/test_site.py tests/unit/test_amc_client.py tests/unit/test_auth.py -q` passed 947 tests.
- `uv run pytest tests/unit -q` passed 2488 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `RequestUtil.request(client, "GET", ["https://test.wikidot.com/test"])` and POST equivalents raise `ValueError("header must be AjaxRequestHeader")` when `client.amc_client.header` is `None`, `object()`, `{}`, `"header"`, or `True`.
- Those malformed header replacements send no HTTP requests.
- Valid direct URL GET/POST batches using a real `AjaxRequestHeader` continue to send client cookies only to `wikidot.com` and `*.wikidot.com` hosts.
- Non-Wikidot direct URL batches continue to omit client cookies.
- Empty URL batches still return `[]` without requiring client config or header state.
- Existing method/URL, return-exceptions, config-object, numeric config, retry, one-client-per-batch, raw AMC, auth, client, page, user, and site workflows remain green.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with AMC header serialization validation. Mitigation: Issue 521 covers malformed state inside a real `AjaxRequestHeader`; this slice covers RequestUtil receiving a replaced non-header object.
- Risk: This could be confused with raw AMC request-state validation. Mitigation: Issue 522 covers `AjaxModuleConnectorClient.request(...)`; this slice covers direct URL `RequestUtil.request(...)`.
- Risk: This could be confused with RequestUtil config-object validation. Mitigation: Issue 523 covers config state before timeout/retry reads; this slice covers the separate header object used for direct URL header forwarding.
- Risk: Valid tests that used bare MagicMock header state may fail. Mitigation: valid RequestUtil tests now use a real `AjaxRequestHeader` instance with mocked `get_header(...)`, preserving assertions while matching runtime object shape.

## Out Of Scope

Changing header immutability, accepting mapping-based header objects, changing cookie-name/value validation, changing header serialization, changing Wikidot-host detection, changing direct URL retry policy, changing URL validation, changing RequestUtil config validation, changing raw AMC request behavior, changing auth behavior, changing live Wikidot behavior, and upstream Issue/PR creation are outside this slice.

## Why This Matters

`RequestUtil.request(...)` is the direct URL executor beneath browser-free profile lookup, page probing, and other retry-aware reads. When nested header state is malformed, the helper should fail before request setup instead of silently dropping client cookies and continuing with a request that no longer represents the caller's stored client state.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used direct URL batches, user profile lookups, page-ID probes, generated fixtures, browser-free client state, auth cookies, and Ajax header state.
- Existing drafts covered direct URL empty batches, direct URL async-client reuse, direct URL exception controls, direct URL numeric/config/method/URL inputs, header value/serialization state, raw AMC request-state objects, and auth header-object state, but did not validate replaced RequestUtil header objects at the direct URL boundary.
- The focused RED failures showed replaced header objects being treated as absent headers while direct URL GET/POST requests continued. The GREEN regression covers those replacements before request work can run.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
