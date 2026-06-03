# PR Draft: Ignore Nested Thread Tables

## Summary

`ForumThreadCollection._parse_list_in_category(...)` parses category thread-list rows returned by `forum/ForumViewCategoryModule`. Before this fix, it selected every descendant `table.table tr.head~tr` in the response. Even after thread metadata extraction was scoped to direct row cells, the row selection itself was still too broad.

That made the parser vulnerable to nested thread-like tables inside a thread description. If authored description markup contained a nested `table.table` with its own header and thread-like row, the nested row could be parsed as an extra `ForumThread`.

This fix scopes category thread-list parsing to direct rows of the structural table under `div.forum-category-box`. Nested thread-like tables inside descriptions are ignored, while normal category thread-list parsing, creator/date cell parsing, pagination, retry-aware acquisition, direct thread lookup, post fetching, and replies remain unchanged.

## Related Issue

Builds on [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), which scoped thread-list metadata extraction to structural cells but did not change the outer row selection boundary. It also applies the same nested-table parser-boundary lesson as [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), and remains adjacent to [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), because category thread-list acquisition feeds this parser.

No upstream issue was filed from this local workspace.

## Changes

- Parse category thread-list rows only from direct `tr` children of `div.forum-category-box > table.table`.
- Skip structural header rows before reading thread cells.
- Require direct `name`, `started`, and `posts` cells in that order before parsing a thread row.
- Preserve existing title, description, creator, date, and post-count parsing from direct structural cells.
- Add a regression test where a real thread description contains a nested `table.table` with a fake `t-9999` thread row.
- Preserve normal category thread-list parsing, category association, pagination, retry-aware acquisition, direct thread detail lookup, thread posts, replies, and adjacent forum category/post/revision behavior.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Nested thread-like tables inside a thread description should not create extra threads. | `TestForumThreadCollectionAcquireAll.test_acquire_all_ignores_nested_thread_tables` asserts the parsed thread IDs are `[3001, 3002]`. | The RED test failed before the fix because parsed thread IDs were `[3001, 9999, 3002]`. |
| Thread post counts should come from the structural category thread-list rows. | The same regression test asserts the real thread post counts remain `5` and `3`. | The fake nested row's `999` post count must not appear as a parsed thread. |
| Normal thread-list parsing, category association, retry behavior, pagination, and direct thread lookup remain intact. | `uv run pytest tests/unit/test_forum_thread.py -q` passed 32 tests. | Regressions in title, description, thread ID, creator/date, post count, category association, pagination, exhausted retry handling, direct thread lookup, post fetching, or replies reject the local completion claim. |
| Adjacent forum workflows stay green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 116 tests. | Forum category, thread, post, or revision regressions reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `b42289d fix(forum_thread): ignore nested thread tables`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_ignores_nested_thread_tables -q` failed before the fix because parsed thread IDs were `[3001, 9999, 3002]` instead of `[3001, 3002]`.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_ignores_nested_thread_tables -q`
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 32 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 116 tests.
- `uv run pytest tests/unit -q` passed 639 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- Category thread-list rows are parsed only from the structural direct table rows emitted under `div.forum-category-box`.
- Thread title, description, creator/date, and post count are parsed from direct structural row cells.
- Nested `table.table`, `tr.head`, thread links, started cells, or post-count cells inside a thread description do not create extra `ForumThread` records.
- Existing category thread-list pagination, retry-aware fetching, exhausted retry handling, direct thread detail fetching, post-list fetching, and reply behavior remain unchanged.
- Existing forum category, post, and revision workflows remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Wikidot forum descriptions can contain rendered tables or copied forum-like UI fragments. The category thread-list parser should treat the forum category box's direct table rows as the structural boundary, not every descendant `table.table` row that might appear in authored descriptions. Scoping row iteration to the structural table prevents nested description markup from creating false threads while preserving the public API and acquisition flow.

## Local Evidence, Not For Upstream Paste

- The rollout ledger for this research run records broad practical `wikidot.py` usage and a high candidate-thread count, including forum category/thread inspection as active surfaces.
- Earlier category thread-list draft [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md) established category thread-list parsing as an active parser-boundary surface.
- Nested category-table draft [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md) established the adjacent failure pattern: descendant table-row selectors can parse authored nested forum-like tables as structural records.
- The refreshed complexity scan continues to flag `src/wikidot/module/forum_thread.py` around category thread-list parsing and acquisition as an audit-worthy forum hot path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and saved page/forum contents out of upstream discussion.

## Additional Notes

This slice does not change category thread-list acquisition retries, pagination, direct thread detail parsing, post acquisition, reply behavior, or forum post/revision parser rules. It only narrows category thread-list row iteration to the structural table rows Wikidot emits for thread records.
