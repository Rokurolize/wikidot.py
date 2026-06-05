# PR Draft: Validate Parent Fullname Inputs

## Summary

`Page.set_parent(...)`, `Page.set_metadata(parent_fullname=...)`, and `Site.page.publish(parent_fullname=...)` all document parent page names as `str | None`, where `None` and `""` intentionally clear the parent. Before this change, non-string values were not handled as a clear input boundary. In the batched `set_metadata(...)` path, a non-string value such as `3` was coerced to `None`, so it could be submitted as a parent clear. In the direct `set_parent(...)` path, the invalid value could flow into request construction and response handling. In the high-level publish helper, the invalid parent value could survive until after save/edit work.

This change rejects non-string, non-`None` parent inputs with `ValueError("parent_fullname must be a string or None")` before login checks, page saves, metadata requests, or local parent-state mutation.

## Outcome

Browser-free parent updates and publish workflows now fail early for malformed parent-name inputs instead of turning a caller bug into a remote parent clear or a later unrelated exception.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free publishing or metadata workflows to set or clear page parents.

## Current Evidence

Local rollout evidence repeatedly uses browser-free publish and metadata workflows that save source, verify source, set tags, set parent pages, and write audit metadata. Existing drafts [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), [246-pr-page-direct-metadata-action-status-context.md](246-pr-page-direct-metadata-action-status-context.md), and [265-pr-page-empty-parent-clear-normalization.md](265-pr-page-empty-parent-clear-normalization.md) establish parent metadata as a practical write surface. Those slices covered batching, status validation, save ordering, and empty-string clear normalization; they did not cover non-string parent-name inputs.

## Related Issue

Builds on [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), [246-pr-page-direct-metadata-action-status-context.md](246-pr-page-direct-metadata-action-status-context.md), and [265-pr-page-empty-parent-clear-normalization.md](265-pr-page-empty-parent-clear-normalization.md). This slice preserves the documented clear semantics for `None` and `""`; it only rejects values outside `str | None`.

No upstream issue was filed from this local workspace.

## Changes

- Add a shared parent-name input validator used by direct parent updates, batched metadata updates, and publish preflight.
- Reject non-string, non-`None` parent values with a stable `ValueError`.
- Validate `Site.page.publish(parent_fullname=...)` before login, page lookup, create/edit, visibility resolution, source verification, or metadata writes.
- Preserve `None` parent clears and empty-string parent clears.
- Preserve successful parent set, batched metadata, and publish behavior.

## Type Of Change

