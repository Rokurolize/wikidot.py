# PR Draft: Scope Recent Changes Comment Markup Parsing

## Summary

`Site.get_recent_changes(...)` parses recent-change rows returned by `changes/SiteChangesListModule`.

Before this fix, recent-change items were selected response-wide with `div.changes-list-item`, and metadata such as title, flags, date, revision number, and user were read with descendant selectors over the entire item. If a user-authored edit comment rendered change-like markup, that nested content could be parsed as an extra `SiteChange` record or add fake flags to the real change.

This fix keeps the existing recent-changes acquisition, pagination, retry, limit, and `SiteChange` API behavior, but parses only top-level change items and direct cells from the structural first row of each change table. Comment text remains read from the direct comment row. Change-like markup inside comments no longer alters the change count or structural flags.

## Related Issue

Builds on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md) and [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), because those drafts established recent changes as a practical local usage path and hardened its acquisition/pagination behavior. The parser-boundary motivation follows [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md), and [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md).

No upstream issue was filed from this local workspace.

## Changes

- Skip `div.changes-list-item` candidates nested inside tables, which covers change-like markup rendered inside the comment cell.
- Locate each structural change table as a direct child of the top-level change item.
- Parse title, flags, modified date, revision number, and modifier from direct cells of the structural first row.
- Parse edit comments from the direct comment row only.
- Add a public `Site.get_recent_changes(...)` regression test where the edit comment contains a nested change-like block with fake flags and user/date metadata.
- Preserve zero-limit behavior, first-page retry handling, empty results, pager parsing, paginated batching, limit-bounded pagination, normal change parsing, and `SiteChange` output fields.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Recent-change records should come from structural top-level change items, not rendered edit-comment content. | `TestSiteGetRecentChanges.test_get_recent_changes_ignores_comment_change_like_markup` asserts only the real change is returned. | The RED test failed before the fix because two changes were returned; the second came from the nested comment block. |
| Recent-change flags should come from the structural flags cell, not comment content. | The same regression asserts `flags == ["S"]` even though the comment contains a nested fake `FAKE` flag. | Descendant flag parsing that includes comment flags rejects the local completion claim. |
| Public recent-changes behavior should remain green. | `uv run pytest tests/unit/test_site.py -q` passed 56 tests. | Regressions in empty results, retry behavior, limit handling, pager parsing, pagination batching, or normal parsing reject the local completion claim. |
| Adjacent site/page behavior stays green. | `uv run pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 150 tests. | Site or page regressions reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `7f3a447 fix(site): scope recent changes parsing`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_ignores_comment_change_like_markup -q` failed before the fix because `len(changes)` was `2` instead of `1`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_ignores_comment_change_like_markup -q`
- `uv run pytest tests/unit/test_site.py -q` passed 56 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 150 tests.
- `uv run pytest tests/unit -q` passed 643 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- Recent changes are parsed only from structural top-level `div.changes-list-item` blocks.
- A change-like block nested inside the comment cell does not create an extra `SiteChange`.
- Flags are parsed only from the structural first-row flags cell.
- Title, revision number, modified date, and modifier are parsed only from direct structural cells.
- Existing zero-limit behavior, first-page retry handling, empty results, pager parsing, paginated batching, limit-bounded pagination, normal fixture parsing, and `SiteChange` field semantics remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Edit comments are user-authored text adjacent to structural recent-change metadata. The parser should treat the first row of each top-level change table as the metadata boundary rather than selecting every matching descendant in the change item. This prevents comment content from changing recent-change counts or flags while preserving the current public `Site.get_recent_changes(...)` behavior and retry/pagination flow.

## Local Evidence, Not For Upstream Paste

- The rollout ledger for this research run records broad practical `wikidot.py` usage and a high candidate-thread count, including site-level read paths and recent-changes acquisition as locally hardened surfaces.
- Earlier recent-changes drafts [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md) and [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md) established this path as a practical local target.
- Parser-boundary drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md), and [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md) established the concrete failure pattern: authored content can collide with structural parser selectors.
- The refreshed complexity scan continues to flag `src/wikidot/module/site.py` around recent-changes parsing as an audit-worthy path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and saved edit comments out of upstream discussion.

## Additional Notes

This slice does not change request construction, retry behavior, pagination batching, limit handling, pager parsing, or the `SiteChange` dataclass. It only narrows recent-change HTML parsing to top-level structural change rows and direct metadata cells.
