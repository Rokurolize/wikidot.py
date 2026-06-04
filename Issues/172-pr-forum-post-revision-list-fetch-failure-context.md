# PR Draft: Include Site Context In Forum Post Revision List Fetch Failures

## Summary

`ForumPostRevisionCollection.acquire_all(...)` and `ForumPostRevisionCollection.acquire_all_for_posts(...)` retrieve forum post edit-history lists through retry-aware AMC requests. When a revision-list response still resolved to `None` after retries, the method raised `UnexpectedException("Cannot retrieve forum post revisions for post: ...")`, which identified the failed post but not the Wikidot site.

This follow-up preserves retry-aware direct and batched forum post revision-list fetching, cached revision-list reuse, duplicate post-ID handling, optional `with_html=True` revision HTML fetching, lazy `ForumPost.revisions`, and partial-success HTML semantics, but includes site unix name in exhausted revision-list fetch failures.

## Related Issue

Builds on [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), which introduced retry-aware forum post revision-list fetching and explicit exhausted-retry failures. It also follows [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), and [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), because those drafts established revision-list retry behavior, duplicate/cached behavior, direct property paths, and adjacent forum post-list context.

No upstream issue was filed from this local workspace.

## Changes

- Include site unix name and post ID when direct post revision-list fetching exhausts retries.
- Include the same site/post context when batched post revision-list fetching exhausts retries for one post in the batch.
- Strengthen the direct and batched exhausted-retry tests to assert the contextual messages.
- Preserve non-retry `amc_request(...)` avoidance, cached revision-list reuse, duplicate post-ID handling, optional revision HTML fetching, lazy `ForumPost.revisions`, and partial-success HTML behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post revision-list fetch failure context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Direct exhausted retry revision-list fetches still fail. | `TestForumPostRevisionCollectionAcquireAll.test_acquire_all_raises_when_retry_is_exhausted` raises `UnexpectedException` when the retry helper returns `None`. | A change that returns an empty revision collection for a failed direct fetch rejects this local completion claim. |
| Batched exhausted retry revision-list fetches still fail for the failed post. | `TestForumPostRevisionCollectionAcquireAllForPosts.test_acquire_all_for_posts_raises_when_retry_is_exhausted` raises `UnexpectedException` when the second batched response returns `None`. | A change that silently drops the failed post from the result rejects this local completion claim. |
| Exhausted-retry failures identify the failed site and post. | Focused tests assert `Cannot retrieve forum post revisions for site: test-site, post: ...`. | The RED tests failed before the fix because messages only named the post ID. |
| Forum post revision behavior remains green. | `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 39 tests. | Regressions in revision parsing, caching, duplicate post handling, optional HTML acquisition, or lazy HTML behavior reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 148 tests. | Regressions in category/thread/post/revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `7bdc590 fix(forum_post_revision): include site in revision list failures`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_raises_when_retry_is_exhausted tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_raises_when_retry_is_exhausted -q` failed before the fix because exhausted-retry messages lacked site context.
- GREEN: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_raises_when_retry_is_exhausted tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_raises_when_retry_is_exhausted -q`
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 39 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 148 tests.
- `uv run pytest tests/unit -q` passed 722 tests.
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Direct and batched exhausted retry-aware forum post revision-list fetches still raise `UnexpectedException`.
- Those exceptions include the site unix name and post ID.
- Successful revision-list parsing, cached revision-list reuse, duplicate post-ID handling, optional revision HTML fetching, lazy `ForumPost.revisions`, and partial-success HTML behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post revision-list acquisition can run across many sites and posts. The exhausted-retry failure should identify both the site and the post so logs can route failures without storing raw AMC responses, revision HTML, post text, or local rollout context.

## Local Evidence, Not For Upstream Paste

- Earlier rollout-backed forum revision drafts established retry-aware revision-list acquisition, duplicate/cached behavior, with-html batching, and lazy property behavior as practical local Codex surfaces.
- Recent context slices showed that site-specific exhausted-retry messages improve multi-site ledgers without changing successful behavior.
- The refreshed complexity memo continues to keep action/read boundaries and remaining direct property/parser failure messages as follow-up leads, but this slice only claims forum post revision-list exhausted-retry diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw AMC responses, raw post text, revision HTML, and raw response bodies out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, retry counts, cached revision-list reuse, duplicate post-ID handling, revision parsing, optional revision HTML fetching, lazy `ForumPost.revisions`, partial-success HTML behavior, or live Wikidot behavior. It only adds site context to existing exhausted retry-aware forum post revision-list failures.
