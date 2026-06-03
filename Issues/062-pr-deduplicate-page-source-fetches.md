# PR Draft: Deduplicate Page Source Fetch IDs

## Summary

`PageCollection.get_page_sources()` previously built one `viewsource/ViewSourceModule` request for every uncached `Page` object in the collection. If callers carried duplicate `Page` objects for the same resolved `page_id`, the method sent duplicate source requests and expected a matching duplicate response count.

This fix groups uncached pages by first-seen `page.id` after page ID acquisition, sends one source request per unique page ID, and applies the parsed source text to every uncached duplicate page entry. It preserves public collection entries, ordering, cached-source skipping, retry-aware AMC, `None` retry-result handling, source parsing, parse-error raising, and lazy `Page.source` behavior.

## Related Issue

Builds on [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md) and [051-pr-preserve-source-batch-successes.md](051-pr-preserve-source-batch-successes.md) by preserving retry-aware and partial-success source acquisition while avoiding duplicate source requests for repeated page IDs. It also complements the source iterator and fallback work in [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), plus the adjacent page detail dedupe follow-ups [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), and [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md).

No upstream issue was filed from this local workspace.

## Changes

- Group uncached `Page` entries by first-seen `page.id` inside `PageCollection._acquire_page_sources(...)` after `_acquire_page_ids(...)`.
- Send one `viewsource/ViewSourceModule` request per unique page ID.
- Parse each successful source response once and assign a new `PageSource(page, wiki_text)` to every duplicate page object in that ID group.
- Preserve cached-source skipping, retry behavior, `None` response handling, source text extraction, first malformed-source error behavior, and lazy `Page.source` semantics.
- Add a focused public-interface regression test for duplicate page IDs in `PageCollection.get_page_sources()`.

## Type Of Change

- Performance and reliability improvement
- Test-covered behavior fix

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Avoid duplicate source fetches for repeated uncached page IDs. | `TestPageCollectionAcquire.test_acquire_sources_deduplicates_duplicate_page_ids` asserts one `viewsource/ViewSourceModule` request for two page objects with the same ID. | Reverting the grouping makes the RED test fail with `ValueError: zip() argument 2 is shorter than argument 1` when the source response count matches unique IDs. |
| Preserve duplicate public collection entries. | The focused test keeps both `Page` objects in the collection and verifies both receive source text. | Collapsing the collection would change caller-visible iteration length and object identity. |
| Preserve source acquisition behavior for normal and adjacent paths. | `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire -q`; `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_site.py -q`; `uv run --extra test pytest tests/unit -q`. | Regression would break source parsing, cache skipping, fallback iterator behavior, page/site tests, or broad unit tests. |
| Preserve static quality gates. | `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Formatting, lint, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `950796e perf(page): deduplicate page source fetch ids`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_deduplicates_duplicate_page_ids -q` failed before the fix with `ValueError: zip() argument 2 is shorter than argument 1`.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_deduplicates_duplicate_page_ids -q`
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 17 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 139 tests.
- `uv run --extra test pytest tests/unit -q` passed 617 tests.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

## Acceptance Criteria

- Duplicate uncached `Page` objects with the same resolved `page.id` send one source request.
- First-seen unique page ID order is preserved in request construction.
- The public `PageCollection` length, ordering, and duplicate object entries remain unchanged.
- Every unacquired duplicate page entry receives parsed source text from the successful shared response.
- A `None` retry result leaves that page ID group unacquired.
- A malformed successful response still raises `NoElementException` after preserving later successful source results.
- Cached sources are still skipped.
- Existing source text normalization, `PageSource(page, wiki_text)` ownership, `Page.source`, `Page.refresh_source()`, page ID acquisition, source iterator fallback behavior, and mutation paths are unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Large source collection, source auditing, and publication verification workflows can accumulate duplicate page objects through joins, retries, merged search results, or caller-side queues. A source fetch batch should avoid redundant requests for the same resolved page ID while still preserving duplicate collection entries for callers that intentionally keep their original queue shape.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence recorded large ListPages/source collection workflows where timeouts, per-page fallback, and source result persistence mattered.
- The existing large-corpus source collection draft and source iterator changes show that source fetching is a practical high-volume path in this environment.
- Prior local source hardening already addressed retry-aware source batches, source cache skipping, source text fidelity, fallback chunk retries, parse-failure isolation, result convenience properties, and partial batch success preservation.
- Keep local rollout paths, account names, and corpus-specific identifiers out of any upstream discussion.

## Additional Notes

This slice does not deduplicate unresolved page ID lookup requests, page revision/vote/file detail requests, or source iterator search results. It only removes duplicate source requests after each page already has a resolved page ID.
