# PR Draft: Validate Ajax Module Connector Config Object

## Summary

`AjaxModuleConnectorClient(..., config=...)` documents `config` as `AjaxModuleConnectorConfig | None`, but malformed caller-provided config objects were accepted and stored. For the default `www` connector path, values such as `object()`, dictionaries, strings, and booleans could construct a client, initialize headers, and only fail later when request, auth, site, or direct-URL helpers tried to read config attributes such as `request_timeout` or `retry_interval`.

This change validates the config object at connector construction. `config=None` still creates the default `AjaxModuleConnectorConfig()`, valid `AjaxModuleConnectorConfig` instances are preserved, and non-config objects now raise `ValueError("config must be AjaxModuleConnectorConfig")` before header setup or HTTP request work.

## Outcome

Malformed Ajax module connector config objects now fail locally at the constructor boundary, while default and valid custom config construction remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who pass `AjaxModuleConnectorConfig` through `AjaxModuleConnectorClient(...)`, `Client(amc_config=...)`, browser-free automation, sandbox setup scripts, account bootstrap checks, CI fixtures, or generated local configuration.

## Current Evidence

Rollout-backed draft [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md) records practical browser-free publishing scripts importing `wikidot`, constructing `Client(...)`, and using `AjaxModuleConnectorConfig` for request behavior. Later infrastructure drafts such as [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md), [395-pr-validate-http-request-timeouts.md](395-pr-validate-http-request-timeouts.md), and [396-pr-validate-listpages-retry-control.md](396-pr-validate-listpages-retry-control.md) establish retry/timeout configuration as a practical safety surface.

Those existing drafts validate fields after a config-like object reaches request helpers. They do not validate that the connector constructor received an `AjaxModuleConnectorConfig` object rather than an arbitrary object that may fail later.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 392. Issue 392 validates numeric fields on a provided `AjaxModuleConnectorConfig` when `AjaxModuleConnectorClient.request(...)` runs; this slice validates the config object itself when `AjaxModuleConnectorClient(...)` is constructed.

This is not a duplicate of Issue 393. Issue 393 validates direct URL request config fields before `RequestUtil.request(...)` sends GET/POST work; this slice rejects malformed config containers before they become connector state.

This is not a duplicate of Issues 395 or 396. Those slices validate lower-level HTTP timeouts and ListPages retry controls; this slice keeps the connector constructor's documented config type honest.

