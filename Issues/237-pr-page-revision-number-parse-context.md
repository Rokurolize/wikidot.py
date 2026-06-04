# PR Draft: Include Context In Page Revision Number Parse Errors

## Summary

`PageCollection.get_page_revisions()` parses generated `history/PageRevisionListModule` rows into page-owned `PageRevision` objects. Earlier local slices made page revision acquisition retry-aware, deduplicated duplicate page revision-list fetches, reused parsed duplicate revision rows, scoped revision row cells to direct structural columns, preserved revision comment spacing, reused cached duplicate page revisions, validated missing revision-list response bodies, added site-aware required-element parser failures, and converted malformed structural `revision-row-*` IDs into contextual parser errors. One adjacent parser-value gap remained after the row ID was parsed: malformed revision number cells still reached `int(tds[0].text.strip().removesuffix("."))` and raised bare `ValueError`.

This follow-up keeps successful revision-list parsing unchanged, but routes the revision number cell through a small parser helper. Malformed revision numbers now raise `NoElementException` with the site unix name, page fullname, structural revision ID, page ID, affected field, and raw cell value, so plain-text logs can identify the broken generated row without retaining raw history HTML or page content.

## Related Issue

Builds on [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [150-pr-page-revision-failure-context.md](150-pr-page-revision-failure-context.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), [222-pr-page-revision-batch-response-body-context.md](222-pr-page-revision-batch-response-body-context.md), and [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md). Those drafts established page revision-list acquisition, parser scoping, cache reuse, response validation, and contextual parser failures as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Add a small parser for generated page-history revision number cell text.
- Convert malformed revision number text into `NoElementException` with site, page, structural revision ID, page ID, field, and raw value context.
- Add a focused regression test for a malformed `<td>not-a-number.</td>` revision number cell.
- Preserve revision-list request construction, retry behavior, duplicate page-ID grouping, cached revision reuse, direct row-cell scoping, successful structural row ID parsing, successful revision number parsing, editor parsing, timestamp parsing, comment extraction, `PageRevisionCollection` ownership, lazy `Page.revisions`, and `Page.latest_revision`.

## Type Of Change

- Bug fix / diagnostics improvement
- Page revision-list parser error-context ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed page-history revision number cells fail with wikidot.py's contextual parser exception rather than a raw integer conversion exception. | `TestPageCollectionAcquire.test_acquire_revisions_malformed_revision_number_includes_site_page_and_value_context` asserts `NoElementException` for `<td>not-a-number.</td>`. | A raw `ValueError`, silent row skip, fabricated revision number, or malformed `PageRevision` rejects this local completion claim. |
| The malformed revision number error identifies the affected site, page, structural revision ID, page ID, field, and raw value. | The focused test asserts `Revision number is malformed for site: test-site, page: test-page, revision: 123 (id=12345, field=revision_number, value=not-a-number.)`. | Omitting site, page, structural revision ID, page ID, field, or raw value makes the failure ambiguous and rejects this local completion claim. |
| Malformed revision numbers do not populate page revisions. | The focused test asserts `mock_page_with_id._revisions is None` after the exception. | Partially assigning a revision collection after a malformed revision number rejects this local completion claim. |
| Successful page revision acquisition behavior remains unchanged. | `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 40 tests, and `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 237 tests. | Regressions in request payloads, retry behavior, duplicate page-ID grouping, cached revision reuse, row-cell scoping, structural row ID parsing, successful revision number parsing, editor parsing, timestamp parsing, comment extraction, lazy revision access, or site/page workflows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `80e5eea fix(page): report malformed revision numbers`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_revision_number_includes_site_page_and_value_context -q` failed before the fix with raw `ValueError` from `rev_no = int(tds[0].text.strip().removesuffix("."))`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_revision_number_includes_site_page_and_value_context -q` passed 1 test.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 40 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 237 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left 2 files unchanged.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run pytest tests/unit -q` passed 782 tests.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A page revision-list response whose revision number cell is malformed raises `NoElementException`.
- The malformed revision number message includes site unix name, page fullname, structural revision ID, page ID, field name, and the raw malformed revision number value.
- Page revisions are not populated after the malformed revision number failure.
- Successful revision-list parsing, structural revision row ID parsing, revision number parsing, editor parsing, timestamp parsing, comment extraction, retry behavior, duplicate page-ID grouping, cached revision reuse, row-cell scoping, lazy `Page.revisions`, and `Page.latest_revision` remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Revision history is a read-heavy evidence surface for page inspection, source auditing, publication checks, and rollback workflows. If Wikidot returns malformed generated history markup, wikidot.py should fail rather than invent a revision number or silently drop a row, but the failure should identify the affected site, page, structural revision, field, and raw value. That keeps strict parser behavior while making logs self-contained enough for maintainers to triage without retaining raw page-history HTML.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified page revision-list acquisition as a practical workflow surface for large page-source and history collection runs.
- Adjacent page revision drafts already covered retry-aware revision-list acquisition, duplicate fetch deduplication, duplicate parse reuse, row-cell parser scoping, comment spacing, cached duplicate revision reuse, required-element site context, direct revision fetch context, response-body validation, batch response-body validation, and structural row ID parse context.
- The immediate RED failure showed a raw `ValueError` from the revision number conversion after the structural row ID had already been parsed.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw history HTML, and page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change structural revision row ID parsing, revision-list request construction, retry policy, duplicate page-ID grouping, cached revision cloning, row-cell scoping, user parsing, date parsing, comment extraction, revision source/HTML fetching, lazy revision properties, or mutation paths. It only converts malformed revision number cell values into contextual parser errors.
