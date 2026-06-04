# PR Draft: Cache Direct Post Revision Acquisition

## Summary

`ForumPost.revisions` caches the `ForumPostRevisionCollection` it lazily reads from `ForumPostRevisionCollection.acquire_all_for_posts([post])`, and both direct revision-list helpers already check `post._revisions` before making AMC requests. Before this fix, callers that used `ForumPostRevisionCollection.acquire_all(post)` or `acquire_all_for_posts([post])` directly received the fetched revision collection but left `post._revisions` unset. A later `post.revisions` access or repeated direct helper call could therefore refetch the same revision list even though the helpers already behaved as cache-aware at entry.

This change stores each successfully fetched revision collection in `post._revisions`. The single-post helper caches after response validation and parsing succeed. The batch helper caches newly fetched target posts only after list parsing and optional `with_html` processing complete, so the stored collection includes any HTML content successfully loaded by that call. Existing cached-post fast paths, cached duplicate reuse, duplicate revision HTML grouping, failed list acquisitions, and request payloads remain unchanged.

## Related Issue

Builds on [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), which made forum post revision-list reads retry-aware, [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), which deduplicated duplicate post IDs in revision-list batches, [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md) and [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), which deduplicated revision HTML fetches, [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), and [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), which established this surface as cache-aware. It also follows the direct helper cache consistency pattern from [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md) and [228-pr-cache-direct-thread-post-acquisition.md](228-pr-cache-direct-thread-post-acquisition.md).

No upstream issue was filed from this local workspace.

## Changes

- Populate `post._revisions` when `ForumPostRevisionCollection.acquire_all(post)` completes successfully.
- Populate `post._revisions` for each newly fetched target post when `ForumPostRevisionCollection.acquire_all_for_posts(...)` completes successfully.
- Preserve existing cached-post fast paths and later cached duplicate reuse.
- Preserve optional `with_html=True` behavior while caching the same collection that receives any successfully loaded revision HTML.
- Delay cache writes until after response-body validation, parsing, and optional HTML processing complete so failed list acquisitions do not seed `post._revisions`.
- Add focused regressions proving direct single-post and batched acquisition populate the post cache and a later `post.revisions` access does not refetch.

## Type Of Change

- Performance improvement
- Cache consistency hardening
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Successful direct single-post revision acquisition must populate `post._revisions` with the returned collection. | `TestForumPostRevisionCollectionAcquireAll.test_acquire_all_populates_post_revisions_cache` asserts `mock_forum_post_no_http._revisions is collection` immediately after direct acquisition. | The RED test failed before the fix because `_revisions` stayed `None` after the helper returned. |
| Successful batched revision acquisition must populate `post._revisions` for newly fetched target posts. | `TestForumPostRevisionCollectionAcquireAllForPosts.test_acquire_all_for_posts_populates_post_revisions_cache` asserts the returned collection is stored in the post cache. | A returned collection that is not stored on the same post rejects this local completion claim. |
| A later `post.revisions` access after direct acquisition must reuse the same collection without another AMC request. | Both focused tests assert `mock_forum_post_no_http.revisions is collection` and `amc_request_with_retry.assert_called_once()`. | A second fetch, a distinct collection object, or a property cache miss rejects this local completion claim. |
| Existing cached-post fast-path behavior remains unchanged. | `test_acquire_all_skips_cached_post_revisions`, `test_acquire_all_for_posts_skips_cached_post_revisions`, `test_acquire_all_for_posts_all_cached_skips_fetch`, and `test_acquire_all_for_posts_with_html_reuses_cached_revision_list` still pass. | Fetching when `_revisions` is already set, losing cached HTML, or returning a different collection for a cached first-seen post rejects this local completion claim. |
| Cached duplicate reuse remains unchanged. | `test_acquire_all_for_posts_reuses_later_cached_duplicate_post_revisions`, duplicate post-ID dedupe, and duplicate revision HTML dedupe tests still pass. | Returning the later duplicate's collection directly for an uncached first-seen post, losing cached HTML, or making an avoidable AMC request rejects this local completion claim. |
| Failed revision-list acquisitions must not seed the cache. | Existing exhausted retry and missing response-body tests still pass; the new cache writes are reached only after successful response validation and parsing. | Caching after a `None` response, missing JSON `body`, or parser failure rejects this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `cb778c3 perf(forum_post_revision): cache direct revision acquisition`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_populates_post_revisions_cache -q` failed before the single-helper fix because `_revisions` remained `None` after a successful direct fetch.
- GREEN: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_populates_post_revisions_cache -q`.
- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_populates_post_revisions_cache -q` failed before the batch-helper fix because `_revisions` remained `None` after a successful batch fetch.
- GREEN: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_populates_post_revisions_cache tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_populates_post_revisions_cache -q`.
- `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts -q` passed 17 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 165 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run pytest tests/unit -q` passed 774 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `ForumPostRevisionCollection.acquire_all(post)` returns the same collection it stores in `post._revisions` after a successful direct read.
- `ForumPostRevisionCollection.acquire_all_for_posts([post])` stores the successful result for each newly fetched first-seen post.
- A following `post.revisions` access returns that stored collection without another AMC request.
- Existing `post._revisions` values still satisfy direct and batched acquisition without fetching.
- Later cached duplicate post revision lists can still satisfy an uncached first-seen duplicate without fetching and without sharing owner-bound revision objects.
- Successful `with_html=True` batch acquisition stores the same collection after any successfully loaded revision HTML is attached.
- Failed list response, missing response body, and malformed parser input do not seed `post._revisions`.
- Revision-list parsing, response-body validation, retry behavior, duplicate post ordering, cached HTML preservation, duplicate revision HTML grouping, lazy `ForumPostRevision.html`, and request payloads remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, non-goals, verification, and false-positive rejection checks.
- `Issues/README.md` records the local draft and implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Callers can naturally use `ForumPostRevisionCollection.acquire_all(post)` or `acquire_all_for_posts([...])` directly while collecting forum edit history, composing retry queues, or choosing whether to request revision HTML eagerly. Because these helpers already check `post._revisions`, a successful direct read should become the cache source for the same post object. Populating the cache after complete acquisition avoids redundant AMC work while preserving explicit refresh through cache clearing or replacement.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed forum drafts repeatedly identified forum post revision acquisition as a practical read-heavy surface, including retry hardening, duplicate post-ID batching, duplicate revision HTML batching, cached first-seen skips, cached duplicate reuse, parser scoping, response-body validation, lazy HTML failure visibility, and site/post/revision diagnostics.
- Prior cache-aware local drafts established that collection helpers should avoid repeat reads when the target object already carries the requested data, and Issues 227/228 applied the same direct-helper cache consistency rule to category thread lists and thread post lists.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved forum contents out of upstream discussion.

## Additional Notes

This slice does not add a public refresh method, change `ForumPost.revisions`, alter revision parser output, change optional HTML retry semantics, or change the result dictionary shape. It only stores complete successful direct revision-list acquisitions in the cache that the helpers already respect.
