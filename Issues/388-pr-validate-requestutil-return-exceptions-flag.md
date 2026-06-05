# PR Draft: Validate RequestUtil Return-Exceptions Flag

## Summary

`RequestUtil.request(client, method, urls, return_exceptions=...)` documents `return_exceptions` as a boolean, but malformed caller-provided values were accepted at the shared direct URL request boundary. Falsy malformed values such as `None` and `0` behaved like the default raising mode, while truthy malformed values such as `"false"` and `1` could silently switch the helper into exception-returning mode for GET/POST batches.

This change validates `return_exceptions` after HTTP method validation and before the empty-URL fast path, client config access, semaphore setup, header preparation, `httpx.AsyncClient` creation, or `asyncio.gather(...)` execution. Malformed values now raise `ValueError("return_exceptions must be a boolean")`. Existing valid empty GET/POST behavior, valid non-empty GET/POST behavior, retry handling, Wikidot header forwarding, and valid `return_exceptions=True` exception-returning behavior remain unchanged.

## Outcome

Direct URL request callers now get deterministic Python-side preflight validation for malformed exception-handling controls instead of accidental truthiness changing whether lower-level request failures are raised or returned.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using direct URL GET/POST helpers for user/profile lookup, direct page-ID probing, browser-free read pipelines, generated audit ledgers, migration scripts, archival tooling, moderation tooling, or other automation that may load request controls from JSON, YAML, CLI flags, spreadsheets, or environment variables.

## Current Evidence

Local rollout-backed drafts repeatedly identify `RequestUtil.request(...)` as a practical shared direct-read surface. Existing drafts [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md), [132-pr-reuse-cached-duplicate-page-ids.md](132-pr-reuse-cached-duplicate-page-ids.md), [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md), [138-pr-reuse-requestutil-async-client.md](138-pr-reuse-requestutil-async-client.md), [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md), [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md), and [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md) cover direct page-ID URL deduplication, user profile title fidelity, cached duplicate page-ID reuse, empty URL fast paths, per-batch AsyncClient reuse, profile ID diagnostics, username validation, and user lookup not-found flag validation.

Those prior slices are not duplicates. They covered empty URL batches, method validation precedence, AsyncClient reuse, direct page-ID/user profile callers, and valid `return_exceptions` preservation. They did not validate the boolean `return_exceptions` control before `RequestUtil.request(...)` branches into `asyncio.gather(...)`. This slice follows the boolean-control preflight pattern from [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md), [385-pr-validate-page-lookup-not-found-flag.md](385-pr-validate-page-lookup-not-found-flag.md), [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md), and [387-pr-validate-site-amc-return-exceptions-flag.md](387-pr-validate-site-amc-return-exceptions-flag.md), but applies it to the direct URL helper rather than the raw site AMC helper.

## Related Issue

