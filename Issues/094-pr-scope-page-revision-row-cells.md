# PR Draft: Scope Page Revision Row Cell Parsing

## Summary

`PageCollection._acquire_page_revisions(...)` parses `history/PageRevisionListModule` rows into page-owned `PageRevisionCollection` objects.

Before this fix, each structural revision row used `rev_element.select("td")`, which collects every descendant table cell in the row. If a revision row cell contained nested table markup before the structural `by`, `date`, or `comment` cells, the parser could shift its positional indexes and fail to read the real editor/date/comment columns. The focused regression failed with `NoElementException("Cannot find created by element ...")` even though the row still had the normal seven direct structural cells.

This fix keeps the existing request batching, retry handling, duplicate page-id behavior, response parse reuse, revision object ownership, and malformed-row error surface, but reads only direct `td` children from each revision row. It also reads editor and date spans directly from their structural cells.

## Related Issue

Builds on [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), and [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), because those drafts established page revision-list acquisition as a practical, repeatedly used page-detail surface. The parser-boundary motivation follows [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), and [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md).

No upstream issue was filed from this local workspace.

## Changes

- Parse direct `td` children of each structural `table.page-history > tr[id^=revision-row-]` row.
- Keep the existing seven-cell positional mapping for revision number, editor, date, and comment.
- Parse direct `span.printuser` from the structural editor cell.
- Parse direct `span.odate` from the structural date cell.
- Add a regression where nested table cells inside a non-metadata revision row cell do not shift editor/date/comment parsing.
- Preserve existing revision-list success, cached-page skipping, duplicate page-id propagation, response parse reuse, and missing-cell error behavior.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Revision-list column positions should come from direct structural row cells, not descendant table cells. | `TestPageCollectionAcquire.test_acquire_revisions_ignores_nested_table_cells` inserts nested table cells into the first revision row and asserts revision ID, revision number, editor, timestamp, and comment still come from the real direct cells. | The RED test failed before the fix with `NoElementException("Cannot find created by element ...")` because descendant `td` collection shifted the editor cell index. |
| Existing page revision acquisition behavior should remain green. | `uv run pytest tests/unit/test_page.py -q` passed 97 tests, and `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py -q` passed 153 tests. | Regressions in revision parsing, lazy revision access, revision source/HTML acquisition, adjacent file behavior, or duplicate page-id behavior reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `13827d3 fix(page): scope revision row cell parsing`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_ignores_nested_table_cells -q` failed before the fix with `NoElementException("Cannot find created by element ...")`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_ignores_nested_table_cells -q`
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_success -q`
- `uv run pytest tests/unit/test_page.py -q` passed 97 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py -q` passed 153 tests.
- `uv run pytest tests/unit -q` passed 646 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- Revision-list parser treats only direct row `td` children as structural columns.
- Nested table cells inside a revision row cannot shift the parsed editor, timestamp, or comment columns.
- Direct structural editor/date cells continue to parse normal `span.printuser` and `span.odate` elements.
- Malformed rows with fewer than seven direct structural cells still raise `NoElementException`.
- Existing request batching, retry handling, duplicate page-id propagation, response parse reuse, page-owned `PageRevisionCollection` objects, lazy `Page.revisions`, and `Page.latest_revision` behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Revision history is a read-heavy evidence surface for page inspection, source auditing, publication checks, and rollback workflows. The revision-list module emits a fixed row schema, so the parser should use direct structural cells as the boundary. That avoids confusing nested table markup with the row's generated columns while preserving the existing public `PageRevision` behavior.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), and [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md) established revision-list acquisition as a practical target rather than speculative code.
- The refreshed complexity scan continued to flag `src/wikidot/module/page.py` around revision-list parsing.
- Parser-boundary drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md) through [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md) established the concrete failure class: descendant selectors can confuse generated module structure with nested markup.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and page content out of upstream discussion.

## Additional Notes

This slice does not change revision-list request construction, retry policy, duplicate page-id grouping, response parse reuse, revision source/HTML fetching, date parsing semantics, user parsing semantics, or mutation paths. It only narrows revision row cell and metadata span discovery to direct structural elements.
