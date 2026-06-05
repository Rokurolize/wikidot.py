# PR Draft: Validate Publish Source Normalizer Before Saving

## Summary

`Site.page.publish(..., verify_source=True, source_normalizer=...)` accepted any non-`None` value until after the page had already been created or edited, the saved page ID had been resolved, and the saved source had been fetched. If a caller passed a non-callable value such as `source_normalizer="strip"`, the publish workflow could reach the write path and then fail with raw Python `TypeError: 'str' object is not callable`.

This change validates `source_normalizer` at the high-level publish boundary when source verification is requested. Non-callable values now raise `ValueError("source_normalizer must be callable or None")` before login checks, page lookup, create/edit saves, post-save page-ID resolution, source refresh, metadata updates, or source normalization begins.

## Outcome

Browser-free publish callers now get deterministic preflight validation for malformed source-verification normalizers instead of partial write-side progress followed by a local callable error.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.page.publish(...)` for browser-free page creation/editing with optional source verification, source normalization, post-save visibility retry, and metadata writes.

## Current Evidence

Local rollout evidence repeatedly uses browser-free publish workflows that save source, verify saved source, normalize source comparisons, update tags/parent/meta values, and record audit-friendly `PagePublishResult` fields. Existing drafts [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md), [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md), [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [204-pr-publish-source-verification-site-context.md](204-pr-publish-source-verification-site-context.md), [226-pr-publish-visibility-404-context.md](226-pr-publish-visibility-404-context.md), [257-pr-publish-source-verification-status.md](257-pr-publish-source-verification-status.md), [258-pr-publish-metadata-update-count.md](258-pr-publish-metadata-update-count.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), and [346-pr-validate-publish-visibility-controls.md](346-pr-validate-publish-visibility-controls.md) establish this as a practical publish/write surface. Those slices covered publish creation, source verification, callable source normalization, source-before-metadata ordering, visibility retry behavior, visibility-control preflight, contextual visibility failures, result ergonomics, and parent input preflight; they did not cover non-callable `source_normalizer` values.

## Related Issue

Builds directly on [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md), which added the caller-supplied normalizer hook, and on [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), which established that source verification failures should stop metadata writes. This slice preserves callable normalizer behavior and adds pre-save validation for malformed normalizer configuration when source verification is requested.

No upstream issue was filed from this local workspace.

## Changes

- Validate `source_normalizer` as callable when `verify_source=True` and the argument is not `None`.
- Reject non-callable source normalizers with `ValueError("source_normalizer must be callable or None")`.
- Perform that validation before login checks, page lookup, create/edit saves, post-save page-ID resolution, source refresh, metadata updates, or source normalization begins.
- Preserve exact source comparison when `source_normalizer` is omitted.
- Preserve caller-supplied callable normalizer behavior for source verification.
- Preserve the existing no-verification publish path; `source_normalizer` remains unused when `verify_source=False`.

## Type Of Change

- Input validation
- Public API behavior hardening
- Write preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.page.publish(..., verify_source=True, source_normalizer=...)` must reject non-callable non-`None` normalizers with `ValueError("source_normalizer must be callable or None")` before login checks, page lookup, save/edit work, post-save page-ID resolution, source refresh, metadata writes, or source normalization. |
| R2 | Existing callable `source_normalizer` behavior must remain unchanged: the callable is applied symmetrically to fetched and submitted source when source verification is requested. |
| R3 | Existing publish behavior with `verify_source=False` must remain unchanged; the normalizer argument is still unused when source verification is skipped. |
| R4 | Existing valid publish behavior must remain unchanged for create/edit branching, post-save page-ID retry, visibility-control validation, parent input validation, source verification ordering, metadata updates, and result fields. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent publish/page-write tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A string normalizer fails with a stable `ValueError` before any publish side effect. | New `TestSitePageAccessor.test_publish_rejects_non_callable_source_normalizer_before_save` failed RED before the fix with raw `TypeError: 'str' object is not callable` after the create path had been reached, and passed GREEN after it. | Leaking `TypeError`, accepting `"strip"`, calling login, looking up a page, calling `Page.create_or_edit(...)`, resolving the saved page ID, refreshing source, or writing metadata rejects this local completion claim. | Publish source-verification preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Callable normalizer behavior remains green. | Existing `TestSitePageAccessor.test_publish_verifies_source_with_custom_normalizer` passed as part of the 22-test publish accessor run. | Changing symmetric normalization, exact comparison fallback, `source_matches`, or mismatch exception behavior rejects this local completion claim. | Publish source verification | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | The new validation is scoped to source verification. | The implementation gates the callable check on `verify_source` before the publish side-effect path. | Tightening no-verification publish calls or invoking a normalizer when verification is skipped rejects this local completion claim. | Publish source-verification preflight | `src/wikidot/module/site.py` |
| R4 | Publish workflow behavior remains green. | `TestSitePageAccessor` passed 22 tests; adjacent publish/page-write tests passed 72 tests; full unit passed 929 tests. | Regressing create/edit selection, post-save visibility retry, visibility-control validation, parent input validation, source verification ordering, metadata gating, 404 exhaustion context, non-404 propagation, or result exports rejects this local completion claim. | Browser-free publish workflow | `tests/unit/test_site.py`, `tests/unit/test_page.py` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, publish class tests passed, adjacent publish/page-write tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `2d99584 fix(site): validate publish source normalizer`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_non_callable_source_normalizer_before_save -q` failed before the fix with raw `TypeError: 'str' object is not callable` after the publish create path had been reached.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_non_callable_source_normalizer_before_save -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed 22 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageWriteMethods -q` passed 72 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run --extra test pytest tests/unit -q` passed 929 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `Site.page.publish("new-page", verify_source=True, source_normalizer="strip")` raises `ValueError("source_normalizer must be callable or None")` before calling login, page lookup, `Page.create_or_edit(...)`, post-save page-ID resolution, `Page.refresh_source()`, or metadata writes.
- `Site.page.publish(..., verify_source=True, source_normalizer=callable)` still applies the callable to both fetched and submitted source before comparing.
- `Site.page.publish(..., verify_source=True, source_normalizer=None)` still performs exact source comparison.
- `Site.page.publish(..., verify_source=False)` behavior remains unchanged; the normalizer argument is unused when verification is skipped.
- Existing source verification, metadata update, post-save visibility retry, visibility-control preflight, result export, and parent input preflight tests remain green.
- The new test uses unit-level code only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`source_normalizer` is a source-verification hook on a write-path helper. If a caller configures that hook incorrectly, the high-level publish API should reject the configuration before a page save can be attempted. Validating callable-ness at the boundary keeps browser-free publishing deterministic while preserving caller-owned normalization policy.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free publish flows with custom source verification, metadata updates, post-save page-ID resolution, and audit-friendly publish result records.
- Existing local drafts covered publish creation, source verification, callable source normalization, source-before-metadata ordering, post-save visibility retry, visibility-control validation, visibility failure context, result ergonomics, metadata ordering, and parent fullname preflight, but did not cover malformed non-callable normalizers.
- The focused RED failure showed a string normalizer leaking raw `TypeError` after the publish create path had already been reached.
- This slice only validates malformed source normalizers when source verification is requested; it does not change valid publish saves, metadata writes, source refresh, callable normalization, skipped verification, retry intervals, retry count semantics, direct 404 handling, non-404 handling, result fields, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed normalizers instead of coercing them. Callers that want string-named normalization policies should resolve those names to actual callables before calling `Site.page.publish(...)`.
