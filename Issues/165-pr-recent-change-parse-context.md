# PR Draft: Include Context In Recent-Change Parse Errors

## Summary

`Site.get_recent_changes(...)` parses `changes/SiteChangesListModule` HTML into `SiteChange` records. The parser already rejects malformed structural change items when required elements such as the table, metadata row, title link, date, revision number, or user are missing, but those `NoElementException` messages only named the missing field.

This follow-up keeps the existing malformed-response failure behavior, retry flow, pagination, limit handling, structural comment filtering, and successful `SiteChange` output shape, but includes the affected site `unix_name`, recent-changes page number, and top-level change item position in those parser failures.

## Related Issue

Builds on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), and [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), because those drafts established recent changes as a retry-aware, paginated, parser-boundary-sensitive read path.

No upstream issue was filed from this local workspace.

## Changes

- Pass the current recent-changes page number into the internal change-item iterator.
- Count only top-level structural `div.changes-list-item` entries after existing nested-table filtering.
- Include site `unix_name`, page number, and structural change-item position in malformed recent-change item `NoElementException` messages.
- Add a focused malformed recent-change title test that asserts the contextual error message.
- Preserve successful recent-change parsing, comment text spacing, page-title text spacing, comment-markup filtering, comment-pager filtering, non-numeric pager handling, batched pagination, limit-bounded pagination, retry behavior, and empty-result behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Recent-change parser error-context ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed structural recent-change items still fail when a required title link is missing. | `TestSiteGetRecentChanges.test_get_recent_changes_missing_title_includes_site_page_and_item_context` raises `NoElementException`. | A change that silently skips, accepts, or fabricates a title for the malformed item rejects this local completion claim. |
| Recent-change parser failures identify the affected site, page number, and structural item position. | The focused test asserts `Title element is not found for site: test (page=1, change=1)`. | The RED test failed before the fix because the message was only `Title element is not found.` |
| Structural item positions ignore nested change-like markup inside comment tables. | Source inspection shows `change_index` increments only after the existing `item.find_parent("table")` skip. | A future change that counts nested comment content before filtering could report misleading change positions. |
| Recent-change workflows remain green. | `uv run pytest tests/unit/test_site.py -q` passed 65 tests. | Regressions in retry, pagination, limits, pager filtering, comment-markup filtering, text spacing, normal parsing, or site helpers reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `0b78eee fix(site): include context in recent change parse errors`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_missing_title_includes_site_page_and_item_context -q` failed before the fix because the error only said `Title element is not found.`
- GREEN: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_missing_title_includes_site_page_and_item_context -q`
- `uv run pytest tests/unit/test_site.py -q` passed 65 tests.
- `uv run pytest tests/unit -q` passed 722 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Missing required structural recent-change elements still raise `NoElementException`.
- Those exceptions include site `unix_name`, recent-changes page number, and top-level change item position.
- Nested change-like markup inside comments remains ignored before item positions are counted.
- Successful recent-change parsing, retry behavior, pagination batching, limit handling, pager filtering, comment and title text spacing, comment-markup isolation, and `SiteChange` field semantics remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Recent-changes parsing is often used in read-only audit and reconciliation workflows. When Wikidot returns malformed recent-change HTML, the exception should identify which site, result page, and structural item caused the failure so maintainers can triage logs without storing the raw recent-changes HTML.

## Local Evidence, Not For Upstream Paste

- Earlier recent-changes drafts made this path retry-aware, batched across pages, bounded by caller limits, and robust against authored comment markup.
- Recent parser-context slices showed that site/page/item-specific `NoElementException` messages improve resumable local ledgers without changing successful parser behavior.
- The refreshed complexity memo continues to list `src/wikidot/module/site.py` parser/acquisition loops as audit-worthy, but this slice only claims recent-change malformed-response diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved edit comments out of upstream discussion.

## Additional Notes

This slice intentionally does not change request payloads, retry policy, page batching, limit math, pager parsing, top-level change filtering, title/date/revision/user extraction rules, comment extraction, flags, `SiteChange` fields, page APIs, publishing, or live Wikidot behavior. It only adds site/page/item context to existing malformed recent-change parser failures.
