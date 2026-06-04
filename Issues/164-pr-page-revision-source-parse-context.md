# PR Draft: Include Context In Page Revision Source Parse Errors

## Summary

`PageRevisionCollection.get_sources()` fetches `history/PageSourceModule` responses and parses the `div.page-source` wrapper before applying the extracted wiki text to one or more `PageRevision` objects. When the response body was malformed and lacked that wrapper, the parser raised `NoElementException("Wiki text element not found")`, which did not identify the affected page or revision.

This follow-up keeps the existing `NoElementException` behavior, retry handling, duplicate revision-ID grouping, and successful source extraction semantics, but includes page fullname and revision ID in that malformed source response failure: `Wiki text element not found for page: <fullname>, revision: <revision_id>`.

## Related Issue

Builds on [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), and [150-pr-page-revision-failure-context.md](150-pr-page-revision-failure-context.md), because those drafts established page revision source/HTML acquisition as retry-aware, deduplicated, parse-once, and visible on exhausted lazy fetches.

No upstream issue was filed from this local workspace.

## Changes

- Pass the unique revision ID into the internal page-revision response parser callback.
- Include page fullname and revision ID when `history/PageSourceModule` source HTML lacks `div.page-source`.
- Add a focused malformed source response test that asserts the contextual `NoElementException` message and leaves the revision source unset.
- Preserve successful source extraction, multiline source normalization, duplicate revision-ID grouping, cached duplicate reuse, retry `None` handling, HTML acquisition, lazy source/HTML properties, and page revision-list behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Page revision source parser error-context ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed page-revision source responses still fail instead of producing empty source data. | `TestPageRevisionCollection.test_get_sources_missing_wiki_text_includes_page_and_revision_context` raises `NoElementException`. | A change that silently accepts a body without `div.page-source` rejects this local completion claim. |
| The malformed source response failure identifies the affected page and revision. | The focused test asserts `Wiki text element not found for page: test-page, revision: 100`. | The RED test failed before the fix because the message was only `Wiki text element not found`. |
| Failed source parsing does not populate the revision cache. | The focused test asserts `sample_revision._source is None`. | A change that leaves partial or placeholder source data after parse failure rejects this local completion claim. |
| Page revision source and HTML acquisition remain green. | `uv run pytest tests/unit/test_page_revision.py -q` passed 35 tests. | Regressions in source extraction, multiline normalization, duplicate ID grouping, cached duplicate reuse, HTML separator handling, or lazy properties reject this local completion claim. |
| Adjacent page workflows remain green. | `uv run pytest tests/unit/test_page_revision.py tests/unit/test_page.py -q` passed 144 tests. | Regressions in page-level source/revision acquisition or direct page properties reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `53d6770 fix(page_revision): include context in source parse errors`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_missing_wiki_text_includes_page_and_revision_context -q` failed before the fix because the error lacked page and revision context.
- GREEN: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_missing_wiki_text_includes_page_and_revision_context -q`
- `uv run pytest tests/unit/test_page_revision.py -q` passed 35 tests.
- `uv run pytest tests/unit/test_page_revision.py tests/unit/test_page.py -q` passed 144 tests.
- `uv run pytest tests/unit -q` passed 721 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageRevisionCollection.get_sources()` still raises `NoElementException` when a source response lacks `div.page-source`.
- That exception includes the page fullname and unique revision ID associated with the malformed response.
- The failed revision remains without cached source data.
- Successful revision source extraction, duplicate revision-ID grouping, cached duplicate reuse, retry `None` handling, HTML acquisition, lazy source/HTML access, and page revision-list acquisition remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Revision source inspection is a read-heavy workflow in history review, source auditing, rollback checks, and publication verification. When Wikidot returns malformed revision source HTML, the failure should identify the page and revision from the exception text so logs are diagnosable without retaining raw response HTML.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts made page revision source/HTML acquisition retry-aware, deduplicated by revision ID, and parse-once per unique response.
- Recent parser-context slices showed that page/object-specific `NoElementException` messages improve resumable local ledgers without changing successful behavior.
- The refreshed complexity memo continues to treat parser/acquisition loops as audit-worthy, but this slice only claims source parse failure context.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change request payloads, retry policy, source text normalization, duplicate source request grouping, cached duplicate source reuse, HTML response parsing, lazy `PageRevision.source` exhausted-retry behavior, page revision-list parsing, page source fetching, publishing, or mutation methods. It only adds page/revision context to an existing malformed page-revision source parser failure.
