# PR Draft: Deduplicate Forum Post Revision With-HTML Fetch IDs

## Summary

`ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` first fetches revision lists with `forum/sub/ForumPostRevisionsModule`, parses them into `ForumPostRevisionCollection` objects, then fetches HTML content for every uncached parsed revision with `forum/sub/ForumPostRevisionModule`. If a parsed revision list contains duplicate `ForumPostRevision.id` entries, the public collection shape should preserve both entries, but the optional HTML path still sent duplicate revision HTML requests.

The fix preserves the post-ID keyed result dictionary, parsed collection contents, first-seen ordering, retry handling, `None` retry-result handling, optional `with_html=True` semantics, and lazy `ForumPostRevision.html` behavior while deduplicating uncached parsed revision HTML requests by first-seen revision ID.

## Related Issue

Builds on the retry-aware forum post revision work in [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), the revision-list request deduplication in [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), and the collection-level revision HTML deduplication in [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md). No upstream issue filed yet.

## Changes

- Deduplicate uncached parsed `ForumPostRevision.id` values inside `acquire_all_for_posts(..., with_html=True)` before constructing optional revision HTML AMC requests.
- Preserve first-seen revision ID order for the optional HTML request batch.
- Apply one successful HTML response to every uncached parsed duplicate revision entry with the same ID.
- Preserve duplicate entries in each returned `ForumPostRevisionCollection`.
- Preserve cached-HTML skipping, retry-aware AMC, `None` retry-result handling, `get_htmls()`, lazy `ForumPostRevision.html`, post-ID keyed result shape, and mutation paths.
- Add a focused regression test that mutates the revision-list fixture to parse duplicate revision IDs through the public acquisition path.

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
| R1: Duplicate parsed revision IDs do not trigger duplicate optional HTML fetches | `acquire_all_for_posts(..., with_html=True)` calls `amc_request_with_retry(...)` with one `ForumPostRevisionModule` request per first-seen uncached parsed revision ID | `test_acquire_all_for_posts_with_html_deduplicates_duplicate_revision_ids` | Reverting the dedupe makes the focused test fail with `ValueError: zip() argument 2 is shorter than argument 1` |
| R2: Parsed duplicate entries keep behavior | Duplicate parsed revision entries remain in the returned collection and all receive the returned HTML content | Same focused test | A change that collapses duplicate collection entries or populates only the first duplicate would fail the focused test |
| R3: Existing forum revision behavior is preserved | Revision parsing, revision-list dedupe, collection-level `get_htmls()` dedupe, retry, partial-success, cached-HTML skip, lazy HTML acquisition, and broader unit tests remain green | Commands listed below | Existing revision tests fail if retry, cache, lazy HTML, or result shape semantics change |

## Testing

Local implementation commit: `09e3a05 perf(forum_post_revision): deduplicate with-html revision ids`

- [x] `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_with_html_deduplicates_duplicate_revision_ids -q` failed before the fix with `ValueError: zip() argument 2 is shorter than argument 1`, then passed after the fix with one revision HTML request per unique parsed revision ID.
- [x] `uv run --extra test pytest tests/unit/test_forum_post_revision.py -q` passed with 31 tests.
- [x] `uv run --extra test pytest tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed with 62 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 612 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`

## Acceptance Criteria

- Duplicate uncached parsed revision IDs in `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` are fetched once.
- First-seen request order is preserved.
- The returned mapping remains keyed by post ID.
- Duplicate parsed revision entries remain in the returned `ForumPostRevisionCollection`.
- Each uncached parsed duplicate revision entry receives the same successful HTML content.
- Existing `None` retry results still leave only the permanently failed revision ID group unacquired.
- Already cached revision HTML is still skipped.
- `get_htmls()`, lazy `ForumPostRevision.html`, revision-list acquisition, revision parsing, `rev_no` assignment, forum post source fetching, edit/reply mutation methods, and request retry policy remain unchanged.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Forum post revision inspection is a read-heavy workflow for moderation, archiving, diffing, and audit tooling. The multi-post acquisition helper already provides an optional `with_html=True` batch path; deduplicating identical parsed revision HTML IDs avoids redundant AMC work while preserving the public collection shape and retry-aware partial-success behavior.

## Local Evidence, Not For Upstream Paste

- Local forum read hardening in [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), and [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md) established forum post inspection as an active read-heavy surface.
- The refreshed complexity scan kept `src/wikidot/module/forum_post_revision.py` in the remaining batch/revision hotspot set, especially the optional `with_html=True` path that walks all parsed revisions before issuing HTML requests.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice does not change revision-list acquisition, forum post parsing, revision ordering, `ForumPostRevision.html` return type, source fetching, edit/reply mutation methods, or the retry policy. It only removes duplicate optional revision HTML requests for repeated parsed revision IDs in the existing multi-post read path.
