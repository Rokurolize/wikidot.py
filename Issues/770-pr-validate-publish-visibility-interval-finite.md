# PR Draft: Validate Publish Visibility Interval Finite Values

## Summary

`Site.page.publish(...)` accepts `post_save_visibility_interval` to wait between post-save page ID visibility retries. Issues 346 and 408 made the visibility controls reject ordinary malformed types, invalid ranges, and booleans before save work starts. One numeric edge remained: Python `float("nan")` and `float("inf")` are `float` values, and the interval validator only checked `value < 0`. That let non-finite delay values pass the public publish preflight.

This change converts the interval once, requires `math.isfinite(...)`, and then applies the existing non-negative check. Valid finite intervals, including `0`, remain unchanged. `NaN` and positive infinity now fail with the existing `ValueError("post_save_visibility_interval must be non-negative")` diagnostic before login, page lookup, or save work starts.

## Outcome

Browser-free publishing no longer accepts non-finite post-save visibility wait intervals that can bypass validation or propagate into retry timing.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free publishing, generated page migration jobs, source verification, metadata synchronization, publication ledgers, or tests that load publish retry controls from Python objects, JSON/YAML adapters, CLI parsing, spreadsheets, or fixtures.

## Current Evidence

Local rollout-backed drafts repeatedly identify `Site.page.publish(...)` and post-save visibility handling as practical write-path infrastructure. Existing drafts cover the publish helper, source verification, metadata ordering, publish result ledgers, post-save visibility retries, post-save 404 context, visibility-control type/range validation, and boolean rejection.

This slice is not a duplicate of [346-pr-validate-publish-visibility-controls.md](346-pr-validate-publish-visibility-controls.md). Issue 346 covers ordinary malformed types and invalid range values for publish visibility controls.

This slice is not a duplicate of [408-pr-reject-boolean-publish-visibility-controls.md](408-pr-reject-boolean-publish-visibility-controls.md). Issue 408 covers Python booleans passing as integers at the same public publish boundary.

This slice is not a duplicate of [731-pr-validate-finite-http-numeric-controls.md](731-pr-validate-finite-http-numeric-controls.md) or [732-pr-validate-finite-amc-and-requestutil-numeric-controls.md](732-pr-validate-finite-amc-and-requestutil-numeric-controls.md). Those issues validate lower request-layer timeout, retry, and backoff controls, not the post-save publish visibility interval.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md), [226-pr-publish-visibility-404-context.md](226-pr-publish-visibility-404-context.md), [346-pr-validate-publish-visibility-controls.md](346-pr-validate-publish-visibility-controls.md), and [408-pr-reject-boolean-publish-visibility-controls.md](408-pr-reject-boolean-publish-visibility-controls.md), with analogous finite numeric-control precedent from [731-pr-validate-finite-http-numeric-controls.md](731-pr-validate-finite-http-numeric-controls.md) and [732-pr-validate-finite-amc-and-requestutil-numeric-controls.md](732-pr-validate-finite-amc-and-requestutil-numeric-controls.md).

## Changes

- Require `post_save_visibility_interval` to be finite after float conversion.
- Preserve the existing number type check for non-numeric values.
- Preserve the existing non-negative diagnostic for negative and non-finite intervals.
- Preserve valid finite interval behavior, including zero-delay retry tests.
- Add a regression test that `NaN` and positive infinity fail before login, page lookup, or save work.

## Type Of Change

