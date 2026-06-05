# PR Draft: Validate Site AMC Return-Exceptions Flag

## Summary

`Site.amc_request(bodies, return_exceptions=...)` documents `return_exceptions` as a boolean, but malformed caller-provided values were accepted at the raw site-scoped Ajax Module Connector boundary. Falsy malformed values such as `None` and `0` behaved like the default raising mode, while truthy malformed values such as `"false"` and `1` could silently switch the helper into exception-returning mode.

This change validates `return_exceptions` before the empty-batch shortcut and before delegation to `client.amc_client.request(...)`. Malformed values now raise `ValueError("return_exceptions must be a boolean")`. Existing valid default/`False` behavior, valid `True` behavior, empty-batch behavior, and retry-wrapper behavior remain unchanged.

## Outcome

Site AMC callers now get deterministic Python-side preflight validation for malformed exception-handling controls instead of accidental truthiness changing whether lower-level request failures are raised or returned.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using raw site-scoped AMC calls, retry-aware collection helpers, browser-free read pipelines, generated audit ledgers, migration scripts, archival tooling, moderation tooling, or other automation that may load request controls from JSON, YAML, CLI flags, spreadsheets, or environment variables.

## Current Evidence

Local rollout-backed drafts repeatedly identify site-scoped AMC request behavior as a practical shared surface. Existing drafts [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [038-pr-retry-first-listpages-fetch.md](038-pr-retry-first-listpages-fetch.md), [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [139-pr-skip-empty-amc-retry-batches.md](139-pr-skip-empty-amc-retry-batches.md), and [140-pr-skip-empty-site-amc-request-batches.md](140-pr-skip-empty-site-amc-request-batches.md) cover retry-aware AMC use, empty-batch handling, and raw site AMC delegation behavior.

Those prior slices are not duplicates. They covered request retry routing, partial-success preservation, retry option validation, and empty raw AMC batches. They did not validate the boolean `return_exceptions` control before `Site.amc_request(...)` branches on it. This slice follows the boolean-control preflight pattern from [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md), [385-pr-validate-page-lookup-not-found-flag.md](385-pr-validate-page-lookup-not-found-flag.md), and [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md), but applies it to the central raw site AMC exception-handling flag.

## Related Issue

Builds directly on [139-pr-skip-empty-amc-retry-batches.md](139-pr-skip-empty-amc-retry-batches.md), [140-pr-skip-empty-site-amc-request-batches.md](140-pr-skip-empty-site-amc-request-batches.md), [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md), [385-pr-validate-page-lookup-not-found-flag.md](385-pr-validate-page-lookup-not-found-flag.md), and [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `return_exceptions` in `Site.amc_request(...)` before empty-batch handling.
- Reject malformed exception-handling controls with `ValueError("return_exceptions must be a boolean")`.
- Preserve valid empty-batch no-op behavior for both `False` and `True`.
- Preserve valid non-empty delegation, site name forwarding, SSL forwarding, overload return types, and retry-wrapper calls that pass `return_exceptions=True`.
- Preserve adjacent site, page, forum, Ajax, and retry-aware collection workflows.

## Type Of Change

- Input validation
- Public API behavior hardening
- Site AMC exception-control preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.amc_request(..., return_exceptions=...)` must reject `None`, strings, integers, and other non-bool values with `ValueError("return_exceptions must be a boolean")` before empty-batch handling or `client.amc_client` access. |
| R2 | Valid empty `Site.amc_request([])` and `Site.amc_request([], return_exceptions=True)` behavior must remain unchanged and return `()` without reading `client.amc_client`. |
| R3 | Valid non-empty default/`False` raw AMC delegation must remain unchanged. |
| R4 | Valid `return_exceptions=True` behavior used by `Site.amc_request_with_retry(...)` must remain unchanged for retry-aware partial-success workflows. |
| R5 | Adjacent site, page, forum, Ajax, and retry-aware collection behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, affected site AMC tests, adjacent tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed exception-handling controls fail before the empty-batch shortcut or client access. | `TestSiteAmcRequest.test_amc_request_rejects_non_bool_return_exceptions_before_empty_batch` failed RED for `None`, `"false"`, `0`, and `1` by returning `()` instead of raising, then passed as part of the `TestSiteAmcRequest` GREEN run after validation was added. | Treating `"false"` or `1` as truthy, treating `None` or `0` as falsy controls, returning an empty tuple, touching `client.amc_client`, delegating to the AMC client, or raising an unrelated later error rejects this local completion claim. | Raw site AMC preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Valid empty batches still no-op without requiring an AMC client. | Existing `test_amc_request_empty_bodies_returns_empty_without_client_request` passed for both valid `False` and valid `True`. | Reading `client.amc_client`, calling `client.amc_client.request(...)`, returning a non-empty result, or raising for valid empty batches rejects this local completion claim. | Raw site AMC empty input | `tests/unit/test_site.py` |
| R3 | Valid non-empty default delegation remains stable. | Existing `test_amc_request_delegates_to_client` passed and still asserts request body forwarding, site name forwarding, and SSL forwarding. | Changing delegated arguments, skipping the raw AMC client, or changing valid default exception behavior rejects this local completion claim. | Raw site AMC delegation | `tests/unit/test_site.py` |
| R4 | Retry-aware valid `True` calls remain stable. | `tests/unit/test_site.py`, adjacent Ajax/forum/page suites, and full unit tests passed after validation was added. | Breaking `amc_request_with_retry(...)`, partial-success retries, exhausted retry handling, or exception-returning AMC calls rejects this local completion claim. | Retry-aware site AMC | affected site/page/forum tests |
| R5 | Adjacent behavior remains green. | `tests/unit/test_ajax.py tests/unit/test_forum_category.py tests/unit/test_page.py` passed 250 tests, and full unit tests passed 1126 tests. | Regressing Ajax request behavior, page collection flows, forum category flows, or retry-aware page/forum reads rejects this local completion claim. | Adjacent workflows | affected adjacent tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic objects and mocks. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/forum content, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d197562 fix(site): validate amc return-exceptions flag`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteAmcRequest::test_amc_request_rejects_non_bool_return_exceptions_before_empty_batch` failed 4 selected tests before the fix because malformed controls were accepted by the empty-batch path and returned `()`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteAmcRequest` passed 9 tests after adding boolean preflight.
- `.venv/bin/ruff format src/wikidot/module/site.py tests/unit/test_site.py` reformatted 1 file and left 1 file unchanged.
- `.venv/bin/python -m pytest -q tests/unit/test_site.py` passed 125 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_ajax.py tests/unit/test_forum_category.py tests/unit/test_page.py` passed 250 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1126 tests.
- `.venv/bin/ruff check src/wikidot/module/site.py tests/unit/test_site.py` passed.
- `.venv/bin/ruff format --check src/wikidot/module/site.py tests/unit/test_site.py` passed with 2 files already formatted.
- `.venv/bin/mypy src/wikidot/module/site.py tests/unit/test_site.py` passed with no issues in 2 source files.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy .` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `site.amc_request([], return_exceptions=None)`, `return_exceptions="false"`, `return_exceptions=0`, and `return_exceptions=1` raise `ValueError("return_exceptions must be a boolean")` before empty-batch handling or AMC client access.
- `site.amc_request([])` still returns `()` without reading `client.amc_client`.
- `site.amc_request([], return_exceptions=True)` still returns `()` without reading `client.amc_client`.
- Valid non-empty default raw AMC calls still delegate the body list, `False`, `site.unix_name`, and `site.ssl_supported` to `client.amc_client.request(...)`.
- Retry-aware calls that use valid `return_exceptions=True` remain green.
- Existing Ajax, site, page, forum, and retry-aware collection behavior remains unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private page/forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `0` or `1` tightens behavior for callers that previously used integers as booleans. Mitigation: the documented API type is `bool`; accepting integer controls can hide configuration parsing mistakes and change exception behavior.
- Risk: Rejecting strings can expose CLI, environment, JSON, YAML, or spreadsheet parsing bugs. Mitigation: text configuration should parse `"true"`/`"false"` into real booleans before calling `Site.amc_request(...)`.
- Risk: The change could be confused with the empty-batch fast path. Mitigation: Issue 140 already covered empty valid batches; this slice only validates the malformed exception-handling flag before that shortcut.
- Risk: The change could be confused with retry option validation. Mitigation: `amc_request_with_retry(...)` batch-size and max-retry validation remains unchanged; this slice only validates the raw helper's `return_exceptions` control.

## Dependencies

- Existing `Site.amc_request(...)` remains the source of truth for raw site-scoped AMC delegation.
- Existing `Site.amc_request_with_retry(...)` remains the source of truth for retry-aware partial-success handling and continues to pass valid `return_exceptions=True`.
- Existing `_validate_page_bool_field(...)` supplies the same strict bool contract and message shape used by adjacent site/page controls.
- The validation is local to `src/wikidot/module/site.py` and does not affect request body construction, response parsing, user lookup, page lookup, page writes, forum parsing, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered raw site AMC `return_exceptions` flag validation path.

## Upstream-Safe Motivation

`return_exceptions` controls a central error-handling branch for raw site AMC calls. Since retry-aware helpers intentionally use valid `True` to preserve partial successes, malformed truthy strings and integer stand-ins should fail deterministically before request work rather than silently changing whether exceptions are raised or returned.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established `Site.amc_request(...)` and `Site.amc_request_with_retry(...)` as practical shared surfaces through retry-aware site reads, page reads, forum reads, ListPages reads, empty-batch behavior, partial-success preservation, and duplicate request handling.
- Existing AMC drafts covered retry routing, empty batches, response parsing, batch splitting, and higher-level caller behavior; they did not validate the caller-provided `return_exceptions` control on the raw site AMC helper.
- This slice only validates `return_exceptions` inputs for `Site.amc_request(...)`. It does not change request body construction, non-empty delegation, retry policy, response parsing, logging, exception conversion, page behavior, forum behavior, user lookup, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or forum names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed exception-handling controls instead of coercing them. Callers that load this flag from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should resolve it into a real boolean before calling `Site.amc_request(...)`.
