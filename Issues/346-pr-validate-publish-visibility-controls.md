# PR Draft: Validate Publish Visibility Controls Before Saving

## Summary

`Site.page.publish(...)` already validates `post_save_visibility_attempts >= 1` and `post_save_visibility_interval >= 0`, but it did not validate their types. String inputs such as `post_save_visibility_attempts="2"` or `post_save_visibility_interval="0"` leaked raw Python comparison `TypeError`. Float retry counts such as `post_save_visibility_attempts=1.5` could pass the existing range check and reach the write path before failing later when the post-save page-ID resolver tried to use the count as a `range(...)` argument.

This change validates publish visibility controls before login checks, page lookup, create/edit saves, metadata updates, source verification, or post-save page-ID resolution begins. Invalid controls now raise stable `ValueError` messages at the high-level publish API boundary.

## Outcome

Browser-free publish callers now get deterministic preflight validation for malformed post-save visibility controls instead of raw comparison errors or failures that can occur after a page save has already been attempted.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.page.publish(...)` for browser-free page creation/editing with optional post-save visibility retry, source verification, and metadata writes.

## Current Evidence

Local rollout evidence repeatedly uses browser-free publish workflows that save source, verify saved source, update tags/parent/meta values, and then need reliable audit fields from `PagePublishResult`. Existing drafts [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md), [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md), [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [204-pr-publish-source-verification-site-context.md](204-pr-publish-source-verification-site-context.md), [226-pr-publish-visibility-404-context.md](226-pr-publish-visibility-404-context.md), [257-pr-publish-source-verification-status.md](257-pr-publish-source-verification-status.md), [258-pr-publish-metadata-update-count.md](258-pr-publish-metadata-update-count.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), and [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md) establish this as a practical publish/write surface. Those slices covered publish creation, source verification, visibility retry behavior, contextual visibility failures, result ergonomics, and parent input preflight; they did not cover non-integer or non-numeric visibility-control types.

## Related Issue

Builds directly on [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md) and [226-pr-publish-visibility-404-context.md](226-pr-publish-visibility-404-context.md), which established the retry controls and the post-save page-ID resolution failure behavior. This slice preserves that behavior and adds pre-save input validation for the controls.

No upstream issue was filed from this local workspace.

## Changes

- Validate `post_save_visibility_attempts` as an integer before any publish side effects.
- Reject non-integer retry counts with `ValueError("post_save_visibility_attempts must be an integer")`.
- Preserve the existing `post_save_visibility_attempts < 1` message: `ValueError("post_save_visibility_attempts must be at least 1")`.
- Validate `post_save_visibility_interval` as a numeric value before any publish side effects.
- Reject non-numeric intervals with `ValueError("post_save_visibility_interval must be a number")`.
- Preserve the existing `post_save_visibility_interval < 0` message: `ValueError("post_save_visibility_interval must be non-negative")`.
- Preserve valid integer retry counts, valid integer/float intervals, post-save retry behavior, source verification ordering, metadata ordering, and `PagePublishResult` fields.

## Type Of Change

- Input validation
- Public API behavior hardening
- Write preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.page.publish(post_save_visibility_attempts=...)` must reject non-integer retry counts with `ValueError("post_save_visibility_attempts must be an integer")` before login checks, page lookup, save/edit work, metadata writes, source verification, or post-save page-ID resolution. |
| R2 | `Site.page.publish(post_save_visibility_interval=...)` must reject non-numeric retry intervals with `ValueError("post_save_visibility_interval must be a number")` before login checks, page lookup, save/edit work, metadata writes, source verification, or post-save page-ID resolution. |
| R3 | Existing range checks must remain unchanged for valid numeric types: retry attempts below 1 still raise `ValueError("post_save_visibility_attempts must be at least 1")`, and negative intervals still raise `ValueError("post_save_visibility_interval must be non-negative")`. |
| R4 | Existing valid publish behavior must remain unchanged for create/edit branching, post-save page-ID retry, direct 404 context, non-404 propagation, source verification, metadata updates, and result fields. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent publish/page-write tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | String and float retry counts fail with a stable `ValueError` before any publish side effect. | New `TestSitePageAccessor.test_publish_post_save_visibility_attempts_must_be_integer_before_save` failed RED before the fix with raw `TypeError` for `"2"` and passed GREEN after it. | Leaking `TypeError`, accepting `"2"`, accepting `1.5`, coercing values, calling login, looking up a page, or calling `Page.create_or_edit(...)` rejects this local completion claim. | Publish visibility preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | String and `None` retry intervals fail with a stable `ValueError` before any publish side effect. | New `TestSitePageAccessor.test_publish_post_save_visibility_interval_must_be_number_before_save` failed RED before the fix with raw `TypeError` for `"0"` and passed GREEN after it. | Leaking `TypeError`, accepting non-numeric intervals, coercing strings, calling login, looking up a page, or calling `Page.create_or_edit(...)` rejects this local completion claim. | Publish visibility preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Existing range validation remains compatible. | The helper preserves the previous messages and adjacent publish tests passed 21 tests. | Changing the message or behavior for `post_save_visibility_attempts < 1` or `post_save_visibility_interval < 0` rejects this local completion claim. | Publish visibility preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R4 | Publish workflow behavior remains green. | `TestSitePageAccessor` passed 21 tests; adjacent publish/page-write tests passed 71 tests; full unit passed 928 tests. | Regressing create/edit selection, source verification ordering, metadata gating, parent input validation, post-save retry success, 404 exhaustion context, non-404 propagation, or result exports rejects this local completion claim. | Browser-free publish workflow | `tests/unit/test_site.py`, `tests/unit/test_page.py` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, publish class tests passed, adjacent publish/page-write tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `441d1a5 fix(site): validate publish visibility controls`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_post_save_visibility_attempts_must_be_integer_before_save tests/unit/test_site.py::TestSitePageAccessor::test_publish_post_save_visibility_interval_must_be_number_before_save -q` failed before the fix. `post_save_visibility_attempts="2"` and `post_save_visibility_interval="0"` leaked raw comparison `TypeError` from the existing range checks.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_post_save_visibility_attempts_must_be_integer_before_save tests/unit/test_site.py::TestSitePageAccessor::test_publish_post_save_visibility_interval_must_be_number_before_save -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed 21 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageWriteMethods -q` passed 71 tests.
- `uv run ruff format src tests` reformatted 1 file and left 79 files unchanged.
- `uv run --extra test pytest tests/unit -q` passed 928 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `Site.page.publish("new-page", post_save_visibility_attempts="2")` raises `ValueError("post_save_visibility_attempts must be an integer")` before calling login, page lookup, or `Page.create_or_edit(...)`.
- `Site.page.publish("new-page", post_save_visibility_attempts=1.5)` raises `ValueError("post_save_visibility_attempts must be an integer")` before calling login, page lookup, or `Page.create_or_edit(...)`.
- `Site.page.publish("new-page", post_save_visibility_interval="0")` raises `ValueError("post_save_visibility_interval must be a number")` before calling login, page lookup, or `Page.create_or_edit(...)`.
- `Site.page.publish("new-page", post_save_visibility_interval=None)` raises `ValueError("post_save_visibility_interval must be a number")` before calling login, page lookup, or `Page.create_or_edit(...)`.
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

Post-save visibility controls are write-path preflight values. If they are malformed, callers should learn that before a page save can be attempted. Rejecting malformed controls at the `publish(...)` boundary keeps publish behavior deterministic and avoids write-side partial progress followed by a local type error.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free publish flows with source verification, metadata updates, post-save page-ID resolution, and audit-friendly publish result records.
- Existing local drafts covered publish creation, source verification, source normalization, post-save visibility retry, visibility failure context, result ergonomics, metadata ordering, and parent fullname preflight, but did not cover malformed visibility control types.
- The focused RED failures showed string visibility controls leaking raw `TypeError`; the new retry-count test also covers a float value so it cannot pass preflight and fail after save work begins.
- This slice only validates publish visibility control types; it does not change valid publish saves, metadata writes, source verification, retry intervals, retry count semantics, direct 404 handling, non-404 handling, result fields, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed visibility control types instead of coercing them. Callers that load publish retry controls from CLI arguments, environment variables, or config files should parse those values into integers or numbers before calling `Site.page.publish(...)`.