- Input validation
- Write-boundary hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.set_parent(...)` must reject non-string, non-`None` parent inputs with `ValueError("parent_fullname must be a string or None")` before login checks or AMC requests. |
| R2 | `Page.set_metadata(parent_fullname=...)` must reject non-string, non-`None` parent inputs with the same `ValueError` before login checks, AMC requests, or local parent-state mutation. |
| R3 | `Site.page.publish(parent_fullname=...)` must reject non-string, non-`None` parent inputs with the same `ValueError` before login checks, page lookup, create/edit, source verification, metadata writes, or result creation. |
| R4 | Existing parent clear semantics must remain unchanged: `None` and `""` still submit `parentName=""` and leave local `parent_fullname is None` after a successful action. |
| R5 | Existing successful parent set, batched metadata update, publish metadata delegation, source verification failure ordering, and result fields must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent metadata/publish tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct non-string parent input fails before login or request construction. | New `TestPageWriteMethods.test_set_parent_rejects_non_string_parent_before_request` failed RED before the fix and passed GREEN after it. | Sending `parentName=3`, raising a later request/status exception, calling login, or mutating `parent_fullname` rejects this local completion claim. | Direct parent write | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Batched non-string parent input fails before login, AMC batching, or local state mutation. | New `TestPageWriteMethods.test_set_metadata_rejects_non_string_parent_before_request` failed RED before the fix and passed GREEN after it. | Coercing the value to a parent clear, issuing a metadata request, raising an unrelated `zip(...)`/response exception, or mutating local parent state rejects this local completion claim. | Batched metadata write | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Publish non-string parent input fails before any save/edit workflow begins. | New `TestSitePageAccessor.test_publish_rejects_non_string_parent_before_save` failed RED before the fix and passed GREEN after it. | Calling login, page lookup, `Page.create_or_edit(...)`, edit, source verification, or metadata writes before rejecting the value rejects this local completion claim. | High-level publish workflow | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R4 | Parent clear behavior remains compatible. | Existing `set_parent(None)`, `set_parent("")`, `set_metadata(parent_fullname=None)`, and `set_metadata(parent_fullname="")` tests passed. | Breaking `None` or empty-string clears, changing the remote clear payload, or leaving local `parent_fullname == ""` after success rejects this local completion claim. | Parent clear semantics | `tests/unit/test_page.py` |
| R5 | Existing metadata and publish behavior remains green. | Adjacent parent/metadata/publish tests passed 9 tests; targeted write/publish classes passed 58 tests; full unit passed 921 tests. | Regressing metadata request order, tag serialization, meta diffing, source verification ordering, publish result fields, or successful parent setting rejects this local completion claim. | Page metadata and publish workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level mocks only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed 921 tests, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `8973e61 fix(page): validate parent fullname inputs`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_rejects_non_string_parent_before_request tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_non_string_parent_before_request -q` failed before the fix because the direct path continued into AMC response handling and the batched path continued into request handling instead of stable input validation.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_rejects_non_string_parent_before_request tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_non_string_parent_before_request tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_non_string_parent_before_save -q` passed 3 tests.
- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_non_string_parent_before_save -q` failed before the publish preflight fix because no `ValueError` was raised before the save path.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_success tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_clear tests/unit/test_page.py::TestPageWriteMethods::test_set_parent_empty_string_clears_local_parent tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_batches_tags_parent_and_metas tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_can_clear_parent tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_empty_parent_string_clears_local_parent tests/unit/test_site.py::TestSitePageAccessor::test_publish_edits_existing_page_sets_metadata_and_verifies_source tests/unit/test_site.py::TestSitePageAccessor::test_publish_creates_missing_page_without_optional_steps tests/unit/test_site.py::TestSitePageAccessor::test_publish_skips_metadata_when_source_verification_fails -q` passed 9 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_site.py::TestSitePageAccessor -q` passed 58 tests.
- `uv run --extra test pytest tests/unit -q` passed 921 tests.
- `uv run ruff format src tests` reformatted 1 file before final checks.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `Page.set_parent(3)` raises `ValueError("parent_fullname must be a string or None")` before login checks, AMC requests, or local parent mutation.
- `Page.set_metadata(parent_fullname=3)` raises the same `ValueError` before login checks, AMC requests, or local parent mutation.
- `Site.page.publish(parent_fullname=3)` raises the same `ValueError` before login checks, page lookup, create/edit, visibility resolution, source verification, or metadata writes.
- `Page.set_parent(None)`, `Page.set_parent("")`, `Page.set_metadata(parent_fullname=None)`, and `Page.set_metadata(parent_fullname="")` keep clearing the parent successfully.
- Successful parent set, metadata batch, publish delegation, source verification failure ordering, and publish result fields remain unchanged.
- The new tests use unit-level mocks only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Parent-page updates are part of browser-free publishing and metadata workflows. The API already defines a meaningful clear operation with `None` and `""`; other object types should not be accepted as implicit clears. Failing before any save or metadata request keeps caller bugs from becoming remote parent changes.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used parent metadata as part of browser-free publish workflows that save source, verify source, update tags, set parent pages, and write metadata.
- Existing local drafts covered parent clear normalization and action response validation but intentionally preserved parent clear semantics for `None` and `""`.
- The focused RED failures showed non-string parent inputs were not rejected at the boundary.
- This slice only validates parent fullname input type; it does not change parent name syntax, empty-string clear behavior, metadata request order, tag serialization, meta diffing, source verification, page save behavior, publish result fields, retry behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, and private site data out of upstream discussion.

## Additional Notes

The validation intentionally does not strip or otherwise normalize non-empty parent names. It only preserves the existing `str` / `None` contract and rejects values outside that contract.
