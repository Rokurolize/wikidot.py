# PR Draft: Scope Thread List Metadata Parsing

## Summary

`ForumThreadCollection._parse_list_in_category(...)` parses category thread-list rows returned by `forum/ForumViewCategoryModule`. Before this fix, the parser selected thread author and creation date with row-wide descendant selectors: `span.printuser` and `span.odate`.

That is too broad for Wikidot-rendered content. A thread description can contain rendered user/date-like markup, and the description cell appears before the structural started-by cell in the row. The parser could therefore treat description content as the thread creator and creation timestamp.

This fix scopes row parsing to the structural cells first: `td.name` for title/description, `td.started` for creator/date, and `td.posts` for post count. Description metadata markup no longer contaminates thread-list authorship, while normal category thread-list parsing, pagination, retry behavior, direct thread lookup, and forum post workflows remain unchanged.

## Related Issue

Builds on the same parser-boundary lesson as [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), and [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md): user-authored rendered markup must not be parsed as structural forum metadata. It is also adjacent to [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), because category thread-list acquisition feeds this parser.

No upstream issue was filed from this local workspace.

## Changes

- Scope category thread-list row parsing to direct structural cells: `td.name`, `td.started`, and `td.posts`.
- Parse title and description from `td.name`.
- Parse thread creator and creation date from `td.started`.
- Add a regression test where the thread description contains fake `span.printuser` and `span.odate` markup before the real started-by cell.
- Preserve normal category thread-list parsing, category association, pagination, retry-aware acquisition, direct thread detail lookup, thread posts, replies, and adjacent forum post/revision behavior.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Description-rendered user/date markup should not become thread-list creator/date metadata. | `TestForumThreadCollectionParseListInCategory.test_parse_ignores_description_metadata_markup` asserts the parsed creator remains `test_user` and the timestamp remains `1700000000`. | The RED test failed before the fix because the parsed creator was `content_user`. |
| Normal thread-list fields remain parsed from the fixture shape. | Existing `test_parse_fields`, `test_parse_success`, and category association tests still pass. | Regressions in title, description, thread ID, post count, or category association reject the local completion claim. |
| Category thread-list acquisition stays green. | `uv run pytest tests/unit/test_forum_thread.py` passed 31 tests. | Pagination, exhausted retry, empty input, direct thread lookup, or thread reply regressions reject the local completion claim. |
| Adjacent forum workflows stay green. | `uv run pytest tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py` passed 113 tests. | Forum category/thread/post/revision regressions reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `fe4f5a8 fix(forum_thread): scope thread list metadata parsing`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionParseListInCategory::test_parse_ignores_description_metadata_markup -q` failed before the fix because the parsed creator was `content_user` instead of `test_user`.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionParseListInCategory::test_parse_ignores_description_metadata_markup tests/unit/test_forum_thread.py::TestForumThreadCollectionParseListInCategory::test_parse_fields tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_single_page -q`
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 31 tests.
- `uv run pytest tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 113 tests.
- `uv run pytest tests/unit -q` passed 636 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Thread-list title and description are parsed from the row's structural `td.name` cell.
- Thread-list creator and creation date are parsed from the row's structural `td.started` cell.
- Thread-list post count is parsed from the row's structural `td.posts` cell.
- Rendered `span.printuser` or `span.odate` markup inside a thread description does not affect `ForumThread.created_by` or `ForumThread.created_at`.
- Existing category thread-list pagination, retry-aware fetching, direct thread detail fetching, post-list fetching, and reply behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Wikidot forum descriptions can render HTML-like fragments that contain user/date widgets or copied forum UI markup. The category thread-list parser should treat table cells as the structural boundary, not the entire row. Scoping metadata extraction to `td.started` prevents description content from changing thread authorship fields while preserving the public API and existing acquisition flow.

## Local Evidence, Not For Upstream Paste

- The rollout ledger for this research run records broad practical `wikidot.py` usage and a high candidate-thread count, including forum module inspection as an active surface.
- Earlier local parser drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), and [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md) established the concrete failure pattern: authored rendered forum-like markup can collide with structural parser selectors.
- The refreshed complexity scan continued to flag `src/wikidot/module/forum_thread.py` around category thread-list parsing and acquisition as an audit-worthy forum hot path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and saved page/forum contents out of upstream discussion.

## Additional Notes

This slice does not change direct thread detail parsing, category acquisition pagination, retry policy, post acquisition, reply behavior, or any forum post parser rules. It only narrows category thread-list row metadata extraction to the cells Wikidot emits for that metadata.
