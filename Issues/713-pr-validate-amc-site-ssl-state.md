# PR Draft: Validate AMC Client Site SSL Request State

## Summary

`AjaxModuleConnectorClient.request(..., site_ssl_supported=...)` accepts a request-time site SSL override that controls whether raw Ajax Module Connector calls use `http://` or `https://`. The public type is `bool | None`, but malformed values such as `"true"`, `"false"`, `1`, `0`, and arbitrary objects were accepted and coerced by Python truthiness when building the request URL. A truthy string could silently force HTTPS, while integer `0` could silently force HTTP.

This change validates the resolved site SSL state before request headers, async tasks, or HTTP work are created. Malformed explicit overrides now raise `ValueError("site_ssl_supported must be a boolean")`, and a mutated retained `AjaxModuleConnectorClient.ssl_supported` value raises the same deterministic preflight error. Valid default fallback behavior and valid `True`/`False` overrides keep their existing URL scheme behavior.

## Outcome

Raw AMC callers now get deterministic request-time validation for the site SSL routing flag instead of accidental truthiness selecting the HTTP scheme.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using raw AMC calls directly or through site, page, forum, member, application, source, migration, moderation, generated fixture, or browser-free automation workflows that may load request routing controls from JSON, YAML, CLI flags, spreadsheets, or environment variables.

## Current Evidence

Local rollout-backed drafts repeatedly identify raw AMC request execution as a shared lower-level surface. Existing drafts [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md), [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), [401-pr-validate-amc-request-bodies.md](401-pr-validate-amc-request-bodies.md), and [522-pr-validate-amc-request-state-objects.md](522-pr-validate-amc-request-state-objects.md) cover exception controls, execution controls, request body shape, config object state, and header object state for `AjaxModuleConnectorClient.request(...)`.

Adjacent site metadata drafts [480-pr-validate-site-constructor-metadata.md](480-pr-validate-site-constructor-metadata.md), [571-pr-validate-site-url-metadata-state.md](571-pr-validate-site-url-metadata-state.md), [629-pr-validate-blank-site-routing-metadata.md](629-pr-validate-blank-site-routing-metadata.md), and [712-pr-validate-site-amc-request-state.md](712-pr-validate-site-amc-request-state.md) validate `Site` constructor metadata, URL-time metadata, blank routing metadata, and Site wrapper retained AMC state. Those prior slices are not duplicates: they do not validate the direct raw AMC `site_ssl_supported` override or the raw AMC client's retained fallback SSL flag at request time. No upstream issue was filed from this local workspace.

## Changes

- Add request-time validation for the resolved raw AMC site SSL flag.
- Reject malformed explicit `site_ssl_supported` overrides before header setup, async task creation, or HTTP requests.
- Reject malformed retained `AjaxModuleConnectorClient.ssl_supported` state before default-fallback requests.
- Preserve valid `site_ssl_supported=True`, `site_ssl_supported=False`, and default `None` fallback behavior.
- Add focused regressions for malformed explicit overrides, valid boolean overrides, and mutated retained SSL state.

## Type Of Change

- Input validation
- Retained-state validation
- Raw Ajax Module Connector request-boundary hardening
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `AjaxModuleConnectorClient.request(..., site_ssl_supported=...)` must reject non-bool explicit overrides with `ValueError("site_ssl_supported must be a boolean")` before HTTP requests are issued. |
| R2 | `AjaxModuleConnectorClient.request(...)` must reject a mutated non-bool retained `client.ssl_supported` fallback with the same diagnostic before HTTP requests are issued. |
| R3 | Valid `site_ssl_supported=True` and `site_ssl_supported=False` overrides must still select HTTPS and HTTP respectively. |
| R4 | Existing request behavior must remain unchanged for default routing fallback, site-name validation, body validation, config/header validation, retry behavior, response parsing, `return_exceptions`, and Site wrapper delegation. |
| R5 | Focused RED/GREEN, affected tests, adjacent request-path tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed explicit SSL overrides fail before any request is sent. | `test_request_rejects_non_bool_site_ssl_supported_before_request` failed RED for `"true"`, `"false"`, `1`, `0`, and `object()` with `DID NOT RAISE`, then passed GREEN after validation was added. | Treating truthy strings/objects as HTTPS, treating `0` as HTTP, consuming the mocked response, or raising a later HTTP/retry error rejects this local completion claim. | Raw AMC request routing override | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | Mutated retained raw AMC SSL state fails before default-fallback requests. | `test_request_rejects_mutated_ssl_supported_before_request` passed after validating the resolved fallback value. | Using mutated `client.ssl_supported` truthiness for scheme choice, issuing HTTP requests, or hiding the state problem behind response handling rejects this local completion claim. | Raw AMC retained scheme state | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R3 | Valid boolean overrides keep existing URL scheme selection. | `test_request_accepts_bool_site_ssl_supported_override` passed for `True` and `False` and asserted the requested URL scheme. | Rejecting real booleans, inverting the scheme, or ignoring the explicit override rejects this local completion claim. | Raw AMC valid routing override | `tests/unit/test_amc_client.py` |
| R4 | Adjacent request behavior remains stable. | `tests/unit/test_amc_client.py` passed 217 tests; adjacent AMC/Site/RequestUtil/HTTP suites passed 826 tests; full unit coverage passed 3579 tests. | Regressing site-name validation, body validation, config/header state validation, token handling, retry behavior, response parsing, `return_exceptions`, Site wrapper delegation, RequestUtil, or shared HTTP helpers rejects this local completion claim. | Request workflows | `tests/unit` |
| R5 | Repository quality gates pass in the local dependency environment. | Full ruff check, ruff format check, mypy, pyright, and `git diff --check` all passed. | Any hidden test, lint, format, type, pyright, or whitespace failure rejects this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live site state or private material is needed to prove the behavior. | The regressions use synthetic unit-level values and `pytest-httpx` only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private content, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `cd8ab25 fix(amc): validate site ssl request state`.

