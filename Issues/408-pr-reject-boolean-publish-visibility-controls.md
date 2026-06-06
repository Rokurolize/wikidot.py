# PR Draft: Reject Boolean Publish Visibility Controls

## Summary

`Site.page.publish(...)` validates `post_save_visibility_attempts` as an integer and `post_save_visibility_interval` as a number before page-write work begins, but those checks used plain Python numeric type tests. Because `bool` is an `int` subclass, `post_save_visibility_attempts=True` could become one retry and proceed into login/page lookup/save work, `post_save_visibility_attempts=False` was classified as a range error, and boolean intervals were accepted as `1.0` or `0.0` seconds.

This change treats boolean visibility controls as malformed numeric controls before login checks, page lookup, page creation/editing, metadata writes, source verification, or post-save page-ID resolution. Existing valid integer retry counts, valid integer/float intervals, range diagnostics, publish create/edit behavior, post-save visibility retry, source verification, metadata updates, and result fields remain unchanged.

## Outcome

Browser-free publish callers now get deterministic pre-save validation for boolean retry controls instead of accidental bool-to-number coercion or misleading range diagnostics.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.page.publish(...)` for browser-free page creation/editing with optional post-save visibility retry, source verification, and metadata writes.

## Current Evidence

Local rollout evidence repeatedly uses browser-free publish workflows that save source, verify saved source, update tags/parent/meta values, and rely on stable `PagePublishResult` audit fields. Existing drafts [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md), [226-pr-publish-visibility-404-context.md](226-pr-publish-visibility-404-context.md), [346-pr-validate-publish-visibility-controls.md](346-pr-validate-publish-visibility-controls.md), [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), [390-pr-validate-http-retry-boolean-controls.md](390-pr-validate-http-retry-boolean-controls.md), [395-pr-validate-http-request-timeouts.md](395-pr-validate-http-request-timeouts.md), and [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md) establish this as a practical write and configuration boundary. Those slices covered publish creation, visibility-control string/float/None validation, boolean write flags, low-level boolean controls, request timeout bool rejection, and returned-ID boolean rejection; they did not cover Python boolean values inside publish visibility numeric controls.

## Related Issue

Builds directly on [346-pr-validate-publish-visibility-controls.md](346-pr-validate-publish-visibility-controls.md), which introduced type validation for string, float, and `None` visibility controls. This slice preserves those diagnostics and adds the missing boolean exclusion for the same controls.

No upstream issue was filed from this local workspace.

## Changes

- Reject `post_save_visibility_attempts=True` and `False` with `ValueError("post_save_visibility_attempts must be an integer")`.
- Reject `post_save_visibility_interval=True` and `False` with `ValueError("post_save_visibility_interval must be a number")`.
- Preserve `post_save_visibility_attempts < 1` as `ValueError("post_save_visibility_attempts must be at least 1")` for non-boolean integers.
- Preserve `post_save_visibility_interval < 0` as `ValueError("post_save_visibility_interval must be non-negative")` for non-boolean numbers.
- Preserve valid publish create/edit, post-save page-ID retry, source verification, metadata update, parent/tag behavior, and result export behavior.

## Type Of Change

- Input validation
- Public API behavior hardening
- Write preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.page.publish(post_save_visibility_attempts=True or False)` must reject the value with `ValueError("post_save_visibility_attempts must be an integer")` before login checks, page lookup, save/edit work, metadata writes, source verification, or post-save page-ID resolution. |
| R2 | `Site.page.publish(post_save_visibility_interval=True or False)` must reject the value with `ValueError("post_save_visibility_interval must be a number")` before login checks, page lookup, save/edit work, metadata writes, source verification, or post-save page-ID resolution. |
| R3 | Existing non-boolean visibility-control validation must remain unchanged for valid integers/floats, malformed strings/`None`, retry counts below 1, and negative intervals. |
| R4 | Existing valid publish behavior must remain unchanged for create/edit branching, post-save page-ID retry, direct 404 context, non-404 propagation, source verification, metadata updates, parent/tag handling, and result fields. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent publish/page-write tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Boolean retry counts fail with the same integer-type diagnostic used for malformed non-integer retry counts. | New `TestSitePageAccessor.test_publish_rejects_boolean_visibility_controls_before_save` failed RED for `True` and `False`, then passed GREEN after `bool` exclusion was added. | Treating `True` as one retry, treating `False` as a range error, calling login, looking up a page, or calling `Page.create_or_edit(...)` rejects this local completion claim. | Publish visibility preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Boolean retry intervals fail with the same numeric-type diagnostic used for malformed non-numeric intervals. | New `TestSitePageAccessor.test_publish_rejects_boolean_visibility_controls_before_save` failed RED for `True` and `False`, then passed GREEN after `bool` exclusion was added. | Treating `True` as `1.0`, treating `False` as `0.0`, calling login, looking up a page, or calling `Page.create_or_edit(...)` rejects this local completion claim. | Publish visibility preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Existing visibility-control type/range checks remain compatible. | `TestSitePageAccessor` passed 40 tests, including the pre-existing string/float/None and range validation coverage. | Changing the message or behavior for string attempts, float attempts, string intervals, `None` intervals, retry counts below 1, or negative intervals rejects this local completion claim. | Publish visibility preflight | `tests/unit/test_site.py` |
| R4 | Publish workflow behavior remains green. | Adjacent publish/page-write tests passed 101 tests; full unit tests passed 1445 tests. | Regressing create/edit selection, source verification ordering, metadata gating, parent input validation, post-save retry success, 404 exhaustion context, non-404 propagation, or result exports rejects this local completion claim. | Browser-free publish workflow | `tests/unit/test_site.py`, `tests/unit/test_page.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, publish class tests passed, adjacent publish/page-write tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `418f8b5 fix(site): reject boolean publish visibility controls`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_boolean_visibility_controls_before_save -q` failed 4 tests before the fix. `post_save_visibility_attempts=True` did not raise, `post_save_visibility_attempts=False` raised the range diagnostic, and boolean intervals did not raise.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_boolean_visibility_controls_before_save -q` passed 4 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed 40 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageWriteMethods -q` passed 101 tests.
- `uv run ruff format src tests` left 81 files unchanged.
- `uv run --extra test pytest tests/unit -q` passed 1445 tests.
- `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_non_dict_body_before_request tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_rejects_later_non_dict_body_before_any_request -q` passed 2 tests after a local test-typing cleanup kept those existing malformed-input fixtures runtime-identical.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `Site.page.publish("new-page", post_save_visibility_attempts=True)` raises `ValueError("post_save_visibility_attempts must be an integer")` before calling login, page lookup, or `Page.create_or_edit(...)`.
- `Site.page.publish("new-page", post_save_visibility_attempts=False)` raises `ValueError("post_save_visibility_attempts must be an integer")` before calling login, page lookup, or `Page.create_or_edit(...)`.
- `Site.page.publish("new-page", post_save_visibility_interval=True)` raises `ValueError("post_save_visibility_interval must be a number")` before calling login, page lookup, or `Page.create_or_edit(...)`.
- `Site.page.publish("new-page", post_save_visibility_interval=False)` raises `ValueError("post_save_visibility_interval must be a number")` before calling login, page lookup, or `Page.create_or_edit(...)`.
- Existing successful post-save visibility retry behavior remains unchanged.
- Existing direct 404 exhaustion context and non-404 propagation behavior remain unchanged.
- Existing source verification, metadata update, result export, and parent input preflight tests remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Post-save visibility controls are write-path numeric controls. Boolean values are usually configuration mistakes from JSON, YAML, generated structures, or flag parsing, and should not silently become retry counts or sleep intervals. Rejecting them at the `publish(...)` boundary keeps publish behavior deterministic and prevents malformed controls from reaching page-write side effects.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free publish flows with source verification, metadata updates, post-save page-ID resolution, and audit-friendly publish result records.
- Existing local drafts covered publish creation, source verification, source normalization, post-save visibility retry, visibility failure context, result ergonomics, metadata ordering, parent fullname preflight, and visibility-control validation for strings/floats/`None`, but did not cover Python booleans passing through numeric checks.
- The focused RED failures showed both bool-coercion modes: `True` reached publish work and `False` was classified as a range error for retry counts, while interval booleans were accepted as numbers.
- The separate local commit `d12ad8d test(amc): type invalid request body fixtures` only typed existing malformed AMC request-body test fixtures as `Any` so `mypy src tests` could check the final tree. It does not change the Issue408 publish behavior and should not be mixed into an upstream publish-control PR unless the maintainer wants the test-typing cleanup too.
- This slice only rejects boolean visibility controls; it does not change valid publish saves, metadata writes, source verification, retry intervals, retry count semantics, direct 404 handling, non-404 handling, result fields, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed visibility-control types instead of coercing them. Callers that load publish retry controls from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should parse those values into real integers or numbers before calling `Site.page.publish(...)`.
