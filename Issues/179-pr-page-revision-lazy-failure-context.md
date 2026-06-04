# PR Draft: Include Page Context In Lazy Page Revision Fetch Failures

## Summary

`PageRevision.source` and `PageRevision.html` use retry-aware lazy acquisition through `PageRevisionCollection.get_sources()` and `get_htmls()`. A previous local slice made those properties fail visibly when retry exhaustion left the requested revision uncached, but the resulting `UnexpectedException` only named the revision ID.

This follow-up keeps the lazy retry behavior, batch partial-success behavior, source/HTML parsing, duplicate revision-ID handling, cached reads, and existing exception type unchanged, but includes the page fullname with the revision ID in lazy exhausted-retry failures.

## Related Issue

Builds on [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [150-pr-page-revision-failure-context.md](150-pr-page-revision-failure-context.md), and [164-pr-page-revision-source-parse-context.md](164-pr-page-revision-source-parse-context.md), because those drafts established page revision source/HTML acquisition as retry-aware, deduplicated, parse-once, visible on exhausted lazy fetches, and contextual for adjacent page-revision failures.

No upstream issue was filed from this local workspace.

## Changes

- Include page fullname and revision ID when lazy `PageRevision.source` retry acquisition leaves the source uncached.
- Include page fullname and revision ID when lazy `PageRevision.html` retry acquisition leaves the rendered HTML uncached.
- Tighten the existing lazy source and HTML exhausted-retry regressions to assert page/revision context.
- Preserve request payloads, retry policy, cached property reads, duplicate revision-ID grouping, source/HTML response parsing, batch partial-success behavior, and exception type.

## Type Of Change

- Bug fix / diagnostics improvement
- Page revision lazy fetch failure context
- Test tightening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Lazy `PageRevision.source` still fails visibly when retry acquisition leaves source uncached. | `TestPageRevision.test_source_property_raises_when_retry_is_exhausted` returns `(None,)` from retry fetches and expects `UnexpectedException`. | Returning `None`, silently caching placeholder source, or changing the retry module payload rejects this local completion claim. |
| Lazy source failures identify both page and revision. | The focused source regression asserts `Cannot retrieve page revision source for page: test-page, revision: 100`. | The RED test failed before the fix because the message only named revision `100`. |
| Lazy `PageRevision.html` still fails visibly when retry acquisition leaves HTML uncached. | `TestPageRevision.test_html_property_raises_when_retry_is_exhausted` returns `(None,)` from retry fetches and expects `UnexpectedException`. | Returning `None`, silently caching placeholder HTML, or changing the retry module payload rejects this local completion claim. |
| Lazy HTML failures identify both page and revision. | The focused HTML regression asserts `Cannot retrieve page revision HTML for page: test-page, revision: 100`. | The RED test failed before the fix because the message only named revision `100`. |
| Page revision behavior remains green. | `uv run pytest tests/unit/test_page_revision.py -q` passed 35 tests. | Regressions in source extraction, HTML separator handling, retry `None` handling, duplicate ID grouping, cached duplicate reuse, or lazy properties reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `dd1e93d fix(page_revision): include page in lazy fetch failures`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_source_property_raises_when_retry_is_exhausted tests/unit/test_page_revision.py::TestPageRevision::test_html_property_raises_when_retry_is_exhausted -q` failed before the fix because both messages only named revision `100`.
- GREEN: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_source_property_raises_when_retry_is_exhausted tests/unit/test_page_revision.py::TestPageRevision::test_html_property_raises_when_retry_is_exhausted -q`
- `uv run pytest tests/unit/test_page_revision.py -q` passed 35 tests.
- `uv run pytest tests/unit -q` passed 725 tests.
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageRevision.source` still performs lazy retry-aware acquisition when `_source` is unset.
- `PageRevision.source` still raises `UnexpectedException` if `_source` remains unset after that acquisition attempt.
- The source failure names the page fullname and revision ID.
- `PageRevision.html` still performs lazy retry-aware acquisition when `_html` is unset.
- `PageRevision.html` still raises `UnexpectedException` if `_html` remains unset after that acquisition attempt.
- The HTML failure names the page fullname and revision ID.
- Batch `PageRevisionCollection.get_sources()` and `get_htmls()` behavior remains unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Revision source and rendered HTML are commonly inspected through single-revision properties after selecting a history row. When that lazy read exhausts retry, logs should identify the page as well as the revision so callers can diagnose the failed history item without keeping raw response HTML, saved page source, credentials, or local rollout details.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established page revision source/HTML fetches as a practical read-heavy surface: retry-aware acquisition, duplicate-ID batching, cached duplicate reuse, source/HTML parsing, visible lazy fetch failures, and contextual source parse failures.
- Recent fetch-context slices showed that compact object identifiers improve multi-surface ledgers without changing successful behavior.
- This slice only claims lazy page revision failure diagnostics. It does not claim any live Wikidot behavior change.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, retry policy, batch partial-success behavior, source text extraction, HTML separator handling, duplicate revision-ID grouping, cached duplicate reuse, page revision-list parsing, page source fetching, publishing, or mutation methods. It only adds page/revision context to existing lazy exhausted-retry failures.
