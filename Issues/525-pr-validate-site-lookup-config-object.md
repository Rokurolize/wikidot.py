# PR Draft: Validate Site Lookup Config Object State

## Summary

`Site.from_unix_name(client, unix_name)` validates site UNIX-name input and delegates retry/timeout controls to the shared HTTP helper, but it still assumed `client.amc_client.config` was an `AjaxModuleConnectorConfig` object once a valid site name reached lookup request setup. A caller, generated fixture, or test double could replace `client.amc_client.config` with `None`, an arbitrary object, a dictionary, a string, or a boolean, and site lookup would fail with incidental attribute errors such as `'dict' object has no attribute 'request_timeout'` while preparing the GET request.

This change validates the stored config object before reading timeout, retry, and backoff fields. Site lookup now rejects replaced config state with `ValueError("config must be AjaxModuleConnectorConfig")` before issuing HTTP requests. Valid site lookup, redirect handling, not-found handling, site metadata parsing, malformed site-response diagnostics, raw AMC requests, RequestUtil, auth login, client construction, and site AMC retry workflows remain unchanged.

## Outcome

Site lookup callers now get deterministic config-object validation at the `Site.from_unix_name(...)` boundary instead of lower-level attribute errors when nested AMC config state is replaced.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free site discovery, account bootstrap scripts, mocked clients, generated local fixtures, JSON/YAML adapters, migration tools, moderation tools, archival workflows, or local CI fixtures that may replace nested client state.

## Current Evidence

Local rollout-backed drafts establish site lookup and AMC config state as practical shared infrastructure. [395-pr-validate-http-request-timeouts.md](395-pr-validate-http-request-timeouts.md) covered low-level HTTP helper timeout values, [394-pr-validate-site-amc-retry-controls.md](394-pr-validate-site-amc-retry-controls.md) covered `Site.amc_request_with_retry(...)` retry controls, [515-pr-validate-amc-config-object.md](515-pr-validate-amc-config-object.md) covered constructor-time AMC config object inputs, [520-pr-validate-amc-config-fields.md](520-pr-validate-amc-config-fields.md) covered config field construction, [522-pr-validate-amc-request-state-objects.md](522-pr-validate-amc-request-state-objects.md) covered raw `AjaxModuleConnectorClient.request(...)` stored request-state objects, [523-pr-validate-requestutil-config-object.md](523-pr-validate-requestutil-config-object.md) covered direct URL `RequestUtil.request(...)` config object state, and [524-pr-validate-auth-login-config-object.md](524-pr-validate-auth-login-config-object.md) covered auth login config object state.

Those prior slices are not duplicates. Issue 395 validates the `timeout` argument once a value reaches the shared HTTP helper. Issues 515 and 520 validate AMC construction surfaces. Issue 522 validates the raw AMC request boundary. Issue 523 validates the direct URL RequestUtil boundary. Issue 524 validates the auth login POST boundary. Issue 394 validates site-level AMC retry batching, not the direct site-lookup HTTP GET path. This slice validates the site lookup boundary after callers or fixtures replace `client.amc_client.config` before `Site.from_unix_name(...)` prepares its GET request. No upstream issue was filed from this local workspace.

## Changes

- Import `AjaxModuleConnectorConfig` into `src/wikidot/module/site.py`.
- Add `_validate_site_config_object(...)` to reject non-`AjaxModuleConnectorConfig` state with `ValueError("config must be AjaxModuleConnectorConfig")`.
- Run config-object validation before site lookup timeout/retry field access or HTTP GET setup.
- Preserve the existing site UNIX-name validation, HTTP redirect handling, not-found handling, metadata parsing, and malformed-response diagnostics.
- Add focused tests for replaced site lookup config objects before request setup.

## Type Of Change

