# PR Draft: Validate AMC Client Return-Exceptions Flag

## Summary

`AjaxModuleConnectorClient.request(bodies, return_exceptions=...)` documents `return_exceptions` as a boolean, but malformed caller-provided values were accepted at the lower-level Ajax Module Connector client boundary. Falsy malformed values such as `None` and `0` behaved like the default raising mode for non-empty batches, while empty batches silently returned `()`; truthy malformed values such as `"false"` and `1` could switch the helper into exception-returning mode for non-empty batches.

This change validates `return_exceptions` before semaphore setup, site override resolution, `httpx.AsyncClient` creation, or `asyncio.gather(...)` execution. Malformed values now raise `ValueError("return_exceptions must be a boolean")`. Existing valid default/`False` behavior, valid `True` exception-returning behavior, request body token preservation, site override validation, retry behavior, response diagnostics, and wrapper-level behavior remain unchanged.

## Outcome

Raw AMC callers now get deterministic Python-side preflight validation for malformed exception-handling controls instead of accidental truthiness changing whether lower-level AMC failures are raised or returned.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using the raw Ajax Module Connector client directly or indirectly through site, page, forum, private-message, member, application, archival, generated-audit, migration, moderation, or browser-free automation workflows that may load request controls from JSON, YAML, CLI flags, spreadsheets, or environment variables.

## Current Evidence

Local rollout-backed drafts repeatedly identify raw AMC request behavior as a practical shared surface. Existing drafts [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md), [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md), [138-pr-reuse-requestutil-async-client.md](138-pr-reuse-requestutil-async-client.md), [139-pr-skip-empty-amc-retry-batches.md](139-pr-skip-empty-amc-retry-batches.md), [140-pr-skip-empty-site-amc-request-batches.md](140-pr-skip-empty-site-amc-request-batches.md), [387-pr-validate-site-amc-return-exceptions-flag.md](387-pr-validate-site-amc-return-exceptions-flag.md), and [388-pr-validate-requestutil-return-exceptions-flag.md](388-pr-validate-requestutil-return-exceptions-flag.md) cover AMC logging, token preservation, empty batches, retry-wrapper behavior, the site wrapper's exception flag, and the direct URL helper's exception flag.

Those prior slices are not duplicates. They covered raw AMC request safety around logging and token preservation, wrapper-level empty batches, retry-aware site AMC behavior, `Site.amc_request(..., return_exceptions=...)`, and `RequestUtil.request(..., return_exceptions=...)`. They did not validate the boolean `return_exceptions` control at the lower-level `AjaxModuleConnectorClient.request(...)` boundary before it reaches `asyncio.gather(...)`. This slice follows the boolean-control preflight pattern from [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md), [385-pr-validate-page-lookup-not-found-flag.md](385-pr-validate-page-lookup-not-found-flag.md), [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md), [387-pr-validate-site-amc-return-exceptions-flag.md](387-pr-validate-site-amc-return-exceptions-flag.md), and [388-pr-validate-requestutil-return-exceptions-flag.md](388-pr-validate-requestutil-return-exceptions-flag.md), but applies it to the raw Ajax client rather than the site wrapper or direct URL helper.

## Related Issue

