# PR Draft: Preserve Thread Title Separators

## Summary

`ForumThreadCollection._parse_thread_page(...)`, used by `ForumThreadCollection.acquire_from_thread_ids(...)`, `Site.get_thread(...)`, `Site.get_threads(...)`, and `ForumThread.get_from_id(...)`, parses direct thread detail HTML returned by `forum/ForumViewThreadModule`.

Before this fix, thread titles were extracted with `bc_elem.get_text(" ", strip=True).split("»")[-1].strip()`. That treats every `»` character in the breadcrumb text as a structural separator. If a real thread title contains the same character, for example `Alpha » Beta`, the parsed title becomes only `Beta`.

This fix first reads the trailing direct text node from `div.forum-breadcrumbs`, removes only the leading breadcrumb separator from that direct title chunk, and keeps the previous full-text split as a fallback. Normal breadcrumbs still parse as before, while titles that contain `»` are preserved.

## Related Issue

Builds on [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), and [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), because those drafts established direct thread detail acquisition, thread detail metadata boundaries, and visible thread detail text fidelity as practical local workflows.

The parser-boundary failure class is adjacent to [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), and [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), because all of these fixes separate user-visible forum content from generated Wikidot structure.

No upstream issue was filed from this local workspace.

## Changes

- Add a focused helper that extracts the title from the trailing direct text node of `div.forum-breadcrumbs`.
- Strip only the leading breadcrumb separator from that direct title chunk.
- Preserve the old full-text split as a fallback for unexpected breadcrumb markup.
- Add a public acquisition regression where a direct thread title containing `»` is preserved.
- Preserve direct thread detail description parsing, structural statistics parsing, retry-aware fetching, duplicate-ID behavior, category thread lists, forum post fetching, forum post revisions, and replies.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Direct thread detail titles should preserve `»` when it is part of the title text. | `TestForumThreadCollectionAcquireFromIds.test_acquire_from_ids_preserves_breadcrumb_title_separator` asserts `title == "Alpha » Beta"` through `ForumThreadCollection.acquire_from_thread_ids(...)`. | The RED test failed before the fix because the parsed title was `Beta`. |
| Normal breadcrumbs and empty-title errors should remain unchanged. | Neighboring direct parser tests for normal fields and empty breadcrumbs remained green. | If the helper accepts an empty title or changes normal `Test Thread Title` parsing, the focused neighboring tests reject the local completion claim. |
| Direct thread acquisition and adjacent forum workflows should remain green. | `uv run pytest tests/unit/test_forum_thread.py -q` passed 36 tests, and `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 121 tests. | Regressions in direct thread lookup, category thread lists, post acquisition, revision parsing, retry handling, duplicate IDs, or replies reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `275b41a fix(forum_thread): preserve breadcrumb title separators`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_preserves_breadcrumb_title_separator -q` failed before the fix because `title` was `Beta`.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_preserves_breadcrumb_title_separator -q`
- `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_preserves_breadcrumb_title_separator tests/unit/test_forum_thread.py::TestForumThreadCollectionParseThreadPage::test_parse_fields tests/unit/test_forum_thread.py::TestForumThreadCollectionParseThreadPage::test_parse_empty_breadcrumb_title_raises tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_success -q` passed 4 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 36 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 121 tests.
- `uv run ruff check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py`
- `uv run ruff format --check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py`
- `uv run pytest tests/unit -q` passed 657 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Direct thread detail titles preserve the `»` character when it appears inside the actual title text.
- Normal breadcrumb title parsing remains unchanged.
- Empty breadcrumb titles still raise `NoElementException("Thread title is not found.")`.
- Description, creator, creation time, post count, and thread ID parsing remain unchanged.
- Existing direct thread lookup, duplicate ID behavior, retry-aware fetching, exhausted retry handling, category thread-list parsing, forum post fetching, revision parsing, and reply behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Wikidot breadcrumbs use `»` as a separator, but the same character can also appear in user-visible forum thread titles. The parser should remove the breadcrumb separator from the generated breadcrumb structure without treating every occurrence of that character as structural. This keeps direct thread lookup faithful to the rendered title without changing request flow or public object shape.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), and [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md) established `forum/ForumViewThreadModule` as a practical read-heavy target and direct thread detail parsing as a parser-boundary risk area.
- Parser-boundary drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), and [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md) established forum authored content and visible text fidelity as recurring parser-boundary concerns.
- The refreshed complexity scan continues to flag forum thread parsing/acquisition paths as audit-worthy.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and thread contents out of upstream discussion.

## Additional Notes

This slice does not change request payloads, retry policy, direct thread batch deduplication, thread ID extraction from scripts, description parsing, structural statistics selection, creator parsing, creation time parsing, post-count parsing, category thread-list acquisition, post acquisition, post revision parsing, or reply behavior. It only changes how the direct thread detail parser separates generated breadcrumb structure from the visible thread title.
