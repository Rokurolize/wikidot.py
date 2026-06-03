# PR Draft: Preserve Source Batch Successes After Parse Failures

## Summary

`PageCollection.get_page_sources()` fetches multiple `viewsource/ViewSourceModule` responses in one retry-aware AMC batch. Before this fix, if one response was missing the expected `div.page-source` wrapper, the method raised immediately and stopped parsing the remaining responses in the same batch. Earlier successful pages stayed cached, but later valid responses were discarded and high-level `site.pages.iter_sources(...)` had to refetch those later pages through fallback requests.

The fix keeps the direct `PageCollection.get_page_sources()` error surface: a malformed source response still raises `NoElementException`. It now parses the rest of the batch first, preserves valid sources before and after the malformed response, and then raises the first parse error. High-level source iteration therefore still yields a per-page failure for the malformed page, but avoids redundant fallback requests for later pages that already had valid source responses.

## Related Issue

Follow-up to the large-corpus source collection work in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [026-pr-source-iterator-parse-failure-isolation.md](026-pr-source-iterator-parse-failure-isolation.md), [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md), and [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md). No upstream issue filed yet.

## Changes

- Continue parsing later `ViewSourceModule` responses after the first missing `div.page-source` wrapper.
- Preserve valid `PageSource` objects for pages before and after a malformed response in the same batch.
- Raise the first `NoElementException` after the batch is processed so direct callers still see the malformed-source error.
- Reduce high-level `site.pages.iter_sources(...)` fallback requests because later successful pages no longer need to be fetched again.
- Preserve `None` retry responses, cache skipping, request construction, source text normalization, and existing direct exception behavior.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Performance/reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Requirements Traceability

| Requirement | Acceptance | Verification | Negative Control |
| --- | --- | --- | --- |
| R1: Later valid source responses are preserved | A batch with valid, malformed, valid responses raises for the malformed page but leaves the first and third pages with cached `PageSource` objects | `test_acquire_sources_preserves_later_successes_when_parse_fails` | The RED test failed before the fix because the third page `_source` stayed `None` |
| R2: Direct malformed-source errors are still visible | `PageCollection.get_page_sources()` still raises `NoElementException` naming the malformed page | `test_acquire_sources_preserves_later_successes_when_parse_fails` | The test would fail if malformed responses were silently converted into success or ignored |
| R3: Iterator fallback requests are reduced without losing per-page failures | `site.pages.iter_sources(...)` retries only the malformed page after a mixed parse batch and still yields success, failure, success in search order | `test_iter_sources_reports_parse_failures_without_losing_other_pages` | The pre-fix expectation included an unnecessary `[403]` fallback request for a page whose original batch response was valid |
| R4: Existing source behavior remains stable | Page and site unit suites, full unit suite, lint, format, type, and whitespace checks pass | `tests/unit/test_page.py`; `tests/unit/test_site.py`; `tests/unit` | Broad tests cover source cache skipping, `None` retry responses, source text parsing, and publish verification paths |

## Testing

Local implementation commit: `018bb43 fix(page): preserve source batch successes`

- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_preserves_later_successes_when_parse_fails -q` failed before the fix because the later valid page source stayed `None`, then passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_reports_parse_failures_without_losing_other_pages -q` initially failed after the fix because the test still expected the old redundant `[403]` fallback request; it passed after the expectation was updated to the improved request pattern.
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_preserves_later_successes_when_parse_fails tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_reports_parse_failures_without_losing_other_pages -q` passed with 2 tests.
- [x] `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_site.py::TestSitePagesAccessor -q` passed with 25 tests.
- [x] `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed with 137 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 606 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] Complexity scan refreshed at `/home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/artifacts/complexity_analysis_wikidot.md`

## Acceptance Criteria

- `PageCollection.get_page_sources()` preserves valid source responses that appear after a malformed source response in the same batch.
- The method still raises `NoElementException` for malformed source responses and includes the malformed page fullname in the error text.
- `site.pages.iter_sources(...)` continues returning a failed `PageSourceResult` for the malformed page while avoiding fallback refetches for later pages that already parsed successfully.
- Source result order, `PageSourceResult.ok`, `PageSourceResult.wiki_text`, source text normalization, and skipped `None` retry-response behavior remain unchanged.
- No live Wikidot request, browser automation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Large Wikidot source collections should salvage every successful response from a batch. A single malformed page should not cause the library to discard later valid source responses or make unnecessary fallback requests. Parsing the whole batch before raising keeps direct error visibility while improving source collection reliability and reducing load.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence recorded large ListPages/source collection workflows where source timeouts and per-page fallback handling mattered.
- The broader local source-collection draft calls for structured per-page source success/failure records that can be persisted without aborting a run.
- Existing local iterator work already isolated malformed source responses at the high-level iterator; this slice improves the lower-level batch preservation behavior that iterator fallback builds on.

## Additional Notes

This slice deliberately does not change retry counts, source request construction, public dataclass fields, or the direct exception type. It only changes when the first parse error is raised so successful responses in the same batch are not lost.

Follow-up: [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md) removes duplicate source requests for repeated resolved page IDs while preserving this slice's later-success preservation behavior.
