# PR Draft: Export Publish Result Audit Records

## Summary

Browser-free publishing callers often write audit rows after `site.page.publish(...)`. Previous local slices exposed create/edit outcome and aggregate publish statuses, but callers still had to rebuild the same dictionary before writing JSONL, TSV-derived ledgers, or publish verification records.

This change adds `PagePublishResult.as_dict()`, returning a compact side-effect-free dictionary with page fullname, page ID, create/edit status, source verification status, metadata update flags, and aggregate metadata/source booleans. It reuses existing result properties and does not change create/edit sequencing, metadata writes, source verification, post-save visibility polling, or exception behavior.

## Related Issue

Builds on [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), and [028-pr-publish-aggregate-status.md](028-pr-publish-aggregate-status.md). It also complements [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md) and [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md), which make publish verification more usable before audit persistence.

No upstream issue was filed from this local workspace.

## Changes

- Add `PagePublishResult.as_dict() -> dict[str, str | int | bool | None]`.
- Return exactly `fullname`, `page_id`, `created`, `source_matches`, `source_verified`, `tags_updated`, `parent_updated`, `metas_updated`, and `metadata_updated`.
- Preserve existing `PagePublishResult.page`, `page_id`, `source_matches`, `tags_updated`, `parent_updated`, `metas_updated`, `created`, `metadata_updated`, and `source_verified` behavior.
- Add a focused public-result regression test that serializes a publish result into an audit-friendly dictionary.

## Type Of Change

- New feature
- Browser-free publishing ergonomics improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Publish result records can be exported without caller-side audit-row branching. | `TestSitePageAccessor.test_publish_result_exports_audit_record` asserts `result.as_dict()` for a publish result with source verification and metadata updates. | The RED test failed before the fix with `AttributeError: 'PagePublishResult' object has no attribute 'as_dict'`. |
| The record shape stays compact and audit-friendly. | The focused test asserts keys and values for page identity, create/edit outcome, source status, metadata flags, and aggregate statuses. | Adding raw `Page` objects or metadata payload dictionaries would fail the exact dictionary assertion and make simple persistence harder. |
| Existing publish behavior is unchanged. | Related publish result tests, the full site module tests, and the broad unit suite still pass. | A regression in create/edit, source verification, metadata, or visibility behavior would fail existing publish tests. |
| Static quality gates remain green. | `tests/unit`; ruff; format; mypy; diff check. | Formatting, lint, type, whitespace, or broad unit failures reject the local completion claim. |

## Testing

Implemented locally in commit `f1626fe feat(site): export publish result audit records`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` failed before the fix with `AttributeError: 'PagePublishResult' object has no attribute 'as_dict'`.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q`
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_reports_create_or_edit_outcome tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exposes_aggregate_operation_statuses tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` passed 3 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed 13 tests.
- `uv run --extra test pytest tests/unit/test_site.py -q` passed 53 tests.
- `uv run --extra test pytest tests/unit -q` passed 625 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`
- `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed current complexity leads.

## Acceptance Criteria

- `PagePublishResult.as_dict()` returns `fullname` from `result.page.fullname`.
- `PagePublishResult.as_dict()` returns `page_id`, `created`, `source_matches`, `source_verified`, `tags_updated`, `parent_updated`, `metas_updated`, and `metadata_updated`.
- `as_dict()` does not include raw `Page` objects, source text, metadata payloads, tags, parent names, exceptions, or credentials.
- Existing create/edit, source verification, source normalization, post-save visibility, metadata status, and aggregate status behavior remains unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

The high-level publish helper is most useful when callers can persist a concise audit record after each publish call. A compact `as_dict()` method avoids repeated ad hoc serialization while keeping the richer `PagePublishResult` object available for callers that need the page object or individual properties.

## Local Evidence, Not For Upstream Paste

- The broader local browser-free publishing draft records practical workflows that wrote ledgers after saving, verifying source, and updating tags, parent, or meta tags.
- Local follow-ups already added create/edit outcome and aggregate publish status properties because audit code needed those values.
- Keep private rollout paths, account names, sandbox details, raw command transcripts, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally avoids adding JSON encoding helpers, file writing, source text serialization, metadata payload serialization, or partial-failure result objects. Failed publish operations still raise the existing wikidot.py exceptions instead of returning partial success records.
