# PR Draft: Add Browser-Free Page Publish Helper

## Summary

Browser-free publishing scripts currently have to compose page lookup, create/edit, metadata writes, page ID discovery, and source verification themselves. The library now exposes those existing primitives through `site.page.publish(...)`, so callers can publish a page and optionally verify source without hand-writing AMC payloads for the common workflow.

The helper deliberately reuses `Page.create_or_edit(...)`, `Page.edit(...)`, `Page.set_metadata(...)`, and `Page.refresh_source()` instead of duplicating raw `savePage`, metadata, or view-source request bodies.

## Related Issue

Drafted from the broader local feature draft in [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md); no upstream issue filed yet.

## Changes

- Add `PagePublishResult`, a frozen result object with `page`, `page_id`, `source_matches`, `tags_updated`, `parent_updated`, and `metas_updated`.
- Add `site.page.publish(...)` for create-or-edit publishing through the existing page accessor.
- Edit existing pages through `Page.edit(...)` and create missing pages through `Page.create_or_edit(..., raise_on_exists=True)`.
- Optionally update tags, parent, and meta tags by reusing `Page.set_metadata(...)`.
- Optionally verify saved source by forcing `Page.refresh_source()` and comparing the fetched source to the submitted source.
- Raise `UnexpectedException` with the page fullname when requested source verification fails.
- Add tests for existing-page publish with metadata and source verification, missing-page creation without optional steps, and source verification mismatch.

## Type Of Change

- [ ] Bug fix
- [x] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Performance/reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Testing

Local implementation commit: `087312d feat(site): add browser-free page publish helper`

- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_edits_existing_page_sets_metadata_and_verifies_source -q` failed before the fix with missing `SitePageAccessor.publish` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed with 8 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 542 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`

## Acceptance Criteria

- `site.page.publish(...)` can create a missing page.
- `site.page.publish(...)` can edit an existing page.
- The helper can optionally set tags, parent, and meta tags after saving source.
- The helper can optionally verify saved source through `ViewSourceModule`.
- The helper returns structured status data including page object, page ID, source verification status, and metadata operation flags.
- Source verification mismatch raises a clear wikidot.py exception instead of returning a false success result.
- The implementation reuses existing lower-level APIs and does not duplicate raw save-page AMC request construction.

## Upstream-Safe Motivation

wikidot.py already exposes the pieces needed for browser-free page publishing, but practical scripts still need to coordinate them manually. A small accessor-level helper gives callers a safer default workflow while preserving the lower-level APIs for custom cases.

## Local Evidence, Not For Upstream Paste

- Local rollout `019e6067-989d-73f1-86a4-a2f0abc22af7` recorded that browser-free AMC usage was preferred over browser automation for lock acquisition, `savePage`, public URL retrieval, source checks, and tag saving.
- Local rollout `019e7a39-505b-76b3-bfb4-b68be3c71fb9` included a publishing script that manually implemented `save_page`, `view_source`, `set_metadata`, tags, parent, and meta operations.
- The broader local feature draft in [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md) calls for a high-level helper with create/edit, metadata, saved-source verification, and structured result data.
- Prior local slices added the lower-level primitives used here: `Page.set_metadata(...)` in [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), `Page.refresh_source()` in [013-pr-refresh-cached-page-source.md](013-pr-refresh-cached-page-source.md), and view-source text fidelity in [014-pr-preserve-viewsource-text.md](014-pr-preserve-viewsource-text.md).

## Additional Notes

This slice does not retry `savePage`, because blind retries of a write operation can duplicate side effects. It also does not add explicit post-save visibility polling beyond the existing page lookup and page ID resolution paths. The source normalization follow-up is drafted in [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md).
