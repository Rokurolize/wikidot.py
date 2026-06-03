# PR Draft: Verify Publish Source Before Metadata Updates

## Summary

`site.page.publish(...)` can save page source, optionally verify the saved source with `Page.refresh_source()`, and optionally update tags, parent, and meta tags. Before this fix, metadata updates ran before source verification. If `verify_source=True` and the saved source did not match the submitted source, the helper still updated tags, parent, and meta tags before raising `UnexpectedException`.

This fix verifies saved source before the metadata phase. A failed source verification keeps the existing exception behavior but no longer applies tags, parent, or meta updates that could mark a mismatched publish as complete. Successful publishes still update metadata and return the same `PagePublishResult` fields.

## Related Issue

Builds on the browser-free publishing feature draft [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), especially the high-level helper in [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), custom source verification in [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md), post-save visibility polling in [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md), create/edit outcome reporting in [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), aggregate status fields in [028-pr-publish-aggregate-status.md](028-pr-publish-aggregate-status.md), and audit dictionary export in [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md).

No upstream issue was filed from this local workspace.

## Changes

- Move `verify_source` handling ahead of the optional `Page.set_metadata(...)` phase inside `SitePageAccessor.publish(...)`.
- Preserve post-save page ID resolution before source verification and metadata updates.
- Preserve exact and caller-normalized source comparison behavior.
- Preserve successful metadata updates when source verification succeeds or is skipped.
- Add a focused public `site.page.publish(...)` regression where source verification fails while tags, parent, and metas were requested.

## Type Of Change

- Bug fix
- Browser-free publishing safety improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A failed source verification must not apply tags, parent, or meta updates. | `TestSitePageAccessor.test_publish_skips_metadata_when_source_verification_fails` asserts `saved_page.set_metadata.assert_not_called()` after `UnexpectedException`. | The RED test failed before the fix because `set_metadata(...)` was called once with tags, parent, and metas before verification raised. |
| Source verification failure must keep the existing exception surface. | The same focused test expects `UnexpectedException("Saved source verification failed for page: test-page")`. | Returning a partial result or changing the exception message would fail the focused assertion and make existing callers harder to audit. |
| Successful publish behavior should remain unchanged. | Existing publish tests for editing, metadata updates, strict mismatch, custom normalization, and audit records remained green. | Regressions in create/edit, source comparison, metadata flags, or result serialization fail the neighboring publish tests. |
| Adjacent site/page workflows should remain green. | `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 160 tests. | Source iterator, page lookup, publish, recent-changes, or page helper regressions reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `e0b2999 fix(site): verify publish source before metadata`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_skips_metadata_when_source_verification_fails -q` failed before the fix because `set_metadata(...)` was called once before source verification raised.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_skips_metadata_when_source_verification_fails -q`
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_edits_existing_page_sets_metadata_and_verifies_source tests/unit/test_site.py::TestSitePageAccessor::test_publish_raises_when_verified_source_mismatches tests/unit/test_site.py::TestSitePageAccessor::test_publish_verifies_source_with_custom_normalizer tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` passed 4 tests.
- `uv run --extra test pytest tests/unit/test_site.py -q` passed 60 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 160 tests.
- `uv run --extra test pytest tests/unit -q` passed 674 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- When `verify_source=True` and the fetched source mismatches, `site.page.publish(...)` raises the existing source-verification `UnexpectedException`.
- In that failed-verification path, `Page.set_metadata(...)` is not called even if tags, parent, or metas were requested.
- When source verification succeeds, requested tags, parent, and metas are still updated as before.
- When source verification is skipped, requested tags, parent, and metas are still updated as before.
- Post-save page ID resolution still happens before verification, metadata updates, and result construction.
- `PagePublishResult.source_matches`, `source_verified`, `metadata_updated`, and `as_dict()` behavior remains unchanged for successful publishes.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Publishing helpers are used to write source and then mark pages with tags, parent links, or audit metadata. If the saved source fails verification, applying those metadata updates can make a failed publish look complete to later scripts. Verifying source before metadata keeps the helper's side effects aligned with its audit result while preserving the existing exception-based failure model.

## Local Evidence, Not For Upstream Paste

- Local browser-free publishing drafts record practical workflows that wrote ledgers after saving, verifying source, and updating tags, parent, or meta tags.
- The broader local feature draft treats source verification and structured publish status as core audit surfaces for non-browser publishing.
- Keep private rollout paths, account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not add partial-failure result objects, write retries, JSON encoding helpers, or new metadata APIs. It only reorders the existing `publish(...)` phases so failed source verification prevents later metadata side effects.
