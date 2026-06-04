# PR Draft: Include Site Context In Page Revision Row Parse Failures

## Summary

`PageCollection.get_page_revisions()` parses `history/PageRevisionListModule` rows and raises `NoElementException` when required generated cells, editor markup, or timestamp markup are missing. Earlier local slices made page revision acquisition retry-aware, scoped revision row parsing to direct structural cells, preserved revision comment spacing, reused duplicate page revision data, and added site-aware direct page revision property failures. The remaining malformed revision row parser messages, however, identified only page fullname and revision ID: `Cannot find revision cells for page: scp-001, revision: 123`.

This follow-up keeps revision request batching, retry behavior, duplicate page-ID grouping, cached revision reuse, direct row-cell scoping, revision number parsing, editor parsing, timestamp parsing, comment text extraction, lazy `Page.revisions` behavior, and exception type unchanged. It only adds the site unix name to the existing malformed revision row parser failure messages: `Cannot find revision cells for site: <site>, page: <fullname>, revision: <id>`, plus the analogous created-by and created-at required-element messages.

## Related Issue

Builds on [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [150-pr-page-revision-failure-context.md](150-pr-page-revision-failure-context.md), and [196-pr-page-property-site-context.md](196-pr-page-property-site-context.md). Those drafts established page revision acquisition and parser failures as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Include `site.unix_name`, representative page fullname, and revision ID in the `NoElementException` raised when a revision row lacks enough direct structural cells.
- Include the same site/page/revision context when the direct created-by `span.printuser` is missing.
- Include the same site/page/revision context when the direct created-at `span.odate` is missing.
- Preserve revision request construction, retry behavior, duplicate page-ID grouping, cached revision reuse, row-cell scoping, successful `PageRevision` construction, lazy `Page.revisions`, and exception type.

## Type Of Change

- Bug fix / diagnostics improvement
- Page revision parser ledger context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed revision rows still raise `NoElementException`, but identify site, page, and revision ID when required cells are missing. | `TestPageCollectionAcquire.test_acquire_revisions_missing_cells_includes_site_context` asserts `Cannot find revision cells for site: test-site, page: test-page, revision: 1`. | Changing exception type, accepting malformed rows, or leaving a page-only message rejects this local completion claim. |
| Missing direct revision editor markup identifies site, page, and revision ID. | `TestPageCollectionAcquire.test_acquire_revisions_missing_created_by_includes_site_context` asserts `Cannot find created by element for site: test-site, page: test-page, revision: 123`. | Parsing nested/editorless rows as valid or leaving a page-only message rejects this local completion claim. |
| Missing direct revision timestamp markup identifies site, page, and revision ID. | `TestPageCollectionAcquire.test_acquire_revisions_missing_created_at_includes_site_context` asserts `Cannot find created at element for site: test-site, page: test-page, revision: 456`. | Parsing timestampless rows as valid or leaving a page-only message rejects this local completion claim. |
| Successful revision acquisition behavior remains unchanged. | Adjacent page/site tests cover revision acquisition, duplicate page-ID grouping, cached revision reuse, lazy page revision access, and page/site workflows. | Regressions in request payloads, retry behavior, duplicate handling, row scoping, comment extraction, or `PageRevision` ownership reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `baea31f fix(page): include site in revision parse failures`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_missing_cells_includes_site_context -q` failed before the fix because the message was `Cannot find revision cells for page: test-page, revision: 1`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_missing_cells_includes_site_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_missing_created_by_includes_site_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_missing_created_at_includes_site_context -q`.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 184 tests.
- `uv run pytest tests/unit -q` passed 735 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageCollection.get_page_revisions()` still uses retry-aware revision acquisition and the existing `history/PageRevisionListModule` payload.
- Cached revision reuse and duplicate page-ID grouping remain unchanged.
- Malformed revision rows still raise `NoElementException`.
- Revision row required-cell, created-by, and created-at parser failures now include site unix name, page fullname, and revision ID.
- Successful revision row parsing, comment text extraction, and `PageRevisionCollection` ownership remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Large page-history collection workflows often aggregate parser failures into plain-text ledgers. A page-only revision parse error is ambiguous when the same fullname exists on multiple Wikidot sites. Adding site context makes the existing strict revision parser failure self-contained without changing request behavior, successful parsing, or how malformed rows are classified.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified parser diagnostics and page revision acquisition as practical workflow surfaces for large corpus runs.
- Recent site-context slices showed the same low-risk pattern: add compact site/object identifiers to existing plain-text exceptions without changing successful behavior.
- This slice only claims page revision row parser diagnostics. It does not claim any live Wikidot behavior change.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally keeps the existing representative-page behavior for duplicate page-ID groups. Pages sharing the same page ID still share one parsed revision response, and a malformed shared response reports the first page in that group just as the previous page-only message did.
