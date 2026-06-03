# PR Draft: Deduplicate Page ID Fetch URLs

## Summary

`PageCollection.get_page_ids()` and the page-detail collection helpers previously built one direct page GET for every unresolved `Page` object in the collection. If callers carried duplicate unresolved `Page` objects for the same page URL, the method requested the same `/norender/true/noredirect/true` page more than once before parsing `WIKIREQUEST.info.pageId`.

This fix groups unresolved pages by first-seen page ID lookup URL, sends one direct GET per unique URL, and applies the parsed page ID to every duplicate page object in that URL group. The public `PageCollection` shape, page object identity, first-seen request order, already-acquired ID skipping, response type checks, page ID extraction, and missing-ID error surface are preserved.

## Related Issue

Builds on [002-pr-batch-source-page-id-lookups.md](002-pr-batch-source-page-id-lookups.md), which moved page-detail source/revision/vote/file acquisition to a collection-level page-ID preflight, and complements [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), and [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), which remove duplicate resolved page-ID AMC requests after ID acquisition.

No upstream issue was filed from this local workspace.

## Changes

- Group unresolved `Page` entries by first-seen `f"{page.get_url()}/norender/true/noredirect/true"` inside `PageCollection._acquire_page_ids(...)`.
- Send one direct GET per unique page-ID lookup URL through `RequestUtil.request(...)`.
- Apply each parsed `WIKIREQUEST.info.pageId` value to every duplicate page object in that URL group.
- Preserve duplicate public collection entries, already-acquired ID skipping, first-seen request ordering, response type checks, missing-ID error messages, lazy `Page.id`, and source/revision/vote/file acquisition paths.
- Add a focused public-interface regression test for duplicate unresolved page URLs in `PageCollection.get_page_ids()`.

## Type Of Change

- Performance and reliability improvement
- Test-covered behavior fix

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Avoid duplicate direct page-ID lookup GETs for repeated unresolved page URLs. | `TestPageCollectionAcquire.test_acquire_page_ids_deduplicates_duplicate_page_urls` asserts one `/norender/true/noredirect/true` URL for two unresolved page objects with the same page URL. | Reverting the grouping makes the RED test fail because `RequestUtil.request(...)` receives the duplicate URL twice. |
| Preserve duplicate public collection entries and page object identity. | The focused test keeps both `Page` objects and verifies both receive the parsed page ID. | A change that collapses the collection or updates only the first duplicate leaves the duplicate page without an acquired ID. |
| Preserve normal page detail acquisition behavior. | `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire -q`; `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_page_file.py tests/unit/test_site.py -q`; `uv run --extra test pytest tests/unit -q`. | Regression would break page ID preflight, source/revision/vote/file batching, lazy page properties, page/site tests, or broad unit tests. |
| Preserve static quality gates. | `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Formatting, lint, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `bdab235 perf(page): deduplicate page id fetch urls`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_deduplicates_duplicate_page_urls -q` failed before the fix because `RequestUtil.request(...)` received the duplicate URL twice.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_deduplicates_duplicate_page_urls -q`
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 21 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_page_file.py tests/unit/test_site.py -q` passed 208 tests.
- `uv run --extra test pytest tests/unit -q` passed 621 tests.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

## Acceptance Criteria

- Duplicate unresolved `Page` objects with the same direct page-ID lookup URL send one direct GET.
- First-seen unique page-ID lookup URL order is preserved in request construction.
- The public `PageCollection` length, ordering, and duplicate object entries remain unchanged.
- Every duplicate page entry receives the parsed page ID from the successful shared response.
- Pages with already-acquired IDs are still skipped.
- Non-`httpx.Response` results still raise `UnexpectedException`.
- Missing `WIKIREQUEST.info.pageId` still raises `UnexpectedException` naming the first page in that URL group.
- Existing lazy `Page.id`, source acquisition, revision-list acquisition, vote-list acquisition, file-list acquisition, page parsing, and mutation paths are unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Large page source, revision, vote, and file collection workflows can accumulate duplicate page objects through merged search results, retry queues, caller-side joins, or evidence ledgers. The collection-level page-ID preflight should avoid redundant direct page GETs for the same page URL while preserving the caller's original queue shape.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence included large source collection, browser-free publishing, page evidence checks, and page detail collection where page-ID preflight latency affects downstream source/revision/vote/file requests.
- Earlier local drafts made page-detail paths use collection-level page-ID preflight and then removed duplicate resolved page-ID AMC requests from source, revision-list, file-list, and vote-list acquisition.
- The same duplicate-request pattern was previously found and fixed in private message details, forum post sources, forum post revisions, forum post revision HTML, forum thread post/detail acquisition, page revision source/HTML fetching, and adjacent page detail acquisition.
- Keep local rollout paths, account names, and corpus-specific identifiers out of any upstream discussion.

## Additional Notes

This slice does not change resolved page-ID source/revision/vote/file AMC request deduplication, ListPages search results, direct single-page lazy `Page.id` behavior, or mutation methods. It only removes duplicate direct page-ID lookup URLs before existing collection-level page detail acquisition continues.
