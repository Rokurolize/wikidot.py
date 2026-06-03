# PR Draft: Deduplicate Page Vote Fetch IDs

## Summary

`PageCollection.get_page_votes()` previously built one `pagerate/WhoRatedPageModule` request for every uncached `Page` object in the collection. If callers carried duplicate `Page` objects for the same resolved `page_id`, the method sent duplicate vote-list requests and expected a matching duplicate response count.

This fix groups uncached pages by first-seen `page.id` after page ID acquisition, sends one vote-list request per unique page ID, and applies the successful vote-list response to every duplicate page object. Each duplicate page still receives its own `PageVoteCollection`, and every parsed `PageVote.page` points at the page object that owns that collection.

## Related Issue

Builds on [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md), which made vote acquisition cache-aware, and complements [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), and [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), which remove the same duplicate-ID request shape from adjacent page detail paths.

No upstream issue was filed from this local workspace.

## Changes

- Group uncached `Page` entries by first-seen `page.id` inside `PageCollection._acquire_page_votes(...)` after `_acquire_page_ids(...)`.
- Send one `pagerate/WhoRatedPageModule` request per unique page ID.
- Apply each successful vote-list response to every duplicate page object in that ID group.
- Preserve duplicate public collection entries while creating page-owned `PageVoteCollection` instances for each duplicate page.
- Preserve retry-aware AMC, `None` response handling, cached-vote skipping, user/value parsing, mismatch errors, and lazy `Page.votes` behavior.
- Add a focused public-interface regression test for duplicate page IDs in `PageCollection.get_page_votes()`.

## Type Of Change

- Performance and reliability improvement
- Test-covered behavior fix

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Avoid duplicate vote-list fetches for repeated uncached page IDs. | `TestPageCollectionAcquire.test_acquire_votes_deduplicates_duplicate_page_ids` asserts one `pagerate/WhoRatedPageModule` request for two page objects with the same ID. | Reverting the grouping makes the RED test fail with `ValueError: zip() argument 2 is shorter than argument 1` when the response count matches unique IDs. |
| Preserve duplicate public collection entries and page-owned vote objects. | The focused test keeps both `Page` objects and verifies both receive vote collections whose first vote points back to the owning page object. | Sharing a single `PageVoteCollection` across duplicates would make `PageVote.page` point at the wrong page object. |
| Preserve normal vote acquisition behavior. | `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire -q`; `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q`; `uv run --extra test pytest tests/unit -q`. | Regression would break vote parsing, mismatch errors, lazy vote access, page-vote tests, page/site tests, or broad unit tests. |
| Preserve static quality gates. | `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Formatting, lint, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `ab33bf1 perf(page): deduplicate page vote fetch ids`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_deduplicates_duplicate_page_ids -q` failed before the fix with `ValueError: zip() argument 2 is shorter than argument 1`.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_deduplicates_duplicate_page_ids -q`
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 20 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 151 tests.
- `uv run --extra test pytest tests/unit -q` passed 620 tests.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

## Acceptance Criteria

- Duplicate uncached `Page` objects with the same resolved `page.id` send one vote-list request.
- First-seen unique page ID order is preserved in request construction.
- The public `PageCollection` length, ordering, and duplicate object entries remain unchanged.
- Every duplicate page entry receives a `PageVoteCollection` populated from the successful shared response.
- Parsed `PageVote.page` references point at the owning duplicate page object, not a shared first page.
- A `None` retry result leaves that page ID group unacquired.
- Cached vote collections are still skipped.
- Existing vote user parsing, vote value parsing, user/value mismatch errors, lazy `Page.votes`, page ID acquisition, and mutation paths are unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Vote inspection is a read-heavy evidence surface for page review, rating audits, publication checks, and moderation workflows. If caller queues contain duplicate page objects for the same resolved ID, the library should not issue duplicate vote-list requests just to preserve the caller's original queue shape.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence included page evidence checks, publishing verification, and page detail collection where ratings and votes can affect downstream decisions.
- Prior local drafts made page detail fetching cache-aware and then removed duplicate resolved page-ID requests from source, revision-list, and file-list acquisition.
- The same duplicate-ID request pattern was previously found in source fetching, page revision-list fetching, page file-list fetching, page revision source/HTML fetching, private message details, forum post sources, forum post revisions, forum post revision HTML, and forum thread post/detail acquisition.
- Keep local rollout paths, account names, and corpus-specific identifiers out of any upstream discussion.

## Additional Notes

This slice does not deduplicate page source requests, revision-list requests, file-list requests, or page revision source/HTML requests. The later follow-up [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md) covers unresolved page ID lookup requests. This slice only removes duplicate page vote-list requests after each page already has a resolved page ID.