Builds directly on [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md), [138-pr-reuse-requestutil-async-client.md](138-pr-reuse-requestutil-async-client.md), [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md), [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md), and [387-pr-validate-site-amc-return-exceptions-flag.md](387-pr-validate-site-amc-return-exceptions-flag.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `return_exceptions` in `RequestUtil.request(...)` after method validation and before empty URL handling.
- Reject malformed exception-handling controls with `ValueError("return_exceptions must be a boolean")`.
- Preserve invalid-method precedence: unsupported methods still raise `ValueError("Invalid method")` before other request options matter.
- Preserve valid empty GET/POST batches returning `[]` without requiring client config.
- Preserve valid non-empty GET/POST retry behavior, Wikidot header forwarding, non-retryable 4xx behavior, timeout/network retry behavior, per-batch `httpx.AsyncClient` reuse, and valid `return_exceptions=True` behavior.

## Type Of Change

- Input validation
- Public API behavior hardening
- Direct URL request exception-control preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `RequestUtil.request(..., return_exceptions=...)` must reject `None`, strings, integers, and other non-bool values with `ValueError("return_exceptions must be a boolean")` before empty URL handling or client config access. |
| R2 | Unsupported HTTP methods must continue to raise `ValueError("Invalid method")` before empty input or `return_exceptions` handling. |
| R3 | Valid empty `GET` and `POST` URL batches must still return `[]` without requiring `client.amc_client.config`. |
| R4 | Valid non-empty `GET` and `POST` request behavior must remain unchanged, including retry behavior, header forwarding, 4xx handling, timeout/network retry handling, and per-batch AsyncClient reuse. |
| R5 | Valid `return_exceptions=True` behavior must remain unchanged for returning request exceptions instead of raising them. |
| R6 | Adjacent user, client, page, and direct page-ID workflows must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, affected RequestUtil tests, adjacent tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed exception-handling controls fail before the empty-URL shortcut or client config access. | `TestRequestUtilEmpty.test_empty_urls_reject_non_bool_return_exceptions_before_client_config` failed RED for `None`, `"false"`, `0`, and `1` across `GET` and `POST` because malformed controls returned `[]` instead of raising, then passed GREEN after validation was added. | Treating `"false"` or `1` as truthy, treating `None` or `0` as falsy controls, returning `[]`, reading `client.amc_client.config`, creating an async client, executing requests, or raising an unrelated later error rejects this local completion claim. | Direct URL request preflight | `src/wikidot/util/requestutil.py`, `tests/unit/test_requestutil.py` |
| R2 | Invalid method precedence remains stable. | Existing `test_empty_urls_still_validate_method` passed after validation was added. | Returning `[]`, raising a return-exceptions validation error first, or accepting unsupported methods rejects this local completion claim. | Request method validation | `tests/unit/test_requestutil.py` |
| R3 | Valid empty GET/POST batches still no-op without requiring client config. | Existing `test_empty_get_urls_returns_empty_without_client_config` and `test_empty_post_urls_returns_empty_without_client_config` passed after validation was added. | Reading `client.amc_client.config`, creating request machinery, raising for valid empty batches, or returning a non-empty result rejects this local completion claim. | Empty direct URL batches | `tests/unit/test_requestutil.py` |
| R4 | Valid non-empty GET/POST request behavior remains stable. | `tests/unit/test_requestutil.py` passed 27 tests after validation was added. | Regressing successful GET/POST, retryable status handling, non-retryable 4xx handling, timeout retry, header forwarding, or one-client-per-batch behavior rejects this local completion claim. | Direct URL requests | `tests/unit/test_requestutil.py` |
| R5 | Valid `return_exceptions=True` behavior still returns exceptions. | Existing `TestRequestUtilGet.test_get_return_exceptions` passed in the focused GREEN run and full requestutil suite. | Raising instead of returning the `HTTPStatusError`, wrapping it incorrectly, or rejecting valid `True` rejects this local completion claim. | Direct URL exception mode | `tests/unit/test_requestutil.py` |
| R6 | Adjacent user, client, page, and direct page-ID behavior remains green. | `tests/unit/test_user.py tests/unit/test_client.py tests/unit/test_page.py tests/unit/test_requestutil.py` passed 282 tests, and full unit tests passed 1134 tests. | Regressing profile lookup, client accessors, direct page-ID probing, page detail acquisition, page source/revision/vote/file workflows, or RequestUtil callers rejects this local completion claim. | Adjacent workflows | affected user/client/page/requestutil tests |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic values and mocks. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `1c40e2a fix(requestutil): validate return-exceptions flag`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_requestutil.py::TestRequestUtilEmpty::test_empty_urls_reject_non_bool_return_exceptions_before_client_config` failed 8 selected tests before the fix because malformed GET/POST empty-batch controls returned `[]` instead of raising.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_requestutil.py::TestRequestUtilEmpty::test_empty_urls_reject_non_bool_return_exceptions_before_client_config tests/unit/test_requestutil.py::TestRequestUtilEmpty tests/unit/test_requestutil.py::TestRequestUtilGet::test_get_return_exceptions` passed 12 tests after adding boolean preflight.
- `.venv/bin/ruff format src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` left 2 files unchanged.
- `.venv/bin/python -m pytest -q tests/unit/test_requestutil.py` passed 27 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_user.py tests/unit/test_client.py tests/unit/test_page.py tests/unit/test_requestutil.py` passed 282 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1134 tests.
- `.venv/bin/ruff check src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed.
- `.venv/bin/ruff format --check src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed with 2 files already formatted.
- `.venv/bin/mypy src/wikidot/util/requestutil.py tests/unit/test_requestutil.py` passed with no issues in 2 source files.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy .` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `RequestUtil.request(object(), "GET", [], return_exceptions=None)`, `return_exceptions="false"`, `return_exceptions=0`, and `return_exceptions=1` raise `ValueError("return_exceptions must be a boolean")` before client config access.
- `RequestUtil.request(object(), "POST", [], return_exceptions=None)`, `return_exceptions="false"`, `return_exceptions=0`, and `return_exceptions=1` raise the same validation error before client config access.
- `RequestUtil.request(object(), "DELETE", [])` still raises `ValueError("Invalid method")`.
- `RequestUtil.request(object(), "GET", [])` and `RequestUtil.request(object(), "POST", [])` still return `[]` without requiring client config.
- Valid non-empty GET/POST requests still preserve retry behavior, header forwarding, timeout/network retry behavior, non-retryable 4xx handling, and one `httpx.AsyncClient` per request batch.
- Valid `return_exceptions=True` still returns `HTTPStatusError` objects for failed requests instead of raising them.
- Existing user/profile lookup, direct page-ID probing, page workflows, and client request-adjacent behavior remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `0` or `1` tightens behavior for callers that previously used integers as booleans. Mitigation: the documented API type is `bool`; accepting integer controls can hide configuration parsing mistakes and change exception behavior.
- Risk: Rejecting strings can expose CLI, environment, JSON, YAML, or spreadsheet parsing bugs. Mitigation: text configuration should parse `"true"`/`"false"` into real booleans before calling `RequestUtil.request(...)`.
- Risk: The change could be confused with empty URL batch behavior. Mitigation: Issues 137 and 138 already covered empty batches and AsyncClient reuse; this slice only validates the malformed exception-handling flag before those paths.
- Risk: The change could be confused with raw site AMC validation. Mitigation: Issue 387 covered `Site.amc_request(...)`; this slice applies to the separate direct URL helper.

## Dependencies

- Existing `RequestUtil.request(...)` remains the source of truth for retry-aware direct URL GET/POST batches.
- Existing user/profile lookup and direct page-ID probing remain the primary public callers covered by adjacent tests.
- Existing invalid-method validation remains the first preflight check.
- The validation is local to `src/wikidot/util/requestutil.py` and does not affect request URL construction, profile parsing, page-ID parsing, raw site AMC behavior, response parsing, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered direct URL `return_exceptions` flag validation path.

## Upstream-Safe Motivation

`RequestUtil.request(...)` is shared by direct URL read workflows such as profile lookup and page-ID probing. Since `return_exceptions` controls whether lower-level HTTP failures are raised or returned, malformed truthy strings and integer stand-ins should fail deterministically before request setup rather than silently changing exception behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established `RequestUtil.request(...)` as a practical shared surface through user/profile lookup, direct page-ID lookup, empty URL batches, cached duplicate page-ID behavior, and per-batch AsyncClient reuse.
- Existing RequestUtil drafts covered empty batches, method validation precedence, AsyncClient reuse, retry/header behavior, and direct caller behavior; they did not validate the caller-provided `return_exceptions` control.
- This slice only validates `return_exceptions` inputs for `RequestUtil.request(...)`. It does not change request URL construction, GET/POST retry policy, header forwarding, response parsing, profile lookup, page-ID probing, raw site AMC behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or user names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed exception-handling controls instead of coercing them. Callers that load this flag from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should resolve it into a real boolean before calling `RequestUtil.request(...)`.
