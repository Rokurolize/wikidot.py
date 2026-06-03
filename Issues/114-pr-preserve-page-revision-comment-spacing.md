# PR Draft: Preserve Page-Revision Comment Spacing

## Summary

`PageCollection._acquire_page_revisions(...)` parses page history rows returned by `history/PageRevisionListModule`, which are exposed through `PageCollection.get_page_revisions()` and `Page.revisions`.

Before this fix, revision comments were extracted with `tds[6].text.strip()`. When a rendered revision comment contained adjacent paragraphs or formatted child elements, visible text could be concatenated. The focused regression used `<p>First <span>part</span></p><p>Second part</p>` in the comment cell; before the fix, the parsed revision comment became `First partSecond part`.

This fix extracts page revision comments with a space separator and `strip=True`, preserving visible word boundaries while keeping page ID acquisition, request deduplication, retry exhaustion behavior, direct row-cell scoping, revision number parsing, author/date parsing, duplicate page propagation, and revision source/HTML acquisition unchanged.

## Related Issue

Builds on [014-pr-preserve-viewsource-text.md](014-pr-preserve-viewsource-text.md), [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), and [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), because those drafts established page revision list/source/HTML collection as a practical workflow and revision rows as a parser boundary that should not be broadened accidentally.

The text-fidelity failure class is adjacent to [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), and [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), because all of these fixes preserve user-visible text while avoiding accidental structural-parser changes.

No upstream issue was filed from this local workspace.

## Changes

- Extract page revision comments with `get_text(" ", strip=True)` instead of `.text.strip()`.
- Add a public revision-list acquisition regression where adjacent paragraphs and inline formatting keep a space between visible comment text chunks.
- Preserve page ID acquisition, request deduplication, retry exhaustion behavior, direct row-cell scoping, missing-cell errors, revision ID/number parsing, user/date parsing, duplicate page propagation, and revision source/HTML behavior.

## Type Of Change

- Bug fix
- Parser/text fidelity improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Page revision comments should not concatenate adjacent rendered paragraphs or formatted child text. | `TestPageCollectionAcquire.test_acquire_revisions_preserves_comment_text_spacing` asserts `mock_page_with_id._revisions[0].comment == "First part Second part"` through `PageCollection.get_page_revisions(...)`. | The RED test failed before the fix because the parsed revision comment was `First partSecond part`. |
| Page revision-list acquisition and parser boundaries should remain unchanged. | `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 24 acquisition tests covering batched page ID acquisition, source/revision/vote/meta/detail acquisition, duplicate page IDs, nested revision table cells, missing revision cells, and retry-exhausted paths. | If request sequencing, parser-boundary filtering, deduplication, duplicate propagation, or acquisition error behavior regresses, the focused acquisition test class rejects the local completion claim. |
| Adjacent page, revision, and site workflows should remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 187 tests. | Regressions in page search, page details, revision source/HTML, site-level iteration, source collection, publishing, or recent changes reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `fe26da9 fix(page): preserve revision comment spacing`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_preserves_comment_text_spacing -q` failed before the fix because `mock_page_with_id._revisions[0].comment` was `First partSecond part`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_preserves_comment_text_spacing -q`
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 24 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 187 tests.
- `uv run pytest tests/unit -q` passed 666 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Page revision comments preserve a separator between adjacent rendered paragraphs and formatted child text.
- Nested revision-row table cells still cannot be mistaken for structural revision columns.
- Existing page ID acquisition, request construction, response deduplication, duplicate page propagation, retry-exhausted `None` behavior, missing-cell errors, revision ID/number parsing, author/date parsing, `PageRevision` ownership, and revision source/HTML behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Page revision comments are user-visible content from Wikidot history rows and can render multiple paragraphs or inline formatting. `PageCollection._acquire_page_revisions(...)` should preserve visible word boundaries in comments without changing the revision-list request flow, row parsing boundaries, or downstream `PageRevision` behavior.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [014-pr-preserve-viewsource-text.md](014-pr-preserve-viewsource-text.md), [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), and [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md) established page revision collection as a practical local target and revision rows as a parser boundary.
- Text-fidelity drafts [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), and [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md) established visible text spacing as a recurring HTML flattening risk.
- The refreshed complexity scan continues to flag `src/wikidot/module/page.py` as a broad parser/acquisition surface, and this slice deliberately changes only the revision comment text extraction line plus the focused public regression.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved revision comments out of upstream discussion.

## Additional Notes

This slice does not change page ID lookup, `history/PageRevisionListModule` request construction, retry exhaustion handling, duplicate page ID deduplication, duplicate page propagation, direct row-cell scoping, missing-cell errors, revision ID/number parsing, author/date parsing, `PageRevision` ownership, or revision source/HTML fetching. It only changes how rendered revision comment HTML is flattened into `PageRevision.comment`.
