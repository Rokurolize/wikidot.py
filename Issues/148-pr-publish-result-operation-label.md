# PR Draft: Expose Publish Result Operation Labels

## Summary

`site.page.publish(...)` returns `PagePublishResult` so browser-free publishing callers can write durable audit rows after saving, optional source verification, and optional metadata updates. Previous local slices added `created`, aggregate status properties, and `as_dict()`, but callers still had to translate the boolean `created` flag into a stable operation label before grouping publish ledgers by create versus edit.

This follow-up adds a read-only `PagePublishResult.operation` property and includes the same value in `PagePublishResult.as_dict()`. Created pages report `"create"`; edited pages report `"edit"`. The existing `created` boolean stays available, and publish sequencing, source verification, metadata updates, and exception behavior are unchanged.

## Related Issue

Builds on [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), [028-pr-publish-aggregate-status.md](028-pr-publish-aggregate-status.md), and [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PagePublishResult.operation -> Literal["create", "edit"]`.
- Include `operation` in `PagePublishResult.as_dict()`.
- Extend publish result tests to cover create/edit operation labels and audit-record export.

## Type Of Change

- Feature / ergonomics improvement
- Browser-free publishing ledger improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Publish results expose a stable low-cardinality operation label without requiring callers to translate `created`. | `TestSitePageAccessor.test_publish_result_reports_create_or_edit_outcome` asserts `"edit"` for an existing-page publish and `"create"` for a missing-page publish. | The RED test failed before the fix because `PagePublishResult` had no `operation` attribute. |
| Audit dictionaries include the same operation label as the object property. | `TestSitePageAccessor.test_publish_result_exports_audit_record` asserts `operation: "edit"` in `as_dict()`. | The RED test failed before the fix because `as_dict()` exported `created` but not `operation`. |
| Publish sequencing, source verification, metadata update flags, and post-save visibility behavior remain unchanged. | `uv run --extra test pytest tests/unit/test_site.py -q` passed 64 site tests, and `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 169 adjacent tests. | A change that alters create/edit branch selection, metadata writes, source verification, visibility retry, or existing result fields rejects this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `067d534 feat(site): expose publish operation label`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_reports_create_or_edit_outcome tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` failed before the fix because `PagePublishResult.operation` was missing and `as_dict()` did not export `operation`.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_reports_create_or_edit_outcome tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q`
- `uv run --extra test pytest tests/unit/test_site.py -q` passed 64 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 169 tests.
- `uv run pytest tests/unit -q` passed 711 tests.
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run mypy src tests --install-types --non-interactive`
- `git diff --check`

Not run: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PagePublishResult.operation` returns `"create"` when `created is True`.
- `PagePublishResult.operation` returns `"edit"` when `created is False`.
- `PagePublishResult.as_dict()` includes `operation` alongside `fullname`, `page_id`, `created`, source verification fields, and metadata status fields.
- Existing `PagePublishResult.page`, `page_id`, `source_matches`, `tags_updated`, `parent_updated`, `metas_updated`, `created`, `metadata_updated`, and `source_verified` behavior remains unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Browser-free publishing workflows commonly persist `PagePublishResult.as_dict()` rows into JSONL or TSV-derived ledgers. A string operation label is easier to scan, group, and chart than a boolean flag while preserving the existing `created` field for callers that already branch on it.

## Local Evidence, Not For Upstream Paste

- The broader local browser-free publishing draft records practical workflows that saved pages, verified source, updated tags, parent, and meta tags, and wrote audit ledgers.
- Local follow-ups already added `created`, aggregate publish status properties, and `PagePublishResult.as_dict()` because publish callers needed structured result data.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not add write retries, JSON encoding helpers, file writing, source text serialization, metadata payload serialization, or partial-failure result objects. Failed publish operations still raise the existing wikidot.py exceptions instead of returning partial success records.
