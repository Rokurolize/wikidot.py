# PR Draft: Include Site Context In Publish Source Verification Failures

## Summary

`site.page.publish(..., verify_source=True)` raises an `UnexpectedException` when the freshly fetched saved source does not match the submitted source. Earlier local browser-free publishing slices made this path safer by verifying source before metadata updates, supporting caller-provided source normalization, reporting create/edit outcomes, and exporting publish audit records. The remaining mismatch message still named only the page fullname: `Saved source verification failed for page: <fullname>`.

This follow-up keeps publish create/edit selection, login checking, post-save visibility resolution, source refresh, optional source normalization, mismatch exception behavior, metadata-not-updated-on-mismatch behavior, and successful `PagePublishResult` fields unchanged. It only adds the site unix name to the existing mismatch message: `Saved source verification failed for site: <site>, page: <fullname>`.

## Related Issue

Builds on [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md), [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md), [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [148-pr-publish-result-operation-label.md](148-pr-publish-result-operation-label.md), [194-pr-page-source-site-context.md](194-pr-page-source-site-context.md), and [203-pr-site-page-get-miss-site-context.md](203-pr-site-page-get-miss-site-context.md). Those drafts established browser-free publishing, source verification, publish ledger ergonomics, direct source site context, and site-aware page lookup diagnostics as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Include `self.site.unix_name` and the requested fullname in the `SitePageAccessor.publish(...)` saved-source mismatch `UnexpectedException`.
- Tighten the focused mismatch regression to assert the new site/page message.
- Keep the metadata side-effect guard regression aligned with the same message.
- Preserve publish sequencing, source normalizer behavior, source refresh, result audit fields, and exception type.

## Type Of Change

- Bug fix / diagnostics improvement
- Browser-free publishing ledger context
- Test update

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A saved-source mismatch during `site.page.publish(..., verify_source=True)` still raises `UnexpectedException`. | `TestSitePageAccessor.test_publish_raises_when_verified_source_mismatches` edits an existing page whose refreshed source differs from the submitted source. | Returning a partial `PagePublishResult`, silently accepting the mismatch, or changing the exception type rejects this local completion claim. |
| The mismatch error identifies both site and page. | The focused regression asserts `Saved source verification failed for site: test-site, page: test-page`. | The RED test failed before the fix because the message was only `Saved source verification failed for page: test-page`. |
| Failed source verification still does not apply tags, parent, or meta updates. | `TestSitePageAccessor.test_publish_skips_metadata_when_source_verification_fails` still asserts `saved_page.set_metadata.assert_not_called()`. | A change that writes metadata after a mismatch rejects this local completion claim. |
| Adjacent publish and page workflows remain green. | `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_raises_when_verified_source_mismatches tests/unit/test_site.py::TestSitePageAccessor::test_publish_skips_metadata_when_source_verification_fails tests/unit/test_site.py::TestSitePageAccessor::test_publish_verifies_source_with_custom_normalizer tests/unit/test_site.py::TestSitePageAccessor::test_publish_edits_existing_page_sets_metadata_and_verifies_source tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` passed 5 tests; `uv run pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 185 tests. | Regressions in create/edit branch selection, source normalization, source refresh, metadata updates, page lookup, or page/site workflows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `c1a181c fix(site): include site in publish verification failures`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_raises_when_verified_source_mismatches -q` failed before the fix because the exception message was `Saved source verification failed for page: test-page`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_raises_when_verified_source_mismatches -q`.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_raises_when_verified_source_mismatches tests/unit/test_site.py::TestSitePageAccessor::test_publish_skips_metadata_when_source_verification_fails tests/unit/test_site.py::TestSitePageAccessor::test_publish_verifies_source_with_custom_normalizer tests/unit/test_site.py::TestSitePageAccessor::test_publish_edits_existing_page_sets_metadata_and_verifies_source tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` passed 5 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 185 tests.
- `uv run pytest tests/unit -q` passed 736 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `site.page.publish(..., verify_source=True)` still compares the freshly fetched saved source with the submitted source after applying `source_normalizer` when provided.
- A mismatch still raises `UnexpectedException`.
- The mismatch message names both the site unix name and requested page fullname.
- Failed verification still prevents requested tags, parent, and meta updates from running.
- Successful source verification and skipped verification keep existing `PagePublishResult` behavior.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Browser-free publishing workflows often run across several Wikidot sites where the same page fullname can exist in more than one place. When saved-source verification fails, the plain exception should identify both the site and page so a ledger or retry queue can route the failure without preserving raw source text, response HTML, local rollout paths, or account context.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established `site.page.publish(...)`, source verification, source normalization, post-save visibility polling, publish audit records, and source-failure diagnostics as practical local surfaces.
- The broader browser-free publishing draft treats clear source verification failures as part of the publish helper contract.
- This slice only claims the mismatch diagnostic. It does not claim write retries, partial failure result objects, live Wikidot behavior changes, or any source normalization policy change.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change publish request payloads, login checks, create/edit branching, post-save page ID resolution, source refresh behavior, source normalization, comparison semantics, metadata update sequencing, successful result fields, `PagePublishResult.as_dict()`, or live Wikidot behavior. It only adds site/page context to the existing saved-source verification mismatch exception.
