# PR Draft: Include Site Context In Lazy Page Revision Fetch Failures

## Summary

`PageRevision.source` and `PageRevision.html` use retry-aware lazy acquisition through `PageRevisionCollection.get_sources()` and `get_htmls()`. Earlier local slices made those properties fail visibly when retry exhaustion leaves the requested revision uncached and later added page/revision context, but the exhausted lazy failure still did not identify the Wikidot site: `Cannot retrieve page revision source for page: scp-001, revision: 123`.

This follow-up keeps lazy retry behavior, batch partial-success behavior, request payloads, source/HTML parsing, duplicate revision-ID grouping, cached duplicate reuse, cached property reads, and exception type unchanged. It only adds the page's site unix name to the existing lazy source and HTML exhausted-retry messages: `Cannot retrieve page revision source for site: <site>, page: <fullname>, revision: <revision_id>` and `Cannot retrieve page revision HTML for site: <site>, page: <fullname>, revision: <revision_id>`.

## Related Issue

Builds on [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), and [200-pr-page-revision-source-parse-site-context.md](200-pr-page-revision-source-parse-site-context.md). Those drafts established page revision source/HTML acquisition as retry-aware, deduplicated, parse-once, visible on exhausted lazy fetches, and now site-contextual for adjacent page revision parse paths.

No upstream issue was filed from this local workspace.

## Changes

- Include `page.site.unix_name`, page fullname, and revision ID when lazy `PageRevision.source` retry acquisition leaves the source uncached.
- Include `page.site.unix_name`, page fullname, and revision ID when lazy `PageRevision.html` retry acquisition leaves the rendered HTML uncached.
- Tighten the existing lazy source and HTML exhausted-retry regressions to assert site/page/revision context.
- Preserve request payloads, retry policy, cached property reads, duplicate revision-ID grouping, cached duplicate reuse, source/HTML response parsing, batch partial-success behavior, and exception type.

## Type Of Change

- Bug fix / diagnostics improvement
- Page revision lazy fetch ledger context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Lazy `PageRevision.source` still fails visibly when retry acquisition leaves source uncached. | `TestPageRevision.test_source_property_raises_when_retry_is_exhausted` returns `(None,)` from retry fetches and expects `UnexpectedException`. | Returning `None`, silently caching placeholder source, or changing the retry module payload rejects this local completion claim. |
| Lazy source failures identify site, page, and revision. | The focused source regression asserts `Cannot retrieve page revision source for site: test-site, page: test-page, revision: 100`. | The RED test failed before the fix because the message only named page/revision. |
| Lazy `PageRevision.html` still fails visibly when retry acquisition leaves HTML uncached. | `TestPageRevision.test_html_property_raises_when_retry_is_exhausted` returns `(None,)` from retry fetches and expects `UnexpectedException`. | Returning `None`, silently caching placeholder HTML, or changing the retry module payload rejects this local completion claim. |
| Lazy HTML failures identify site, page, and revision. | The focused HTML regression asserts `Cannot retrieve page revision HTML for site: test-site, page: test-page, revision: 100`. | The RED test failed before the fix because the message only named page/revision. |
| Page revision behavior remains green. | `uv run pytest tests/unit/test_page_revision.py -q` passed 35 tests. | Regressions in source extraction, HTML separator handling, retry `None` handling, duplicate ID grouping, cached duplicate reuse, or lazy properties reject this local completion claim. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 219 tests. | Regressions in page source acquisition, page revision-list acquisition, source iterator behavior, page source workflows, or site publish-adjacent workflows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `4ac707e fix(page_revision): include site in lazy fetch failures`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_source_property_raises_when_retry_is_exhausted tests/unit/test_page_revision.py::TestPageRevision::test_html_property_raises_when_retry_is_exhausted -q` failed before the fix because both messages only named page/revision.
- GREEN: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_source_property_raises_when_retry_is_exhausted tests/unit/test_page_revision.py::TestPageRevision::test_html_property_raises_when_retry_is_exhausted -q`.
- `uv run pytest tests/unit/test_page_revision.py -q` passed 35 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_site.py -q` passed 219 tests.
- `uv run pytest tests/unit -q` passed 735 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageRevision.source` still performs lazy retry-aware acquisition when `_source` is unset.
- `PageRevision.source` still raises `UnexpectedException` if `_source` remains unset after that acquisition attempt.
- The lazy source failure names the site unix name, page fullname, and revision ID.
- `PageRevision.html` still performs lazy retry-aware acquisition when `_html` is unset.
- `PageRevision.html` still raises `UnexpectedException` if `_html` remains unset after that acquisition attempt.
- The lazy HTML failure names the site unix name, page fullname, and revision ID.
- Batch `PageRevisionCollection.get_sources()` and `get_htmls()` behavior remains unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Revision source and rendered HTML are commonly inspected through single-revision properties after selecting a history row. When that lazy read exhausts retry, a page/revision-only log line remains ambiguous if the same page fullname exists on multiple Wikidot sites. Adding site context makes the existing strict lazy failure self-contained without changing request behavior, successful source/HTML acquisition, duplicate handling, or batch partial-success semantics.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established page revision source/HTML fetches as a practical read-heavy surface: retry-aware acquisition, duplicate-ID batching, cached duplicate reuse, source/HTML parsing, visible lazy fetch failures, source parser diagnostics, and revision row parser diagnostics.
- Recent site-context slices showed the same low-risk pattern: add compact site/object identifiers to existing plain-text exceptions without changing successful behavior.
- This slice only claims lazy page revision fetch diagnostics. It does not claim any live Wikidot behavior change.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, retry policy, batch partial-success behavior, source text extraction, HTML separator handling, duplicate revision-ID grouping, cached duplicate reuse, page revision-list parsing, page source fetching, publishing, or mutation methods. It only adds site/page/revision context to existing lazy exhausted-retry failures.
