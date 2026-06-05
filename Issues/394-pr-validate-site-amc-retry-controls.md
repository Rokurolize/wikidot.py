# PR Draft: Validate Site AMC Retry Controls

## Summary

`Site.amc_request_with_retry(...)` is the retry-aware Ajax Module Connector batch helper used by page, forum, member, application, recent-changes, ListPages, and source-collection read paths, but its retry controls were only partially validated. Explicit non-positive numeric values were rejected, yet malformed types such as `batch_size=True`, `batch_size="2"`, `batch_size=1.5`, `max_retries=False`, `max_retries="1"`, or malformed `client.amc_client.config.retry_batch_size` / `retry_max_retries` defaults could reach comparison, `range(...)`, batch splitting, or retry-loop behavior instead of failing at the helper boundary.

This change validates explicit and config-default retry controls before any AMC request is issued. `batch_size` must be a non-bool positive integer. `max_retries` must be a non-bool non-negative integer. Empty body lists still return `()` without reading `client.amc_client`, while explicit invalid controls remain rejected before that empty-batch shortcut.

## Outcome

Retry-aware Site AMC callers now get deterministic wikidot.py-side validation for malformed batch and retry controls instead of accidental bool coercion, unstable `TypeError`, hidden zero/one retry shape changes, or malformed default config behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using retry-aware AMC batches for page sources, page files, page revisions, forum categories, forum threads, forum posts, site members, site applications, recent changes, ListPages, archival workflows, moderation tools, migration tools, or generated audits that may load retry settings from JSON, YAML, CLI flags, spreadsheets, environment variables, or mocked clients.

## Current Evidence

Local rollout-backed drafts repeatedly identify `Site.amc_request_with_retry(...)` as shared infrastructure. It backs retry-aware page source/file/revision/vote acquisition, forum category/thread/post reads, site member/application listing, recent changes, ListPages pagination, source iteration, partial-success preservation, and cached/deduplicated batch flows. [139-pr-skip-empty-amc-retry-batches.md](139-pr-skip-empty-amc-retry-batches.md) made empty retry batches no-op after explicit retry option validation. [387-pr-validate-site-amc-return-exceptions-flag.md](387-pr-validate-site-amc-return-exceptions-flag.md) validates the lower-level `Site.amc_request(..., return_exceptions=...)` flag used by this helper. [391-pr-validate-http-retry-numeric-controls.md](391-pr-validate-http-retry-numeric-controls.md), [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), and [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md) cover adjacent retry helpers, not the site-level batch/retry defaults used by `Site.amc_request_with_retry(...)`.

Those prior slices are not duplicates. Issue 139 validates empty-batch behavior and basic explicit numeric lower bounds, but it does not reject malformed types or config-default retry controls. Issue 387 validates a boolean exception-returning control in `Site.amc_request(...)`, not batch splitting or retry count controls. Issues 391, 392, and 393 validate shared HTTP, raw AMC, and direct URL RequestUtil numeric controls; this slice applies to the site-level retry batch helper that delegates to `Site.amc_request(..., return_exceptions=True)`.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [139-pr-skip-empty-amc-retry-batches.md](139-pr-skip-empty-amc-retry-batches.md), [387-pr-validate-site-amc-return-exceptions-flag.md](387-pr-validate-site-amc-return-exceptions-flag.md), [391-pr-validate-http-retry-numeric-controls.md](391-pr-validate-http-retry-numeric-controls.md), [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), and [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md).

## Changes

- Validate explicit `batch_size` before empty-batch handling and before AMC request work.
- Validate explicit `max_retries` before empty-batch handling and before AMC request work.
- Validate config-default `retry_batch_size` for non-empty retry batches before batch splitting.
- Validate config-default `retry_max_retries` for non-empty retry batches before retry loops.
- Reject booleans even though Python treats them as integers.
- Preserve `batch_size=1`, valid positive batch sizes, `max_retries=0`, valid positive retry counts, existing partial-success behavior, exhausted retry behavior, empty-batch no-config behavior, and downstream Page/Forum/Site workflows.

## Type Of Change

