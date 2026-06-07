# PR Draft: Validate RequestUtil Method And URL Inputs

## Summary

`RequestUtil.request(client, method, urls, ...)` is documented as a direct URL GET/POST batch helper, but two caller-provided inputs were still validated only indirectly. Non-string `method` values reached `method.upper()` and failed with incidental `AttributeError`, while malformed `urls` containers or entries could be treated as an empty batch, reach client config access, or reach `httpx` type errors instead of failing at the wikidot.py request boundary.

This change validates `method` and `urls` before empty-batch handling, client config access, semaphore setup, header preparation, `httpx.AsyncClient` creation, or GET/POST execution. `method` must be a string and is still normalized to uppercase before the existing `GET`/`POST` allowlist. `urls` must be a list of strings. Valid empty lists still return `[]` without requiring client config, and existing valid GET/POST request behavior remains unchanged.

## Outcome

Direct URL request callers now get deterministic Python-side preflight validation for malformed method and URL-batch inputs instead of accidental attribute errors, empty-tuple no-ops, client-config access, or lower-level `httpx` type errors.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using direct URL GET/POST helpers for user/profile lookup, direct page-ID probing, generated audits, migration tools, moderation tools, archival workflows, browser-free automation, local fixtures, or config-driven scripts that may load method names and URL batches from JSON, YAML, CLI flags, spreadsheets, generated structures, or test doubles.

## Current Evidence

Local rollout-backed drafts repeatedly identify `RequestUtil.request(...)` as practical infrastructure. Existing drafts [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md), [138-pr-reuse-requestutil-async-client.md](138-pr-reuse-requestutil-async-client.md), [388-pr-validate-requestutil-return-exceptions-flag.md](388-pr-validate-requestutil-return-exceptions-flag.md), and [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md) cover direct page-ID URL deduplication, empty direct URL batches, per-batch `AsyncClient` reuse, exception-returning controls, and numeric request controls.

