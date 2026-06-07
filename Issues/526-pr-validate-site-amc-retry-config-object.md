# PR Draft: Validate Site AMC Retry Config Object State

## Summary

`Site.amc_request_with_retry(...)` validates explicit and config-derived retry control values, but it still assumed `self.client.amc_client.config` was an `AjaxModuleConnectorConfig` object once a non-empty body batch reached retry setup. A caller, generated fixture, or test double could replace `client.amc_client.config` with `None`, an arbitrary object, a dictionary, a string, or a boolean, and the retry helper would fail with incidental attribute errors such as `'dict' object has no attribute 'retry_batch_size'` before its existing retry-control validators could run.

This change validates the stored config object before reading `retry_batch_size` or `retry_max_retries`. Non-empty Site AMC retry batches now reject replaced config state with `ValueError("config must be AjaxModuleConnectorConfig")` before batch splitting or AMC request delegation. Empty body lists still return `()` without reading `client.amc_client`, explicit invalid retry controls are still rejected before the empty-batch shortcut, and valid retry-aware Site/Page/Forum/member/application workflows remain unchanged.

## Outcome

Retry-aware Site AMC callers now get deterministic config-object validation at the `Site.amc_request_with_retry(...)` boundary instead of lower-level attribute errors when nested AMC config state is replaced.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page source/file/revision/vote acquisition, forum reads, site member/application listing, recent changes, ListPages pagination, generated local fixtures, JSON/YAML adapters, migration tools, moderation tools, archival workflows, or local CI fixtures that may replace nested client state.

## Current Evidence

Local rollout-backed drafts establish `Site.amc_request_with_retry(...)` and AMC config state as practical shared infrastructure. [139-pr-skip-empty-amc-retry-batches.md](139-pr-skip-empty-amc-retry-batches.md) preserved empty retry batches without config reads, [394-pr-validate-site-amc-retry-controls.md](394-pr-validate-site-amc-retry-controls.md) validated explicit and config-derived retry values, [515-pr-validate-amc-config-object.md](515-pr-validate-amc-config-object.md) covered constructor-time AMC config object inputs, [520-pr-validate-amc-config-fields.md](520-pr-validate-amc-config-fields.md) covered config field construction, [522-pr-validate-amc-request-state-objects.md](522-pr-validate-amc-request-state-objects.md) covered raw `AjaxModuleConnectorClient.request(...)` stored request-state objects, [523-pr-validate-requestutil-config-object.md](523-pr-validate-requestutil-config-object.md) covered direct URL `RequestUtil.request(...)` config object state, [524-pr-validate-auth-login-config-object.md](524-pr-validate-auth-login-config-object.md) covered auth login config object state, and [525-pr-validate-site-lookup-config-object.md](525-pr-validate-site-lookup-config-object.md) covered direct site lookup config object state.

Those prior slices are not duplicates. Issue 139 covers the empty retry-batch no-op and explicit invalid-option precedence. Issue 394 validates retry values after a config-like object exists, but not whether the stored object itself is a real `AjaxModuleConnectorConfig`. Issues 515 and 520 validate construction surfaces. Issue 522 validates the lower-level raw AMC request boundary. Issues 523, 524, and 525 validate direct URL, auth login, and site lookup boundaries. This slice validates the retry-aware Site AMC helper after callers or fixtures replace `client.amc_client.config` before non-empty retry batch setup. No upstream issue was filed from this local workspace.

## Changes

- Reuse the Site module config-object validator before `Site.amc_request_with_retry(...)` reads retry defaults.
- Keep explicit `batch_size` and `max_retries` validation before empty-batch handling.
- Preserve empty non-explicit body batches returning `()` without reading `client.amc_client`.
- Convert affected valid test fixtures to use real `AjaxModuleConnectorConfig` objects instead of MagicMock config state.
- Add focused tests for replaced Site AMC retry config objects before request delegation.

## Type Of Change