This is not a duplicate of Issue 514. Issue 514 validates `Client.__init__(...)` credential pair presence; this slice validates the Ajax connector config object used by `Client(amc_config=...)` and raw connector construction.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_amc_config(...)` in `src/wikidot/connector/ajax.py`.
- Preserve `config=None` by returning a fresh default `AjaxModuleConnectorConfig()`.
- Preserve valid custom `AjaxModuleConnectorConfig` instances by returning the same object.
- Reject non-config objects with `ValueError("config must be AjaxModuleConnectorConfig")`.
- Add constructor tests for malformed config objects before header setup or HTTP request work.

## Type Of Change

- Input validation
- Connector constructor preflight hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `AjaxModuleConnectorClient(site_name="www", config=object())` must raise `ValueError("config must be AjaxModuleConnectorConfig")` before header setup. |
| R2 | Dictionary, string, and boolean config values must raise the same `ValueError` before header setup. |
| R3 | Invalid config objects must not initialize `AjaxRequestHeader` or issue HTTP requests. |
| R4 | `config=None` must still create a default `AjaxModuleConnectorConfig()`, and valid custom `AjaxModuleConnectorConfig` instances must remain accepted. |
| R5 | Existing request numeric validation, request body validation, response parsing, retry behavior, header/cookie validation, auth login behavior, client construction, direct URL request behavior, and site workflows must remain unchanged. |
| R6 | This slice must not validate config field values at construction time, change retry defaults, require live Wikidot actions, credentials, cookies, auth JSON, raw response bodies, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, AMC tests, adjacent AMC/client/auth/request utility/site tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Arbitrary object configs fail with the stable config-object `ValueError`. | `TestAjaxModuleConnectorClientInit.test_invalid_config_object_rejected_before_header_setup` failed RED for `object()` because no `ValueError` was raised, then passed GREEN after validation was added. | Accepting `object()` as connector config, storing it, initializing headers, or raising an unrelated later attribute error rejects this local completion claim. | AMC constructor preflight | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | Dictionary, string, and boolean config values fail with the same diagnostic. | The same parameterized test failed RED for `{}`, `"config"`, and `True` with `DID NOT RAISE`, then passed GREEN after validation was added. | Treating mappings, strings, or booleans as config-like objects rejects this local completion claim. | AMC constructor preflight | `tests/unit/test_amc_client.py` |
| R3 | Invalid config objects do not advance to header or HTTP setup. | The GREEN test patches `AjaxRequestHeader`, asserts it is not called, and asserts `httpx_mock.get_requests() == []`. | Header initialization, SSL-probe HTTP work, request helper work, or raw response capture rejects this local completion claim. | Constructor side effects | `tests/unit/test_amc_client.py` |
| R4 | Default and valid custom config behavior remains stable. | Existing default/custom config tests and the AMC suite passed after the guard. | Replacing valid config objects unexpectedly, changing defaults, or failing `site_name="www"` construction rejects this local completion claim. | Connector construction | `tests/unit/test_amc_client.py` |
| R5 | Existing request and adjacent workflows remain green. | AMC tests passed 117 tests, adjacent AMC/client/auth/request utility/site tests passed 489 tests, and full unit passed 2311 tests. | Regressing request numeric validation, request body validation, response parsing, retry behavior, header/cookie validation, auth login, client construction, direct URL behavior, or site workflows rejects this local completion claim. | AMC and adjacent workflows | `tests/unit` |
| R6 | No private material or live action is needed to prove the behavior. | All regressions use synthetic config values, patched local header setup, and pytest-httpx request inspection; the draft contains no raw credentials, cookies, auth JSON, or response bodies. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, AMC tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `a3103f3 fix(ajax): validate connector config object`.

- RED config-object tests: `uv run pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientInit::test_invalid_config_object_rejected_before_header_setup -q` failed 4 malformed config object cases before the fix with `DID NOT RAISE`.
- GREEN config-object tests: the same focused command passed 4 tests after config object validation was added.
- `uv run ruff format src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_amc_client.py -q` passed 117 tests.
- `uv run pytest tests/unit/test_amc_client.py tests/unit/test_client.py tests/unit/test_auth.py tests/unit/test_requestutil.py tests/unit/test_site.py -q` passed 489 tests.
- `uv run ruff check src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed.
- `uv run ruff format --check src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2311 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `AjaxModuleConnectorClient(site_name="www", config=object())` raises `ValueError("config must be AjaxModuleConnectorConfig")` before header setup.
- `AjaxModuleConnectorClient(site_name="www", config={})`, `"config"`, and `True` raise the same validation error before header setup.
- Invalid config objects do not initialize `AjaxRequestHeader` or issue HTTP requests.
- `AjaxModuleConnectorClient(site_name="www", config=None)` still uses default config.
- `AjaxModuleConnectorClient(site_name="www", config=AjaxModuleConnectorConfig(...))` still preserves the valid custom config object.
- Existing request numeric validation, request body validation, response parsing, retry behavior, header/cookie validation, auth login behavior, client construction, direct URL request behavior, and site workflows remain green.
- The new tests use synthetic config objects only and do not require live Wikidot, real credentials, cookies, auth JSON, raw response bodies, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This tightens behavior for callers that supplied a config-like object with matching attributes. Mitigation: the public type is `AjaxModuleConnectorConfig | None`; accepting arbitrary objects hides configuration mistakes and leaves later request code to fail with less useful diagnostics.
- Risk: This could be confused with existing numeric config validation. Mitigation: field values are still validated at their existing request boundaries; this slice only validates the config container type at construction.
- Risk: The guard could change valid connector behavior. Mitigation: default config construction, valid custom config construction, AMC tests, adjacent tests, and full unit tests remain green.
- Risk: Tests could accidentally require live HTTP. Mitigation: the focused regression uses `site_name="www"`, patches header setup, and asserts pytest-httpx saw no requests.

## Out Of Scope

Config field value validation at construction time, retry default changes, timeout policy changes, request body validation, response parsing, auth login behavior, client credential validation, direct URL request behavior, site workflow changes, live Wikidot actions, and accepting structural duck-typed config objects are outside this slice.

## Why This Matters

Config-driven browser-free workflows often wire retry and timeout behavior from JSON, YAML, environment adapters, or generated fixtures. If the wrong object reaches the connector constructor, wikidot.py should fail where the configuration boundary is crossed rather than storing the bad object and failing later as an unrelated request-time attribute problem.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used browser-free clients, Ajax module connector retry settings, direct request helpers, auth setup, site accessors, and generated configuration as practical operational surfaces.
- Existing local drafts covered AMC numeric config values, direct URL numeric config values, HTTP retry controls, ListPages retry controls, client credential pairs, and login credential types, but did not cover the connector config object itself.
- The focused RED failures showed malformed config objects silently constructed `www` connectors before the fix. The GREEN regression covers those values before header setup or HTTP requests can run.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw response bodies, private content, and private site data out of upstream discussion.
