# PR Draft: Preserve Recent-Change Comment Spacing

## Summary

`Site.get_recent_changes(...)` parses recent-change rows returned by `changes/SiteChangesListModule`.

Before this fix, edit comments were extracted with `comment_elem.get_text().strip()`. When a rendered edit comment contained adjacent paragraph or formatted child elements, visible text could be concatenated. The focused regression changed `Test edit comment` to `<p>First <span>part</span></p><p>Second part</p>`; before the fix, the parsed comment became `First partSecond part`.

This fix extracts recent-change comment text with a space separator and `strip=True`, preserving visible word boundaries while keeping request construction, retry handling, pagination, limit handling, structural change parsing, page title parsing, flags, revision parsing, modifier parsing, and `SiteChange` output shape unchanged.

## Related Issue

Builds on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), and [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), because those drafts established recent changes as a practical read-heavy site workflow and edit comments as authored markup that must not contaminate structural parsing or pagination.

The text-fidelity failure class is adjacent to [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), and [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), because all of these fixes preserve user-visible text while avoiding accidental parser-boundary changes.

No upstream issue was filed from this local workspace.

## Changes

- Extract recent-change edit comment text with `get_text(" ", strip=True)` instead of `get_text().strip()`.
- Add a public recent-changes regression where adjacent paragraphs and inline formatting keep a space between visible comment text chunks.
- Preserve request construction, retry handling, empty results, real pagination, comment-pager filtering, limit-bounded pagination, structural change parsing, page title parsing, flags, revision parsing, modifier parsing, and `SiteChange` field semantics.

## Type Of Change

- Bug fix
- Parser/text fidelity improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Recent-change edit comments should not concatenate adjacent rendered paragraphs or formatted child text. | `TestSiteGetRecentChanges.test_get_recent_changes_preserves_comment_text_spacing` asserts `comment == "First part Second part"` through `Site.get_recent_changes(...)`. | The RED test failed before the fix because the parsed comment was `First partSecond part`. |
| Recent-changes acquisition and parser boundaries should remain unchanged. | `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 11 recent-change tests covering normal parsing, authored comment markup filtering, empty results, limit handling, retry, non-numeric pager links, comment pager filtering, paginated batching, and limit-bounded pagination. | If request sequencing, parser-boundary filtering, pagination, retry, or limit behavior regresses, the recent-change test class rejects the local completion claim. |
| Site behavior should remain green. | `uv run pytest tests/unit/test_site.py -q` passed 58 tests. | Regressions in page iteration, source collection, publishing, recent changes, or site-level helpers reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `aee09e9 fix(site): preserve recent change comment spacing`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_preserves_comment_text_spacing -q` failed before the fix because `comment` was `First partSecond part`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_preserves_comment_text_spacing -q`
- `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 11 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 58 tests.
- `uv run pytest tests/unit -q` passed 664 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Recent-change edit comments preserve a separator between adjacent rendered paragraphs and formatted child text.
- Empty comment cells still normalize to `None`.
- Authored comment markup still cannot create fake recent changes, alter structural flags, or trigger phantom pagination.
- Existing zero-limit behavior, first-page retry handling, empty results, real pagination, non-numeric pager handling, paginated batching, limit-bounded pagination, normal fixture parsing, page title parsing, revision parsing, modifier parsing, and `SiteChange` field semantics remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Recent-change edit comments are user-visible content and can render multiple paragraphs or formatted inline HTML. `Site.get_recent_changes(...)` should preserve visible word boundaries in comment text without changing the request flow, pagination logic, or structural metadata parsing.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), and [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md) established `changes/SiteChangesListModule` as a practical local target and edit comments as an authored-markup parser boundary.
- Text-fidelity drafts [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), and [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md) established visible text spacing as a recurring HTML flattening risk.
- The refreshed complexity scan continues to flag `src/wikidot/module/site.py` around recent-changes parsing as an audit-worthy path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved edit comments out of upstream discussion.

## Additional Notes

This slice does not change request construction, retry behavior, batch sizing, limit handling, top-level change parsing, title/date/revision/user extraction, flag parsing, pager filtering, or the `SiteChange` dataclass. It only changes how recent-change edit comment text is flattened from rendered HTML into `SiteChange.comment`.
