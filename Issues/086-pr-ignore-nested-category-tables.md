# PR Draft: Ignore Nested Category Tables

## Summary

`ForumCategoryCollection.acquire_all(...)`, exposed through `site.forum.categories`, parses the forum index returned by `forum/ForumStartModule`. Before this fix, it selected every descendant `table tr.head~tr` and then searched each row with row-wide selectors for category name, thread count, and post count.

That made the category parser vulnerable to nested tables inside a category description. If authored description markup contained a table with its own header row and category-like cells, the nested row could be parsed as an extra `ForumCategory`. Row-wide selectors also allowed nested count cells to be selected before the structural thread/post cells.

This fix scopes category parsing to direct rows of the forum group's structural category table and reads category metadata from the direct cells in each row. Nested category-like tables inside descriptions are ignored, while normal category parsing, empty forum indexes, retry-aware acquisition, missing-element failures, and thread creation remain unchanged.

## Related Issue

Builds on the category acquisition work in [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md). It also applies the same structural parser-boundary lesson as [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), and [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md).

No upstream issue was filed from this local workspace.

## Changes

- Parse category rows only from direct rows of `div.forum-group > div:not(.head) > table`.
- Skip structural header rows before reading category cells.
- Require direct `name`, `threads`, and `posts` cells in that order before parsing a category row.
- Parse the category title/link and description from direct children of the direct name cell.
- Parse thread and post counts from the structural direct count cells.
- Add a regression test where a real category description contains a nested category-like table with fake category ID and count cells.
- Preserve normal category parsing, empty forum index behavior, retry-aware acquisition, missing-element failures, and `ForumCategory.create_thread(...)`.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Nested category-like tables inside a category description should not create extra categories. | `TestForumCategoryCollectionAcquireAll.test_acquire_all_ignores_nested_category_tables` asserts the parsed category IDs are `[1001]`. | The RED test failed before the fix because parsed category IDs were `[1001, 9999]`. |
| Thread and post counts should come from the structural category row cells. | The same regression test asserts `threads_count == 10` and `posts_count == 50`. | Nested fake count cells with values `999` and `888` must not affect the parsed category. |
| Normal category parsing, empty list handling, retry behavior, and thread creation remain intact. | `uv run pytest tests/unit/test_forum_category.py -q` passed 16 tests. | Regressions in category values, empty forum index behavior, transient retry handling, exhausted retry handling, missing-element handling, or thread creation reject the local completion claim. |
| Adjacent forum workflows stay green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 115 tests. | Forum category, thread, post, or revision regressions reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `3b7aae8 fix(forum_category): ignore nested category tables`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_ignores_nested_category_tables -q` failed before the fix because parsed category IDs were `[1001, 9999]` instead of `[1001]`.
- GREEN: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_ignores_nested_category_tables -q`
- `uv run pytest tests/unit/test_forum_category.py -q` passed 16 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 115 tests.
- `uv run pytest tests/unit -q` passed 638 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- Category rows are parsed only from the structural direct category table rows emitted under each forum group.
- Category name, title link, description, thread count, and post count are parsed from direct structural cells.
- Nested `tr.head`, category links, or count cells inside a category description do not create extra `ForumCategory` records or override structural counts.
- Existing category field values, empty forum index behavior, retry-aware acquisition, exhausted retry handling, missing-element failures, and thread creation remain unchanged.
- Existing forum thread, post, and revision workflows remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum categories are structural rows in the `ForumStartModule` category table. The parser should treat that table's direct rows and cells as the metadata boundary, not every descendant table row that might appear inside authored category descriptions. Scoping category extraction to direct structural cells prevents nested description markup from changing category identity or counts while preserving the public API and acquisition flow.

## Local Evidence, Not For Upstream Paste

- The rollout ledger for this research run records broad practical `wikidot.py` usage and a high candidate-thread count, including forum category and thread inspection as active surfaces.
- Earlier category acquisition draft [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md) established `ForumStartModule` category inspection as a read-heavy workflow worth hardening.
- Parser-boundary drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), and [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md) established the concrete failure pattern: authored or nested forum-like markup can collide with structural parser selectors.
- The refreshed complexity scan continues to flag `src/wikidot/module/forum_category.py` as a forum inspection path with selector-heavy parsing worth auditing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and saved page/forum contents out of upstream discussion.

## Additional Notes

This slice does not change category acquisition retries, exhausted retry error behavior, thread caching, `ForumCategory.create_thread(...)`, thread retrieval, forum post parsing, or revision parsing. It only narrows forum-start category list parsing to structural category table rows and direct row cells.
