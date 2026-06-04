# PR Draft: Include Site Context In Page Revision Source Parse Failures

## Summary

`PageRevisionCollection.get_sources()` fetches `history/PageSourceModule` responses and parses the generated `div.page-source` wrapper before applying the extracted wiki text to one or more `PageRevision` objects. Earlier local slices made revision source/HTML acquisition retry-aware, deduplicated revision-ID requests, reused duplicate parsed source responses, surfaced lazy fetch failures, and added page/revision context to malformed revision source parser failures. The malformed revision source parser error, however, still did not identify the site: `Wiki text element not found for page: scp-001, revision: 123`.

This follow-up keeps retry behavior, request payloads, duplicate revision-ID grouping, cached duplicate source reuse, parse-once response reuse, multiline source normalization, successful `PageSource` construction, lazy `PageRevision.source` behavior, HTML acquisition, and exception type unchanged. It only adds the page's site unix name to that existing source parser failure message: `Wiki text element not found for site: <site>, page: <fullname>, revision: <revision_id>`.

## Related Issue

Builds on [014-pr-preserve-viewsource-text.md](014-pr-preserve-viewsource-text.md), [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [164-pr-page-revision-source-parse-context.md](164-pr-page-revision-source-parse-context.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), and [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md). Those drafts established page revision source acquisition and page revision parser diagnostics as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Include `page.site.unix_name`, page fullname, and revision ID in the `NoElementException` raised when a `history/PageSourceModule` response lacks `div.page-source`.
- Preserve revision source request construction, retry behavior, duplicate revision-ID grouping, cached duplicate source reuse, parse-once response reuse, multiline source normalization, successful `PageSource` ownership, lazy revision source behavior, HTML acquisition behavior, and exception type.

## Type Of Change

- Bug fix / diagnostics improvement
- Page revision source parser ledger context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed revision source responses still raise `NoElementException`, but identify site, page, and revision ID. | `TestPageRevisionCollection.test_get_sources_missing_wiki_text_includes_site_page_and_revision_context` asserts `Wiki text element not found for site: test-site, page: test-page, revision: 100`. | Changing exception type, accepting a body without `div.page-source`, or leaving a page-only message rejects this local completion claim. |
| Revision source acquisition behavior remains unchanged. | `uv run pytest tests/unit/test_page_revision.py -q` covers successful source extraction, multiline source normalization, failed retry responses, duplicate revision-ID grouping, cached duplicate reuse, HTML acquisition, and lazy source/HTML paths. | Regressions in request payloads, retry behavior, source text extraction, duplicate handling, or lazy properties reject this local completion claim. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 219 tests. | Regressions in page revision-list acquisition, source iterator behavior, page source workflows, or site publish-adjacent workflows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `1fc8f82 fix(page_revision): include site in source parse failures`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_missing_wiki_text_includes_site_page_and_revision_context -q` failed before the fix because the message was `Wiki text element not found for page: test-page, revision: 100`.
- GREEN: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_missing_wiki_text_includes_site_page_and_revision_context -q`.
- `uv run pytest tests/unit/test_page_revision.py -q` passed 35 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 219 tests.
- `uv run pytest tests/unit -q` passed 735 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageRevisionCollection.get_sources()` still uses retry-aware revision source acquisition and the existing `history/PageSourceModule` payload.
- Cached duplicate source reuse and duplicate revision-ID grouping remain unchanged.
- A malformed revision source wrapper still raises `NoElementException`.
- That revision source parser failure now includes site unix name, page fullname, and revision ID.
- Successful revision source extraction, multiline source normalization, HTML acquisition, and lazy `PageRevision.source` behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Large history/source review workflows often aggregate revision source parser failures into plain-text ledgers. A page/revision-only source parse error is ambiguous when the same page fullname exists on multiple Wikidot sites. Adding site context makes the existing strict revision source parser failure self-contained without changing request behavior, successful source extraction, or how malformed source wrappers are classified.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified page revision source acquisition, source parsing, duplicate revision reuse, and parser diagnostics as practical workflow surfaces for history/source review.
- Recent site-context slices showed the same low-risk pattern: add compact site/object identifiers to existing plain-text exceptions without changing successful behavior.
- This slice only claims page revision source parser diagnostics. It does not claim any live Wikidot behavior change.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally keeps the existing collection-level page ownership behavior. A `PageRevisionCollection` still uses its `page` owner for source requests and `PageSource` ownership, and duplicate revision IDs still share one parsed response before being applied to every matching revision entry.