- Input/state validation
- Site AMC retry preflight hardening
- Test fixture correction
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.amc_request_with_retry(...)` must reject replaced non-`AjaxModuleConnectorConfig` `client.amc_client.config` state before reading retry defaults or issuing AMC requests. |
| R2 | The rejection must use `ValueError("config must be AjaxModuleConnectorConfig")` rather than incidental attribute errors or retry-field diagnostics. |
| R3 | Invalid config replacements must not delegate to `client.amc_client.request`. |
| R4 | Empty body lists must still return `()` without requiring `client.amc_client`, while explicit invalid retry controls remain rejected before that empty-batch shortcut. |
| R5 | Existing valid Site AMC retry behavior and downstream Site/Page/Forum/member/application workflows must remain unchanged. |
| R6 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, Site AMC retry tests, site tests, adjacent tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Directly replacing `client.amc_client.config` with `None`, arbitrary objects, dictionaries, strings, or booleans raises before retry defaults are read. | `test_amc_request_with_retry_rejects_invalid_config_object_before_request` failed RED for five malformed replacements with old attribute errors, then passed GREEN. | Reading `.retry_batch_size` or `.retry_max_retries` on malformed config state rejects this local completion claim. | Site AMC retry preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | The raised error is `ValueError("config must be AjaxModuleConnectorConfig")`. | The focused GREEN test asserts that exact diagnostic for five malformed config replacements. | Returning `AttributeError`, `batch_size must be positive`, `max_retries must be non-negative`, or raw AMC diagnostics rejects this local completion claim. | Config object diagnostics | `tests/unit/test_site.py` |
| R3 | Invalid config replacements do not call `client.amc_client.request`. | The focused GREEN test asserts `mock_client.amc_client.request.assert_not_called()`. | Delegating to raw AMC request work, batch splitting under malformed config state, or silently defaulting replaced config rejects this local completion claim. | Site AMC retry side effects | `tests/unit/test_site.py` |
| R4 | Empty-body no-config behavior and explicit invalid-option precedence remain stable. | `TestSiteAmcRequest` passed 38 tests after the guard and fixture updates. | Reading `client.amc_client` for `site.amc_request_with_retry([])`, accepting explicit invalid controls on empty batches, or changing the empty return shape rejects this local completion claim. | Site AMC retry public boundary | `tests/unit/test_site.py` |
| R5 | Existing site and adjacent retry-aware workflows remain green. | `uv run pytest tests/unit/test_site.py -q` passed 256 tests; adjacent Site/Page/Forum/SiteMember/SiteApplication/AMC/RequestUtil suites passed 1420 tests; full unit passed 2468 tests. | Regressing valid batch splitting, partial failure tolerance, exhausted retry behavior, member/application retries, source/file/revision/vote acquisition, forum reads, raw AMC, or RequestUtil behavior rejects this local completion claim. | Site and adjacent workflows | `tests/unit` |
| R6 | No private material or live action is needed to prove the behavior. | All regressions use synthetic config replacements and local unit tests; the draft contains no raw credentials, cookies, auth JSON, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `08b5104 fix(site): validate amc retry config object state`.

- RED config-object tests: `uv run pytest tests/unit/test_site.py::TestSiteAmcRequest::test_amc_request_with_retry_rejects_invalid_config_object_before_request -q` failed 5 cases before the fix because `None`, arbitrary objects, dictionaries, strings, and booleans raised `AttributeError` while reading `retry_batch_size`.
- GREEN focused tests: the same focused command passed 5 tests after config-object preflight was added.
- `uv run pytest tests/unit/test_site.py::TestSiteAmcRequest -q` passed 38 tests.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` passed with 2 files left unchanged.
- `uv run pytest tests/unit/test_site.py -q` passed 256 tests.
- Initial adjacent run exposed one valid `SiteMember` test fixture that used MagicMock config state; the fixture was corrected to `AjaxModuleConnectorConfig`, and `uv run pytest tests/unit/test_site_member.py::TestSiteMemberGet::test_get_members_retries_transient_first_page_failures -q` passed.
- `uv run ruff format tests/unit/test_site.py tests/unit/test_site_member.py` passed with 2 files left unchanged.
- `uv run pyright src/wikidot/module/site.py tests/unit/test_site.py tests/unit/test_site_member.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_amc_client.py tests/unit/test_requestutil.py -q` passed 1420 tests.
- `uv run pytest tests/unit -q` passed 2468 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `site.amc_request_with_retry([{"moduleName": "Test"}])` raises `ValueError("config must be AjaxModuleConnectorConfig")` when `client.amc_client.config` is `None`, `object()`, `{}`, `"config"`, or `True`.
- Those malformed config replacements do not call `client.amc_client.request`.
- `site.amc_request_with_retry([])` still returns `()` without requiring `client.amc_client`.
- Explicit invalid `batch_size` and `max_retries` values remain rejected before empty-batch handling.
- Valid Site AMC retry batching, partial-success preservation, exhausted retry behavior, site member/application retries, page source/file/revision/vote acquisition, forum reads, raw AMC requests, direct URL RequestUtil requests, and adjacent site workflows remain unchanged.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with site AMC retry-control value validation. Mitigation: Issue 394 covers malformed values such as booleans, strings, floats, and negative retry counts; this slice covers the stored config object type before those value validators can run.
- Risk: This could be confused with empty retry-batch behavior. Mitigation: Issue 139 covers empty batches; this slice preserves empty non-explicit batches without config access and applies only to non-empty retry setup after explicit controls are validated.
- Risk: This could be confused with AMC constructor config validation. Mitigation: Issues 515 and 520 cover constructor inputs and field construction; this slice covers Site retry request-time nested state after replacement.
- Risk: This could be confused with raw AMC, RequestUtil, auth login, or site lookup config-object validation. Mitigation: Issues 522, 523, 524, and 525 cover other request boundaries; this slice covers the central retry-aware Site AMC helper.
- Risk: Rejecting replaced config objects may expose mocks that used bare MagicMock config state. Mitigation: valid retry-aware tests and callers should use a real `AjaxModuleConnectorConfig` or full client fixture when they expect real Site retry behavior.

## Out Of Scope

Changing config immutability, accepting mapping-based config objects, changing numeric timeout/retry/backoff validation, changing retry policy, changing batch splitting, changing partial-success semantics, changing `Site.from_unix_name(...)`, changing raw AMC request behavior, changing RequestUtil behavior, changing live Wikidot behavior, and upstream Issue/PR creation are outside this slice.

## Why This Matters

`Site.amc_request_with_retry(...)` is the central retry-aware batch helper beneath many browser-free read paths. When nested client state is malformed, the retry helper should identify the malformed config object before batch splitting or request delegation starts.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used retry-aware Site AMC batches for page source/file/revision/vote acquisition, forum reads, site member/application listing, recent changes, ListPages pagination, generated fixtures, and mocked clients.
- Existing drafts covered empty retry batches, retry-control values, config construction, raw AMC request-state validation, direct URL config-object validation, auth login config-object validation, and site lookup config-object validation, but did not validate replaced config objects at the central Site AMC retry helper boundary.
- The focused RED failures showed replaced config objects surfacing as attribute errors while `Site.amc_request_with_retry(...)` prepared retry defaults. The GREEN regression covers those replacements before request delegation can run.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
