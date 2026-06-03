# PR Draft: Deduplicate Forum Post Revision Fetch IDs

## Summary

`ForumPostRevisionCollection.acquire_all_for_posts(...)` fetches revision lists for each input forum post with `forum/sub/ForumPostRevisionsModule` and returns a dictionary keyed by post ID. If the input list contains the same post ID more than once, the public result already collapses to one dictionary entry, but the read path still does redundant revision-list requests for the duplicate ID.

The fix keeps the post-ID keyed result contract, retry handling, exhausted retry errors, revision parsing, ordering, and optional HTML acquisition stable while deduplicating revision-list fetch requests by first-seen post ID.

## Related Issue

Builds on the retry-aware forum post revision work in [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md). Also follows the ordered deduplication pattern from [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md). Follow-up HTML-fetch deduplication drafts: [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md) and [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md). No upstream issue filed yet.

## Changes

- Deduplicate `acquire_all_for_posts(...)` input posts by `post.id` before constructing revision-list AMC requests.
- Preserve first-seen post ID order for the request batch.
- Preserve the existing dictionary keyed by post ID.
- Preserve revision parsing, `rev_no` assignment, exhausted retry errors, optional `with_html=True` acquisition, cached-HTML skipping, and mutation paths.
- Add a focused regression test covering duplicate post IDs in multi-post revision-list acquisition.

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
| R1: Duplicate forum post IDs do not trigger duplicate revision-list fetches | `acquire_all_for_posts(...)` calls `amc_request_with_retry(...)` with one `ForumPostRevisionsModule` request per first-seen post ID | `test_acquire_all_for_posts_deduplicates_duplicate_post_ids` | Reverting the dedupe makes the focused test fail with `zip(strict=True)` length mismatch or duplicate request payloads |
| R2: Existing result shape is preserved | The returned mapping remains keyed by post ID and uses the first-seen post object for the collection | Same focused test | A change that returns duplicate entries would break the existing `dict[int, ForumPostRevisionCollection]` contract |
| R3: Existing forum revision behavior is preserved | Revision parsing, retry/exhausted-error semantics, optional HTML acquisition, and broad unit tests remain green | Commands listed below | Existing revision tests fail if parsing, retry, or HTML semantics change |

## Testing

Local implementation commit: `858f79a perf(forum_post_revision): deduplicate revision fetch ids`

- [x] `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_deduplicates_duplicate_post_ids -q` failed before the fix with `ValueError: zip() argument 2 is shorter than argument 1`, then passed after the fix with one revision-list request.
- [x] `uv run --extra test pytest tests/unit/test_forum_post_revision.py -q` passed with 29 tests.
- [x] `uv run --extra test pytest tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed with 60 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 610 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`

## Acceptance Criteria

- Duplicate post IDs in `ForumPostRevisionCollection.acquire_all_for_posts(...)` input are fetched once.
- First-seen request order is preserved.
- The returned mapping remains keyed by post ID.
- The first-seen post object remains the `ForumPostRevisionCollection.post` for that post ID.
- Existing `None` retry results for required revision-list reads still raise the same post-ID-specific `UnexpectedException`.
- Successful revision parsing, newest-to-oldest reversal, `rev_no` assignment, optional `with_html=True`, `get_htmls()`, lazy `ForumPostRevision.html`, `ForumPost.edit(...)`, and `ForumThread.reply(...)` remain unchanged.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Forum post revision inspection is a read-heavy workflow for moderation, archiving, diffing, and audit tooling. Deduplicating identical revision-list IDs avoids redundant AMC work while preserving the existing post-ID keyed result shape and retry-aware behavior.

## Local Evidence, Not For Upstream Paste

- Local forum read hardening in [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), and [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md) established forum post inspection as an active read-heavy surface.
- The refreshed complexity scan flags `src/wikidot/module/forum_post_revision.py` as a module worth auditing for repeated request construction and nested list handling.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice does not change forum post revision parsing, revision HTML fetching, lazy HTML behavior, forum post source fetching, edit/reply mutation methods, request retry policy, or dictionary result shape. It only removes duplicate revision-list requests for repeated post IDs in the existing multi-post read path.