- Input/state validation
- Site lookup preflight hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.from_unix_name(...)` must reject replaced non-`AjaxModuleConnectorConfig` `client.amc_client.config` state before preparing the site lookup request. |
| R2 | The rejection must use `ValueError("config must be AjaxModuleConnectorConfig")` rather than incidental attribute errors or field-level timeout diagnostics. |
| R3 | Invalid config replacements must not issue HTTP requests. |
| R4 | Existing valid site lookup, redirect handling, not-found handling, malformed site-response diagnostics, and site AMC retry behavior must remain unchanged. |
| R5 | Existing site, HTTP, QuickModule, client, auth, AMC, RequestUtil, and full unit workflows must remain green. |
| R6 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, site tests, adjacent tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Directly replacing `client.amc_client.config` with `None`, arbitrary objects, dictionaries, strings, or booleans raises before the site lookup request is prepared. | `test_from_unix_name_rejects_invalid_config_object_before_request` failed RED for five malformed replacements with old attribute errors, then passed GREEN. | Reading `.request_timeout` on malformed config state, preparing a site lookup GET, or silently defaulting replaced state rejects this local completion claim. | Site lookup preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | The raised error is `ValueError("config must be AjaxModuleConnectorConfig")`. | The focused GREEN test asserts that exact diagnostic for five malformed config replacements. | Returning `AttributeError`, `timeout must be a positive number`, HTTPX-level errors, or site-response parsing errors rejects this local completion claim. | Config object diagnostics | `tests/unit/test_site.py` |
| R3 | Invalid config replacements do not send HTTP requests. | The focused GREEN test asserts `httpx_mock.get_requests() == []`. | Issuing any request through `httpx`, registering a redirect, or parsing response data under invalid config state rejects this local completion claim. | Site lookup side effects | `tests/unit/test_site.py` |
| R4 | Existing site lookup and site retry behavior remains stable. | `uv run pytest tests/unit/test_site.py -q` passed 251 tests. | Regressing valid SSL/non-SSL lookup, not-found handling, missing metadata diagnostics, malformed site ID diagnostics, `Site.amc_request(...)`, `Site.amc_request_with_retry(...)`, publish, invite, source, recent-change, member, or application workflows rejects this local completion claim. | Site workflows | `tests/unit/test_site.py` |
| R5 | Existing adjacent workflows remain green. | Adjacent site/HTTP/QuickModule/client/auth/AMC/RequestUtil suites passed 832 tests, and full unit passed 2463 tests. | Regressing shared HTTP retry helpers, QuickModule lookup, client construction, auth login/logout, raw AMC request validation, direct URL requests, or site workflows rejects this local completion claim. | Site and adjacent workflows | `tests/unit` |
| R6 | No private material or live action is needed to prove the behavior. | All regressions use synthetic config replacements and local unit tests; the draft contains no raw credentials, cookies, auth JSON, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `3f1add8 fix(site): validate lookup config object state`.

- RED config-object tests: `uv run pytest tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_rejects_invalid_config_object_before_request -q` failed 5 cases before the fix because `None`, arbitrary objects, dictionaries, strings, and booleans raised `AttributeError` while reading `request_timeout`.
- GREEN focused tests: the same focused command passed 5 tests after config-object preflight was added.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` passed with 2 files left unchanged.
- `uv run pytest tests/unit/test_site.py -q` passed 251 tests.
- `uv run ruff check src/wikidot/module/site.py tests/unit/test_site.py` passed.
- `uv run ruff format --check src/wikidot/module/site.py tests/unit/test_site.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/module/site.py tests/unit/test_site.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/site.py tests/unit/test_site.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit/test_site.py tests/unit/test_http.py tests/unit/test_quick_module.py tests/unit/test_client.py tests/unit/test_auth.py tests/unit/test_amc_client.py tests/unit/test_requestutil.py -q` passed 832 tests.
- `uv run pytest tests/unit -q` passed 2463 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Site.from_unix_name(client, "test-site")` raises `ValueError("config must be AjaxModuleConnectorConfig")` when `client.amc_client.config` is `None`, `object()`, `{}`, `"config"`, or `True`.
- Those malformed config replacements send no HTTP requests.
- Existing invalid `unix_name` validation still runs before config validation and sends no request.
- Valid SSL and non-SSL site lookup, not-found handling, missing site ID/title/unix name/domain diagnostics, malformed site ID diagnostics, `Site.amc_request(...)`, `Site.amc_request_with_retry(...)`, and adjacent site workflows remain unchanged.
- Shared HTTP helper behavior, QuickModule lookup, auth login, raw AMC requests, direct URL RequestUtil requests, and client construction remain unchanged.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This could be confused with shared HTTP timeout validation. Mitigation: Issue 395 covers timeout values after the helper receives one; this slice validates the nested config object before field reads.
- Risk: This could be confused with AMC constructor config validation. Mitigation: Issues 515 and 520 cover constructor inputs and field construction; this slice covers site lookup request-time nested state after replacement.
- Risk: This could be confused with raw AMC, RequestUtil, or auth login config-object validation. Mitigation: Issues 522, 523, and 524 cover other request boundaries; this slice covers the direct site lookup GET path.
- Risk: This could be confused with site AMC retry-control validation. Mitigation: Issue 394 covers `Site.amc_request_with_retry(...)`; this slice covers `Site.from_unix_name(...)`.
- Risk: Rejecting replaced config objects may expose mocks that used bare dictionaries or generic objects. Mitigation: site lookup needs configured timeout, attempt limit, retry interval, max backoff, and backoff factor values; mocks should use a real `AjaxModuleConnectorConfig` or a full client fixture.

## Out Of Scope

Changing config immutability, accepting mapping-based config objects, changing numeric timeout/retry/backoff validation, changing site UNIX-name validation, changing redirect policy, changing site metadata parsing, changing `Site.amc_request_with_retry(...)`, changing raw AMC request behavior, changing RequestUtil behavior, changing auth behavior, live Wikidot behavior, and upstream Issue/PR creation are outside this slice.

## Why This Matters

`Site.from_unix_name(...)` is the browser-free site discovery path. When nested client state is malformed, the lookup boundary should identify the malformed config object before retry setup or HTTP machinery starts.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used browser-free clients, site discovery, account bootstrap flows, mocked client objects, generated fixtures, raw AMC clients, and nested client state that depends on `client.amc_client.config`.
- Existing drafts covered shared HTTP timeout values, site AMC retry controls, AMC constructor config validation, AMC config field construction, raw AMC request-state validation, direct URL RequestUtil config-object validation, and auth login config-object validation, but did not validate replaced config objects at the site lookup boundary.
- The focused RED failures showed replaced config objects surfacing as attribute errors while `Site.from_unix_name(...)` prepared the GET helper call. The GREEN regression covers those replacements before requests or site response parsing can run.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
