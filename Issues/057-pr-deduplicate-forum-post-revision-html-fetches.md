# PR Draft: Deduplicate Forum Post Revision HTML Fetch IDs

## Summary

`ForumPostRevisionCollection.get_htmls()` fetches HTML content for each uncached revision with `forum/sub/ForumPostRevisionModule`. If a collection contains duplicate `ForumPostRevision.id` entries, the existing public behavior keeps both entries in the list and should cache HTML on each one, but the request path still sent duplicate revision HTML fetches.

The fix preserves the collection shape, first-seen ordering, retry handling, cached-HTML skipping, partial-success behavior, and lazy `ForumPostRevision.html` semantics while deduplicating uncached revision HTML requests by first-seen revision ID.

## Related Issue

Builds on the retry-aware forum post revision work in [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md) and the revision-list deduplication work in [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md). Also follows the ordered duplicate-ID request pattern from [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md). No upstream issue filed yet.

## Changes

- Deduplicate uncached `ForumPostRevision.id` values inside `ForumPostRevisionCollection.get_htmls()` before constructing revision HTML AMC requests.
- Preserve first-seen revision ID order for the request batch.
- Apply the single successful HTML response to every uncached duplicate revision entry with the same ID.
- Preserve cached-HTML skipping, retry-aware AMC, `None` retry-result handling, lazy `ForumPostRevision.html`, list membership, and mutation paths.
- Add a focused regression test covering duplicate revision IDs in a revision collection.

## Type Of Change

- [ ] Bug fix
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
| R1: Duplicate uncached revision IDs do not trigger duplicate HTML fetches | `get_htmls()` calls `amc_request_with_retry(...)` with one `ForumPostRevisionModule` request per first-seen uncached revision ID | `test_get_htmls_deduplicates_duplicate_revision_ids` | Reverting the dedupe makes the focused test fail with `ValueError: zip() argument 2 is shorter than argument 1` |
| R2: Duplicate collection entries keep behavior | Every uncached duplicate revision entry receives the returned HTML content and the method still returns the original collection | Same focused test | A change that collapses duplicate list entries or populates only the first duplicate would fail the focused test |
| R3: Existing forum revision behavior is preserved | Retry, partial-success, cached-HTML skip, lazy HTML acquisition, and broader forum tests remain green | Commands listed below | Existing revision tests fail if retry, cache, or lazy HTML semantics change |

## Testing

Local implementation commit: `465a9b9 perf(forum_post_revision): deduplicate revision html fetch ids`

- [x] `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_deduplicates_duplicate_revision_ids -q` failed before the fix with `ValueError: zip() argument 2 is shorter than argument 1`, then passed after the fix with one revision HTML request.
- [x] `uv run --extra test pytest tests/unit/test_forum_post_revision.py -q` passed with 30 tests.
- [x] `uv run --extra test pytest tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed with 61 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 611 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`

## Acceptance Criteria

- Duplicate uncached revision IDs in `ForumPostRevisionCollection.get_htmls()` are fetched once.
- First-seen request order is preserved.
- The original collection and duplicate list entries are preserved.
- Each uncached duplicate revision entry receives the same successful HTML content.
- Existing `None` retry results still leave only the permanently failed revision ID group unacquired.
- Already cached revision HTML is still skipped.
- Lazy `ForumPostRevision.html`, `acquire_all_for_posts(...)`, revision parsing, `rev_no` assignment, forum post source fetching, edit/reply mutation methods, and request retry policy remain unchanged.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Forum post revision inspection is a read-heavy workflow for moderation, archiving, diffing, and audit tooling. Deduplicating identical revision HTML IDs avoids redundant AMC work while preserving the public collection shape and retry-aware partial-success behavior.

## Local Evidence, Not For Upstream Paste

- Local forum read hardening in [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), and [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md) established forum post inspection as an active read-heavy surface.
- The refreshed complexity scan keeps `src/wikidot/module/forum_post_revision.py` in the remaining batch/revision hotspot set, supporting another narrow request-deduplication pass.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice does not change revision-list acquisition, forum post parsing, revision ordering, `ForumPostRevision.html` return type, source fetching, edit/reply mutation methods, or the retry policy. It only removes duplicate revision HTML requests for repeated uncached revision IDs in the existing collection read path.
