# PR Draft: Validate Meta Tag Inputs Before Metadata Writes

## Summary

`Page.metas = ...`, `Page.set_metadata(metas=...)`, and `Site.page.publish(metas=...)` all document meta tags as `dict[str, str]`, but malformed values were not validated at the public API boundary. Non-dictionary inputs could leak raw Python errors after login and meta reads. Dictionaries with non-string keys or values could reach AMC request construction, send malformed `metaName` or `metaContent` payloads, or update local `_metas` with values outside the documented public shape.

This change validates meta tag inputs before login checks, AMC requests, page save/edit work, source verification, metadata batching, or local `_metas` mutation. Invalid meta tag input now raises stable `ValueError` messages: `metas must be a dictionary`, `metas keys must be strings`, or `metas values must be strings`.

## Outcome

Browser-free metadata and publish callers now get deterministic preflight validation for malformed meta tag payloads instead of partial write-side progress, raw container errors, or invalid local meta state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use direct page metadata APIs or `Site.page.publish(...)` for browser-free page publishing, audit metadata, migration scripts, source collection ledgers, and cleanup workflows.

## Current Evidence

Local rollout evidence repeatedly uses browser-free page publishing and metadata workflows that save source, verify source, update tags, set parent pages, write meta tags, and persist audit-friendly result records. Existing drafts [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [007-pr-batch-meta-tag-updates.md](007-pr-batch-meta-tag-updates.md), [011-pr-robust-meta-tag-parsing.md](011-pr-robust-meta-tag-parsing.md), [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [028-pr-publish-aggregate-status.md](028-pr-publish-aggregate-status.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), [249-pr-page-metas-setter-action-status-context.md](249-pr-page-metas-setter-action-status-context.md), [258-pr-publish-metadata-update-count.md](258-pr-publish-metadata-update-count.md), [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), [346-pr-validate-publish-visibility-controls.md](346-pr-validate-publish-visibility-controls.md), and [347-pr-validate-publish-source-normalizer.md](347-pr-validate-publish-source-normalizer.md) establish metadata writes as a practical write surface. Those slices covered meta parsing, batching, action status validation, parent preflight, publish ordering, visibility controls, source normalizer validation, and result ergonomics; they did not cover malformed `metas` input shapes.

## Related Issue

Builds directly on [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), and [249-pr-page-metas-setter-action-status-context.md](249-pr-page-metas-setter-action-status-context.md), which established batched metadata writes and response-status validation. It also follows the input-boundary pattern from [342-pr-validate-tag-list-inputs.md](342-pr-validate-tag-list-inputs.md), [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), [346-pr-validate-publish-visibility-controls.md](346-pr-validate-publish-visibility-controls.md), and [347-pr-validate-publish-source-normalizer.md](347-pr-validate-publish-source-normalizer.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a shared meta input validator for the documented `dict[str, str]` shape.
- Reject non-dictionary `metas` values with `ValueError("metas must be a dictionary")`.
- Reject non-string meta names with `ValueError("metas keys must be strings")`.
- Reject non-string meta contents with `ValueError("metas values must be strings")`.
- Apply validation to the `Page.metas` setter before login checks or AMC requests.
- Apply validation to `Page.set_metadata(metas=...)` before login checks, AMC requests, or local metadata mutation.
- Apply validation to `Site.page.publish(metas=...)` before login checks, page lookup, create/edit saves, post-save page-ID resolution, source refresh, metadata writes, or result creation.
- Preserve valid meta diffing, batch request construction, response status validation, local `_metas` updates, publish metadata delegation, source verification ordering, and `PagePublishResult` fields.

## Type Of Change

- Input validation
- Public API behavior hardening
- Write preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.set_metadata(metas=...)` must reject non-dictionary `metas` values with `ValueError("metas must be a dictionary")` before login checks, AMC requests, meta reads, or local `_metas` mutation. |
| R2 | `Page.set_metadata(metas=...)` must reject dictionaries with non-string values with `ValueError("metas values must be strings")` before login checks, AMC requests, meta reads, or local `_metas` mutation. |
| R3 | `Page.metas = ...` must reject dictionaries with non-string keys with `ValueError("metas keys must be strings")` before login checks, AMC requests, meta reads, or local `_metas` mutation. |
| R4 | `Site.page.publish(metas=...)` must reject malformed meta values before login checks, page lookup, save/edit work, post-save page-ID resolution, source refresh, metadata writes, or result creation. |
| R5 | Valid metadata and publish behavior must remain unchanged for meta diffing, batch request order, action status validation, parent/tag updates, source verification ordering, create/edit branching, visibility-control validation, and result fields. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent metadata/publish/page-write tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-dictionary `metas` fails with a stable `ValueError` before any metadata side effect. | `TestPageWriteMethods.test_set_metadata_rejects_invalid_metas_before_request` covers `metas=3` and passed after the fix. | Leaking raw container errors, calling login, fetching current metas, calling AMC, or changing `_metas` rejects this local completion claim. | Page metadata preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | A non-string meta value fails with a stable `ValueError` before any metadata side effect. | The same `set_metadata` test failed RED before the fix because an integer meta value reached AMC request construction and the mock exposed a raw `zip()` length `ValueError`; it passed GREEN after the fix. | Sending `metaContent=3`, accepting the value, coercing it, calling login, calling AMC, or changing `_metas` rejects this local completion claim. | Page metadata preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | A non-string meta key fails with a stable `ValueError` before any direct meta setter side effect. | `TestPageWriteMethods.test_metas_setter_rejects_invalid_metas_before_request` passed and asserts login and AMC were not called. | Sending a numeric `metaName`, accepting the key, coercing it, calling login, calling AMC, or changing `_metas` rejects this local completion claim. | Page metas setter preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Publish rejects malformed meta payloads before page save work. | `TestSitePageAccessor.test_publish_rejects_invalid_metas_before_save` failed RED before the publish preflight because no `ValueError` was raised, then passed GREEN after the fix. | Calling login, looking up a page, calling `Page.create_or_edit(...)`, editing an existing page, resolving page IDs, verifying source, writing metadata, or returning a result rejects this local completion claim. | Publish metadata preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R5 | Existing metadata and publish behavior remains green. | Focused metadata/publish tests passed 3 tests; `TestPageWriteMethods` plus `TestSitePageAccessor` passed 64 tests; adjacent page-write/publish tests passed 75 tests; full unit passed 932 tests. | Regressing valid meta diffing, request ordering, status validation, local cache updates, tags, parent clearing, publish create/edit, source verification, visibility controls, or result exports rejects this local completion claim. | Metadata and publish workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent metadata/publish/page-write tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `0f80126 fix(page): validate meta tag inputs`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_invalid_metas_before_request -q` failed before the fix because a non-string meta value reached AMC request construction and the focused mock surfaced raw `ValueError: zip() argument 2 is shorter than argument 1`.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_invalid_metas_before_request -q` passed 1 test after the `Page.set_metadata(...)` validation.
- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_invalid_metas_before_save -q` failed before the publish preflight because no `ValueError` was raised before the publish side-effect path.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_invalid_metas_before_save -q` passed 1 test after the publish preflight.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_invalid_metas_before_request tests/unit/test_page.py::TestPageWriteMethods::test_metas_setter_rejects_invalid_metas_before_request tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_invalid_metas_before_save -q` passed 3 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_site.py::TestSitePageAccessor -q` passed 64 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_site.py::TestSitePageAccessor -q` passed 75 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run --extra test pytest tests/unit -q` passed 932 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `Page.set_metadata(metas=3)` raises `ValueError("metas must be a dictionary")` before calling login, fetching current metas, sending AMC requests, or changing `_metas`.
- `Page.set_metadata(metas={"description": 3})` raises `ValueError("metas values must be strings")` before calling login, fetching current metas, sending AMC requests, or changing `_metas`.
- `page.metas = {3: "description"}` raises `ValueError("metas keys must be strings")` before calling login, sending AMC requests, or changing `_metas`.
- `Site.page.publish("new-page", metas={"description": 3})` raises `ValueError("metas values must be strings")` before calling login, page lookup, create/edit save work, post-save page-ID resolution, source verification, or metadata writes.
- Existing successful meta diffing, batch metadata requests, action status validation, local `_metas` cache updates, parent clearing, tag updates, publish create/edit branching, source verification ordering, and publish result fields remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Meta tags are write-path payloads. If caller configuration has the wrong shape, wikidot.py should reject it before a page save or metadata request can be attempted. Runtime validation keeps the documented `dict[str, str]` API honest, avoids malformed AMC payloads, and prevents invalid local `_metas` state without changing valid metadata batching or publish behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free publish and metadata flows that saved pages, verified source, updated tags, parents, and meta tags, and wrote audit ledgers.
- Existing local drafts covered meta parsing, retry-aware meta reads, batched meta writes, action status validation, parent input validation, publish metadata ordering, visibility controls, source-normalizer validation, and result ergonomics, but did not cover malformed meta tag input payloads.
- The focused RED failures showed non-string meta values reaching metadata write request construction and malformed publish meta payloads not being rejected at the high-level publish boundary.
- This slice only validates meta tag input shape; it does not change valid meta diffing, request bodies, response validation, source verification, visibility retry behavior, result fields, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, metadata values from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed meta tag inputs instead of coercing them. Callers that load meta tags from JSON, YAML, CLI flags, environment variables, or mixed-type configuration should normalize them into `dict[str, str]` before calling wikidot.py write helpers.
