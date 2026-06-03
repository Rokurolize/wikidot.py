# PR Draft: Reuse Cached Duplicate Forum Post Sources

## Summary

`ForumPostCollection.get_post_sources()` already skips posts whose `_source` is cached, and it already deduplicates uncached duplicate post IDs before fetching `forum/sub/ForumEditPostFormModule`. Before this fix, a collection containing both a cached post and an uncached duplicate with the same post ID still fetched the edit form for the uncached duplicate instead of reusing the cached source already present in the same collection.

This fix first indexes cached source text by post ID, copies that source to uncached duplicates in the same collection, and only fetches edit forms for post IDs that remain unresolved. Public collection membership and ordering remain unchanged.

## Related Issue

Builds directly on [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), which established that duplicate forum post IDs should not trigger duplicate source-read requests. It also depends on the retry-aware source-read behavior from [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md) and the edit-form control scoping from [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md).

No upstream issue was filed from this local workspace.

## Changes

- Build a `post.id -> source` map from already cached posts in the collection.
- Populate uncached duplicate posts from that map before constructing source-fetch requests.
- Keep first-seen request order and existing uncached duplicate grouping for the remaining unresolved post IDs.
- Add a focused regression where one duplicate post is cached and another duplicate with the same ID is uncached.
- Preserve retry-aware source fetches, failed retry handling, source textarea parsing, lazy `ForumPost.source`, edit behavior, reply behavior, post parsing, and adjacent forum workflows.

## Type Of Change

- Performance/reliability improvement
- Cache behavior improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Cached source from a duplicate post ID must be reused within the same collection. | `TestForumPostCollectionGetSources.test_get_post_sources_reuses_cached_duplicate_post_source` asserts the uncached duplicate receives `cached source`. | The RED test failed before the fix because the duplicate source came from a new edit-form fetch instead. |
| Reusing cached duplicate source must avoid unnecessary network work. | The same focused test asserts neither plain `amc_request(...)` nor retry-aware `amc_request_with_retry(...)` is called. | A regression that fetches the edit form for the duplicate fails the not-called assertions. |
| Existing source collection behavior remains intact. | `TestForumPostCollectionGetSources`, `TestForumPostSource`, and `TestForumPostEdit` passed 18 tests. | Regressions in retry, exhausted retry, cached-source skipping, duplicate uncached source propagation, source scoping, or edit behavior reject this local completion claim. |
| Forum post and adjacent forum workflows stay green. | `uv run pytest tests/unit/test_forum_post.py -q` passed 43 tests, and `uv run pytest tests/unit/test_forum*.py -q` passed 131 tests. | Regressions in post parsing, source fetching, edit behavior, revision parsing, thread parsing, or category parsing reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `2ec41e9 perf(forum_post): reuse cached duplicate sources`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_reuses_cached_duplicate_post_source -q` failed before the fix because the uncached duplicate was filled from a new edit-form fetch instead of the already cached source.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_reuses_cached_duplicate_post_source -q`
- `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources tests/unit/test_forum_post.py::TestForumPostSource tests/unit/test_forum_post.py::TestForumPostEdit -q` passed 18 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 43 tests.
- `uv run pytest tests/unit/test_forum*.py -q` passed 131 tests.
- `uv run pytest tests/unit -q` passed 679 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- A cached source on one post object is reused for uncached collection entries with the same post ID.
- No AMC source-fetch request is sent when every uncached post can be satisfied from cached duplicates in the same collection.
- Uncached duplicate post IDs with no cached source still use the existing one-request-per-ID source fetch path.
- Exhausted retry results still leave only unresolved post IDs unacquired.
- Existing source textarea scoping, cached-source skipping, empty collection behavior, lazy `ForumPost.source`, `ForumPost.edit(...)`, `ForumThread.reply(...)`, and forum parser behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post source collection is a read-heavy inspection workflow. If a caller holds multiple objects for the same post ID and one already has source text, fetching the same edit form again adds avoidable AMC work and another failure point. Reusing the cached source keeps source acquisition consistent with the existing duplicate-ID dedupe rule while preserving the public collection shape.

## Local Evidence, Not For Upstream Paste

- Existing local drafts established forum post source reads as a practical rollout-backed surface for inspection, archiving, and audit workflows.
- Issue 055 already established duplicate forum post IDs as a realistic performance lead for source fetching.
- The refreshed complexity scan continues to flag `src/wikidot/module/forum_post.py` around source acquisition as a worthwhile audit area.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page/forum contents out of upstream discussion.

## Additional Notes

This slice does not change edit-form request construction, source textarea parsing, retry policy, duplicate uncached source grouping, mutation paths, or result object shape. It only lets already cached source text satisfy duplicate uncached entries in the same collection before any source-fetch request is built.