Those prior slices are not duplicates. Issue 137 preserves valid empty list behavior but does not validate the URL container type. Issue 388 validates `return_exceptions`, not `method` or `urls`. Issue 393 validates config-derived timeout/retry/concurrency values for non-empty batches, not direct caller method or URL-list inputs.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_request_method(...)` in `src/wikidot/util/requestutil.py`.
- Reject non-string methods with `ValueError("method must be a string")` before calling `.upper()`.
- Preserve the existing uppercase normalization and `ValueError("Invalid method")` diagnostic for unsupported string methods.
- Add `_validate_request_urls(...)`.
- Reject non-list URL containers and non-string URL entries with `ValueError("urls must be a list of strings")`.
- Keep valid empty URL lists as no-op batches that return `[]` without requiring client config.
- Add focused unit tests for malformed method values, malformed URL containers, and malformed URL entries.

## Type Of Change

- Input validation
- Public helper behavior hardening
- Direct URL request preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Non-string `method` values must raise `ValueError("method must be a string")` before URL handling or client config access. |
| R2 | Unsupported string methods must continue to raise `ValueError("Invalid method")`. |
| R3 | Non-list `urls` containers must raise `ValueError("urls must be a list of strings")` before empty-batch handling or client config access. |
| R4 | URL list entries must be strings and malformed entries must raise the same URL-list `ValueError` before client config access or `httpx` request setup. |
| R5 | `RequestUtil.request(object(), "GET", [])` and POST equivalents must still return `[]` without requiring client config. |
| R6 | Existing valid GET/POST behavior, header forwarding, retry behavior, `return_exceptions`, numeric config validation, and adjacent page/user/site workflows must remain unchanged. |
| R7 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private page/user data, raw response bodies, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, RequestUtil tests, adjacent direct URL/page/user/site tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `method=None`, `True`, `1`, and `object()` fail with a stable method-type `ValueError`. | `TestRequestUtilInvalidMethod.test_rejects_non_string_method_before_url_handling` failed RED with `.upper()` `AttributeError`, then passed GREEN after validation was added. | Calling `.upper()` on non-strings, accepting booleans or integers, returning `[]`, or reading client config rejects this local completion claim. | Direct URL method preflight | `src/wikidot/util/requestutil.py`, `tests/unit/test_requestutil.py` |
| R2 | Existing invalid string method behavior remains stable. | Existing `test_invalid_method_raises` passed after the guard. | Changing the unsupported-method diagnostic, accepting unsupported methods, or rejecting valid case-normalized methods rejects this local completion claim. | Direct URL method allowlist | `tests/unit/test_requestutil.py` |
| R3 | Tuple, string, dictionary, and arbitrary object URL containers fail before empty handling or client config access. | `TestRequestUtilUrlValidation.test_rejects_non_list_urls_before_client_config` failed RED with `DID NOT RAISE`, client config `AttributeError`, or `len(...)` `TypeError`, then passed GREEN after validation was added. | Treating `()` as a valid empty batch, iterating strings as URL characters, reading client config, or relying on `len(...)` errors rejects this local completion claim. | Direct URL batch preflight | `tests/unit/test_requestutil.py` |
| R4 | Lists containing `123`, `None`, `True`, or arbitrary objects fail before client config access or `httpx` setup. | `TestRequestUtilUrlValidation.test_rejects_non_string_url_entries_before_client_config` failed RED because malformed entries reached client config access, then passed GREEN after validation was added. | Coercing entries to strings, sending invalid `httpx` requests, or raising lower-level type errors rejects this local completion claim. | Direct URL entry preflight | `tests/unit/test_requestutil.py` |
| R5 | Valid empty list batches remain dependency-light no-ops. | Existing empty GET/POST tests passed in the RequestUtil suite. | Requiring `client.amc_client.config`, creating request machinery, raising for `[]`, or returning non-empty results rejects this local completion claim. | Empty direct URL batches | `tests/unit/test_requestutil.py` |
| R6 | Existing request and adjacent workflows remain green. | RequestUtil tests passed 99 tests, adjacent RequestUtil/user/page/client/site tests passed 675 tests, and full unit passed 2327 tests. | Regressing valid GET/POST success, header forwarding/suppression, retryable 5xx, non-retryable 4xx, timeout retry, return-exceptions behavior, numeric config validation, profile lookup, page-ID probing, client accessors, or site workflows rejects this local completion claim. | Direct URL behavior and callers | `tests/unit` |
| R7 | No private material or live action is needed to prove the behavior. | All regressions use unit-level synthetic values and mocks; the draft contains no raw credentials, cookies, auth JSON, rollout paths, or response bodies. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, RequestUtil and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `79fe87a fix(requestutil): validate method and url inputs`.

- RED method/URL tests: `uv run pytest tests/unit/test_requestutil.py::TestRequestUtilInvalidMethod::test_rejects_non_string_method_before_url_handling tests/unit/test_requestutil.py::TestRequestUtilUrlValidation -q` failed 12 cases before the fix with `.upper()` `AttributeError`, tuple `DID NOT RAISE`, client config `AttributeError`, and `len(...)` `TypeError`.
- GREEN focused tests: the same focused command passed 12 tests after method and URL-list validation was added.
- `uv run ruff format src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_requestutil.py -q` passed 99 tests.
- `uv run pytest tests/unit/test_requestutil.py tests/unit/test_user.py tests/unit/test_page.py tests/unit/test_client.py tests/unit/test_site.py -q` passed 675 tests.
- `uv run ruff check src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed.
- `uv run ruff format --check src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2327 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `RequestUtil.request(object(), None, [])`, `method=True`, `method=1`, and `method=object()` raise `ValueError("method must be a string")` before URL handling or client config access.
- `RequestUtil.request(object(), "DELETE", [])` still raises `ValueError("Invalid method")`.
- `RequestUtil.request(object(), "GET", ())`, `urls="https://example.com/test"`, `urls={"url": "https://example.com/test"}`, and `urls=object()` raise `ValueError("urls must be a list of strings")` before client config access.
- `RequestUtil.request(object(), "GET", [123])`, `[None]`, `[True]`, and `[object()]` raise the same URL-list validation error before client config access.
- `RequestUtil.request(object(), "GET", [])` and `RequestUtil.request(object(), "POST", [])` still return `[]` without requiring client config.
- Valid GET/POST request behavior, retry behavior, header forwarding, timeout handling, `return_exceptions`, and numeric config validation remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Rejecting tuple URL containers tightens behavior for callers that accidentally passed sequences. Mitigation: the public parameter is documented as `list[str]`, and rejecting malformed containers prevents empty-tuple no-ops from hiding generated config mistakes.
- Risk: Rejecting strings as URL containers can expose CLI, environment, JSON, YAML, or spreadsheet parsing bugs. Mitigation: callers should wrap individual URLs in a list before using the batch helper.
- Risk: This could be confused with Issue 137. Mitigation: Issue 137 preserves valid empty list behavior; this slice validates the `urls` container before the empty-list shortcut.
- Risk: This could be confused with Issue 388 or 393. Mitigation: those slices cover `return_exceptions` and numeric config controls; this slice covers direct `method` and `urls` inputs.

## Out Of Scope

URL grammar validation, URL scheme allowlists, host filtering changes, redirect policy, header forwarding rules, retry limits, backoff behavior, `return_exceptions`, numeric config validation, raw AMC request behavior, profile parsing, page-ID parsing, live Wikidot behavior, and accepting non-list URL sequence objects are outside this slice.

## Why This Matters

`RequestUtil.request(...)` is the direct URL batch executor beneath profile lookup and direct page probes. Method names and URL lists often come from generated queues or config adapters, so malformed shapes should fail deterministically before any client setup or remote request machinery starts.

## Rollout-Backed Notes

- Local rollout-backed work established `RequestUtil.request(...)` as practical infrastructure through profile lookup, direct page probing, empty URL batching, cached duplicate page-ID behavior, and per-batch `AsyncClient` reuse.
- Existing RequestUtil drafts covered empty batches, AsyncClient reuse, exception-returning controls, and numeric request controls, but did not validate direct method type or URL-batch shape.
- The focused RED failures showed malformed inputs reaching `.upper()`, empty-batch shortcuts, client config access, or `len(...)` instead of a stable wikidot.py-side input error.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or user names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
