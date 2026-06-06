# PR Draft: Validate AMC Request Body Batches

## Summary

`AjaxModuleConnectorClient.request(...)` documents `bodies` as `list[dict[str, Any]]`, then creates one Ajax Module Connector request task per entry. Existing local slices validated exception controls, retry/timeout/concurrency controls, cookie names, cookie values, and non-cookie header values before request execution, but malformed request-body batches could still reach the asynchronous executor.

This change validates the raw AMC request-body batch before semaphore setup, async client creation, or HTTP request work. `bodies` must be a list, and every entry must be a dictionary. Invalid batch shapes now raise deterministic `ValueError` messages such as `bodies must be a list of dictionaries` or `bodies[1] must be a dictionary` before any request is issued. Valid request bodies, empty batches, caller body immutability, explicit `wikidot_token7` preservation, header-cookie token defaults, site override validation, retry policy, response parsing, and higher-level wrapper behavior remain unchanged.

## Outcome

Malformed raw AMC request batches now fail at the public request boundary instead of leaking internal `TypeError` from `**_body` expansion or allowing a partially valid batch to start HTTP work before a later malformed entry fails.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build raw AMC request batches from generated code, JSON/YAML config, CLI flags, spreadsheets, environment variables, sandbox tooling, or continuation ledgers before calling `AjaxModuleConnectorClient.request(...)`.

## Current Evidence

Local rollout-backed drafts already establish raw AMC request execution as a practical shared surface. [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md) covered request-body token precedence. [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md) covered the raw AMC exception-handling flag. [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md) covered timeout, retry, backoff, and semaphore controls. [398-pr-validate-amc-cookie-names.md](398-pr-validate-amc-cookie-names.md), [399-pr-validate-amc-cookie-values.md](399-pr-validate-amc-cookie-values.md), and [400-pr-validate-amc-header-values.md](400-pr-validate-amc-header-values.md) covered request-header state.

Those prior slices are not duplicates. Issue 050 preserves token values within valid body dictionaries. Issue 389 validates `return_exceptions`. Issue 392 validates numeric execution controls. Issues 398-400 validate header state. This slice validates the raw request-body batch shape itself before task creation.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md), [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md), [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), [398-pr-validate-amc-cookie-names.md](398-pr-validate-amc-cookie-names.md), [399-pr-validate-amc-cookie-values.md](399-pr-validate-amc-cookie-values.md), and [400-pr-validate-amc-header-values.md](400-pr-validate-amc-header-values.md).

## Changes

- Add one `_validate_amc_request_bodies(...)` helper in `src/wikidot/connector/ajax.py`.
- Reject non-list `bodies` values before request setup with `ValueError("bodies must be a list of dictionaries")`.
- Reject non-dictionary batch entries before request setup with `ValueError("bodies[<index>] must be a dictionary")`.
- Validate the whole batch before creating asynchronous request tasks, so a later malformed entry cannot allow earlier valid entries to issue HTTP requests.
- Preserve valid dictionary request bodies, empty batches, token defaults, explicit token preservation, caller body immutability, site override validation, retry policy, response parsing, and higher-level wrapper behavior.

## Type Of Change

- Input validation
- Raw AMC request-boundary hardening
- Batch preflight
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `AjaxModuleConnectorClient.request(...)` must reject non-list `bodies` values before semaphore setup, async client creation, or HTTP request work. |
| R2 | `AjaxModuleConnectorClient.request(...)` must reject non-dictionary body entries before semaphore setup, async client creation, or HTTP request work. |
| R3 | A malformed later entry in a batch must reject the entire batch before any earlier valid entry issues an HTTP request. |
| R4 | Existing valid raw AMC behavior must remain unchanged, including empty batches, successful requests, multiple requests, caller body immutability, explicit `wikidot_token7` preservation, header-cookie token defaults, site override validation, return-exceptions behavior, numeric-control validation, retry behavior, response parsing, cookie validation, and request-header value validation. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent AMC/ajax/site/RequestUtil/auth tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `client.request(None)`, `client.request({"moduleName": "TestModule"})`, and tuple input raise `ValueError("bodies must be a list of dictionaries")` and send no HTTP requests. | `TestAjaxModuleConnectorClientRequest.test_request_rejects_non_list_bodies_before_request` passed GREEN for all three inputs. | Iterating a dict/string/tuple as a batch, accepting non-list batches, issuing requests, or leaking lower-level errors rejects this local completion claim. | Raw AMC request preflight | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | `client.request([123])` raises `ValueError("bodies[0] must be a dictionary")` and sends no HTTP requests. | `TestAjaxModuleConnectorClientRequest.test_request_rejects_non_dict_body_before_request` failed RED with internal `TypeError`, then passed GREEN after body-batch validation. | Reaching `**_body`, returning a raw `TypeError`, creating async request work, or issuing HTTP requests rejects this local completion claim. | Raw AMC request preflight | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R3 | `client.request([{"moduleName": "ValidModule"}, 123])` raises `ValueError("bodies[1] must be a dictionary")` and sends no HTTP requests. | `TestAjaxModuleConnectorClientRequest.test_request_rejects_later_non_dict_body_before_any_request` passed GREEN. | Sending the first valid request before discovering the second invalid body rejects this local completion claim. | Raw AMC batch preflight | `tests/unit/test_amc_client.py` |
| R4 | Existing valid adjacent behavior remains stable. | `TestAjaxModuleConnectorClientRequest` passed 59 tests; `tests/unit/test_amc_client.py tests/unit/test_ajax.py` passed 137 tests; `tests/unit/test_site.py tests/unit/test_requestutil.py tests/unit/test_auth.py` passed 243 tests; full unit passed 1431 tests. | Breaking empty batches, successful raw requests, multiple requests, caller body immutability, explicit or header-derived token handling, custom site routing, return-exceptions, numeric controls, retry behavior, response parsing, cookie validation, header-value validation, site wrapper delegation, RequestUtil, or auth behavior rejects this local completion claim. | AMC/request utility workflows | affected unit suites |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic batch values, mocks, and local assertions. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private site data, source text from real sites, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `1d6dc9c fix(amc): validate request body batches`.

