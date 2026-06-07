# PR Draft: Validate RequestUtil Config Object State

## Summary

`RequestUtil.request(client, method, urls, ...)` validates direct URL method, URL-batch, exception-returning, and numeric config inputs, but it still assumed `client.amc_client.config` was an `AjaxModuleConnectorConfig` object once a non-empty URL batch reached request setup. A caller, generated fixture, or test double could replace `client.amc_client.config` with `None`, an arbitrary object, a dictionary, a string, or a boolean, and direct URL requests would fail with the misleading numeric-field diagnostic `ValueError("request_timeout must be a positive number")` instead of identifying the malformed config object.

This change validates the config object itself before reading timeout, retry, backoff, and semaphore fields. Direct URL GET/POST batches now reject replaced config state with `ValueError("config must be AjaxModuleConnectorConfig")` before creating semaphores, clients, request headers, or HTTP requests. Valid empty URL batches, valid GET/POST behavior, existing numeric config validation, header forwarding, retry behavior, raw AMC requests, page/user/client/site workflows, and auth behavior remain unchanged.

## Outcome

Direct URL request callers now get deterministic config-object validation at the RequestUtil boundary instead of a misleading timeout-field error when the stored AMC config object is replaced.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using direct URL helpers for user/profile lookup, direct page-ID probing, generated audits, migration tools, moderation tools, archival workflows, browser-free automation, mocked clients, JSON/YAML adapters, or local fixtures that may replace nested client state.

## Current Evidence

Local rollout-backed drafts establish `RequestUtil.request(...)` and AMC config state as shared practical infrastructure. [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md) covered numeric timeout/retry/concurrency fields read by RequestUtil, [515-pr-validate-amc-config-object.md](515-pr-validate-amc-config-object.md) covered constructor-time AMC config object inputs, [517-pr-validate-requestutil-method-urls.md](517-pr-validate-requestutil-method-urls.md) covered direct method and URL-batch inputs, [520-pr-validate-amc-config-fields.md](520-pr-validate-amc-config-fields.md) covered config field construction, and [522-pr-validate-amc-request-state-objects.md](522-pr-validate-amc-request-state-objects.md) covered raw `AjaxModuleConnectorClient.request(...)` stored config and header object state.

Those prior slices are not duplicates. Issue 393 assumes a config-like object exists and validates its numeric fields. Issues 515 and 520 validate AMC construction surfaces. Issue 522 validates the raw AMC request boundary. This slice validates the direct URL RequestUtil boundary after callers or fixtures replace `client.amc_client.config` before a non-empty URL batch. No upstream issue was filed from this local workspace.

## Changes

- Import `AjaxModuleConnectorConfig` into `src/wikidot/util/requestutil.py`.
- Add `_validate_request_config_object(...)` to reject non-`AjaxModuleConnectorConfig` state with `ValueError("config must be AjaxModuleConnectorConfig")`.
- Run config-object validation before RequestUtil reads numeric config fields.
- Preserve the existing numeric config validators for malformed fields on otherwise valid config objects.
- Preserve valid empty URL batch behavior, valid GET/POST behavior, request header forwarding, retry behavior, and adjacent workflows.
- Add focused tests for replaced config objects across GET and POST direct URL batches.

## Type Of Change

- Input/state validation
- Direct URL request preflight hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `RequestUtil.request(...)` must reject replaced non-`AjaxModuleConnectorConfig` `client.amc_client.config` state before reading numeric fields or starting HTTP work. |
| R2 | The rejection must use `ValueError("config must be AjaxModuleConnectorConfig")` rather than misleading numeric-field diagnostics. |
| R3 | Existing valid numeric config field validation must remain unchanged for real `AjaxModuleConnectorConfig` objects. |
| R4 | Existing valid direct URL GET/POST behavior, header forwarding, retry behavior, and `return_exceptions` behavior must remain unchanged. |
| R5 | Existing RequestUtil, user, page, client, site, AMC, and auth workflows must remain green. |
| R6 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, RequestUtil tests, adjacent tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Directly replacing `client.amc_client.config` with `None`, arbitrary objects, dictionaries, strings, or booleans raises before any request is sent. | `test_rejects_invalid_config_object_before_request` failed RED for GET and POST with the old numeric timeout diagnostic, then passed GREEN. | Reading `.request_timeout` on malformed config state, creating request clients, issuing HTTP requests, or silently defaulting replaced state rejects this local completion claim. | RequestUtil direct URL preflight | `src/wikidot/util/requestutil.py`, `tests/unit/test_requestutil.py` |
| R2 | The raised error is `ValueError("config must be AjaxModuleConnectorConfig")`. | The focused GREEN test asserts that exact diagnostic for 10 malformed config replacements. | Returning `request_timeout must be a positive number`, attribute errors, or HTTPX-level errors rejects this local completion claim. | Config object diagnostics | `tests/unit/test_requestutil.py` |
| R3 | Numeric field validation remains delegated to the existing RequestUtil config validators after the object type passes. | Existing RequestUtil numeric validation tests passed inside the 109-test RequestUtil suite. | Removing numeric field validation, changing diagnostics for malformed numeric fields, or accepting malformed numeric state rejects this local completion claim. | RequestUtil numeric controls | `tests/unit/test_requestutil.py` |
| R4 | Valid direct URL behavior remains stable. | Existing GET/POST success, empty batch, header forwarding, retry, timeout, and `return_exceptions` tests passed inside the RequestUtil and adjacent suites. | Changing valid request method handling, URL handling, header forwarding, retry behavior, timeout handling, exception-returning behavior, or empty-batch behavior rejects this local completion claim. | Direct URL behavior | `tests/unit` |
| R5 | Existing adjacent workflows remain green. | Adjacent RequestUtil/user/page/client/site/AMC/auth suites passed 912 tests, and full unit passed 2453 tests. | Regressing profile lookup, page-ID probing, client accessors, site workflows, raw AMC requests, auth login/logout, or request utility behavior rejects this local completion claim. | RequestUtil and adjacent workflows | `tests/unit` |
| R6 | No private material or live action is needed to prove the behavior. | All regressions use synthetic config replacements and local unit tests; the draft contains no raw credentials, cookies, auth JSON, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `56272fe fix(requestutil): validate config object state`.

