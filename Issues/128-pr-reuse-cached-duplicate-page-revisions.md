# PR Draft: Reuse Cached Duplicate Page Revision Lists

## Summary

`PageCollection.get_page_revisions()` already skips pages whose revision list is cached, deduplicates uncached duplicate page IDs before fetching `history/PageRevisionListModule`, and reuses parsed revision-list rows for duplicate uncached pages. Before this fix, a collection containing both a cached page and an uncached duplicate with the same resolved page ID still fetched the revision list for the uncached duplicate instead of reusing the cached revision list already present in the same collection.

This fix indexes cached page revision collections by page ID, clones cached revision metadata into uncached same-ID duplicate pages before building AMC requests, and only fetches page IDs that remain unresolved. Public collection membership and ordering remain unchanged, and the duplicate target receives its own `PageRevisionCollection`, `PageRevision`, and cached `PageSource` wrappers bound to the duplicate `Page` object rather than sharing the cached page's objects.

## Related Issue

Builds directly on [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md), which established cached page-detail skipping, [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), which established that duplicate page IDs should not trigger duplicate revision-list requests, and [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), which established that duplicate uncached page IDs should reuse parsed revision-list rows. It also preserves failed-retry visibility from [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md) and follows the cached duplicate reuse pattern from [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md) and [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md).

No upstream issue was filed from this local workspace.

## Changes

- Build a `page.id -> PageRevisionCollection` map from already cached page revision lists in the collection.
- Populate uncached duplicate pages from that map before constructing `history/PageRevisionListModule` requests.
- Preserve page ownership by creating a new `PageRevisionCollection(page, revisions)` and fresh `PageRevision(page=page, ...)` objects for each duplicate target page.
- Preserve cached per-revision source text by creating new `PageSource(page, wiki_text)` wrappers, and preserve cached per-revision HTML strings.
- Keep first-seen request order and existing uncached duplicate grouping for the remaining unresolved page IDs.
- Add a focused regression where one duplicate page has cached revisions and another duplicate with the same page ID is uncached.
- Preserve retry-aware revision-list fetches, failed retry handling, revision-row parsing, malformed-revision error behavior, lazy `Page.revisions`, source/HTML data on revision objects, and adjacent page/site workflows.

## Type Of Change

- Performance/reliability improvement
- Cache behavior improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Cached revision lists from a duplicate page ID must be reused within the same collection. | `TestPageCollectionAcquire.test_acquire_revisions_reuses_cached_duplicate_page_revisions` asserts the uncached duplicate receives the cached revision metadata. | The RED test failed before the fix because the duplicate path called `history/PageRevisionListModule` for the already cached page ID. |
| Reusing cached duplicate revision lists must avoid unnecessary network work. | The same focused test asserts neither plain `amc_request(...)` nor retry-aware `amc_request_with_retry(...)` is called. | A regression that fetches the revision list for the duplicate fails the not-called assertions. |
| Cached duplicate reuse must preserve page ownership. | The focused test asserts the duplicate target has a distinct `PageRevisionCollection`, a distinct `PageRevision`, and `duplicate_page._revisions[0].page is duplicate_page`. | Sharing the cached page's collection or revision object would make the revision point at the wrong owning page object. |
| Cached duplicate reuse must preserve cached revision source and HTML data safely. | The focused test asserts the duplicate revision receives a distinct `PageSource` wrapper whose `page` is the duplicate page, the same `wiki_text`, and the cached HTML string. | Sharing the cached revision's `PageSource` object would make the source point at the wrong owning page object. Dropping cached source or HTML would force later duplicate fetch work. |
| Existing page revision-list behavior remains intact. | `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 26 tests, and `uv run pytest tests/unit/test_page.py -q` passed 102 tests. | Regressions in cached detail skipping, duplicate uncached request grouping, parsed-row reuse, failed retry handling, malformed-row errors, or lazy behavior reject this local completion claim. |
| Adjacent page workflows stay green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 194 tests. | Regressions in page source acquisition, page revision source/HTML access, page/site reads, or publishing-adjacent search behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `9aecc45 perf(page): reuse cached duplicate revisions`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_reuses_cached_duplicate_page_revisions -q` failed before the fix because the uncached duplicate sent a `history/PageRevisionListModule` request for the already cached page ID.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_reuses_cached_duplicate_page_revisions -q`
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 26 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 102 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 194 tests.
- `uv run pytest tests/unit -q` passed 683 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- A cached revision list on one page object is reused for uncached collection entries with the same resolved page ID.
- No AMC revision-list request is sent when every uncached page can be satisfied from cached duplicates in the same collection.
- The duplicate target page receives its own `PageRevisionCollection` whose `page` points at that target page.
- Every copied revision receives its own `PageRevision` object whose `page` points at the duplicate target page.
- Cached per-revision source text is preserved through a fresh `PageSource` wrapper bound to the duplicate target page.
- Cached per-revision HTML strings are preserved.
- Uncached duplicate page IDs with no cached revision list still use the existing one-request-per-ID revision-list fetch path.
- Exhausted retry results still leave only unresolved page IDs unacquired.
- Existing revision-list parsing, cached-detail skipping, duplicate uncached grouping, parsed-row reuse, malformed-row error behavior, lazy `Page.revisions`, page ID acquisition, page source fetching, revision source/HTML fetching, and mutation paths remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Large history inspection, source auditing, publication verification, and retry-ledger workflows can carry duplicate page objects from merged searches or caller-side queues. If one duplicate page object already has its revision list, fetching the same `PageRevisionListModule` response again adds avoidable AMC work and another failure point. Reusing cached duplicate revision lists keeps collection revision acquisition consistent with the existing cached-detail skip, duplicate-ID dedupe, and parsed-row reuse rules while preserving the caller-visible collection shape.

## Local Evidence, Not For Upstream Paste

- Existing local drafts established page revision-list reads as a practical rollout-backed surface for large source collection, publication verification, history inspection, and audit workflows.
- Issue 009 established cached page-detail skipping, Issue 063 established duplicate page IDs as a realistic revision-list performance lead, and Issue 074 showed that one parsed revision-list response should populate duplicate uncached page objects.
- Issues 126 and 127 showed the same cached-duplicate reuse gap after request deduplication in adjacent page revision-data and page source paths.
- The refreshed complexity scan continues to flag `src/wikidot/module/page.py` around page acquisition as a worthwhile audit area.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not change revision-list request construction, retry policy, row parsing, failed retry behavior, duplicate uncached grouping, lazy property return types, page source fetching, revision source/HTML fetching, publishing, or mutation methods. It only lets already cached revision lists satisfy duplicate uncached page entries in the same collection before any revision-list request is built.
