# PR Draft: Retry Forum Post Source Fetches

## Summary

`ForumPostCollection.get_post_sources()` and the lazy `ForumPost.source` property fetch forum post source text with `forum/sub/ForumEditPostFormModule`. That read path still used plain `site.amc_request(...)`, while the surrounding forum category, thread, post-list, and post-revision reads now use retry-aware AMC. A transient AMC failure could therefore be parsed as a response and fail with an attribute/parsing error before the library's retry behavior ran.

The fix routes forum post source fetches through `site.amc_request_with_retry(...)`. Successful responses still populate each post's cached source exactly as before. If retry is exhausted for one response, that post remains unacquired while successful responses in the same batch are preserved; the existing `ForumPost.source` property then raises its current `NoElementException` when a single lazy source fetch still has no source.

## Related Issue

Complements [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), which made forum post-list fetches retry-aware, and [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), which applied retry-aware handling to forum post revision reads. It also mirrors the partial-success source/HTML behavior from [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md). No upstream issue filed yet.

## Changes

- Use `thread.site.amc_request_with_retry(...)` in `ForumPostCollection._acquire_post_sources(...)`.
- Skip `None` retry results so exhausted retries leave only the affected post source unacquired.
- Preserve successful source parsing from `textarea[name='source']`.
- Keep cached-source skipping unchanged.
- Keep `ForumPost.source` lazy acquisition and existing `NoElementException` behavior unchanged.
- Keep `ForumPost.edit(...)`, thread replies, post-list retrieval, and action/mutation paths unchanged.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [ ] Security/privacy hardening
- [x] Reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Requirements Traceability

| Requirement | Acceptance | Verification | Negative Control |
| --- | --- | --- | --- |
| R1: Forum post source collection uses retry-aware AMC | `ForumPostCollection.get_post_sources()` fetches source with `site.amc_request_with_retry(...)` and does not call plain `amc_request(...)` | `test_get_post_sources_success`, `test_get_post_sources_multiple_posts` | Plain AMC assertions fail if the source path is reverted |
| R2: Transient source-fetch failures are retried | A transient `RuntimeError` response from AMC is retried and the source is cached after the successful retry | `test_get_post_sources_retries_transient_fetch_failures` | The test failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` |
| R3: Exhausted source-fetch retries preserve partial success semantics | A `None` retry result leaves the affected post's source unset instead of parsing a missing response | `test_get_post_sources_skips_failed_retry_response` | A missing response is not parsed and successful source responses from the same batch remain usable |
| R4: Lazy `ForumPost.source` keeps its public failure surface | When a lazy single-post source fetch is exhausted, `ForumPost.source` raises the existing `NoElementException` rather than returning a fabricated empty source | `test_source_property_raises_when_retry_is_exhausted` | The property does not silently cache `None` or an empty string |
| R5: Existing source parsing and caching are preserved | Successful edit-form responses still parse `textarea[name='source']`, cached sources skip network work, and empty collections remain no-ops | `tests/unit/test_forum_post.py` full module | Existing source, cache, parse, edit, reply-adjacent, and collection tests remain green |

## Testing

Local implementation commit: `9dbaecb fix(forum_post): retry source fetches`

- [x] `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_retries_transient_fetch_failures -q` failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources tests/unit/test_forum_post.py::TestForumPostSource -q` passed with 9 tests.
- [x] `uv run --extra test pytest tests/unit/test_forum_post.py -q` passed with 28 tests.
- [x] `uv run --extra test pytest tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed with 56 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 593 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`

## Acceptance Criteria

- Forum post source reads use `amc_request_with_retry(...)`, not plain `amc_request(...)`.
- A transient source-fetch AMC failure is retried and then caches the returned post source.
- A permanently failed retry result leaves only that post source unacquired and does not discard successful source responses in the same batch.
- Lazy `ForumPost.source` preserves the existing explicit failure behavior when source remains unavailable.
- Cached-source skipping, empty collection behavior, source textarea parsing, forum post parsing, edit action paths, and thread reply action paths remain unchanged.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Forum post source reads are read-only inspection calls, just like page revision source/HTML reads and forum post revision reads. They should tolerate transient AMC failures consistently with the surrounding read-heavy APIs, especially because source inspection is a natural dependency for moderation, archiving, diffing, and local audit tooling.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence repeatedly used `wikidot.py` for source collection, publish verification, page/revision evidence, and forum inspection workflows where read-heavy AMC paths needed retry-aware behavior.
- Existing local issues [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), and [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md) established the same retry-sensitive forum read surface.
- Existing local issue [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md) established the partial-success model for batched source/HTML reads; this draft applies that model to forum post source forms.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice deliberately does not retry `ForumPost.edit(...)`'s save action or `ForumThread.reply(...)`. Those mutation paths have different idempotency and lock semantics. The change is limited to the read-only edit-form source acquisition path used by `ForumPostCollection.get_post_sources()` and lazy `ForumPost.source`.
