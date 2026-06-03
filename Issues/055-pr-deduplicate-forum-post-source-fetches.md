# PR Draft: Deduplicate Forum Post Source Fetch IDs

## Summary

`ForumPostCollection.get_post_sources()` fetches source text for each uncached post in a collection with `forum/sub/ForumEditPostFormModule`. If the collection contains the same forum post ID more than once, the current output should still contain both collection entries, but the source-read path does not need to request the same edit form twice.

The fix keeps collection membership, ordering, retry handling, failed-response handling, and source parsing stable while deduplicating source fetch requests by post ID. The first uncached occurrence of each post ID drives the AMC request, and the parsed source is copied to every uncached entry with that ID.

## Related Issue

Builds on the retry-aware forum post source work in [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md). Also follows the ordered deduplication pattern from [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md). No upstream issue filed yet.

## Changes

- Group uncached forum posts by `post.id` before constructing source-fetch AMC requests.
- Preserve first-seen post ID order for the request batch.
- Apply one parsed source response to every uncached collection entry sharing that post ID.
- Preserve cached-source skipping, `None` retry-result behavior, source textarea parsing, lazy `ForumPost.source`, and mutation paths.
- Add a focused regression test covering duplicate post IDs in a source-fetch collection.

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
| R1: Duplicate forum post IDs do not trigger duplicate source fetches | `get_post_sources()` calls `amc_request_with_retry(...)` with one request per uncached post ID | `test_get_post_sources_deduplicates_duplicate_post_ids` | Reverting the grouping makes the focused test fail with `zip(strict=True)` length mismatch or duplicate request payloads |
| R2: Duplicate collection entries still receive source text | Every uncached entry with the fetched post ID has `_source` populated from the single response | Same focused test | A fix that only updates the first entry leaves the duplicate entry unacquired |
| R3: Existing forum source behavior is preserved | Successful source parsing, cached-source skipping, exhausted retry behavior, and broader unit tests remain green | Commands listed below | Existing source tests fail if retry or cached-source semantics change |

## Testing

Local implementation commit: `206cc41 perf(forum_post): deduplicate source fetch ids`

- [x] `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_deduplicates_duplicate_post_ids -q` failed before the fix with `ValueError: zip() argument 2 is shorter than argument 1`, then passed after the fix with one source-fetch request.
- [x] `uv run --extra test pytest tests/unit/test_forum_post.py -q` passed with 31 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 609 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`

## Acceptance Criteria

- Duplicate uncached forum post IDs in a `ForumPostCollection` are fetched once.
- First-seen request order is preserved.
- All uncached collection entries with the duplicated post ID receive the fetched source text.
- Existing `None` retry results still leave the affected post ID's source unset and do not fabricate empty source text.
- Cached-source skipping, empty collection behavior, successful source textarea parsing, lazy `ForumPost.source`, `ForumPost.edit(...)`, and `ForumThread.reply(...)` remain unchanged.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Forum post source inspection is a read-heavy workflow for moderation, archiving, diffing, and local audit tooling. Deduplicating identical source-read IDs avoids redundant AMC work while preserving the public collection shape and retry-aware behavior.

## Local Evidence, Not For Upstream Paste

- Local forum read hardening in [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), and [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md) established forum source/post inspection as an active read-heavy surface.
- The refreshed complexity scan flags `src/wikidot/module/forum_post.py` as a module worth auditing for repeated request construction and nested list handling.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice does not change forum post parsing, pagination, post revision reads, edit/reply mutation methods, request retry policy, or source textarea extraction. It only removes duplicate source-fetch requests for repeated uncached post IDs in the existing source-read path.
