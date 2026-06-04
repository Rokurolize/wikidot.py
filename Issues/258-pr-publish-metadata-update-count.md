# PR Draft: Expose Publish Metadata Update Count On Publish Results

## Summary

`PagePublishResult` already exposes individual metadata-operation flags (`tags_updated`, `parent_updated`, and `metas_updated`) plus the aggregate `metadata_updated` boolean. Callers that write publish audit rows can tell whether any metadata operation was requested, but still need to repeat a small sum when they want to record how many metadata categories were touched by a publish call.

This follow-up adds `PagePublishResult.metadata_update_count`, derived from the existing metadata flags. It returns `0` when publish skipped metadata updates, `1` through `3` when tags, parent, and/or meta tags were requested, and it is included in `PagePublishResult.as_dict()` for audit-record exports. Existing metadata booleans, source verification fields, create/edit operation fields, URL, publish sequencing, and exception behavior remain unchanged.

## Related Issue

Builds on the browser-free publish workflow and publish-result drafts [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md), [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), [028-pr-publish-aggregate-status.md](028-pr-publish-aggregate-status.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [148-pr-publish-result-operation-label.md](148-pr-publish-result-operation-label.md), [204-pr-publish-source-verification-site-context.md](204-pr-publish-source-verification-site-context.md), [226-pr-publish-visibility-404-context.md](226-pr-publish-visibility-404-context.md), [231-pr-publish-result-url.md](231-pr-publish-result-url.md), [232-pr-publish-verification-request-status.md](232-pr-publish-verification-request-status.md), and [257-pr-publish-source-verification-status.md](257-pr-publish-source-verification-status.md). Those drafts established publish results as audit-ledger objects and metadata operation flags as first-class publish outcomes.

No upstream issue was filed from this local workspace.

## Changes

- Add `PagePublishResult.metadata_update_count`.
- Count requested tag, parent, and meta-tag update categories from the existing booleans.
- Include `metadata_update_count` in `PagePublishResult.as_dict()`.
- Add focused regressions for one requested metadata category, zero requested categories, and audit export of two requested categories.
- Preserve existing publish-result booleans and existing publish behavior.

## Type Of Change

- Publish-result ergonomics
- Audit-record field addition
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A publish result with one requested metadata category reports count `1`. | `TestSitePageAccessor.test_publish_result_exposes_aggregate_operation_statuses` asserts `verified_with_metadata.metadata_update_count == 1`. | Returning only a boolean, omitting the attribute, or counting source verification rejects this local completion claim. |
| A publish result with no requested metadata categories reports count `0`. | The same focused regression asserts `skipped_optional_steps.metadata_update_count == 0`. | Treating skipped metadata as one update rejects this local completion claim. |
| Failed source verification does not affect metadata update counting. | The same focused regression asserts `failed_source_check.metadata_update_count == 1` while `source_matches` is `False`. | Coupling metadata count to source-verification result rejects this local completion claim. |
| Audit-record exports include the same metadata count. | `TestSitePageAccessor.test_publish_result_exports_audit_record` asserts `as_dict()["metadata_update_count"] == 2` for tag and meta updates. | Omitting the key from `as_dict()` leaves ledger callers with duplicate count logic and rejects this local completion claim. |
| Existing publish-result fields remain unchanged. | The same focused tests continue asserting `metadata_updated`, individual metadata flags, source verification fields, operation, URL, and page ID. | Changing existing field semantics rejects this local completion claim. |
| Adjacent page and site behavior remains unchanged. | `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 217 tests. | Regressions in page or site unit tests reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `deae40c feat(site): expose publish metadata update count`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exposes_aggregate_operation_statuses -q` failed before the fix with `AttributeError: 'PagePublishResult' object has no attribute 'metadata_update_count'`.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exposes_aggregate_operation_statuses -q` passed.
- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` failed before the dictionary export update because `metadata_update_count` was missing from `as_dict()`.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` passed.
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_reports_create_or_edit_outcome tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exposes_aggregate_operation_statuses tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` passed 3 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 217 tests.
- `uv run --extra test pytest tests/unit -q` passed 808 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PagePublishResult.metadata_update_count` returns the number of requested metadata update categories across tags, parent, and meta tags.
- `PagePublishResult.metadata_update_count` returns `0` when publish requested no metadata updates.
- `PagePublishResult.as_dict()` includes `metadata_update_count`.
- Existing publish-result raw booleans, aggregate booleans, source verification labels, operation label, URL, and page identity fields keep their current behavior.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Publish results are used as compact audit records for browser-free page publishing. A metadata update count lets downstream ledgers distinguish "metadata was touched" from "how broad was the metadata side effect" without repeating local count logic at each call site. Keeping the individual booleans plus the aggregate boolean preserves detailed decisions while making common audit output easier to sort and compare.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established browser-free publishing, metadata batching, source verification, publish result URL/operation fields, source verification labels, and audit-record exports as practical workflows.
- This slice intentionally targets only the publish-result object and its dictionary export; publish execution, metadata request construction, source verification, visibility retry behavior, and live Wikidot behavior remain separate boundaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved page contents, source text from real pages, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change publish request construction, page creation/editing, metadata update mechanics, source verification mechanics, visibility retry behavior, or exception handling. It only exposes a derived count for already-existing metadata operation flags.
