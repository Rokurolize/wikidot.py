# PR Draft: Preserve Forum Post Title Spacing

## Summary

`ForumPostCollection.acquire_all_in_thread(...)` and `ForumPostCollection.acquire_all_in_threads(...)` parse forum post HTML returned by `forum/ForumViewThreadPostsModule`.

Before this fix, post titles were extracted with `title_elem.get_text().strip()`. When a rendered post title contained adjacent paragraph or formatted child elements, visible text could be concatenated. The focused regression changed `Test Post Title` to `<p>First <span>part</span></p><p>Second part</p>`; before the fix, the parsed title became `First partSecond part`.

This fix extracts post title text with a space separator and `strip=True`, preserving visible word boundaries while keeping post ID parsing, parent-post detection, content HTML preservation, author/date parsing, edit metadata parsing, pagination, duplicate-thread deduplication, retry handling, source fetching, and edit behavior unchanged.

## Related Issue

Builds on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), and [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), because those drafts established forum post acquisition as a practical read-heavy workflow and separated structural post metadata from rendered post content.

The text-fidelity failure class is adjacent to [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), and [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), because all of these fixes prevent adjacent rendered user-visible blocks from being collapsed during HTML-to-text flattening.

No upstream issue was filed from this local workspace.

## Changes

- Extract forum post title text with `get_text(" ", strip=True)` instead of `get_text().strip()`.
- Add a public thread-post acquisition regression where adjacent paragraphs and inline formatting keep a space between visible title text chunks.
- Preserve post ID parsing, parent-post detection, content HTML preservation, author/date parsing, edit metadata parsing, pagination, duplicate-thread deduplication, retry handling, source fetching, and edit behavior.

## Type Of Change

- Bug fix
- Parser/text fidelity improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Forum post titles should not concatenate adjacent rendered paragraphs or formatted child text. | `TestForumPostCollectionAcquireAll.test_acquire_all_preserves_title_text_spacing` asserts `title == "First part Second part"` through `ForumPostCollection.acquire_all_in_thread(...)`. | The RED test failed before the fix because the parsed title was `First partSecond part`. |
| Forum post acquisition should remain unchanged. | Neighboring acquisition tests for normal parsing, content-pager filtering, pagination, duplicate-thread deduplication, non-numeric pager targets, and exhausted retry remained green. | If normal post parsing, pager handling, duplicate-thread handling, or retry failure behavior regresses, the focused neighboring tests reject the local completion claim. |
| Adjacent forum workflows should remain green. | `uv run pytest tests/unit/test_forum_post.py -q` passed 38 tests, and `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 124 tests. | Regressions in category lists, category-owned thread lists, thread detail reads, forum post acquisition/source/edit behavior, forum post revisions, retry handling, or replies reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `6411d9c fix(forum_post): preserve title spacing`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_preserves_title_text_spacing -q` failed before the fix because `title` was `First partSecond part`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_preserves_title_text_spacing -q`
- `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_preserves_title_text_spacing tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_ignores_content_pager_markup tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_pagination tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_deduplicates_duplicate_thread_ids tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_ignores_non_numeric_pager_targets tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_raises_when_first_page_retry_is_exhausted tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_raises_when_paginated_retry_is_exhausted -q` passed 8 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 38 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 124 tests.
- `uv run pytest tests/unit -q` passed 661 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Forum post titles preserve a separator between adjacent rendered paragraphs and formatted child text.
- Forum post IDs, parent-post relationships, content HTML, authors, timestamps, edit metadata, pagination, duplicate-thread deduplication, and retry failure behavior remain unchanged.
- Existing post source fetching, source caching, duplicate source fetch handling, edit-form retry behavior, editing behavior, forum thread parsing, forum category parsing, and forum post revision parsing remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post titles are user-visible content. Forum post parsing should preserve visible word boundaries instead of concatenating adjacent rendered text nodes. This keeps `thread.posts` and batched forum post acquisition faithful to the rendered title without changing request flow or public object shape.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), and [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md) established `forum/ForumViewThreadPostsModule` as a practical parser boundary and post acquisition as a rollout-backed target.
- Text-fidelity drafts [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), and [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md) established visible text spacing as a recurring HTML flattening risk.
- The refreshed complexity scan continues to flag forum post parsing/acquisition paths as audit-worthy.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and post contents out of upstream discussion.

## Additional Notes

This slice does not change request payloads, retry policy, row selection, post ID parsing, parent-post parsing, content HTML preservation, author parsing, timestamp parsing, edit metadata parsing, pagination, source fetching, edit behavior, or forum post revision behavior. It only changes how forum post title text is flattened from rendered HTML into `ForumPost.title`.