- Input validation
- Retry helper behavior hardening
- Public Site AMC helper safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.amc_request_with_retry(...)` must reject malformed explicit `batch_size` values before calling `client.amc_client.request`. |
| R2 | `Site.amc_request_with_retry(...)` must reject malformed config-default `retry_batch_size` values before calling `client.amc_client.request`. |
| R3 | `Site.amc_request_with_retry(...)` must reject malformed explicit `max_retries` values before calling `client.amc_client.request`. |
| R4 | `Site.amc_request_with_retry(...)` must reject malformed config-default `retry_max_retries` values before calling `client.amc_client.request`. |
| R5 | Empty body lists must still return `()` without reading `client.amc_client`, while explicit invalid retry controls remain rejected before that empty-batch shortcut. |
| R6 | Valid retry-aware Site AMC behavior must remain unchanged, including batch splitting, partial failure tolerance, exhausted retry handling, and downstream Page/Forum/Site workflows. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, affected Site tests, adjacent Page/Forum/Site tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Explicit `batch_size=True`, `False`, `"2"`, `0`, `-1`, and `1.5` raise `ValueError("batch_size must be positive, got ...")` before request work. | `test_amc_request_with_retry_rejects_invalid_explicit_batch_size_before_request` passed GREEN and asserts `client.amc_client.request` was not called. | Accepting booleans, coercing strings, treating floats as integers, or issuing an AMC request rejects this local completion claim. | Site AMC retry helper | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Config-default `retry_batch_size=None`, booleans, strings, zero, negative integers, and floats raise before request work. | `test_amc_request_with_retry_rejects_invalid_config_batch_size_before_request` passed GREEN and asserts no request was issued. | Letting malformed config reach `range(...)`, comparison `TypeError`, batch slicing, or AMC request work rejects this local completion claim. | Site AMC retry defaults | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Explicit `max_retries=True`, `False`, `"1"`, `-1`, and `1.5` raise `ValueError("max_retries must be non-negative, got ...")` before request work. | `test_amc_request_with_retry_rejects_invalid_explicit_max_retries_before_request` passed GREEN and asserts no request was issued. | Treating `False` as zero retries, `True` as one retry, coercing strings, accepting floats, or issuing a request rejects this local completion claim. | Site AMC retry helper | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R4 | Config-default `retry_max_retries=None`, booleans, strings, negative integers, and floats raise before request work. | `test_amc_request_with_retry_rejects_invalid_config_max_retries_before_request` passed GREEN and asserts no request was issued. | Letting malformed defaults reach `range(max_retries)`, comparison `TypeError`, or retry request work rejects this local completion claim. | Site AMC retry defaults | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R5 | Empty body behavior and explicit invalid-option precedence remain stable. | Existing empty-batch tests in `TestSiteAmcRequest` passed after validation was added. | Reading `client.amc_client` for empty body lists, allowing explicit invalid controls on empty body lists, or changing the empty return shape rejects this local completion claim. | Site AMC retry public boundary | `tests/unit/test_site.py` |
| R6 | Valid downstream Site/Page/Forum retry-aware workflows remain stable. | `tests/unit/test_site.py` passed 149 tests; adjacent Page/Forum/Site member/application tests passed 629 tests; full unit passed 1358 tests. | Regressing retry-aware source, file, revision, forum, member, application, recent-changes, ListPages, partial-success, or exhausted-retry behavior rejects this local completion claim. | Downstream workflows | affected unit suites |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic values and mocks. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, affected tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `17e9267 fix(site): validate amc retry controls`.

- RED tracer: `timeout 8s .venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteAmcRequest::test_amc_request_with_retry_rejects_invalid_config_batch_size_before_request` failed before the fix because config `retry_batch_size="2"` reached `batch_size <= 0` and raised `TypeError` instead of a stable preflight `ValueError`.
- GREEN tracer: `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteAmcRequest::test_amc_request_with_retry_rejects_invalid_config_batch_size_before_request` passed after adding retry-control validation.
- Focused GREEN: `timeout 12s .venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteAmcRequest` passed 33 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_site.py` passed 149 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_site_member.py tests/unit/test_site_application.py` passed 629 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1358 tests.
- `.venv/bin/python -m ruff check src/wikidot/module/site.py tests/unit/test_site.py` passed.
- `.venv/bin/python -m ruff format --check src/wikidot/module/site.py tests/unit/test_site.py` passed with 2 files already formatted.
- `.venv/bin/python -m mypy src/wikidot/module/site.py tests/unit/test_site.py` passed with no issues in 2 source files.
- `.venv/bin/python -m ruff check .` passed.
- `.venv/bin/python -m ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/python -m mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `site.amc_request_with_retry([{"moduleName": "Test"}], batch_size=True)`, `False`, `"2"`, `0`, `-1`, and `1.5` raise `ValueError` matching `batch_size must be positive` before issuing an AMC request.
- `site.amc_request_with_retry([{"moduleName": "Test"}])` rejects config-default `retry_batch_size=None`, booleans, strings, zero, negative integers, and floats before issuing an AMC request.
- `site.amc_request_with_retry([{"moduleName": "Test"}], max_retries=True)`, `False`, `"1"`, `-1`, and `1.5` raise `ValueError` matching `max_retries must be non-negative` before issuing an AMC request.
- `site.amc_request_with_retry([{"moduleName": "Test"}])` rejects config-default `retry_max_retries=None`, booleans, strings, negative integers, and floats before issuing an AMC request.
- Valid `batch_size=1`, positive integer batch sizes, `max_retries=0`, and positive integer retry counts remain accepted.
- `site.amc_request_with_retry([])` still returns `()` without requiring `client.amc_client`.
- Explicit invalid retry controls on an empty body list remain rejected before the empty-batch shortcut.
- Existing Site, Page, Forum, SiteMember, SiteApplication, raw AMC, direct URL RequestUtil, and shared HTTP helper tests remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting booleans tightens behavior for callers that accidentally relied on Python's `bool` subclassing `int`. Mitigation: retry and batch controls are numeric settings; accepting booleans hides configuration parsing mistakes.
- Risk: Rejecting strings can expose CLI, environment, JSON, YAML, spreadsheet, or generated-structure parsing bugs. Mitigation: textual configuration should parse retry controls into real integers before calling `Site.amc_request_with_retry(...)`.
- Risk: Rejecting `max_retries=False` changes a previously accepted zero-retry equivalent. Mitigation: callers should pass `0` when they want no retries; `False` is a boolean control mistake.
- Risk: This change could be confused with Issue 139. Mitigation: Issue 139 covered empty retry batches and basic explicit lower bounds; this slice covers malformed types and config-default retry controls.
- Risk: This change could be confused with Issues 391, 392, or 393. Mitigation: those slices covered shared HTTP, raw AMC, and direct URL RequestUtil numeric controls; this slice applies to `Site.amc_request_with_retry(...)`.

