# PR Draft: Preserve Thread List Description Spacing

## Summary

`ForumThreadCollection._parse_list_in_category(...)`, used by `ForumThreadCollection.acquire_all_in_category(...)` and `ForumCategory.threads`, parses category thread-list HTML returned by `forum/ForumViewCategoryModule`.

Before this fix, category thread-list descriptions were extracted with `description_elem.text`. When a rendered thread description contained adjacent paragraph or formatted child elements, visible text could be concatenated. The focused regression changed `Test thread description` to `<p>First <span>part</span></p><p>Second part</p>`; before the fix, the parsed description became `First partSecond part`.

This fix extracts thread-list description text with a space separator and `strip=True`, preserving visible word boundaries while keeping category thread-list metadata, pagination, pager filtering, direct thread lookup, post fetching, and reply behavior unchanged.

## Related Issue

Builds on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), and [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), because those drafts established category thread-list parsing as a practical local workflow and separated thread descriptions from generated thread-list controls and metadata.

The text-fidelity failure class is adjacent to [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), because both fixes prevent adjacent rendered user-visible blocks from being collapsed during HTML-to-text flattening.

No upstream issue was filed from this local workspace.

## Changes

- Extract category thread-list description text with `get_text(" ", strip=True)` instead of raw `.text`.
- Add a public category acquisition regression where adjacent paragraphs and inline formatting keep a space between visible text chunks.
- Preserve category association, title parsing, creator parsing, creation time parsing, post-count parsing, pagination, retry handling, pager filtering, direct thread lookup, post fetching, and replies.

## Type Of Change

- Bug fix
- Parser/text fidelity improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Category thread-list descriptions should not concatenate adjacent rendered paragraphs or formatted child text. | `TestForumThreadCollectionAcquireAll.test_acquire_all_preserves_description_text_spacing` asserts `description == "First part Second part"` through `ForumThreadCollection.acquire_all_in_category(...)`. | The RED test failed before the fix because the parsed description was `First partSecond part`. |
| Category thread-list parsing and pager behavior should remain unchanged. | Neighboring acquisition tests for single-page parsing, description pager filtering, real pagination, and normal field parsing remained green. | If pagination, structural metadata, or normal descriptions regress, the focused neighboring tests reject the local completion claim. |
| Direct and adjacent forum workflows should remain green. | `uv run pytest tests/unit/test_forum_thread.py -q` passed 37 tests, and `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 122 tests. | Regressions in category list parsing, thread detail reads, forum post acquisition, forum post revisions, retry handling, or replies reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `a7f673f fix(forum_thread): preserve list description spacing`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_preserves_description_text_spacing -q` failed before the fix because `description` was `First partSecond part`.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_preserves_description_text_spacing -q`
- `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_ignores_description_pager_markup tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_preserves_description_text_spacing tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_pagination tests/unit/test_forum_thread.py::TestForumThreadCollectionParseListInCategory::test_parse_fields -q` passed 5 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 37 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 122 tests.
- `uv run ruff check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py`
- `uv run ruff format --check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py`
- `uv run pytest tests/unit -q` passed 659 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Category thread-list descriptions preserve a separator between adjacent rendered paragraphs and formatted child text.
- Category thread-list title, creator, creation-time, post-count, and category association parsing remain unchanged.
- Description-rendered pager markup still cannot trigger phantom category page fetches.
- Existing category thread-list lookup, real pagination, retry-aware fetching, exhausted retry handling, direct thread lookup, post-list fetching, forum post revisions, and reply behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Thread descriptions in category thread lists are user-visible content and can render multiple paragraphs or formatted inline HTML. Thread-list parsing should preserve visible word boundaries instead of concatenating adjacent rendered text nodes. This keeps category thread-list reads faithful to the rendered description without changing request flow or public object shape.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), and [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md) established `forum/ForumViewCategoryModule` as a practical read-heavy target and thread descriptions as a parser-boundary risk area.
- Text-fidelity drafts [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md) and [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md) established visible text spacing as a recurring HTML flattening risk.
- The refreshed complexity scan continues to flag forum thread parsing/acquisition paths as audit-worthy.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and thread contents out of upstream discussion.

## Additional Notes

This slice does not change request payloads, retry policy, pager discovery, row selection, title parsing, creator parsing, creation time parsing, post-count parsing, category assignment, direct thread detail lookup, post acquisition, post revision parsing, or reply behavior. It only changes how category thread-list description text is flattened from rendered HTML into `ForumThread.description`.