- RED config-object tests: `uv run pytest tests/unit/test_requestutil.py::TestRequestUtilConfigValidation::test_rejects_invalid_config_object_before_request -q` failed 10 cases before the fix because `None`, arbitrary objects, dictionaries, strings, and booleans across GET and POST raised `ValueError("request_timeout must be a positive number")`.
- GREEN focused tests: the same focused command passed 10 tests after config-object preflight was added.
- `uv run ruff format src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed with 2 files left unchanged.
- `uv run pytest tests/unit/test_requestutil.py -q` passed 109 tests.
- `uv run ruff check src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed.
- `uv run ruff format --check src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit/test_requestutil.py tests/unit/test_user.py tests/unit/test_page.py tests/unit/test_client.py tests/unit/test_site.py tests/unit/test_amc_client.py tests/unit/test_auth.py -q` passed 912 tests.
- `uv run pytest tests/unit -q` passed 2453 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `RequestUtil.request(client, "GET", ["https://example.com/test"])` and POST equivalents raise `ValueError("config must be AjaxModuleConnectorConfig")` when `client.amc_client.config` is `None`, `object()`, `{}`, `"config"`, or `True`.
- Those malformed config replacements send no HTTP requests.
- Valid empty URL batches still return `[]` before requiring client config.
- Valid `AjaxModuleConnectorConfig` objects still use the existing numeric timeout, retry, backoff, and semaphore validation.
- Valid GET/POST request behavior, header forwarding, retry behavior, `return_exceptions`, raw AMC requests, auth behavior, and page/user/client/site workflows remain unchanged.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This could be confused with numeric RequestUtil config validation. Mitigation: Issue 393 validates fields after config access; this slice validates the object before any field access.
- Risk: This could be confused with AMC constructor config validation. Mitigation: Issues 515 and 520 cover constructor inputs and field construction; this slice covers direct URL request-time nested state after replacement.
- Risk: This could be confused with raw AMC request-state validation. Mitigation: Issue 522 covers `AjaxModuleConnectorClient.request(...)`; this slice covers `RequestUtil.request(...)` direct URL batches.
- Risk: Rejecting replaced config objects may expose mocks that used bare dictionaries or generic objects. Mitigation: direct URL request helpers need the configured timeout, retry, backoff, and concurrency values; mocks should use a real `AjaxModuleConnectorConfig` or a full client fixture.

## Out Of Scope

Changing config immutability, accepting mapping-based config objects, changing numeric timeout/retry/backoff/semaphore validation, changing empty URL batch behavior, changing RequestUtil header forwarding, changing retry timing, changing raw AMC request behavior, changing auth behavior, live Wikidot behavior, and upstream Issue/PR creation are outside this slice.

## Why This Matters

`RequestUtil.request(...)` is the direct URL executor beneath browser-free profile lookup and page probing. When nested client state is malformed, the request boundary should identify the malformed config object before field-level validation or HTTP machinery starts.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used direct URL helpers, profile lookup, direct page-ID probing, generated fixtures, raw AMC clients, and nested client state that depends on `client.amc_client.config`.
- Existing drafts covered RequestUtil method/URL inputs, RequestUtil numeric controls, AMC constructor config validation, AMC config field construction, and raw AMC request-state validation, but did not validate replaced config objects at the direct URL RequestUtil boundary.
- The focused RED failures showed replaced config objects being reported as malformed `request_timeout` values. The GREEN regression covers those replacements before any request or numeric field validation can run.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
