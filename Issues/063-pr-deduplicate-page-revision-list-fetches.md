# PR Draft: Deduplicate Page Revision List Fetch IDs

## Summary

`PageCollection.get_page_revisions()` previously built one `history/PageRevisionListModule` request for every uncached `Page` object in the collection. If callers carried duplicate `Page` objects for the same resolved `page_id`, the method sent duplicate revision-list requests and expected a matching duplicate response count.

This fix groups uncached pages by first-seen `page.id` after page ID acquisition, sends one revision-list request per unique page ID, and applies the successful revision-list response to every duplicate page object. Each duplicate page still receives its own `PageRevisionCollection`, and every parsed `PageRevision.page` points at the page object that owns that collection.

## Related Issue

Builds on [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), which hardened failed revision-list acquisition, and complements [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), which deduplicated page revision source/HTML fetches after revision lists are already present. It also aligns with adjacent page detail dedupe follow-ups [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), and [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md).

No upstream issue was filed from this local workspace.

## Changes

- Group uncached `Page` entries by first-seen `page.id` inside `PageCollection._acquire_page_revisions(...)` after `_acquire_page_ids(...)`.
- Send one `history/PageRevisionListModule` request per unique page ID.
- Apply each successful revision-list response to every duplicate page object in that ID group.
- Preserve duplicate public collection entries while creating page-owned `PageRevisionCollection` instances for each duplicate page.
- Preserve retry-aware AMC, `None` response handling, cached-revision skipping, revision parsing, parse errors, and lazy `Page.revisions` behavior.
- Add a focused public-interface regression test for duplicate page IDs in `PageCollection.get_page_revisions()`.

## Type Of Change

- Performance and reliability improvement
- Test-covered behavior fix

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Avoid duplicate revision-list fetches for repeated uncached page IDs. | `TestPageCollectionAcquire.test_acquire_revisions_deduplicates_duplicate_page_ids` asserts one `history/PageRevisionListModule` request for two page objects with the same ID. | Reverting the grouping makes the RED test fail with `ValueError: zip() argument 2 is shorter than argument 1` when the response count matches unique IDs. |
| Preserve duplicate public collection entries and page-owned revision objects. | The focused test keeps both `Page` objects and verifies both receive revision collections whose first revision points back to the owning page object. | Sharing a single `PageRevisionCollection` across duplicates would make `PageRevision.page` point at the wrong page object. |
| Preserve normal revision acquisition behavior. | `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire -q`; `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q`; `uv run --extra test pytest tests/unit -q`. | Regression would break revision parsing, lazy revision access, source/HTML revision behavior, page/site tests, or broad unit tests. |
| Preserve static quality gates. | `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Formatting, lint, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `44bf86a perf(page): deduplicate page revision list fetch ids`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_deduplicates_duplicate_page_ids -q` failed before the fix with `ValueError: zip() argument 2 is shorter than argument 1`.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_deduplicates_duplicate_page_ids -q`
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 18 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 170 tests.
- `uv run --extra test pytest tests/unit -q` passed 618 tests.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

## Acceptance Criteria

- Duplicate uncached `Page` objects with the same resolved `page.id` send one revision-list request.
- First-seen unique page ID order is preserved in request construction.
- The public `PageCollection` length, ordering, and duplicate object entries remain unchanged.
- Every duplicate page entry receives a `PageRevisionCollection` populated from the successful shared response.
- Parsed `PageRevision.page` references point at the owning duplicate page object, not a shared first page.
- A `None` retry result leaves that page ID group unacquired.
- Cached revision collections are still skipped.
- Existing revision parsing, malformed-row errors, lazy `Page.revisions`, `Page.latest_revision`, revision source/HTML acquisition, page ID acquisition, and mutation paths are unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Revision history is a read-heavy evidence surface for page inspection, history comparison, source auditing, publication verification, and rollback workflows. If caller queues contain duplicate page objects for the same resolved ID, the library should not issue duplicate revision-list requests just to preserve the caller's original queue shape.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used revision history and source revision counts as part of publishing and verification ledgers.
- Prior local drafts hardened page revision acquisition, revision source/HTML retries, and revision source/HTML deduplication, showing page history is an important practical workflow surface.
- The same duplicate-ID request pattern was previously found in source fetching, page revision source/HTML fetching, private message details, forum post sources, forum post revisions, forum post revision HTML, and forum thread post/detail acquisition.
- Keep local rollout paths, account names, and corpus-specific identifiers out of any upstream discussion.

## Additional Notes

This slice does not deduplicate page source requests, vote requests, file requests, or page revision source/HTML requests. The later follow-up [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md) covers unresolved page ID lookup requests. This slice only removes duplicate revision-list requests after each page already has a resolved page ID.