## Dependencies

- Existing `Site.amc_request_with_retry(...)` remains the source of truth for retry-aware Site AMC batch splitting and partial failure tolerance.
- Existing `Site.amc_request(...)` remains the lower-level AMC delegate used by the retry helper.
- Existing Page, Forum, SiteMember, SiteApplication, recent-changes, ListPages, and source-iterator flows continue to use their current retry-aware call sites.
- The validation is local to `src/wikidot/module/site.py` and does not affect URL construction, response parsing, raw AMC request execution, direct URL RequestUtil execution, shared HTTP retry helpers, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered Site AMC retry-control path.

## Upstream-Safe Motivation

`Site.amc_request_with_retry(...)` is the public partial-success batch helper beneath many Wikidot read workflows. Since `batch_size` determines batch splitting and `max_retries` determines retry-loop shape, booleans, strings, floats, `None`, negative values, and zero batch sizes should fail deterministically before request work.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established `Site.amc_request_with_retry(...)` as practical infrastructure through retry-aware page, forum, site, ListPages, and source-collection workflows.
- Existing retry-helper drafts covered empty body lists, raw `Site.amc_request(...)` return-exception validation, and adjacent raw AMC/HTTP/RequestUtil numeric controls; they did not validate site-level retry batch defaults or malformed explicit retry-control types.
- This slice only validates `Site.amc_request_with_retry(...)` batch and retry controls. It does not change request body construction, retry response mapping, partial-success semantics, exhausted retry behavior, response parsing, raw AMC behavior, direct URL RequestUtil behavior, shared HTTP helper behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or user names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed retry controls instead of coercing them. Callers that load these controls from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should resolve them into real integers before calling `Site.amc_request_with_retry(...)`.
