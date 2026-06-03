# PR Draft: Preserve Thread List Title Spacing

## Summary

`ForumThreadCollection.acquire_all_in_category(...)`, used by `ForumCategory.threads`, parses category thread-list HTML returned by `forum/ForumViewCategoryModule`.

Before this fix, category thread-list titles were extracted with `title.text`. When a rendered thread-list title contained adjacent paragraph or formatted child elements, visible text could be concatenated. The focused regression changed `Test Thread` to `<p>First <span>part</span></p><p>Second part</p>`; before the fix, the parsed title became `First partSecond part`.

This fix extracts category thread-list title text with a space separator and `strip=True`, preserving visible word boundaries while keeping thread ID parsing, description parsing, creator/date parsing, post-count parsing, nested thread-table filtering, description-pager filtering, pagination, retry handling, thread detail lookup, post acquisition, and reply behavior unchanged.

## Related Issue

Builds on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), and [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), because those drafts established category thread-list acquisition as a practical read-heavy workflow and separated structural thread rows from rendered description content.

The text-fidelity failure class is adjacent to [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), and [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), because all of these fixes preserve user-visible forum text while avoiding accidental parser-boundary changes.

No upstream issue was filed from this local workspace.

## Changes

- Extract category thread-list title text with `get_text(" ", strip=True)` instead of raw `.text`.
- Add a public category thread-list acquisition regression where adjacent paragraphs and inline formatting keep a space between visible title text chunks.
- Preserve thread ID parsing, description parsing, creator/date parsing, post-count parsing, nested thread-table filtering, description-pager filtering, pagination, retry handling, thread detail lookup, post acquisition, and reply behavior.

## Type Of Change

- Bug fix
- Parser/text fidelity improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Category thread-list titles should not concatenate adjacent rendered paragraphs or formatted child text. | `TestForumThreadCollectionAcquireAll.test_acquire_all_preserves_title_text_spacing` asserts `title == "First part Second part"` through `ForumThreadCollection.acquire_all_in_category(...)`. | The RED test failed before the fix because the parsed title was `First partSecond part`. |
| Category thread-list acquisition should remain unchanged. | Neighboring acquisition tests for normal parsing, nested thread-table filtering, description-pager filtering, description spacing, pagination, non-numeric pager links, and exhausted retry remained green. | If normal category thread-list parsing, row-boundary filtering, pager handling, or retry failure behavior regresses, the focused neighboring tests reject the local completion claim. |
| Adjacent forum workflows should remain green. | `uv run pytest tests/unit/test_forum_thread.py -q` passed 38 tests, and `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 125 tests. | Regressions in category lists, category-owned thread lists, thread detail reads, forum post acquisition/source/edit behavior, forum post revisions, retry handling, or replies reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `b3fa3c9 fix(forum_thread): preserve list title spacing`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_preserves_title_text_spacing -q` failed before the fix because `title` was `First partSecond part`.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_preserves_title_text_spacing -q`
- `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_ignores_nested_thread_tables tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_ignores_description_pager_markup tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_preserves_description_text_spacing tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_preserves_title_text_spacing tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_pagination tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_ignores_non_numeric_pager_links tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_raises_when_paginated_retry_is_exhausted -q` passed 8 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 38 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 125 tests.
- `uv run pytest tests/unit -q` passed 662 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Category thread-list titles preserve a separator between adjacent rendered paragraphs and formatted child text.
- Thread IDs, descriptions, authors, timestamps, post counts, category associations, pagination, nested thread-table filtering, description-pager filtering, and retry failure behavior remain unchanged.
- Existing category list parsing, thread detail parsing, forum post acquisition, forum post source/edit behavior, forum post revision parsing, and reply behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Category thread-list titles are user-visible content. Thread-list parsing should preserve visible word boundaries instead of concatenating adjacent rendered text nodes. This keeps `category.threads` faithful to rendered thread titles without changing request flow or public object shape.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), and [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md) established `forum/ForumViewCategoryModule` as a practical parser boundary and category thread-list acquisition as a rollout-backed target.
- Text-fidelity drafts [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), and [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md) established visible forum text preservation as a recurring HTML flattening risk.
- The refreshed complexity scan continues to flag forum thread parsing/acquisition paths as audit-worthy.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and thread contents out of upstream discussion.

## Additional Notes

This slice does not change request payloads, retry policy, row selection, thread ID parsing, description parsing, creator parsing, timestamp parsing, post-count parsing, pagination, nested-table filtering, description-pager filtering, thread detail parsing, forum post parsing, forum post revision parsing, or reply behavior. It only changes how category thread-list title text is flattened from rendered HTML into `ForumThread.title`.
