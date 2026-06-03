# PR Draft: Retry Forum Post Revision Fetches

## Summary

`ForumPostRevisionCollection.acquire_all(...)`, `acquire_all_for_posts(...)`, and `get_htmls()` are public read helpers for forum post edit history. They still used the plain `site.amc_request(...)` path, unlike the already-hardened forum category, thread, and post-list read paths. A transient AMC failure could therefore be parsed as a response and fail with an attribute/parsing error before the library's retry behavior ran.

The fix routes forum post revision-list and revision-HTML reads through `site.amc_request_with_retry(...)`. Exhausted revision-list retries now raise `UnexpectedException` with the affected post ID, while exhausted revision-HTML retries leave only the failed revision's HTML cache unset so successful revision HTML responses from the same batch are preserved.

## Related Issue

Complements [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), which made forum thread post-list fetches retry-aware, and [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), which applied the same retry and partial-success behavior to page revision source/HTML fetches. No upstream issue filed yet.

Follow-up performance drafts: [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md) removes duplicate revision-list requests, [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md) removes collection-level duplicate revision HTML requests, and [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md) removes optional `with_html=True` duplicate revision HTML requests while preserving this retry-aware read path and post-ID keyed result shape.

## Changes

- Use `post.thread.site.amc_request_with_retry(...)` in `ForumPostRevisionCollection.acquire_all(post)`.
- Use `site.amc_request_with_retry(...)` in `ForumPostRevisionCollection.acquire_all_for_posts(posts, ...)`.
- Raise `UnexpectedException("Cannot retrieve forum post revisions for post: <id>")` when a revision-list retry is exhausted.
- Use retry-aware AMC for `with_html=True` revision HTML acquisition.
- Use retry-aware AMC in `ForumPostRevisionCollection.get_htmls()`.
- Leave only permanently failed revision HTML items unacquired when retry returns `None`, preserving successful HTML results from the same batch.
- Keep revision parsing, revision ordering, `rev_no` assignment, lazy `ForumPostRevision.html`, cached-HTML skipping, and post action paths unchanged.

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
| R1: Single-post forum revision-list acquisition uses retry-aware AMC | `ForumPostRevisionCollection.acquire_all(post)` calls `site.amc_request_with_retry(...)` and does not call plain `amc_request(...)` | `test_acquire_all_retries_transient_fetch_failures` | The test failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` |
| R2: Exhausted single-post revision-list retry fails explicitly | `ForumPostRevisionCollection.acquire_all(post)` raises `UnexpectedException` with the post ID when retry returns `None` | `test_acquire_all_raises_when_retry_is_exhausted` | The test failed before the fix with `AttributeError: 'NoneType' object has no attribute 'json'` |
| R3: Multi-post forum revision-list acquisition uses retry-aware AMC | `acquire_all_for_posts(...)` retries transient per-post revision-list failures and returns successful collections for all requested posts | `test_acquire_all_for_posts_retries_transient_fetch_failures` | The test failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` |
| R4: Exhausted multi-post revision-list retry fails explicitly | `acquire_all_for_posts(...)` raises `UnexpectedException` with the affected post ID when retry returns `None` | `test_acquire_all_for_posts_raises_when_retry_is_exhausted` | A missing response is not parsed and the post is not silently omitted |
| R5: Forum revision HTML acquisition is retry-aware and partial-success tolerant | `with_html=True` and `get_htmls()` use retry-aware AMC; successful HTML responses are cached while `None` retry results stay unacquired | `test_acquire_all_for_posts_with_html_retries_transient_html_failures`, `test_get_htmls_retries_transient_fetch_failures`, `test_get_htmls_skips_failed_retry_response` | Transient HTML fetch failure failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` |
| R6: Existing parsing behavior is preserved | Successful revision-list and revision-HTML responses still parse as before | `tests/unit/test_forum_post_revision.py` full module | Existing parse, find, property, cache, and HTML setter tests remain green |

## Testing

Local implementation commit: `15f7b29 fix(forum_post_revision): retry revision fetches`

- [x] `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_retries_transient_fetch_failures -q` failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_raises_when_retry_is_exhausted -q` failed before the fix with `AttributeError: 'NoneType' object has no attribute 'json'` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_retries_transient_fetch_failures -q` failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_raises_when_retry_is_exhausted -q`
- [x] `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_with_html_retries_transient_html_failures -q` failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_retries_transient_fetch_failures -q` failed before the fix with `AttributeError: 'RuntimeError' object has no attribute 'json'` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_skips_failed_retry_response -q`
- [x] `uv run --extra test pytest tests/unit/test_forum_post_revision.py -q` passed with 28 tests.
- [x] `uv run --extra test pytest tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed with 53 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 590 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed the current complexity leads.

## Acceptance Criteria

- Forum post revision-list reads use `amc_request_with_retry(...)`, not plain `amc_request(...)`.
- Exhausted forum post revision-list retry raises an explicit `UnexpectedException` with the affected post ID.
- Forum post revision HTML reads use retry-aware AMC in both `with_html=True` and `get_htmls()` paths.
- A failed revision HTML retry leaves only that revision unacquired and does not discard successful revision HTML responses in the same batch.
- Successful revision parsing, newest-to-oldest reversal, `rev_no` assignment, lazy HTML acquisition, and cached HTML behavior remain unchanged.
- Forum post source/edit action paths remain unchanged.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Forum post revision reads are the forum equivalent of page revision source/HTML reads: they inspect historical content and should tolerate transient AMC failures without losing successful results from the same batch. This keeps forum read APIs consistent with the already retry-aware forum category, thread, post-list, private-message, recent-changes, member-list, application-list, page detail, and page revision read paths.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence repeatedly used `wikidot.py` for source collection, publishing verification, page/revision evidence, and forum inspection workflows where read-heavy AMC paths needed retry-aware behavior.
- Existing local issues [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), and [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md) established the same retry-sensitive forum read surface.
- Existing local issue [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md) established partial-success semantics for revision HTML/source reads; this draft applies the same model to forum post revisions.
- The refreshed complexity scan still flags `src/wikidot/module/forum_post_revision.py` as a batch/revision acquisition hotspot, supporting this narrow reliability fix.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice does not change `ForumPost.edit(...)`, `ForumThread.posts`, forum post parsing, revision ordering, user/date parsing, or the `ForumPostRevision.html` public return type. It only moves forum post revision-list and revision-HTML read requests to the same retry-aware AMC model used by the surrounding read APIs.
