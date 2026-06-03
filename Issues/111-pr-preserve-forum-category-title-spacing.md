# PR Draft: Preserve Forum Category Title Spacing

## Summary

`ForumCategoryCollection.acquire_all(...)`, used by `site.forum.categories`, parses forum category HTML returned by `forum/ForumStartModule`.

Before this fix, category titles were extracted with `name_link_elem.text`. When a rendered category title contained adjacent paragraph or formatted child elements, visible text could be concatenated. The focused regression changed `Test Category` to `<p>First <span>part</span></p><p>Second part</p>`; before the fix, the parsed title became `First partSecond part`.

This fix extracts category title text with a space separator and `strip=True`, preserving visible word boundaries while keeping category ID parsing, description parsing, thread-count parsing, post-count parsing, nested category-table filtering, retry handling, category thread access, and thread creation behavior unchanged.

## Related Issue

Builds on [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), and [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), because those drafts established forum category list acquisition as a practical read-heavy workflow, separated category rows from rendered description content, and covered the adjacent description text-fidelity risk in the same parser.

The text-fidelity failure class is adjacent to [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), and [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), because all of these fixes preserve user-visible forum text while avoiding accidental parser-boundary changes.

No upstream issue was filed from this local workspace.

## Changes

- Extract forum category title text with `get_text(" ", strip=True)` instead of raw `.text`.
- Add a public category acquisition regression where adjacent paragraphs and inline formatting keep a space between visible title text chunks.
- Preserve category ID parsing, description parsing, thread-count parsing, post-count parsing, nested category-table filtering, retry handling, category thread access, and thread creation behavior.

## Type Of Change

- Bug fix
- Parser/text fidelity improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Forum category titles should not concatenate adjacent rendered paragraphs or formatted child text. | `TestForumCategoryCollectionAcquireAll.test_acquire_all_preserves_title_text_spacing` asserts `title == "First part Second part"` through `ForumCategoryCollection.acquire_all(...)`. | The RED test failed before the fix because the parsed title was `First partSecond part`. |
| Forum category list parsing should remain unchanged. | Neighboring acquisition tests for normal parsing, existing fields, description spacing, nested category-table filtering, empty lists, and exhausted retry remained green. | If normal category parsing, count parsing, description spacing, nested-table filtering, or retry failure behavior regresses, the focused neighboring tests reject the local completion claim. |
| Adjacent forum workflows should remain green. | `uv run pytest tests/unit/test_forum_category.py -q` passed 18 tests, and `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 126 tests. | Regressions in category lists, category-owned thread lists, thread detail reads, forum post acquisition/source/edit behavior, forum post revisions, retry handling, or replies reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `833e720 fix(forum_category): preserve title spacing`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_preserves_title_text_spacing -q` failed before the fix because `title` was `First partSecond part`.
- GREEN: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_preserves_title_text_spacing -q`
- `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_success tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_parse_fields tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_preserves_description_text_spacing tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_preserves_title_text_spacing tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_ignores_nested_category_tables tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_empty tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_raises_when_retry_is_exhausted -q` passed 7 tests.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 18 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 126 tests.
- `uv run pytest tests/unit -q` passed 663 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Forum category titles preserve a separator between adjacent rendered paragraphs and formatted child text.
- Forum category ID, description, thread-count, post-count, and site association parsing remain unchanged.
- Description-rendered nested category-table markup still cannot create fake categories.
- Existing category list lookup, retry-aware fetching, exhausted retry handling, category thread access, thread creation, forum thread/post/revision parsing, and reply behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum category titles are user-visible content and can render multiple paragraphs or formatted inline HTML. Forum category parsing should preserve visible word boundaries instead of concatenating adjacent rendered text nodes. This keeps `site.forum.categories` faithful to the rendered title without changing request flow or public object shape.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), and [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md) established `forum/ForumStartModule` as a practical parser boundary and category list acquisition as a rollout-backed target.
- Text-fidelity drafts [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), and [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md) established visible forum text preservation as a recurring HTML flattening risk.
- The refreshed complexity scan continues to flag forum category parsing/acquisition paths as audit-worthy.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and category contents out of upstream discussion.

## Additional Notes

This slice does not change request payloads, retry policy, row selection, category ID parsing, description parsing, thread-count parsing, post-count parsing, nested category-table filtering, category-owned thread lookup, thread creation, or forum post behavior. It only changes how forum category title text is flattened from rendered HTML into `ForumCategory.title`.