- RED: `uv run pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_non_bool_site_ssl_supported_before_request -q` failed 5 selected cases before the fix with `DID NOT RAISE` because malformed overrides were accepted and used to consume mocked HTTP responses.
- GREEN focused: `uv run pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_non_bool_site_ssl_supported_before_request -q` passed 5 tests after validation was added.
- Focused preservation/state: `uv run pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_non_bool_site_ssl_supported_before_request tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_accepts_bool_site_ssl_supported_override tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_mutated_ssl_supported_before_request -q` passed 10 tests.
- `uv run pytest tests/unit/test_amc_client.py -q` passed 217 tests.
- `uv run pytest tests/unit/test_amc_client.py tests/unit/test_site.py tests/unit/test_requestutil.py tests/unit/test_http.py -q` passed 826 tests.
- `uv run pytest tests/unit -q` passed 3579 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `AjaxModuleConnectorClient(site_name="www").request([body], site_ssl_supported="true")`, `"false"`, `1`, `0`, or an arbitrary object raises `ValueError("site_ssl_supported must be a boolean")` before HTTP requests are issued.
- A mutated non-bool `client.ssl_supported` fallback raises the same error before HTTP requests are issued.
- Valid explicit `site_ssl_supported=True` still requests `https://<site>.wikidot.com/ajax-module-connector.php`.
- Valid explicit `site_ssl_supported=False` still requests `http://<site>.wikidot.com/ajax-module-connector.php`.
- Valid default `site_ssl_supported=None` still falls back to the connector's retained SSL support value.
- Existing raw AMC body, config/header, token, retry, response, `return_exceptions`, site-name override, Site wrapper, RequestUtil, and shared HTTP behavior remains green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Callers may have passed `0` or `1` as integer stand-ins for booleans. Mitigation: the public type is `bool | None`, and accepting integers can silently flip the URL scheme.
- Risk: Callers may have passed string values loaded from CLI, YAML, JSON, spreadsheet, or environment configuration. Mitigation: configuration layers should parse text into real booleans before calling the raw AMC client.
- Risk: This could be confused with Site wrapper validation. Mitigation: Issue 712 covers `Site.amc_request(...)` retained state; this slice applies to the lower-level raw AMC client.
- Risk: This could be confused with Site URL metadata validation. Mitigation: Issues 571 and 629 cover `Site.url` and site routing metadata; this slice covers raw request URL construction in `AjaxModuleConnectorClient.request(...)`.

## Dependencies

- Existing `AjaxModuleConnectorClient.request(...)` remains the source of truth for raw Ajax Module Connector request execution.
- Existing Site wrapper request validation remains separate and unchanged.
- Existing `StringUtil.validate_site_unix_name(...)` remains responsible for site-name override validation.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered raw AMC site SSL request-state path.

## Upstream-Safe Motivation

`site_ssl_supported` controls raw AMC request URL construction. Because malformed truthy/falsy values can silently select `http://` or `https://`, rejecting non-booleans before request work makes configuration mistakes visible and keeps the public API aligned with its type.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established raw AMC request behavior as practical shared infrastructure through site, page, forum, member, application, source, migration, generated-fixture, and browser-free automation workflows.
- Existing AMC drafts covered exception controls, numeric controls, body shape, config/header state, and Site wrapper retained state; they did not validate the direct raw AMC `site_ssl_supported` scheme-control surface.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
