# PR Draft: Expose Publish Source Verification Status On Publish Results

## Summary

`PagePublishResult` already exposes the raw tri-state `source_matches` value plus convenience booleans such as `source_verification_requested` and `source_verified`. Callers that write audit records still need to reinterpret the tri-state value when they want a compact source verification status for ledgers.

This follow-up adds `PagePublishResult.source_verification_status`, a low-cardinality label derived from `source_matches`: `matched` when source verification matched, `mismatched` when verification was requested and failed, and `skipped` when source verification was not requested. `PagePublishResult.as_dict()` now includes the same label for audit-record exports. Existing `source_matches`, `source_verification_requested`, `source_verified`, `operation`, `url`, and metadata status fields remain unchanged.

## Related Issue

Builds on the browser-free publish workflow and publish-result drafts [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md), [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), [028-pr-publish-aggregate-status.md](028-pr-publish-aggregate-status.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [148-pr-publish-result-operation-label.md](148-pr-publish-result-operation-label.md), [204-pr-publish-source-verification-site-context.md](204-pr-publish-source-verification-site-context.md), [226-pr-publish-visibility-404-context.md](226-pr-publish-visibility-404-context.md), [231-pr-publish-result-url.md](231-pr-publish-result-url.md), and [232-pr-publish-verification-request-status.md](232-pr-publish-verification-request-status.md). Those drafts established publish results as audit-ledger objects and source verification as a first-class publish outcome.

No upstream issue was filed from this local workspace.

## Changes

- Add `PagePublishResult.source_verification_status`.
- Map `source_matches is True` to `matched`.
- Map `source_matches is False` to `mismatched`.
- Map `source_matches is None` to `skipped`.
- Include `source_verification_status` in `PagePublishResult.as_dict()`.
- Add focused regressions for matched, mismatched, and skipped publish outcomes.
- Preserve existing publish-result fields and their existing meanings.

## Type Of Change

- Publish-result ergonomics
- Audit-record field addition
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Matched source verification exports a compact status. | `TestSitePageAccessor.test_publish_result_exposes_aggregate_operation_statuses` asserts `verified_with_metadata.source_verification_status == "matched"`. | Requiring callers to reinterpret `source_matches is True` rejects this local completion claim. |
| Skipped source verification exports a compact status. | `TestSitePageAccessor.test_publish_result_exposes_aggregate_operation_statuses` asserts `skipped_optional_steps.source_verification_status == "skipped"`. | Treating a skipped check as matched, mismatched, or an absent attribute rejects this local completion claim. |
| Failed source verification exports a compact status. | `TestSitePageAccessor.test_publish_result_exposes_aggregate_operation_statuses` asserts `failed_source_check.source_verification_status == "mismatched"`. | Collapsing a failed verification into `False`, `skipped`, or a raw exception rejects this local completion claim. |
| Audit-record exports include the same status label. | `TestSitePageAccessor.test_publish_result_exports_audit_record` asserts `as_dict()["source_verification_status"] == "matched"`. | Omitting the key from `as_dict()` leaves ledger callers with duplicate tri-state interpretation and rejects this local completion claim. |
| Existing publish-result booleans and operation fields remain unchanged. | The same focused tests continue asserting `source_matches`, `source_verification_requested`, `source_verified`, `metadata_updated`, `operation`, `page_id`, and URL fields. | Changing existing field semantics rejects this local completion claim. |
| Adjacent page and site behavior remains unchanged. | `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 217 tests. | Regressions in page or site unit tests reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `d049e9d feat(site): expose publish source verification status`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exposes_aggregate_operation_statuses -q` failed before the fix with `AttributeError: 'PagePublishResult' object has no attribute 'source_verification_status'`.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exposes_aggregate_operation_statuses tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_reports_create_or_edit_outcome tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exposes_aggregate_operation_statuses tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` passed 3 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 217 tests.
- `uv run --extra test pytest tests/unit -q` passed 808 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PagePublishResult.source_verification_status` returns `matched` when `source_matches` is `True`.
- `PagePublishResult.source_verification_status` returns `mismatched` when `source_matches` is `False`.
- `PagePublishResult.source_verification_status` returns `skipped` when `source_matches` is `None`.
- `PagePublishResult.as_dict()` includes `source_verification_status`.
- Existing publish-result raw and boolean fields keep their current behavior.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Publish results are increasingly useful as audit records for browser-free page publishing. A compact source-verification label lets downstream ledgers record source verification as a small finite state without duplicating tri-state boolean interpretation at each call site. This keeps the raw `source_matches` value available while making common audit output easier to scan and compare.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established browser-free publishing, source verification, publish result URL/operation fields, and audit-record exports as practical workflows.
- This slice intentionally targets only the publish-result object and its dictionary export; publish execution, source normalization, metadata updates, visibility retry behavior, and live Wikidot behavior remain separate boundaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved page contents, source text from real pages, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change publish request construction, page creation/editing, source verification mechanics, metadata updates, visibility retry behavior, or exception handling. It only gives existing publish-result data a stable low-cardinality audit label.