- RED tracer: `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_non_dict_body_before_request -q` failed before the fix because `client.request([123])` reached `request_body = {..., **_body}` and raised internal `TypeError: 'int' object is not a mapping`.
- GREEN tracer: `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_non_dict_body_before_request tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_non_list_bodies_before_request tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_later_non_dict_body_before_any_request -q` passed 5 tests.
- `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest -q` passed 59 tests.
- `uv run --extra test pytest tests/unit/test_amc_client.py tests/unit/test_ajax.py -q` passed 137 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_requestutil.py tests/unit/test_auth.py -q` passed 243 tests.
- `uv run --extra test pytest tests/unit -q` passed 1431 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 81 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files.
- `git diff --check` passed before the code commit.

Not run successfully: `pyright --version` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- Non-list `bodies` values are rejected with `ValueError("bodies must be a list of dictionaries")` before request setup.
- Non-dictionary entries are rejected with `ValueError("bodies[<index>] must be a dictionary")` before request setup.
- A batch containing a valid dictionary followed by a malformed entry sends no HTTP requests.
- Valid dictionary request batches continue to send the same request data and preserve caller-owned body dictionaries.
- Empty batches, explicit request-body `wikidot_token7`, header-cookie token defaults, site override validation, return-exceptions behavior, numeric-control validation, retry behavior, response parsing, cookie validation, header-value validation, Site wrapper delegation, RequestUtil, and auth behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting tuple batches could surprise callers that passed tuple-like iterables even though the public annotation and docs say `list[dict[str, Any]]`. Mitigation: the raw AMC executor constructs asynchronous request tasks from a caller-owned batch, and keeping the accepted shape explicit prevents strings, mappings, generators, and tuple-like accidental inputs from being interpreted as request bodies.
- Risk: Over-validating body dictionaries could reject valid module-specific payloads. Mitigation: this slice only validates the outer batch and per-entry dictionary shape; it does not require `moduleName`, action keys, or field-specific value types.
- Risk: Validation order could hide numeric config errors when both bodies and config are malformed. Mitigation: body shape is the public request payload boundary and should be valid before request execution controls matter; existing valid-body numeric-control tests still cover Issue 392 behavior.
- Risk: This change could be confused with token preservation. Mitigation: Issue 050 remains the source for token precedence, and this slice leaves dictionary body merging unchanged for valid inputs.
- Risk: This change could be confused with header validation. Mitigation: Issues 398-400 validate header state; this slice validates request body batch shape only.

## Dependencies

- Existing `AjaxModuleConnectorClient.request(...)` remains the source of truth for raw Ajax Module Connector request execution.
- Existing `AjaxRequestHeader.cookie` remains the source of truth for default `wikidot_token7` header-cookie values.
- Existing request-body merging remains the source of truth for explicit caller token preservation.
- Existing Site and RequestUtil wrappers continue to own their higher-level delegation behavior.
- The validation is local to `src/wikidot/connector/ajax.py` and does not alter URL routing, retry policy, response parsing, request body field semantics, RequestUtil host filtering, or live Wikidot behavior.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-body field-type checks, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered raw AMC request-body batch path.

## Upstream-Safe Motivation

Raw AMC request execution is a shared lower-level workflow for browser-free Wikidot operations. Since `AjaxModuleConnectorClient.request(...)` creates request tasks from `bodies` and merges each entry into the outbound request payload, malformed batch shapes should fail deterministically before async request setup. The fix is intentionally narrow: it validates only that `bodies` is a list and each entry is a dictionary, while preserving all module-specific body fields and existing request behavior for valid dictionaries.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established raw AMC request execution as shared infrastructure for `wikidot_token7` handling, site wrapper delegation, request utilities, login/session setup, public source fetches, and many module workflows.
- Existing drafts covered sensitive-log masking, token value preservation, return-exceptions validation, numeric request controls, cookie-name validation, cookie-value validation, and explicit request-header value validation; they did not validate the raw request-body batch shape before async task creation.
- This slice only validates `bodies` and its entries. It does not change token defaults, token masking, login credentials, session-cookie validation, logout cleanup, retry controls, URL routing, request-body field semantics, response parsing, RequestUtil behavior, Site wrapper behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The validation intentionally does not require `moduleName`: some raw AMC request bodies use action/event style payloads instead of module reads, and higher-level modules remain responsible for their own payload semantics.