- Input validation
- Public publish-boundary hardening
- Retry-control safety
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.page.publish(..., post_save_visibility_interval=float("nan"))` must raise before login, page lookup, or save work. |
| R2 | `Site.page.publish(..., post_save_visibility_interval=float("inf"))` must raise before login, page lookup, or save work. |
| R3 | Existing malformed-type and boolean diagnostics for visibility controls must remain unchanged. |
| R4 | Valid finite intervals, including `0`, must continue to preserve post-save visibility retry behavior. |
| R5 | Existing post-save 404 exhaustion and non-404 propagation behavior must remain unchanged. |
| R6 | Adjacent site, page, page-source, page-revision, page-file, and page-vote workflows must remain compatible. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | RED/GREEN, affected site tests, adjacent page workflow tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `float("nan")` raises `ValueError("post_save_visibility_interval must be non-negative")` before any save work. | The focused regression failed RED because execution continued into publish result construction; it passed after the finite check. | Calling `login_check`, `page.get`, `Page.create_or_edit`, returning a result, or raising an unrelated later error rejects this local completion claim. | Publish visibility preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | `float("inf")` raises the same validation error before any save work. | The focused regression failed RED for positive infinity and then passed after the finite check. | Sleeping forever, raising an `OverflowError`, calling save work, or constructing a result rejects this local completion claim. | Publish visibility preflight | focused test |
| R3 | Existing malformed-type and boolean visibility controls remain stable. | Focused GREEN included number-type and boolean visibility-control tests. | Changing established messages for strings, `None`, `True`, or `False` rejects this local completion claim. | Public publish API compatibility | focused tests |
| R4 | Zero interval still supports immediate retry behavior. | Focused GREEN included `test_publish_retries_post_save_visibility_before_returning_page_id`; broader site tests passed. | Regressing zero-delay retry or valid finite publish behavior rejects this local completion claim. | Publish retry workflow | site tests |
| R5 | Post-save 404 and non-404 behavior remains stable. | Focused GREEN included 404 exhaustion context and non-404 propagation tests. | Masking non-404 HTTP errors, dropping 404 context, or changing retry count rejects this local completion claim. | Publish visibility error handling | site tests |
| R6 | Adjacent page workflows remain compatible. | Adjacent site/page/page-constructor/page-source/page-revision/page-file/page-votes suite passed 1355 tests. | Regressing page publishing, page construction, source verification, revision, file, vote, or site workflows rejects this local completion claim. | Site and page modules | affected unit suites |
| R7 | No live site state or private material is needed. | The regression uses unit-level synthetic values, mocks, and no network actions. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | RED/GREEN, site tests, adjacent tests, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `c21549f fix(site): validate finite publish visibility interval`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_post_save_visibility_interval_must_be_finite_before_save -q --tb=short` failed before the fix for `NaN` and positive infinity because the validator did not reject them and execution continued into publish result construction.
- GREEN focused: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_post_save_visibility_interval_must_be_finite_before_save tests/unit/test_site.py::TestSitePageAccessor::test_publish_post_save_visibility_interval_must_be_number_before_save tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_boolean_visibility_controls_before_save tests/unit/test_site.py::TestSitePageAccessor::test_publish_retries_post_save_visibility_before_returning_page_id tests/unit/test_site.py::TestSitePageAccessor::test_publish_reports_context_when_post_save_visibility_404_exhausts tests/unit/test_site.py::TestSitePageAccessor::test_publish_surfaces_non_404_post_save_visibility_http_errors -q --tb=short` passed 10 tests.
- `uv run pytest tests/unit/test_site.py -q --tb=short` passed 365 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py -q --tb=short` passed 1355 tests.
- `uv run pytest tests/unit -q --tb=short` passed 3777 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no change-propagation, cognitive-load, duplication, accidental-complexity, dependency, domain-model, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker. Code pre-commit evidence reported `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.139.0"`, local clawpatch commit `d89ca91`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Site.page.publish(..., post_save_visibility_interval=float("nan"))` raises `ValueError("post_save_visibility_interval must be non-negative")` before login, page lookup, or `Page.create_or_edit(...)`.
- `Site.page.publish(..., post_save_visibility_interval=float("inf"))` raises the same validation error before login, page lookup, or `Page.create_or_edit(...)`.
- Existing type and boolean visibility-control validation messages remain unchanged.
- Valid finite intervals, including `0`, continue to support post-save page ID visibility retries.
- Existing post-save 404 exhaustion context and non-404 HTTP propagation remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A caller intentionally used positive infinity to mean "wait indefinitely" after publish. Mitigation: this field controls concrete `time.sleep(...)` retry timing; unbounded wait semantics should be represented by an explicit higher-level policy, not a non-finite float.
- Risk: Rejecting `NaN` exposes configuration parsing bugs from generated data or fixtures. Mitigation: `NaN` cannot produce meaningful wait behavior and already bypasses ordinary comparisons.
- Risk: This could be confused with Issue 346. Mitigation: Issue 346 covers ordinary types and range values; this slice covers non-finite floats that pass those checks.
- Risk: The same publish path is write-facing. Mitigation: the validation happens before login, page lookup, or save work, and the focused regression asserts that no save work starts.

## Dependencies

- `Site.page.publish(...)` remains the source of truth for browser-free publish orchestration.
- Existing post-save visibility retry logic continues to call `time.sleep(...)` only for valid finite positive intervals.
- Existing page source, metadata, tag, parent, and source-verification workflows remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-shape validation, result ergonomics, action/read boundaries, or measured complexity candidates outside this now-covered publish visibility interval validation.

## Upstream-Safe Motivation

The publish helper is a write-facing API. Its retry controls should reject non-finite numeric values before any login or save side effects can begin, matching the finite numeric-control policy already applied to lower request-layer retry and timeout settings.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: `NaN` and positive infinity were not rejected by the publish visibility interval validator.
- Existing local drafts covered publish orchestration, post-save visibility retry behavior, post-save 404 context, ordinary visibility-control validation, boolean rejection, and lower request-layer finite numeric controls; they did not cover non-finite publish visibility intervals.
- This slice only validates the public publish post-save visibility interval. It does not change request behavior, save payloads, source verification, metadata writes, tag writes, parent writes, page ID acquisition, result fields, cache behavior, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or user names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

This is a public publish retry-control validation fix. It preserves valid finite intervals and established diagnostics while preventing Python's non-finite floats from becoming publish retry state.
