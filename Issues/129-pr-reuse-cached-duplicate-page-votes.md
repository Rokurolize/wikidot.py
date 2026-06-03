# PR Draft: Reuse Cached Duplicate Page Vote Lists

## Summary

`PageCollection.get_page_votes()` already skips pages whose vote list is cached, and it already deduplicates uncached duplicate page IDs before fetching `pagerate/WhoRatedPageModule`. Before this fix, a collection containing both a cached page and an uncached duplicate with the same resolved page ID still fetched the vote list for the uncached duplicate instead of reusing the cached vote list already present in the same collection.

This fix indexes cached page vote collections by page ID, clones cached vote data into uncached same-ID duplicate pages before building AMC requests, and only fetches page IDs that remain unresolved. Public collection membership and ordering remain unchanged, and the duplicate target receives its own `PageVoteCollection` and `PageVote` objects bound to the duplicate `Page` object rather than sharing the cached page's objects.

## Related Issue

Builds directly on [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md), which established cached page-detail skipping, and [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), which established that duplicate page IDs should not trigger duplicate vote-list requests. It also preserves WhoRated parser scoping from [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md) and follows the cached duplicate reuse pattern from [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md) and [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md).

No upstream issue was filed from this local workspace.

## Changes

- Build a `page.id -> PageVoteCollection` map from already cached page vote lists in the collection.
- Populate uncached duplicate pages from that map before constructing `pagerate/WhoRatedPageModule` requests.
- Preserve page ownership by creating a new `PageVoteCollection(page, votes)` and fresh `PageVote(page, user, value)` objects for each duplicate target page.
- Keep first-seen request order and existing uncached duplicate grouping for the remaining unresolved page IDs.
- Add a focused regression where one duplicate page has cached votes and another duplicate with the same page ID is uncached.
- Preserve retry-aware vote-list fetches, failed retry handling, WhoRated parser scoping, mismatch errors, lazy `Page.votes`, and adjacent page/site workflows.

## Type Of Change

- Performance/reliability improvement
- Cache behavior improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Cached vote lists from a duplicate page ID must be reused within the same collection. | `TestPageCollectionAcquire.test_acquire_votes_reuses_cached_duplicate_page_votes` asserts the uncached duplicate receives the cached vote user and value. | The RED test failed before the fix because the duplicate path called `pagerate/WhoRatedPageModule` for the already cached page ID. |
| Reusing cached duplicate vote lists must avoid unnecessary network work. | The same focused test asserts neither plain `amc_request(...)` nor retry-aware `amc_request_with_retry(...)` is called. | A regression that fetches the vote list for the duplicate fails the not-called assertions. |
| Cached duplicate reuse must preserve page ownership. | The focused test asserts the duplicate target has a distinct `PageVoteCollection`, a distinct `PageVote`, and `duplicate_page._votes[0].page is duplicate_page`. | Sharing the cached page's collection or vote object would make the vote point at the wrong owning page object. |
| Existing page vote-list behavior remains intact. | `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 27 tests, and `uv run pytest tests/unit/test_page.py -q` passed 103 tests. | Regressions in cached detail skipping, duplicate uncached request grouping, failed retry handling, WhoRated parser scoping, mismatch errors, or lazy behavior reject this local completion claim. |
| Adjacent page workflows stay green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 172 tests. | Regressions in page vote access, page/site reads, source iteration, or publishing-adjacent search behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `b94f206 perf(page): reuse cached duplicate page votes`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_reuses_cached_duplicate_page_votes -q` failed before the fix because the uncached duplicate sent a `pagerate/WhoRatedPageModule` request for the already cached page ID.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_reuses_cached_duplicate_page_votes -q`
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 27 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 103 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 172 tests.
- `uv run pytest tests/unit -q` passed 684 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- A cached vote list on one page object is reused for uncached collection entries with the same resolved page ID.
- No AMC vote-list request is sent when every uncached page can be satisfied from cached duplicates in the same collection.
- The duplicate target page receives its own `PageVoteCollection` whose `page` points at that target page.
- Every copied vote receives its own `PageVote` object whose `page` points at the duplicate target page.
- Vote users and numeric values are preserved.
- Uncached duplicate page IDs with no cached vote list still use the existing one-request-per-ID vote-list fetch path.
- Exhausted retry results still leave only unresolved page IDs unacquired.
- Existing WhoRated parsing, cached-detail skipping, duplicate uncached grouping, mismatch error behavior, lazy `Page.votes`, page ID acquisition, source/revision/file acquisition, and mutation paths remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Large page inspection, moderation review, publishing verification, and retry-ledger workflows can carry duplicate page objects from merged searches or caller-side queues. If one duplicate page object already has its vote list, fetching the same `WhoRatedPageModule` response again adds avoidable AMC work and another failure point. Reusing cached duplicate vote lists keeps collection vote acquisition consistent with the existing cached-detail skip and duplicate-ID dedupe rules while preserving the caller-visible collection shape.

## Local Evidence, Not For Upstream Paste

- Existing local drafts established page detail reads as a practical rollout-backed surface for large source collection, publication verification, page inspection, and audit workflows.
- Issue 009 established cached page-detail skipping, and Issue 065 established duplicate page IDs as a realistic vote-list performance lead.
- Issues 127 and 128 showed the same cached-duplicate reuse gap after request deduplication in adjacent page source and page revision-list paths.
- The refreshed complexity scan continues to flag `src/wikidot/module/page.py` around page acquisition as a worthwhile audit area.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not change vote-list request construction, retry policy, WhoRated parsing, failed retry behavior, duplicate uncached grouping, lazy property return types, source/revision/file fetching, publishing, or mutation methods. It only lets already cached vote lists satisfy duplicate uncached page entries in the same collection before any vote-list request is built.
