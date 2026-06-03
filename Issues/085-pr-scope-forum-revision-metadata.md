# PR Draft: Scope Forum Revision Metadata Parsing

## Summary

`ForumPostRevisionCollection._parse(...)` parses edit-history rows returned by `forum/sub/ForumPostRevisionsModule`. Before this fix, it selected the editor, edit date, and revision action link with row-wide descendant selectors: `span.printuser`, `span.odate`, and `a[onclick*='showRevision']`.

That made the parser vulnerable to unrelated nested markup inside the same table row. A nested preview or copied Wikidot UI fragment containing user/date/action-like markup could be selected before the structural revision-list cells, producing the wrong revision ID, editor, and timestamp.

This fix scopes parsing to the revision table's direct rows and structural cells: the editor cell, the date cell, and the action cell. Nested markup inside a revision row no longer contaminates revision metadata, while normal revision ordering, `rev_no` assignment, retry-aware acquisition, optional HTML acquisition, and forum post workflows remain unchanged.

## Related Issue

Builds on the forum revision acquisition work in [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), and [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md). It also applies the same structural parser-boundary lesson as [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), and [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md).

No upstream issue was filed from this local workspace.

## Changes

- Parse revision rows from the first revision table's direct `tr` children instead of every descendant table row.
- Require at least three direct `td` cells before parsing a revision row.
- Parse the editor from the first direct cell's direct `span.printuser`.
- Parse the edit date from the second direct cell's direct `span.odate`.
- Parse the revision action from the third direct cell's direct `showRevision(...)` link.
- Add a regression test where nested row content contains fake user/date/revision-action markup before the real structural cells.
- Preserve normal revision-list parsing, newest-to-oldest reversal, `rev_no` assignment, retry-aware acquisition, optional `with_html=True`, `get_htmls()`, lazy revision HTML, and adjacent forum workflows.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Nested user/date/action-like markup inside a revision row should not become revision metadata. | `TestForumPostRevisionCollectionParse.test_parse_uses_revision_cells_for_metadata` asserts the parsed ID is `9001`, editor is `test_user`, and timestamp is `1700000000`. | The RED test failed before the fix because the parsed revision ID was `9999` from nested markup. |
| Normal revision-list parsing remains intact. | Existing parse tests still assert IDs `[9001, 9002, 9003]`, oldest-first ordering, and `rev_no` assignment. | Regressions in ID order, count, or revision numbers reject the local completion claim. |
| Retry-aware forum revision acquisition and HTML acquisition remain unchanged. | `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 32 tests. | Regressions in retry, exhausted retry, duplicate handling, `with_html=True`, `get_htmls()`, lazy HTML, or cache behavior reject the local completion claim. |
| Adjacent forum workflows stay green. | `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py -q` passed 99 tests. | Forum post, thread, or revision regressions reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `8764e0d fix(forum_revision): scope revision row metadata parsing`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionParse::test_parse_uses_revision_cells_for_metadata -q` failed before the fix because the parsed revision ID was `9999` instead of `9001`.
- GREEN: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionParse::test_parse_uses_revision_cells_for_metadata -q`
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 32 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py -q` passed 99 tests.
- `uv run pytest tests/unit -q` passed 637 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- Revision-list rows are parsed only from the structural revision table's direct rows.
- Revision editor, edit date, and revision action ID are parsed from the row's structural cells.
- Nested `span.printuser`, `span.odate`, or `showRevision(...)` markup inside unrelated row content does not affect parsed revision metadata.
- Existing revision ordering, `rev_no` assignment, retry-aware revision-list acquisition, optional revision HTML acquisition, cached HTML behavior, and lazy `ForumPostRevision.html` remain unchanged.
- Existing forum post and thread workflows remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum revision history is structural table data. The parser should treat the row cells as the metadata boundary, not the entire descendant tree of a row. Scoping editor/date/action extraction to the cells Wikidot emits for those fields prevents nested user/date/action-like markup from changing revision identity or authorship while preserving the public API and acquisition flow.

## Local Evidence, Not For Upstream Paste

- The rollout ledger for this research run records broad practical `wikidot.py` usage and a high candidate-thread count, including forum inspection and revision-related acquisition as active surfaces.
- Earlier local revision drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), and [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md) established forum revision inspection as an active read-heavy surface.
- Parser-boundary drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), and [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md) established the concrete failure pattern: authored or nested forum-like markup can collide with structural parser selectors.
- The refreshed complexity scan continues to flag `src/wikidot/module/forum_post_revision.py` as a revision-list and revision-HTML hotspot worth auditing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and saved page/forum contents out of upstream discussion.

## Additional Notes

This slice does not change revision acquisition retries, request deduplication, optional HTML fetch deduplication, revision HTML parsing, forum post source fetching, edit behavior, or reply behavior. It only narrows revision-list row metadata extraction to the structural cells Wikidot emits for that metadata.
