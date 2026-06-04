# PR Draft: Include Context In Forum Post ID Parse Errors

## Summary

`ForumPostCollection.acquire_all_in_thread(...)`, used by `thread.posts`, parses generated forum post-list markup from `forum/ForumViewThreadPostsModule`. The post-list parser already includes site, thread, page, structural post position, and parsed post ID context for many malformed row errors, but malformed structural `post-*` IDs still reached raw `int(...)` conversions and raised bare `ValueError`.

This follow-up keeps successful post parsing and existing `NoElementException` behavior for malformed Wikidot-generated post-list markup, but routes malformed top-level post IDs and parent post IDs through a contextual parser-error helper. The raised message now identifies the site, thread, page, structural post position, affected field, raw value, and parsed child post ID when available, so plain-text logs can explain which post-list item failed without preserving raw HTML or post bodies.

## Related Issue

Builds on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [228-pr-cache-direct-thread-post-acquisition.md](228-pr-cache-direct-thread-post-acquisition.md), and [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md). Those drafts established retry-aware thread post-list acquisition, structural parser boundaries, post-list parse context, response-body validation, successful direct cache population, and the adjacent parser-value diagnostic pattern.

No upstream issue was filed from this local workspace.

## Changes

- Add a small post-list ID parser for generated `post-*` values.
- Convert malformed top-level post IDs into `NoElementException` with site, thread, page, structural post position, field, and raw value.
- Convert malformed parent post IDs into `NoElementException` with site, thread, page, structural child post position, child post ID, field, and raw value.
- Extend post-list acquisition tests to cover malformed top-level and parent post ID values.
- Preserve request construction, retry handling, pagination, cached thread post reuse, cached duplicate thread post reuse, pseudo-post filtering, nested post-container filtering, title/body extraction, metadata scoping, source fetching, edit behavior, reply behavior, and successful parent ID parsing.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post-list parser error-context ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed top-level forum post IDs fail with wikidot.py's contextual parser exception rather than a raw integer conversion exception. | `TestForumPostCollectionAcquireAll.test_acquire_all_malformed_post_id_includes_thread_page_and_value_context` asserts `NoElementException` for `id="post-not-a-number"`. | A raw `ValueError`, silent coercion, fabricated ID, skipped post, or malformed `ForumPost` rejects this local completion claim. |
| The malformed top-level post ID error identifies the affected site, thread, page, structural post position, field, and raw value. | The focused test asserts `Post ID is malformed for site: test-site (thread=3001, page=1, post=1, field=post_id, value=post-not-a-number)`. | Omitting site, thread, page, position, field, or value makes the failure ambiguous and rejects this local completion claim. |
| Malformed parent post IDs fail with contextual parser errors after the child post ID is parsed. | `TestForumPostCollectionAcquireAll.test_acquire_all_malformed_parent_post_id_includes_child_post_context` asserts `NoElementException` for a malformed parent `id="bad-parent"` around child post `5002`. | A raw `ValueError`, dropped parent relation without failure, fabricated parent ID, or missing child post context rejects this local completion claim. |
| Successful post-list parsing remains unchanged. | `uv run pytest tests/unit/test_forum_post.py` passed 58 tests. | Changing post order, post IDs, parent IDs, title/body text, metadata parsing, pagination, cache behavior, source fetching, edit behavior, or replies rejects this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 170 tests. | Regressions in category, thread, post, or post-revision parsing and acquisition reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `538cb8a fix(forum_post): report malformed post id context`.

- RED: `uv run pytest tests/unit/test_forum_post.py -k malformed_post_id_includes_thread_page_and_value_context` failed before the fix with raw `ValueError` from `post_id = int(str(post_id_attr).removeprefix("post-"))`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py -k malformed_post_id_includes_thread_page_and_value_context` passed 1 test after top-level post IDs used the contextual parser helper.
- RED: `uv run pytest tests/unit/test_forum_post.py -k malformed_parent_post_id_includes_child_post_context` failed before the parent-ID fix with raw `ValueError` from `parent_id = int(str(parent_id_attr).removeprefix("post-"))`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py -k 'malformed_post_id_includes_thread_page_and_value_context or malformed_parent_post_id_includes_child_post_context'` passed 2 tests.
- `uv run pytest tests/unit/test_forum_post.py` passed 58 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 170 tests.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left 2 files unchanged.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run pytest tests/unit -q` passed 780 tests.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A thread post-list response whose structural post element has a malformed `post-*` ID raises `NoElementException`.
- A nested reply whose structural parent post has a malformed ID raises `NoElementException` after identifying the parsed child post ID.
- The malformed ID messages include the site `unix_name`, thread ID, page number, structural post index, affected field, raw malformed value, and child post ID when the child was already parsed.
- Successful thread post-list parsing, retry behavior, pagination, cached thread post reuse, cached duplicate thread post reuse, pseudo-post filtering, nested post-container filtering, title/body text spacing, metadata scoping, source fetching, edit behavior, reply behavior, and successful parent ID parsing remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post-list inspection is a read-heavy prerequisite for source, revision, edit, and reply workflows. When Wikidot returns malformed generated post-list markup, wikidot.py should still fail rather than inventing IDs or silently dropping structural relationships, but the failure should identify the affected thread, page, post position, field, and raw value so maintainers can triage from logs without storing raw generated HTML, post content, or credentials.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum post-list acquisition as a practical read-heavy workflow, including retry-aware fetching, response-body validation, parser scoping, pseudo-post filtering, nested content filtering, title text spacing, source fetching, edit-form safety, and cache-aware direct acquisition.
- The refreshed complexity scanner continued to flag `src/wikidot/module/forum_post.py` as a parser/acquisition hotspot after Issue 234 closed the adjacent forum thread-list count parser gap.
- The immediate RED failures showed the same raw `ValueError` class in both top-level post IDs and parent post IDs, while the GREEN path preserved the existing post-list behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw post-list HTML, and post contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `ForumPostCollection.acquire_all_in_thread(...)` or `acquire_all_in_threads(...)` request construction, retry handling, pagination, cache assignment, successful parser output, pseudo-post filtering, nested post-container filtering, title/body extraction, metadata scoping, `ForumPost.source`, `ForumPost.edit(...)`, `ForumThread.reply(...)`, or live Wikidot behavior. It only converts malformed structural post ID values into contextual parser errors.
