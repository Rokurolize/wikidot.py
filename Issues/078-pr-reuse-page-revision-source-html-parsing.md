# PR Draft: Reuse Page Revision Source And HTML Parsing For Duplicate IDs

## Summary

`PageRevisionCollection.get_sources()` and `PageRevisionCollection.get_htmls()` already deduplicate duplicate uncached revision IDs before sending `history/PageSourceModule` and `history/PageVersionModule` requests. The duplicate revision entries still processed the same successful response once per duplicate object, so a shared source or HTML response was decoded repeatedly even though only one remote response was needed.

This fix processes each successful unique page-revision source or HTML response once, then applies the parsed source text or HTML body to every duplicate `PageRevision` object in that revision-ID group. The public collection shape, duplicate entries, source/HTML cache semantics, retry `None` handling, source extraction, HTML separator handling, and lazy `PageRevision.source` / `PageRevision.html` acquisition remain unchanged.

## Related Issue

Builds directly on [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), which removed duplicate source and HTML requests for repeated page revision IDs. It follows the duplicate-response parse reuse pattern from [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), and [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md).

No upstream issue was filed from this local workspace.

## Changes

- Change the internal `_generic_acquire(...)` response callback from per-revision mutation to per-response parsing that returns a per-revision applicator.
- Parse each successful `history/PageSourceModule` response body once per unique uncached revision ID.
- Parse each successful `history/PageVersionModule` response body once per unique uncached revision ID.
- Apply the parsed source text or HTML content to every duplicate unacquired `PageRevision` entry with that ID.
- Preserve request deduplication, first-seen request order, cached item skipping, retry-aware AMC, `None` retry-result handling, malformed source errors, HTML separator handling, lazy source/HTML acquisition, revision-list acquisition, and mutation boundaries.
- Strengthen the existing duplicate-ID source and HTML tests to assert one response JSON decode per unique revision ID.

## Type Of Change

- Performance improvement
- Refactoring
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Duplicate uncached revision IDs should not re-read the same source response body. | `TestPageRevisionCollection.test_get_sources_deduplicates_duplicate_revision_ids` asserts `mock_response.json.call_count == 1` while both duplicate entries receive source. | The RED test failed before the fix with `assert 2 == 1` for `mock_response.json.call_count`. |
| Duplicate uncached revision IDs should not re-read the same HTML response body. | `TestPageRevisionCollection.test_get_htmls_deduplicates_duplicate_revision_ids` asserts `mock_response.json.call_count == 1` while both duplicate entries receive HTML. | The RED test failed before the fix with `assert 2 == 1` for `mock_response.json.call_count`. |
| Duplicate collection entries stay visible and populated. | The focused tests still assert both duplicate revision objects receive the shared source text or HTML content. | Collapsing duplicate entries or populating only the first entry would fail the existing assertions. |
| Existing page revision behavior stays green. | `uv run --extra test pytest tests/unit/test_page_revision.py -q`; `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q`; `uv run --extra test pytest tests/unit -q`. | Regressions in source extraction, HTML separator handling, lazy access, or adjacent page/site behavior reject the local completion claim. |
| Static quality gates remain green. | `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Formatting, lint, type, or whitespace failures reject the local completion claim. |
| Complexity evidence is interpreted conservatively. | The refreshed scanner artifact remains a lead list; the claimed improvement is duplicate response decode reuse in page revision source/HTML acquisition, not removal of all page revision warnings. | Overclaiming that page-revision scanner warnings disappeared would reject the draft. |

## Testing

Implemented locally in commit `4792079 perf(page_revision): reuse duplicate revision responses`.

- RED: `uv run --extra test pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_deduplicates_duplicate_revision_ids tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_deduplicates_duplicate_revision_ids -q` failed before the fix with `assert 2 == 1` for both source and HTML response JSON call counts.
- GREEN: `uv run --extra test pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_deduplicates_duplicate_revision_ids tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_deduplicates_duplicate_revision_ids -q`
- `uv run --extra test pytest tests/unit/test_page_revision.py -q` passed 30 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 178 tests.
- `uv run --extra test pytest tests/unit -q` passed 630 tests.
- `uv run ruff check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py`
- `uv run ruff format --check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py`
- `uv run mypy src/wikidot/module/page_revision.py tests/unit/test_page_revision.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not spawn the `pyright` executable.

## Acceptance Criteria

- Duplicate uncached `PageRevision` IDs still send one source request.
- Duplicate uncached `PageRevision` IDs still send one HTML request.
- Each successful source response body is decoded once per unique revision ID.
- Each successful HTML response body is decoded once per unique revision ID.
- Every duplicate unacquired revision object receives the shared source text or HTML content.
- Cached source and HTML entries are still skipped.
- A `None` retry result still leaves the affected revision ID group unacquired, preserving lazy retry semantics.
- Missing `div.page-source` still raises the existing `NoElementException`.
- HTML separator handling still tolerates separator whitespace and falls back to the full body when the separator is absent.
- Existing lazy `PageRevision.source`, lazy `PageRevision.html`, revision-list acquisition, page source acquisition, page publish behavior, and mutation paths remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Page revision source and HTML inspection are read-heavy in history comparison, source auditing, publication verification, and rollback workflows. Once duplicate `PageRevision` objects share the same revision ID and successful source/HTML response, decoding the same response body once per duplicate object does not add information. Reusing the parsed value reduces avoidable CPU work while preserving the public duplicate entries and lazy cache behavior callers already see.

## Local Evidence, Not For Upstream Paste

- [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md) removed duplicate revision source/HTML requests but intentionally preserved duplicate revision entries.
- The focused RED tests demonstrated the remaining cost: duplicate revision entries still decoded the same source and HTML response bodies twice.
- The same request-deduplication-then-parse-reuse follow-up pattern was previously found for private-message detail responses, page revision-list responses, and page file-list responses.
- Keep local rollout paths, account names, and corpus-specific identifiers out of any upstream discussion.

## Additional Notes

This slice does not change revision-list acquisition, revision ID request construction, retry policy, source text normalization, HTML separator parsing rules, lazy property return types, page source fetching, publishing, or mutation methods. It only avoids redoing the same successful page revision source/HTML response decode for duplicate unacquired revision entries that share a revision ID.