Builds directly on [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md), [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md), [139-pr-skip-empty-amc-retry-batches.md](139-pr-skip-empty-amc-retry-batches.md), [140-pr-skip-empty-site-amc-request-batches.md](140-pr-skip-empty-site-amc-request-batches.md), [387-pr-validate-site-amc-return-exceptions-flag.md](387-pr-validate-site-amc-return-exceptions-flag.md), and [388-pr-validate-requestutil-return-exceptions-flag.md](388-pr-validate-requestutil-return-exceptions-flag.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `return_exceptions` in `AjaxModuleConnectorClient.request(...)` before request setup.
- Reject malformed exception-handling controls with `ValueError("return_exceptions must be a boolean")`.
- Preserve valid default/`False` behavior for raising AMC exceptions.
- Preserve valid `return_exceptions=True` behavior for returning exceptions in result tuples.
- Preserve request body token preservation, site override validation, request retry behavior, response parsing, status diagnostics, sensitive log masking, and wrapper-level behavior.

## Type Of Change

- Input validation
- Public API behavior hardening
- Raw Ajax Module Connector exception-control preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `AjaxModuleConnectorClient.request(..., return_exceptions=...)` must reject `None`, strings, integers, and other non-bool values with `ValueError("return_exceptions must be a boolean")` before request setup. |
| R2 | Valid default/`False` AMC request behavior must remain unchanged, including raising on AMC HTTP/status/response errors. |
| R3 | Valid `return_exceptions=True` behavior must remain unchanged for returning exceptions in the result tuple instead of raising them. |
| R4 | Existing request body handling must remain unchanged, including not mutating caller bodies and preserving explicit `wikidot_token7` values. |
| R5 | Existing request routing and diagnostics must remain unchanged, including site override validation, SSL/site URL selection, retry behavior, response parsing, status handling, and sensitive log masking. |
| R6 | Adjacent Ajax connector, client, site wrapper, and direct URL helper behavior must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, affected AMC client tests, adjacent tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed exception-handling controls fail before empty-batch request setup or HTTP work. | `TestAjaxModuleConnectorClientRequest.test_request_rejects_non_bool_return_exceptions_before_request` failed RED for `None`, `"false"`, `0`, and `1` because malformed controls were accepted and returned `()`, then passed GREEN after validation was added. | Treating `"false"` or `1` as truthy, treating `None` or `0` as falsy controls, returning `()`, creating request work, issuing HTTP requests, or raising an unrelated later error rejects this local completion claim. | Raw Ajax client preflight | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | Valid default raw AMC behavior still raises existing exception types. | Existing error, retry, invalid JSON, invalid status, no-permission, and max-retry tests in `tests/unit/test_amc_client.py` passed after validation was added. | Regressing exception type, retry count, JSON validation, Wikidot status handling, HTTP status handling, or response-data diagnostics rejects this local completion claim. | Raw Ajax request behavior | `tests/unit/test_amc_client.py` |
| R3 | Valid `return_exceptions=True` still returns exceptions in the result tuple. | Existing `TestAjaxModuleConnectorClientRequest.test_return_exceptions_mode` passed in the focused GREEN run and full AMC client suite. | Raising instead of returning `WikidotStatusCodeException`, wrapping it incorrectly, losing successful responses, or rejecting valid `True` rejects this local completion claim. | Raw Ajax exception mode | `tests/unit/test_amc_client.py` |
| R4 | Request body token handling remains stable. | Existing body mutation, explicit token, and header token tests in `tests/unit/test_amc_client.py` passed after validation was added. | Mutating caller dictionaries, overwriting explicit `wikidot_token7`, failing to use header cookie defaults, or leaking sensitive token values in logs rejects this local completion claim. | Request body preparation | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R5 | Request routing and diagnostics remain stable. | `tests/unit/test_amc_client.py` passed 37 tests after validation was added. | Regressing invalid site override validation, custom site request routing, SSL choice, retry/backoff behavior, response parsing, status handling, or sensitive log masking rejects this local completion claim. | Ajax connector request path | `tests/unit/test_amc_client.py` |
| R6 | Adjacent connector and wrapper behavior remains green. | `tests/unit/test_ajax.py tests/unit/test_client.py tests/unit/test_site.py tests/unit/test_requestutil.py tests/unit/test_amc_client.py` passed 227 tests, and full unit tests passed 1138 tests. | Regressing site AMC delegation, RequestUtil direct URL behavior, client accessors, Ajax helpers, or higher-level wrappers rejects this local completion claim. | Adjacent workflows | affected Ajax/client/site/requestutil tests |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic values and mocks. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `8585876 fix(ajax): validate return-exceptions flag`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_non_bool_return_exceptions_before_request` failed 4 selected tests before the fix because malformed empty-batch controls were accepted and returned `()` instead of raising.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_non_bool_return_exceptions_before_request tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_return_exceptions_mode` passed 5 tests after adding boolean preflight.
- `.venv/bin/python -m pytest -q tests/unit/test_amc_client.py` passed 37 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_ajax.py tests/unit/test_client.py tests/unit/test_site.py tests/unit/test_requestutil.py tests/unit/test_amc_client.py` passed 227 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1138 tests.
- `.venv/bin/ruff check src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed.
- `.venv/bin/ruff format --check src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed with 2 files already formatted.
- `.venv/bin/mypy src/wikidot/connector/ajax.py tests/unit/test_amc_client.py` passed with no issues in 2 source files.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy .` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `AjaxModuleConnectorClient(site_name="www").request([], return_exceptions=None)`, `return_exceptions="false"`, `return_exceptions=0`, and `return_exceptions=1` raise `ValueError("return_exceptions must be a boolean")` before HTTP requests are issued.
- `AjaxModuleConnectorClient.request(..., return_exceptions=False)` and the default call path still return successful responses and raise the same AMC HTTP/status/response exceptions on failures.
- `AjaxModuleConnectorClient.request(..., return_exceptions=True)` still returns a tuple containing both successful `httpx.Response` objects and exceptions for failed requests.
- Caller request body dictionaries are still not mutated, explicit `wikidot_token7` body values are still preserved, and header-cookie token defaults still work.
- Existing site override validation, custom site routing, SSL URL selection, retry behavior, response JSON validation, Wikidot status handling, and sensitive log masking remain unchanged.
- Existing `Site.amc_request(...)` and `RequestUtil.request(...)` behavior remains unchanged; those higher-level surfaces already have their own validation coverage from Issues 387 and 388.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `0` or `1` tightens behavior for callers that previously used integers as booleans. Mitigation: the documented API type is `bool`; accepting integer controls can hide configuration parsing mistakes and change exception behavior.
- Risk: Rejecting strings can expose CLI, environment, JSON, YAML, or spreadsheet parsing bugs. Mitigation: text configuration should parse `"true"`/`"false"` into real booleans before calling `AjaxModuleConnectorClient.request(...)`.
- Risk: The change could be confused with site wrapper validation. Mitigation: Issue 387 covered `Site.amc_request(...)`; this slice applies to the separate lower-level Ajax client.
- Risk: The change could be confused with direct URL helper validation. Mitigation: Issue 388 covered `RequestUtil.request(...)`; this slice applies only to raw Ajax Module Connector batches.

## Dependencies

- Existing `AjaxModuleConnectorClient.request(...)` remains the source of truth for raw Ajax Module Connector request execution.
- Existing site, page, forum, private-message, member, and application workflows continue to use their current wrappers and retry helpers.
- Existing `Site.amc_request(...)` and `RequestUtil.request(...)` validation remains separate and unchanged.
- The validation is local to `src/wikidot/connector/ajax.py` and does not affect request body construction, retry policy, response parsing, wrapper behavior, direct URL request behavior, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered raw Ajax client `return_exceptions` flag validation path.

## Upstream-Safe Motivation

`AjaxModuleConnectorClient.request(...)` is the lower-level batch executor beneath many raw Wikidot AMC workflows. Since `return_exceptions` controls whether lower-level request failures are raised or returned, malformed truthy strings and integer stand-ins should fail deterministically before request setup rather than silently changing exception behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established raw AMC request behavior as a practical shared surface through page, forum, private-message, member, application, and site workflows.
- Existing AMC drafts covered token preservation, sensitive log masking, empty batches, retry behavior, and wrapper/direct-URL exception controls; they did not validate the caller-provided `return_exceptions` control at `AjaxModuleConnectorClient.request(...)`.
- This slice only validates `return_exceptions` inputs for `AjaxModuleConnectorClient.request(...)`. It does not change request body construction, non-empty request execution, retry policy, response parsing, logging, site wrapper behavior, RequestUtil behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or user names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed exception-handling controls instead of coercing them. Callers that load this flag from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should resolve it into a real boolean before calling `AjaxModuleConnectorClient.request(...)`.
