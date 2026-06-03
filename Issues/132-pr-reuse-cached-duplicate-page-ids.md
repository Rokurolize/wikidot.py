# PR Draft: Reuse Cached Duplicate Page IDs

## Summary

`PageCollection.get_page_ids()` already skips pages whose page ID is cached, and it already deduplicates duplicate unresolved page-ID lookup URLs before requesting `/<page>/norender/true/noredirect/true`. Before this fix, a collection containing both an ID-cached page and an unresolved duplicate with the same page URL still performed a direct GET for the duplicate instead of reusing the cached page ID already present in the same collection.

This fix indexes cached page IDs by the same page-ID lookup URL used for unresolved requests, copies the cached ID into unresolved duplicate pages before building the direct GET batch, and only requests URLs that remain unresolved. Public collection membership, object identity, and first-seen unresolved URL order remain unchanged.

## Related Issue

Builds directly on [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), which established that duplicate unresolved page URLs should not trigger duplicate page-ID lookup GETs. It also preserves the collection-level page-ID preflight from [002-pr-batch-source-page-id-lookups.md](002-pr-batch-source-page-id-lookups.md), cached source/detail reuse from [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), and [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), and follows the same cached duplicate reuse pattern as [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md).

No upstream issue was filed from this local workspace.

## Changes

- Build a page-ID lookup URL to page-ID map from already acquired pages in the input collection.
- Populate unresolved duplicate pages from that map before constructing direct page-ID lookup GETs.
- Keep the existing unresolved URL grouping for pages that still need a direct lookup.
- Add a focused regression where one page has a cached ID and another same-URL page is unresolved.
- Preserve response type checks, missing-ID errors, lazy `Page.id`, source acquisition, revision-list acquisition, vote-list acquisition, file-list acquisition, page parsing, and mutation paths.

## Type Of Change

- Performance/reliability improvement
- Cache behavior improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A cached page ID from a same-URL page must be reused inside the same collection. | `TestPageCollectionAcquire.test_acquire_page_ids_reuses_cached_duplicate_page_url` asserts the unresolved duplicate receives page ID `333`. | The RED test failed before the fix because `RequestUtil.request(...)` was called for the duplicate lookup URL. |
| Reusing cached duplicate IDs must avoid unnecessary direct GET work. | The same focused test asserts `RequestUtil.request(...)` is not called when the unresolved duplicate can be satisfied from the cached page. | A regression that requests the duplicate URL fails the not-called assertion. |
| Existing unresolved duplicate URL dedupe remains intact. | `TestPageCollectionAcquire.test_acquire_page_ids_deduplicates_duplicate_page_urls` remains covered by `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q`, which passed 29 tests. | Regressions that reintroduce duplicate unresolved URLs or update only the first duplicate reject the local completion claim. |
| Page detail preflight behavior remains intact. | `uv run pytest tests/unit/test_page.py -q` passed 105 tests, and `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_page_file.py -q` passed 174 tests. | Regressions in source, revision-list, vote-list, file-list, lazy property, or detail batching behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `fef74c6 perf(page): reuse cached duplicate page ids`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_reuses_cached_duplicate_page_url -q` failed before the fix because `RequestUtil.request(...)` was called once for `https://test-site.wikidot.com/test-page/norender/true/noredirect/true`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_reuses_cached_duplicate_page_url -q`
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 29 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 105 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_page_file.py -q` passed 174 tests.
- `uv run pytest tests/unit -q` passed 687 tests.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page.py`
- `uv run ruff format --check src/wikidot/module/page.py tests/unit/test_page.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- A cached page ID on one page object is reused for unresolved collection entries with the same page-ID lookup URL.
- No direct page-ID lookup GET is sent when every unresolved page can be satisfied from cached same-URL pages in the same collection.
- Unresolved duplicate page URLs with no cached ID still use the existing one-request-per-URL fetch path.
- First-seen unresolved URL order is preserved for remaining direct GET requests.
- Pages with already acquired IDs remain unchanged.
- Non-`httpx.Response` results still raise `UnexpectedException`.
- Missing `WIKIREQUEST.info.pageId` still raises `UnexpectedException` naming the first page in that URL group.
- Existing lazy `Page.id`, source acquisition, revision-list acquisition, vote-list acquisition, file-list acquisition, page parsing, publish helpers, and mutation paths are unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Large page collection workflows can accumulate duplicate page objects through merged search results, retry queues, source ledgers, or caller-side joins. If one object already has the page ID, resolving the same page URL again adds avoidable direct GET latency and another failure point. Reusing cached duplicate page IDs keeps page-ID acquisition consistent with existing cached-skip and duplicate-URL dedupe behavior while preserving the caller-visible collection shape.

## Local Evidence, Not For Upstream Paste

- Existing local drafts established page source, revision, vote, and file acquisition as practical rollout-backed surfaces where page-ID preflight latency affects downstream collection work.
- Issue 066 established duplicate page-ID lookup URLs as a realistic performance lead, while Issues 127 through 130 showed the same cached-duplicate reuse gap after request deduplication in adjacent page detail paths.
- The refreshed complexity scan continues to flag `src/wikidot/module/page.py` around page-detail acquisition as a worthwhile audit area.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not change page URL construction, direct response parsing, response type validation, missing-ID error messages, resolved page-detail AMC request deduplication, lazy property return types, ListPages parsing, publish helpers, or mutation methods. It only lets already cached page IDs satisfy unresolved duplicate page entries in the same collection before any direct page-ID lookup GET is built.
