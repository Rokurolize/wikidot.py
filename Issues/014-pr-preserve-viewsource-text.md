# PR Draft: Preserve Multiline ViewSource Text

## Summary

`PageCollection.get_page_sources()` and `PageRevisionCollection.get_sources()` parse Wikidot source from `div.page-source`. The previous extraction used whole-string trimming, which removed meaningful boundary whitespace and only handled a leading wrapper tab at the start of the entire text. Multiline source returned by Wikidot can include one wrapper tab per rendered line, so later lines could keep an extra tab in the resulting `PageSource.wiki_text`.

The fix centralizes source extraction in `extract_page_source_text(...)` and removes one Wikidot wrapper tab per line while preserving the source text's own blank lines.

## Related Issue

Drafted from local rollout evidence; no upstream issue filed yet.

## Changes

- Add a shared `extract_page_source_text(...)` helper for `div.page-source` elements.
- Use the helper for current page source acquisition through `PageCollection.get_page_sources()`.
- Use the same helper for revision source acquisition through `PageRevisionCollection.get_sources()`.
- Preserve multiline source blank lines while removing the per-line wrapper tab inserted by Wikidot's source view markup.
- Add regression tests for current page source and revision source parsing.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Performance/reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Testing

Local implementation commit: `f89b170 fix(page): preserve viewsource text`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_preserves_multiline_source_text -q` failed before the fix and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_preserves_multiline_source_text tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_preserves_multiline_source_text -q`
- [x] `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_revision.py -q` passed with 101 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 535 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`

## Acceptance Criteria

- Multiline `div.page-source` responses remove Wikidot's one wrapper tab from every rendered source line, not just the first text position.
- Blank lines inside the source are preserved.
- Current page source and revision source use the same extraction behavior.
- Existing single-line source responses continue to parse unchanged.
- Missing `div.page-source` behavior remains unchanged.

## Upstream-Safe Motivation

Source acquisition should return the page's Wikidot markup, not display-wrapper indentation from the source-view HTML. This matters for browser-free publishing verification, source diffing, and large corpus collection where callers compare saved source text with expected local files.

## Local Evidence, Not For Upstream Paste

- Local rollout `019e7a39-505b-76b3-bfb4-b68be3c71fb9` included a browser-free publishing script that manually fetched `ViewSourceModule` output and normalized source text before round-trip comparison.
- Local rollout `019e3df7-5e71-7e16-973d-88e75a4b845a` included a campaign queue source extractor and a test named `test_page_source_from_view_source_html_preserves_wikidot_source`, showing that preserving source text from view-source HTML was operationally important.
- The local publisher draft in [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md) includes saved-source verification, and the local refresh-source draft in [013-pr-refresh-cached-page-source.md](013-pr-refresh-cached-page-source.md) exposes the fetch hook used for that verification.

## Additional Notes

This PR draft does not add a high-level publish or compare API. It only fixes the lower-level source acquisition fidelity that those workflows depend on.
