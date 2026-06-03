# PR Draft: Retry Forum Post Edit Form Fetch

## Summary

`ForumPost.edit(...)` must fetch `forum/sub/ForumEditPostFormModule` before saving so it can read `currentRevisionId`. That pre-save form lookup is a read-only AMC request, but it still used plain `site.amc_request(...)`. A transient AMC failure could therefore be parsed as a response and fail with an attribute/parsing error before the library's retry behavior ran, even though no edit save had happened yet.

The fix routes only the edit-form lookup through `site.amc_request_with_retry(...)`. If the form fetch succeeds after retry, the existing save action proceeds unchanged. If retries are exhausted, `ForumPost.edit(...)` raises `UnexpectedException("Cannot retrieve forum post edit form: <post_id>")` and does not send the save action.

## Related Issue

Complements [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), which made the same `ForumEditPostFormModule` source-read path retry-aware for `ForumPostCollection.get_post_sources()` and lazy `ForumPost.source`. It also follows the read-path retry pattern from [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md) and [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md). No upstream issue filed yet.

## Changes

- Use `self.thread.site.amc_request_with_retry(...)` for `ForumPost.edit(...)`'s pre-save edit-form fetch.
- Raise `UnexpectedException("Cannot retrieve forum post edit form: <post_id>")` when the edit-form retry result is `None`.
- Preserve existing parsing of `input[name='currentRevisionId']`.
- Preserve title/source local-state updates after a successful save.
- Keep the `saveEditPost` mutation request on plain `site.amc_request(...)` so this slice does not retry a potentially non-idempotent save action.
- Keep `ForumThread.reply(...)`, `ForumCategory.create_thread(...)`, and other forum mutation paths unchanged.

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
| R1: Edit-form lookup is retry-aware | `ForumPost.edit(...)` retries transient failures while fetching `forum/sub/ForumEditPostFormModule` | `test_edit_retries_transient_form_fetch_failures` | The test failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` |
| R2: Save action is not sent when form retry is exhausted | A `None` retry result raises `UnexpectedException` with the post ID and does not call plain `amc_request(...)` for `saveEditPost` | `test_edit_raises_when_form_fetch_retry_is_exhausted` | Exhausted form fetch does not update local source/title or attempt a save |
| R3: Successful edit behavior is preserved | Existing edit and edit-with-title flows still save once, update local source, and update title when requested | `test_edit_success`, `test_edit_with_new_title` | Plain save AMC is still called once after a successful form fetch |
| R4: Existing forum post behavior is preserved | Source fetches, cached source behavior, post-list reads, and revision reads remain green | `tests/unit/test_forum_post.py`; `tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py` | Adjacent forum tests still pass |

## Testing

Local implementation commit: `c61fa13 fix(forum_post): retry edit form fetch`

- [x] `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_retries_transient_form_fetch_failures -q` failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostEdit -q` passed with 5 tests.
- [x] `uv run --extra test pytest tests/unit/test_forum_post.py -q` passed with 30 tests.
- [x] `uv run --extra test pytest tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed with 86 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 595 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`

## Acceptance Criteria

- `ForumPost.edit(...)` uses retry-aware AMC for the read-only edit-form fetch.
- A transient edit-form fetch failure is retried before parsing `currentRevisionId`.
- An exhausted edit-form fetch retry raises an explicit post-ID-specific `UnexpectedException` and does not send the `saveEditPost` request.
- A successful edit still sends one plain save request, updates `_source`, and updates `title` only when a title argument is supplied.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Editing a forum post requires a fresh `currentRevisionId`, so the form fetch is an unavoidable read before the mutation. Making that read retry-aware prevents transient AMC errors from surfacing as parser/attribute errors, while keeping the actual save action on the existing non-retried path to avoid changing mutation idempotency semantics.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence repeatedly used `wikidot.py` for source collection, publish verification, page/revision evidence, and forum inspection/edit-adjacent workflows where read-heavy AMC paths needed retry-aware behavior.
- Existing local issue [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md) established that `ForumEditPostFormModule` reads should use retry-aware AMC for source access.
- Existing local issues [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md) and [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md) established the surrounding retry-sensitive forum read surface.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice deliberately does not retry `saveEditPost`, `ForumThread.reply(...)`, or `ForumCategory.create_thread(...)`. Those mutation paths have different idempotency and duplicate-action risks. The change is limited to the read-only edit-form fetch needed before `ForumPost.edit(...)` can build the existing save request.
