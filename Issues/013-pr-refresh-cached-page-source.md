# PR Draft: Refresh Cached Page Source

## Summary

`Page.source` intentionally caches source text after it has been acquired or after `Page.create_or_edit(...)` returns a page with the submitted source. That is good for normal reads, but browser-free publishing workflows need a way to force a fresh `ViewSourceModule` fetch after saving so they can verify what Wikidot actually stored.

The fix adds `Page.refresh_source()`, a small public helper that clears the local source cache, reuses the existing retry-aware collection source acquisition path, and returns the freshly fetched `PageSource`.

## Related Issue

Drafted from local rollout evidence; no upstream issue filed yet.

## Changes

- Add `Page.refresh_source() -> PageSource`.
- Force a remote source fetch even when `Page._source` is already populated.
- Reuse `PageCollection.get_page_sources()` so parsing, page-id acquisition, retry behavior, and partial-failure handling stay centralized.
- Preserve existing `Page.source` cache behavior for normal reads.
- Add a regression test proving that a cached source is replaced through the retry-aware `ViewSourceModule` path.

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

Local implementation commit: `ada455f feat(page): refresh cached source`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_refresh_source_forces_remote_source_fetch tests/unit/test_page.py::TestPageProperties::test_source_property_auto_acquire tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_skips_already_acquired_pages tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_skips_failed_retry_response -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py -q` passed with 74 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 533 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`

## Acceptance Criteria

- Calling `page.refresh_source()` fetches remote source even when `page.source` is already cached.
- The method returns the fresh `PageSource` object now stored on the page.
- The method uses the same `ViewSourceModule` parsing and retry-aware acquisition path as `PageCollection.get_page_sources()`.
- Existing `Page.source` remains cached and does not force network calls on ordinary property access.
- If acquisition cannot populate source, the method raises `NotFoundException` consistently with the existing source property.

## Upstream-Safe Motivation

Page save workflows should be able to verify the saved source without reimplementing raw `ViewSourceModule` calls. A small explicit refresh method keeps the default cached property efficient while giving publishing scripts a clear way to perform a remote round-trip check.

## Local Evidence, Not For Upstream Paste

- Local rollout `019e7a39-505b-76b3-bfb4-b68be3c71fb9` included a browser-free publishing script that manually implemented a `view_source(...)` function after `savePage` to verify persisted source text.
- Local rollout `019e6067-989d-73f1-86a4-a2f0abc22af7` recorded that browser-free AMC usage was preferred over browser automation for lock acquisition, `savePage`, public URL retrieval, source checks, tag saving, and related publish actions.
- The local feature draft in [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md) includes optional saved-source verification as a core acceptance criterion.
- The local source retry draft in [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md) and cache-aware source draft in [008-pr-skip-cached-source-fetches.md](008-pr-skip-cached-source-fetches.md) make collection source fetching reliable and efficient; this draft exposes an explicit single-page refresh hook for verification workflows.

## Additional Notes

This is a small API slice toward the high-level browser-free publisher. It deliberately does not decide source normalization, save-result structure, or retry-after-save visibility polling; those remain in the broader feature draft.
