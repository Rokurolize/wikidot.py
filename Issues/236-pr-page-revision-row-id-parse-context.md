# PR Draft: Include Context In Page Revision Row ID Parse Errors

## Summary

`PageCollection.get_page_revisions()` parses generated `history/PageRevisionListModule` rows whose structural IDs use the `revision-row-<id>` form. Earlier local slices made page revision acquisition retry-aware, deduplicated duplicate page revision-list fetches, scoped revision row cells to direct structural columns, preserved revision comment spacing, reused cached duplicate page revisions, validated missing revision-list response bodies, and added site-aware required-element parser failures. One remaining parser-value gap was earlier in the same row loop: malformed `revision-row-*` IDs still reached a raw `int(...)` conversion and raised bare `ValueError` before wikidot.py could attach site or page context.

This follow-up keeps successful revision-list parsing unchanged, but routes the structural revision row ID through a small parser helper. Malformed row IDs now raise `NoElementException` with the site unix name, page fullname, page ID, affected field, and raw value, so plain-text logs can identify the broken generated row without retaining raw history HTML or page content.

## Related Issue

Builds on [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [150-pr-page-revision-failure-context.md](150-pr-page-revision-failure-context.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), and [222-pr-page-revision-batch-response-body-context.md](222-pr-page-revision-batch-response-body-context.md). Those drafts established page revision-list acquisition, parser scoping, cache reuse, and contextual parser failures as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Add a small parser for generated `revision-row-*` values.
- Convert malformed revision row IDs into `NoElementException` with site, page, page ID, field, and raw value context.
- Add a focused regression test for a malformed `id="revision-row-not-a-number"` row.
- Preserve revision-list request construction, retry behavior, duplicate page-ID grouping, cached revision reuse, direct row-cell scoping, successful revision number parsing, editor parsing, timestamp parsing, comment extraction, `PageRevisionCollection` ownership, lazy `Page.revisions`, and `Page.latest_revision`.

## Type Of Change

- Bug fix / diagnostics improvement
- Page revision-list parser error-context ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed structural page revision row IDs fail with wikidot.py's contextual parser exception rather than a raw integer conversion exception. | `TestPageCollectionAcquire.test_acquire_revisions_malformed_revision_id_includes_site_page_and_value_context` asserts `NoElementException` for `id="revision-row-not-a-number"`. | A raw `ValueError`, silent row skip, fabricated revision ID, or malformed `PageRevision` rejects this local completion claim. |
| The malformed row ID error identifies the affected site, page, page ID, field, and raw value. | The focused test asserts `Revision ID is malformed for site: test-site, page: test-page (id=12345, field=revision_row_id, value=revision-row-not-a-number)`. | Omitting site, page, page ID, field, or raw value makes the failure ambiguous and rejects this local completion claim. |
| Malformed row IDs do not populate page revisions. | The focused test asserts `mock_page_with_id._revisions is None` after the exception. | Partially assigning a revision collection after a malformed structural row rejects this local completion claim. |
| Successful page revision acquisition behavior remains unchanged. | `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 39 tests, and `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 236 tests. | Regressions in request payloads, retry behavior, duplicate page-ID grouping, cached revision reuse, row-cell scoping, revision number parsing, editor parsing, timestamp parsing, comment extraction, lazy revision access, or site/page workflows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `49fa21f fix(page): report malformed revision row ids`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_revision_id_includes_site_page_and_value_context -q` failed before the fix with raw `ValueError` from `rev_id = int(str(rev_element["id"]).removeprefix("revision-row-"))`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_revision_id_includes_site_page_and_value_context -q` passed 1 test.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 39 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 236 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left 2 files unchanged.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run pytest tests/unit -q` passed 781 tests.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A page revision-list response whose structural row has a malformed `revision-row-*` ID raises `NoElementException`.
- The malformed row ID message includes site unix name, page fullname, page ID, field name, and the raw malformed row ID value.
- Page revisions are not populated after the malformed structural row failure.
- Successful revision-list parsing, revision number parsing, editor parsing, timestamp parsing, comment extraction, retry behavior, duplicate page-ID grouping, cached revision reuse, row-cell scoping, lazy `Page.revisions`, and `Page.latest_revision` remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Revision history is a read-heavy evidence surface for page inspection, source auditing, publication checks, and rollback workflows. If Wikidot returns malformed generated history markup, wikidot.py should fail rather than invent a revision ID or silently drop a row, but the failure should identify the affected site, page, field, and raw value. That keeps strict parser behavior while making logs self-contained enough for maintainers to triage without retaining raw page-history HTML.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified page revision-list acquisition as a practical workflow surface for large page-source and history collection runs.
- Adjacent page revision drafts already covered retry-aware revision-list acquisition, duplicate fetch deduplication, duplicate parse reuse, row-cell parser scoping, comment spacing, cached duplicate revision reuse, required-element site context, direct revision fetch context, response-body validation, and batch response-body validation.
- The immediate RED failure showed a raw `ValueError` from the structural row ID conversion before any existing row-cell or required-element parser context could run.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw history HTML, and page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change revision number cell parsing, revision-list request construction, retry policy, duplicate page-ID grouping, cached revision cloning, row-cell scoping, user parsing, date parsing, comment extraction, revision source/HTML fetching, lazy revision properties, or mutation paths. It only converts malformed structural revision row ID values into contextual parser errors.
