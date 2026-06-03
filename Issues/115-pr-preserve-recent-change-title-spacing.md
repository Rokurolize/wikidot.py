# PR Draft: Preserve Recent-Change Page Title Spacing

## Summary

`Site.get_recent_changes(...)` parses recent-change rows returned by `changes/SiteChangesListModule`.

Before this fix, page titles were extracted with `title_elem.get_text().strip()`. When a rendered recent-change title contained adjacent formatted child elements, visible text could be concatenated. The focused regression changed the first fixture title link to `<span>First <em>part</em></span><span>Second part</span>`; before the fix, the parsed page title became `First partSecond part`.

This fix extracts recent-change page title text with a space separator and `strip=True`, preserving visible word boundaries while keeping request construction, retry handling, pagination, limit handling, structural change parsing, href-derived page fullname, flags, revision parsing, modifier parsing, comment parsing, and `SiteChange` output shape unchanged.

## Related Issue

Builds on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), and [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), because those drafts established recent changes as a practical read-heavy site workflow and recent-change comments/titles as user-visible markup that should preserve text fidelity without weakening structural parsing.

The text-fidelity failure class is adjacent to [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), and [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), because all of these fixes preserve user-visible text while avoiding accidental parser-boundary changes.

No upstream issue was filed from this local workspace.

## Changes

- Extract recent-change page title text with `get_text(" ", strip=True)` instead of `get_text().strip()`.
- Add a public recent-changes regression where adjacent formatted title chunks keep a space between visible text chunks.
- Preserve request construction, retry handling, empty results, real pagination, comment-pager filtering, limit-bounded pagination, structural change parsing, href-derived page fullname, flags, revision parsing, modifier parsing, comment parsing, and `SiteChange` field semantics.

## Type Of Change

- Bug fix
- Parser/text fidelity improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Recent-change page titles should not concatenate adjacent rendered title chunks or formatted child text. | `TestSiteGetRecentChanges.test_get_recent_changes_preserves_page_title_text_spacing` asserts `page_title == "First part Second part"` through `Site.get_recent_changes(...)`. | The RED test failed before the fix because the parsed title was `First partSecond part`. |
| Recent-changes acquisition and parser boundaries should remain unchanged. | `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 12 recent-change tests covering normal parsing, authored comment markup filtering, comment spacing, title spacing, empty results, limit handling, retry, non-numeric pager links, comment pager filtering, paginated batching, and limit-bounded pagination. | If request sequencing, parser-boundary filtering, pagination, retry, or limit behavior regresses, the recent-change test class rejects the local completion claim. |
| Adjacent site and page workflows should remain green. | `uv run pytest tests/unit/test_site.py -q` passed 59 tests; `uv run pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 158 tests. | Regressions in page iteration, source collection, publishing, page details, page search, recent changes, or site-level helpers reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `da07175 fix(site): preserve recent change title spacing`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_preserves_page_title_text_spacing -q` failed before the fix because `page_title` was `First partSecond part`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_preserves_page_title_text_spacing -q`
- `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 12 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 59 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 158 tests.
- `uv run pytest tests/unit -q` passed 667 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Recent-change page titles preserve a separator between adjacent rendered title chunks and formatted child text.
- The href-derived `page_fullname` remains independent of title text flattening.
- Existing zero-limit behavior, first-page retry handling, empty results, real pagination, non-numeric pager handling, comment-pager filtering, paginated batching, limit-bounded pagination, normal fixture parsing, comment parsing, revision parsing, modifier parsing, flag parsing, and `SiteChange` field semantics remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Recent-change page titles are user-visible content and may contain formatted title chunks. `Site.get_recent_changes(...)` should preserve visible word boundaries in page title text without changing the request flow, pagination logic, structural metadata parsing, or href-derived page identity.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), and [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md) established `changes/SiteChangesListModule` as a practical local target and recent-change text fields as authored/user-visible parser surfaces.
- Text-fidelity drafts [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), and [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md) established visible text spacing as a recurring HTML flattening risk.
- The refreshed complexity scan continues to flag `src/wikidot/module/site.py` around recent-changes parsing as an audit-worthy path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved recent-change titles out of upstream discussion.

## Additional Notes

This slice does not change request construction, retry behavior, batch sizing, limit handling, top-level change parsing, href-derived page fullname, date/revision/user extraction, flag parsing, comment extraction, pager filtering, or the `SiteChange` dataclass. It only changes how recent-change page title text is flattened from rendered HTML into `SiteChange.page_title`.
