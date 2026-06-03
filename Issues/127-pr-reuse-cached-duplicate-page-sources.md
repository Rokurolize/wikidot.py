# PR Draft: Reuse Cached Duplicate Page Sources

## Summary

`PageCollection.get_page_sources()` already skips pages whose source is cached, and it already deduplicates uncached duplicate page IDs before fetching `viewsource/ViewSourceModule`. Before this fix, a collection containing both a cached page and an uncached duplicate with the same resolved page ID still fetched source for the uncached duplicate instead of reusing the cached source already present in the same collection.

This fix indexes cached source text by page ID, copies that text into uncached same-ID duplicate pages before building AMC requests, and only fetches page IDs that remain unresolved. Public collection membership and ordering remain unchanged, and the copied `PageSource` is owned by the duplicate `Page` object rather than sharing the cached page's `PageSource` instance.

## Related Issue

Builds directly on [008-pr-skip-cached-source-fetches.md](008-pr-skip-cached-source-fetches.md), which established cached-source skipping, and [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), which established that duplicate page IDs should not trigger duplicate source requests. It also preserves source retry/partial-success behavior from [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md) and [051-pr-preserve-source-batch-successes.md](051-pr-preserve-source-batch-successes.md), and follows the cached duplicate reuse pattern from [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md) and [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md).

No upstream issue was filed from this local workspace.

## Changes

- Build a `page.id -> wiki_text` map from already cached page sources in the collection.
- Populate uncached duplicate pages from that map before constructing `viewsource/ViewSourceModule` source-fetch requests.
- Preserve page ownership by creating a new `PageSource(page, wiki_text)` for each duplicate target page.
- Keep first-seen request order and existing uncached duplicate grouping for the remaining unresolved page IDs.
- Add a focused regression where one duplicate page is cached and another duplicate with the same page ID is uncached.
- Preserve retry-aware source fetches, failed retry handling, source parsing, malformed-source error behavior, lazy `Page.source`, explicit `Page.refresh_source()`, and source iterator behavior.

## Type Of Change

- Performance/reliability improvement
- Cache behavior improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Cached source from a duplicate page ID must be reused within the same collection. | `TestPageCollectionAcquire.test_acquire_sources_reuses_cached_duplicate_page_source` asserts the uncached duplicate receives `cached page source`. | The RED test failed before the fix because the duplicate source path called `viewsource/ViewSourceModule` for the same page ID. |
| Reusing cached duplicate source must avoid unnecessary network work. | The same focused test asserts neither plain `amc_request(...)` nor retry-aware `amc_request_with_retry(...)` is called. | A regression that fetches source for the duplicate fails the not-called assertions. |
| Cached duplicate reuse must preserve `PageSource` ownership. | The focused test asserts `duplicate_page._source.page is duplicate_page`. | Sharing the cached page's `PageSource` object would make the source point at the wrong owning page object. |
| Existing source collection behavior remains intact. | `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 25 tests, and `uv run pytest tests/unit/test_page.py -q` passed 101 tests. | Regressions in retry, exhausted retry, cached-source skipping, duplicate uncached source propagation, source parsing, malformed-source handling, or lazy behavior reject this local completion claim. |
| Adjacent page workflows stay green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 193 tests. | Regressions in source iteration, page revision acquisition, page/site reads, or publishing-adjacent search behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `55887b6 perf(page): reuse cached duplicate page sources`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_reuses_cached_duplicate_page_source -q` failed before the fix because the uncached duplicate sent a `viewsource/ViewSourceModule` request for the already cached page ID.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_reuses_cached_duplicate_page_source -q`
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 25 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 101 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 193 tests.
- `uv run pytest tests/unit -q` passed 682 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- A cached source on one page object is reused for uncached collection entries with the same resolved page ID.
- No AMC source request is sent when every uncached page can be satisfied from cached duplicates in the same collection.
- The duplicate target page receives its own `PageSource` object whose `page` points at that target page.
- Uncached duplicate page IDs with no cached source still use the existing one-request-per-ID source fetch path.
- Exhausted retry results still leave only unresolved page IDs unacquired.
- Existing source extraction, source text normalization, cached-source skipping, duplicate uncached grouping, malformed-source error behavior, lazy `Page.source`, explicit `Page.refresh_source()`, page ID acquisition, source iterator fallback behavior, and mutation paths remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Large source collection, source auditing, and publication verification workflows can carry duplicate page objects from merged searches, retry queues, or caller-side ledgers. If one duplicate page object already has source text, fetching the same `ViewSourceModule` response again adds avoidable AMC work and another failure point. Reusing cached duplicate source keeps collection source acquisition consistent with the existing cached-source skip and duplicate-ID dedupe rules while preserving the caller-visible collection shape.

## Local Evidence, Not For Upstream Paste

- Existing local drafts established page source reads as a practical rollout-backed surface for large source collection, publication verification, and source auditing.
- Issue 008 established cached-source skipping for retry ergonomics, and Issue 062 established duplicate page IDs as a realistic source-fetch performance lead.
- Issues 125 and 126 showed the same cached-duplicate reuse gap after request deduplication in adjacent source acquisition paths.
- The refreshed complexity scan continues to flag `src/wikidot/module/page.py` around source acquisition as a worthwhile audit area.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not change source request construction, retry policy, source text normalization, malformed response handling, duplicate uncached source grouping, lazy property return types, page ID lookup, source iterator fallback behavior, publishing, or mutation methods. It only lets already cached source text satisfy duplicate uncached page entries in the same collection before any source-fetch request is built.
